#!/usr/bin/env python3
"""Pick the strongest available Codex model and emit ready-to-use flags.

Model names change every few releases, so hardcoding one guarantees the skill
goes stale and silently runs on a weaker model than the user is paying for.
`codex debug models` reports the catalog this binary actually sees, including a
`priority` ranking and each model's supported reasoning levels. This resolves
that at call time instead.

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
    python3 codex_pick_model.py --list          # show the whole catalog

Effort defaults to `xhigh`. If the chosen model doesn't support the requested
level, this falls back to the strongest level it does support and says so on
stderr rather than emitting a flag the CLI would reject.
"""

import argparse
import json
import shutil
import subprocess
import sys

# Strongest last. Used to rank a model's supported levels and to resolve a
# requested effort the model can't honor down to its best available.
EFFORT_ORDER = ["low", "medium", "high", "xhigh", "max", "ultra"]

DEFAULT_EFFORT = "xhigh"


def load_catalog(bundled_only=False):
    """Return the model catalog, falling back to the bundled copy if the
    network refresh fails (offline, restricted CI, expired auth)."""
    if not shutil.which("codex"):
        sys.exit("error: `codex` not found on PATH")

    attempts = [True] if bundled_only else [False, True]
    last_err = ""
    for bundled in attempts:
        cmd = ["codex", "debug", "models"] + (["--bundled"] if bundled else [])
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            last_err = "timed out"
            continue
        if proc.returncode != 0:
            last_err = (proc.stderr or "").strip()
            continue
        try:
            models = json.loads(proc.stdout).get("models") or []
        except json.JSONDecodeError as exc:
            last_err = f"unparseable catalog: {exc}"
            continue
        if models:
            if bundled and not bundled_only:
                print("note: using bundled catalog (refresh failed)", file=sys.stderr)
            return models

    sys.exit(f"error: could not load model catalog: {last_err or 'empty catalog'}")


def selectable(models):
    """Models a user can actually pick.

    `visibility: hide` marks internal entries (e.g. codex-auto-review) that
    aren't meant to be selected directly.
    """
    return [m for m in models if m.get("visibility") == "list" and m.get("slug")]


def best_model(models):
    """Lowest `priority` wins — the catalog ranks strongest first (priority 1
    is described as the latest frontier agentic coding model)."""
    ranked = sorted(selectable(models), key=lambda m: (m.get("priority", 10**6), m["slug"]))
    if not ranked:
        sys.exit("error: no selectable models in catalog")
    return ranked[0]


def supported_efforts(model):
    levels = [
        lvl.get("effort")
        for lvl in model.get("supported_reasoning_levels") or []
        if lvl.get("effort")
    ]
    # Preserve the canonical weak->strong ordering; ignore unknown names.
    return [e for e in EFFORT_ORDER if e in levels]


def resolve_effort(model, requested):
    """Return an effort the model actually supports.

    Emitting an unsupported level would make the whole `codex exec` call fail,
    which is a worse outcome than quietly running one tier lower.
    """
    available = supported_efforts(model)
    if not available:
        # Catalog didn't report levels; trust the caller rather than block.
        return requested
    if requested in available:
        return requested
    fallback = available[-1]
    print(
        f"note: {model['slug']} does not support effort '{requested}'; "
        f"using '{fallback}' (supports: {', '.join(available)})",
        file=sys.stderr,
    )
    return fallback


def render_list(models):
    rows = sorted(selectable(models), key=lambda m: (m.get("priority", 10**6), m["slug"]))
    width = max((len(m["slug"]) for m in rows), default=10)
    out = [f"{'PRIO':<5} {'MODEL':<{width}}  {'DEFAULT':<8} EFFORTS"]
    for m in rows:
        out.append(
            f"{m.get('priority', '?'):<5} {m['slug']:<{width}}  "
            f"{m.get('default_reasoning_level', '?'):<8} {','.join(supported_efforts(m))}"
        )
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--effort", default=DEFAULT_EFFORT, help=f"reasoning effort (default: {DEFAULT_EFFORT})")
    ap.add_argument("--model", help="use this slug instead of auto-selecting the strongest")
    ap.add_argument("--slug-only", action="store_true", help="print only the model slug")
    ap.add_argument("--effort-only", action="store_true", help="print only the resolved effort")
    ap.add_argument(
        "--export",
        action="store_true",
        help="emit shell assignments for CODEX_MODEL/CODEX_EFFORT (use with eval)",
    )
    ap.add_argument("--list", dest="do_list", action="store_true", help="print the catalog and exit")
    ap.add_argument("--bundled", action="store_true", help="skip the network refresh")
    args = ap.parse_args()

    models = load_catalog(bundled_only=args.bundled)

    if args.do_list:
        print(render_list(models))
        return 0

    if args.model:
        match = next((m for m in models if m.get("slug") == args.model), None)
        if match is None:
            available = ", ".join(m["slug"] for m in selectable(models))
            sys.exit(f"error: model '{args.model}' not in catalog. Available: {available}")
        model = match
    else:
        model = best_model(models)

    effort = resolve_effort(model, args.effort)

    if args.slug_only:
        print(model["slug"])
    elif args.effort_only:
        print(effort)
    elif args.export:
        # Single-quoted so the values survive eval unchanged. Slugs and effort
        # names come from a fixed vocabulary, but quoting costs nothing.
        print(f"CODEX_MODEL='{model['slug']}'")
        print(f"CODEX_EFFORT='{effort}'")
    else:
        print(f"-m {model['slug']} -c model_reasoning_effort={effort}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
