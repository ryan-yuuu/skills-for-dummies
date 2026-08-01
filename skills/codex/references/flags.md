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

**Codex writes the trust entry itself**, when a run *creates a session* with a
sandbox other than `read-only` (`-s`, `-c sandbox_mode`, a config value,
`--full-auto`, `--yolo`). The key is the **git repo root** of the workdir — or
the workdir itself outside a repo. Verified: a run with `-C <repo>/sub/deeper`
wrote `[projects."<repo>"]`.

**Genuinely resuming a session does not write one.** Verified: `codex exec
resume <id> -c sandbox_mode='"workspace-write"'` left the config untouched,
while an otherwise identical plain `codex exec` wrote an entry. The exception is
telling — a resume that *silently starts fresh* (unknown thread name, or
`--last` with no session) is creating a session, so it does write one. The trust
entry appearing after a resume is therefore a signal that the resume didn't
resume. Verified on a fresh `CODEX_HOME` and a
fresh repo: one `-s workspace-write` run that failed at the API still wrote it,
and the next bare `codex exec` then resolved to `workspace-write`. **Neither
`--ephemeral` nor `--ignore-user-config` prevents the write** — they change what
a run reads, not what it records.

So delegating a single implementation task permanently raises the default for
that repository. Always pass `-s` explicitly.

**Matching is broader than writing**, so trust can be granted by entries a run
would never create. Writing produces a repo-root key (or the workdir outside a
repo); matching accepts an **exact** entry on either the workdir itself or its repo
root — it is not a prefix walk, so `[projects."/Users/you"]` does not trust
every repo beneath it (verified). Verified: a hand-written `[projects."<repo>/sub"]` grants
`workspace-write` to a run in `<repo>/sub`, a key no write path produces. So
auditing only repo-root entries under-predicts where write access already
exists.

Otherwise: a nested repo inside a trusted repo is *not* trusted; a subdirectory
of a trusted root is — not by prefix, but because its repo root is the trusted
key; a worktree resolves to its main repo's root (inheriting
trust and writing trust there), and `-C/--cd` selects the directory checked
rather than your shell's cwd. Trust does not relax the network block.

**`workspace-write` blocks network access by default.** Verified with two
otherwise-identical runs differing only in the flag: `curl` could not resolve
DNS under `workspace-write`, and returned 200 with network access enabled. The
header also states it — `(network access enabled)` is appended to the sandbox
line when it is on. Since `exec` has no approval
prompt to escalate through, a task whose tests fetch dependencies simply fails.
Enable it deliberately:

```bash
codex exec -s workspace-write -c sandbox_workspace_write.network_access=true "<task>" < /dev/null
```

