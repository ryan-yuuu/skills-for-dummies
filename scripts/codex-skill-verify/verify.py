#!/usr/bin/env python3
"""Verification harness for the `codex` skill.

Exists because two failure modes bit repeatedly during development:

  1. A str.replace() whose target string did not exist silently did nothing,
     and the fix was reported as applied. Three rounds in a row.
  2. A test harness passed flags as one unquoted string; zsh does not
     word-split parameter expansions, so the flag never reached the binary and
     produced a confident but wrong refutation.

So: `edit()` refuses to no-op, and `sh()` takes an argv list, never a string.
Run this after every change. Exit 0 means every claim still holds.
"""

import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

SKILL = pathlib.Path(__file__).resolve().parents[2] / "skills" / "codex"
FAILS = []


def check(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(label)
    return cond


def edit(path, old, new, *, expect=1):
    """Replace `old` with `new`, refusing to silently do nothing.

    Raises unless `old` occurs exactly `expect` times and `new` is present
    afterwards. This is the guard the development process lacked.
    """
    p = pathlib.Path(path)
    text = p.read_text()
    n = text.count(old)
    if n != expect:
        raise AssertionError(f"{p.name}: expected {expect} occurrence(s) of {old[:60]!r}, found {n}")
    updated = text.replace(old, new)
    if new and new not in updated:
        raise AssertionError(f"{p.name}: replacement not present after edit")
    p.write_text(updated)
    return n


def sh(argv, **kw):
    """Run a command from an argv LIST. Never accept a string: a string would
    be word-split by bash and not by zsh, which is the bug that produced a
    wrong refutation during development."""
    assert isinstance(argv, (list, tuple)), "pass argv as a list, not a string"
    return subprocess.run(list(argv), capture_output=True, text=True, **kw)


# ---------------------------------------------------------------- self-test
def self_test():
    """The harness must itself be free of the quoting bug it guards against."""
    print("=== harness self-test ===")
    probe = "printf 'argc=%d' \"$#\""
    for shell in ("bash", "zsh"):
        r = subprocess.run([shell, "-c", f'set -- -s danger-full-access; {probe}'],
                           capture_output=True, text=True)
        check(f"{shell}: argv list keeps flags separate", r.stdout.strip() == "argc=2", r.stdout)
    # edit() must refuse a no-op
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
        fh.write("hello world"); tmp = fh.name
    try:
        edit(tmp, "NOT PRESENT", "x")
        check("edit() refuses a no-op replacement", False, "did not raise")
    except AssertionError:
        check("edit() refuses a no-op replacement", True)
    finally:
        os.unlink(tmp)


# ---------------------------------------------------------------- docs
def docs():
    F = {p.name: p.read_text() for p in [SKILL / "SKILL.md"] + sorted((SKILL / "references").glob("*.md"))}
    ALL = "\n".join(F.values())
    print("=== documented facts (each was a verified finding) ===")
    check("no $MF anti-pattern in a runnable example", not re.search(r'^\s*codex exec \$MF', ALL, re.M))
    check("no stale skill name", "codex-non-interactive" not in ALL)
    check("resume: no 'inherits' survivor", not re.search(r'inherits the original session', ALL))
    check("trust keyed on git repo root", "git repo root" in F["flags.md"])
    check("trust matching is exact, not a prefix walk", "not a prefix walk" in F["flags.md"])
    check("worktree trusts the MAIN repo", "main repo" in F["patterns.md"].lower())
    check("no bare `git reset` in any recipe", not re.search(r'^git reset\s*(#|$)', ALL, re.M))
    check("throwaway git index used", "GIT_INDEX_FILE" in ALL)
    check("worktree diffs against BASE", 'BASE=$(git rev-parse HEAD)' in F["patterns.md"])
    check("no `diff main` in worktree recipe", not re.search(r'codex-wt diff main', ALL))
    check("exit code 2 documented in flags.md", "`2` on argument-parse failure" in F["flags.md"])
    check("review does not claim to write trust", "review` writes a project trust entry" not in ALL)
    check("danger-full-access flips web access", "danger-full-access" in F["flags.md"] and "external_web_access" in F["flags.md"])
    check("codex cloud listed as interactive", "codex cloud`" in F["SKILL.md"])
    check("--last does not make resume safe", "--last` does not help" in F["SKILL.md"])
    check("approval line described as unreliable", "approvals_reviewer" in F["SKILL.md"])
    # round 7
    check("stage 1 failure is checked before resuming",
          "codex_digest.py\" stage1.jsonl" in F["patterns.md"])
    check("resume isolation warning PRECEDES the recipe",
          F["patterns.md"].index("cannot be isolated") < F["patterns.md"].index("SESSION=$(jq"))
    check("stage 2 example defaults to read-only",
          'resume "$SESSION" "${MODEL[@]}" -c sandbox_mode=\'"read-only"\'' in F["patterns.md"])
    check("review recipe guards an empty diff", '[ -s "$DIFF" ]' in ALL)
    check("review output does not land in the user repo",
          "${TMPDIR:-/tmp}/review.md" in ALL and "> review.md" not in ALL)
    check("SKILL.md points at the relocated review recipe",
          "reviewing-a-working-diff" in F["SKILL.md"])
    check("Implement example points at the canonical worktree recipe",
          "worktree-isolation" in F["SKILL.md"] and "git worktree add" not in F["SKILL.md"])
    check("SKILL_DIR derivation does not use the broken find",
          "find ~ -name SKILL.md" not in F["SKILL.md"] and 'ls "$SKILL_DIR/scripts' in F["SKILL.md"])
    check("no `git diff main` recommended anywhere",
          "git diff main" not in "\n".join(F.values()))
    check("CI uses a throwaway index, not the real one",
          "GIT_INDEX_FILE" in F["patterns.md"])
    check("CI empty-patch uses if, not an AND-list",
          '[ -s codex.patch ] &&' not in F["patterns.md"])
    check("resume not called a 'session picker' in the flag table",
          "session picker (`codex resume`)" not in F["SKILL.md"])
    # round 7 CLI
    check("trust write scoped to session creation, not 'any run'",
          "creates a session" in F["flags.md"] and "Any run whose sandbox resolves" not in F["flags.md"])
    check("resuming does not write trust (stated)",
          "resuming a session does not write one" in F["flags.md"].lower()
          or "does not write one" in F["flags.md"])
    check("codex cloud subcommands noted as non-interactive",
          "codex cloud exec" in F["SKILL.md"])
    check("web_search evidence class stated", "wire_api=responses" in F["flags.md"])

    print("=== superseded claims must not survive ===")
    for label, pat in [("web search on by default", r"web search is on by default"),
                       ("--full-auto equivalence", r"only observable difference"),
                       ("matching is symmetric", r"symmetric with the write"),
                       ("read-only is simply the default", r"It's also the default"),
                       ("always reads never", r"always reads `never`")]:
        check(f"no survivor: {label}", not re.search(pat, ALL, re.I))

    print("=== structure ===")
    total = bad = 0
    for name, text in F.items():
        check(f"{name}: fences balanced", text.count("```") % 2 == 0)
        for b in re.findall(r"```bash\n(.*?)```", text, re.S):
            total += 1
            src = ("SKILL_DIR=/tmp; MODEL=(-m x); CODEX_MODEL=x; CODEX_EFFORT=x; SESSION=s;"
                   " RESUMED=s; BASE=h; TMPIDX=/tmp/i; OPENAI_API_KEY=k\n") + b
            with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as fh:
                fh.write(src); path = fh.name
            for shell in ("bash", "zsh"):
                if sh([shell, "-n", path]).returncode:
                    bad += 1
            os.unlink(path)
    check(f"all {total} bash blocks parse in bash+zsh", bad == 0, f"{bad} failures")

    def cells(row):
        i = row.strip()
        if i.startswith("|"): i = i[1:]
        if i.endswith("|"): i = i[:-1]
        return len(re.split(r'(?<!\\)\|', i))
    broken = 0
    for name, text in F.items():
        infence = False; block = []
        for ln in text.split("\n"):
            if ln.strip().startswith("```"): infence = not infence; continue
            if infence: continue
            if ln.strip().startswith("|"): block.append(ln)
            else:
                if len(block) > 1 and len(set(map(cells, block))) > 1: broken += 1
                block = []
        if len(block) > 1 and len(set(map(cells, block))) > 1: broken += 1
    check("no broken markdown tables", broken == 0, f"{broken}")

    def slug(h):
        h = h.lower().replace('`', '')
        return re.sub(r'[^a-z0-9 _-]', '', h).replace(' ', '-')
    heads = {n: {slug(h) for h in re.findall(r'^#{2,3} (.+)$', t, re.M)} for n, t in F.items()}
    nb = 0
    for name, text in F.items():
        for _, target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text):
            if target.startswith('#'):
                if target[1:] not in heads[name]: nb += 1
            elif '#' in target and not target.startswith('http'):
                path, anc = target.split('#', 1)
                base = os.path.basename(path)
                if base in heads and anc not in heads[base]: nb += 1
    check("all anchors resolve", nb == 0, f"{nb} broken")

    r = sh(["python3", str(pathlib.Path(__file__).resolve().parents[2] / ".claude/skills/skill-creator/scripts/quick_validate.py"), str(SKILL)])
    check("quick_validate passes", "Skill is valid!" in r.stdout, r.stdout.strip() + r.stderr.strip())


