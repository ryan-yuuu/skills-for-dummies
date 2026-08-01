---
name: codex-non-interactive
description: >-
  Delegate work to the OpenAI Codex CLI (`codex exec`) from an agent session,
  running it headless so it never opens the interactive TUI. Use this skill
  whenever you want to hand a task, a question, or a half-formed idea to
  Codex — have Codex review a diff, design, or plan; have Codex implement a
  scoped change; ask Codex for a second opinion or an independent critique of
  an architecture; get Codex to extract structured data; or fan several Codex
  runs out across a codebase in parallel. Trigger it when the user says "ask
  codex", "get codex's opinion", "have codex review this", "have codex
  implement/check this", "run codex", "delegate this to codex", "second
  opinion", "see what another model thinks", or mentions `codex exec`, `codex
  review`, `codex resume`, codex in CI, headless codex, or scripting codex.
  Also consult it before running any `codex` shell command yourself, because
  invoking bare `codex` from an agent launches an interactive UI that hangs the
  session with no way to recover. This is specifically the `codex` binary — not
  the OpenAI API or SDK, not another agent's CLI, and not work you should
  simply do yourself. Covers the safe invocation contract, model and effort
  selection, sandbox choice, output capture, parallelism, resuming sessions,
  and verifying what Codex hands back.
---

# Delegating to Codex

Codex CLI is a full coding agent, not a text-completion endpoint. When you shell
out to it you are handing work to a second engineer who will read files, run
commands, and possibly edit code — then hand you back a claim about what it did.

Two facts shape everything below:

- **It runs autonomously.** `codex exec` has no approval prompts, so nobody is
  standing between Codex and your filesystem except the sandbox you choose.
- **It starts cold.** Codex sees none of your conversation. Whatever context you
  don't put in the prompt does not exist.

## The invocation contract

Never run bare `codex`. With no subcommand it launches the interactive terminal
UI, which waits forever for keystrokes that will never come — your Bash call
hangs and the session is stuck. The non-interactive entry point is `codex exec`
(alias `codex e`).

Two preconditions worth checking once, since both fail confusingly rather than
clearly. Codex must be installed and authenticated, and it refuses to run
outside a Git repository:

```bash
codex --version && codex login status   # exits 0 when credentials exist
```

If either fails, say Codex isn't available rather than retrying or quietly
falling back — `codex doctor` diagnoses installation, config, auth, and Git
health in one pass. Outside a Git repo you'll get *"Not inside a trusted
directory and --skip-git-repo-check was not specified"*; pass
`--skip-git-repo-check` only when you're sure the directory is safe.

Paths below are written relative to this skill's directory. You'll be running
`codex` from the target repository, not from here, so set this once and use it
throughout:

```bash
SKILL_DIR="/abs/path/to/skills/codex-non-interactive"   # this skill's directory
```

The safe baseline, which you can copy and adjust:

```bash
codex exec $(python3 "$SKILL_DIR/scripts/codex_pick_model.py") \
  --ephemeral -s read-only "<self-contained prompt>" < /dev/null
