#!/usr/bin/env python3
"""Condense a `codex exec --json` event stream into a short digest.

Raw JSONL from a real Codex run is long and mostly noise: progress narration,
full command output, duplicated started/completed pairs. Reading it directly
wastes context. This prints what you actually need to judge the run — what it
ran, what it changed, what it concluded, what it cost.

Usage:
    python3 codex_digest.py run.jsonl
    codex exec --json "<task>" < /dev/null | python3 codex_digest.py

Options:
    --full-output   Don't truncate captured command output.
    --json          Emit the digest as JSON instead of text.

Exit status is 0 only for a run that reached `turn.completed` without errors.
A failed run, or one whose stream was cut off (timeout, kill), exits 1 — so it
can gate a pipeline directly.
"""

import argparse
import json
import sys

# Command output is merged stdout+stderr and can run to thousands of lines.
# Enough to see what happened, not enough to flood a context window.
OUTPUT_HEAD_LINES = 8
OUTPUT_LINE_CHARS = 200


def parse_stream(lines):
    """Fold a JSONL event stream into a digest dict.

    Malformed lines are collected rather than raised on: a truncated run (killed
    by a timeout, say) is exactly when you most want to see the partial digest.
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
        "malformed_lines": 0,
        "other_items": [],
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

        if etype == "thread.started":
            d["thread_id"] = event.get("thread_id")
        elif etype == "turn.completed":
            d["completed"] = True
            d["usage"] = event.get("usage")
        elif etype == "turn.failed":
            d["failed"] = True
            # Shape of the failure payload isn't guaranteed; keep it verbatim.
            if event.get("error") is not None:
                d["errors"].append(event["error"])
        elif etype == "error":
            d["failed"] = True
            d["errors"].append(event.get("message") or event.get("error") or event)
        elif etype == "item.completed":
            # Only completed items carry full payloads; item.started duplicates
            # them with null exit codes and empty output.
            _collect_item(d, event.get("item") or {})

    return d


def _collect_item(d, item):
    itype = item.get("type")

    if itype == "agent_message":
        text = item.get("text")
        if text:
            d["messages"].append(text)
    elif itype == "command_execution":
        d["commands"].append(
            {
                "command": item.get("command", ""),
                "exit_code": item.get("exit_code"),
                "output": item.get("aggregated_output", ""),
            }
        )
    elif itype == "file_change":
        for change in item.get("changes") or []:
            d["file_changes"].append(
                {"path": change.get("path", ""), "kind": change.get("kind", "?")}
            )
    elif itype:
        # Item types this build emits that the script doesn't model yet
        # (reasoning, mcp_tool_call, web_search, plan updates). Surfacing the
        # count beats silently dropping them.
        d["other_items"].append(itype)


def truncate_output(text, full=False):
    if not text:
        return []
    lines = text.rstrip("\n").split("\n")
    if full:
        return lines
    shown = [ln[:OUTPUT_LINE_CHARS] for ln in lines[:OUTPUT_HEAD_LINES]]
    hidden = len(lines) - OUTPUT_HEAD_LINES
    if hidden > 0:
        shown.append(f"… {hidden} more line(s)")
    return shown


def render(d, full_output=False):
    out = []
    failed_cmds = [c for c in d["commands"] if c["exit_code"] not in (0, None)]

    # A stream with neither turn.completed nor turn.failed was cut off — killed
    # by a timeout, or still running. Reporting that as success is the most
    # dangerous thing this script could do, so it gets its own status.
    if d["failed"]:
        status = "FAILED"
    elif d["completed"]:
        status = "completed"
    else:
        status = "INCOMPLETE — no turn.completed event (run truncated, killed, or still in progress)"
    out.append(f"=== Codex run: {status} ===")
    if d["thread_id"]:
        out.append(f"session: {d['thread_id']}   (resume: codex exec resume {d['thread_id']})")

    if d["errors"]:
        out.append("")
        out.append("Errors:")
        for err in d["errors"]:
            out.append(f"  {json.dumps(err) if not isinstance(err, str) else err}")

    out.append("")
    out.append(
        f"Commands: {len(d['commands'])} ({len(failed_cmds)} non-zero)   "
        f"Files changed: {len(d['file_changes'])}   "
        f"Messages: {len(d['messages'])}"
    )
    if d["other_items"]:
        counts = {}
        for name in d["other_items"]:
            counts[name] = counts.get(name, 0) + 1
        summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        out.append(f"Other items: {summary}")
    if d["malformed_lines"]:
        out.append(f"WARNING: {d['malformed_lines']} unparseable line(s) — stream may be truncated.")

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
            marker = " " if code in (0, None) else "!"
            out.append(f"{marker} [{code}] {cmd['command']}")
            # Only expand output for failures; successful command output is
            # rarely why you're reading a digest.
            if marker == "!":
                for ln in truncate_output(cmd["output"], full_output):
                    out.append(f"      {ln}")

    out.append("")
    if d["messages"]:
        # Only the last agent_message is the result. The earlier ones are
        # progress narration and read deceptively like conclusions.
        out.append("--- Final message ---")
        out.append(d["messages"][-1])
        if len(d["messages"]) > 1:
            out.append("")
            out.append(f"({len(d['messages']) - 1} earlier progress message(s) omitted)")
    else:
        out.append("--- Final message ---")
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


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file", nargs="?", help="JSONL file; reads stdin when omitted")
    ap.add_argument("--full-output", action="store_true", help="don't truncate command output")
    ap.add_argument("--json", dest="as_json", action="store_true", help="emit digest as JSON")
    args = ap.parse_args()

    if args.file:
        try:
            with open(args.file, encoding="utf-8") as fh:
                digest = parse_stream(fh)
        except OSError as exc:
            print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
            return 2
    else:
        if sys.stdin.isatty():
            ap.error("no input: pass a file or pipe `codex exec --json` output")
        digest = parse_stream(sys.stdin)

    if args.as_json:
        digest["final_message"] = digest["messages"][-1] if digest["messages"] else None
        print(json.dumps(digest, indent=2))
    else:
        print(render(digest, full_output=args.full_output))

    # Incomplete counts as failure: a truncated run must not gate a pipeline green.
    return 0 if digest["completed"] and not digest["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