# ---------------------------------------------------------------- scripts
def scripts():
    print("=== codex_digest.py behaviour (cases from rounds 2-6) ===")
    D = str(SKILL / "scripts/codex_digest.py")

    def run(lines, *flags):
        r = subprocess.run(["python3", D, *flags], input="\n".join(lines), capture_output=True, text=True)
        return r.stdout, r.returncode

    cmd = lambda i, c, **k: json.dumps({"type": k.get("ev", "item.started"),
                                        "item": {"id": i, "type": "command_execution", "command": c, **k.get("extra", {})}})
    done = lambda: json.dumps({"type": "turn.completed", "usage": {}})

    out, _ = run([cmd("A", "sleep 999"), cmd("B", "echo quick"),
                  cmd("B", "echo quick", ev="item.completed", extra={"exit_code": 0})])
    check("concurrent same-type, 2nd finishes first", "sleep 999" in out.split("no completion seen")[-1])

    out, rc = run(['{"type":"turn.started"}', done(), '{"type":"turn.started"}', cmd("c", "hung")])
    check("multi-turn cut mid-turn-2 -> INCOMPLETE", "INCOMPLETE" in out and rc == 1)

    out, rc = run(['{"type":"turn.started"}', cmd("1", "rm -rf /tmp/scratch"),
                   json.dumps({"type": "item.completed", "item": {"id": "9", "type": "agent_message", "text": "Done"}}),
                   done()])
    check("destructive started-cmd visible on a clean run", "rm -rf /tmp/scratch" in out)

    out, _ = run([json.dumps({"type": "item.completed", "item": {"id": "i", "type": ["a"]}}), done()])
    check("non-hashable item type does not crash", "Traceback" not in out)

    out, rc = run([json.dumps({"type": "item.completed", "item": {"id": "e", "type": "error", "message": "meta"}}),
                   json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}}), done()])
    check("warning item does not fail the run", rc == 0)

    out, _ = run([json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "first"}}),
                  json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "LAST"}}), done()])
    check("last agent_message wins", out.split("Final message ---")[1].strip().startswith("LAST"))

    out, _ = run([done()], "--json")
    check("no internal keys in --json", "_done_" not in out and '"ident"' not in out)

    # round 8
    import json as _json
    out, _ = run(['{"type":"turn.started"}',
                  json.dumps({"type":"item.started","item":{"type":"reasoning","id":"r"}}),
                  json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"ok"}}),
                  done()], "--json")
    check("--json applies the same in-flight gate as text",
          _json.loads(out)["in_flight"] == [])
    r = sh(["python3", str(SKILL / "scripts/codex_pick_model.py"), "--model", ""])
    check("--model '' is rejected, not silently auto-selected", r.returncode != 0)

    # round 9: rankability lived in two places and the display copy went stale
    import tempfile as _tf, os as _os, stat as _st
    d = _tf.mkdtemp(); fk = _os.path.join(d, "codex")
    open(fk, "w").write("#!/bin/sh\necho '" + json.dumps({"models":[
        {"slug":"strong","visibility":"list","priority":1.0,"supported_reasoning_levels":[{"effort":"high"}]},
        {"slug":"weak","visibility":"list","priority":2,"supported_reasoning_levels":[{"effort":"high"}]}]}) + "'\n")
    _os.chmod(fk, 0o755)
    env = dict(_os.environ); env["PATH"] = d + _os.pathsep + env["PATH"]
    r = subprocess.run(["python3", str(SKILL / "scripts/codex_pick_model.py"), "--list"],
                       capture_output=True, text=True, env=env)
    check("--list PRIO column agrees with the sort (float priority)",
          r.stdout.splitlines()[1].split()[0] == "1", r.stdout)
    r = subprocess.run(["python3", str(SKILL / "scripts/codex_pick_model.py"), "--slug-only"],
                       capture_output=True, text=True, env=env)
    check("float priority selects the stronger model", r.stdout.strip() == "strong", r.stdout)

    print("=== codex_pick_model.py ===")
    P = str(SKILL / "scripts/codex_pick_model.py")
    r = sh(["python3", P])
    check("real catalog resolves", r.returncode == 0 and r.stdout.startswith("-m "), r.stdout.strip())
    r = sh(["python3", P, "--model", "gpt-5.5", "--effort", "ultra"])
    check("effort resolves DOWN, never up", "model_reasoning_effort=xhigh" in r.stdout, r.stdout.strip())
    r = sh(["python3", P, "--slug-only", "--export"])
    check("output modes mutually exclusive", r.returncode == 2)
    for f in (SKILL / "scripts").glob("*.py"):
        check(f"{f.name} compiles", sh(["python3", "-m", "py_compile", str(f)]).returncode == 0)


if __name__ == "__main__":
    self_test(); docs(); scripts()
    print(f"\n{'FAILURES: ' + str(len(FAILS)) if FAILS else 'ALL CHECKS PASS'}")
    for f in FAILS:
        print("  - " + f)
    sys.exit(1 if FAILS else 0)
