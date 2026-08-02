#!/usr/bin/env python3
"""Pick the strongest available Codex model and emit ready-to-use flags.

Model names change every few releases, so hardcoding one guarantees the skill
goes stale and silently runs on a weaker model than the user is paying for.
`codex debug models` reports the catalog this binary actually sees, including a
`priority` ranking and each model's supported reasoning levels. This resolves
that at call time instead.

Note that `codex debug models` is an *experimental* subcommand upstream, so its
field names may change. Every field read here is treated as optional: if the
catalog can't be understood, this exits non-zero with a clear message so the
caller can fall back to invoking codex without `-m`, rather than emitting
garbage flags.

Usage:
    # Splice flags straight into a command. Inline $(...) is the portable form:
    # command substitution word-splits in both bash and zsh.
    codex exec $(python3 codex_pick_model.py) -s read-only "<task>" < /dev/null

    # To resolve once and reuse, use --export. Do NOT stash the flag string in a
    # variable and expand it unquoted -- zsh does not word-split parameter
    # expansions, so `$MF` arrives as one argument and the run fails.
    eval "$(python3 codex_pick_model.py --export)"
    codex exec -m "$CODEX_MODEL" -c model_reasoning_effort="$CODEX_EFFORT" ...

    python3 codex_pick_model.py                 # -m <best> -c model_reasoning_effort=xhigh
    python3 codex_pick_model.py --effort max    # request a specific effort
    python3 codex_pick_model.py --slug-only     # just the model slug
    python3 codex_pick_model.py --list          # show selectable models

Exit status: 0 on success; 1 when the catalog can't be loaded, nothing is
selectable, the requested model isn't selectable, or the resolved slug/effort
couldn't be spliced safely; 2 for bad arguments.

Only the default output mode enforces a shell-safe charset, because only it is
consumed by unquoted `$(...)`. `--export` quotes properly via shlex, and
`--slug-only`/`--effort-only` are meant to be quoted by the caller.

Effort defaults to `xhigh`. If the chosen model doesn't support the requested
level, this resolves *downward* to the strongest level it does support, so a
request can't silently become more expensive than what was asked for. It goes
above the request only when the model supports nothing lower, and says on stderr
which way it went. If the catalog uses an effort vocabulary this doesn't
recognize, it falls back to catalog order and says the direction is unknown.
"""

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys

# Weakest to strongest. `minimal` is documented upstream but absent from every
# model in the observed catalog; `max` and `ultra` are in the catalog but not in
# the published config reference. Keeping the union means this ranks correctly
# whichever vocabulary a given release actually ships.
EFFORT_ORDER = ["minimal", "low", "medium", "high", "xhigh", "max", "ultra"]

DEFAULT_EFFORT = "xhigh"

CATALOG_TIMEOUT_S = 45


def load_catalog(bundled_only=False):
    """Return the model catalog, falling back to the bundled copy if the
    network refresh fails (offline, restricted CI, expired auth)."""
    if not shutil.which("codex"):
        sys.exit("error: `codex` not found on PATH")

    attempts = [True] if bundled_only else [False, True]
    errs = []
    for bundled in attempts:
        cmd = ["codex", "debug", "models"] + (["--bundled"] if bundled else [])
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  errors="replace", timeout=CATALOG_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            errs.append(f"`{' '.join(cmd)}` timed out after {CATALOG_TIMEOUT_S}s")
            continue
        except OSError as exc:
            errs.append(f"could not run `{' '.join(cmd)}`: {exc}")
            continue
        if proc.returncode != 0:
            errs.append((proc.stderr or "").strip() or f"exit {proc.returncode}")
            continue
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            errs.append(f"unparseable catalog: {exc}")
            continue
        # Everything below is untrusted shape: guard rather than assume.
        if not isinstance(payload, dict):
            errs.append(f"catalog is {type(payload).__name__}, expected an object")
            continue
        raw_models = payload.get("models")
        if raw_models is not None and not isinstance(raw_models, list):
            errs.append(f"catalog `models` is {type(raw_models).__name__}, expected a list")
            continue
        models = [m for m in (raw_models or []) if isinstance(m, dict)]
        if models:
            if bundled and not bundled_only:
                print(f"note: using bundled catalog ({errs[0] if errs else 'refresh failed'})", file=sys.stderr)
            return models
        errs.append("catalog contained no usable model entries")

    seen, unique = set(), []
    for e in errs:
        flat = " ".join(str(e).split())
        if flat not in seen:
            seen.add(flat)
            unique.append(flat)
    sys.exit(f"error: could not load model catalog: {'; '.join(unique)}")