```

Each piece earns its place:

| Fragment | Why |
|---|---|
| `exec` | The headless entry point. Without it you get the TUI. |
| `$(codex_pick_model.py)` | Expands to `-m <strongest model> -c model_reasoning_effort=xhigh`. See below — the defaults are weaker than you'd expect. |
| `--ephemeral` | Doesn't persist a session file. Skip it when you intend to `resume`. |
| `-s read-only` | Explicit least privilege — **not redundant.** The effective default depends on user config: in a project the user has trusted, `exec` silently gets `workspace-write`. See below. |
| `< /dev/null` | Codex reads stdin as *additional context* even when a prompt argument is given. Closing stdin prevents an inherited pipe from blocking the run. |

Output splits across two streams, which is what makes this scriptable:

- **stdout** — the final agent message, and nothing else. Pipe or capture this.
- **stderr** — the run header (model, sandbox, cwd, session id) and the live
  progress transcript. Read it when debugging or when you need the session id.

Exit code is `0` on success and `1` on failure, so `if ! codex exec ...` works.

## Always set the model and the effort

Leaving these to their defaults is the quietest way to get mediocre results,
because **both defaults are lower than you would guess**:

- The **model** comes from the user's `config.toml`, which is frequently an
  older release than the best one available. An observed default was several
  ranks down the catalog while a stronger model sat unused.
- The **reasoning effort** comes from the model's own
  `default_reasoning_level`, and for the current top model that value is
  **`low`**. A frontier model at `low` effort will underperform a weaker model
  at high effort, so this is the single cheapest quality lever available.

There is no `--effort` flag; effort is set through a config override.

```bash
-m <model-slug> -c model_reasoning_effort=xhigh
```

**Don't hardcode a model slug.** They turn over every few releases, and a stale
slug either errors out or silently pins Codex to an old model. Discover the
strongest one at call time:

`codex debug models` prints the catalog this binary sees, ranked by `priority`.
The bundled script reads it and picks for you (field details in
`references/flags.md`):

```bash
python3 "$SKILL_DIR/scripts/codex_pick_model.py"           # -m <strongest> -c model_reasoning_effort=xhigh
python3 "$SKILL_DIR/scripts/codex_pick_model.py" --list    # selectable models
python3 "$SKILL_DIR/scripts/codex_pick_model.py" --effort max
```

Splice it straight into a command:

```bash
codex exec $(python3 "$SKILL_DIR/scripts/codex_pick_model.py") -s read-only "<task>" < /dev/null
```

`codex debug models` is an experimental subcommand, so the script exits
non-zero with a clear message if the catalog shape changes — fall back to
running without `-m` rather than guessing a slug.

**Use the inline `$(...)` form, not a variable holding the flag string.** This
one is worth internalizing because it fails differently depending on the shell:

```bash
MF=$(python3 "$SKILL_DIR/scripts/codex_pick_model.py")
codex exec $MF ...        # WRONG — works in bash, breaks in zsh
```

Command substitution word-splits in both shells; *parameter* expansion splits
only in bash. Under zsh `$MF` arrives as one argument, so `-m` swallows the
whole string and the run dies with an opaque HTTP 400. Assume zsh semantics —
it's the macOS default and Codex spawns its own commands through it.

To resolve once and reuse — in a loop, or across several calls — use `--export`,
which keeps each value separately quoted:

```bash
eval "$(python3 "$SKILL_DIR/scripts/codex_pick_model.py" --export)"
codex exec -m "$CODEX_MODEL" -c model_reasoning_effort="$CODEX_EFFORT" \
  -s read-only "<task>" < /dev/null
