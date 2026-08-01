# The `--json` event stream

`--json` turns stdout into JSONL: one JSON object per line, emitted as the run
progresses. Use it when you need to know *what Codex did* — which commands ran,
which files changed, what it cost. When you only need the conclusion, plain mode
is simpler, because there stdout is already just the final message.

`$SKILL_DIR` below is the directory holding this skill's `SKILL.md`; set it as
shown there. Recipes use `jq`.

## Contents

- [Envelope types](#envelope-types)
- [The multiple-`agent_message` trap](#the-multiple-agent_message-trap)
- [Item types](#item-types)
- [Parsing recipes](#parsing-recipes)
- [Failure handling](#failure-handling)

## Envelope types

Every line has a `type`. A normal run is bracketed by thread/turn events with
item events in between:

```jsonl
{"type":"thread.started","thread_id":"019fb9b5-a083-70c0-b334-fcd42a8a14e0"}
{"type":"turn.started"}
{"type":"item.started","item":{...}}
{"type":"item.completed","item":{...}}
{"type":"turn.completed","usage":{"input_tokens":29971,"cached_input_tokens":19200,"cache_write_input_tokens":0,"output_tokens":89,"reasoning_output_tokens":13}}
```

| Type | Meaning |
|---|---|
| `thread.started` | Carries `thread_id` — the session id you pass to `codex exec resume`. |
| `turn.started` | Turn beginning. |
| `item.started` | An item began. Long-running items (commands, file changes) emit this first. |
| `item.updated` | An in-progress item changed. Safe to ignore for most parsing. |
| `item.completed` | An item finished. Carries the full payload — this is the line worth parsing. |
| `turn.completed` | Success, with a `usage` object. |
| `turn.failed` | Failure. |
| `error` | Error event. |

Not every item emits `item.started`; `agent_message` items appear only as
`item.completed`. Parsing `item.completed` alone gives a complete picture.

## The multiple-`agent_message` trap

**A single run emits many `agent_message` items, and only the last one is the
answer.** The others are progress narration Codex writes as it works.

An observed run of one small bug-fix task produced this sequence:

```
agent_message, command_execution, command_execution, agent_message,
command_execution, command_execution, command_execution, agent_message,
file_change, agent_message, command_execution, command_execution,
command_execution, agent_message
```

Five `agent_message` items. The first four are narration —

> "I'll inspect the failing test and the calculator implementation first…"

— and only the fifth is the result:

> "Fixed calc.py: `add` now returns `a + b` instead of `a - b`. Verification: …"

So extraction must take the **last** one:

```bash
# Correct
jq -r 'select(.item.type=="agent_message") | .item.text' run.jsonl | tail -1
```

Taking the first, or concatenating all of them, yields a confident-sounding
statement of intent that reads like a result. That failure is easy to miss
precisely because the narration is well-written.

The simplest way to sidestep this entirely is `-o/--output-last-message <FILE>`,
which writes exactly the final message and works alongside `--json`:

```bash
codex exec --json -o answer.md "<task>" < /dev/null > events.jsonl
```

## Item types

Observed in real runs (0.144.1, unchanged in 0.146.0):

**`agent_message`** — narration or final answer. No `status` field.

```json
{"id":"item_1","type":"agent_message","text":"The repo root has 6 top-level entries…"}
```

**`command_execution`** — a shell command. `item.started` has
`exit_code: null` and empty `aggregated_output`; `item.completed` has both
filled in. `aggregated_output` merges stdout and stderr and can be large, so
truncate before putting it in context.

```json
{"id":"item_0","type":"command_execution","command":"/bin/zsh -lc ls",
 "aggregated_output":"LICENSE\nREADME.md\n…","exit_code":0,"status":"completed"}
```

**`file_change`** — one item can carry several changes. Paths are absolute.
`kind` is `update` in the observed run; expect `add` and `delete` too.

```json
{"id":"item_8","type":"file_change","status":"completed",
 "changes":[{"path":"/abs/path/calc.py","kind":"update"}]}
```

**`error`** — a failure surfaced as an item, in addition to any top-level
`error` / `turn.failed` event. Treat it as run failure:

```json
{"id":"item_0","type":"error","message":"Model metadata for `zzz` not found. …"}
```

The types **`reasoning`**, **`mcp_tool_call`**, **`web_search`**, and
**`todo_list`** also exist in this build, but weren't exercised by the sample
runs — reasoning items in particular depend on `reasoning summaries` being
enabled (the header reports it as `none` by default). The names are real; treat
their exact *field* shapes as unconfirmed and inspect a live stream before
depending on them.

## Parsing recipes

Final answer only:

```bash
jq -r 'select(.item.type=="agent_message") | .item.text' run.jsonl | tail -1
```

Every command Codex ran, with exit status:

```bash
jq -r 'select(.type=="item.completed" and .item.type=="command_execution")
       | "[\(.item.exit_code)] \(.item.command)"' run.jsonl
```

Files touched — note the `item.completed` guard, without which every change is
reported twice, once from `item.started` and once from `item.completed`:

```bash
jq -r 'select(.type=="item.completed" and .item.type=="file_change")
       | .item.changes[] | "\(.kind) \(.path)"' run.jsonl
```

Did any command fail?

```bash
jq -e 'select(.type=="item.completed" and .item.type=="command_execution"
              and .item.exit_code != null and .item.exit_code != 0)' run.jsonl
```

`jq -e` exits `4` when nothing matches, not `1` — fine inside `if !` or `&&`,
but don't test it against `1`.

Token usage:

```bash
jq -r 'select(.type=="turn.completed") | .usage' run.jsonl
```

Session id, for resuming:

```bash
jq -r 'select(.type=="thread.started") | .thread_id' run.jsonl
```

For a single readable summary instead of separate queries, use the bundled
script, which applies the last-message rule and truncates command output:

```bash
python3 "$SKILL_DIR/scripts/codex_digest.py" run.jsonl
```

## Failure handling

A run that fails still produces valid JSONL — check for `turn.failed` and
`error` rather than assuming well-formed output means success:

```bash
jq -e 'select(.type=="turn.failed" or .type=="error")' run.jsonl > /dev/null \
  && echo "run failed"
```

**Don't treat an empty event file as the failure signal.** That heuristic holds
only in plain mode. Under `--json` the same hard failure (bad model, auth
problem) produces a *well-formed* stream and a silent stderr — the error arrives
as events, not as `ERROR:` lines:

```jsonl
{"type":"thread.started","thread_id":"019fb9cf-…"}
{"type":"item.completed","item":{"id":"item_0","type":"error","message":"Model metadata for `zzz` not found. …"}}
{"type":"turn.started"}
{"type":"error","message":"{\"type\":\"error\",\"status\":400,…}"}
{"type":"turn.failed","error":{"message":"{\"type\":\"error\",\"status\":400,…}"}}
```

So the `turn.failed or error` check above is the right test in JSON mode, and
the process exit code remains the most reliable check in either mode.
