---
name: sdk-api-design
description: >-
  Design, implement, review, or refactor language-agnostic SDK and client-library
  public APIs using the durable principles from Joshua Bloch's talk "How to
  Design a Good API and Why It Matters." Use this skill whenever a user asks to
  create or critique an SDK surface, API client, service wrapper, reusable
  library interface, public package contract, plugin API, or SPI—even when they
  ask only to "make this client easier to use," "clean up these methods," or
  implement a service integration. Apply it across programming languages and
  transports. Do not use it for a purely internal refactor that cannot affect a
  reused boundary.
---

# SDK API Design

Treat an SDK as a small language its users must learn. Shape that language from
their use cases before implementation makes the public surface expensive to
change.

This skill is derived solely from Joshua Bloch's talk *How to Design a Good API
and Why It Matters*. `references/bloch-principles.md` is the source map: every
normative API-design instruction below cites a `Bxx` identifier defined there.
Do not import rules from other SDK guidelines. Use target-ecosystem conventions
only to translate Bloch's principles into a native form [B15, B28].

## Start by choosing the mode

- **Design mode:** propose a new public SDK surface. Follow the full workflow
  and deliver the design brief.
- **Implementation mode:** create or change working SDK code. Follow the design
  workflow before implementation; compress it only when concrete use cases,
  client trials, and an approved surface already exist [B03-B05].
- **Review mode:** audit an existing or proposed surface. Read
  `references/review-checklist.md`, report evidence-backed findings, and do not
  edit unless the user requested changes.

Always read `references/bloch-principles.md` before making public-surface
decisions. It contains the reasoning needed when rules pull against one another.

## Workflow: use before implementation

### 1. Identify the commitment and audience [B01-B02]

State:

- who will call, implement, or maintain the API;
- what vocabulary and platform knowledge they already have;
- how public and long-lived the boundary is;
- what existing client code or compatibility constraints already depend on it.

Spend more scrutiny on surfaces with more users, implementations, or expected
longevity. Treat an established public behavior as costly to remove [B01, B08].

### 2. Recover requirements as use cases [B03]

Separate each requested outcome from the mechanism a stakeholder proposed.
Write a small set of concrete client tasks that will judge the design. Include:

- the ordinary simple path;
- legitimate complex paths;
- likely mistakes the surface should make difficult.

Reject capability that has no demonstrated use case. Generalize only when the
general form solves the underlying problem more simply or coherently [B03,
B10].

### 3. Sketch the whole public surface [B04]

Keep the first draft to roughly one page: exported types and operations,
signatures, and one-line contracts. Do not bury unresolved design choices under
implementation detail. Restructure freely while the sketch is cheap to change.

### 4. Write client code against the unimplemented surface [B05]

For every use case, write realistic client code as if the SDK already existed.
Show setup, the main operation, result use, and relevant failure behavior. Also
write at least one plausible misuse when misuse resistance matters.

Read the client code as a language:

- Can an intended user guess it and later read it without constant lookup?
  [B02, B09]
- Does it expose plumbing rather than client intent? [B19]
- Can names, types, parameter order, or surprising side effects invite a likely
  mistake? [B20-B25]
- Does ordinary behavior require rare sentinels or exception-driven control
  flow? [B26-B27]

Do not implement a new public surface until these trials show it supports the
use cases coherently [B04-B05]. Preserve the trials as samples and tests, and
hold them to an unusually high standard because users will copy them [B05].

### 5. Reduce the surface's conceptual weight [B09-B12]

For every exported capability, type, method, and parameter, ask which use case
requires it. Remove uncertain commitments; addition is easier than removal
[B01, B10]. Count concepts users must learn, not declarations. Reuse an
appropriate, familiar platform abstraction when that adds power without a new
concept [B10, B15].

Let naming push back on the design. If clear, consistent names do not emerge,
split unrelated purposes, merge internal steps, or find the coherent containing
abstraction [B09]. Expose only elements clients actually need [B12].

Keep replaceable choices—storage, transport, internal algorithm, serialization,
or framework vocabulary—out of the public contract unless interoperability or
a use case requires the commitment [B11]. Avoid implementation-convenience size
limits [B16].

### 6. Make correct use natural [B17-B27]

- Minimize mutability and keep any necessary state machine small and explicit
  [B17].
- Use inheritance only for honest substitutability; either specify the
  interaction of overridable operations or prohibit subclassing [B18].
- Move necessary repeatable plumbing into the SDK when the SDK can do it
  correctly without hiding a meaningful client choice [B19].
- Make names describe primary effects and important side effects [B20].
- Prevent invalid states when the platform can express the constraint; otherwise
  reject invalid input at the earliest operation that can recognize it [B21].
- Expose structured access to every datum also rendered in a display string
  [B22].
- Avoid same-name variants whose resolution can silently select meaningfully
  different behavior [B23].
