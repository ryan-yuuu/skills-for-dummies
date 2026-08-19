# Bloch's API design principles

This reference distills Joshua Bloch's *How to Design a Good API and Why It
Matters* into durable design judgments for SDKs. It introduces no normative
source beyond the supplied talk transcript and abstract.

Source annotations use the local source documents reviewed when this skill was
created:

- `abstract.md:Lx-Ly` refers to the supplied extended abstract.
- `transcript.txt:Lx-Ly` refers to the supplied video transcript.

The identifiers `B01`–`B28` are the source map for `SKILL.md`, the review
checklist, and the eval expectations. A language-specific example from the talk
illustrates its mapped principle; it is not automatically a rule for another
language.

## Contents

- [Why the boundary deserves care](#why-the-boundary-deserves-care) — B01-B02
- [Design process](#design-process) — B03-B08
- [Shape and conceptual model](#shape-and-conceptual-model) — B09-B16
- [Types, objects, and extension](#types-objects-and-extension) — B17-B18
- [Operations and client behavior](#operations-and-client-behavior) — B19-B27
- [Applying the principles](#applying-the-principles) — B28 and recurring
  tensions

## Why the boundary deserves care

### B01 — Treat every reused boundary as a lasting commitment

**Sources:** `abstract.md:L14-L18`; `transcript.txt:L7-L21`

Every programmer designs APIs because module boundaries become APIs when they
are reused. Successful APIs accumulate client code and learned knowledge; poor
ones accumulate support cost and constrain future work. Spend design effort in
proportion to the surface's reach and expected lifetime, and assume a published
commitment will be much harder to remove than to add.

**Practical test:** Who outside this implementation may compile, deploy, learn,
or build operations around this surface? What would break if it changed?

### B02 — Fit the audience and optimize for readable, misuse-resistant use

**Sources:** `abstract.md:L20-L22`; `transcript.txt:L23-L29`

A good API is easy to learn and use, hard to misuse, readable in client code,
powerful enough for its requirements, and able to evolve. It should make simple
tasks easy, complex legitimate tasks possible, and wrong operations difficult.
These qualities are audience-relative: use the concepts and vocabulary the
intended programmers already understand.

**Practical test:** Can an intended user guess the ordinary call sequence and
read it later without repeatedly consulting documentation? What likely mistake
does the surface prevent?

## Design process

### B03 — Recover problems from proposed solutions and express them as use cases

**Sources:** `abstract.md:L24-L26`; `transcript.txt:L33-L41`

Gather requirements skeptically. Stakeholders often request a mechanism when
their real requirement is the outcome that mechanism happens to suggest. Ask
what problem must be solved, then write concrete programs or tasks the API must
support. Use those cases—not feature count—as the yardstick for every decision.
A more general solution is justified when it is also simpler or better fits the
real problem, not merely because a framework sounds powerful.

**Practical test:** For every proposed element, which use case requires it? If a
request names a mechanism, what observable outcome is underneath it?

### B04 — Keep the first complete surface short and cheap to restructure

**Sources:** `abstract.md:L28-L28`; `transcript.txt:L43-L53`

Begin with roughly one page of signatures and one-line descriptions. Early
agility matters more than specification completeness: a compact sketch can be
shown widely and radically revised before authors become invested in detail.
Flesh it out only as evidence builds that the overall shape is right.

**Practical test:** Can reviewers see the entire public vocabulary and call
shape at once? Can a structural correction still be made in minutes?

### B05 — Write client code before implementation and preserve it

**Sources:** `abstract.md:L30-L34`; `transcript.txt:L53-L85`

Pretend the API already exists and code every important use case against it
before implementing or fully specifying it. Continue those trials as the API
evolves; otherwise late use can expose a fundamentally broken shape after it is
expensive to repair. Preserve the trials as examples, tutorials, and tests.
Treat examples with exceptional care because clients copy them at scale.

**Practical test:** Is there executable-looking client code for each use case,
including setup, success, and relevant failure behavior? Would copying it teach
the intended pattern safely?

### B06 — Exercise an extension point with multiple providers

**Sources:** `transcript.txt:L85-L91`

An SPI or plugin API designed around one implementation will usually expose
that implementation's accidental assumptions. Write at least two genuinely
different providers before trusting the boundary; a third supplies much
stronger evidence that it can support an open-ended family.

**Practical test:** What changes when a second and third provider implement the
same contract? Which requirement exists only because of the first provider?

### B07 — Invite broad feedback but preserve one coherent design voice

**Sources:** `abstract.md:L36-L40`; `transcript.txt:L93-L99`

Most APIs are overconstrained, so no design will satisfy every stakeholder
fully. Seek many perspectives to expose failures of imagination, balance the
important use cases, and accept reasonable compromise. Do not combine every
suggestion mechanically; a strong design lead or single-minded group must keep
the resulting language cohesive.

**Practical test:** Whose legitimate use case is currently least well served?
Has feedback changed the design, or merely accumulated features?

### B08 — Expect mistakes and leave room for compatible extension

**Sources:** `abstract.md:L38-L40`; `transcript.txt:L97-L103`

Real use will reveal needs the designers could not imagine, usually after
clients depend on the original contract. Prefer a small foundation that can be
extended around flaws. Once clients rely on a public surface, favor additions
that preserve old programs over destructive cleanup.

**Practical test:** If one assumption proves wrong, can a new capability or
refined abstraction be added without changing existing client meaning?

## Shape and conceptual model

### B09 — Make the API do one explainable thing; let naming test the design

**Sources:** `abstract.md:L44-L46`; `transcript.txt:L103-L115`; `transcript.txt:L143-L153`

An API should have a coherent purpose that is easy to explain. Hard-to-find
names often reveal a muddled boundary: split an API that contains unrelated
purposes, merge pieces that expose internal steps, or place the capability in a
better general setting. Names form a small language. Prefer intelligible words;
use one word for one concept; distinguish different concepts clearly; seek
symmetry where the operations truly are symmetric. The reward is client code
that reads like prose.

**Practical test:** Describe the API in one sentence. Do names fall naturally
from that sentence and retain the same meaning everywhere?

### B10 — Minimize conceptual weight and omit uncertain commitments

**Sources:** `abstract.md:L48-L50`; `transcript.txt:L117-L127`

"When in doubt, leave it out" applies to functionality, types, methods, and
parameters. Addition remains possible; removal usually does not. Measure size
by concepts users must learn, not raw declarations. Reusing an already-familiar
platform abstraction can add implementations or capability without adding a
new conceptual language.

**Practical test:** Which new concept must a user learn for this element? Is it
required by a present use case? Could an existing, appropriate abstraction
carry the same meaning?

### B11 — Keep replaceable implementation choices out of the contract

**Sources:** `abstract.md:L52-L52`; `transcript.txt:L127-L139`

Implementation details confuse users and remove implementer freedom. Leakage
can occur through types, errors, serialization forms, documented algorithms,
wire/storage representations, or any behavior clients can observe and begin to
depend on. Specify the guarantees clients need, not incidental facts about the
current implementation. Some details truly are contract when persistence or
interoperation depends on them; make that commitment deliberately.

**Practical test:** Could storage, transport, algorithm, or internal structure
change while conforming to the API? If not, did a use case require that detail
to be fixed?

### B12 — Expose as little as possible

**Sources:** `abstract.md:L62-L62`; `transcript.txt:L139-L143`

Minimize accessibility of types, members, and state. A narrow exported surface
reduces coupling and lets components be understood, implemented, tested,
optimized, and changed independently. Public mutable fields are especially
costly because they expose representation and behavior at once; constants are
the narrow exception described in the talk.

**Practical test:** Does each exported element need to be called, implemented,
or named by a client? What freedom returns if it becomes private?

### B13 — Document every exported contract, not the current implementation

**Sources:** `abstract.md:L56-L56`; `transcript.txt:L153-L169`

Document every exported type, operation, field, parameter, and failure. For an
operation, state preconditions, postconditions, and side effects. For data,
state units, formats, and ownership: can the client mutate or retain a passed
object, or has control transferred? For mutable abstractions, document the
state space and which operations are legal in each state. Without a contract,
clients must guess or treat source code as specification, accidentally freezing
implementation details.

**Practical test:** Can a client predict legal calls and observable outcomes
without reading the implementation?

### B14 — Consider lasting performance constraints without warping the API

**Sources:** `abstract.md:L58-L58`; `transcript.txt:L169-L181`

API choices can permanently prevent efficient implementations, so consider
performance consequences while the surface is still malleable. But do not
damage a long-lived API to bypass a temporary implementation cost. Good
encapsulation, appropriate abstraction, and deliberate mutability often permit
both clarity and efficient implementations.

**Practical test:** Does the contract force allocation, copying, traversal, or a
specific implementation? Is the proposed workaround tied to a temporary cost?

### B15 — Design in the target platform's native language

**Sources:** `abstract.md:L60-L60`; `transcript.txt:L181-L189`

An API must coexist with its platform. Follow its customary naming and core
patterns so users can transfer existing knowledge. Do not transliterate types
and methods from an SDK in another language. Step back to the capability and
express it as the target platform ordinarily would.

**Practical test:** Does this look like a natural member of the target ecosystem,
or like another language's API with spelling changes?

### B16 — Avoid artificial fixed input limits

**Sources:** `abstract.md:L42-L42`; `abstract.md:L96-L96`

Fixed size limits narrow legitimate use and hasten obsolescence. Do not make a
ceiling part of the public contract merely because the present implementation
finds it convenient. Under B28, a genuine domain or resource boundary may
justify a limit; distinguish that reasoned exception from an implementation
shortcut.

**Practical test:** Is the limit inherent in the promised capability, or could a
future implementation reasonably lift it?

## Types, objects, and extension

### B17 — Minimize mutability and state space

**Sources:** `abstract.md:L54-L54`; `transcript.txt:L189-L199`

Prefer immutable values because they are simpler, safely shareable, and easier
to reason about. When the represented concept must change, expose the smallest
well-defined state space: make legal transitions clear and avoid reuse cycles
that add states merely to save object creation. Hidden mutability is still
mutability and can surprise concurrent clients.

**Practical test:** What real-world fact requires this object to change? Can its
lifecycle and every legal transition be stated briefly?

### B18 — Use inheritance only for honest substitutability and make it safe

**Sources:** `abstract.md:L64-L66`; `transcript.txt:L199-L215`

Expose a subtype relationship only when every subtype value can honestly stand
where the supertype is promised; implementation reuse alone is not a reason.
An extensible base abstraction must deliberately specify how overridable
operations interact—its self-use patterns—because implementation changes can
otherwise break subclasses. If that contract is not designed and documented,
prohibit public subclassing through the target language's available mechanism.

**Practical test:** Is every proposed subtype truly an instance of the promised
supertype behavior? Could a base implementation change invalidate an override?

## Operations and client behavior

### B19 — Put necessary repeatable work in the library

**Sources:** `abstract.md:L68-L68`; `transcript.txt:L215-L235`

Do not make every client perform a sequence the module can perform correctly
itself. Repeated ceremony is ugly, hard to read, and a copy-and-modify source of
bugs. This principle checks B10's omission pressure: omit speculative
convenience, but absorb necessary mechanics demonstrated by a use case.

**Practical test:** Which lines in each client are identical plumbing rather
than an expression of client intent? Can the SDK own them without hiding a
meaningful choice?

### B20 — Make behavior match the reasonable reading of its name

**Sources:** `abstract.md:L70-L70`; `transcript.txt:L235-L243`

Follow least astonishment. A name should describe the primary effect, including
important mutation or other side effects. Extra implementation effort, and
sometimes reduced performance, is justified when it prevents users from making
the predictable wrong assumption.

**Practical test:** Before reading documentation, what would an intended user
expect this call to observe or change? Does the implementation do more?

### B21 — Detect errors as early as the platform permits

**Sources:** `abstract.md:L72-L72`; `transcript.txt:L245-L251`

Move errors toward design or construction time when the language can express
the constraint. Otherwise reject invalid input at the first operation that can
recognize it, rather than storing bad state and failing later. Early failure
localizes cause and limits damage.

**Practical test:** How far can invalid data travel before rejection? Will the
reported failure point identify the client action that caused it?

### B22 — Give structured access to information rendered as text

**Sources:** `abstract.md:L80-L80`; `transcript.txt:L253-L255`

Whenever the API exposes information in a display string, also expose that
information programmatically. Otherwise clients must parse text, and the
format becomes an accidental compatibility contract that cannot safely evolve.
Make clear when a display form is not a parseable protocol.

**Practical test:** Could a legitimate program need any datum embedded in this
string? If so, where is its structured accessor?

### B23 — Overload only when shared behavior makes the choice unsurprising

**Sources:** `abstract.md:L82-L82`; `transcript.txt:L257-L261`

Overloads or equivalent same-name variants are dangerous when the same value
can select behaviors with different meaning. Prefer distinct names when
behavior differs, or make the behavior depend consistently on the runtime value
when that is the actual contract. Translate this to whatever call-dispatch
mechanisms the target language offers.

**Practical test:** Can a cast, inferred type, omitted label, or resolution rule
silently change meaning? Would separate names communicate the distinction?

### B24 — Use types that state the real contract

**Sources:** `abstract.md:L84-L84`; `transcript.txt:L263-L271`

Choose parameter and result types appropriate to the represented value. Favor
an appropriate interface over a concrete implementation, while making input
types specific enough that every accepted value is valid. Convert wire strings
into meaningful values rather than spreading representation through the SDK.
Use numerics that preserve the required semantics, such as exact values for
money.

**Practical test:** Does the type admit values the operation cannot honor? Is a
string or primitive standing in for a meaningful domain value?

### B25 — Keep parameter order and count easy to use correctly

**Sources:** `abstract.md:L86-L88`; `transcript.txt:L273-L283`

Use consistent parameter ordering across related operations. Keep lists short,
especially where adjacent parameters share a type and accidental swapping
cannot be detected. Shorter operations, a helper value, named arguments, or a
builder are possible mechanisms; choose the customary target-platform form
rather than mandating the talk's Java example.

**Practical test:** Can a user recall the order from related calls? Can two
same-shaped values be swapped while still appearing valid?

### B26 — Prefer ordinary return shapes over rare sentinel handling

**Sources:** `abstract.md:L90-L90`; `transcript.txt:L283-L287`

Avoid results that require exceptional client processing when a normal
value-shaped result exists. Rare sentinels are forgotten because most calls do
not exercise them. An empty collection rather than absence is the talk's
example; apply the principle according to the result's actual meaning and the
target platform's conventions.

**Practical test:** Must every caller remember a branch that is rarely needed?
Can a normal result represent the outcome without losing information?

### B27 — Use exceptions only for exceptional conditions

**Sources:** `abstract.md:L92-L94`

Do not require exception handling for normal flow; it makes client programs
harder to read and can make them buggy or slow. Where a language distinguishes
checked from unchecked failures, require explicit recovery only when a client
can realistically recover. Choose the target platform's mechanism while
preserving those two judgments.

**Practical test:** Is this outcome expected during correct ordinary use? If
handling is forced, what realistic recovery can the client perform?

## Applying the principles

### B28 — Treat the rules as judgment aids, not a mechanical scoring system

**Sources:** `abstract.md:L96-L96`; `transcript.txt:L93-L99`

API design is an art. Seek a cohesive, intelligible whole and trust informed
judgment. Violate a heuristic rarely and for a reason tied to audience and use
cases. Record the tradeoff so a future designer knows whether the exception is
still justified.

When principles pull in different directions, return to B02 and B03: serve the
intended audience's demonstrated use cases, make the correct path natural, and
avoid commitments unsupported by evidence. Common tensions include:

- **B10 omission versus B19 convenience:** omit speculative helpers, but absorb
  necessary boilerplate repeated by real use cases.
- **B09 symmetry versus B10 surface size:** add the symmetric operation only if
  the domain and use cases make the symmetry real.
- **B14 performance versus B20 astonishment:** consider lasting performance
  constraints, but do not surprise users to bypass a temporary cost.
- **B11 hiding versus B13 documentation:** document observable guarantees fully
  without promising incidental algorithms or representation.
- **B08 compatibility versus correction:** improve unpublished drafts freely;
  extend established APIs without silently changing client meaning.

**Practical test:** Which use case or audience fact justifies the exception, and
what evidence would cause the decision to be revisited?
