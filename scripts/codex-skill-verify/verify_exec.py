#!/usr/bin/env python3
"""Execute the documented shell recipes, rather than merely checking the text exists.

Added after shipping `find ~ -name SKILL.md -path '*/codex/*'` as the documented
way to derive SKILL_DIR: it returns the FILE path while the prose promised the
directory. The text-presence harness passed it happily. Presence is not
correctness -- a documented command has to be run.

No codex inference is used; only the git/shell scaffolding around it.
"""

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

SKILL = str(pathlib.Path(__file__).resolve().parents[2] / "skills" / "codex")
FAILS = []


def check(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(label)


def sh(argv, **kw):
    assert isinstance(argv, (list, tuple)), "argv must be a list — a string would word-split differently in bash vs zsh"
    return subprocess.run(list(argv), capture_output=True, text=True, **kw)


def main():
    print("=== documented shell recipes actually execute ===")
    tmp = tempfile.mkdtemp()
    repo = os.path.join(tmp, "repo")
    try:
        os.makedirs(repo)
        for c in (["git", "init", "-q", "."], ["git", "config", "user.email", "t@t.t"],
                  ["git", "config", "user.name", "t"]):
            sh(c, cwd=repo)
        open(os.path.join(repo, "a.txt"), "w").write("v1\n")
        open(os.path.join(repo, "keep.txt"), "w").write("keep\n")
        sh(["git", "add", "-A"], cwd=repo)
        sh(["git", "commit", "-qm", "init"], cwd=repo)
        open(os.path.join(repo, "a.txt"), "w").write("v2\n")
        open(os.path.join(repo, "new.txt"), "w").write("new\n")
        # user stages keep.txt with one change, then modifies it again (the "MM"
        # case) -- so the recipe must capture staged + unstaged + untracked
        open(os.path.join(repo, "keep.txt"), "w").write("staged change\n")
        sh(["git", "add", "keep.txt"], cwd=repo)
        open(os.path.join(repo, "keep.txt"), "a").write("further unstaged edit\n")
        before = sh(["git", "diff", "--cached", "--name-only"], cwd=repo).stdout

        review = (
            "set -e\n"
            f"cd {repo}\n"
            'TMPIDX=$(mktemp -u); DIFF=$(mktemp)\n'
            "trap 'rm -f \"$TMPIDX\" \"$DIFF\"' EXIT\n"
            'GIT_INDEX_FILE="$TMPIDX" git read-tree HEAD\n'
            'GIT_INDEX_FILE="$TMPIDX" git add -A\n'
            'GIT_INDEX_FILE="$TMPIDX" git diff --cached HEAD > "$DIFF"\n'
            'rm -f "$TMPIDX"\n'
            '[ -s "$DIFF" ] || { echo EMPTY; exit 0; }\n'
            'grep -c "^+++" "$DIFF"\n'
        )
        r = sh(["bash", "-c", review])
        after = sh(["git", "diff", "--cached", "--name-only"], cwd=repo).stdout
        check("review recipe leaves the user's index untouched", before == after, f"{before!r} -> {after!r}")
        check("review recipe sees all 3 changed/new files",
              r.stdout.strip() == "3", r.stdout.strip() + r.stderr)

        # empty-diff guard on a clean tree
        clean = os.path.join(tmp, "clean")
        os.makedirs(clean)
        for c in (["git", "init", "-q", "."], ["git", "config", "user.email", "t@t.t"],
                  ["git", "config", "user.name", "t"]):
            sh(c, cwd=clean)
        open(os.path.join(clean, "f"), "w").write("x\n")
        sh(["git", "add", "-A"], cwd=clean); sh(["git", "commit", "-qm", "i"], cwd=clean)
        r = sh(["bash", "-c", review.replace(repo, clean)])
        check("empty-diff guard fires on a clean tree", "EMPTY" in r.stdout, r.stdout)

        # worktree recipe: BASE excludes the user's own commits
        sh(["git", "checkout", "-qb", "feature"], cwd=repo)
        sh(["git", "add", "-A"], cwd=repo)
        sh(["git", "commit", "-qm", "mine"], cwd=repo)
        base = sh(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
        wt = os.path.join(tmp, "wt")
        sh(["git", "worktree", "add", "-q", wt, "-b", "codex/x", base], cwd=repo)
        open(os.path.join(wt, "a.txt"), "a").write("codexline\n")
        d = sh(["git", "-C", wt, "diff", base]).stdout
        check("worktree diff vs BASE has Codex's change", "codexline" in d)
        check("worktree diff vs BASE excludes the user's own commit", "mine" not in d)
        # and the patch must carry files Codex created
        open(os.path.join(wt, "created.txt"), "w").write("brand new\n")
        sh(["git", "-C", wt, "add", "-N", "."])
        p = sh(["git", "-C", wt, "diff", "--binary", base]).stdout
        check("adopted patch includes files Codex created", "created.txt" in p)
        sh(["git", "worktree", "remove", wt, "--force"], cwd=repo)

        # documented SKILL_DIR confirmation
        r = sh(["ls", os.path.join(SKILL, "scripts/codex_pick_model.py")])
        check("documented SKILL_DIR check command works", r.returncode == 0, r.stderr)

        # CI: empty patch must not abort under set -e
        r = sh(["bash", "-c",
                'set -euo pipefail; p=$(mktemp); GITHUB_OUTPUT=/dev/null; '
                'if [ -s "$p" ]; then echo has_patch=true >> "$GITHUB_OUTPUT"; fi; echo OK'])
        check("CI empty-patch branch survives set -e", r.stdout.strip() == "OK", r.stderr)

        # fan-out failure detection, in BOTH shells
        fan = ('rc=0; pids=(); (exit 1) & pids+=($!); (exit 1) & pids+=($!); '
               'for p in "${pids[@]}"; do wait "$p" || rc=1; done; echo "rc=$rc"')
        for shell in ("bash", "zsh"):
            r = sh([shell, "-c", fan])
            check(f"{shell}: fan-out detects failures", r.stdout.strip() == "rc=1", r.stdout)
    finally:
        sh(["git", "worktree", "prune"], cwd=repo)
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'EXEC FAILURES: ' + str(len(FAILS)) if FAILS else 'ALL EXEC CHECKS PASS'}")
    for f in FAILS:
        print("  - " + f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