- Choose types that express the actual domain and precision, neither so broad
  that common inputs fail later nor tied to one implementation [B24].
- Keep parameter order consistent and parameter lists short enough to use
  correctly, especially around same-shaped values [B25].
- Prefer ordinary value-shaped results to rare sentinels that every caller must
  remember [B26].
- Reserve exceptions for exceptional conditions; force explicit recovery only
  where the platform supports that distinction and callers can realistically
  recover [B27].

### 7. Seek feedback without designing by accretion [B07-B08]

Show the short surface and client trials to relevant users and implementers.
Use disagreement to uncover missed use cases and hidden assumptions. Balance
important constituencies, but keep one coherent vocabulary and design voice.
Expect imagination to fail and preserve room for compatible additions.

For an SPI or plugin boundary, write multiple genuinely different providers
before publishing it: two expose single-provider assumptions; a third gives
stronger confidence that the abstraction can stretch [B06].

### 8. Implement behind the validated boundary [B11, B14-B16]

Use the target language's customary mechanisms rather than copying another
language's SDK shape [B15]. Keep implementation types and errors behind the
boundary [B11]. Consider whether the contract prevents an efficient
implementation, but do not distort a long-lived surface to work around a
temporary performance problem [B14]. Do not introduce a fixed ceiling merely
because the first implementation is simpler with one [B16].

If implementation exposes a design flaw, return to the sketch and client
trials. Do not patch over a bad surface with more internal machinery [B04-B05,
B09].

### 9. Specify, document, and preserve the contract [B05, B13]

Document every exported element. Cover what an instance represents; operation
preconditions, postconditions, side effects, and failures; parameter units,
formats, and ownership; and legal transitions of mutable state [B13]. Specify
observable guarantees without freezing incidental implementation behavior
[B11, B13].

Keep the exemplary use-case programs current as samples and tests whenever the
surface changes [B05]. Run the review checklist before declaring the public API
ready.

## Translate mechanics; preserve judgments

Bloch's examples use Java-era mechanisms. For each target language [B15, B28]:

1. Identify the user-facing failure or property in the mapped principle.
2. Inspect the customary mechanisms already used by the target platform and
   repository.
3. Choose the native mechanism that best realizes the principle.
4. Explain the tradeoff in terms of use cases and client harm.

For example, B25 supports reducing a long, ambiguous parameter list. Depending
on the language, the native answer might be named arguments, a helper value,
several cohesive operations, or a builder. The builder is an illustration, not
the rule. Apply the same translation to overloads, checked exceptions, static
typing, inheritance controls, and any other language-bound mechanism [B15,
B21, B23, B27-B28].

## Resolve tensions explicitly [B28]

Use this order when the heuristics conflict:

1. Serve the intended audience's demonstrated use cases [B02-B03].
2. Make correct ordinary use natural and misuse difficult [B02].
3. Minimize conceptual weight [B09-B10].
4. Omit unsupported commitments [B10].
5. Still absorb necessary repeated client work [B19].
6. Prefer target-platform customs over cross-language sameness [B15].
7. Preserve established client meaning while extending around mistakes [B08].
8. Consider lasting performance consequences without warping the contract
   [B14].

Treat this as informed judgment, not scoring. If violating a heuristic, name
the competing principle, the use-case evidence, and what would cause the choice
to be revisited [B28].

## Deliverables

### Design brief

```markdown
## Audience and underlying problem
## Use cases
## Public-surface sketch
## Client-code trials
## Misuse and failure trials
## Omissions
## Tradeoffs and evolvability
## Feedback still needed
```

Keep the surface sketch compact. Put explanations after the client trials so
the surface must first stand on its own [B02, B04-B05].

### Implementation handoff

Summarize:

- the use cases and validated public surface [B03-B05];
- the implementation boundary and hidden choices [B11];
- samples, tests, and exported contract documentation added [B05, B13];
- deliberate heuristic violations and their evidence [B28].

### Review report

Lead with findings, ordered by irreversible client impact [B01, B08]. For each:

```markdown
### [Severity] Finding title
- Evidence: [specific signature, call sequence, behavior, or file location]
- Principle: [Bxx and name]
- Client harm: [misuse, conceptual load, coupling, delayed failure, or blocked evolution]
- Smallest correction: [minimum coherent change]
- Tradeoff: [reason the current design might remain, if real]
```

Do not label an internal preference an API defect. Tie every finding to a
public consequence and a mapped principle [B28].

## Source-only audit

Before finalizing work claimed to follow this skill:

1. List the normative API-design recommendations in the output.
2. Map each to a `Bxx` principle in `references/bloch-principles.md`.
3. Remove, relabel, or justify any recommendation that lacks a mapping. A user
   requirement or repository constraint may still apply, but do not attribute
   it to Bloch.
4. Confirm platform conventions were used only as mechanisms for B15, not as an
   additional design doctrine.
