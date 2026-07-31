---
name: codex-non-interactive
description: >-
  Delegate work to the OpenAI Codex CLI (`codex exec`) from an agent session,
  running it headless so it never opens the interactive TUI. Use this skill
  whenever you want to hand a task, a question, or a half-formed idea to Codex:
  getting a second opinion or an independent review of a diff, design, or plan;
  delegating a scoped implementation; brainstorming approaches with a different
  model; critiquing an architecture; extracting structured data; or fanning out
  analysis across a codebase. Trigger it when the user says "ask codex", "get
  codex's opinion", "have codex review this", "have codex implement/check
  this", "run codex", "second opinion", "see what another model thinks", or
  mentions `codex exec`, codex in CI, headless codex, or scripting codex. Also
  consult it before running any `codex` shell command yourself, because
  invoking bare `codex` from an agent launches an interactive UI that hangs the
  session with no way to recover. Covers the safe invocation contract, sandbox
  selection, output capture, resuming sessions, and verifying what Codex hands
  back.
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

The safe baseline, which you can copy and adjust:

```bash
codex exec $(python3 scripts/codex_pick_model.py) \
  --ephemeral -s read-only "<self-contained prompt>" < /dev/null
```

Each piece earns its place:

| Fragment | Why |
|---|---|
| `exec` | The headless entry point. Without it you get the TUI. |
| `$(codex_pick_model.py)` | Expands to `-m <strongest model> -c model_reasoning_effort=xhigh`. See below — the defaults are weaker than you'd expect. |
| `--ephemeral` | Doesn't persist a session file. Skip it when you intend to `resume`. |
| `-s read-only` | Explicit least privilege. It's also the default, but stating it documents intent and survives a user config that changed the default. |
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

```bash
codex debug models          # full JSON catalog this binary can actually see
```

Each entry carries a `priority` (lower is stronger — `1` is the current
frontier coding model), a `visibility` (`hide` marks internal entries you
shouldn't select), and its `supported_reasoning_levels`. The bundled script
does that selection for you:

```bash
python3 scripts/codex_pick_model.py             # -m gpt-5.6-sol -c model_reasoning_effort=xhigh
python3 scripts/codex_pick_model.py --list      # inspect the whole catalog
python3 scripts/codex_pick_model.py --effort max
```

Splice it straight into a command:

```bash
codex exec $(python3 scripts/codex_pick_model.py) -s read-only "<task>" < /dev/null
```

**Use the inline `$(...)` form, not a variable holding the flag string.** This
one is worth internalizing because it fails differently depending on the shell:

```bash
MF=$(python3 scripts/codex_pick_model.py)
codex exec $MF ...        # WRONG — works in bash, breaks in zsh
```

Command substitution word-splits in both bash and zsh, but *parameter* expansion
word-splits only in bash. Under zsh, `$MF` arrives as a single argument, so `-m`
receives the literal string `" gpt-5.6-sol -c model_reasoning_effort=xhigh"` and
the run dies with an opaque HTTP 400 about an unsupported model. Since zsh is
the default shell on macOS, and Codex itself spawns commands via `/bin/zsh -lc`,
assume zsh semantics.

To resolve the catalog once and reuse it — in a loop, or across several calls —
use `--export`, which keeps every value individually quoted:

```bash
eval "$(python3 scripts/codex_pick_model.py --export)"
codex exec -m "$CODEX_MODEL" -c model_reasoning_effort="$CODEX_EFFORT" \
  -s read-only "<task>" < /dev/null
```

### Choosing an effort level

Levels run `low → medium → high → xhigh → max → ultra`, though not every model
supports the top ones (the script falls back to the model's best supported level
rather than emitting a flag the CLI would reject).

**Default to `xhigh`.** It's supported by every currently listed model and is
the right setting for the work worth delegating at all. Reach past it only
deliberately: `max` for genuinely hard reasoning — subtle concurrency bugs,
intricate refactors — and `ultra`, which adds automatic task delegation, for
large open-ended work. Drop to `medium` only for mechanical, low-stakes calls
where latency matters more than depth.

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
something articulate and 80% right, and because it reads well and you're already
invested in the result, you accept the missing 20%. Deciding the target while
you still have no output to be attached to is the defense against that.

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

Hold it without flinching. When the returned work misses the bar, the options
are to re-delegate with a sharper prompt, close the gap yourself, or tell the
user plainly what fell short — never to quietly lower the bar to fit what came
back. If you find yourself arguing that a criterion "wasn't really necessary,"
that's the moment the discipline exists for.

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
| `read-only` *(default)* | Read files, run read-only commands | Questions, review, design critique, brainstorming, analysis — most delegation |
| `workspace-write` | Also write inside the workspace | Delegated implementation, refactors, fixes |
| `danger-full-access` | Anything, unsandboxed | Only inside a disposable container/VM |

`--add-dir <DIR>` grants write access to extra directories and is the right
answer when `workspace-write` is *almost* enough — reach for it instead of
escalating to full access.

`--dangerously-bypass-approvals-and-sandbox` removes the boundary entirely.
Don't use it to make an error message go away; if a task is failing under
`workspace-write`, that is usually information about the task, not the sandbox.

**If you are also editing the repo, do not give Codex `workspace-write` on it.**
Two agents writing the same files concurrently corrupt each other's work in ways
that are painful to untangle. Isolate it first:

```bash
git worktree add /tmp/codex-wt -b codex/attempt
codex exec $(python3 scripts/codex_pick_model.py) \
  -s workspace-write -C /tmp/codex-wt "<task>" < /dev/null
git -C /tmp/codex-wt diff main   # review before it touches your tree
```

## Four shapes of delegation

These all resolve the model once up front (see the shell-splitting note above
for why the values are kept in separate quoted variables):

```bash
eval "$(python3 scripts/codex_pick_model.py --export)"
MODEL=(-m "$CODEX_MODEL" -c model_reasoning_effort="$CODEX_EFFORT")
```

`MODEL` is an array, expanded below as `"${MODEL[@]}"` — safe in both bash and
zsh. If arrays feel like overkill for a one-off, just inline
`$(python3 scripts/codex_pick_model.py)` instead.

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
codex exec review "${MODEL[@]}" --base main --ephemeral < /dev/null
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

## Long runs will outlive your default timeout

A real Codex task runs for minutes — often longer than a default Bash timeout,
and a timeout kills the run with nothing to show for the tokens spent. Two ways
to handle it, both fine:

- **Run it in the background** and collect the output file when it finishes.
  Best for anything you expect to take a while, since it doesn't block you.
- **Raise the timeout explicitly** on the tool call. Simpler when you need the
  answer before you can do anything else.

Either way, redirect to files rather than relying on scrollback:

```bash
codex exec -s read-only "<task>" < /dev/null > answer.md 2> progress.log
```

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

Paths below are relative to this skill's directory. You'll generally be running
`codex` from the target repository instead, so resolve them against the skill
directory — e.g. `python3 <skill-dir>/scripts/codex_pick_model.py` — rather than
assuming the current working directory.

Read these as needed rather than up front:

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
  `python3 scripts/codex_digest.py run.jsonl`

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
is wrong — that output is the authority, and it beats any documentation
including this file. The behaviors described here were verified against
**codex-cli 0.146.0**; the notable divergences from the published docs (no
`-a/--ask-for-approval`, no `--search`, deprecated `--full-auto`) held across
0.144.1 and 0.146.0, but re-check rather than trusting that they still do.
