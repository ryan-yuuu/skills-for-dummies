# Handoff: reviewing the `codex` skill

You are picking up review of `skills/codex/` with no prior context. This document
exists so you don't repeat nine rounds of discovery.

**Read this before reviewing anything.** The most expensive mistakes in this
skill's history were not wrong facts — they were *correct-looking verifications*
that were quietly confounded. Section 3 is the important part.

---

## 1. What the skill is

`skills/codex/` teaches an agent to delegate work to the **OpenAI Codex CLI**
(`codex exec`) headlessly: second opinions, code review, scoped implementation,
design critique, structured extraction.

```
skills/codex/
├── SKILL.md                    decision + rules (always loaded when the skill triggers)
├── references/
│   ├── flags.md                canonical: CLI behavior, flag tables, evidence
│   ├── json-events.md          canonical: --json event schema, jq recipes
│   └── patterns.md             canonical: worked recipes
└── scripts/
    ├── codex_pick_model.py     resolves strongest model + supported effort from the live catalog
    └── codex_digest.py         condenses a --json event stream
```

**Content rule the files follow** (violating it caused ~8 defects across rounds
4–7): SKILL.md holds the *rule*, enough to write the right command. References
hold the *evidence*, exhaustive tables, and worked recipes. Cross-file
references get a sentence and a link — never restated reasoning. When you fix a
fact, fix the canonical copy and **delete** any duplicate rather than editing
both.

Verified against **codex-cli 0.146.0**. The flag surface moves between releases;
`codex exec --help` outranks the docs and this file.

---

## 2. Verification tooling (run this first, and after every change)

```bash
python3 scripts/codex-skill-verify/facts.py        # 88 load-bearing facts still present?
python3 scripts/codex-skill-verify/verify.py       # ~60 text + script behavior assertions
python3 scripts/codex-skill-verify/verify_exec.py  # documented shell recipes actually EXECUTE
python3 .claude/skills/skill-creator/scripts/quick_validate.py skills/codex
```

All four must pass. What each is for:

- **`facts.py`** — a file-agnostic inventory. Consolidation moves things, so it
  asserts a fact still exists *somewhere*, not where. It tracks **remedies as
  well as claims**: a pruning pass once deleted the only stated fix for a
  problem the skill still raised, while an inventory of claims alone reported
  "0 missing". A hazard with no remedy is worse than silence.
- **`verify.py`** — includes `edit()`, which refuses to no-op. Use it for every
  documentation change. Three "fixes" were once `str.replace()` calls against
  strings that didn't exist; they silently did nothing and were reported as
  fixed for three consecutive rounds.
- **`verify_exec.py`** — runs the documented git/shell recipes in throwaway
  repos. Added because the text-presence harness passed a documented command
  that returned a *file* where the prose promised a *directory*. Presence is not
  correctness.

---

## 3. Methodology — read this before trusting any result

Every one of nine rounds refuted a claim previously asserted as verified. Every
single failure had the same shape: **one observation consistent with two
explanations, and the discriminating condition never varied.**

### Confounders that have actually bitten

| Variable | What it hid |
|---|---|
| **Project trust** — codex *writes* a trust entry for the git repo root when a run **creates** a session with a non-`read-only` sandbox | The default sandbox, twice. Sequential probes in one directory are confounded. **Use a fresh `CODEX_HOME` + fresh repo per probe.** |
| **`approvals_reviewer` in config** | Without it the `approval:` header prints `never` for everything — hid a real `--full-auto` difference for three rounds |
| **Model `tool_mode`** | `gpt-5.6-*` are `code_mode_only` and send no top-level `tools`; `gpt-5.5` and older do. One model's payload says nothing about the other |
| **Sandbox mode when capturing web-search payloads** | `danger-full-access` flips `external_web_access` to true |
| **Tool *presence* vs tool *contents*** | `web_search` can be present with `external_web_access: false` |
| **`-m zzz-not-real` in behavioral probes** | It aborts before the behavior under test. One round wrongly concluded `resume` exits 1 because of it |
| **Isolated vs the user's real config** | Test both. Testing only an isolated `CODEX_HOME` hid a CRITICAL |

### Harness hazards that produced wrong conclusions

- **Pass flags as an argv array, never an unquoted string.** zsh does not
  word-split parameter expansions, so `FLAGS="-s danger-full-access"; codex $FLAGS`
  sends **one** argument and your flag never reaches the binary. This produced
  two wrong refutations. Self-test in bash *and* zsh before trusting anything.
- **`timeout` does not exist on macOS.** A check piped through it exited 127,
  grep received nothing, and the result was read as "clean" while the bug was
  still there. Use Python's `subprocess(timeout=...)`.
- **A failed assertion mid-batch skips every later edit.** Apply edits
  independently, then verify *every* intended change is present — not just the
  ones you spot-check.

