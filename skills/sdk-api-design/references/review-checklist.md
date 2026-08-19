# SDK API review checklist

Use this checklist for review mode and as the final pass in design or
implementation mode. Read `bloch-principles.md` first. Every check maps to its
normative source through a `Bxx` principle identifier.

Do not count violations mechanically. Report only issues with evidence and a
public consequence, then apply B28 when principles conflict.

## 1. Establish review context

- Identify the intended audience, the boundary's current users, and how hard it
  is to change [B01-B02].
- Recover the underlying outcomes from requested mechanisms and list the use
  cases that should judge the API [B03].
- Separate unpublished design freedom from established behaviors that require
  compatibility-preserving evolution [B01, B08].

If these facts are missing, call out the uncertainty before making strong
surface recommendations.

## 2. Try the use cases as client code

- Sketch or extract the whole public surface in compact form [B04].
- Write or inspect client code for each ordinary and complex use case [B05].
- Include setup, operation, result use, and relevant failure behavior [B05].
- Test one or more likely mistakes: swapped inputs, invalid states, forgotten
  special cases, or surprising side effects [B02, B20-B27].
- Check whether the examples are safe and clear enough to be copied widely
  [B05].

A surface that cannot express a core use case coherently has a design problem;
do not bury it beneath implementation fixes [B03-B05].

## 3. Audit purpose, concepts, and names

- Can the API's single purpose be explained in one sentence [B09]?
- Do types or operation groups combine unrelated purposes that should split, or
  expose internal steps that should merge [B09]?
- Does each exported element serve a demonstrated use case [B03, B10]?
- Are users learning avoidable new concepts where a suitable familiar platform
  abstraction already exists [B10, B15]?
- Does one word retain one meaning throughout the API [B09]?
- Are different meanings clearly named, and are real domain symmetries reflected
  consistently [B09]?
- Does representative client code read close to the user's intent [B02, B09]?

Treat naming difficulty as design evidence, not a cosmetic defect [B09].

## 4. Audit exposure and evolvability

- Can any exported type, member, state, or behavior become private [B12]?
- Do public types, errors, serialization forms, algorithms, storage details,
  transport details, or framework vocabulary freeze replaceable implementation
  choices [B11]?
- Are specified behaviors genuine client guarantees rather than observations of
  the current implementation [B11, B13]?
- Does the contract impose a fixed input size for implementation convenience
  rather than a real requirement [B16]?
- Could foreseeable capability be added without changing existing client
  meaning [B08]?
- Does the surface force an avoidable lasting performance cost, or is a proposed
  API distortion merely compensating for a temporary one [B14]?
- Does the SDK feel customary in the target platform rather than transliterated
  from another language [B15]?

## 5. Audit objects and extension points

- Is mutable state required by the represented concept [B17]?
- Is the state space small, explicit, and documented, including legal
  transitions and reuse rules [B13, B17]?
- Could hidden mutability surprise clients or make sharing unsafe [B17, B20]?
- Is every exposed subtype honestly substitutable for the supertype [B18]?
- If subclassing is allowed, are self-use patterns of overridable operations
  designed and documented; otherwise, is subclassing prohibited [B18]?
- For an SPI or plugin API, have two genuinely different providers been written
  against it, and preferably a third before claiming open-ended flexibility
  [B06]?

## 6. Audit operations for natural and safe use

- Does the SDK make every client repeat necessary plumbing it could perform once
  and correctly [B19]?
- Does each name describe the operation's primary effect and important side
  effects [B20]?
- Are invalid values prevented or rejected at the earliest point the platform
  reasonably permits [B21]?
- Is every datum embedded in display text also available structurally [B22]?
- Can overload resolution, inferred types, casts, or same-name variants silently
  select meaningfully different behavior [B23]?
- Do input and result types state the real domain, accepted values, and required
  precision [B24]?
- Are related parameter orders consistent [B25]?
- Are parameter lists short and distinguishable enough to avoid undetectable
  swaps, with a customary native mechanism used where they are not [B15, B25]?
- Must callers remember a rare sentinel branch that a normal result shape could
  eliminate [B26]?
- Are exceptions reserved for exceptional outcomes rather than ordinary flow
  [B27]?
- If the platform can force exception handling, can clients realistically
  recover from every forced failure [B27]?

## 7. Audit documentation and examples

For every exported element, verify that the contract covers what applies [B13]:

- what a type instance represents;
- preconditions and postconditions;
- side effects;
- failure behavior;
- parameter units and formats;
- ownership, retention, and mutation rights;
- legal mutable states and transitions.

Then verify:

- client examples originate in real use-case trials and remain current [B05];
- examples use the safest intended patterns rather than shortcuts clients should
  not copy [B05];
- documentation promises observable guarantees without treating implementation
  source as specification [B11, B13].

## 8. Apply judgment before reporting

For each candidate finding [B28]:

1. Name the affected use case and audience.
2. Identify the concrete public consequence.
3. Map it to one or more `Bxx` principles.
4. Check the competing principle: omission versus convenience, symmetry versus
   weight, performance versus astonishment, or correction versus compatibility.
5. Recommend the smallest coherent correction.
6. Record a real reason to retain the current design, if one exists.

Order findings by client impact and irreversibility [B01, B08]:

1. A core use case cannot be expressed or is easy to misuse.
2. A public commitment blocks evolution or leaks implementation.
3. A surprising behavior, delayed failure, or exceptional client path invites
   bugs.
4. Conceptual weight, naming, or repeated ceremony makes ordinary use harder.
5. Documentation leaves an otherwise sound contract ambiguous.

## Finding format

```markdown
### [Severity] Finding title
- Evidence: [signature, behavior, client snippet, or file location]
- Principle: [Bxx — principle name]
- Client harm: [specific consequence]
- Smallest correction: [minimum coherent change]
- Tradeoff: [credible reason to keep the current design, or "None found"]
```

End with:

- **Use-case coverage:** which cases the API serves or misses [B03-B05].
- **Omissions worth preserving:** tempting additions correctly left out [B10].
- **Unresolved judgments:** choices needing audience evidence rather than a
  mechanical rule [B28].