def selectable(models):
    """Models a user can actually pick.

    Allowlist: only `visibility: "list"` is selectable, so a novel value like
    `"beta"` is excluded rather than assumed safe. Falls back to "anything not
    explicitly hidden" only when NO entry claims `list`, which means the
    catalog's vocabulary changed.
    """
    # Allowlist, matching the documented rule (`list` selectable, `hide`
    # internal). A denylist would promote internal entries like
    # codex-auto-review the moment the catalog introduces a new value.
    # A catalog that drops the field entirely still degrades usefully: the
    # fallback below selects everything not explicitly hidden.
    named = [m for m in models if isinstance(m.get("slug"), str)]
    listed = [m for m in named if m.get("visibility") == "list"]
    if listed:
        return listed
    # No entry claims `list` -- the vocabulary changed. Fall back to "anything
    # not explicitly hidden", which is still better than selecting nothing.
    return [m for m in named if m.get("visibility") != "hide"]


def _rank(model):
    """The model's priority as an int, or None when it genuinely can't rank.

    A catalog shipping `1.0` instead of `1` must not lose to an int `2`:
    demoting it silently selects a weaker model, which is the failure this
    script exists to prevent. Int-valued floats are coerced, matching how
    codex_digest.py treats exit codes. Booleans are excluded because
    `True == 1` in Python and would otherwise rank as priority 1.
    """
    priority = model.get("priority")
    if isinstance(priority, bool):
        return None
    if isinstance(priority, int):
        return priority
    if isinstance(priority, float) and priority.is_integer():
        return int(priority)
    return None


def _priority_key(model):
    rank = _rank(model)
    # Unrankable entries sort last, then alphabetically, so ordering stays
    # deterministic rather than depending on catalog order.
    return (float("inf") if rank is None else rank, model.get("slug", ""))


def best_model(models):
    """Lowest `priority` wins -- the catalog ranks strongest first (priority 1
    is described as the latest frontier agentic coding model)."""
    pool = selectable(models)
    # Say so when a priority can't be ranked at all (a string, a bool, a
    # non-integral float). Such entries sort last, which can select a weaker
    # model than the catalog intends -- the failure this script exists to
    # prevent. Integral floats are handled by _rank and never reach here.
    unrankable = [m["slug"] for m in pool
                  if m.get("priority") is not None and _rank(m) is None]
    if unrankable:
        print(
            f"note: unrankable priority on {', '.join(unrankable)}; treating as lowest rank. "
            f"Check `codex debug models` before trusting the selection.",
            file=sys.stderr,
        )
    ranked = sorted(pool, key=_priority_key)
    if not ranked:
        sys.exit("error: no selectable models in catalog")
    return ranked[0]


def supported_efforts(model, warn=False):
    """Effort levels this model supports, ordered weakest to strongest."""
    levels = model.get("supported_reasoning_levels")
    if not isinstance(levels, list):
        return []
    raw = [lvl.get("effort") for lvl in levels if isinstance(lvl, dict) and isinstance(lvl.get("effort"), str)]
    known = [e for e in EFFORT_ORDER if e in raw]
    if known:
        unknown = [e for e in raw if e not in EFFORT_ORDER]
        if unknown and warn:
            print(
                f"note: ignoring unrecognized effort name(s) in catalog: {', '.join(unknown)}",
                file=sys.stderr,
            )
        return known
    if raw and warn:
        # The catalog renamed the vocabulary. Preserve its ordering rather than
        # silently reporting "no levels", which would disable validation.
        print(
            f"note: unrecognized effort names in catalog ({', '.join(raw)}); using catalog order",
            file=sys.stderr,
        )
    return raw