```

### Choosing an effort level

Levels run `low → medium → high → xhigh → max → ultra`, and support varies by
model — the script resolves an unsupported request *downward* to the model's
best supported level, going higher only when the model supports nothing lower,
and saying which way on stderr. So a request won't silently cost more than you
asked for. (The published docs stop at `xhigh` and don't list `max`/`ultra`;
the binary has them. See `references/flags.md`.)

**Default to `xhigh`.** Every model in the observed catalog supports it, and
it's the right setting for work worth delegating at all — though upstream notes
`xhigh` is model-dependent, so it's a live-catalog fact rather than a
guarantee. Reach past it deliberately: `max` for genuinely hard reasoning —
subtle concurrency bugs, intricate refactors — and `ultra`, which adds automatic
task delegation, for large open-ended work. Drop to `medium` only for
mechanical, low-stakes calls where latency matters more than depth.

Higher effort costs more tokens and wall-clock time. That trade is usually worth
taking, because the expensive failure is not a slow run — it's a fast, confident,
wrong answer you then have to verify and discard.

Confirm what actually took effect. In plain (non-`--json`) mode, the stderr
header echoes the resolved settings, so a typo'd override shows up rather than
silently doing nothing:

```
model: gpt-5.6-sol
sandbox: read-only
reasoning effort: xhigh
```

**`--json` suppresses that header, and the event stream carries no model or
effort fields** — verified: a `--json` run's entire stderr was one line
("Reading additional input from stdin..."). So in JSON mode there is nothing to
check against. Either verify the flags once with a throwaway plain run, or trust
`codex_pick_model.py`, which prints exactly what it resolved.

This is also why a silently mistyped `-c` override is dangerous: unknown config
keys are accepted without complaint. `--strict-config` turns that into an error
instead.

## Set the bar before you delegate

Before writing the prompt — before the call goes out at all — decide what a
correct result actually looks like, and write it down. This is the acceptance
criteria you will grade the returned work against, and fixing it in advance is
what makes the grading honest.

The order matters. A bar set *after* seeing the output isn't a bar; it's a
rationalization. The characteristic failure of delegation is that Codex returns
something articulate and 80% right, and because it reads well you accept the
missing 20%. Deciding the target before there's any output to be attached to is
the defense.

A usable bar is specific and checkable. Vague targets can't fail, which is
exactly what makes them useless:

| Too vague | A real bar |
|---|---|
| "Fix the parser bug" | `pytest tests/test_parser.py` passes; only `src/parser.py` changed; no new dependencies; existing tests still green |
| "Review the diff" | Every finding cites file and line; each names a concrete failure scenario; severity assigned; no stylistic nitpicks |
| "Suggest a caching design" | Addresses invalidation, cold start, and the 3 access patterns in `docs/access.md`; states trade-offs; flags what it would need to measure |

The bar then does double duty:

1. **It goes into the prompt.** Codex can hit a target it can see. Stating the
   acceptance criteria is usually the difference between a result you can use
   and one you have to re-do.
2. **It's your checklist afterward.** You grade the output against the list you
   wrote, item by item.

When the returned work misses the bar, re-delegate with a sharper prompt, close
the gap yourself, or tell the user plainly what fell short — don't quietly lower
the bar to fit what came back. Catching yourself arguing that a criterion
"wasn't really necessary" is the signal.

## Write a prompt for someone with amnesia

This is the single biggest quality lever, and the easiest thing to get wrong.
You have a whole conversation of context; Codex has an empty room and a
repository. A prompt that reads fine to you ("fix the bug we discussed")
produces confident nonsense.

Every delegated prompt should carry:

1. **The concrete goal**, stated without reference to prior discussion.
2. **Where to look** — actual paths. Codex will find things on its own, but
   naming files saves it minutes of searching and you tokens.
3. **The acceptance criteria you just wrote** — stated as the target, so Codex
   is aiming at the same bar you'll grade it against. For code, name the exact
   test command.
4. **The output shape you want** — "reply with a numbered list of findings, most
   severe first" beats leaving it to chance, because you have to parse the reply.
5. **Boundaries** — what it must not touch, especially under `workspace-write`.

Codex cannot ask a clarifying question. If your prompt is ambiguous it will pick
an interpretation and commit to it, so resolve ambiguity yourself up front or
tell it explicitly what to do when it hits one ("if the intent is unclear, stop
and report the ambiguity instead of guessing").

## Pick the sandbox deliberately

In interactive use a human approves each escalation. `codex exec` has no
approval flag at all — there is nobody to ask — so **the sandbox is the entire
safety boundary**. Choose the least privilege that lets the task finish:

| Mode | Codex can | Use for |
|---|---|---|
| `read-only` | Read files, run read-only commands | Questions, review, design critique, brainstorming, analysis — most delegation |
| `workspace-write` | Also write inside the workspace | Delegated implementation, refactors, fixes |
| `danger-full-access` | Anything, unsandboxed | Only inside a disposable container/VM |

**Always pass `-s` — the default is not what you think.** The built-in default
is `read-only`, but user config overrides it, and *project trust* is part of
that config. Verified: the same `codex exec` command with no `-s` reports
`sandbox: read-only` in an untrusted directory and
`sandbox: workspace-write` inside a project recorded as
`trust_level = "trusted"` in `~/.codex/config.toml`. Users accumulate trusted
projects just by working in them.

So an omitted `-s` means a delegated "just answer this question" can arrive
holding write access to the user's repository. `--ignore-user-config` also
restores `read-only`, but naming the sandbox you want is clearer than relying on
that side effect.

`--add-dir <DIR>` grants write access to extra directories and is the right
answer when `workspace-write` is *almost* enough — reach for it instead of
escalating to full access.

**`workspace-write` blocks network access by default.** This catches out the
most common delegated task there is: "fix this and run the tests" dies the
moment the test command fetches a dependency, and since `exec` has no approval
prompt, nothing asks — it just fails. Either install dependencies before
invoking Codex (better, keeps its reach narrow) or enable network explicitly:

```bash
-c sandbox_workspace_write.network_access=true
```

**Two subcommands can't take `-s` at all.** `codex exec resume` inherits the
original session's sandbox — so a follow-up you think of as "just a question"
still carries write access — and `codex exec review` rejects `-s` outright. For
both, constrain them through config instead:

```bash
-c sandbox_mode='"read-only"'
```

`--dangerously-bypass-approvals-and-sandbox` removes the boundary entirely.
Don't use it to make an error message go away; if a task is failing under
`workspace-write`, that is usually information about the task, not the sandbox.

**If you are also editing the repo, do not give Codex `workspace-write` on it.**
Two agents writing the same files concurrently corrupt each other's work in ways
that are painful to untangle. Isolate it first:

```bash
git worktree add /tmp/codex-wt -b codex/attempt
codex exec $(python3 "$SKILL_DIR/scripts/codex_pick_model.py") \
  -s workspace-write -C /tmp/codex-wt "<task>" < /dev/null
