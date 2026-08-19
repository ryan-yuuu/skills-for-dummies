# `sdk-api-design` skill design

Date: 2026-08-18
Status: Approved for planning

## Context

Create a new, language-agnostic skill that turns Joshua Bloch's talk *How to
Design a Good API and Why It Matters* into a practical workflow for designing,
implementing, and reviewing SDK APIs.

The skill must draw its normative guidance solely from:

- `/Users/ryan/Projects/how-to-design-a-good-api-and-why-it-matters/abstract.md`
- `/Users/ryan/Projects/how-to-design-a-good-api-and-why-it-matters/transcript.txt`

The talk's Java examples are evidence for broader design principles, not
timeless prescriptions. The skill will preserve the joints and judgment calls
in Bloch's argument while translating examples into the customary mechanisms
of the user's target language and platform.

An untracked `skills/python-sdk-design/` package is being developed separately.
This work must neither edit nor depend on it.

## Goals

The skill should enable an agent to:

1. Recover underlying requirements from stakeholder-proposed solutions.
2. Design a small, coherent SDK API around concrete use cases and its intended
   audience.
3. Validate a proposed API by writing realistic client code before implementing
   it.
4. Implement the approved surface without leaking implementation details.
5. Review an existing SDK API for usability, misuse resistance, conceptual
   weight, platform fit, evolvability, and contract quality.
6. Make and explain tradeoffs using Bloch's principles rather than applying a
   checklist mechanically.

## Non-goals

- Prescribe a particular programming language, transport, protocol, package
  layout, HTTP stack, authentication model, telemetry system, or release
  process.
- Import Azure SDK, language-specific style-guide, or other external API-design
  doctrine.
- Treat Bloch's Java-era mechanics—builders, overloads, checked exceptions, or
  compile-time checking—as universal syntax rules.
- Maximize completeness, abstraction, configurability, or symmetry without a
  demonstrated use case.

## Package architecture

Use a layered skill package:

```text
skills/sdk-api-design/
├── SKILL.md
├── evals/
│   └── evals.json
└── references/
    ├── bloch-principles.md
    └── review-checklist.md
```

### `SKILL.md`

Keep the active instructions compact. It will contain:

- A pushy description that triggers for designing, implementing, reviewing, or
  refactoring an SDK, client library, public library API, or service wrapper.
- A scope guard distinguishing public API design from unrelated internal
  refactoring.
- Design, implementation, and review mode selection.
- The common workflow and decision hierarchy.
- Required deliverable shapes for each mode.
- Routing instructions for the two references.
- The rule for translating dated coding examples into platform-native choices.
- Stable principle identifiers that connect each normative workflow rule to the
  source map in `references/bloch-principles.md`.

### `references/bloch-principles.md`

Preserve the talk's nuance without reproducing the transcript. Organize the
principles around the design decisions they settle:

- Why APIs deserve disproportionate care and why public commitments are hard to
  reverse.
- Requirements, audience, use cases, short early drafts, client-code trials,
  stakeholder feedback, and cohesive ownership.
- Cohesion, naming, conceptual weight, omission, implementation hiding,
  accessibility, documentation, performance, and platform customs.
- Mutability, inheritance, client boilerplate, least astonishment, early
  failure, structured data, overloading, types, parameter design, return values,
  and exceptions.
- Avoidance of fixed input-size limits and validation of an SPI or extension
  point against multiple genuinely different providers before publishing it.
- Expected failures of imagination, compatibility-preserving evolution, and the
  role of judgment when principles conflict.

For each cluster, state the underlying reason and the practical test an agent
can apply. Give each durable principle a stable identifier and cite its source
as an abstract maxim and/or transcript line range. Distinguish principles from
historical examples. These citations form the normative source map; they must
point only to the two approved local source documents.

### `references/review-checklist.md`

Turn the same teachings into a concise audit sequence. Each check should ask for
evidence and connect the finding to client harm. The checklist will prioritize
hard-to-reverse public-surface defects over internal preferences. Each
normative check will cite the stable principle identifier that authorizes it.

