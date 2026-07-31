# Flag reference

Verified against **codex-cli 0.146.0** (and cross-checked against 0.144.1).
Flag surfaces move between releases — when something is rejected, run
`codex exec --help` rather than guessing, and consider `codex update`.

## Contents

- [`codex exec`](#codex-exec)
- [`codex exec resume`](#codex-exec-resume)
- [`codex exec review`](#codex-exec-review)
- [Model selection and reasoning effort](#model-selection-and-reasoning-effort)
- [Config overrides with `-c`](#config-overrides-with--c)
- [Authentication](#authentication)
- [Documented flags that don't exist here](#documented-flags-that-dont-exist-here)
- [Exit codes and failure modes](#exit-codes-and-failure-modes)

## `codex exec`

```
codex exec [OPTIONS] [PROMPT]
codex exec [OPTIONS] <COMMAND> [ARGS]
```

`PROMPT` is read from stdin when omitted or when given as `-`. When stdin is
piped *and* a prompt argument is present, the piped content is appended as a
`<stdin>` block — the argument is the instruction, stdin is the context.

### Output and format

| Flag | Effect |
|---|---|
| `--json` | Emit JSONL events on stdout, one per line. See `json-events.md`. |
| `-o, --output-last-message <FILE>` | Write the final message to `FILE`. Still prints to stdout. |
| `--output-schema <FILE>` | Path to a JSON Schema file constraining the final response. Path only — not inline JSON. |
| `--color <always\|never\|auto>` | Default `auto`. Use `never` when capturing to a file that something else parses. |

### Sandbox and permissions

| Flag | Effect |
|---|---|
| `-s, --sandbox <MODE>` | `read-only` (default), `workspace-write`, `danger-full-access`. |
| `--add-dir <DIR>` | Extra writable directory alongside the workspace. Prefer this over escalating to full access. |
| `--dangerously-bypass-approvals-and-sandbox` | No sandbox at all. Only inside an externally sandboxed environment. |
| `--dangerously-bypass-hook-trust` | Runs enabled hooks without persisted trust. Only when hook sources are already vetted. |
| `--skip-git-repo-check` | Allow running outside a Git repository. |

`--full-auto` still parses but warns: *"`--full-auto` is deprecated; use
`--sandbox workspace-write` instead."* Use the explicit flag.

### Model and configuration

| Flag | Effect |
|---|---|
| `-m, --model <MODEL>` | Model to use. Invalid names fail at request time with HTTP 400, not at parse time. |
| `-c, --config <key=value>` | Override a `config.toml` value. Dotted paths for nesting. Value parsed as TOML, falling back to a literal string. |
| `-p, --profile <NAME>` | Layer `$CODEX_HOME/<name>.config.toml` over the base config. |
| `--enable <FEATURE>` / `--disable <FEATURE>` | Repeatable. Equivalent to `-c features.<name>=true|false`. |
| `--strict-config` | Error on config keys this build doesn't recognize. Useful in CI to catch drift. |
| `--oss` | Use an open-source provider. |
| `--local-provider <lmstudio\|ollama>` | Which local provider to use with `--oss`. |

### Environment and session

| Flag | Effect |
|---|---|
| `-C, --cd <DIR>` | Working root for the agent. Essential for worktree isolation. |
| `--ephemeral` | Don't persist session files. Omit when you intend to `resume`. |
| `--ignore-user-config` | Skip `$CODEX_HOME/config.toml`. Auth still resolves via `CODEX_HOME`. |
| `--ignore-rules` | Skip user and project execpolicy `.rules` files. |
| `-i, --image <FILE>...` | Attach image(s) to the initial prompt. |

Together, `--ignore-user-config --ignore-rules --strict-config` give a run that
behaves the same regardless of local machine state — worth it in CI, where a
developer's personal config silently changing CI behavior is a real hazard.

## `codex exec resume`

```
codex exec resume [OPTIONS] [SESSION_ID] [PROMPT]
```

`SESSION_ID` accepts a UUID or a thread name; UUIDs win when the string parses
as one. Omit it and pass `--last` to continue the most recent session.

| Flag | Effect |
|---|---|
| `--last` | Resume the newest recorded session. |
| `--all` | Search all sessions, disabling the working-directory filter. |

Accepts `-c`, `-m`, `-i`, `--json`, `-o`, `--output-schema`, `--ephemeral`,
`--strict-config`, `--ignore-user-config`, `--ignore-rules`,
`--skip-git-repo-check`, `--enable/--disable`, and the two `--dangerously-*`
flags.

**`resume` has no `-s/--sandbox` flag, and it inherits the original session's
sandbox.** Verified: resuming a session that ran `workspace-write` produced a
header reading `sandbox: workspace-write [workdir, /tmp, $TMPDIR]` without any
sandbox flag being passed. This is a real footgun — a follow-up prompt you think
of as "just a question" still carries write access. There is also no `-C/--cd`,
`--add-dir`, `--color`, `-p/--profile`, `--oss`, or `--local-provider`.

To constrain a resumed run, override the config key directly:

```bash
codex exec resume "$SESSION" -c sandbox_mode='"read-only"' "<follow-up>" < /dev/null
```

Model and reasoning effort are likewise inherited, so a session started on a
weak model stays there unless you re-pass `-m` and `-c model_reasoning_effort=`.

Resuming requires a persisted session, so a run started with `--ephemeral`
cannot be resumed.

## `codex exec review`

```
codex exec review [OPTIONS] [PROMPT]
```

Runs a code review scoped to a review target. Targets are mutually exclusive:

| Flag | Scope |
|---|---|
| `--uncommitted` | Staged, unstaged, and untracked changes. |
| `--base <BRANCH>` | Changes relative to a base branch. |
| `--commit <SHA>` | Changes introduced by one commit. |
| *(bare `PROMPT`)* | Custom review instructions. |

`--title <TITLE>` adds a commit title to the summary and applies only with
`--commit`.

Pairs well with `--output-schema` when you want findings as structured data
rather than prose you have to parse.

## Model selection and reasoning effort

`codex debug models` prints the catalog this binary can actually see, as JSON:

```bash
codex debug models              # refreshes from the remote catalog
codex debug models --bundled    # only what ships with this binary; no network
```

Each entry carries the fields that make automatic selection possible:

| Field | Meaning |
|---|---|
| `slug` | The value for `-m`. |
| `priority` | Rank; **lower is stronger**. `1` is the current frontier coding model. |
| `visibility` | `list` for selectable models, `hide` for internal ones (e.g. `codex-auto-review`) — filter these out. |
| `default_reasoning_level` | What you get if you don't set effort. Frequently `low`, even on the top model. |
| `supported_reasoning_levels` | Array of `{effort, description}`. Not every model supports every level. |
| `display_name`, `description` | Human-readable labels. |
| `service_tiers`, `additional_speed_tiers` | Speed tiers such as `fast`, where offered. |

Strongest selectable model in one line:

```bash
codex debug models \
  | jq -r '[.models[] | select(.visibility=="list")] | sort_by(.priority) | .[0].slug'
```

Effort levels, weakest to strongest: `low`, `medium`, `high`, `xhigh`, `max`,
`ultra` (`ultra` adds automatic task delegation). Support varies by model — an
observed catalog had the top two models supporting all six while older ones
stopped at `xhigh` — so validate before passing one:

```bash
codex debug models | jq -r --arg m "gpt-5.6-sol" \
  '.models[] | select(.slug==$m) | .supported_reasoning_levels[].effort'
```

There is **no `--effort` flag**. Effort is set only via config override:

```bash
codex exec -m <slug> -c model_reasoning_effort=xhigh "<task>" < /dev/null
```

`scripts/codex_pick_model.py` does the selection, validation, and fallback in
one step, and is the reason nothing in this skill hardcodes a model name.

Both settings are echoed in the stderr header (`model:` / `reasoning effort:`)
in plain mode — read it to confirm an override landed instead of assuming it
did. **`--json` suppresses the header**, and no event in the stream reports the
model or effort, so JSON runs offer no way to confirm after the fact.

## Config overrides with `-c`

`-c` reaches settings that have no dedicated flag. The value is parsed as TOML,
so strings generally need quotes that survive your shell.

| Override | Purpose |
|---|---|
| `-c model_reasoning_effort=xhigh` | Raise reasoning effort. The main quality lever, since `exec` has no `--effort` flag. Confirmed in the run header. |
| `-c model="gpt-5.6-sol"` | Equivalent to `-m`. |
| `-c sandbox_mode='"read-only"'` | Set the sandbox where no `-s` flag exists — notably on `resume`. Verified. |
| `-c shell_environment_policy.inherit=all` | Control which environment variables reach spawned commands. |
| `-c 'sandbox_permissions=["disk-full-read-access"]'` | Fine-grained sandbox permissions. |

In plain mode the stderr header echoes the effective model, sandbox, approval
mode, reasoning effort, and session id. Read it to confirm an override actually
landed — unrecognized `-c` keys are otherwise accepted silently, which
`--strict-config` converts into an error. Note that `--json` suppresses this
header entirely.

## Authentication

`codex exec` reuses saved CLI auth by default; `codex login status` exits `0`
when credentials exist, which makes it a usable precondition check.

`CODEX_API_KEY` overrides auth for a single invocation and is supported **only**
on `codex exec`:

```bash
CODEX_API_KEY=<key> codex exec --json "<task>" < /dev/null
```

Set it inline for the one command rather than exporting it job-wide. Anything
else running in that process environment — build scripts, tests, dependency
lifecycle hooks — can read an exported key. In GitHub Actions, prefer
[`openai/codex-action`](https://github.com/openai/codex-action), which proxies
the key instead of exposing it to job steps.

## Documented flags that don't exist here

The published docs describe a build that differs from 0.144.1. These are
rejected as unexpected arguments on `codex exec`:

| Flag | Status | What to do instead |
|---|---|---|
| `-a, --ask-for-approval` | Not present | `exec` is non-interactive; the sandbox is the only control. |
| `--search` | Not present | No `exec`-level web search toggle on this build. |

`--full-auto` is present but deprecated (warns, then behaves as
`workspace-write`).

## Exit codes and failure modes

`0` on success, `1` on failure. Verified failures:

- **Invalid model** — warns about missing metadata, then `ERROR: {"type":"error","status":400,...}` on stderr, empty stdout, exit `1`.
- **Outside a Git repository** — *"Not inside a trusted directory and `--skip-git-repo-check` was not specified."*
- **Required MCP server fails to initialize** — a server configured `required = true` aborts the run rather than continuing degraded.

Because a failed run leaves **stdout empty**, treat an empty final message as a
failure signal and read stderr for the reason:

```bash
if ! codex exec -s read-only "<task>" < /dev/null > out.md 2> err.log; then
    echo "codex failed:"; tail -20 err.log; exit 1
fi
```