git -C /tmp/codex-wt diff main   # review before it touches your tree
```

## Four shapes of delegation

These all resolve the model once up front (see the shell-splitting note above
for why the values are kept in separate quoted variables):

```bash
eval "$(python3 "$SKILL_DIR/scripts/codex_pick_model.py" --export)"
MODEL=(-m "$CODEX_MODEL" -c model_reasoning_effort="$CODEX_EFFORT")
```

`MODEL` is an array, expanded below as `"${MODEL[@]}"` — safe in both bash and
zsh. If arrays feel like overkill for a one-off, just inline
`$(python3 "$SKILL_DIR/scripts/codex_pick_model.py")` instead.

**Ask** — a question, a design critique, a brainstorm. Read-only, answer on
stdout. This is where model diversity pays: a different model family reaches
different conclusions, which is the whole point of a second opinion.

```bash
codex exec "${MODEL[@]}" --ephemeral -s read-only \
  "Read src/auth/session.rs. We're considering moving session storage from
   Redis to Postgres. Argue the strongest case AGAINST that move, grounded in
   what this code actually does. Be specific about what would break." \
  < /dev/null
```

**Review** — independent eyes on a diff. The dedicated subcommand knows how to
scope itself to changes:

```bash
codex exec review "${MODEL[@]}" --base main -c sandbox_mode='"read-only"' \
  --ephemeral < /dev/null
```

Targets are mutually exclusive: `--uncommitted` (staged + unstaged + untracked),
`--base <BRANCH>`, `--commit <SHA>`, or a bare prompt for custom instructions.
`--title` only applies with `--commit`.

**Implement** — hand over a scoped task. Needs write access, so isolate first
(above), and always read the resulting diff yourself.

```bash
codex exec "${MODEL[@]}" -s workspace-write -C /tmp/codex-wt \
  "Fix the failing test in tests/test_parser.py::test_nested_quotes. Run
   'pytest tests/test_parser.py' until green. Change only src/parser.py.
   Do not modify the test." \
  < /dev/null
```

**Extract** — when you need typed data rather than prose, constrain the final
message with a JSON Schema. Far more reliable than asking for JSON in the prompt:

```bash
codex exec "${MODEL[@]}" --ephemeral -s read-only --output-schema schema.json \
  -o result.json "Extract project metadata." < /dev/null