def resolve_effort(model, requested):
    """Return an effort the model actually supports, resolving downward.

    Emitting an unsupported level makes the whole `codex exec` call fail, but
    silently *escalating* is worse than failing: it spends more of the user's
    quota than they asked for. So prefer the strongest supported level that is
    still <= the request, and only exceed the request when nothing lower exists.
    """
    available = supported_efforts(model)
    if not available:
        # Catalog didn't report levels; trust the caller rather than block.
        return requested
    if requested in available:
        return requested
    # Only now is the catalog's vocabulary worth commenting on.
    available = supported_efforts(model, warn=True)

    # `requested` is CLI-constrained by argparse choices, but this is also an
    # importable function: keep the membership test so callers can't crash it.
    if requested in EFFORT_ORDER and all(a in EFFORT_ORDER for a in available):
        cutoff = EFFORT_ORDER.index(requested)
        lower = [a for a in available if EFFORT_ORDER.index(a) < cutoff]
        choice = lower[-1] if lower else available[0]
    else:
        choice = available[0]

    # `choice` may be a catalog-native name absent from EFFORT_ORDER, so only
    # claim a direction when both names are rankable.
    if choice in EFFORT_ORDER and requested in EFFORT_ORDER:
        direction = "down " if EFFORT_ORDER.index(choice) < EFFORT_ORDER.index(requested) else "up "
    else:
        direction = "(direction unknown — unfamiliar catalog vocabulary) "
    print(
        f"note: {model.get('slug', '?')} does not support effort '{requested}'; "
        f"resolving {direction}to '{choice}' (supports: {', '.join(available)})",
        file=sys.stderr,
    )
    return choice


def render_list(models):
    rows = sorted(selectable(models), key=_priority_key)
    hidden = len(models) - len(rows)
    width = max(5, max((len(m["slug"]) for m in rows), default=10))
    out = [f"{'PRIO':<5} {'MODEL':<{width}}  {'DEFAULT':<8} EFFORTS"]
    for m in rows:
        # A key present with a JSON null survives .get(k, default), so coerce
        # rather than relying on the default -- the live catalog does ship nulls.
        # Display via _rank so the column always agrees with the sort. A second
        # copy of this test is what let the table print "?" in the first row.
        rank = _rank(m)
        prio = "?" if rank is None else str(rank)
        level = m.get("default_reasoning_level")
        level = level if isinstance(level, str) else "?"
        out.append(f"{prio:<5} {m['slug']:<{width}}  {level:<8} {','.join(supported_efforts(m))}")
    if hidden:
        out.append(f"({hidden} entr{'y' if hidden == 1 else 'ies'} omitted -- not selectable)")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--effort",
        default=DEFAULT_EFFORT,
        choices=EFFORT_ORDER,
        help=f"reasoning effort (default: {DEFAULT_EFFORT})",
    )
    ap.add_argument("--model", help="use this slug instead of auto-selecting the strongest")
    ap.add_argument("--bundled", action="store_true", help="skip the network refresh")
    # These four each own stdout, so allowing two would emit an unusable mix.
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--slug-only", action="store_true", help="print only the model slug")
    mode.add_argument("--effort-only", action="store_true", help="print only the resolved effort")
    mode.add_argument(
        "--export",
        action="store_true",
        help="emit shell assignments for CODEX_MODEL/CODEX_EFFORT (use with eval)",
    )
    mode.add_argument("--list", dest="do_list", action="store_true", help="print selectable models and exit")
    args = ap.parse_args()

    models = load_catalog(bundled_only=args.bundled)

    if args.do_list:
        print(render_list(models))
        # Consistent with the default path, which exits 1 on the same catalog.
        return 0 if selectable(models) else 1

    if args.model is not None:
        match = next((m for m in selectable(models) if m.get("slug") == args.model), None)
        if match is None:
            available = ", ".join(m["slug"] for m in selectable(models)) or "none"
            sys.exit(f"error: model '{args.model}' not selectable. Available: {available}")
        model = match
    else:
        model = best_model(models)

    effort = resolve_effort(model, args.effort)

    if args.slug_only:
        print(model["slug"])
    elif args.effort_only:
        print(effort)
    elif args.export:
        # shlex.quote, not hand-rolled quoting: these values are consumed by
        # `eval`, and a slug containing a quote would otherwise execute.
        print(f"CODEX_MODEL={shlex.quote(model['slug'])}")
        print(f"CODEX_EFFORT={shlex.quote(effort)}")
    else:
        # This form is spliced with unquoted $(...), which word-splits but does
        # NOT remove quotes -- so quoting here would produce broken argv.
        # Refuse anything that couldn't survive the splice instead.
        for label, value in (("model", model["slug"]), ("effort", effort)):
            if not re.fullmatch(r"[A-Za-z0-9._][A-Za-z0-9._-]*", value):
                sys.exit(
                    f"error: {label} '{value}' contains characters unsafe for $(...) splicing; "
                    f"use --export and quote it yourself"
                )
        print(f"-m {model['slug']} -c model_reasoning_effort={effort}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
