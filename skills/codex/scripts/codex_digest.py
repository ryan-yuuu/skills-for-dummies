#!/usr/bin/env python3
"""Condense a `codex exec --json` event stream into a short digest.

Raw JSONL from a real Codex run is long and mostly noise: progress narration,
full command output, duplicated started/completed pairs. Reading it directly
wastes context. This prints what you actually need to judge the run -- what it
ran, what it changed, what it concluded, what it cost.

Usage:
    python3 codex_digest.py run.jsonl
    codex exec --json "<task>" < /dev/null | python3 codex_digest.py

Options:
    --full-output   Include output for successful commands, and don't truncate.
                    (Failed commands always show output, truncated by default.)
    --json          Emit the digest as JSON instead of text. Matches the text
                    form: truncates command output, keeps only the final agent
                    message (with `omitted_messages` counting the rest) unless
                    --full-output is passed, and applies the same visibility
                    gate to `in_flight`.

Exit status:
    0   the final turn reached `turn.completed` without failing (errors carried
        over from a superseded earlier turn do not count)
    1   failed, or the stream was cut off (timeout, kill) -- so it can gate a
        pipeline directly
    2   the input file could not be read, or bad arguments
"""

import argparse
import io
import json
import sys

# Command output is merged stdout+stderr and can run to thousands of lines.
# Enough to see what happened, not enough to flood a context window.
OUTPUT_HEAD_LINES = 8
OUTPUT_LINE_CHARS = 200


def parse_stream(lines):
    """Fold a JSONL event stream into a digest dict.

    Malformed lines are counted rather than raised on: a truncated run (killed
    by a timeout, say) is exactly when you most want to see the partial digest.
    Payload shapes are checked with isinstance for the same reason -- a stream
    that half-matches expectations should degrade, not crash.
    """
    d = {
        "thread_id": None,
        "commands": [],
        "file_changes": [],
        "messages": [],
        "usage": None,
        "completed": False,
        "failed": False,
        "errors": [],
        "superseded_errors": [],
        "warnings": [],
        "malformed_lines": 0,
        "unmodeled_lines": 0,
        "other_items": {},
        "in_flight": [],
        "_done_types": {},
        "_done_ids": {},
    }

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            d["malformed_lines"] += 1
            continue
        if not isinstance(event, dict):
            d["malformed_lines"] += 1
            continue

        etype = event.get("type")

        if etype == "turn.started":
            # A new turn reopens the run: a stream cut during turn 2 must not
            # inherit turn 1's completion, nor its failure. Errors move aside
            # too -- leaving them would print an "Errors:" block above a
            # "completed" status, which reads as a contradiction.
            d["completed"] = False
            d["failed"] = False
            d["superseded_errors"].extend(d["errors"])
            d["errors"] = []
        elif etype == "thread.started":
            tid = event.get("thread_id")
            d["thread_id"] = tid if isinstance(tid, str) else None
        elif etype == "turn.completed":
            d["completed"] = True
            # A later turn without usage must not erase usage already seen
            # (resumed sessions emit more than one turn).
            if isinstance(event.get("usage"), dict):
                d["usage"] = event["usage"]
        elif etype == "turn.failed":
            d["failed"] = True
            if event.get("error") is not None:
                d["errors"].append(event["error"])
        elif etype == "error":
            d["failed"] = True
            d["errors"].append(event.get("message") or event.get("error") or event)
        elif etype == "item.completed":
            # Only completed items carry full payloads; item.started duplicates
            # them with null exit codes and empty output.
            item = event.get("item")
            if isinstance(item, dict):
                _collect_item(d, item)
            else:
                d["unmodeled_lines"] += 1
        elif etype == "item.started":
            # Tracked only so a truncated run can show what was in flight when
            # it died -- otherwise an INCOMPLETE digest reports "Commands: 0".
            item = event.get("item")
            itype = item.get("type") if isinstance(item, dict) else None
            if isinstance(itype, str):
                label = item.get("command") or itype
                d["in_flight"].append(
                    {"type": itype, "ident": _identity(item), "label": str(label)}
                )
            else:
                d["unmodeled_lines"] += 1
        elif etype != "item.updated":
            # `item.updated` is a known no-op for this parser. Anything else is
            # an envelope type we don't model -- count it rather than dropping
            # it silently, which is the principle applied to item types below.
            d["unmodeled_lines"] += 1

    # Reconcile started against completed in two passes. Pass 1 matches exact
    # (type, id) so concurrent items of the same type are told apart -- codex
    # runs tool calls in parallel, so "the second one finished first" is normal.
    # Pass 2 sweeps up whatever is left using per-type counts, which covers
    # id-less items, ids reused across turns, and starts whose completion
    # reported a different id. Every completed item is counted, including types
    # the digest doesn't model, or a clean run would report them as hung.
    by_id = dict(d.pop("_done_ids", {}))
    by_type = dict(d.pop("_done_types", {}))
    survivors = []
    for started in d["in_flight"]:
        ident = started["ident"]
        if ident is not None and by_id.get(ident, 0) > 0:
            by_id[ident] -= 1
            by_type[started["type"]] = by_type.get(started["type"], 0) - 1
            continue
        survivors.append(started)
    remaining = []
    for started in survivors:
        if by_type.get(started["type"], 0) > 0:
            by_type[started["type"]] -= 1
            continue
        remaining.append(started)
    d["in_flight"] = remaining
    return d