### Free ways to verify (no paid inference)

- `--help` on every subcommand; parse-rejection probes (exit 2, cost nothing)
- `-m zzz-not-real` — fails *after* the header prints and *after* any trust write
- `codex debug models`, `codex doctor`, `codex sandbox`
- A **local fake `model_provider`** — captures real request bodies and lets runs
  complete at zero cost:
  `-c model_provider=fake -c model_providers.fake.base_url=http://127.0.0.1:PORT/v1 -c model_providers.fake.env_key=FAKE_KEY`

### Never run these

`codex`, `codex resume`, `codex fork`, `codex cloud` — all open a UI and **hang
your session**. `codex app` launches a desktop GUI. Verify their behavior from
`--help` only.

### Don't modify the user's `~/.codex/config.toml`

Hash it before and after. A non-`read-only` run appends a trust entry — earlier
sessions polluted it with three stale scratchpad entries that had to be cleaned
up by hand.

---

## 4. State at handoff

Nine review rounds, 20 independent reviewer passes. Rounds 8 and 9 both returned
**0 CRITICAL**. Round 9 returned 6 MUST-FIX, all fixed and verified.

**Round 10 was never run**, so the round-9 fixes are unreviewed. Every prior
round's fixes introduced at least one new defect, so treat that as the highest
risk area. What round 9 changed:

- `render_list` now calls `_rank` (a float-priority regression: rankability had
  been duplicated in two places and the display copy went stale)
- Digest item identity is **turn-scoped** (ids restart per turn, so a hung
  command in turn 1 matched turn 2's completion)
- `patterns.md`: worktree section now says the worktree holds the **committed**
  tree only; the `gh pr comment` example no longer posts model output unread;
  the false "which stage 1 just marked trusted" attribution is corrected
- `SKILL.md`: `resume` rejects `-C` (so a write-enabled resume cannot be
  isolated); header field list now includes `reasoning summaries`
- `flags.md`: regained the `--json` verification remedy — SKILL.md had been
  linking to it for "full resolution rules" while holding more detail itself

### Known open items (all NICE-TO-HAVE, none blocking)

- SKILL.md is **524 lines** against a `<500` guideline. Reviewers proposed ~45
  lines of moves: header-verification detail → `flags.md`, the `--export`
  variant → `patterns.md`, trim "Choosing an effort level".
- Duplication persists in ~5 places (the "takes minutes" note appears 3×; `-i`
  variadic and `--output-schema` each appear 2×). This is the mechanism behind
  earlier defect clusters — collapse to one canonical copy plus links.
- `$CODEX_HOME` is used but never defined in `flags.md`/`patterns.md` scope
  (`$SKILL_DIR` is handled correctly everywhere by contrast).
- Description is 967/1024 chars — only 57 chars of headroom.
- Minor wrap scars: over-long lines at a few spots; one double blank line.

### Settled — do not re-litigate without new evidence

These were each refuted at least once and are now verified correct. If you think
one is wrong, you are probably hitting a confounder from section 3:

- Trust is written on **session creation** with a non-`read-only` sandbox, keyed
  on the **git repo root**; a genuine `resume` writes none; matching is an
  **exact** match on workdir *or* repo root, not a prefix walk; a worktree run
  trusts the **main** repo.
- `workspace-write` blocks network; `network_access=true` enables it; trust does
  not relax it.
- `resume` rejects `-s` and `-C`, inherits neither sandbox nor model nor effort,
  and **silently starts a fresh session at exit 0** on an unknown thread *name*
  or `--last` with no session (only an unknown well-formed UUID exits 1).
- `--full-auto` also forces `approval_policy=never`; visible only when
  `approvals_reviewer` is set.
- The `approval:` header is not evidence either way.
- Exit codes 0/1/2; **config-load errors are 1**, not 2.
- `web_search`: default `cached` = `external_web_access:false` under `read-only`
  and `workspace-write`; `danger-full-access`/`--yolo`/`live`/`indexed` = true;
  `disabled` removes the tool; **all no-ops on `gpt-5.6-*`**.

---

## 5. Suggested first moves

1. Run all four checks in section 2. They should be green on a clean checkout.
2. Review the round-9 changes listed in section 4 — that code and prose is the
   least-reviewed material in the skill.
3. If you verify a behavioral claim, name the alternative explanation and run
   the experiment that separates them. Write the discriminating experiment down.
4. When you fix something, add an assertion to `verify.py` (or a fact to
   `facts.py`) so it cannot silently regress. That is how each round's findings
   were prevented from recurring.

Reproduce any reviewer finding yourself before acting on it. Twice in this
skill's history a *true* statement was "corrected" because a reviewer's evidence
was confounded, and once a fact was written into the docs from a report that was
never tested.
