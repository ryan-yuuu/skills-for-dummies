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
- [Diagnosing a broken environment](#diagnosing-a-broken-environment)
- [Global flags that don't propagate to `exec`](#global-flags-that-dont-propagate-to-exec)
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
| `-o, --output-last-message <FILE>` | Write the final message to `FILE`. Also prints to stdout *in plain mode*; under `--json` stdout is the event stream, so the file is the only place the final message appears on its own. |
| `--output-schema <FILE>` | Path to a JSON Schema file constraining the final response. Path only — not inline JSON. |
| `--color <always\|never\|auto>` | Default `auto`. Use `never` when capturing to a file that something else parses. |

### Sandbox and permissions

| Flag | Effect |
|---|---|
| `-s, --sandbox <MODE>` | `read-only`, `workspace-write`, `danger-full-access`. The built-in default is `read-only`, but user config overrides it — see below. |
| `--add-dir <DIR>` | Extra writable directory alongside the workspace. Prefer this over escalating to full access. |
| `--dangerously-bypass-approvals-and-sandbox` | No sandbox at all. Only inside an externally sandboxed environment. |
| `--dangerously-bypass-hook-trust` | Runs enabled hooks without persisted trust. Only when hook sources are already vetted. |
| `--skip-git-repo-check` | Allow running outside a Git repository. |

**Project trust silently changes the default sandbox.** Verified — the same
`codex exec` with no `-s`:

| Working directory | Reported sandbox |
|---|---|
| Untrusted directory | `read-only` |
| Project with `trust_level = "trusted"` in `$CODEX_HOME/config.toml` | `workspace-write [workdir, /tmp, $TMPDIR]` |
| Any directory, with `--ignore-user-config` | `read-only` |

**Codex writes the trust entry itself.** Any run whose sandbox resolves to
something other than `read-only` (`-s`, `-c sandbox_mode`, a config value,
`--full-auto`, `--yolo`) appends `[projects."<workdir>"] trust_level =
"trusted"` to `$CODEX_HOME/config.toml`. Verified on a fresh `CODEX_HOME` and a
fresh repo: one `-s workspace-write` run that failed at the API still wrote it,
and the next bare `codex exec` then resolved to `workspace-write`. **Neither
`--ephemeral` nor `--ignore-user-config` prevents the write** — they change what
a run reads, not what it records.

So delegating a single implementation task permanently raises the default for
that repository. Always pass `-s` explicitly.

Trust is matched by **exact git repo root** of the effective workdir: a nested
repo inside a trusted repo is *not* trusted, a subdirectory of one is, a
worktree of a trusted repo inherits trust, and `-C/--cd` selects the directory
that gets checked. Trust does not relax the network block.

**`workspace-write` blocks network access by default.** Verified with
`codex sandbox`: `curl` under `workspace-write` couldn't resolve DNS, and
returned 200 once network access was enabled. Since `exec` has no approval
prompt to escalate through, a task whose tests fetch dependencies simply fails.
Enable it deliberately:

```bash
codex exec -s workspace-write -c sandbox_workspace_write.network_access=true "<task>" < /dev/null
```

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
| `-i, --image <FILE>...` | Attach image(s). **Variadic — it swallows the prompt.** `codex exec -i pic.png "do the thing"` consumes the prompt as a second image path and then blocks reading stdin. Put `-i` *after* the prompt, or separate with `--`. (On `resume` it's non-variadic and safe.) |

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

**`resume` has no `-s/--sandbox` flag, and it does *not* inherit the original
session's sandbox** — it re-resolves the default for the current directory,
which in a trusted project is `workspace-write` (see the trust table above).
Verified in both directions: a session started `-s read-only` came back as
`workspace-write` on resume, and one started `-s danger-full-access` also came
back as `workspace-write`. So resuming can silently *escalate* a deliberately
restricted session. There is also no `-C/--cd`, `--add-dir`, `--color`,
`-p/--profile`, `--oss`, or `--local-provider`.

To constrain a resumed run, override the config key directly:

```bash
SESSION=$(jq -r 'select(.type=="thread.started") | .thread_id' run.jsonl)
codex exec resume "$SESSION" -c sandbox_mode='"read-only"' "<follow-up>" < /dev/null
```

Model and reasoning effort are **not** inherited either — they resolve from
flags and config on every resume. Re-pass `-m` and `-c model_reasoning_effort=`
on each resume if you want them held steady.

Resuming requires a persisted session, so a run started with `--ephemeral`
cannot be resumed.

**`resume` can silently start a fresh session.** An unknown thread *name*, or
`--last` where the directory has no sessions, begins a new context-free session
and exits `0` — only a well-formed but unknown UUID exits `1`. Assert the
resumed `thread_id` rather than relying on the exit code, or stage 2 will look
successful while having lost everything stage 1 learned.

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

All four targets are mutually exclusive at parse time — any pair errors out.

`--title <TITLE>` is only half-enforced: used alone it hard-errors demanding
`--commit`, but combined with `--base` or `--uncommitted` it parses cleanly and
is silently ignored. Don't read a successful parse as proof it took effect.

**`review` rejects most of `exec`'s flags** — the same class of surprise as
`resume`, and more consequential because this is the review path. Rejected:
`-s/--sandbox`, `-C/--cd`, `--add-dir`, `--color`, `-p/--profile`, `-i/--image`,
`--oss`. It accepts `-c`, `-m`, `--json`, `-o`, `--output-schema`,
`--ephemeral`, `--strict-config`, `--ignore-user-config`, `--ignore-rules`,
`--skip-git-repo-check`, `--enable/--disable`, and the two `--dangerously-*`
flags.

Since there's no `-s`, constrain its sandbox through config:

```bash
codex exec review --base main -c sandbox_mode='"read-only"' < /dev/null
```

Pairs well with `--output-schema` when you want findings as structured data
rather than prose you have to parse.

## Model selection and reasoning effort

`codex debug models` prints the catalog this binary can actually see, as JSON.
It's an **experimental** subcommand upstream ("may be removed or changed"), so
treat its field names as liable to move — `codex_pick_model.py` exits non-zero
with a clear message rather than emitting garbage flags if the shape changes,
letting you fall back to running without `-m`.

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

Effort levels, weakest to strongest: `minimal`, `low`, `medium`, `high`,
`xhigh`, `max`, `ultra` (`ultra` adds automatic task delegation).

This vocabulary **diverges from the published docs**, which document
`minimal | low | medium | high | xhigh` and no `max`/`ultra`. Conversely
`minimal` appears in the docs but is supported by no model in the observed
catalog. Support also varies by model — in one observed catalog the top two
supported all of `low`…`ultra`, the third stopped at `max`, and older ones
stopped at `xhigh`. Validate before passing one:

```bash
codex debug models | jq -r --arg m "gpt-5.6-sol" \
  '.models[] | select(.slug==$m) | .supported_reasoning_levels[].effort'
```

There is **no `--effort` flag**. Effort is set only via config override:

```bash
codex exec -m <slug> -c model_reasoning_effort=xhigh "<task>" < /dev/null
```

`$SKILL_DIR/scripts/codex_pick_model.py` (see `SKILL.md` for `SKILL_DIR`) does
the selection, validation, and fallback in one step, and is the reason nothing in this skill hardcodes a model name.

Both settings are echoed in the stderr header (`model:` / `reasoning effort:`)
in plain mode. The header shows the **resolved** value — flag, then `-c`, then
the user's `config.toml` — so `reasoning effort: xhigh` does not prove your flag
landed if their config already said `xhigh`; vary the value if you need
certainty. `none` means nothing set it and the model's catalog default applies.
**`--json` suppresses the header**, and no event reports model or effort, so
JSON runs offer no way to confirm after the fact.

## Config overrides with `-c`

`-c` reaches settings that have no dedicated flag. The value is parsed as TOML,
so strings generally need quotes that survive your shell.

| Override | Purpose |
|---|---|
| `-c model_reasoning_effort=xhigh` | Raise reasoning effort. The main quality lever, since `exec` has no `--effort` flag. Confirmed in the run header. |
| `-c model="gpt-5.6-sol"` | Equivalent to `-m`. |
| `-c sandbox_mode='"read-only"'` | Set the sandbox where no `-s` flag exists — notably on `resume`. Verified. |
| `-c shell_environment_policy.inherit=all` | Control which environment variables reach spawned commands. |
| `-c sandbox_workspace_write.network_access=true` | Allow network under `workspace-write`. |

`sandbox_permissions` appears in codex's own `-c` help text but is **not a
recognized key** in 0.146.0 — `--strict-config` rejects it exactly like a
nonsense key, and without that flag it is accepted and silently does nothing.

Unrecognized `-c` keys are accepted silently; `--strict-config` turns that into
an error. To confirm an override landed, read the stderr header — see
[Model selection and reasoning effort](#model-selection-and-reasoning-effort),
which also covers the `--json` caveat. The header's `approval:` line echoes the resolved `approval_policy` — it can
read `on-request` — but that describes the setting, not `exec`'s behavior:
nothing can approve non-interactively whatever it says.

## Authentication

`codex exec` reuses saved CLI auth by default; `codex login status` exits `0`
when credentials exist, which makes it a usable precondition check.

`CODEX_API_KEY` overrides auth for a single invocation. Upstream documents it as
intended for `codex exec`; the binary resolves it as part of a general auth
chain alongside `OPENAI_API_KEY` and `CODEX_ACCESS_TOKEN`, so don't rely on it
being scoped to `exec`.

```bash
CODEX_API_KEY="$MY_CODEX_KEY" codex exec --json "<task>" < /dev/null
```

Set it inline for the one command rather than exporting it job-wide — and the
same applies to `OPENAI_API_KEY`. Anything else running in that process
environment (build scripts, tests, dependency lifecycle hooks, a compromised
action) can read an exported key. In GitHub Actions, prefer
[`openai/codex-action`](https://github.com/openai/codex-action), which proxies
the key instead of exposing it to job steps.

## Diagnosing a broken environment

When a run fails for environmental rather than logical reasons — missing auth,
bad config, no Git repo — `codex doctor` reports on installation, config, auth,
runtime, Git, and terminal health in one pass. Reach for it before re-running a
failing command with different flags.

## Global flags that don't propagate to `exec`

These exist on the top-level `codex` command but are **rejected as unexpected
arguments** on `codex exec`. The docs say global flags mostly propagate, "see
the relevant command help for exceptions" — these are those exceptions, not a
version mismatch:

| Flag | On `codex` | On `codex exec` | Use instead |
|---|---|---|---|
| `-a, --ask-for-approval` | Yes | **Rejected** | Nothing can approve non-interactively. `-c approval_policy=never` is the documented non-interactive setting; the sandbox is the real control. |
| `--search` | Yes | **Rejected** | `-c web_search='"live"'` — see below. |

**Web search isn't simply off under `exec`.** `web_search` is a valid config key
accepting `disabled`/`cached`/`indexed`/`live`, and upstream documents the
default as `"cached"` with full-access sandboxes promoting it to `"live"`.
Neither default was observable from this build — captured request bodies carried
no `tools` entry at all — so treat `-c web_search='"live"'` as the toggle and
the defaults as unverified.

### Hidden flags

Some accepted flags don't appear in `--help`, so `--help` proves a flag exists
but never proves one doesn't:

| Flag | Notes |
|---|---|
| `--full-auto` | Deprecated; warns, then applies `workspace-write`. Under `exec` the only observable difference from `-s workspace-write` is the warning. |
| `--yolo` | Alias for `--dangerously-bypass-approvals-and-sandbox`. Worth recognizing in someone else's script. |
| `--experimental-json` | Alias for `--json`. |

## Exit codes and failure modes

`0` on success, `1` on failure. Verified failures:

- **Invalid model** — warns about missing metadata, then `ERROR: {"type":"error","status":400,...}` on stderr, empty stdout, exit `1`.
- **Outside a Git repository** — *"Not inside a trusted directory and `--skip-git-repo-check` was not specified."*
- **Required MCP server fails to initialize** — a server configured `required = true` aborts the run rather than continuing degraded.

In **plain mode** a failed run leaves stdout empty, so an empty final message is
a failure signal. This does *not* hold under `--json`, where the same failure
produces a well-formed event stream and a silent stderr — see
`json-events.md`. The exit code is the reliable check in both modes:

```bash
if ! codex exec -s read-only "<task>" < /dev/null > out.md 2> err.log; then
    echo "codex failed:"; tail -20 err.log; exit 1
fi
```