def _identity(item):
    """(type, id) when the item carries a usable scalar id, else None.

    Ids are imperfect -- they restart per turn and repeat across types -- so
    they are used as a *hint*, with a per-type count as the fallback. Neither
    alone is sufficient: matching only by id mishandles id-less and reused ids,
    and matching only by count cannot tell two concurrent commands apart.
    """
    itype = item.get("type")
    if not isinstance(itype, str):
        return None
    iid = item.get("id")
    if isinstance(iid, bool) or not isinstance(iid, (str, int)):
        return None
    return (itype, str(iid))


def _collect_item(d, item):
    itype = item.get("type")
    if isinstance(itype, str):
        d["_done_types"][itype] = d["_done_types"].get(itype, 0) + 1
        ident = _identity(item)
        if ident is not None:
            d["_done_ids"][ident] = d["_done_ids"].get(ident, 0) + 1

    if itype == "agent_message":
        text = item.get("text")
        # Keep empty strings: an empty final message must not silently promote
        # an earlier progress note to "the answer".
        if isinstance(text, str):
            d["messages"].append(text)
    elif itype == "command_execution":
        d["commands"].append(
            {
                "id": item.get("id"),
                "command": str(item.get("command", "")),
                "exit_code": _as_exit_code(item.get("exit_code")),
                "output": item.get("aggregated_output") if isinstance(item.get("aggregated_output"), str) else "",
            }
        )
    elif itype == "file_change":
        changes = item.get("changes")
        if isinstance(changes, list):
            for change in changes:
                if isinstance(change, dict):
                    d["file_changes"].append(
                        {
                            "id": item.get("id"),
                            "path": str(change.get("path", "")),
                            "kind": str(change.get("kind", "?")),
                        }
                    )
    elif itype == "error":
        # NOT a run failure: a successful run can carry an item-level error
        # (e.g. "Model metadata for X not found. Defaulting to fallback").
        # Only turn.failed and a top-level `error` event decide the status.
        msg = item.get("message")
        d["warnings"].append(msg if isinstance(msg, str) else item)
    elif isinstance(itype, str):
        # Item types this build emits that the digest doesn't model
        # (reasoning, mcp_tool_call, web_search, todo_list). Counting them
        # beats silently dropping them.
        d["other_items"][itype] = d["other_items"].get(itype, 0) + 1
    else:
        d["unmodeled_lines"] += 1