### `evals/evals.json`

Provide three realistic prompts with expected outcomes and objective assertions
where possible:

1. Greenfield SDK API design.
2. Review and redesign of a misuse-prone existing SDK.
3. Implementation guidance in a non-Java ecosystem.

## Operating modes

### Design mode

Produce:

1. Audience and underlying-problem statement.
2. Concrete use cases, including the dominant simple cases and legitimate
   advanced cases.
3. A compact public-surface sketch with signatures and one-line contracts.
4. Client-side code written against the unimplemented surface.
5. An explicit omission ledger: tempting features deliberately left out and
   the evidence that would justify adding them.
6. Tradeoffs, open questions, and evolvability risks.

Do not implement the surface until client-code trials and review show that the
shape is sound.

### Implementation mode

Apply the design workflow first, compressed only when the repository already
contains an approved public surface and representative use cases. Then:

1. Preserve the public boundary while hiding implementation choices.
2. Use the target platform's customary names, types, conventions, and error
   mechanisms.
3. Make invalid use difficult and detect errors as early as the platform
   reasonably permits.
4. Put work the SDK can reliably perform inside the SDK rather than repeating it
   in every client.
5. Maintain exemplary client programs as samples and tests.
6. Document every exported element and every relevant contract detail.

### Review mode

Report findings with:

- Concrete evidence from the proposed or existing API.
- The implicated Bloch principle.
- The likely effect on users, maintenance, or evolution.
- The smallest viable correction.
- Any real tradeoff or reason to retain the current design.

Order findings by irreversibility and client impact. Do not turn personal style
preferences into API defects.

## Common workflow

1. **Identify the audience.** An API is a language for a particular group; its
   vocabulary and assumptions must fit that group.
2. **Interrogate requirements.** Separate the problem to solve from the
   stakeholder's proposed mechanism.
3. **Write use cases.** Use them as the yardstick for every surface decision.
4. **Sketch one page.** Favor signatures and short contracts while the design is
   cheap to restructure.
5. **Write client code first.** Exercise ordinary use, advanced use, and likely
   misuse without implementing the API.
6. **Reduce conceptual weight.** Revisit cohesion and names; split, merge, or
   reuse familiar platform abstractions where they reduce what users must learn.
7. **Apply omission pressure.** Remove any capability, type, method, or parameter
   without a clear use-case burden of proof.
8. **Remove client ceremony.** Where a task is necessary and the SDK can perform
   it correctly, absorb it behind the API.
9. **Test the contract.** Check least astonishment, type suitability, parameter
   consistency, early failure, structured access, normal return shapes, and
   abstraction-level errors.
10. **Avoid premature ceilings.** Do not publish fixed input-size limits unless
    the actual contract requires them; artificial ceilings curtail use and age
    badly.
11. **Exercise extension points.** Before publishing an SPI or plugin boundary,
    write multiple genuinely different providers against it so one
    implementation's assumptions do not harden into the contract.
12. **Seek feedback.** Invite many perspectives to uncover failures of
    imagination while keeping one coherent design voice.
13. **Implement behind the boundary.** Avoid exposing storage, wire, framework,
    or other replaceable choices.
14. **Preserve the trials.** Turn client programs into unusually careful samples
    and tests, and keep them current as the API evolves.

## Decision hierarchy

When principles pull in different directions, reason in this order:

1. Satisfy demonstrated use cases for the intended audience.
2. Make simple things easy, complex things possible, and wrong things difficult.
3. Minimize conceptual weight, not merely method or type count.
4. Leave uncertain public commitments out because addition is easier than
   removal.
5. Still absorb necessary, repeatable client boilerplate that the SDK can do
   correctly once.
6. Prefer the target platform's customary expression over transliteration from
   another SDK.
7. Consider performance consequences without warping the lasting contract to
   address a temporary implementation cost.
8. Prefer compatibility-preserving extension when an established public API has
   flaws.
9. Treat all rules as heuristics: violate them rarely, consciously, and with a
   reason tied to the use cases.

