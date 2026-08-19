---
name: dsl-design
description: >-
  Design and implement fluent APIs, SDKs, and domain-specific languages using the
  principles from Martin Fowler's Domain-Specific Languages (Semantic Model,
  Expression Builder, Method Chaining, progressive interfaces, Notification,
  code-generation patterns). Use this skill whenever the user designs, implements,
  or reviews a library or SDK public API, a builder or fluent interface, a
  chained/method-chaining API, a configuration file format or schema, an
  options/kwargs surface, a rule engine, state machine, workflow or pipeline
  configuration, a parser for a custom text format, a code generator, or a
  generated client SDK — even if they never say "DSL" or "fluent". Also use it
  when asked whether an API should be "more fluent", how to structure builders,
  how to validate config input, or how users should extend generated code.
---

# DSL and Fluent API Design (Fowler)

This skill applies the design principles of Martin Fowler with Rebecca Parsons,
*Domain-Specific Languages* (2010) — the definitive treatment of what makes a
library's calling surface readable, composable, safe, and evolvable. Fowler's own
framing is why the book is really about SDK design: "most DSLs are merely a thin
facade over a library or framework," and "library design is language design."
The full distillation with citations lives in the repo doc
`docs/dsl-design-principles.md`; this skill carries the operational core.

**When not to apply it:** one-off scripts, internal helpers with two call sites,
or an API whose plain command-query form already serves its users. Fowler's rule:
"Not every library benefits from having a DSL wrapper over it." Adding a fluent
layer nobody needed is negative value — more to maintain, more to document, more
ways to say the same thing. Say so instead of applying the pattern ritually.

## First, decide the mode

- **Design mode** — the user wants an API/DSL/format proposal. Follow
  [Design workflow](#design-workflow); deliver the design (model sketch, surface
  grammar, call-shape choices with reasons), not code.
