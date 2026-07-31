# Delegation patterns

Composable recipes for `codex exec`. Behaviors verified against codex-cli
0.146.0; `codex exec --help` is the authority if anything here is rejected.

`MF` in these examples is the model/effort pair from
`scripts/codex_pick_model.py` — see the model section in `SKILL.md` for why
leaving those at their defaults costs real quality.

## Contents

- [Worktree isolation](#worktree-isolation)
- [Multi-turn with resume](#multi-turn-with-resume)
- [Feeding data through stdin](#feeding-data-through-stdin)
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
git worktree add /tmp/codex-wt -b codex/fix-parser
codex exec $(python3 scripts/codex_pick_model.py) -s workspace-write -C /tmp/codex-wt \
  "Fix the failing test in tests/test_parser.py. Run 'pytest tests/test_parser.py'
   until it passes. Change only src/parser.py." \
  < /dev/null > /tmp/codex-answer.md 2> /tmp/codex-progress.log

git -C /tmp/codex-wt diff main          # review before adopting anything
git -C /tmp/codex-wt log --oneline main..HEAD
```

To adopt the work, cherry-pick or apply the diff — don't merge blindly:

```bash
git -C /tmp/codex-wt diff main > /tmp/codex.patch
git apply --check /tmp/codex.patch && git apply /tmp/codex.patch
```

Clean up when finished:

```bash
git worktree remove /tmp/codex-wt --force
git branch -D codex/fix-parser
```

`-C/--cd` sets the agent's working root, which is what confines it to the
worktree. Without it, `-s workspace-write` applies to wherever you invoked the
command.

## Multi-turn with resume

Useful when a task splits into stages and the second stage depends on what the
first one learned. Resuming preserves the session's context, so the follow-up
prompt doesn't need to restate it.

```bash
MF=$(python3 scripts/codex_pick_model.py)

# Stage 1 — note: no --ephemeral, or there is no session to resume
codex exec $MF --json -s workspace-write \
  "Review src/ for race conditions. List each with file and line." \
  < /dev/null > stage1.jsonl

SESSION=$(jq -r 'select(.type=="thread.started") | .thread_id' stage1.jsonl)

# Stage 2 — inherits the analysis, the sandbox, and the model from stage 1
codex exec resume "$SESSION" \
  "Fix the highest-severity race condition you identified. Leave the rest." \
  < /dev/null
```

Three things that bite:

- **`--ephemeral` makes a run unresumable.** Drop it when you plan a stage 2.
- **`resume` has no `-s/--sandbox` flag, and inherits the original session's
  sandbox.** Verified: resuming a `workspace-write` session reports
  `sandbox: workspace-write` with no flag passed. So a follow-up you think of as
  "just a question" still carries write access, and conversely a session started
  `read-only` cannot be upgraded with `-s`. Plan the sandbox at stage 1.
- **Model and effort are inherited too**, so a session started on a weak model
  stays weak. Set them at stage 1, or re-pass `-m` and
  `-c model_reasoning_effort=` on the resume.

To tighten a resumed run, override the config key directly — verified to work:

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
on what else has run in that directory, which makes it a poor fit for anything
reproducible.

## Feeding data through stdin

Two distinct modes, and picking the wrong one is a common source of confusion:

**Prompt argument + piped stdin** — stdin becomes *context* appended as a
`<stdin>` block, the argument stays the instruction. Use this when another
command produces the data you want examined:

```bash
npm test 2>&1 \
  | codex exec -s read-only "Summarize the failing tests and propose the smallest fix"
```

Note there is no `< /dev/null` here — stdin is deliberately in use.

**`codex exec -`** — stdin becomes the *whole prompt*. Use it when a script or
file generates the entire instruction:

```bash
cat prompt.txt | codex exec -
printf 'Summarize this log in 3 bullets:\n\n%s\n' "$(tail -n 200 app.log)" | codex exec -
```

Since stdout is just the final message, Codex composes with ordinary Unix tools:

```bash
gh run view 123456 --log | codex exec "summarize this CI failure in 5 bullets" \
  | gh pr comment 789 --body-file -
```

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

codex exec review --base main --ephemeral \
  --output-schema review-schema.json -o findings.json < /dev/null

jq -r '.findings[] | select(.severity=="high") | "\(.file):\(.line) — \(.issue)"' findings.json
```

`--output-schema` takes a **file path**, not inline JSON. Keep schemas strict
(`required` + `additionalProperties: false`) so a malformed response fails
loudly instead of silently omitting fields.

## Parallel fan-out

Independent, separable questions can run concurrently. The gain is real, but so
is the cost — every run consumes quota — so fan out across genuinely different
subjects rather than re-asking one question many ways.

```bash
MF=$(python3 scripts/codex_pick_model.py)   # resolve once, not per iteration

for area in auth billing search; do
  codex exec $MF --ephemeral -s read-only \
    "Audit src/$area/ for error-handling gaps. List findings, most severe first." \
    < /dev/null > "audit-$area.md" 2> "audit-$area.log" &
done
wait
```

Keep every parallel run `read-only`. Concurrent writers in one tree collide, and
that is precisely what the worktree pattern exists to prevent.

## Adversarial second opinion

Where a different model family earns its keep. A neutral "review this" tends to
produce agreeable output; asking for the strongest case *against* surfaces the
disagreement you're actually paying for.

Raise effort here rather than accepting the default — finding the real objection
is exactly the kind of work that rewards deeper reasoning:

```bash
codex exec $(python3 scripts/codex_pick_model.py --effort max) --ephemeral -s read-only \
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

```bash
# Background: doesn't block, collect the files when it finishes
codex exec -s read-only "<large audit>" < /dev/null \
  > audit.md 2> audit.log &
CODEX_PID=$!
wait $CODEX_PID; echo "exit=$?"
```

Always redirect both streams to files. Relying on scrollback loses the output
when it matters most, and `audit.log` is where the failure reason lives.

For progress visibility on a long run, `--json` plus the digest script gives a
readable snapshot at any point — the digest reports `INCOMPLETE` while the
stream is still open, which distinguishes "still working" from "finished":

```bash
codex exec --json -s read-only "<task>" < /dev/null > run.jsonl 2> run.log &
python3 scripts/codex_digest.py run.jsonl   # safe to run mid-flight
```

## CI usage

For GitHub Actions, prefer [`openai/codex-action`](https://github.com/openai/codex-action)
over installing the CLI yourself — it proxies the API key rather than exposing
it to job steps that run repository-controlled code.

When running the CLI directly, pin behavior against local-config drift and fail
loudly:

```bash
set -euo pipefail

MF=$(python3 scripts/codex_pick_model.py)   # don't hardcode a slug in CI either

CODEX_API_KEY="$SECRET_KEY" codex exec $MF \
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

python3 scripts/codex_digest.py run.jsonl
```

Each flag addresses a specific CI hazard:

| Flag | Hazard it removes |
|---|---|
| `--ignore-user-config` | A developer's `config.toml` silently changing CI behavior |
| `--ignore-rules` | Project execpolicy `.rules` files altering what may run |
| `--strict-config` | Config keys this build doesn't recognize passing unnoticed |
| `--ephemeral` | Session files accumulating on the runner |
| `--color never` | ANSI escapes corrupting captured logs |

Set `CODEX_API_KEY` inline for the single command rather than as a job-level
env var — anything else in that process environment can read an exported key.

The safest shape for a write-enabled CI job is to grant Codex only read
permissions on the repository, have it produce a patch, and open the pull
request from a separate job that never sees the API key:

```bash
git add -N .
git diff --binary HEAD > codex.patch
[ -s codex.patch ] && echo "has_patch=true" >> "$GITHUB_OUTPUT"
```