```

`--output-schema` takes a file path, not inline JSON. `-o/--output-last-message`
writes the final message to a file *and* still prints it to stdout.

## Long runs, and running several at once

A real Codex task runs for minutes, often past a default command timeout — and a
timeout kills the run with nothing to show for the tokens already spent. Two
mechanisms cover this, and they compose:

| Mechanism | How | Use when |
|---|---|---|
| **Background the tool call** | Your harness's own backgrounding — in Claude Code, the Bash tool's `run_in_background` parameter | A single long task. You keep working, get notified on exit, and never guess a timeout. |
| **Fan out inside one call** | Shell `&` … `wait` | Several runs that form one unit of work; reports back once when the batch finishes. |

The distinction is easy to collapse: reaching for `&` when you meant the first
one gives the harness a command that returns instantly, so it stops tracking the
work and you get no notification. Prefer backgrounding to simply raising the
timeout, which trades one blocking wait for a longer one.

They compose. One backgrounded call that fans out internally gives N parallel
runs and a single notification; backgrounding N separate calls gives N
notifications, so you can act on each result as it lands rather than waiting for
the slowest. Worked fan-out recipe in `references/patterns.md`.

Three constraints apply either way:

- **Parallelism multiplies cost.** Four concurrent runs cost four runs. It buys
  wall-clock, not quota — so fan out across genuinely separable subjects, not
  the same question asked several ways.
- **Concurrent writers collide.** Keep parallel runs `read-only`, or give each
  its own worktree. Two agents writing one tree corrupt each other's work.
- **Always redirect to files.** There's no stream to watch, so
  `> answer.md 2> progress.log` isn't housekeeping — it's how you get the result
  at all, and `progress.log` is where a failure explains itself.

`codex_digest.py` reads a partial JSONL stream mid-flight and reports
`INCOMPLETE`, which is how you tell "still working" from "finished".

## Trust the work, verify the output

Trust Codex to do the work — that's the point of delegating, and second-guessing
every step wastes what you paid for. But the *output* always gets reviewed
against the bar you set. Codex reports on its own work, and a self-report is not
evidence. The final message is a claim about what happened, not proof it did.

Grade against your written criteria, then check the claims underneath them:

- **For code changes** — read the diff and run the tests yourself. "All tests
  pass" in the final message is an assertion; your own green run is a fact.
  Confirm the change is scoped to what you allowed — an unrequested "helpful"
  refactor of an adjacent file is a bar violation even when the code is fine.
- **For findings and reviews** — spot-check specific claims against the files.
  A confident, well-written finding about a function that doesn't exist is a
  normal failure mode, and fluent prose is not evidence of a real defect.
- **For designs and brainstorms** — check that it engaged the actual constraints
  you named rather than a generic version of the problem. Plausible-sounding
  advice that ignores your stated constraint is the most common way this fails.
- **For anything surprising** — read the stderr transcript, or run
  `scripts/codex_digest.py` on a `--json` stream, to see which commands actually
  ran. A run that never executed the test command did not verify anything,
  whatever the summary says.

State the verdict honestly. If the work meets the bar, say so plainly. If it
misses, say which criterion it missed — don't launder a partial result into
"Codex handled it."

Relay Codex's conclusions as *Codex's conclusions*, especially when you disagree.
When your review and its review conflict, that disagreement is the useful signal
— surface both rather than silently picking one.

## When not to delegate

Shelling out to Codex costs the user's quota and real wall-clock time, and it
returns a claim you then have to verify. It's a poor trade for anything you can
do directly — reading a file, a quick grep, a small edit, a factual question.

Delegate when you're buying something you can't produce yourself: an independent
opinion from a different model, genuine parallelism across separable work, or a
long task you'd rather not spend your own context on.

## Reference material

Read these as needed rather than up front (`$SKILL_DIR` is set above):

- **`references/flags.md`** — flag tables for `exec`, `exec resume`, and
  `exec review`, plus useful `-c` config overrides, model catalog fields, auth,
  exit codes, and which widely-documented flags don't actually exist.
- **`references/json-events.md`** — the `--json` JSONL event schema, item types,
  and parsing recipes. Read when you need to observe *what Codex did*, not just
  what it concluded.
- **`references/patterns.md`** — multi-turn `resume`, piping stdin, parallel
  fan-out, worktree isolation, and CI usage.
- **`scripts/codex_pick_model.py`** — resolves the strongest available model and
  a supported effort level from the live catalog, so nothing is hardcoded.
- **`scripts/codex_digest.py`** — condenses a `--json` event stream into a short
  digest (commands run, files changed, final message, token usage). Use it
  instead of reading raw JSONL into context:
  `python3 "$SKILL_DIR/scripts/codex_digest.py" run.jsonl`

## Keeping Codex current

Codex ships frequently, and the flag surface and model catalog both move between
releases. Assume the newest version rather than any pinned behavior described
here, and update when something looks stale:

```bash
codex --version
codex update          # self-update; no-op on debug builds
```

Updating is safe to do without asking — it changes only the CLI, not the
repository. Newer releases are how the strongest models become reachable at all,
so an out-of-date binary quietly caps the quality of everything above.

When a flag is rejected, check `codex exec --help` before assuming the command
is wrong — it beats any documentation including this file. One caveat: some
accepted flags are hidden (`--full-auto`, `--yolo`, `--experimental-json`), so
`--help` proves a flag exists but never proves one doesn't.

Behaviors here were verified against **codex-cli 0.146.0**. Two genuine
divergences from the published docs are worth knowing: `-a/--ask-for-approval`
and `--search` exist on `codex` but are rejected by `codex exec`, and the effort
ladder runs past the documented `xhigh` to `max` and `ultra`. Re-check rather
than assuming these still hold.