`--full-auto` still parses but warns: *"`--full-auto` is deprecated; use
`--sandbox workspace-write` instead."* Prefer the explicit flag — but note the
two are **not** equivalent; see [Hidden flags](#hidden-flags).

### Model and configuration

| Flag | Effect |
|---|---|
| `-m, --model <MODEL>` | Model to use. Invalid names fail at request time with HTTP 400, not at parse time. |
| `-c, --config <key=value>` | Override a `config.toml` value. Dotted paths for nesting. Value parsed as TOML, falling back to a literal string. |
| `-p, --profile <NAME>` | Layer `$CODEX_HOME/<name>.config.toml` over the base config. |
| `--enable <FEATURE>` / `--disable <FEATURE>` | Repeatable. Equivalent to `-c features.<name>=true` or `=false`. |
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
flags and config on every resume, so an unflagged resume can *switch models*
(observed: a `gpt-5.5` session resuming as `gpt-5.6-sol` at effort `none`), not
merely lose the effort setting. Codex warns on the switch — under `--json` it
arrives as an `error` item — but only the *first* time, because that resume
rewrites the session's recorded model. Re-pass `-m` and `-c model_reasoning_effort=`
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

`review` follows the ordinary sandbox rule — a `read-only` review writes no
trust entry (verified). Pin `-c sandbox_mode='"read-only"'` anyway, since it has
no `-s` and would otherwise inherit a trusted project's `workspace-write`.

`--title <TITLE>` is only half-enforced: used alone it hard-errors demanding
`--commit`, but combined with `--base` or `--uncommitted` it parses cleanly and
is silently ignored. Don't read a successful parse as proof it took effect.

**`review` rejects most of `exec`'s flags** — the same class of surprise as
`resume`, and more consequential because this is the review path. Rejected:
`-s/--sandbox`, `-C/--cd`, `--add-dir`, `--color`, `-p/--profile`, `-i/--image`,
`--oss`, `--local-provider`. It accepts `-c`, `-m`, `--json`, `-o`, `--output-schema`,
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
The CLI doesn't mark `debug` experimental (unlike `cloud`, `app-server`,
`remote-control`, `exec-server`), but it is a debugging surface rather than a
supported API, so treat its field names as liable to move — `codex_pick_model.py` exits non-zero
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
| `priority` | Rank; **lower is stronger**. `1` is the current frontier coding model. Not a total order — values can tie, so break ties deterministically. |
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
which also covers the `--json` caveat. The header's `approval:` line is not a reliable signal: it reads `never` under
most configurations, but echoes the configured `approval_policy` when
`approvals_reviewer` is set. Neither reading changes `exec`'s behavior — nothing
can approve non-interactively.

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
| `--search` | Yes | **Rejected** | `web_search` is a config key, but what it does depends on the model — see below before relying on it. |

**`web_search` behaves differently depending on the model**, which makes it
easy to reason about wrongly. Values: `disabled`, `cached` (the default),
`indexed`, `live`. Captured request bodies:

On `tool_mode=null` models (`gpt-5.5` and older) a `web_search` tool is sent and
`external_web_access` is what varies:

| Setting | `external_web_access` |
|---|---|
| default / `"cached"` under `read-only` or `workspace-write` | `false` |
| default under `danger-full-access` (incl. `--yolo`, `--dangerously-bypass-…`) | **`true`** |
| `"live"` | `true` |
| `"indexed"` | `true` (plus `indexed_web_access: true`) |
| `"disabled"` | tool absent entirely |

`--full-auto` resolves to `workspace-write`, so it stays `false`. Enabling
network with `sandbox_workspace_write.network_access=true` does **not** flip it —
only the sandbox being `danger-full-access` does.

On `tool_mode=code_mode_only` models (all `gpt-5.6-*`) no `tools` array is sent
at all, no `web_search` appears anywhere in the request, and every setting above
is a no-op.

Two consequences. On `tool_mode=null` models, external web access is off by
default only while the sandbox is `read-only` or `workspace-write`; choosing
`danger-full-access` turns it on without you asking. And on the `gpt-5.6-*` models — which include the strongest
one this skill selects — the client sends no `web_search` tool at all, so
`-c web_search='"disabled"'` is a **no-op there**; don't treat it as a
containment control on those models.

This is client-side evidence from payloads captured over an HTTP
`wire_api=responses` endpoint; production uses a websocket transport, though the
payload structs are shared. It can't rule out server-side retrieval inside code
mode either. Treat it as "the flag does not do what you'd assume", not as proof
the model cannot search.

### Hidden flags

Some accepted flags don't appear in `--help`, so `--help` proves a flag exists
but never proves one doesn't:

| Flag | Notes |
|---|---|
| `--full-auto` | Deprecated; warns, then applies `workspace-write` **and** forces `approval_policy=never`, which `-s workspace-write` does not. (Visible only when `approvals_reviewer` is set — otherwise the header prints `never` either way, which is what made an earlier check conclude they were identical.) |
| `--yolo` | Alias for `--dangerously-bypass-approvals-and-sandbox`. Worth recognizing in someone else's script. |
| `--experimental-json` | Alias for `--json`. |

## Exit codes and failure modes

`0` on success, `1` on runtime failure, `2` on argument-parse failure —
a rejected flag, a missing required argument, or conflicting arguments.
Config-load errors (malformed TOML, wrong type, `--strict-config` rejections)
are `1`, not `2`. Verified failures:

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