- **Implementation mode** — the user wants working code. Run the design workflow
  first (compressed if the design is obvious), then follow
  [Implementation workflow](#implementation-workflow).
- **Review mode** — the user has an existing API, config format, or generated-SDK
  setup to audit. Follow [Review checklist](#review-checklist); report violations
  with locations and the smallest refactor that restores each invariant.

Then load the reference that matches the surface being built:

- Fluent/builder/options APIs in a host language →
  [references/fluent-api-patterns.md](references/fluent-api-patterns.md)
- The underlying model, builders, error collection, symbol/registry design →
  [references/foundational-patterns.md](references/foundational-patterns.md)
- A text/config format that must be parsed, or choosing internal vs external →
  [references/external-dsl-and-codegen.md](references/external-dsl-and-codegen.md)
  and [references/foundations-and-strategy.md](references/foundations-and-strategy.md)
- Rule engines, state machines, dependency/pipeline models, code generators,
  generated client SDKs →
  [references/external-dsl-and-codegen.md](references/external-dsl-and-codegen.md)

## Vocabulary — use it precisely

| Term | Meaning |
|---|---|
| **Semantic Model** | The library/object model that holds all meaning and behavior. Every surface (fluent API, config file, CLI, generated client) merely *populates* it. Not an AST: the AST mirrors syntax; the model captures meaning. |
| **Command-query API** | The plain API: each method makes sense alone in an autocomplete list. A *vocabulary*. |
| **Fluent interface / internal DSL** | An API whose methods only make sense inside a larger expression. A vocabulary *plus a grammar* (Mike Roberts). |
| **Expression Builder** | The separate object(s) hosting the fluent surface, translating it into command-query calls on the model. The fence that licenses fluent style. |
| **External DSL** | A separate parsed text format (custom syntax, or a carrier syntax like YAML/JSON/XML). |
| **Notification** | An object accumulating all errors from a batch validation instead of failing on the first. |
| **Progressive interfaces** | Each chained call returns a narrower type exposing only what is legal next — the grammar enforced by the type system (today: the type-state pattern). |
| **Adaptive Model** | A model whose *population* acts as the program (rules, state machines, dependency networks). |
| **Generation Gap** | Generated code and handwritten customizations separated into different classes/files related by inheritance, so regeneration never destroys edits. |

## The invariants

1. **Ship the model, not the syntax.** Build a Semantic Model that is fully
   usable and testable through a plain programmatic interface; every other
   surface is a thin, replaceable front end that populates it. Attribute
   benefits honestly: reuse, runtime reconfiguration, multiple targets, and
   testability come from the model, not from any syntax over it. Operational
   tests: (a) a test suite touching only the plain API can exercise everything;
   (b) validation lives in the model, not in loaders or builders, so it applies
   identically for every front end.

2. **The seam comes first.** Before designing any convenience surface, separate
   the invariant engine from the per-use configuration code ("this separation is
   the vital step"). Then grow the surface in thin end-to-end slices against
   real usage scenarios written the way you wish callers could write them.

3. **Two layers, never mixed.** Fluent methods live in dedicated builder types;
   model/domain objects stay plain and conventional. Never mix fluent and
   command-query styles on one class. Inside the builder fence you may break
   normal conventions (mutators returning `this`, naming bent for the call-site
   reader, a surface deliberately *less* expressive than the model); the license
   is the fence. Review question: *if a user obtained this object outside the
   fluent chain, would its interface confuse them?* If yes, the fluent methods
   are on the wrong class.

4. **Choose call shapes from the grammar of what the caller supplies.**
   Mandatory, fixed-shape input → function/constructor arguments (the only shape
   that can *require*). Optional pick-and-choose settings → chained builder
   methods or keyword arguments. Homogeneous repetition → varargs/lists.
   Many optional heterogeneous attributes → options object/kwargs *with explicit
   key validation that names offending keys*. Real hierarchy → nested calls,
   blocks, or child builders — never indentation alone. Required order or
   presence in a chain → progressive interfaces. Each choice leaves an
   enforcement gap; name it and close it.

5. **Limited expressiveness is a feature.** A constrained surface makes it
   "harder to say wrong things and easier to see when you've made an error."
   Police scope relentlessly — the config format that grows loops and the
   pricing library that grows an HTTP client are the same failure. For rare
   needs, add one narrow escape hatch (a plugin point; an embedded snippet that
   is a single call into real code) instead of new core surface.

6. **Collect errors; structure them; layer them.** Batch validation returns a
   Notification with *all* problems, each carrying location/field/value as
   data, rendered to text only at the edge. Offer both a query (`is_valid`) and
   a raiser (`raise_for_errors`). Fail fast only on programmer errors against
   model invariants. Every parser, loader, and options surface fails loudly on
   unrecognized input — silent tolerance is a bug factory, and passing tests on
   valid input alone "indicates only that the parser didn't blow up."

7. **Anything users hand-edit is a published language.** Config schemas and file
   formats acquire language obligations the moment humans maintain them:
   a version marker from day one (nearly impossible to retrofit), migrations as
   many small steps, error messages with source positions, version control.

8. **Magic must pay its way in tooling survival.** Judge every metaprogramming
   trick by whether the abstraction survives the debugger, stack trace, type
   checker, and IDE. Prefer closures to macros/codegen for deferred evaluation;
   use dynamic method interception only for fully general mappings (special
   cases inside the hook mean define real methods) and always route unknown
   names to the error path. Prefer structural fixes to source rewriting. Scope
   extensions to types you don't own; never bolt DSL vocabulary onto shared
   domain types.

9. **Declarative surfaces owe an explanation mechanism.** If behavior moves out
   of imperative code into rules/states/graphs/config, ship a trace or
   "explain" facility and a way to dump the assembled configuration — you just
   traded away free debuggability, and config-driven magic without tracing
   becomes a system only its authors can maintain.

10. **Spend the type system where it exists.** Progressive interfaces make
    illegal call sequences fail at compile time and turn autocomplete into
    documentation. Replace stringly-typed identifiers with declared symbols
    (enums, literal unions, generated constants) when users have tooling that
    exploits them — and skip the ceremony when they don't.

## Design workflow

1. **Find the axis of variation.** What varies per use lives in the surface;
   what is invariant belongs in the library. If the variable part is trivial, a
   plain API is the answer — say so and stop.

2. **Design the model first, via the "magically already there" trick.** Write
   the *usage* code (the operational interface) as if a populated model already
   existed; then design the population interface that builds it. Keep the two
   interfaces distinct. Put every invariant and validation in the model.

3. **Sketch the surface as a grammar.** Write the ideal call sites (or config
   file) for 3–5 real scenarios first — the way you wish they could read. Then
   write the grammar those examples imply (BNF-ish is fine, informally) and read
   the call shapes off it using invariant 4. This is where you decide chaining
   vs nesting vs blocks vs options objects — consult
   [references/fluent-api-patterns.md](references/fluent-api-patterns.md) for
   the mapping table and the ten-step decision sequence.

4. **Decide internal vs external** (if a text format is on the table): internal
   inherits the whole IDE and stays cheap; external buys syntactic freedom,
   runtime reconfiguration, sandboxing for untrusted/non-programmer authors,
   and a hard wall against host-language leakage. Ten factors, two usually
   decisive: tooling and boundary strength. See
   [references/foundations-and-strategy.md](references/foundations-and-strategy.md).

5. **Design the error experience** with invariant 6, and the evolution story
   with invariant 7. For declarative/model-driven behavior, design the explain
   facility now (invariant 9), not later.

6. **Name what you are *not* building:** the scope boundary, the escape hatch,
   and which grammar rules are unenforced (documented convention) vs enforced
   (types, validation).

Deliver the design as: model sketch (types + operational interface), surface
grammar with example call sites, call-shape decisions with the grammar rule each
one satisfies, error/versioning/explain decisions, and rejected alternatives
with reasons.

## Implementation workflow

Build in thin end-to-end slices: simplest scenario through model + surface +
tests, then the next scenario. Model first (TDD against the plain API), surface
second, translation last. Concretely:

- Builders buffer; models validate. A `build()`/terminal step is where
  completeness checks run and the immutable product is constructed. Enforce
  builder lifecycle (reject reuse/mutation after build) with clear errors.
- When a chain needs `.end()`/`.build()` noise or accumulates "current thing"
  state, switch shape: nested calls or a block/closure form terminate
  structurally and scope context lexically. The context-carrying maturity
  ladder runs globals → instance fields → return values → lexically scoped
  blocks; move down it, never up.
- Child builders mirror the grammar's nesting, and each must forward the
  parent's chain so users don't hit dead ends mid-expression.
- Test in three places, because there are three seams: the model via the plain
  API (the bulk), the translation layer (each surface construct populates the
  model correctly), and invalid input (loud, located, complete error reports).
- Formatting is API design in fluent code: one clause per line makes stack
  traces and debugger steps point at the failing clause.

For parsers, code generators, rule engines, and state machines, follow
[references/external-dsl-and-codegen.md](references/external-dsl-and-codegen.md)
— it carries the parsing-strategy tripwires (>1 token lookahead → parser
generator; regular language → lexer may suffice; needing semantic predicates →
redesign the language), the output-strategy choice, and the generated-SDK
architecture: **thin generated layer over a fat handwritten runtime** (generate
declarations that populate the runtime's small stable API; never generate what
the runtime could own), **Generation Gap** for user customization (generated
files never hand-edited; always emit the concrete user-facing class, even
empty), and generated output optimized for reading and debugging, with
provenance comments pointing at the model.

## Review checklist

Audit in this order — cheapest checks catch the most rot:

1. **Mixed layers:** fluent methods (mutators returning `this`, phrase-named
   methods) on model/domain/response objects users hold at runtime → invariant 3.
2. **Model bypass:** logic or validation living only in a builder, loader, or
   parser, so different front ends behave differently → invariant 1. Check for
   a test path that exercises everything through the plain API.
3. **Hidden context:** static/global "current object" state; builders with a
   `currentX` field and order-dependent calls; a second context variable on one
   builder (the signal for child builders or blocks) → implementation ladder.
4. **Enforcement gaps:** required parameters supplied via omit-able chained
   setters; options maps that accept unknown keys silently; hierarchies
   expressed only by indentation; call order enforced only by documentation →
   invariant 4 (and 10: could types enforce this?).
5. **Error experience:** first-error-only validation; messages without
   location/field; formatting composed at every call site; lower layers
   printing or touching presentation → invariant 6.
6. **Silent tolerance:** parsers/loaders that skip unrecognized input; magic
   interception that swallows unknown names; tolerant-by-default recovery with
   no strict mode → invariant 6. Confirm tests include invalid input.
7. **Scope creep and unpoliced magic:** conditionals/loops growing in a config
   format; DSL vocabulary on shared types; metaprogramming that breaks stack
   traces; regex preprocessing accumulating cases → invariants 5 and 8.
8. **Published-language hygiene:** hand-edited formats with no version marker or
   migration story; DSL scripts outside version control → invariant 7.
9. **Codegen hygiene:** hand-edited generated files; marked-region mixing;
   generated code reaching into runtime internals; logic inlined in templates
   or grammar actions (more than a single call) → generated-SDK rules in
   [references/external-dsl-and-codegen.md](references/external-dsl-and-codegen.md).
10. **Missing explain facility** on any rule/state/graph-driven component →
    invariant 9.

For refactors, restore invariant 1 first (a fully capable plain API with tests)
— every later change is protected by it.

## Going deeper

- [references/fluent-api-patterns.md](references/fluent-api-patterns.md) — the
  fifteen internal patterns (Expression Builder through Literal Extension), the
  grammar→technique table, decision sequence, and collected judgement calls.
- [references/foundational-patterns.md](references/foundational-patterns.md) —
  Semantic Model, Symbol Table, Context Variable, Construction Builder, Macro,
  Notification: the infrastructure every DSL and SDK shares.
- [references/external-dsl-and-codegen.md](references/external-dsl-and-codegen.md)
  — parsing strategies and tripwires, output production, computational models
  (rules, state machines, dependency networks), and the six code-generation
  patterns including the generated-SDK architecture.
- [references/foundations-and-strategy.md](references/foundations-and-strategy.md)
  — definitions and boundaries, why/why-not, lifecycle, testing/errors/
  migration, internal-vs-external factors, workbenches, real-DSL lessons.
- `docs/dsl-design-principles.md` (repo root) — the full 5,600-line distillation
  of the book with complete citations, if a claim here needs its source.
