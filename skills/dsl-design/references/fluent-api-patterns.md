# Fluent API Patterns

Condensed from Martin Fowler, *Domain-Specific Languages* (2010), Part IV (Ch. 32–46) — the internal-DSL patterns and Fowler's synthesis of how to
choose among them; citations kept for traceability.

## Contents

- [Three framing ideas](#three-framing-ideas)
- **Function combination:** [Expression Builder](#expression-builder-ch-32) · [Function Sequence](#function-sequence-ch-33) · [Nested
  Function](#nested-function-ch-34) · [Method Chaining](#method-chaining-ch-35) · [Object Scoping](#object-scoping-ch-36) · [Closure](#closure-ch-37) ·
  [Nested Closure](#nested-closure-ch-38)
- **Choosing:** [Grammar → technique](#grammar--technique-mapping) · [Decision sequence](#the-decision-sequence) · [Evaluation-order
  tradeoff](#the-evaluation-order-tradeoff) · [Context-handling arc](#the-context-handling-arc) · [Finishing problem](#the-finishing-problem-restated) ·
  [Licensed violations](#convention-violations-licensed-inside-the-fence)
- **Expressive vocabulary:** [Literal List](#literal-list-ch-39) · [Literal Map](#literal-map-ch-40) · [Dynamic Reception](#dynamic-reception-ch-41) ·
  [Annotation](#annotation-ch-42) · [Parse Tree Manipulation](#parse-tree-manipulation-ch-43) · [Class Symbol Table](#class-symbol-table-ch-44) ·
  [Textual Polishing](#textual-polishing-ch-45) · [Literal Extension](#literal-extension-ch-46)
- [The judgement calls, collected](#the-judgement-calls-collected)

---

## Three framing ideas

**1. Fluent interface vs. command-query API.** The normal style — self-standing methods obeying command-query separation — is a **command-query API**;
"it's so normal that we don't have a general name for it" *(Ch. 32)*. A **fluent interface** optimizes readability of *the whole expression*, so fluent
methods "make little sense individually, and often violate the rules for good command-query APIs." They get license to break normal rules; the price is
quarantine.

**2. Fluent API design *is* grammar design.** Write the BNF-ish production the clause must satisfy, then read off the technique that fits. The resulting
tree of Expression Builders "really is a syntax tree for the DSL."

**3. Evaluation order is a first-class design variable.** Function Sequence and Method Chaining run left-to-right; Nested Function evaluates arguments
*before* the enclosing call; Nested Closure lets the parent decide *when*. Most tradeoffs here reduce to which evaluation order you need.

---

## Expression Builder (Ch. 32)

> **Intent:** "An object, or family of objects, that provides a fluent interface over a normal command-query API." *(Ch. 32)*

**Concept.** A separate layer that hosts the fluent methods and translates them into ordinary command-query calls on the Semantic Model. Two interfaces
coexist: the normal one on domain objects, the fluent one on builders, "clearly isolated, making it easier to follow." Fluent methods *are* strange —
mutators returning `this`, query-shaped names for commands, `First()`/`Third()` where a parameter belongs, C# getters that mutate ("I would confine this
abomination to a securely fenced Expression Builder," *Ch. 35*). **The builder is the fence.**

**Mechanics.** Translation layer, fluent in and command-query out; "often a *Composite* using child Expression Builders" for subexpressions. **One vs.
many builders** is "one of the most notable questions": a tree of builders mirrors the syntax tree, and "the more complex the DSL, the more valuable a
tree of Expression Builders is." **Key structural tip:** keep the Semantic Model usable *without any DSL at all*, with tests touching only that
interface, and test builders by comparing the model objects they produce. **Immutable models** leave fluent calls nowhere to write, so buffer — Context
Variables on one builder, or (preferred) a child builder per subexpression with the parent holding a list of children. Each child keeps a back-pointer,
because **the punctuation call that starts the *next* child arrives at the child and must be forwarded upward**; a final `getContent()` materializes the
whole model at once, which is what permits immutability.

**When to use it.** A **default** — "I tend to use it pretty much all the time unless there's a good reason not to." Against putting fluent methods on
the Semantic Model, in order of weight: (1) **separation of concerns** — building logic and execution logic are both substantial, and "it's easier to
understand if we separate" them; (2) **unfamiliarity** — one class then mixes two API styles, the rarer of which developers know less well. Best
argument for merging: execution logic so simple that building adds little complexity. Cost of skipping the builder: anyone modifying the object outside
the DSL needs normal mutators too, so the class carries two overlapping mutation APIs, and the fluent one used out of context "would lead to
hard-to-read code."

**Relationships.** Supplies the object **Method Chaining** chains on and the class **Object Scoping** scopes to; hosts **Context Variables (Ch. 13)**;
uses **Construction Builder (Ch. 14)**; produces the **Semantic Model (Ch. 11)**, which must stay independently usable.

> **SDK lens:** *The* foundational SDK pattern here. Keep the fluent surface in builder types and resource/response objects plain — users hold domain
> objects at runtime and should never meet a mutator returning `this`. Make the plain API complete enough that the SDK works without the sugar, and
> **prove it with tests touching only the plain API**: a guard against features reachable only through the DSL. Model the builder tree on the
> *configuration grammar*, not the class hierarchy. Immutable models plus fluent building work only if you buffer in builders and construct at the end —
> the justification for `build()` terminals.

---

## Function Sequence (Ch. 33)

> **Intent:** "A combination of function calls as a sequence of statements." *(Ch. 33)*

**Concept.** A flat run of statements with "no data relationship between them" — calls relate only by order in time. Apparent structure is **not in the
code**; the builder reconstructs it from parse state, so "a heavy use of Function Sequence means you use a lot of Context Variables." Indentation is
"just arbitrary use of whitespace."

**Mechanics.** Readability wants **bare** calls, which global functions supply along with two problems. Narrow **global visibility** by namespacing down
to the builder; without global functions you write class-qualified calls, "which often adds noise to the DSL." **Static parse data** is worse — you can
never be sure who is using it, "particularly with multithreading," and it is "particularly pernicious with Function Sequence." **Object Scoping fixes
both**: use it "in all but the very simplest cases." The visible cost: `speed()` is ambiguous between processor and disk, so it must branch on which
Context Variable is set and throw if neither is — clause resolution becomes runtime state inspection, and illegal scripts fail at runtime, not compile
time.

**When to use it.** The bluntest verdict in the part: "the least useful of the function call combinations," because tracking a parse with Context
Variables "is always awkward, leading to code that's hard to understand and easy to get wrong." Reasonable only **(a) at the top level** of a language,
or the top level inside a Nested Closure, where one result list and one Context Variable suffice — below that, use Nested Function or Method Chaining;
and **(b) because you have to start somehow**: every DSL opens with a Function Sequence of at least one call, since "all the other function call
techniques require some kind of context." For the simple case, **Literal List (Ch. 39)** substitutes.

**Relationships.** Requires Context Variables, should use Object Scoping, uses Construction Builder; alternative is Literal List; dramatically improved
by a wrapping **Nested Closure** that creates the Context Variable before the sequence and tears it down after.

> **SDK lens:** The imperative statement-style config API — `client.setRegion(...); client.setRetries(...);`, or top-level calls mutating shared session
> state. If you need hidden mutable state to answer "which thing am I configuring right now?", you are here and inherit the costs: thread hazards,
> order-dependence, names that dispatch on state, runtime-only errors. **Static/global parse state is the specific thing to refuse** — bind state to an
> instance. A top-level sequence of independent operations is fine; *nested* configuration this way is not.

---

## Nested Function (Ch. 34)

> **Intent:** "Compose functions by nesting function calls as arguments of other calls." *(Ch. 34)*

**Concept.** Subelements are literally the arguments: `computer(processor(cores(2)), disk(size(150)))`. The DSL's hierarchy becomes the host language's
expression tree, "not just in a formatting convention." **The structure is real, not indentation.**

**Mechanics.** **Evaluation order is the defining property:** arguments evaluate before the enclosing call — the **Old MacDonald problem**, where you
type the vowels inside-out. Consequences: a built-in context for the arguments (children return fully formed values the parent assembles); **no
finishing problem** (the outermost bracket *is* the end); **no Context Variable** (data flows through return values). **Fit to grammar:** with mandatory
elements "along the lines of `parent ::= first second`, Nested Function works particularly well" — the signature declares the required arguments and
their types, enabling autocompletion.

**Labeling arguments.** `disk(150, 7200)` gives "no indication what the numbers mean, unless you have a language with keyword arguments." Wrap each
value in a naming function; a wrapper that returns its argument unchanged is "pure syntactic sugar" and **enforces nothing** — `disk(speed(7200),
size(150))` "could easily result in a very slow disk." Returning intermediate data makes the type system carry the meaning. **Optional arguments:** use
defaults, else one function per combination — "tedious but reasonable" for a couple, but "as the number of optional arguments increases, so does the
tediousness (but not the reasonableness)"; **Literal Map (Ch. 40)** is the cleanest escape where available. Repetition → varargs, "a nested Literal
List." **The worst case** is `parent ::= (this | that)*`: without keyword arguments, identification is by position and type alone, "downright impossible
if `this` and `that` have the same types," forcing intermediate results or a Context Variable — and the Context Variable route is hard "since the parent
function isn't evaluated till the end." **Bare calls are an asymmetry:** global functions are much less problematic here, since their "biggest problem…
is when they come with a global parsing state," which Nested Function rarely needs. **Tokens** (type tag + value, dispatched by the parent) turn "which
argument is this?" from a positional into a *data* question, buying ordering and optionality; **subtype tokens** go further — "you want autocompletion
popups to force you to put size before speed. By using subclasses, you can pull this off" — making `disk(SizeToken, SpeedToken)` compiler-enforced, the
Nested Function analogue of **progressive interfaces**.

**When to use it.** **Strength and weakness are the same thing: evaluation order.** Arguments-first is "very useful for building up a hierarchy of
values," but **wrong for command sequences** — for left-to-right reading prefer Function Sequence or Method Chaining, and "for precise control of when
to evaluate multiple arguments, use Nested Closure." **Weak on optionality and variety:** it "expects you to say what you want and in the precise order
you want it"; for flexibility, "look to Method Chaining or a Literal Map." **Punctuation is the aesthetic cost** — at worst "a disfigured Lisp," though
"less of an issue for DSLs aimed at programmers." **Name clashes are less trouble than with Function Sequence**, "since the parent function provides the
context to interpret the nested function call." And "Nested Function is the better choice for mandatory clauses" *(Ch. 35)*. Two lessons from the
recurring-events example: **the DSL may read *opposite* to the model** ("first and third Monday" is `Or` in the specification, "so that both read
naturally"), and **name for the reader of the script** — `Schedule`, not `ScheduleBuilder`.

**Relationships.** Opposes Function Sequence / Method Chaining on evaluation order; complemented by **Literal List** (varargs), **Literal Map**
(optionality + ordering), **Nested Closure** (control of *when*), **Object Scoping** (bare calls), **Expression Builder**.

> **SDK lens:** The "constructor / nested options-object" style, and the only technique here that can *require* things. **Required parameters and
> structural hierarchy belong here** — what must be present belongs in the signature, not in chainable setters that can always be omitted. Sugar
> wrappers that only label a value enforce nothing; typed wrappers enforce *and* drive autocomplete, the tradeoff behind newtype/branded parameters. The
> crucial judgement is the **degradation curve**: excellent for a fixed mandatory shape, worse with every optional setting added (combinatorial
> overloads, positional ambiguity, unordered heterogeneous arguments) — exactly where builders and option maps win. Prefer keyword arguments / options
> objects wherever the language has them.

---

## Method Chaining (Ch. 35)

> **Intent:** "Make modifier methods return the host object, so that multiple modifiers can be invoked in a single expression." *(Ch. 35)*

**Concept.** `new HardDrive().capacity(150).external().speed(7200)`. Fowler's corrective: chaining "caught on a bit too much — people started to assume
that Method Chaining was synonymous with fluent interfaces and internal DSLs," when "it's one of several techniques."

**Mechanics.** It **breaks command-query separation knowingly** ("a fluent interface is one case when we need to break it") and **breaks naming
conventions**: a `sata()` that modifies "would seem like a query… it will seriously confuse anyone who is expecting a command-query API." Two
independent reasons to fence it in a builder. It also **changes formatting conventions** — one call per line, because "error messages and debugger
control usually work on a line-by-line basis." **Constructors aren't the answer**: they are hard to read, "since constructors often allow only
positional parameters." **Builders or values:** prefer chaining on Expression Builders, which "reduces the confusion between the conventions of fluent
and command-query APIs"; chaining on domain types (`42.grams.flour`, each step a different Value Object) is Neal Ford's **type transmogrification**, and
Fowler is non-dogmatic — "plenty of good developers… are comfortable with [it]… My inclination, however, leads me to prefer using Expression Builders as
much as possible."

**The finishing problem.** "It boils down to the lack of a clear end-point to a method chain": every method must return a builder, so nothing signals
completion and the finished object never appears. Options, ranked: (1) **a natural last clause that returns the finished object**, best when the grammar
has a terminal clause; (2) **an explicit finisher** (`.end()`, `.build()`) — "isn't too bad, but… still a bit of syntactic noise"; (3) **an implicit
conversion operator** (C#), which "does mean you'll forgo `var` for an explicit type"; (4) **use a different pattern** — "this is where using Nested
Function or Nested Closure can be a valuable alternative," their enclosing call being the terminator. Without a finisher you must split into a builder
statement plus a separate `getValue()`.

**Hierarchic structure.** Chaining "doesn't naturally fit a hierarchic structure," so hierarchy ends up "suggested by the indentation and not captured
in the structure of the code itself. As a result, we have to manage that structure ourselves. This problem also occurs with Function Sequence." Two
strategies: **Context Variables**, or **a child builder per subelement**, whose real payoff is grammar scoping — "a separate builder allows us to limit
the methods available to only those required." Simple Construction Builders suit simple cases while "full delegation works better for more complicated
cases." **Punctuation forwarding** recurs: a child builder must forward calls belonging to the parent. Balanced verdict: chaining "reads very clearly,"
but "to pull it off, I have to do a lot of fiddling around with Context Variables and cope with the finishing problem."

**Progressive interfaces — type-encoded grammars.** Use "multiple interfaces to drive a fixed sequence of method-chaining calls": the first exposes only
`to`; `to` returns an interface exposing only `to`/`cc`/`subject`; `subject` returns one exposing only `body`. One builder implements all of them, each
method returning `this` *typed as the next interface*; interfaces may inherit so later stages keep earlier legal steps. **Payoff:** autocompletion "can
step you through each clause in the DSL by only suggesting the methods that are valid for that point in the chain" — caveat, "methods inherited from
`Object` also show up." Versus child builders: either can scope legality, "but progressive interfaces are easier if there's no other reason to make a
child builder." **Mandatory elements:** "define an interface that only takes a single mandatory element."

**When to use it.** Best "when it's used in conjunction with other function combinations," and **best for optional clauses** — it "easily allows a DSL
script writer to pick and choose clauses," whereas requiring a clause is impossible: "progressive interfaces allow some ordering… but in the end clauses
can always be left out. Nested Function is the better choice for mandatory clauses." **Escape hatches:** on hitting the finishing problem "you're better
off using a Nested Function or Nested Closure," which "are also better choices if you are getting into a mess with Context Variables."

**Relationships.** Usually hosted on an **Expression Builder**, sometimes on Value Objects (with **Literal Extension**); needs **Context Variables** or
child builders for hierarchy; progressive interfaces ≈ subtype tokens (Ch. 34).

> **SDK lens:** The highest-density SDK chapter in the book. **The finishing problem is the everyday `.build()` question**, and the ranking transfers
> directly: natural terminal clause (best), explicit `build()`/`end()` (acceptable, noisy), implicit conversion (costs type inference), or restructure
> to a callback form where the enclosing call terminates (often the real answer). **Progressive interfaces are the type-state pattern**: a narrower
> interface per step makes illegal call sequences fail at *compile* time and turns autocomplete into documentation — how SDKs enforce "set auth before
> you send." **Chaining cannot express requirement**; required inputs belong in the factory/constructor. **Chain on builders, not on the objects users
> keep.** **Hierarchy needs child builders, not indentation** — and a child builder must forward the parent's punctuation, or users hit "method not
> found" mid-chain. **Formatting is API design**: one call per line is what makes stack traces point at the failing clause.

---

## Object Scoping (Ch. 36)

> **Intent:** "Place the DSL script so that bare references will resolve to a single object." *(Ch. 36)*

**Concept.** Bare calls aid readability, "but in their basic forms they come with a serious cost: global functions and (worse) global state." Object
Scoping resolves bare calls against one host object, avoiding a cluttered global namespace and "allowing you to store any parsing data within the host
object. The most common way… is to write the DSL script inside a subclass of a builder that defines the functions."

**Mechanics.** Objects give "a contained scope for functions and data," and inheritance lets you "use this scope separately from where it's defined":
put DSL functions and parse-data fields on a base class — the natural home of the **Expression Builder** — and write scripts in subclasses, which may
add or override DSL functions. **Alternatives to inheritance:** Ruby's **instance evaluation** (`instance_eval`), which runs code "within the context of
a particular object" with no declared link to the base class, and Java's **instance initializers** (double-brace idiom), "not well known nor often used,
but can work well." **Scope switching down the tree:** instance-evaluating *child* builders lets one bare name bind differently at different depths —
how you get multiple builders *and* bare calls.

**When to use it.** "I would always suggest using Object Scoping if you can." Where you can't or shouldn't: **it requires an OO language**; **it
constrains where the script lives** (inside a method in a builder subclass — fine for self-contained scripts in their own file); **the real problem is
fragmentary DSLs**, where it "forces you into an inheritance relationship that may be awkward or even impossible" — the **self-contained vs.
fragmentary** distinction that recurs in Ch. 38 and is one of the most transferable ideas in Part IV; **sometimes globals are fine**, since the biggest
problem with global functions is modifying global data, so a bare function that merely creates and returns an object needs much less protection; and
there is an **extensibility bonus** — user subclasses extend the language, and "if particular methods are only needed in one script, then that script
subclass can define those methods directly."

**Two lessons this chapter carries.** (1) **Make the DSL surface deliberately less expressive than the model** *(Ch. 36, "Security Codes")* — the model
allows arbitrary Booleans, the DSL only conjunction, because such expressions are "often difficult for people, particularly non-nerds, to follow. So
some form of simplified structure can be handy in a DSL." (2) **Push boilerplate onto the library, not the user** — passing the target via a build
method avoids forcing a constructor declaration into the user's subclass: "a small thing, but… these small things add up." Honest cost: the pattern
"does introduce noise in the code that declares the DSL class."

**Relationships.** Enables bare calls for **Function Sequence** and **Nested Function**; hosts the **Expression Builder** and its **Context Variables**;
needed for bare calls inside a **Nested Closure**; `instance_eval` links it to **Closure** and **Dynamic Reception**.

> **SDK lens:** The "configuration block / DSL block" family — Gradle, RSpec, JMock, Rails initializers, Kotlin receiver lambdas. It answers a real SDK
> question: how to give users terse unqualified vocabulary without a global namespace or global mutable state? Bind the vocabulary to an instance and
> run the user's code inside that instance's scope. **The self-contained vs. fragmentary axis is the decision rule** — a standalone config file can
> afford an implicit receiver; a few lines embedded in application code should not force inheritance or a rebound `this`. **Extensibility falls out for
> free** (user subclasses = plugin points), and **boilerplate belongs on the library**, since every declaration forced into user code is noise paid at
> every use site.

---

## Closure (Ch. 37)

> **Intent:** "A block of code that can be represented as an object… placed seamlessly into the flow of code by allowing it to reference its lexical
> scope." *(Ch. 37)* **Also known as:** lambda, block, anonymous function.

**Concept.** **"A Closure is a code fragment that can be treated as an object."** The motivating problem is two loops differing only in a Boolean test:
the varying part "is a chunk of behavior — which is often not easy to parametrize." The OO answer (a filter interface plus a class per predicate) works,
but "there's so much code in setting up the predicate object that the cure is worse than the disease."

**Mechanics.** **Terminology is a mess and Fowler says so** — lambda, block, anonymous function, no standard term. **What makes it a closure:** the
block *uses* a local from the enclosing scope, saving "all the faffing around with parameters," and those variables stay usable even if the block is
stored and run much later. **Terseness is the whole ballgame:** "**the usefulness of Closures is directly proportional to how terse they are to use**."
**The libraries have to cooperate** — "for Closures to be really useful in a language, the libraries need to be written with Closures in mind."
**Deferred evaluation** is why "Closures [are] so useful for Adaptive Models." **Language limits shape the API:** Ruby's pretty block syntax passes only
*one* closure.

**When to use it.** General programming: "a valuable tool to take chunks of logic and arrange them to eliminate duplication and support custom control
structures." In DSLs: "an essential element for Nested Closure. They also can make it easier to define an Adaptive Model."

**Relationships.** Prerequisite for **Nested Closure**; enables **Adaptive Model**; preferred alternative to **Macro (Ch. 15)** for deferred evaluation;
interacts with **Object Scoping** where the execution context can be rebound.

> **SDK lens:** Callbacks, handlers, predicates, interceptors as first-class parameters. **Custom control structures**: the SDK owns setup and teardown,
> the user supplies the middle — retries, transactions, connection scoping, instrumentation spans; the mechanism behind context-manager APIs. **Deferred
> evaluation**: taking a closure rather than a value lets the SDK decide *whether* and *how many times* to evaluate. Two constraints: such an API is
> only pleasant if the language's closure syntax is terse (a legitimate reason for per-language surfaces to differ), and the *whole library* must be
> closure-designed or users get a fluent island in an imperative sea.

---

## Nested Closure (Ch. 38)

> **Intent:** "Express statement subelements of a function call by putting them into a closure in an argument." *(Ch. 38)*

**Concept.** Nested Function with the children wrapped in a closure — `processor(cores(2), i386)` becomes `processor { cores 2; i386 }`: "instead of
passing two Nested Function arguments, I pass a single Nested Closure argument."

**Mechanics.** **The central mechanic: you control evaluation.** The closure runs only when you program it to, and "**the `processor` function can also
carry out other tasks before and after the closure evaluation, such as setting up Context Variables**." That bracketing is the value proposition: the
parent creates the Context Variable before evaluating the closure and tears it down after, which "can greatly reduce the problem of Context Variables
appearing all over the place." **Three shapes go inside:** a **Function Sequence** bracketed by the parent's setup/teardown; **Method Chaining**, where
"the parent function can set up the head of the chain and pass it into the closure as an argument"; or a **Function Sequence with an explicit Context
Variable as the closure argument**, which "often makes it easier to follow, without adding too much clutter." **Scoping:** bare functions inside a
closure resolve in its *defining* scope, "so, again, it's usually wise to use Object Scoping" — or pass an explicit Context Variable / use Method
Chaining, which also lets you split code into different builders. **Multiple closures** let each subclosure evaluate independently, canonically a
two-branch conditional. **The delimiters are not noise:** they "introduce an explicit hierarchic structure to what otherwise is a linear sequence with a
formatting convention… marking the structure from the reader's point of view." Child builders inside closures also allow "an unqualified `speed` method
for both the processor and the disk without ambiguity" — **structural disambiguation replaces runtime disambiguation.** Candid on language fit: the
pattern "works much less well in C# than it did in Ruby."

**Self-contained vs. fragmentary — the instance_eval reversal.** Instance evaluation gives multiple builders *and* bare calls by changing what `self`
means inside the block. It looks free; it isn't. Jim Weirich's builder library "used `instance_eval`, but later switched to explicit parameters. The
reason is that **programmers are used to the call behavior with closures; redefining `self` causes a lot of confusion and makes it very difficult to
refer to elements in the static context that you need.**" Fowler's rule: "the choice lies in whether you are using the DSL script in a self-contained or
fragmentary style. In a fragmentary context… redefining `self`… is not a good choice. With self-contained DSL scripts… the redefinition then doesn't
cause confusion and is worth it to remove the noisy references." Real Ruby DSLs use Function Sequence inside each closure with an explicit closure
argument, which "results in a more regular style of code that rubyists find easier to work with." **Explicit receivers cost characters and buy
regularity, multiple builders, and fragmentary usability.**

**When to use it.** It "combines the explicitly hierarchic structure of Nested Function with the ability to control when the arguments are evaluated,"
avoiding "many of the limitations of Nested Function." **The core limitation is the host language:** many have no closures, and those that do "often
provide the syntax in a way that doesn't jive terribly well with DSLs." **Best mental model — an enhancement, not a rival:** treat it "as an enhancement
to Nested Function, Function Sequence, and Method Chaining," all of which "boil down to the fact that you can do specific setup and tear-down operations
on either side of the closure invocations."

**Relationships.** Built on **Closure**; enhances the other three combinations; tames **Context Variables** by bounding their lifetime; interacts with
**Object Scoping**; solves Method Chaining's **finishing problem** and Function Sequence's context sprawl.

> **SDK lens:** The "configuration block" API — `resource("x") { … }`, `with_transaction { … }`, Kotlin receiver lambdas, Gradle. **Setup/teardown
> around the closure is the SDK superpower**: it makes context-manager APIs work and scopes "which object am I configuring" to a lexical block instead
> of a mutable field — if your builder has a `currentThing` field, a block-scoped API removes it. **It fixes hierarchy and finishing at once**: the
> block delimits the subexpression, so there is nothing to `.end()`. **Explicit vs. implicit receiver is load-bearing**: explicit costs characters but
> preserves scoping intuitions, works fragmentarily, and enables multiple builders; implicit is terser for standalone config files but surprises readers
> and breaks access to enclosing scope. Fowler's rule — implicit for self-contained, explicit for fragmentary — is directly usable, and Weirich's
> reversal is the cautionary tale.

---

## Choosing among the fluent techniques

These seven are not alternatives picked by taste. Fowler chooses by writing the grammar production the clause must satisfy and reading off the technique
that fits.

### Grammar → technique mapping

| Grammar shape | Recommended technique | Why |
|---|---|---|
| `parent ::= first second` (fixed, mandatory children) | **Nested Function** | The parent's signature declares exactly the required arguments and, when statically typed, their types *(Ch. 34, "How It Works")* |
| `parent ::= (this \| that)*` (heterogeneous, repeatable, unordered) | Nested Function's **worst case** — forces intermediate tokens or a Context Variable; prefer **Literal Map** / keyword args, or **Method Chaining** | With no keyword arguments, arguments can only be identified by position and type, "downright impossible if `this` and `that` have the same types" *(Ch. 34, "How It Works")* |
| `parent ::= child*` (homogeneous repetition) | **Literal List** / varargs, usually nested inside a Nested Function | *(Ch. 34, "How It Works"; Ch. 39, "When to Use It")* |
| Mostly-optional clauses, any subset | **Method Chaining** | "Method Chaining easily allows a DSL script writer to pick and choose clauses" *(Ch. 35, "When to Use It")* |
| Mandatory clauses, or a required *order* of clauses | **Nested Function**, or Method Chaining + **progressive interfaces** | Plain chaining can never require a clause; progressive interfaces enforce ordering and can enforce a mandatory element via an interface exposing only it *(Ch. 35, "Progressive Interfaces" / "When to Use It")* |
| Hierarchy that must be structural, not cosmetic | **Nested Function** or **Nested Closure** | Function Sequence and Method Chaining only *suggest* hierarchy through indentation *(Ch. 35, "Hierarchic Structure")* |
| A top-level list of statements | **Function Sequence** (with Object Scoping), or a Function Sequence inside a **Nested Closure** | Only one result list and one Context Variable needed *(Ch. 33, "When to Use It")* |

### The decision sequence

1. **Start with an Expression Builder.** Default; keep the fluent layer off the Semantic Model *(Ch. 32)*.
2. **You must start the DSL with a Function Sequence of at least one call**, because every other technique needs a context to hang off *(Ch. 33)*.
3. **Below the top level, avoid bare Function Sequence.** It's the least useful combination and it forces Context Variables *(Ch. 33)*.
4. **Mandatory / hierarchical / fixed-shape → Nested Function** *(Ch. 34)*.
5. **Optional / pick-and-choose → Method Chaining**, accepting that you can't require anything, you'll manage hierarchy yourself, and you'll face the
   finishing problem *(Ch. 35)*.
6. **Need order or requirement *and* you're chaining → progressive interfaces** (or child builders) *(Ch. 35)*.
7. **Lots of optional, unordered, heterogeneous arguments → Literal Map / keyword arguments**, not Nested Function *(Ch. 34)*.
8. **Bare calls without globals → Object Scoping** — unless your bare functions are pure value-returning statics, in which case you may not need it
   *(Ch. 36; Ch. 34)*.
9. **Need control over *when* things evaluate, or want to bracket setup/teardown, or are drowning in Context Variables → Nested Closure** *(Ch. 38)*.
10. **Fragmentary usage constrains everything.** Inheritance-based Object Scoping and implicit-receiver tricks are for self-contained scripts;
    fragmentary DSLs need explicit receivers and no inheritance requirement *(Ch. 36 and Ch. 38)*.

### The evaluation-order tradeoff

- **Function Sequence and Method Chaining evaluate left-to-right.** Natural for a sequence of commands and for reading; but nothing is assembled until
  the end, so structure must be reconstructed from accumulated state.
- **Nested Function evaluates arguments before the enclosing call — inside-out.** Perfect for building a hierarchy of values (children return fully
  formed objects the parent assembles), which is why it needs no Context Variables and has no finishing problem. Wrong for command sequences — the Old
  MacDonald problem *(Ch. 34)*.
- **Nested Closure lets the parent decide when — and whether, and how often.** That single capability buys setup/teardown bracketing, Context Variable
  lifetimes bounded by a block, chain heads passed in as arguments, and independent evaluation of alternative branches *(Ch. 38)*.

### The context-handling arc

| Pattern | How context is carried | Cost |
|---|---|---|
| Function Sequence | Context Variables on the builder (or, badly, statics) | Ambiguous clause names, runtime dispatch, order-dependence, thread hazards |
| Nested Function | Return values of the argument functions | None — but rigid shape, poor optionality |
| Method Chaining | Context Variables *or* child builders | Fiddly; child builders must forward parent punctuation |
| Object Scoping | Instance fields of the scoping builder | Constrains where the script may live |
| Nested Closure | Closure argument, or Context Variables scoped to the closure's lifetime, or a rebound receiver | Language-dependent syntax; receiver rebinding surprises readers |

The trajectory of the whole part: **push context out of global state, into instances, then into return values or lexically scoped blocks.** Each step
trades a bit of syntax for a large reduction in the class of bugs available. That arc — globals → instances → return values → lexically scoped blocks —
is a usable maturity ladder for any configuration API.

### The finishing problem, restated

Only left-to-right techniques have it. Method Chaining must return a builder from every call to keep the chain alive, so no call can return the finished
product and nothing marks the end *(Ch. 35, "Finishing Problem")*. Nested Function and Nested Closure don't have it at all, because the enclosing call's
closing bracket *is* the terminator and its return value *is* the product. When you find yourself designing a `.end()` or `.build()`, that is the moment
to check whether an enclosing-call form would serve better — "usually if you run into this you're better off using a Nested Function or Nested Closure"
*(Ch. 35, "When to Use It")*.

### Convention violations licensed inside the fence

Fluent layers earn a license to break normal API rules, granted by — and only by — isolation in an Expression Builder. The violations Fowler explicitly
endorses:

- **Mutators that return values**, breaking command-query separation *(Ch. 35, "How It Works")*.
- **Query-shaped names for commands** — a `sata()` that sets rather than asks *(Ch. 35, "How It Works")*.
- **Property getters that mutate and return `this`** — "this abomination," acceptable only "when clearly placed in a fluent context" *(Ch. 35, "Chaining
  with Properties (C#)")*.
- **Separate methods where a parameter would be correct design** — `First()` and `Third()` rather than one method with an index *(Ch. 34, "Recurring
  Events (C#)")*.
- **A DSL structure that inverts the model's structure** — "and" in the language meaning `Or` in the specification, so both language and model read
  naturally *(Ch. 34, "Recurring Events (C#)")*.
- **A DSL deliberately less expressive than its own model** — conjunction-only rules over a model supporting arbitrary Booleans *(Ch. 36, "Security
  Codes (C#)")*.
- **Naming rules bent for the script reader** — plural type names, builders named for how they read rather than what they are *(Ch. 34, "Recurring
  Events (C#)"; Ch. 44, "How It Works")*.

The unifying rule: **optimize the fluent layer for the reader of the script, and pay for that by quarantining it away from every object the reader of
ordinary code will touch.** Practical review question for any SDK: *if a user obtained this object from somewhere other than the fluent chain, would its
interface confuse them?* If yes, the fluent methods are on the wrong class.

---

## Literal List (Ch. 39)

> **Intent:** Represent a language expression with a literal list. *(Ch. 39)*

**Concept.** The host language's inline list syntax holding a parent element's children, which the parent walks and interprets. Such syntaxes nest, so
you can build tree-shaped expressions — one view of a Lisp program is as a nested list.

**Mechanics.** Almost always **used inside a function call**, and **the list carries no semantics — the enclosing function supplies them**. **Not all
languages have a usable one:** C-derived languages often permit only constants, not arbitrary symbols or expressions. **Varargs is a substitute**, with
the parent function baked into the syntax, though strongly typed varargs forces all elements to share a type.

**When to use it.** Good when the list sits **nested inside another element** and the grammar is essentially `parent ::= child*`; items are often
function calls themselves, which is what makes **Nested Function** workable. **Prefer varargs over an explicit literal list when the list is an
argument** — Fowler prefers `companions(jo, saraJane, leela)` to `companions([jo, saraJane, leela])`, the brackets being noise when the function
boundary already delimits the list. A DSL built from nothing but Literal Lists is essentially Lisp — natural there, but "little more than a fun exercise
in other languages."

**Relationships.** Pairs with **Nested Function**; adjacent to **Literal Map** (with lists but no maps, encode maps as lists of key/value sublists);
contrasts with **Method Chaining** / **Function Sequence**.

> **SDK lens:** "Prefer varargs to an explicit collection literal" is a durable heuristic: when a parameter is "zero or more of X", a variadic signature
> beats forcing callers to build a collection — *provided* elements are homogeneous; the moment they aren't, the type system pushes you to an options
> object. And a bare list carries no meaning of its own, so a list parameter is only as clear as the function name it sits inside.

---

## Literal Map (Ch. 40)

> **Intent:** Represent an expression as a literal map. *(Ch. 40)*

**Concept.** The host language's inline dictionary syntax — the "named options" construct. Where Literal List expresses "a sequence of children",
**Literal Map expresses "a set of distinct named attributes, each appearing at most once."**

**Mechanics.** **The central weakness is key validation:** in a dynamic language nothing enforces or communicates the valid key set, so you write the
checking yourself and nothing tells the DSL author which keys are correct — **no discoverability**. A static language can dodge this with an enum of
legal key types. **Keys should be symbols** where available. **Keyword arguments are a superior form**, since they often let you declare the valid
keywords, but they are "even rarer than a literal map syntax"; without map literals, fall back to literal lists or alternating key/value arguments.
**Delimiter elision:** where the language lets you drop the braces, exploit it. **Validate the keys — the actionable rule:** diff supplied keys against
an explicit whitelist and raise a dedicated exception **naming the unrecognized keys**, since otherwise a typo silently does nothing; "it's easy for the
caller to introduce an incorrect key by accident, so it's worth doing a little checking here."

**Greenspun form — purity as a diagnostic, not a goal.** Pushing one technique to its limit, explicitly as an exercise: **lists + maps only** turns
every call into a list headed by a symbol, making the script pure nested data processed by a **Recursive Descent Parser** and giving **complete control
over order of evaluation** — "like an external DSL encoded in internal literal collection syntax instead of a string"; **lists only** is more regular
but fits the host idiom badly; and "either case isn't as good as the earlier example which mixed function calls with literal collections."
**Principle:** purity in one technique is a diagnostic exercise, not a goal — when a construct fights the host idiom, stop.

**When to use it.** "A great choice when you need a list of different elements where each element should appear no more than once." Missing key
validation is annoying, but the syntax still wins for this shape: it communicates that each subelement is at-most-once, and the map suits the receiving
function. Otherwise fall back to **Literal List**, **Nested Function**, or **Method Chaining**.

**Relationships.** Complement of **Literal List**; both usually consumed by **Nested Function**; the full-list form leads into **Recursive Descent
Parser** territory.

> **SDK lens:** The **options-object / kwargs API** pattern, and the critique is the modern one: options bags trade discoverability for expressiveness —
> users can't see valid keys, IDEs can't complete them, typos fail silently. **Validate keys explicitly and fail loudly with a message naming the
> offending keys** — the single most actionable takeaway for library authors. **Prefer real keyword parameters, a typed options struct, a TypedDict, or
> an enum-keyed map** wherever available. The shape rule decides whether an options object fits at all: "many distinct, independent, at-most-once named
> attributes" — nothing else.

---

## Dynamic Reception (Ch. 41)

> **Intent:** Handle messages without defining them in the receiving class. *Also known as:* overriding `method_missing` / `doesNotUnderstand`. *(Ch.
> 41)*

**Concept.** Hijack the language's "unknown message" failure path so your object responds meaningfully to method names you never declared —
**dynamically altering the rules for reception of method calls**.

**Mechanics.** Override the hook in your class (general use: automatic delegation). **DSL use 1 — move parameters into the method name:** Active
Record's `find_by_firstname_and_lastname(...)` is defined nowhere; the superclass checks the prefix, parses the name, builds a query — "essentially, you
are embedding an external DSL in the method name." **DSL use 2 — a sequence of receptions:** `find_by.firstname("martin").and.lastname("fowler")`, or
fully bare, `find_by.firstname.martin…`; the first call returns an **Expression Builder** and you compose with **Method Chaining**. **Removing quotes:**
with **Object Scoping**, capture the *next* unknown call as the value after a keyword method; **Textual Polishing (Ch. 45)** strips further punctuation.

**When to use it.** Two reasons it appeals: **it mimics real methods at a fraction of the effort**, a real saving when combinations are many; and
**punctuation consistency**, so users never wonder when to use dots vs. parens vs. quotes. **Fowler dissents on the second:** "I like separating what is
schema from what is data, so I prefer the way `find_by.firstname("martin")…` puts field names into method calls and the data into parameters." Weigh
alternatives first: attribute names as parameters, a closure predicate, a fragmentary external DSL in a string.

> "Above all… Dynamic Reception only pays its way when it allows you to build these structures **in general, without any special case handling**." *(Ch.
> 41, "When to Use It")*

Corollaries: worthwhile only where a **clear, mechanical translation** exists from the dynamic name to methods that already exist for other purposes;
and **"if you need to write special methods to handle particular cases of Dynamic Reception, that usually means you shouldn't be using Dynamic
Reception."**

**Costs and hard limits.** **Impossible in static languages.** **Debuggability** — "any mistake can lead you into deep debugging trouble. **Stack traces
often become impenetrable.**" **Encoding limits** — ASCII-only identifier grammars break on real data such as non-ASCII names. **Expressiveness limits**
— `...greater_than.2` fails because most dynamic languages disallow a digit there, and the workaround "obstructs much of the fluency that you're doing
it for." **Not for complex Boolean composition** — with nested likes, comparisons and negations "you're running down a road that forces you to implement
a kludgy parser in an environment not well-suited for it."

**The layering principle — the Active Record lesson.** The complexity ceiling is *not* an argument against simple cases: Active Record supports dynamic
finders for simple cases and deliberately refuses complex ones. "Some people don't like that, preferring a single mechanism, but I think it's good to
realize that **different solutions may work best at different complexities, so you should provide more than one.**" On the model side too, some
conditions come through the DSL and others through a closure-backed condition object.

**Containment techniques.** **Delegate unknown names upward** so genuinely unknown methods still produce the normal error; **validate arity and shape
yourself**, since you now own signature validation; **use the open-ended mechanism only where the vocabulary is open** (dynamic names for attributes and
values, ordinary methods for the fixed operator set); **scope the magic with per-section builders**, which "keep[s] each one simple and clearly scope[s]
what each builder is recognizing"; and use **two-stage evaluation for forward references**, storing bodies as closures so the Symbol Table is fully
populated first.

**The verdict worth memorizing:** **"once you start parsing sequences of method calls like this, you might as well just switch to an external DSL… The
desire to build up parse trees is a smell indicating that the internal DSL is doing too much work."** Overall: "**A mixture of techniques is often the
best bet.**"

**Relationships.** Usually combined with **Expression Builder**, **Method Chaining**, **Object Scoping**, **Symbol Table**, **Context Variable**;
**Textual Polishing** removes further punctuation; its failure mode points at **external DSLs**.

> **SDK lens:** The `__getattr__` / `method_missing` / JS `Proxy` pattern. (1) **Only use it when the mapping is fully general** — if you're writing `if
> name == "foo"` in the hook, define `foo`. (2) **Always delegate unhandled names to the default error path**; never silently return null or a no-op
> builder. (3) **Budget for debuggability** — impenetrable stack traces are the recurring cost, paid by every future user. (4) **Scope the magic**:
> per-section builders beat one god-object. (5) **Validate arity and shape yourself**, with errors naming the method and what was expected. (6) **Layer
> the API deliberately** — a magic path for the simple 80%, an explicit mechanism for the complex 20%. (7) **Data does not belong in identifiers** when
> it may be non-ASCII or contain digits.

---

## Annotation (Ch. 42)

> **Intent:** Data about program elements, such as classes and methods, which can be processed during compilation or execution. *(Ch. 42)*

**Concept.** Sometimes you want to classify *elements of the program itself*: annotations are "information about a program element" and "provide a
mechanism to extend the programming language." **The concept is broader than any special syntax.** The annotation-defining syntax *is* an internal DSL,
building a **Semantic Model** by attaching data to the language's own model of the program.

**Defining an annotation — four techniques**, in decreasing order of language support: (1) **purpose-designed syntax** (`@Test`, `[Test]`) with
parameters, most obvious and often easiest; (2) **class methods called in the class body**, "almost as easy as using purpose-designed syntax" — the call
must be given the **name of the element it annotates**, but that buys the ability to **separate annotations from the annotated declarations**, "a big
payoff for languages that make this easy" (gotchas: annotations must *execute* to be stored, and class-level storage is often shared with subclasses);
(3) a **marker interface** in static languages, which **only works on classes**; (4) **naming conventions** (early xUnit's `test` prefix), fine for
simple cases, but "multiple annotations are difficult to support and parameters are practically impossible." **A structural limit unique to
Annotations:** the model must decorate the program's own representation, so **"you can't practically build a completely separate and independent
Semantic Model."**

**Processing.** Runtime processing is the most common case (test runners, ORM mapping), and it can be **split across phases** — build validators once at
startup, run cheap checks many times. Runtime processing ≈ model execution; the alternative is **code generation**, awkward in compiled languages, which
need compiler hooks, pre-compilation generation ("such intimate intermixing of written and generated code can be confusing"), or bytecode
postprocessing. **One definition, many processors is the killer application:** validations enforced in the browser for responsiveness *and* on the
server because you can never trust the browser — "both checks can be fully derived from a single Annotation."

**When to use it.** "We are still learning when best to use them." The key property: **"Annotations… allow you to separate definition from
processing."** Enforcing a range inside the setter **fuses the constraint's definition with the moment it's enforced**; separating them lets you check
at different times, apply *different subsets* at different times, and read constraints standing alone. **Decision rule:** "the strength of Annotations
lies where it makes sense to separate definition and processing" — qualifying motivations are that *processing* should vary independently, or that the
*definition* should be understandable alone. **Downside:** you must "look in two disconnected places," and "the processing code is also generic, which
may make it even harder to follow."

> "The definition of an Annotation should be **declarative and not involve any logic flow**. Furthermore, it shouldn't imply any ties to when the
> processing logic occurs, or any ordering of processing Annotations attached to the same or different program elements." *(Ch. 42, "When to Use It")*

Three prohibitions in one sentence: no control flow in the declaration; no assumption about *when* the processor runs; no ordering dependency between
annotations. Violate any and you have built a trap that looks like a declaration. Two asides: self-validation isn't always right, because "you always
[validate] for a context, and that context is usually some action involving that object"; and **decouple annotation from processor** via dictionary
lookup rather than letting the annotation implement or name its check ("I generally prefer… to make annotations independent of the processing
mechanism"). When the Ruby example upgrades processing to generate methods, **"I don't need to modify the annotation calls"** — the declarative surface
is unchanged while processing improves underneath.

**Relationships.** Builds a **Semantic Model (Ch. 11)** constrained to decorate the program model; alternative to **explicit registration**; related to
**Symbol Table (Ch. 12)** and code generation.

> **SDK lens:** A design brief for **declarative metadata APIs** — decorators, attributes, schema classes, ORM field descriptors, serialization tags,
> validation decorators, DI annotations. **Annotation beats explicit registration** when definition and processing genuinely vary independently, or when
> the declaration should read in isolation next to what it describes; explicit registration wins when the reader needs *what happens* and *when* in one
> place. **Any decorator you ship must be purely declarative** — no control flow, no ordering dependencies, no coupling to when processing runs.
> **Decouple the annotation from its processor**: inert data plus a processor chosen from a registry. **The multi-target payoff is the strongest
> argument for a declarative API**: one declaration, N processors, no drift. And **accept the discoverability cost honestly** — readers must look in two
> places, so invest in docs and in error messages from the generic processing code.

---

## Parse Tree Manipulation (Ch. 43)

> **Intent:** Capture the parse tree of a code fragment to manipulate it with DSL processing code. *(Ch. 43)*

**Concept.** A closure gives you code to *execute* later; Parse Tree Manipulation lets you **examine and modify the code's structure**. Host-language
expressions become input data to your processor.

**Mechanics.** You need an environment that turns code into a workable parse tree — "a relatively rare programming language feature," rare in support
and rarer in use. Exemplars: **C# expression trees** (only an **expression inside a lambda**, so no multi-statement code), **Ruby's ParseTree**, and
**Lisp**, categorically different because its source *is* a serialized parse tree. **You can't accept arbitrary host-language expressions:** "it's
important to fail fast should you get an expression that you can't handle," since the tree may contain any legal construct and **all checking is
yours**. **Walk only what you must** — "usually you won't need, or want, to walk the entire parse tree": walk what populates the Semantic Model and hand
the rest back to the language to evaluate.

**When to use it.** The driving reason: **use a fuller range of host-language features "instead of the pidgin of the usual internal DSL constructs."**
The key distinction: you can always intermix host language with DSLish constructs, but "usually, you can only manipulate the executable **results** of
the host language — you can't dive into host language expressions and manipulate their structure." **Not many DSL use cases exist**; the best is LINQ —
Boolean expressions translated into **SQL**, i.e. source-to-source translation, useful "when your target language is not well known or you want multiple
targets." Tree *surgery* is possible, but "it's not clear how useful that kind of surgery is in a DSL context."

> "I also worry a bit that Parse Tree Manipulation is one of those techniques where **the intricacies of doing it may be just too appealing for many
> programmers. It's an appeal that can blindside people into missing other, simpler ways of achieving the same goal.**"

**Transferable ideas from the example.** A **"phantom" receiver object** exists purely so the compiler accepts and the IDE completes an expression you
intend to *inspect*: "the return values of its methods are irrelevant as they'll never actually be called." Clients "can't use *any* C#," only the
supported subset, and the walker throws on the rest. And **"don't parse what you can evaluate"** — compile and invoke the *value* side rather than
walking it, which "allows me to put any legal C# into the value side… without having to deal with it in my navigation code."

**One meta-lesson from "Stepping Back."** **He wouldn't build it this way** — plain **Method Chaining** needs a handful of methods plus one Context
Variable, and is simpler because "**the structure of the internal DSL is more similar to the IMAP query itself**"; the fancy version's only real
advantage "boils down to IDE support."

**Relationships.** Populates a **Semantic Model**; its main competitor is plain **Method Chaining** (+ Expression Builder + Context Variable); **Macro
(Ch. 15)** is the same idea by another route.

> **SDK lens:** The pattern behind LINQ-to-SQL, ORM expression translation, and any API that **inspects a lambda instead of calling it**. Your API
> accepts only a *subset* of the host language, so **fail loudly and specifically** outside it — silent mistranslation is far worse than an exception.
> **Design the surface to mirror the target, not the host**: the IMAP verdict is the lesson, with IDE support the only genuine advantage of the fancy
> version. **Evaluate what you don't need to inspect** — a clear boundary between structure you interpret and subexpressions you hand back massively
> shrinks what you support. And **beware technique-attraction**.

---

## Class Symbol Table (Ch. 44)

> **Intent:** Use a class and its fields to implement a symbol table in order to support type-aware autocompletion in a statically typed language. *(Ch.
> 44)*

**Concept.** Strings and built-in symbol types carry no type information, so the IDE can offer nothing when you type a DSL symbol name. Class Symbol
Table makes symbols **statically typed host-language entities** by declaring each as a **field in an Expression Builder**: the field name is the symbol
name, and its declared type says what the symbol can do.

**Mechanics.** **Put the DSL script inside a single Expression Builder class** (usually a subclass of a general builder): one method holding the script,
plus fields declaring the symbols. **Naming conventions get bent for readability** — a plural class name is unconventional, but "the readability of the
DSL is trumping my usual code style rules." **The runtime gap:** a field reference yields the field's **contents**, not its definition, so you must
**populate every field before the script executes**, from a constructor or build method, with the script in an instance method. Contents are usually
**small Expression Builders** linking to the model object and carrying the field name (field name = key, builder = value; occasional lookup by name is
why builders keep their name). **Reflection is the price**, since builders must refer to each other: "usually there's not too much of it and, provided
it's well encapsulated, it shouldn't make the language too difficult to process." Three further lessons: **intermediate builders decouple declaration
order**; builders **notify without knowing** what the recipient will do with the fact; and **only script-visible types pay the readability tax**, so
types the DSL author never writes keep conventional names.

**When to use it.** **Benefit:** full static typing of all DSL elements — type-aware autocompletion above all, plus compile-time checking, "which
matters a lot to many people (but rather less to me)." **Scope limit:** "much less useful if you don't have an IDE that takes advantage of static types.
It also does not bring much benefit in a dynamically typed language." **Cost:** "you have to bend your DSL significantly to fit within the type system.
The resulting builder classes look very odd," and scripts must live where they can exploit the facilities, "such as all in the same class." **The
tradeoff statement:** "the fundamental tradeoff is between the restrictions on the DSL script and the benefits of the IDE support." **Cheaper
alternative:** "you can often get what you need by using **enums as symbols**." **Verdict:** the tricky code is "usually a worthwhile tradeoff."

**Relationships.** A specialization of **Symbol Table (Ch. 12)**; requires **Expression Builder**; often combined with **Object Scoping**; cheaper
alternative, enums as symbols.

> **SDK lens:** The general technique is **turning stringly-typed identifiers into typed program elements so tooling can see them** — enums instead of
> string constants, typed key objects, literal-union types, generated stubs, typed schema classes. All are the same trade: declaration ceremony for
> autocompletion, compile-time checking, rename refactoring, go-to-definition. **Reuse the tradeoff statement directly:** restrictions on how users
> write code vs. tooling benefits. If users have no IDE exploiting static types, or the language is dynamic, the benefits evaporate and the restrictions
> remain — don't pay. **Reach for the cheap version first** (enums, literal unions), **confine ugliness to the implementation**, and **break naming
> conventions only on the types the user actually types**.

---

## Textual Polishing (Ch. 45)

> **Intent:** Perform simple textual substitutions before more serious processing. *(Ch. 45)* Sketch: `3 hours ago` → `3.hours.ago`

**Concept.** Internal DSLs are littered with host-language artifacts (dots, colons, parens, quotes) that nonprogrammers find awkward. Textual Polishing
runs **regex substitutions** over the script *before* it reaches the evaluator, turning a domain-expert-friendly surface into a valid internal-DSL
expression.

**Mechanics.** **The output of polishing is an expression in an internal DSL** — host-language code, not a model. Specification is easy, correctness is
not: "the tricky thing… is getting the regular expressions correct so you don't get unwanted substitutions"; a space inside a quoted string must not
become a dot, "but that makes the regex much harder to write," and every regex needs boundary expressions at both ends. **Most natural in dynamic
languages**, where polished text is evaluated at runtime; static languages must polish before compiling, adding a build step. Occasionally useful before
lexing an external DSL (semantic indentation). Conceptually "a simple application of textual **Macros**, with all the corresponding problems."

**When to use it.** Fowler argues himself out of the pattern: "if you use a little, it doesn't help much, and if you use a lot, it gets very
complicated, so it may then be better to use an external DSL." **The hard structural limit:** it "cannot do anything to change the syntactic structure
of the input, so you are still tied to the basic syntactic structure of the host language" — re-skin, not re-shape. **Keep the two forms recognizably
similar:** the resulting internal DSL "should be as clear as possible for programmers to read — the polishing is only a visual convenience for
nonprogrammers," or debugging becomes guesswork. **A cheaper alternative — fix it in the editor, not the language:** syntax coloring that fades noise
characters into the background. **Escalation rule:** "if you find yourself doing a lot of polishing… explore using an external DSL instead," since a
parser is easier to maintain "than the sequence of polishing steps." What the example does *first*: **Object Scoping removes noise for free** (dropping
the receiver prefix and **moving the Method Chaining finishing call into the processing code**, out of the user-visible DSL), and **adjusting the DSL's
own vocabulary** — rename a method rather than substitute, which "makes it easier to see the correspondence between the polished text and the resulting
DSL."

**Relationships.** A degenerate form of **Macro (Ch. 15)**; frequently paired with **Object Scoping**, which removes noise without any substitution —
always try that first; its escalation path is an **external DSL** with a parser.

> **SDK lens:** Mostly cautionary. **Prefer structural fixes to textual ones** — Object Scoping and renaming achieved most of the goal with none of the
> regex risk. **Hide terminator calls from users** where you can, moving `.build()` into the harness. **Don't let the user-facing surface and the
> underlying calls diverge**, or you destroy every error message, stack trace, and debugging session downstream — the problem with heavy source
> rewriting, transpilation, and macro-based APIs. And **solve cosmetic complaints with tooling** rather than by adding a translation layer.

---

## Literal Extension (Ch. 46)

> **Intent:** Add methods to program literals. *(Ch. 46)* Sketch: `42.grams.flour`

**Concept.** Literals make a natural *starting point* for DSL expressions (`42.grams`, `3.days.ago`), and C# **extension methods** or Ruby **open
classes** let you **start a method chain with a literal**.

**Mechanics.** A key decision is **whether to use an Expression Builder**: without one, every intermediate type in the chain must carry the fluent
methods; with one, you must be able to get cleanly from the builder back to the underlying object. **What should `42.grams` return?** (1) **A number**
in a canonical unit — **danger: "type transmogrification"** (Neal Ford's term), where an integer becomes a float and every later method must be defined
on *multiple* numeric types. (2) **A quantity object** (magnitude plus unit): "I much prefer quantities to simple numbers for representing dimensioned
values," since they express intent and enable useful behavior such as "alerting me to problems with `42.grams + 35.cm`" — encapsulating the magnitude
makes transmogrification largely disappear, at the cost that the quantity class now carries DSL methods. (3) **An Expression Builder** — full control
over the rest of the expression, but calling code must unpack the subject: fine inside a scoped block, a problem for arithmetic like `42.grams + 3.oz`.
"I tend to prefer an Expression Builder most of the time, but it really depends on the context of its use."

**When to use it.** **Sceptical framing:** it helps fluency, "although there's also **the suspicion that some of this enthusiasm is fondness of a new
toy**." **The real cost is global interface pollution:** these extensions "are only needed in some contexts, so if they appear in more contexts they can
make a class's interface much more confusing." **The mitigation is namespace scoping**, where the environment allows it, so the method "will only show
up if I'm in the right namespace." **Keep DSL vocabulary off general-purpose types:** Fowler wrote `Quantity` himself and still refuses to put the DSL's
`Of` method on it — "**`Of` is part of a DSL for a limited purpose, while the quantity class can be used as part of a general library.**"

**Relationships.** Typically the entry point into **Method Chaining**; may or may not use **Expression Builder**; resolves names via **Symbol Table (Ch.
12)**.

> **SDK lens:** **Monkey-patching / extension-method design**, and the rule is namespace or module scoping: extensions to types you don't own should be
> opt-in and locally scoped, never globally visible — a library adding methods to the integer type imposes its vocabulary on the whole program. **Keep
> DSL-specific fluent methods off general-purpose types**: don't bolt your framework's vocabulary onto shared domain classes. **Watch the return type of
> every chain step** — transmogrification forces you to define your vocabulary on every type it passes through, so a purpose-built wrapper that stays
> stable is almost always better. And **fluency is not free**: a technique's availability and elegance are not reasons to adopt it.

---

## The judgement calls, collected

1. **Keep the magic proportional to the benefit.** Dynamic Reception's fluency is paid for in impenetrable stack traces *(Ch. 41)*; Parse Tree
   Manipulation's power in a walker that must reject most of the host language *(Ch. 43)*; Class Symbol Table's autocompletion in reflective setup and a
   contorted script layout *(Ch. 44)*. In every case Fowler states the exchange rate explicitly and refuses the trade when the benefit is thin.
2. **Use the open-ended mechanism only where the vocabulary is genuinely open.** Dynamic dispatch for attribute names and values; ordinary declared
   methods for the fixed operator set *(Ch. 41)*.
3. **Layer the API by complexity; don't stretch one mechanism to cover everything.** "Different solutions may work best at different complexities, so
   you should provide more than one" *(Ch. 41, "When to Use It")*.
4. **When a technique starts requiring special cases, you've outgrown it.** Special-cased Dynamic Reception means don't use Dynamic Reception *(Ch.
   41)*. A growing pile of polishing regexes means write a parser *(Ch. 45)*. A desire to build parse trees out of chained calls "is a smell indicating
   that the internal DSL is doing too much work" *(Ch. 41)*.
5. **Mix techniques; don't chase purity.** Greenspun form *(Ch. 40)* and the fully symbol-free state machine *(Ch. 41)* both show that maximizing one
   technique produces a worse language than a judicious blend. "A mixture of techniques is often the best bet."
6. **Discoverability vs. expressiveness is the recurring axis.** Literal Map is expressive but its keys are invisible and unvalidated *(Ch. 40)*; Class
   Symbol Table sacrifices expressiveness and layout freedom to buy discoverability *(Ch. 44)*; Literal Extension buys fluency at the cost of polluting
   a widely-used interface *(Ch. 46)*.
7. **Shape the DSL like its domain or target, not like the host language's flashiest feature.** The IMAP comparison is the cleanest demonstration: the
   Method-Chaining version won because it mirrored IMAP's own query language *(Ch. 43)*.
8. **Separate definition from processing when — and only when — they should vary independently** *(Ch. 42)*, with the corollary discipline that
   declarations must be purely declarative: no logic flow, no ordering dependencies, no implied coupling to when processing runs.
9. **Explanation order is not construction order** *(Ch. 43, "Stepping Back")*. Build feature by feature, refactoring as you go; present the result
   decomposed by concern.
10. **Solve cosmetic problems with tooling before adding machinery** *(Ch. 45)*.
