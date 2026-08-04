# Delegation patterns

Composable recipes for `codex exec`. Behaviors verified against codex-cli
0.146.0; `codex exec --help` is the authority if anything here is rejected.

Examples resolve the model once with `--export` and expand it as a quoted
array. Do **not** stash the flag string in a plain variable and expand it
unquoted — zsh doesn't word-split parameter expansions, so `$MF` arrives as a
single argument and the run dies with an opaque HTTP 400. See the model section
in `SKILL.md` for why the defaults are worth overriding at all.

```bash
SKILL_DIR="/abs/path/to/skills/codex"   # this skill's directory
eval "$(python3 "$SKILL_DIR/scripts/codex_pick_model.py" --export)"
MODEL=(-m "$CODEX_MODEL" -c model_reasoning_effort="$CODEX_EFFORT")
```

Several recipes use `jq`.

## Contents

- [Worktree isolation](#worktree-isolation)
- [Multi-turn with resume](#multi-turn-with-resume)
- [Feeding data through stdin](#feeding-data-through-stdin)
- [Reviewing a working diff](#reviewing-a-working-diff)
- [Structured output](#structured-output)
- [Parallel fan-out](#parallel-fan-out)
- [Adversarial second opinion](#adversarial-second-opinion)
- [Long-running and background execution](#long-running-and-background-execution)
- [CI usage](#ci-usage)

## Worktree isolation

The pattern to reach for whenever Codex needs write access to a repository you
are also working in. Concurrent agents editing the same files produce
interleaved, half-applied changes that are far more expensive to untangle than
the setup cost here.

```bash
# Record the fork point. `git worktree add` branches from HEAD, so diffing
# against `main` later would fold your own unmerged commits into the patch.
BASE=$(git rev-parse HEAD)
git worktree add /tmp/codex-wt -b codex/fix-parser "$BASE"
codex exec "${MODEL[@]}" -s workspace-write -C /tmp/codex-wt \
  -c sandbox_workspace_write.network_access=true \
  "Fix the failing test in tests/test_parser.py. Run 'pytest tests/test_parser.py'
   until it passes. Change only src/parser.py." \
  < /dev/null > /tmp/codex-answer.md 2> /tmp/codex-progress.log

git -C /tmp/codex-wt diff "$BASE"       # modified files, vs the fork point
git -C /tmp/codex-wt status --short     # AND files Codex created — diff won't show them
git -C /tmp/codex-wt log --oneline "$BASE"..HEAD
```

To adopt the work, cherry-pick or apply the diff — don't merge blindly:

```bash
# `git add -N` registers new files so diff can see them, and --binary keeps
# binary content. Without both, a patch silently loses every file Codex
# created — with no error. Diff against "$BASE", never `main`.
git -C /tmp/codex-wt add -N .
git -C /tmp/codex-wt diff --binary "$BASE" > /tmp/codex.patch
git apply --check /tmp/codex.patch && git apply /tmp/codex.patch
```

Clean up when finished:

```bash
git worktree remove /tmp/codex-wt --force
git branch -D codex/fix-parser
```

The worktree holds the **committed** tree, so anything you have uncommitted is
invisible to Codex — commit or stash first when the task concerns work in
progress, or it will reason about stale content and the patch will conflict on
adoption.

`-C/--cd` sets the agent's working root, which is what confines it to the
worktree. Without it, `-s workspace-write` applies to wherever you invoked the
command.

**A worktree does not isolate the trust side effect.** Codex keys trust on the
*git repo root*, and a worktree shares the main repo's root — so this run writes
a trust entry for **the main repository**, not for `/tmp/codex-wt`. Verified: a
`-s workspace-write` run with `-C <worktree>` wrote
`[projects."<main repo>"]`, after which a bare `codex exec` in the main repo
resolved to `workspace-write`.

So the worktree protects your *working files* from concurrent edits — which is
what it's for — but the escalation lands on the real repository and outlives
`git worktree remove`. Pass `-s` explicitly on every later run there, or delete
the entry from `$CODEX_HOME/config.toml` (`~/.codex` by default).

`sandbox_workspace_write.network_access=true` is there because
`workspace-write` blocks the network by default
([`flags.md`](flags.md#sandbox-and-permissions)). Omit it when the task
genuinely needs no network — that's the safer default when you can afford it.

## Multi-turn with resume

Useful when a task splits into stages and the second stage depends on what the
first one learned. Resuming preserves the session's context, so the follow-up
prompt doesn't need to restate it.

**Read this before the recipe: a write-enabled resume cannot be isolated.**
`resume` accepts neither `-s` nor `-C` (both rejected at parse time), so stage 2
writes into whatever directory you invoke it from — you cannot point it at a
worktree. If you're also editing that repo, keep stage 2 `read-only` and apply
the change yourself. A `workspace-write` stage 2 does *not* trust the repo root — resuming an
existing session never writes an entry — but if the resume silently starts fresh
instead, it will.

```bash
# Stage 1 — note: no --ephemeral, or there is no session to resume
codex exec "${MODEL[@]}" --json -s read-only \
  "Review src/ for race conditions. List each with file and line." \
  < /dev/null > stage1.jsonl 2> stage1.log

# A FAILED stage 1 still emits thread.started, so SESSION would populate and the
# assertion below would compare a dead session against itself and pass. Check
# the run actually completed before going on.
python3 "$SKILL_DIR/scripts/codex_digest.py" stage1.jsonl > /dev/null \
  || { echo "stage 1 failed — see stage1.log"; exit 1; }

SESSION=$(jq -r 'select(.type=="thread.started") | .thread_id' stage1.jsonl)

# Stage 2 — inherits the conversation, but NOT the sandbox/model/effort.
# --json so the resumed thread id can be asserted; -o to still capture the answer.
# read-only by default: switch to workspace-write only when you are NOT editing
# this repo yourself, since stage 2 cannot be confined to a worktree.
codex exec resume "$SESSION" "${MODEL[@]}" -c sandbox_mode='"read-only"' \
  --json -o stage2-answer.md \
  "Name the single change that would fix the highest-severity race condition." \
  < /dev/null > stage2.jsonl 2> stage2.log
```

Three things that bite:

- **`--ephemeral` makes a run unresumable.** Drop it when you plan a stage 2.
- **`resume` does not inherit the sandbox, and has no `-s` flag to set one.**
  It re-resolves the default for the current directory, so in a trusted project
  a stage 1 you deliberately ran `read-only` comes back as `workspace-write`.
  Verified in both directions — a `danger-full-access` stage 1 also resumes as
  `workspace-write`. Stage 1's choice simply doesn't carry.
- **Model and effort don't carry either.** They resolve from flags and config on
  every resume, so re-pass them each time.

`resume` also has no `-C/--cd`, and it resolves the sandbox from the directory
you invoke it in. `cd`-ing into a worktree doesn't buy you `read-only` either: a
worktree resolves to its main repo's root, which may already be trusted — any
earlier write-enabled run there would have marked it so. Set the sandbox
explicitly rather than relying on location.

Because nothing carries, set the sandbox explicitly on *every* resume:

```bash
codex exec resume "$SESSION" -c sandbox_mode='"read-only"' "<follow-up>" < /dev/null
```

Note the nested quoting: `-c` parses its value as TOML, so the string needs
quotes that survive the shell.

`--last` resumes the most recent session from the current directory, with
`--all` widening the search past the cwd filter:

```bash
codex exec resume --last "now write a test that would have caught it" < /dev/null
```

Prefer an explicit session id in scripts. `--last` is ambient state — it depends
on what else has run in that directory — and worse, when there is nothing to
resume it silently starts a **fresh, context-free session and exits `0`**. The
same applies to an unknown thread name. Assert you got the session you meant:

```bash
RESUMED=$(jq -r 'select(.type=="thread.started") | .thread_id' stage2.jsonl)
if [ "$RESUMED" != "$SESSION" ]; then
  echo "WARNING: resumed thread id ($RESUMED) != requested ($SESSION)."
  echo "Check stage2 output for stage-1 context before trusting it."
fi
```

A resumed run does re-emit `thread.started` with the original id (confirmed), so
a mismatch is a real signal. It warns rather than exiting anyway, so an
unexpected id can't abort work that actually succeeded.

## Feeding data through stdin

Two distinct modes, and picking the wrong one is a common source of confusion:

**Prompt argument + piped stdin** — stdin becomes *context* appended as a
`<stdin>` block, the argument stays the instruction. Use this when another
command produces the data you want examined:

```bash
npm test 2>&1 \
  | codex exec "${MODEL[@]}" -s read-only "Summarize the failing tests and propose the smallest fix"
```

Note there is no `< /dev/null` here — stdin is deliberately in use.

**`codex exec -`** — stdin becomes the *whole prompt*. Use it when a script or
file generates the entire instruction:

```bash
cat prompt.txt | codex exec "${MODEL[@]}" -
printf 'Summarize this log in 3 bullets:\n\n%s\n' "$(tail -n 200 app.log)" \
  | codex exec "${MODEL[@]}" -
```

Since stdout is just the final message, Codex composes with ordinary Unix tools:

```bash
gh run view 123456 --log | codex exec "${MODEL[@]}" -s read-only \
  "summarize this CI failure in 5 bullets" > summary.md
# read summary.md yourself, then post it
gh pr comment 789 --body-file summary.md
```

Deliberately two steps: piping straight into `gh pr comment` would publish model
output, derived from attacker-influenceable CI logs, without anyone reading it.

**Piped content is untrusted input.** CI logs, pull request bodies, commit
messages, and issue text can all carry instructions aimed at the model. Keep
runs like this `read-only`, treat the output as a draft rather than something to
post unread, and don't pipe attacker-influenced text into a write-enabled run.

## Reviewing a working diff

`codex exec review` scopes itself automatically, but its target flags
(`--uncommitted`, `--base`, `--commit`) cannot be combined with a prompt — so
acceptance criteria can't reach it. Pipe the diff into a plain `codex exec`
instead.

```bash
# Build the diff in a THROWAWAY index so the user's staging is untouched.
# `git add -N` in the real index would break `git stash` and make the next
# `git commit -a` sweep in untracked files; `git reset` to undo it would
# destroy any partial staging they had.
TMPIDX=$(mktemp -u); DIFF=$(mktemp)
trap 'rm -f "$TMPIDX" "$DIFF"' EXIT
GIT_INDEX_FILE="$TMPIDX" git read-tree HEAD
GIT_INDEX_FILE="$TMPIDX" git add -A
GIT_INDEX_FILE="$TMPIDX" git diff --cached HEAD > "$DIFF"
rm -f "$TMPIDX"

# An empty diff would get a confident "no issues found" that reads like a clean
# bill of health for code Codex never saw.
[ -s "$DIFF" ] || { echo "no uncommitted changes to review"; exit 0; }

codex exec "${MODEL[@]}" --ephemeral -s read-only \
  "Review this diff. Every finding must cite file and line, name a concrete
   failure scenario, and carry a severity. No stylistic nitpicks." \
  < "$DIFF" > "${TMPDIR:-/tmp}/review.md" 2> "${TMPDIR:-/tmp}/review.log"
rm -f "$DIFF"
```

That covers staged, unstaged, and untracked — the same scope as `--uncommitted`,
without touching the user's index. For a base-branch review, set
`BASE=$(git merge-base HEAD main)` first and swap the last `git diff` for
`GIT_INDEX_FILE="$TMPIDX" git diff --cached "$BASE"`, so the diff excludes
commits already on the base. Note there's no `< /dev/null`: stdin carries the
diff.

## Structured output

When a downstream step needs fields rather than prose, constrain the final
message with a JSON Schema. This is markedly more reliable than asking for JSON
in the prompt, because the shape is enforced rather than requested.

```bash
cat > review-schema.json <<'EOF'
{
  "type": "object",
  "properties": {
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "file":     { "type": "string" },
          "line":     { "type": "integer" },
          "severity": { "type": "string", "enum": ["high", "medium", "low"] },
          "issue":    { "type": "string" }
        },
        "required": ["file", "line", "severity", "issue"],
        "additionalProperties": false
      }
    }
  },
  "required": ["findings"],
  "additionalProperties": false
}
EOF

codex exec review "${MODEL[@]}" --base main --ephemeral \
  -c sandbox_mode='"read-only"' \
  --output-schema review-schema.json -o findings.json < /dev/null

jq -r '.findings[] | select(.severity=="high") | "\(.file):\(.line) — \(.issue)"' findings.json
```

`review` has no `-s` flag, hence the `-c sandbox_mode` override.

`--output-schema` takes a **file path**, not inline JSON. Keep schemas strict
(`required` + `additionalProperties: false`) so a malformed response fails
loudly instead of silently omitting fields.

## Parallel fan-out

Independent, separable questions can run concurrently. The gain is real, but so
is the cost — every run consumes quota — so fan out across genuinely different
subjects rather than re-asking one question many ways.

```bash
pids=()
for area in auth billing search; do
  codex exec "${MODEL[@]}" --ephemeral -s read-only \
    "Audit src/$area/ for error-handling gaps. List findings, most severe first." \
    < /dev/null > "audit-$area.md" 2> "audit-$area.log" &
  pids+=($!)
done

rc=0
for p in "${pids[@]}"; do wait "$p" || rc=1; done
if [ "$rc" -ne 0 ]; then echo "at least one run failed — check audit-*.log"; fi
for f in audit-*.md; do
  [ -s "$f" ] || echo "empty result: $f — see ${f%.md}.log"
done
```

Use `if`, not `[ ... ] && echo`: when everything succeeds the test is false, so
the AND-list evaluates to 1. `set -e` won't abort on it mid-script, but as the
final statement it silently becomes the script's exit status — a green run
reported as a failure. The empty-file loop catches
the other failure signature — a run that died leaves a zero-length answer.

**Collect exit statuses; don't use a bare `wait`.** Bare `wait` returns `0` even
when every job failed — verified — so a fan-out that died three times reports
success and leaves you three empty result files. An empty output file with a
zero status is the signature of exactly this mistake.

Keep every parallel run `read-only`, or give each its own worktree. Concurrent
writers in one tree collide, which is what the worktree pattern exists to
prevent.

## Adversarial second opinion

Where a different model family earns its keep. A neutral "review this" tends to
produce agreeable output; asking for the strongest case *against* surfaces the
disagreement you're actually paying for.

Raise effort here rather than accepting the default — finding the real objection
is exactly the kind of work that rewards deeper reasoning. Ask the script for
`max` rather than hardcoding it, so it resolves down if the model tops out
lower:

```bash
eval "$(python3 "$SKILL_DIR/scripts/codex_pick_model.py" --effort max --export)"
codex exec -m "$CODEX_MODEL" -c model_reasoning_effort="$CODEX_EFFORT" --ephemeral -s read-only \
  "Read docs/rfc-caching.md and the code in src/cache/.
   Argue the strongest case AGAINST this design, grounded in what the code
   actually does. Name concrete failure scenarios with file and line.
   If the design is sound, say so plainly rather than inventing objections." \
  < /dev/null
```

The closing clause matters: without it, a prompt demanding objections reliably
manufactures them. Treat the result as one informed opinion to weigh against
your own, not a verdict — and when the two conflict, surface both.

## Long-running and background execution

A substantial Codex task can run for many minutes, well past a default command
timeout. A timeout kills the run and wastes everything spent so far, so decide
up front:

For a *single* long run, prefer your harness's own backgrounding — the Bash
tool's `run_in_background` in Claude Code — rather than a shell `&`, so the
harness keeps tracking the work and notifies you when it exits (see the table in
`SKILL.md`). Use `&` when you want the exit status of a run whose output goes to
files:

```bash
codex exec "${MODEL[@]}" -s read-only "<large audit>" < /dev/null \
  > audit.md 2> audit.log &
CODEX_PID=$!
wait "$CODEX_PID"; echo "exit=$?"   # blocks here by design — collects the status
```

Always redirect both streams to files. Relying on scrollback loses the output
when it matters most, and `audit.log` is where the failure reason lives.

For progress visibility on a long run, `--json` plus the digest script gives a
readable snapshot at any point — the digest reports `INCOMPLETE` while the
stream is still open, which distinguishes "still working" from "finished":

```bash
codex exec "${MODEL[@]}" --json -s read-only "<task>" < /dev/null > run.jsonl 2> run.log &
python3 "$SKILL_DIR/scripts/codex_digest.py" run.jsonl   # safe to run mid-flight
```

## CI usage

For GitHub Actions, prefer [`openai/codex-action`](https://github.com/openai/codex-action)
over installing the CLI yourself — it proxies the API key rather than exposing
it to job steps that run repository-controlled code.

When running the CLI directly, pin behavior against local-config drift and fail
loudly. Run your setup steps (`npm ci`, `pip install`) *before* invoking Codex,
so the run itself needs no network — that's what lets you leave the default
network-off `workspace-write` sandbox alone:

```bash
set -euo pipefail

# Self-contained: set these in the workflow, not from the preamble above.
SKILL_DIR="/abs/path/to/skills/codex"
CODEX_KEY="${OPENAI_API_KEY:?set this from your CI secret store}"
eval "$(python3 "$SKILL_DIR/scripts/codex_pick_model.py" --export)"
MODEL=(-m "$CODEX_MODEL" -c model_reasoning_effort="$CODEX_EFFORT")

CODEX_API_KEY="$CODEX_KEY" codex exec "${MODEL[@]}" \
  --json \
  --ephemeral \
  --sandbox workspace-write \
  --ignore-user-config \
  --ignore-rules \
  --strict-config \
  --color never \
  -o final-message.md \
  "<task>" \
  < /dev/null > run.jsonl 2> run.log || {
    echo "::error::codex run failed"; tail -50 run.log; exit 1;
  }

python3 "$SKILL_DIR/scripts/codex_digest.py" run.jsonl
```

Each flag addresses a specific CI hazard:

| Flag | Hazard it removes |
|---|---|
| `--ignore-user-config` | A developer's `config.toml` silently changing CI behavior. Note it does **not** stop codex writing a trust entry, so a persistent runner accumulates them across jobs. |
| `--ignore-rules` | Project execpolicy `.rules` files altering what may run |
| `--strict-config` | Config keys this build doesn't recognize passing unnoticed |
| `--ephemeral` | Session files accumulating on the runner |
| `--color never` | ANSI escapes corrupting captured logs |

If the task genuinely can't be pre-provisioned, add
`-c sandbox_workspace_write.network_access=true` — but prefer installing
dependencies beforehand, since that keeps the model's reach narrower.

Set `CODEX_API_KEY` inline for the single command rather than as a job-level env
var — and the same for `OPENAI_API_KEY`. Anything else in that process
environment (build scripts, tests, dependency lifecycle hooks) can read an
exported key. Sanitize any prompt text drawn from pull requests, commit
messages, or issue bodies before it reaches Codex.

The safest shape for a write-enabled CI job is to grant Codex only read
permissions on the repository, have it produce a patch, and open the pull
request from a separate job that never sees the API key:

```bash
# Throwaway index: `git add -N .` on the real one would leave the checkout
# dirty for later steps.
TMPIDX=$(mktemp -u)
GIT_INDEX_FILE="$TMPIDX" git read-tree HEAD
GIT_INDEX_FILE="$TMPIDX" git add -A
GIT_INDEX_FILE="$TMPIDX" git diff --cached --binary HEAD > codex.patch
rm -f "$TMPIDX"
# `if`, not `[ ... ] && echo`: an empty patch is the normal "nothing to change"
# outcome, and a false AND-list as the step's LAST command becomes exit 1 and
# fails the step. `set -e` does not fire on it -- same trap as Parallel fan-out.
if [ -s codex.patch ]; then echo "has_patch=true" >> "$GITHUB_OUTPUT"; fi
```