def _as_exit_code(value):
    """Coerce to int or None. A string "0" must not read as a failure."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def truncate_output(text, full=False):
    if not isinstance(text, str) or not text:
        return []
    lines = text.rstrip("\n").split("\n")
    if full:
        return lines
    shown = []
    for ln in lines[:OUTPUT_HEAD_LINES]:
        shown.append(ln if len(ln) <= OUTPUT_LINE_CHARS else ln[:OUTPUT_LINE_CHARS] + " …[truncated]")
    hidden = len(lines) - OUTPUT_HEAD_LINES
    if hidden > 0:
        shown.append(f"… {hidden} more line(s)")
    return shown


def status_of(d):
    # A stream with neither turn.completed nor turn.failed was cut off -- killed
    # by a timeout, or still running. Reporting that as success is the most
    # dangerous thing this script could do, so it gets its own status.
    if d["failed"]:
        return "FAILED"
    if d["completed"]:
        return "completed"
    return "INCOMPLETE"


def render(d, full_output=False):
    out = []
    # exit_code None means the command never reported one (interrupted), which
    # is not success -- count it separately rather than letting it read as fine.
    failed_cmds = [c for c in d["commands"] if c["exit_code"] not in (0, None)]
    unfinished_cmds = [c for c in d["commands"] if c["exit_code"] is None]

    status = status_of(d)
    if status == "INCOMPLETE":
        status = "INCOMPLETE — no turn.completed event (run truncated, killed, or still in progress)"
    out.append(f"=== Codex run: {status} ===")
    if d["thread_id"]:
        out.append(f"session: {d['thread_id']}   (resume: codex exec resume {d['thread_id']})")

    if d["errors"]:
        out.append("")
        out.append("Errors:")
        for err in d["errors"]:
            out.append(f"  {err if isinstance(err, str) else json.dumps(err)}")

    if d["superseded_errors"]:
        out.append("")
        out.append("Errors from an earlier turn that a later turn superseded:")
        for err in d["superseded_errors"]:
            out.append(f"  {err if isinstance(err, str) else json.dumps(err)}")

    if d["warnings"]:
        out.append("")
        out.append("Warnings (not failures):")
        for warn in d["warnings"]:
            out.append(f"  {warn if isinstance(warn, str) else json.dumps(warn)}")

    out.append("")
    counts = (
        f"Commands: {len(d['commands'])} ({len(failed_cmds)} non-zero"
        + (f", {len(unfinished_cmds)} unfinished" if unfinished_cmds else "")
        + f")   Files changed: {len(d['file_changes'])}   Messages: {len(d['messages'])}"
    )
    out.append(counts)
    if d["other_items"]:
        summary = ", ".join(f"{k}={v}" for k, v in sorted(d["other_items"].items()))
        out.append(f"Other items: {summary}")
    if d["malformed_lines"]:
        out.append(f"WARNING: {d['malformed_lines']} unparseable line(s) — stream may be truncated.")
    if d["unmodeled_lines"]:
        out.append(f"Note: {d['unmodeled_lines']} event(s) in an unrecognized shape were skipped.")

    # A hung *command* is the real signal, so it is shown unconditionally --
    # it matters most on a run that otherwise looks clean. Other item types are
    # only reported when the run didn't finish: their completion events aren't
    # fully characterised, so an unmatched one on a successful run is more
    # likely a gap in this parser than a real hang.
    cmds = [s for s in d["in_flight"] if s["type"] == "command_execution"]
    others = {}
    if status_of(d) != "completed":
        for s2 in d["in_flight"]:
            if s2["type"] != "command_execution":
                others[s2["type"]] = others.get(s2["type"], 0) + 1
    if cmds or others:
        out.append("")
        out.append("--- Started, no completion seen ---")
        for started in cmds:
            out.append(f"  {started['label']}")
        if others:
            out.append("  " + ", ".join(f"{v}x {k}" for k, v in sorted(others.items())))

    if d["file_changes"]:
        out.append("")
        out.append("--- Files changed ---")
        for change in d["file_changes"]:
            out.append(f"  {change['kind']:<7} {change['path']}")

    if d["commands"]:
        out.append("")
        out.append("--- Commands ---")
        for cmd in d["commands"]:
            code = cmd["exit_code"]
            marker = " " if code == 0 else "!"
            out.append(f"{marker} [{'--' if code is None else code}] {cmd['command']}")
            # Failures always show output; successes only with --full-output,
            # since successful command output is rarely why you read a digest.
            if marker == "!" or full_output:
                for ln in truncate_output(cmd["output"], full_output):
                    out.append(f"      {ln}")

    out.append("")
    out.append("--- Final message ---")
    if d["messages"]:
        # Only the last agent_message is the result. The earlier ones are
        # progress narration and read deceptively like conclusions.
        out.append(d["messages"][-1] or "(empty)")
        if len(d["messages"]) > 1:
            out.append("")
            out.append(f"({len(d['messages']) - 1} earlier progress message(s) omitted)")
    else:
        out.append("(none — the run produced no agent message, which usually means it failed)")

    if d["usage"]:
        u = d["usage"]
        out.append("")
        out.append(
            "Tokens: in={} (cached {}) out={} reasoning={}".format(
                u.get("input_tokens", "?"),
                u.get("cached_input_tokens", "?"),
                u.get("output_tokens", "?"),
                u.get("reasoning_output_tokens", "?"),
            )
        )

    return "\n".join(out)


def as_json(d, full_output=False):
    """JSON form of the digest.

    Command output is truncated here too unless --full-output is passed --
    otherwise this returns the raw noise the script exists to remove.
    """
    payload = dict(d)
    payload["status"] = status_of(d)
    payload["final_message"] = d["messages"][-1] if d["messages"] else None
    # Same gate as the text renderer: a hung *command* always matters, but other
    # item types have unconfirmed completion-event shapes and false-positive on
    # clean runs. Applying it in only one renderer made the two disagree.
    visible = [i for i in d["in_flight"]
               if i["type"] == "command_execution" or status_of(d) != "completed"]
    payload["in_flight"] = [{"type": i["type"], "label": i["label"]} for i in visible]
    payload["commands"] = [
        {**c, "output": "\n".join(truncate_output(c["output"], full_output))} for c in d["commands"]
    ]
    # Narration is available via the count; carrying every progress message
    # defeats the point of a digest. Emit the key unconditionally so consumers
    # see a stable schema regardless of flags.
    payload["omitted_messages"] = 0 if full_output else max(0, len(d["messages"]) - 1)
    if not full_output:
        payload["messages"] = d["messages"][-1:]
    return payload


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file", nargs="?", help="JSONL file; reads stdin when omitted")
    ap.add_argument(
        "--full-output",
        action="store_true",
        help="include output for successful commands, and don't truncate",
    )
    ap.add_argument("--json", dest="as_json", action="store_true", help="emit digest as JSON")
    args = ap.parse_args()

    if args.file:
        try:
            # errors="replace": a run killed mid-write can split a multi-byte
            # character, and crashing on that defeats the whole point of
            # digesting a truncated stream.
            with open(args.file, encoding="utf-8", errors="replace") as fh:
                digest = parse_stream(fh)
        except OSError as exc:
            print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
            return 2
    else:
        if sys.stdin.isatty():
            ap.error("no input: pass a file or pipe `codex exec --json` output")
        stream = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
        digest = parse_stream(stream)

    if args.as_json:
        print(json.dumps(as_json(digest, args.full_output), indent=2))
    else:
        print(render(digest, full_output=args.full_output))

    return 0 if digest["completed"] and not digest["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
