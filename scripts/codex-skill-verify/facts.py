#!/usr/bin/env python3
"""Fact inventory for the `codex` skill — the no-information-loss safety net.

Built BEFORE the consolidation pass. Each entry is a load-bearing claim that
must survive pruning SOMEWHERE in the skill. The point is not where it lives —
consolidation deliberately moves things — but that it still exists.

Run before and after pruning. Any fact that disappears is information loss.
"""

import pathlib
import re
import sys

SKILL = pathlib.Path(__file__).resolve().parents[2] / "skills" / "codex"

# (label, regex that must match somewhere in the skill's prose)
FACTS = [
    # --- when/whether to delegate ---
    ("delegation costs quota + wall clock", r"quota and real wall-clock"),
    ("don't delegate what you can do directly", r"poor trade for anything you can\s+do directly"),
    # --- what hangs ---
    ("bare codex / resume / fork / cloud open a UI", r"`codex resume`,\s*\n?`codex fork`, and `codex cloud`"),
    ("--last skips picker but still opens UI", r"--last` does not help"),
    ("codex app is a desktop GUI", r"codex app` launches the desktop GUI"),
    ("dropping exec from exec resume hangs", r"dropping `exec` from `codex exec resume`"),
    ("non-interactive command list", r"codex cloud` that\s*\n?opens the TUI|codex cloud exec"),
    # --- preconditions ---
    ("codex must be installed + authed", r"codex --version && codex login status"),
    ("codex doctor diagnoses env", r"codex doctor` diagnoses"),
    ("git repo required, exact message", r"Not inside a trusted\s*\n?directory"),
    ("SKILL_DIR is this skill's directory", r"SKILL_DIR"),
    ("-C sets the working root", r"-C/--cd <DIR>`, which sets the agent's working root"),
    # --- the invocation contract ---
    ("stdout = final message only", r"\*\*stdout\*\* — the final agent message"),
    ("stderr = header + transcript", r"\*\*stderr\*\* — the run header"),
    ("exit 0/1/2", r"`2` on argument-parse failure|`2` when a flag is\s*\n?rejected"),
    ("stdin read as extra context; < /dev/null", r"reads stdin as \*additional context\*"),
    ("-i is variadic and swallows the prompt", r"variadic"),
    ("--ephemeral doesn't persist a session", r"[Dd]oesn't persist a session|Don't persist session files"),
    # --- model + effort ---
    ("model default comes from config.toml", r"comes from the user's `config.toml`"),
    ("top model's own default effort is low", r"`default_reasoning_level`"),
    ("no --effort flag", r"no `--effort` flag"),
    ("don't hardcode a slug", r"Don't hardcode a model slug"),
    ("codex debug models lists the catalog", r"codex debug models"),
    ("effort ladder incl. minimal..ultra", r"minimal.*low.*medium.*high.*xhigh.*max.*ultra"),
    ("default to xhigh", r"\*\*Default to `xhigh`\*\*"),
    ("ultra delegates sub-tasks", r"delegate sub-tasks"),
    ("zsh doesn't word-split parameter expansions", r"parameter\s*\n?expansion doesn't word-split|does not word-split"),
    ("--export for resolve-once", r"--export"),
    ("header shows RESOLVED value", r"shows the \*\*resolved\*\* value"),
    ("--json suppresses the header", r"`--json` suppresses"),
    ("unknown -c keys accepted silently; --strict-config", r"--strict-config"),
    # --- acceptance bar + prompting ---
    ("write acceptance criteria before delegating", r"before the call goes out at all"),
    ("bar goes into the prompt AND is the checklist", r"double duty"),
    ("don't lower the bar after the fact", r"don't quietly lower the bar"),
    ("codex starts cold", r"empty room and a\s*\n?repository|starts cold"),
    ("codex cannot ask a clarifying question", r"cannot ask a clarifying question"),
    ("prompt must carry goal/paths/criteria/shape/boundaries", r"\*\*The concrete goal\*\*"),
    # --- sandbox ---
    ("three sandbox modes", r"danger-full-access"),
    ("exec has no approval flag; sandbox is the boundary", r"sandbox is the entire\s*\n?safety boundary"),
    ("trust silently changes the default sandbox", r"[Pp]roject trust silently changes the default sandbox"),
    ("codex WRITES the trust entry on session creation", r"writes the trust entry itself"),
    ("trust keyed on git repo root", r"git repo root"),
    ("resuming does not write trust", r"resuming a session does not write one"),
    ("--ephemeral/--ignore-user-config don't prevent the write", r"[Nn]either\s*\n?`--ephemeral` nor `--ignore-user-config` prevents"),
    ("matching broader than writing; exact, not prefix", r"not a prefix walk"),
    ("worktree trusts the MAIN repo", r"worktree resolves to its main repo's root|worktree does not contain this"),
    ("workspace-write blocks network by default", r"blocks network access by default|blocks network by default"),
    ("network_access=true enables it", r"sandbox_workspace_write\.network_access=true"),
    ("--add-dir instead of full access", r"--add-dir"),
    ("review and resume reject -s; use -c sandbox_mode", r"sandbox_mode="),
    ("resume does not inherit sandbox/model/effort", r"does \*not\* inherit the original|don't carry"),
    ("resume can silently start fresh and exit 0", r"silently start a fresh session|silent-success trap"),
    ("piped content is untrusted", r"[Tt]reat piped-in content as untrusted|untrusted input"),
    ("web_search is not containment", r"web_search"),
    ("don't give workspace-write on a repo you're editing", r"do not give Codex `workspace-write` on it"),
    ("--dangerously-bypass removes the boundary", r"dangerously-bypass-approvals-and-sandbox"),
    # --- shapes ---
    ("review targets are mutually exclusive", r"[Tt]argets are mutually exclusive"),
    ("target flag + prompt cannot combine", r"target flag and a prompt can't be combined"),
    ("--title only with --commit", r"--title` only applies with `--commit`"),
    ("--output-schema takes a file path", r"takes a file path|takes a \*\*file path\*\*"),
    ("throwaway index protects the user's staging", r"GIT_INDEX_FILE"),
    ("empty diff guard", r"no uncommitted changes to review"),
    # --- long runs / parallelism ---
    ("runs take minutes; background or raise timeout", r"takes \*\*minutes\*\*|runs for minutes"),
    ("two mechanisms: harness backgrounding vs & wait", r"run_in_background"),
    ("parallelism multiplies cost", r"Parallelism multiplies cost"),
    ("concurrent writers collide", r"Concurrent writers collide"),
    ("always redirect to files", r"Always redirect to files"),
    ("bare wait returns 0 even when all fail", r"bare `wait` returns `0`|Bare `wait` returns"),
    ("digest reports INCOMPLETE mid-flight", r"INCOMPLETE"),
    # --- verification ---
    ("self-report is not evidence", r"self-report is not\s*\n?evidence"),
    ("read the diff and run tests yourself", r"read the diff and run the tests yourself"),
    ("spot-check findings against files", r"spot-check specific claims"),
    ("relay Codex's conclusions as Codex's", r"Relay Codex's conclusions"),
    # --- REMEDIES ---------------------------------------------------------
    # Added after a consolidation pass deleted the only stated fix for a
    # problem the skill still raised, while this inventory reported 0 missing.
    # It tracked the CLAIM ("--json suppresses the header") but not the
    # GUIDANCE that resolved it. A hazard with no remedy is worse than silence:
    # it tells an agent to worry and not what to do.
    ("remedy: confirm flags under --json via a plain run or the picker",
     r"throwaway plain run|prints exactly what it resolved"),
    ("remedy: get criteria into a review via bare prompt or piped diff",
     r"bare-prompt form and describe the scope yourself"),
    ("remedy: --strict-config catches a mistyped -c key", r"--strict-config"),
    ("remedy: isolate write work in a worktree", r"worktree-isolation"),
    ("remedy: assert the resumed thread id", r"RESUMED"),
    ("remedy: collect PIDs instead of a bare wait", r"[Cc]apture each PID"),
    ("remedy: -c sandbox_mode where -s is rejected", r"sandbox_mode='\"read-only\"'"),
    ("remedy: network_access flag when tests need the network",
     r"sandbox_workspace_write\.network_access=true"),
    ("remedy: throwaway index protects staging", r"GIT_INDEX_FILE"),
    ("remedy: codex doctor for environmental failure", r"codex doctor"),
    ("remedy: codex update when the binary is stale", r"codex update"),
    ("remedy: fall back to no -m if the catalog shape changes",
     r"guessing a slug"),
    # --- currency ---
    ("codex update is safe to run", r"codex update` is safe"),
    ("--help beats this file; some flags hidden", r"--help` proves a flag exists but never proves one\s*\n?doesn't"),
    ("verified against 0.146.0", r"0\.146\.0"),
]


def main():
    files = {p.name: p.read_text() for p in
             [SKILL / "SKILL.md"] + sorted((SKILL / "references").glob("*.md"))}
    blob = "\n".join(files.values())
    missing = []
    for label, pat in FACTS:
        where = [n for n, t in files.items() if re.search(pat, t, re.S)]
        if not where:
            missing.append(label)
        else:
            print(f"  {len(where)}x {label:<52} {' '.join(where)}")
    print(f"\n{len(FACTS)} facts tracked, {len(missing)} MISSING")
    for m in missing:
        print("  MISSING: " + m)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