## Error and contract design

Derive error guidance from the talk:

- Prevent or identify misuse at the earliest stage the platform supports.
- Use appropriate domain and platform types instead of undifferentiated strings
  or overly broad inputs.
- Keep failures at the API's abstraction level; do not leak a replaceable
  implementation's error vocabulary.
- Reserve exceptions for exceptional conditions rather than normal control
  flow.
- Where a platform distinguishes forced from optional exception handling, force
  handling only when clients can realistically recover.
- Avoid return values that require clients to remember rare special cases when a
  normal empty or value-shaped result is available.
- Provide structured access to every datum also rendered as text so display
  strings do not become accidental protocols.
- Document preconditions, postconditions, side effects, units, formats,
  ownership, mutable state transitions, and failure behavior for every exported
  element to which they apply.

## Translation rule

For every language-specific example in the talk:

1. Extract the user-facing failure or desired property.
2. State the durable principle that explains it.
3. Inspect what is customary and enforceable in the target ecosystem.
4. Choose the native mechanism that best realizes the principle.
5. Explain any tradeoff; do not present the historical Java mechanism as the
   principle itself.

This rule permits, for example, a helper parameter object where it reduces a
long ambiguous argument list, without mandating a Java-style builder in a
language where named arguments are customary.

## Evaluation strategy

The three evals should test both content and process. Assertions should verify
that the agent:

- Identifies audience, underlying requirements, and use cases before settling
  the surface.
- Produces a compact surface and client-side trials before implementation.
- Uses omission and conceptual weight as explicit decision tools.
- Adapts examples to target-platform idioms instead of copying Java mechanics.
- Finds client boilerplate, surprising behavior, delayed failure, weak types,
  special-case returns, implementation leaks, and undocumented contracts when
  those defects exist in the prompt.
- Makes implementation advice traceable to the approved public contract.
- Does not import unrelated modern SDK doctrine.

Run each prompt with and without the skill, grade objective assertions, aggregate
the benchmark, and generate the skill-creator review artifact for qualitative
human feedback. Store these runs in a sibling `sdk-api-design-workspace/`, not
inside the distributable skill package. Incorporate the user's feedback into a
new skill iteration and repeat the relevant evals until the user approves the
skill, returns no corrective feedback, or further iteration no longer produces
meaningful improvement. Human approval is the completion gate.

Before presenting any iteration for review, perform a source-only audit:

1. Extract the normative statements from `SKILL.md` and
   `references/review-checklist.md`, plus normative expected outcomes and
   assertions from `evals/evals.json`.
2. Resolve each statement's stable principle identifier in
   `references/bloch-principles.md`.
3. Confirm the mapped source is one of the two approved documents and supports
   the statement without importing additional doctrine.
4. Treat an unmapped or unsupported instruction as a validation failure.

Immediately before the first implementation write, record a sorted file
inventory and SHA-256 content hashes for `skills/python-sdk-design/` in the
sibling evaluation workspace. Repeat the inventory and hashes immediately after
the last implementation write. If they differ, do not claim isolation from the
hashes alone: the package is under legitimate parallel development. Instead,
identify the changed paths, audit this task's patch targets and commands, and
surface any unresolved overlap to the user. A matching comparison proves the
parallel package was untouched during this task's write window.

## Acceptance criteria

- The skill is named `sdk-api-design` and does not modify
  `skills/python-sdk-design/`.
- Every normative rule is traceable to Bloch's talk or abstract.
- The skill supports design, implementation, and review without becoming
  language-specific.
- Dated examples are translated through their rationale and platform custom.
- The active `SKILL.md` stays lean and routes deeper reading deliberately.
- The checklist prioritizes public client consequences rather than internal
  code style.
- Every normative instruction and checklist item maps through a stable
  principle identifier to a supporting location in one of the two approved
  source documents.
- Fixed-size ceilings and multi-provider SPI trials are included where relevant.
- Three eval cases and their review artifact are created through the
  skill-creator workflow, and user feedback is incorporated until the completion
  gate is met.
