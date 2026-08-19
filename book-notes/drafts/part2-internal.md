# Part 2 — The Pattern Catalog I: Foundations and Fluent APIs

## 9. Foundational patterns every DSL (and SDK) needs

Fowler's Part II collects the six patterns that apply regardless of whether your language is
internal (written in a host programming language) or external (with its own parser). They are
foundational in a strong sense: the rest of the catalog is largely defined *in terms of* them.
One pattern — Semantic Model — is the hub, and the other five describe how you populate it, how
you track your position while populating it, how you reconcile immutability with gradual
discovery, how you report what went wrong, and one technique (Macro) you should mostly avoid.

If you read nothing else in this part, read the Semantic Model section. It contains the single
most transferable piece of API-design advice in the book.

---

### Semantic Model (Ch. 11)

> **Intent:** "The model that's populated by a DSL." *(Ch. 11, intent line)*

#### The concept, from scratch

Imagine you are building a tool that configures state machines. You could write a parser that
reads a configuration file and, as it reads each line, directly performs the effect — opening a
door, wiring up a callback, emitting code. Most people's first instinct is exactly this: the
parser *is* the program.

Semantic Model says: don't do that. Instead, build an ordinary in-memory object model of the
*same subject matter* the language describes. If your language describes state machines, build
classes for `State`, `Event`, `Transition`. A particular script then corresponds to a particular
**population** of that schema — one `Event` object per event declared, one `State` per state, and
so on. The script is data; the model is the thing that actually knows what a state machine *is*.

The framing sentence worth memorizing: the Semantic Model is **"the library or framework that the
DSL populates"** *(Ch. 11, "How It Works")*. The DSL is not the thing. The DSL is a *front end*
for populating something that could exist perfectly well without it.

The representation is not required to be an in-memory object model. It could be a plain data
structure with behavior supplied by functions over that data. It need not even be in memory — a
DSL could populate a model held in a relational database. Fowler uses in-memory object models
throughout the book because that is what he knows best, not because the pattern requires it
*(Ch. 11, "How It Works")*.

#### The decisive design rule: usable without the DSL

> The Semantic Model **should be usable without a DSL present.** You should be able to populate it
> through an ordinary command-query interface. *(Ch. 11, "How It Works")*

This is the constraint that keeps the pattern honest, and Fowler gives two reasons. First, it
ensures the Semantic Model fully captures the semantics of the subject area — if some concept can
only be expressed by going through the parser, that concept lives in the parser, and the model is
incomplete. Second, it makes the model and the parser **independently testable**: you test
semantics by populating the model directly and asserting on its behavior; you test the parser by
asserting that it produced the right population.

If populating the model requires going through the DSL, you have smeared semantics into your
parser and lost the whole benefit.

Fowler gives a behavioral test for whether you have really achieved this *(Ch. 32, "How It
Works")*: you should be able to write tests for the Semantic Model that use no DSL at all. He
immediately tempers it — the point of an internal DSL is to make these objects *easier* to work
with, so most tests will naturally use the DSL — "But I'd usually include at least some tests that
only use the command-query interface."

#### The two interfaces

It is usually helpful to think of the Semantic Model as having **two distinct interfaces**
*(Ch. 11, "How It Works")*:

1. **Operational interface** — what clients use to *do work with* an already-populated model. It
   assumes the model has been created and makes it easy for the rest of the system to take
   advantage of it.
2. **Population interface** — what the DSL/parser uses to *create instances* of the model's
   classes. Used only by the parser(s) and by the model's own test code.

The population interface also acts as a **decoupling seam**. There is always *some* dependency —
the parser obviously has to see the Semantic Model in order to populate it — but by making the
population interface an explicit, deliberately designed boundary, an implementation change inside
the Semantic Model is much less likely to force a change in the parser. Fowler reports exactly
this payoff in the book's introductory example: he refactored the state machine model's internals
without touching the parsing code, because the changes did not alter the population interface
*(Ch. 11, "The Introductory Example (Java)")*.

#### The "pretend the model is magically already there" trick

This is the API design move that carries furthest beyond DSLs, and Fowler presents it as a general
rule of thumb for *any* objects, not just DSL-ish ones:

> **Assume the model is magically already there, then ask yourself how you would use it.**

Define the operational interface *first*, even though at runtime the population interface
necessarily executes first. Fowler acknowledges this is counterintuitive but insists it produces
better designs *(Ch. 11, "How It Works")*.

The reason it works is that construction concerns are seductive and dominant. If you design
construction first, every subsequent decision is shaped by "how do I get the values in?" — which
is a question your users mostly don't care about. Designing usage first forces you to answer "what
does the caller want to ask this thing?", which is the question that determines whether the
abstraction is any good.

#### Semantic Model vs. Domain Model

The Semantic Model is similar to a Domain Model *[PoEAA]*, but Fowler deliberately uses a separate
term, for four reasons *(Ch. 11, "How It Works")*:

- Semantic Models are often *subsets* of Domain Models, but don't have to be.
- "Domain Model" implies a behaviorally rich object model; a Semantic Model **may be data alone**.
- A Domain Model captures the core behavior of an application; a Semantic Model may play only a
  supporting role.
- The worked distinction: a DSL that describes object-relational mappings produces a Semantic Model
  consisting of the *Data Mappers* — **not** the Domain Model that is the subject of the mapping.

That last one is the clarifying case. The thing your language talks *about* and the thing your
language *builds* are different objects.

#### Semantic Model vs. syntax tree / AST

This distinction is the crux of the pattern *(Ch. 11, "How It Works")*:

- A **syntax tree corresponds to the structure of the DSL script.** Even an *abstract* syntax tree,
  which simplifies and reorganizes the input somewhat, still takes fundamentally the same form as
  the input.
- A **Semantic Model is based on what will be done with the information** in the script. It often
  has a substantially different structure, and is usually **not a tree at all** — graphs with
  cross-references are common. A state machine's transitions point at *shared* state and event
  objects; a tree cannot express that sharing.

Occasionally an AST *is* an effective Semantic Model, but "these are the exception rather than the
rule."

Fowler notes that traditional parsing/compiler literature doesn't use the term, and diagnoses why:
for a general-purpose language, a syntax tree is a perfectly suitable basis for code generation, so
there is less pressure to build something different. Compiler people *do* occasionally build one —
a call-graph representation is very useful for optimization — and they call these **intermediate
representations**.

#### Where the model comes from

Two common origin stories *(Ch. 11, "How It Works")*:

- **The model precedes the DSL.** You already have a Domain Model and decide that some portion of
  it would be better populated from a DSL than through the regular command-query interface. The DSL
  is layered on top.
- **The model and the DSL are built together**, with discussions with domain experts refining both
  the expressions of the language and the structure of the model. Each informs the other.

#### Execution: interpreter style vs. compiler style

The Semantic Model can either **hold the code to execute itself** (interpreter style) or **be the
basis for code generation** (compiler style). Even when generating code, Fowler recommends *also*
providing interpretation — it helps enormously with testing and debugging, and lets you use the
Semantic Model as a **simulator for the generated code** *(Ch. 11, "How It Works")*.

Because the code generator works off the Semantic Model rather than off the parser, multiple code
generators become cheap: independence from the parser avoids duplicating parser logic across
generators.

#### Validation belongs in the model

The Semantic Model is "usually the best place for validation behavior, since you have all the
information and structures in place to express and run the validations" *(Ch. 11, "How It Works")*.
Crucially: run validations *before* either running the interpreter or generating code.

In the introductory state-machine example the validations were things like: no unreachable states,
no states you can't get out of, all events and commands actually used in the definitions of states
and transitions *(Ch. 11, "The Introductory Example (Java)")*. Note that none of these are
*syntactic* — you cannot express them as grammar rules, and you cannot check them one line at a
time. They are properties of the whole populated graph, which is exactly why they belong to the
model and not the parser.

This is also where **Notification (Ch. 16)** joins the picture: validations over a populated model
naturally want to report *all* problems at once rather than aborting on the first.

#### Computational vs. compositional DSLs

Fowler cites Brad Cross's distinction *[cross-comps]* and observes that it is really a distinction
about the *kind of Semantic Model* produced *(Ch. 11, "How It Works")*:

- **Compositional DSL** — describes some composite structure in textual form. XAML describing a UI
  layout is the example; the primary form of the Semantic Model is *how the various elements are
  composed*.
- **Computational DSL** — the Semantic Model "feels more like code than data" and drives
  computation, usually with an alternative computational model instead of the usual imperative one.
  The Semantic Model here is usually an **Adaptive Model**. The state machine is of this kind.

The tradeoff he flags: "You can do a lot more with a computational DSL, but people often find them
more difficult to work with."

This distinction is worth carrying into SDK work directly. A configuration API that assembles a
structure (a pipeline, a schema, a UI tree) is compositional; its model is mostly data and its main
job is composition rules. An API that lets users express *behavior* (rules, policies, predicates,
retry strategies) is computational; its model holds executable fragments and its main job is
evaluation. The second is more powerful and materially harder for users.

#### When to use it — and when not to

Fowler's answer is essentially *always*, and he is self-aware about it: he notes he's uncomfortable
saying "always" because absolute advice is usually a sign of closed-minded thinking, but he can see
very few cases where you wouldn't want one, and those are all very simple situations *(Ch. 11,
"When to Use It")*.

**Arguments for:**

1. **Separate testing of semantics and parsing.** Test semantics against the model directly; test
   the parser by checking it populates the model with the right objects.
2. **Multiple parsers become tractable.** With more than one parser, you can check they're
   semantically equivalent by comparing the populations they produce. Fowler had exactly this
   requirement in the book's introductory example — multiple internal *and* external DSLs over one
   model — and the Semantic Model let him add a new DSL+parser without duplicating code in the
   other parsers or altering the model.
3. **Independent evolution.** More common than multiple DSLs is simply evolving the DSL separately
   from the Semantic Model, and vice versa.
4. **Flexibility in execution.** Direct interpretation, code generation off the model, both at once
   (model-as-simulator), multiple code generators, plus non-execution outputs like visualizations.
5. **The most important reason, in his words:** it "separates thinking about semantics from
   thinking about parsing. Even a simple DSL contains enough complexity to justify dividing it up
   into two simpler problems."

**The exceptions he envisages** *(Ch. 11, "When to Use It")*:

- **Simple imperative interpretation** — you just execute each statement as you parse it. A
  calculator evaluating arithmetic expressions is the canonical case.
- **When the AST already *is* the model.** For arithmetic expressions, even if you don't interpret
  immediately, the AST is pretty much what a Semantic Model would be anyway. Generalized rule:
  *if you can't think of a more useful model than the AST, there's little point creating a separate
  Semantic Model.*
- **Code generation directly off the AST** — the most common real-world case where people skip the
  pattern. Reasonable *provided* the AST is a good model of the underlying semantics **and** you
  don't mind coupling code generation to the AST. If either condition fails, it's often simpler to
  transform the AST into a Semantic Model and do a simpler code generation from that.

**His stated bias:** always *start* by assuming you need a Semantic Model. Even if thinking it
through convinces you one isn't necessary, stay alert to increasing complexity and put one in as
soon as any complication starts creeping into the parsing logic.

**Honest caveat:** Semantic Model is not part of DSL culture in the functional programming world.
The FP community has a long history of DSL thinking, and Fowler admits his experience with modern
functional languages is "no more than occasional experimentation," so he explicitly declines to
claim his inclination applies there.

#### Relationships

- **Symbol Table (Ch. 12)** — its values are usually Semantic Model objects (or builders that will
  produce them); it is how a script's textual identifiers resolve to model objects.
- **Construction Builder (Ch. 14)** — needed when the model's objects are immutable but the parse
  gathers their field values gradually.
- **Context Variable (Ch. 13)** — the "current item" during a parse is typically a model object or a
  builder for one.
- **Notification (Ch. 16)** — the reporting vehicle for validations run over a populated model.
- **Expression Builder (Ch. 32)** — the fluent front end that populates the model; explicitly *not*
  part of the model.
- **Adaptive Model** — the usual form of the Semantic Model for a computational DSL.

> **SDK lens:** This is the most important idea in the book for library authors, and it holds even
> when no DSL is involved. Design a core model that is fully usable and testable through an
> ordinary programmatic interface, and treat *every* other surface — fluent builder, YAML loader,
> CLI, config decorator, code generator — as a second-class front end that merely populates it.
> Everything a front end can express must be expressible directly. This is the same discipline as
> "the CLI is a client of the library, not the other way around." Three concrete practices follow:
> (1) design the operational interface first by pretending the object already exists and writing
> the usage code before the construction code; (2) make the population/construction interface an
> explicit, narrow boundary so internal refactoring doesn't ripple into every loader and adapter;
> (3) put validation in the model, not in the loader, so it applies uniformly regardless of which
> front end produced the object. And treat multiple front ends as a design *test*: if two very
> different surface syntaxes can both populate the model and produce equivalent populations, the
> model is probably factored at the right level.

---

### Symbol Table (Ch. 12)

> **Intent:** "A location to store all identifiable objects during a parse to resolve references."
> *(Ch. 12, intent line)*

#### The concept

Many languages need to refer to the same object at several points in a script. If a DSL defines
tasks and their dependencies, one task's definition must be able to *name* other tasks. So you
invent some form of **symbol** for each task, and while processing the script you put those symbols
into a table that stores the link between the symbol and the underlying object holding the full
information.

The essential purpose is to **map between the symbol used in the DSL script and the object it
refers to** *(Ch. 12, "How It Works")*. That maps naturally onto a dictionary, and the most common
implementation is exactly that: a map with the symbol as key and the **Semantic Model** object as
value.

#### Choice of key type

For many languages the obvious choice is a string, because the text of the DSL *is* a string. The
main reason to use something else is a language with a genuine **symbol data type** *(Ch. 12, "How
It Works")*:

- Symbols are structurally like strings (a sequence of characters) but differ in behavior — many
  string operations (concatenation, substrings) make no sense for a symbol.
- A symbol's principal task is *lookup*, and symbol types are designed with that in mind. Two
  occurrences of `"foo"` are often distinct objects compared by content; two occurrences of a symbol
  literal always resolve to the *same* object and compare much faster.
- Performance can justify symbols, but for small DSLs it may not matter much. **The big reason is
  intent communication**: declaring something as a symbol states clearly what you're using it for.
- Symbol literal syntax also makes symbols visually stand out in an internal DSL — a further reason
  to use them.

#### Choice of value type

Values can be either **final model objects** or **intermediate builders**. Model objects make the
Symbol Table act as *result data*, which is good for simple situations. Putting a **builder** as
the value gives more flexibility at the cost of a bit more work *(Ch. 12, "How It Works")*.

#### One map, several maps, or a special class?

Many languages have different *kinds* of thing to refer to — the book's state machine has states,
commands, and events *(Ch. 12, "How It Works")*:

- **Single map for everything.** All lookups share one map. Immediate consequence: you can't use the
  same symbol name for different kinds of things. That may be a *useful* constraint for reducing
  confusion in the DSL. But it makes the processing code harder to read, because it's less clear
  what kind of thing you're manipulating. **Fowler does not recommend this.**
- **Multiple maps** — one per kind of object. You can think of this as one logical Symbol Table or
  three separate ones. **This is Fowler's preference**, because the processing code now makes clear
  which kind of object is being referred to at each step.
- **A special class** — a single Symbol Table object with kind-specific methods (`getEvent(code)`,
  `registerEvent(code, event)`). Sometimes useful, and gives a natural home for symbol-processing
  behavior. Most of the time Fowler doesn't find a compelling need for it.

#### Forward references

Objects referred to before they are properly defined. DSLs usually *don't* have strict
declare-before-use rules, so forward references often make sense. If you allow them, **any
reference to a symbol must populate the entry in the symbol table if it isn't already there**
*(Ch. 12, "How It Works")*. The mechanic is a `register(name)` helper that **creates the object
lazily if the name isn't in the map yet**, called for both sides of every reference — so the table
is both populated by and consulted by the same code path.

This will often push you toward using builders as values, unless the model objects are very
flexible about being filled in later.

#### Misspelled symbols

If there's no explicit declaration of symbols, misspellings become a frustrating error source — a
typo silently creates a new, unrelated entity. If there's any way to detect misspelled symbols, put
that checking in; it "will prevent a lot of hair-pulling" *(Ch. 12, "How It Works")*. This is one
reason to *require* that all symbols be declared in some way. Note that requiring declaration does
**not** mean requiring declaration *before* usage.

#### Nested scopes

Symbols defined only within a subset of the program. Very common in general-purpose languages,
"much rarer in simpler DSLs." If you need it, use *Symbol Table for Nested Scopes* *[parr-LIP]*.

#### Statically typed symbols

In a statically typed host language you can trivially use a hashmap with string keys and it works,
but Fowler lists four concrete disadvantages *(Ch. 12, "Statically Typed Symbols")*:

1. Strings introduce **syntactic noise** — you have to quote everything.
2. The compiler **can't type check.** Misspelled names surface only at runtime; and with several
   *kinds* of identified object, the compiler can't tell you when you've referred to the wrong kind.
3. **No IDE autocompletion** on strings — you lose a powerful element of programming assistance.
4. **Automated refactorings** may not work well with strings.

The fix is some kind of statically typed symbol. **Enums** are the simple good choice; a **Class
Symbol Table (Ch. 44)** is the other, heavier one.

Fowler is candid that he isn't enthusiastic about static typing *for finding errors* — he thinks it
catches few errors that decent testing wouldn't — but he values it for **IDE support**: type
Control-Space and get the list of all symbols valid at that point *(Ch. 12, "Enums as Statically
Typed Symbols (Java)")*.

Three judgement calls from the enum example worth keeping:

- Enums "don't force inheritance or constraints on where you can write DSL script code — an
  advantage compared to a *Class Symbol Table*."
- If the set of symbols must correspond to some **external data source**, write a build step that
  reads that source and **code-generates the enum declarations**, keeping everything in sync
  *[kabanov-hunger]*.
- A single enum implies a **single namespace of symbols**. Fine when many little scripts share one
  symbol set; not fine when different scripts want different sets. The fix: define the builder in
  terms of an **interface**, have several enums implement it, then selectively import only the group
  you need so the IDE offers only relevant symbols.

#### When to use it

Short and decisive: "Symbol Tables are common to any language-processing exercise, and I expect
you'll almost always need to use them" *(Ch. 12, "When to Use It")*.

The times they aren't strictly necessary: with Tree Construction you can always delve around in the
syntax tree to find things, and often a search on the Semantic Model you're building could do the
job. "But sometimes you need an intermediate store, and even when you don't, it often makes life
easier."

#### Relationships

- **Semantic Model (Ch. 11)** — the usual value type.
- **Construction Builder (Ch. 14)** — the alternative value type, and what makes forward references
  practical.
- **Class Symbol Table (Ch. 44)** — the statically-typed, IDE-oriented specialization.
- **Literal Extension (Ch. 46)** — its substance registry is a Symbol Table with lazy creation.

> **SDK lens:** The string-key critique is a general API critique, not a DSL-specific one. Any
> string-keyed lookup surface — feature flags, metric names, event types, config paths, resource
> identifiers — costs you compile-time checking, autocompletion, and safe rename refactoring. Enums,
> sealed types, literal-union types, or generated constant modules are the fix, and
> **code-generating those constants from the authoritative external source** is how you keep them
> honest as the source changes. Two more directly reusable mechanics: **lazy create-on-reference**
> in a registry is the standard technique for accepting declarations in any order (essential for
> config loaders and dependency registries), and **namespace scoping via interfaces plus selective
> imports** is a low-tech way to give one shared builder several disjoint vocabularies without
> reaching for generics. Finally: if your API accepts free-form identifiers with no declaration
> step, add misspelling detection, because a typo that silently creates a new entity is one of the
> most expensive bug classes you can ship.

---

### Context Variable (Ch. 13)

> **Intent:** "Use a variable to hold context required during a parse." *(Ch. 13, intent line)*

#### The concept

You are parsing a list of items, capturing data about each. Each individual piece of information can
be captured independently, but you also need to know **which item** you're currently capturing
information for. A Context Variable holds the current item in a variable and reassigns it as you
move to a new one.

The sketch is an INI-style file: a `[section]` header assigns `currentProject = new Project(...)`,
and the following `name = …` / `lead = …` lines all operate on `currentProject` *(Ch. 13, sketch)*.

That's the whole mechanism. You have a Context Variable whenever you have a variable named something
like `currentItem` that you update periodically during a parse. The pattern exists mainly to *name*
this thing so its costs can be discussed.

#### What goes in it

A Context Variable can hold either a **Semantic Model object** or a **builder**. A Semantic Model
object is superficially more straightforward, but only if *all* of its properties are mutable at the
moments the parse needs to change them. If they're not, it's usually best to use a builder to gather
the information and create the model object at the end — i.e. a **Construction Builder (Ch. 14)**
*(Ch. 13, "How It Works")*.

#### When to use it — mostly a warning

This chapter is unusual in that its "when to use it" is largely a caution *(Ch. 13, "When to Use
It")*:

- There are many places where you must keep context during a parse, and a Context Variable is the
  obvious choice. It's easy to create and easy to get going with.
- **But they are problematic, particularly as you get more of them.** "By their nature, they are
  mutable state that has to be kept track of, and bugs adore this kind of mutable state." It is easy
  to forget to update the variable at the right moment, and debugging that is difficult.
- There are usually **alternative ways of organizing the parse that reduce the need for Context
  Variables** — in practice: nested closures or nested functions that carry the current object as an
  argument or in lexical scope, or delegating a sub-block to a sub-parser object that owns its own
  item.
- His position: **"While I don't say that any Context Variable is evil, I do prefer to use techniques
  that don't need them."**

The concrete cost is visible in the Function Sequence example *(Ch. 33)*: a `speed()` clause that
could mean processor speed or disk speed must branch on which context variable is currently set, and
throw if neither is. Clause-name resolution degrades from a compile-time question into a runtime
state inspection.

Two smaller lessons from the INI example *(Ch. 13, "Reading an INI File (C#)")*. First, on format
choice: INI can seem old-fashioned, but it remains a lightweight, readable way to handle a **simple
list of items with properties**. XML and YAML handle more complex structures, "but at a cost of
readability and parsing difficulty. If your needs are simple enough for an INI file, it remains a
reasonable choice." Second, the example assigns properties by **reflection** on the property name
rather than a hand-written switch, with the tradeoff stated plainly: "Using reflection makes the code
more complex, but it does mean that I don't need to update the parser when I add more properties to
the Semantic Model."

#### Relationships

- **Construction Builder (Ch. 14)** — the alternative content when the model object isn't freely
  mutable during the parse.
- **Function Sequence (Ch. 33)** — the technique that *forces* Context Variables.
- **Nested Function (Ch. 34)** — eliminates them by passing data through return values.
- **Nested Closure (Ch. 38)** — tames them by scoping their lifetime to a closure invocation.
- **Delimiter-Directed Translation (Ch. 17)** — the parsing style that most often needs them,
  because line-at-a-time parsing has no natural nesting to carry context.

> **SDK lens:** This is the classic critique of **stateful, order-dependent "current object" APIs** —
> `setCurrentX()` followed by a sequence of mutators, or a builder with a `currentThing` field that
> every clause consults. They are easy to write and easy to get wrong: order-dependence,
> thread-safety hazards, ambiguous method names that must dispatch on state, and errors that surface
> at runtime instead of at the call site. Prefer passing the target explicitly, or scoping it with a
> block/closure/context manager so the "current" thing is lexically obvious and cannot leak past its
> region. When you find yourself adding a second context variable to a builder, that is the signal to
> switch to child builders or a block-scoped API.

---

### Construction Builder (Ch. 14)

> **Intent:** "Incrementally create an immutable object with a builder that stores constructor
> arguments in fields." *(Ch. 14, intent line)*

#### The concept

You want the product object to be **immutable**, but you can only discover its field values
**gradually**. Construction Builder resolves that tension: a mutable scratch object accumulates the
values, then hands you a fully-formed immutable product in one shot.

Immutability is a property of the **finished object**, not a constraint on the **construction
process**. That single sentence is the whole pattern.

#### How it works

The recipe is deliberately simple *(Ch. 14, "How It Works")*:

1. Take each of the product's constructor arguments and **make a mutable field for each** on the
   builder.
2. Add further fields for any other attributes of the product you're collecting.
3. Add a method that **creates and returns a new product object** assembled from all the data in the
   builder.

**Optional lifecycle controls** worth adding:

- Check whether you have enough information to create the product before allowing creation.
- Set a flag once you've returned a product, to prevent returning it again — or stash the created
  product in a field.
- Raise an error if someone tries to add attributes to the builder *after* the product was created.

**Composition:** multiple Construction Builders can be combined into deeper structures, so they
produce a *group of related objects* rather than a single object. The example does exactly this — a
flight builder owns a list of leg builders, and the top-level materialization cascades down,
converting each leg builder to an immutable leg on the way *(Ch. 14, "Building Simple Flight Data
(C#)")*.

#### When to use it

Use it whenever you need to create an object with **multiple immutable fields** whose values you
gather **gradually**. The builder gives you "a coherent place to put all this data before you
actually create the product" *(Ch. 14, "When to Use It")*.

**Alternatives Fowler considers and rejects:**

- **Local variables or loose fields.** Capture the pieces in locals until you can call the
  constructor. Fine for one or two products, "but soon gets confusing if you need to create a bunch
  of objects at once, such as when you're parsing." A parse is exactly the case where many half-built
  objects are alive simultaneously.
- **Copy-on-write on the real model object.** Create an actual model object and, each time you learn
  one more immutable attribute, create a new copy with that attribute changed. This saves writing a
  builder but is "generally more awkward to do and follow." The killer objection: **it doesn't work
  if you have multiple references to the object** — you have to chase down and replace every
  reference. This is precisely why it fails for graph-shaped Semantic Models with cross-references.

**The scope limit, stated plainly:** "you only need it when you have immutable fields. If that's not
the case, then just create your product objects directly." Don't reach for a builder reflexively.

#### Construction Builder ≠ Expression Builder

Fowler is emphatic that despite the shared word "builder" these are **different patterns**
*(Ch. 14, "When to Use It")*:

- **Construction Builder** is *purely* about gradually building up constructor arguments. It makes
  **no attempt to provide a fluent interface.**
- **Expression Builder (Ch. 32)** is focused on providing a **fluent interface** — it exists to shape
  the *reading experience* of the DSL.

It is not unusual to find a single object that is both, "but that doesn't mean they are the same
concept."

This separation matters more than it first appears. *Staged construction* and *fluent surface syntax*
are orthogonal design decisions that happen to be frequently combined. Conflating them produces two
failure modes: builders that exist purely for fluency even though the product is mutable (pure
ceremony), and builders whose fluent method names have been contorted to also serve as the
construction API (two jobs, both done badly). Ask separately: *does the product have immutable fields
gathered over time?* (Construction Builder) and *do I want the call site to read as a sentence?*
(Expression Builder).

#### Relationships

- **Semantic Model (Ch. 11)** — the product is typically a model object; the builder is population
  machinery.
- **Symbol Table (Ch. 12)** — putting builders rather than final model objects into the table is what
  makes forward references practical.
- **Context Variable (Ch. 13)** — when the model object isn't mutable enough, the context variable
  holds a Construction Builder instead.
- **Expression Builder (Ch. 32)** — often the same object, conceptually distinct.

> **SDK lens:** This is the canonical justification for **builder types in a library API**: you want
> your public value objects immutable (safe to share, safe to cache, thread-safe, equality-friendly),
> yet callers assemble them over many steps. Don't compromise the product's immutability to make
> construction convenient — add a builder. Put the **lifecycle controls on the builder, not the
> product**: completeness validation at `build()` time, single-use enforcement, and rejecting
> mutation after build. These produce clear, early errors instead of half-built products escaping
> into the system. **Nest builders to mirror nested immutable structures** rather than exposing
> mutable collections on the product. And recognize the rejected alternative in the wild: an API that
> returns a modified copy on every setter looks elegant until objects are referenced from more than
> one place — Fowler's aliasing objection is the precise reason it breaks down at scale.

---

### Macro (Ch. 15)

> **Intent:** "Transform input text into a different text before language processing using Templated
> Generation." *(Ch. 15, intent line)*

This is the chapter where Fowler argues *against* a technique at length. It is the longest of the six
foundational chapters and is essentially a catalogue of failure modes. Understanding *why* he rejects
it is more valuable than the technique itself, because the reasons generalize to every
metaprogramming or code-generation feature you might ship.

#### The concept

A language has a fixed set of forms it can process. Sometimes you can see a way to add abstraction by
manipulating its input text with a purely textual transformation **before** that text is parsed.
Since you know the final form you want, it makes sense to describe the transformation by writing the
desired output with callouts for the parametrizable values — i.e. a template.

Two varieties *(Ch. 15, "How It Works")*:

- **Textual macros** treat text as text. More familiar and easier to understand. A textual macro
  processor can operate on **any** language represented as text — which is essentially all of them.
- **Syntactic macros** are aware of the *syntactic structure* of the host language, so it's easier to
  ensure they operate on syntactically sensible units and produce valid results. A syntactic macro
  processor works with **only a single language**; it's usually baked into that language's tooling or
  its specification.

Historical framing: "In the early days of programming, macros were as prevalent as functions. Since
then, they've largely fallen out of favor, mostly for good reasons." They survive mainly in internal
DSLs, particularly in the Lisp community.

The simplest legitimate form is symbolic substitution. Fowler's example is CSS: a color repeated as a
raw hex code across many rules is hard to update and obscures meaning; a macro processor lets you
name it. Two observations he draws out *(Ch. 15, "Textual Macros")*: the file you now edit **isn't
proper CSS anymore** — "you've enhanced the CSS language with a macro processor," which is precisely
the DSL move; and this particular substitution could equally be done with **Textual Polishing
(Ch. 45)**. The same mechanism handles including common headers and footers into HTML files, which
he concedes is "remarkably handy for small websites."

The critical semantic difference from a function call: **the macro is evaluated at compile time**,
doing textual search-and-replace and substituting arguments as it goes. The compiler never sees the
macro name at all.

#### The four failure modes

These are the heart of the chapter *(Ch. 15, "Textual Macros" / "Syntactic Macros")*:

1. **Mistaken expansion.** A `sqr(x)` macro defined as `x * x`, invoked as `sqr(a + b)`, expands to
   `a + b * a + b` — which, because multiplication binds tighter, is not what you meant. "Expansions
   may work most of the time but only break down in particular cases, leading to surprising bugs that
   are hard to find." Mitigation: "use more parenthesis than a Lisper." **Syntactic macros largely
   avoid this class**, because they know the host grammar.

2. **Multiple evaluation.** You pass an argument with a side effect, and the macro body mentions that
   argument more than once, so it's evaluated more than once — `max(++a, ++b)` increments both twice.
   "It's particularly frustrating because it's hard to predict the various ways macro expansions can
   go wrong. You have to think differently than you do with function calls, and it's harder to see
   through consequences, particularly when you start nesting macros." **Syntactic macros do *not* fix
   this.**

3. **Variable capture (macro declares the name).** A macro body that declares its own local variable
   silently shadows a caller variable of the same name; the passed-in variable is ignored and the
   caller's is left with the wrong value. "The name was expanded into the macro but interpreted by the
   macro as a variable defined within the macro itself."

4. **Reverse variable capture (macro clobbers the caller's name).** The mirror image, in languages
   that don't force variable declaration. The macro body assigns to a name the caller was already
   using, **silently overwriting the caller's variable** while still producing the correct value for
   the named output. The visible behavior looks right, so the bug lands somewhere else, later. "The
   consequences of the capture may be different, indeed worse, than the earlier form of variable
   capture, but both of them stem from the same basic problem."

#### The dominant actual use of macros: deferred evaluation

This is the most transferable insight in the chapter and the reason it earns its place in an SDK
document.

Fowler shows an *Execute-Around Method [beck-sbpp]*: a `safe.open { ... }` call where `open` unlocks
the safe, runs the passed-in block, then locks it again. "**The key point is that the content of the
closure isn't evaluated until the receiver calls `yield`**, so the receiver can open the safe *before*
running the passed-in code." Contrast passing the contents as an ordinary parameter — that fails,
because the parameter is evaluated *before* the call.

> "Deferred evaluation means that the receiving method to a call chooses when, or indeed if, to
> execute the code that's been passed in." *(Ch. 15, "Syntactic Macros")*

In Lisp, writing that call as a plain function requires wrapping the argument in a `lambda`, which
"looks way too messy." A macro restores the clean call syntax. Fowler's conclusion:

> "A large part (perhaps the majority) of the use of Lisp macros is to provide a clear syntax for the
> mechanism of delayed evaluation. **A language with a cleaner closure syntax doesn't need macros for
> this.**" *(Ch. 15, "Syntactic Macros")*

That is the chapter's most important judgement: **most macro use is a workaround for clumsy closure
syntax.** If your language has good block/lambda syntax, you already have most of the benefit with
none of the four failure modes.

He then shows that the Lisp version *still* hits variable capture and multiple evaluation. Lisp's
mitigations are Scheme's **hygienic macros** (the system automatically avoids capture by renaming
symbols behind the scenes) and Common Lisp's **gensyms** (generate guaranteed-unique symbols; more
trouble to use, but they let you *deliberately* use variable capture where that's useful). Fixing both
problems noticeably complicates the macro, and his verdict is: **"Avoiding such issues makes macros a
lot harder to write than they might seem at first sight."**

#### The second use: Parse Tree Manipulation

Beyond deferred evaluation, Lisp macros enable **Parse Tree Manipulation (Ch. 43)**. Lisp's syntax
"seems quirky on first glance, but as you get used to it, you realize that it's a good representation
of the parse tree of the program": in each list the first element is the node type and the rest are
its children. Manipulating Lisp code before evaluation *is* parse tree manipulation.

The worked example is `setf`, which takes an **access expression** and automatically computes and
applies the corresponding **update** — sparing you from remembering an accessor and a mutator for
every data shape. Its limits reduce the magic: it works only on **invertible functions**, with Lisp
keeping a record of inverses. **The load-bearing point:** defining `setf` *requires* macros, because
it depends on the ability to parse the input expression. **"This ability to parse its arguments is
the key advantage of Lisp macros."** *(Ch. 15, "Syntactic Macros")*

Macros aren't the only route: C# supports Parse Tree Manipulation by giving you the parse tree for an
expression plus a library to manipulate it.

#### When to use it

**The appeal:** textual macros work with any text-based language, do all manipulation at compile time,
and can implement impressive behaviors beyond the host language's abilities.

**The costs** *(Ch. 15, "When to Use It")*:

- Subtle bugs — mistaken expansion, variable capture, multiple evaluation — are "often intermittent
  and hard to track down."
- **Macros don't appear in downstream tools.** "The abstractions they provide leak like a sieve
  without the wires, and you get no support from debuggers, intelligent IDEs, or anything else that
  relies on the expanded code."
- **Nested macro expansion is much harder to reason about than nested function calls.** Fowler
  concedes this could be a lack of practice, "but I suspect it's something more fundamental."

**Verdict on textual macros:** "I don't recommend using textual macros in anything but the very
simplest cases." For *Templated Generation* they work acceptably, **provided you avoid trying to be
too clever with them — in particular, avoiding nesting the expansions.** Otherwise "they are simply
not worth the trouble."

**Verdict on syntactic macros:** most of the same reasoning applies. You're less likely to get
mistaken expansions, "but the other problems still crop up. This makes me very wary of them." As an
outsider to Lisp he is reluctant to judge too hard: "they do make sense for Lisp, but I'm not
convinced that the logic of using them there makes sense for other language environments."

**The practical shape of the decision:** most language environments don't support syntactic macros at
all, "so there's no choice to worry about." Where you do have them, "they are often necessary to do
useful things, so you have to become at least a little familiar with them." **The choice on using
syntactic macros is really made for you by your language environment.** The only genuine choice left
is whether macros are a reason to *choose* a language: "For the moment, I see macros as a worse choice
than available alternatives, and thus a point deducted from those environments that use them" —
explicitly hedged.

#### Relationships

- **Templated Generation** — the only use Fowler blesses for textual macros.
- **Textual Polishing (Ch. 45)** — the simplest substitution cases can just be search-and-replace;
  Fowler calls polishing "a simple application of textual Macros, with all the corresponding problems."
- **Closure (Ch. 37) / Nested Closure (Ch. 38)** — the *preferred alternative* for the
  deferred-evaluation use case that motivates most Lisp macros.
- **Parse Tree Manipulation (Ch. 43)** — the other Lisp-macro use case.
- **Nested Function (Ch. 34)** — what makes Lisp code parse-tree-shaped in the first place.

> **SDK lens:** Three rules fall out. (1) **Prefer closures over macros or codegen for deferred
> evaluation.** Execute-around, resource scoping, retry wrappers, transaction blocks, instrumentation
> spans — all of these should be higher-order functions taking a callback, not generated code.
> Fowler's strongest claim is that most macro usage compensates for poor closure syntax; if your
> language has terse lambdas, you already have the feature. (2) **"Leaks like a sieve without the
> wires" is a general test for any metaprogramming feature you ship**: does the abstraction survive
> into the debugger, the stack trace, the type checker, and the IDE? If it disappears from downstream
> tooling, your users pay for it during every incident. (3) **Document evaluation cardinality
> explicitly** for any API that takes an expression or thunk and may run it zero, one, or many times —
> multiple evaluation and name capture generalize far beyond macros. And whatever generation you do
> permit, **don't nest it**; nesting is where reasoning collapses.

---

### Notification (Ch. 16)

> **Intent:** "Collects errors and other messages to report back to the caller." *(Ch. 16, intent
> line)*

#### The concept

You've carried out operations that made significant changes to an object model, and now you want to
check the result is valid. You initiate a validation command. You want the answer as a **simple
Boolean**, but if there *are* errors you want to know more — and in particular you want to know about
**all** the errors rather than having validation stop at the first one.

A Notification is an object that **collects errors**. When a check fails it adds an error to the
Notification. When the command finishes, it **returns the Notification**. The caller can then ask
whether everything was OK, and if not, delve into the errors.

#### How it works

- The basic form is simply **a collection of errors**. During the notified task you need the ability
  to add an error: as simple as a message string, or as involved as a structured error object.
- When the task is done, the Notification goes back to the caller, who invokes a **simple Boolean
  query method** to see if all is well, and interrogates further if not.
- **Getting the Notification to where errors happen.** It usually needs to be available to several
  methods in the model. Two options *(Ch. 16, "How It Works")*: pass it in as an argument — a
  **Collecting Parameter** *[beck-ip]* — or **stash it in a field** if there's an object corresponding
  to the task at hand (a validator object, a parse-helper object) that can own it for the duration.
- **Beyond errors.** The primary purpose is collecting errors, but it's sometimes useful to capture
  **warnings** and **informational messages** too. Fowler's definitions: an **error** indicates the
  requested command has *failed*; a **warning** occurs for something that doesn't fail but is still a
  matter of potential concern; an **informational message** is just potentially handy information.
- **"In many ways, a Notification is an object acting like a log file, so many of the features
  commonly found in logging can be useful here."** *(Ch. 16, "How It Works")* — severity levels,
  formatting, filtering, structured payloads, report rendering.

#### When to use it — the fail-fast vs. collect-all decision rule

The tradeoff is crisp *(Ch. 16, "When to Use It")*:

- Use a Notification "whenever there is a complicated operation that may trigger multiple errors and
  you don't want to fail at the first error."
- **"If you do want to fail at the first error, then you can simply throw an exception."** A
  Notification is what you use when you want to store multiple errors "to give the caller a fuller
  picture of what the request led to."

That is the entire decision rule, and it is refreshingly mechanical: *how many independent problems
can one invocation surface, and does the caller need to see them all before acting?* If the answer is
one, throw. If it's many — validating a document, a schema, a config file, a migration, a whole
populated Semantic Model — collect.

#### The layering argument

The second motivating situation is not about error handling at all. It is about layers *(Ch. 16,
"When to Use It")*:

> **When a user interface initiates an operation at a lower layer:** "The lower layer should not try
> to interact with the user interface directly, so a Notification makes an appropriate messenger."

The lower layer *reports*; it does not *present*. A Notification is the messenger across the layer
boundary — the alternative being that your model layer starts printing, logging at the user, or
reaching up into the presentation layer, which couples the two permanently and makes the lower layer
untestable and unusable in any other context.

#### Design decisions from the examples

**Simple Notification** *(Ch. 16, "A Very Simple Notification (C#)")* — errors stored as plain
strings. Two carry-away decisions:

- The add-error method takes a **format string plus arguments**, formatting internally. "Using a
  format string and parameters makes it a bit easier to use the notification to capture errors, as the
  client code doesn't need to build the format string." Push message assembly *into* the Notification
  so call sites stay one-liners.
- It provides both **`IsOK` and `HasErrors`** Boolean queries (deliberate redundancy so the caller can
  write whichever reads better), **and** an **`AssertOK()`** that throws if there are errors.
  *"Sometimes this fits the flow of usage better than using the Boolean check methods."* — **offer
  both a query-style and a throw-style consumption path** over the same collected data.

**Parsing Notification** *(Ch. 16, "Parsing Notification (Java)")* — more involved, and it accepts
specific *kinds* of error rather than strings:

- It lives in the parse helper, and at the end of the run, if there are errors, the whole parse fails
  with a **single exception carrying the accumulated report**. This is the **collect-then-fail-once**
  shape: gather everything during the operation, raise one well-populated failure at the boundary.
- It handles **two distinct error sources** and unifies them: errors from the parser generator itself
  (hooked by overriding the generator's error-reporting method, delegating to the default so standard
  behavior is preserved) and semantic errors detected by the translation code.
- **Internal structure:** the error list holds message *objects*, not strings, with a small class
  hierarchy — one wrapping the parser's recognition exception, one holding the offending token plus
  the formatted message. The base class exists essentially as a marker to make the generics work ("In
  time, I might add something to it, but for the moment a bare marker suffices"). **"By passing the
  token in, I'm able to provide better diagnostic information."**

**Fowler's closing design principle for the chapter:**

> "I think the most important point here is to build a Notification that makes the calling code as
> simple and compact as possible. Therefore, I pass all the relevant data to the Notification and let
> the Notification sort out how to compose error messages from this data." *(Ch. 16, "Parsing
> Notification (Java)")*

That is: **call sites hand over raw structured context (token, object, values); the Notification owns
formatting and presentation.** Not the reverse.

#### Relationships

- **Semantic Model (Ch. 11)** — validations over a populated model are the archetypal producer of
  Notifications, and Ch. 11 explicitly says validation belongs there and should run *before*
  interpretation or code generation.
- **Collecting Parameter *[beck-ip]*** — the mechanism for threading a Notification through many
  methods.
- **Parse Tree Manipulation (Ch. 43)** — its IMAP example accumulates validation errors in a
  Notification before throwing.

> **SDK lens:** Almost nothing here is DSL-specific. **Batch validation should collect, not fail
> fast.** Any API that validates a document, config, schema, request payload, or migration should
> return *all* the problems in one pass; returning one error at a time forces users into an
> infuriating fix-rerun loop. **Offer both consumption styles** over the same result — an `is_ok()`
> query for callers who want to branch, and an `assert_ok()`/`raise_for_status()` for callers who want
> an exception at their own boundary — and don't force the choice on them. **Structured messages beat
> strings:** carry location (line/column, JSON path, field name) and the offending value as data on the
> message object, and render human text only at the edge; this is what makes errors machine-consumable
> for IDE squiggles and CI annotations as well as readable. **Keep formatting out of call sites** so
> error-raising stays a single line and wording stays centrally changeable. And observe the **layering
> discipline**: a lower layer returns a Notification rather than printing or reaching into the
> presentation layer.

---

## 10. Fluent interface patterns — the grammar of an API

Part IV of the book covers internal DSL techniques, and Chapters 32–38 are its core: the ways you glue
DSL clauses together in a host language. Three ideas run through all of them and are worth stating up
front, because every pattern is judged against them.

**1. Fluent interface vs. command-query API.** Fowler explicitly names the *normal* style of API —
self-standing methods, each understandable on its own, obeying command-query separation — as a
**command-query API**, noting "it's so normal that we don't have a general name for it" *(Ch. 32,
opening)*. A **fluent interface** is a different animal: it is designed for readability of *the whole
expression*, and as a result "fluent interfaces lead to methods that make little sense individually,
and often violate the rules for good command-query APIs." Nearly every decision in this part is
downstream of that: fluent methods get license to break normal API rules, and the price of the license
is that they must be quarantined somewhere.

**2. Fluent API design *is* grammar design.** Fowler repeatedly reasons about which technique to use by
writing the production rule the clause must satisfy, in BNF-ish notation, then choosing the technique
that fits it. The full mapping appears in the synthesis subsection below. He also observes that the
tree of Expression Builders you end up with "really is a syntax tree for the DSL" *(Ch. 32, "How It
Works")*.

**3. Evaluation order is a first-class design variable.** Function Sequence and Method Chaining
evaluate left-to-right. Nested Function evaluates arguments *before* the enclosing call (inside-out).
Nested Closure lets the parent decide *when* — including before/after setup and teardown. Most of the
tradeoffs in this part reduce to which evaluation order you need.

---

### Expression Builder (Ch. 32)

> **Intent:** "An object, or family of objects, that provides a fluent interface over a normal
> command-query API." *(Ch. 32, intent)*

#### The concept

An Expression Builder is a *separate layer* whose only job is to host the fluent, DSL-flavored
methods and translate those calls into ordinary command-query calls on the underlying Semantic Model.
You keep two interfaces to your system: the normal one on your domain objects, and the fluent one on
the builders. Because the fluent one lives somewhere else, it is "clearly isolated, making it easier
to follow" *(Ch. 32, opening)*.

Why the isolation matters: fluent methods *are* strange. They return `this` from mutators (violating
command-query separation). They are named like queries but act like commands. They define separate
`First()` and `Third()` methods where a parameter would be better programming. In C# they may be
implemented as property *getters* that mutate. Fowler's own words about that last trick: it is
something he "would call extremely bad code" — "only acceptable when clearly placed in a fluent
context — again, I would confine this abomination to a securely fenced Expression Builder" *(Ch. 35,
"Chaining with Properties (C#)")*. **The Expression Builder is the fence.**

#### How it works

- Think of the builder as a **translation layer**: fluent interface in, command-query API out.
- It is "often a *Composite* [gof] using child Expression Builders to build subexpressions within an
  overall clause" *(Ch. 32, "How It Works")*.
- Its exact shape depends on which function-combination pattern supplies the fluent surface. With
  Method Chaining, it's a sequence of method calls each returning a builder. With Nested Function, the
  builder may be a superclass (Object Scoping) or a bag of static functions. Fowler declines to give
  general structural rules for that reason.
- **One vs. many builders** is "one of the most notable questions." Multiple builders form a tree that
  mirrors the DSL's syntax tree, and "the more complex the DSL, the more valuable a tree of Expression
  Builders is" *(Ch. 32, "How It Works")*.
- **The key structural tip:** have a well-defined Semantic Model whose objects have command-query
  interfaces and can be manipulated *without any DSL at all* — with at least some tests that touch
  only that interface. Builders are then tested by comparing the model objects they produce, inspected
  through direct command-query calls.

The multiple-builder mechanics are worth internalizing *(Ch. 32, "Using Multiple Builders for the
Calendar (Java)")*. If the model object is immutable, fluent calls have nowhere to write partial data,
so you must accumulate it somewhere. Option A is fields on a single top-level builder — i.e. Context
Variables. Option B, which Fowler prefers, is to give each subexpression its own child builder,
"essentially, using a Construction Builder." The parent holds a *list* of child builders; a call that
starts a new child creates it, registers it, and returns it so the chain continues on the child; the
child holds a back-pointer to the parent, because **the punctuation call that starts the *next* child
arrives at the child and must be forwarded upward**. A final `getContent()` on the parent walks all
children and materializes the entire Semantic Model at once — which is exactly what lets the model be
immutable.

#### When to use it

Fowler is unusually direct: **Expression Builder is a default.** "I consider Expression Builder a
default pattern — meaning I tend to use it pretty much all the time unless there's a good reason not
to" *(Ch. 32, "When to Use It")*.

The alternative is putting the fluent methods on the Semantic Model itself. His objections, in order
of weight:

1. **Separation of concerns (the main one).** It intermingles the API for *building* the model with
   the methods that *run* it. Both are usually substantial: execution logic often requires an
   alternative computational model to understand; fluent interfaces have their own logic to maintain
   flow. "It's easier to understand if we separate building logic from execution logic."
2. **Unfamiliarity.** Mixing fluent and command-query methods on one class mixes two ways of
   representing an API, and because fluent APIs are rarer, developers are less familiar with them,
   "exacerbat[ing] the situation."

The best argument *against*: when the Semantic Model's execution logic is very simple, mixing building
into it adds little complexity. Fowler notes people combine the two frequently — partly from
unawareness of the pattern, partly from unwillingness to add classes — and states his bias plainly: "I
prefer lots of little classes to a few big classes, so my fundamental design philosophy encourages me
to use Expression Builder."

The calendar example makes the cost concrete *(Ch. 32, "A Fluent Calendar with and without a Builder
(Java)")*. Without a builder, fluent methods sit oddly next to genuine queries on the domain class.
Worse: if anyone needs to modify an event *outside* the DSL context, you must *also* supply normal
command-query mutators — so the class ends up carrying two overlapping mutation APIs, and using the
fluent one outside its intended context "would lead to hard-to-read code."

#### Relationships

- Supplies the object that **Method Chaining (Ch. 35)** chains on and the class that **Object Scoping
  (Ch. 36)** scopes to.
- Hosts **Context Variables (Ch. 13)**, keeping parse state out of global/static space.
- Uses **Construction Builder (Ch. 14)** for subexpression data — same object sometimes, different
  concept always.
- Produces the **Semantic Model (Ch. 11)**, which must remain independently usable.
- Multiple Expression Builders ≈ the DSL's syntax tree.

> **SDK lens:** This is *the* foundational SDK-design pattern in the book. Keep the ergonomic/fluent
> surface in dedicated builder types and keep your resource/response/domain objects plain,
> inspectable, and conventional — users hold the domain objects at runtime and should never encounter
> a mutator that returns `this` or a getter that mutates. Make the plain API complete enough that the
> SDK is fully usable without the fluent sugar, and **prove it with tests that touch only the plain
> API**; that's both an architectural constraint and a regression guard against features becoming
> reachable only through the DSL. Model the builder tree on the shape of the *configuration grammar*,
> not on your class hierarchy — one builder per nesting level is the norm for anything non-trivial.
> And note the immutability corollary: immutable model objects and fluent building are compatible only
> if you buffer in builders and construct at the end, which is the direct justification for
> `build()`-style terminal methods in immutable-first SDKs.

---

### Function Sequence (Ch. 33)

> **Intent:** "A combination of function calls as a sequence of statements." *(Ch. 33, intent)*

#### The concept

The simplest combination: a flat run of statements, one call per line. Crucially, "there is no data
relationship between them" *(Ch. 33, "How It Works")* — the calls are related only by their order in
time. Any structure the DSL *appears* to have (nesting, "this size belongs to that disk") is **not in
the code**; it must be reconstructed by the builder from accumulated parse state. Hence: "a heavy use
of Function Sequence means you use a lot of Context Variables."

```
computer()
  processor()
    cores(2)
    speed(2500)
```

Fowler is explicit that the indentation above is a lie in the technical sense: "that's just arbitrary
use of whitespace. The script is really just a sequence of function calls with no deeper relationship
between them. The deeper relationship is built up entirely using Context Variables" *(Ch. 33, "Simple
Computer Configuration (Java)")*.

#### How it works

- For readability you want **bare** function calls — no receiver prefix. The obvious way is global
  functions, which brings two problems: global visibility and static parse data.
- **Global visibility**: mitigate with whatever namespacing the language has, to narrow the scope of
  the calls down to the Expression Builder. In languages with no global-function mechanism at all
  you're stuck writing class-qualified calls, "which often adds noise to the DSL."
- **Static parse data** is the worse problem, and Fowler singles it out: "Static data is often a
  problem because you can never be entirely sure who is using it — particularly with multithreading.
  This problem is particularly pernicious with Function Sequence because you need a lot of Context
  Variables to make it work" *(Ch. 33, "How It Works")*.
- **Object Scoping fixes both.** It hosts the functions on a class in the natural OO way and gives you
  an instance to put parse data in. His recommendation: "I suggest using Object Scoping if you are
  using Function Sequence in all but the very simplest cases."

The most instructive detail in the worked example is that **`speed()` is ambiguous** — it could mean
processor speed or disk speed, so it must branch on which context variable is currently set and throw
if neither is *(Ch. 33, "Simple Computer Configuration (Java)")*. This is the direct, visible cost of
"no data relationship between calls": clause-name resolution becomes runtime state inspection, and
illegal scripts fail at runtime rather than at compile time.

#### When to use it

The bluntest verdict in the part: "On the whole, Function Sequence is the least useful of the function
call combinations to use for DSLs. Using Context Variables to keep track of where you are in a parse is
always awkward, leading to code that's hard to understand and easy to get wrong" *(Ch. 33, "When to Use
It")*.

Where it *is* reasonable:

- **At the top level of a language**, or at the top level inside a Nested Closure, where the DSL is a
  list of high-level statements. There you only need a single result list and one Context Variable —
  the cost stays bounded. Below that level, form expressions with Nested Function or Method Chaining.
- **Because you have to start somehow.** "Perhaps the biggest reason to use Function Sequence is that
  you always have to start your DSL with something, and that something has to be a Function Sequence
  even if there's only one call in the sequence. This is because all the other function call techniques
  require some kind of context."
- Alternative for the simple case: a Function Sequence is a list of elements, so **Literal List
  (Ch. 39)** is the obvious substitute.

#### Relationships

- **Requires** Context Variables; **should** use Object Scoping; uses Construction Builder for the
  accumulated pieces.
- Alternative: Literal List.
- Dramatically improved by wrapping in a **Nested Closure (Ch. 38)**, which lets the parent create the
  Context Variable just before the sequence and tear it down just after.

> **SDK lens:** This is the imperative "statement-style" configuration API — `client.setRegion(...);
> client.setRetries(...);` or, worse, a sequence of top-level calls that implicitly mutate shared
> session state. If your SDK's surface relies on hidden mutable state to answer "which thing am I
> configuring right now?", you are in Function Sequence territory and you inherit its costs:
> thread-safety hazards, order-dependence, ambiguous method names that must dispatch on state, and
> errors surfacing at runtime. **Static/global parse state is the specific thing to refuse** — bind
> state to an instance. The legitimate uses map cleanly: a top-level sequence of independent
> operations is fine; expressing *nested* configuration this way is not.

---

### Nested Function (Ch. 34)

> **Intent:** "Compose functions by nesting function calls as arguments of other calls." *(Ch. 34,
> intent)*

#### The concept

Each clause's subelements are literally the arguments of its function call:

```
computer(processor(cores(2), speed(2500), i386),
         disk(size(150)),
         disk(size(75), speed(7200), SATA))
```

The hierarchy of the DSL becomes the hierarchy of the host language's expression tree. Fowler's
framing: "By representing a DSL clause as a Nested Function, you're able to reflect the hierarchic
nature of the language in a way that's mirrored in the host language, not just in a formatting
convention" *(Ch. 34, "How It Works")*. **The structure is real, not indentation.**

#### How it works

**Evaluation order is the defining property.** "Function Sequence and Method Chaining both evaluate the
functions in a left-to-right sequence. Nested Function evaluates the arguments of a function before the
enclosing function itself." Fowler's mnemonic is the **Old MacDonald problem**: to sing the chorus you
type the vowels inside-out. "This evaluation order has an impact on both how to use Nested Function and
when to choose it instead of alternatives" *(Ch. 34, "How It Works")*.

Three consequences of arguments-first:

- **A built-in context to work with the arguments.** Argument functions return fully formed values that
  the enclosing function assembles into its return value.
- **No finishing problem** (unlike Method Chaining) — the closing bracket of the outermost call *is* the
  end, and that call naturally returns the finished object.
- **No Context Variable needed** (unlike Function Sequence) — the data flows through return values.

**Fit to grammar.** "With mandatory elements in the grammar, along the lines of `parent ::= first
second`, Nested Function works particularly well. A parent function can define exactly the arguments
required in the child functions and, with a statically typed language, can also define the return
types, which enables IDE autocompletion."

**Labeling arguments.** `disk(150, 7200)` is unreadable — "there's no indication what the numbers mean,
unless you have a language with keyword arguments." The fix is a wrapping function that exists only to
name the value: `disk(size(150), speed(7200))`. In its simplest form the wrapper returns its argument
unchanged, "representing pure syntactic sugar." But sugar has a cost: **no enforcement** — "a call to
`disk(speed(7200), size(150))` could easily result in a very slow disk." The fix is to have the nested
functions return intermediate data — a builder or a token — so the type system carries the meaning, at
the cost of more setup.

**Optional arguments.** Use the language's default arguments if it has them. Otherwise define a
different function per combination — "tedious but reasonable" for a couple, but "as the number of
optional arguments increases, so does the tediousness (but not the reasonableness)." Intermediate
data/tokens are one escape; **Literal Map (Ch. 40)** is the cleanest, "the only problem is that C-like
languages don't usually support Literal Map."

**Multiple arguments of the same kind.** Varargs is best where supported; "You can also think of this
as a nested Literal List."

**The worst case.** "The worst case of this is a grammar like `parent ::= (this | that)*`." Without
keyword arguments, the only identification available is position and type — "messy, and downright
impossible if `this` and `that` have the same types." You are forced into returning intermediate
results or into a Context Variable, and the Context Variable route is "particularly difficult here
since the parent function isn't evaluated till the end, forcing you to use the broader context of the
language to properly set up the Context Variable."

**Bare calls: an important asymmetry.** Same question as always — global functions or Object Scoping —
but "global functions can often be much less problematic in Nested Function, because the biggest
problem with global functions is when they come with a global parsing state. A global function that
just returns a value, such as a static method like `DayOfWeek.MONDAY`, is often a good choice." Nested
Function usually needs no parse state, so the danger largely evaporates *(Ch. 34, "How It Works")*.

**Tokens and subtype tokens.** The escape from the worst case is to have every nested function return a
**token** object carrying a type tag plus a value; the parent takes a varargs of tokens, iterates, and
dispatches on the tag *(Ch. 34, "Handling Multiple Different Arguments with Tokens (C#)")*. Tokens
convert "which argument is this?" from a *positional* question into a *data* question, buying arbitrary
ordering and optionality at the cost of a token type and a dispatch switch.

The refinement is sharper *(Ch. 34, "Using Subtype Tokens for IDE Support (Java)")*: "Checking is all
very well, but in a statically typed language with a modern IDE, you want to go further. You want
autocompletion popups to force you to put size before speed. By using subclasses, you can pull this
off." Define a **subtype per clause** — `SizeToken`, `SpeedToken` — so the parent's signature is
`disk(SizeToken, SpeedToken)`; the compiler enforces the right token in the right position and
autocompletion suggests the right function in the right place. This is the Nested Function analogue of
**progressive interfaces** in Method Chaining: encoding grammar constraints in the type system so the
IDE teaches the language.

A useful reframing from the same chapter: C#'s object initializers "can be thought of as Nested
Functions that can take keyword arguments (like a Literal Map) which are restricted to object
construction" *(Ch. 34, "Using Object Initializers (C#)")*.

#### When to use it

- **The strength and the weakness are the same thing: evaluation order.** Arguments-first "is very
  useful for building up a hierarchy of values because you can have the arguments create fully formed
  model objects to be assembled by the parent function. This can avoid much of the mucking about with
  replacements and intermediate data that you get with Function Sequence and Method Chaining."
- **Conversely, it's wrong for command sequences.** "This evaluation order causes problems in a
  sequence of commands, leading to the Old MacDonald problem… So, for a sequence that you want to read
  from left to right, Function Sequence or Method Chaining are usually a better bet. For precise
  control of when to evaluate multiple arguments, use Nested Closure."
- **Weak on optionality and variety.** "Nested Function very much expects you to say what you want and
  in the precise order you want it. If you need greater flexibility you'll need to look to Method
  Chaining or a Literal Map." Literal Map is singled out because "it allows you to get the arguments
  sorted out before calling the parent while giving you the flexibility of ordering and optionality of
  the arguments."
- **Punctuation is the aesthetic cost.** It "usually relies on matching brackets and putting commas in
  the right place. At its worst, this can look like a disfigured Lisp, with all the parentheses and
  added warts. This is less of an issue for DSLs aimed at programmers, who get more used to these
  warts."
- **Name clashes are *less* trouble than with Function Sequence**, "since the parent function provides
  the context to interpret the nested function call. As a result, you can happily use 'speed' for
  processor speed and disk speed and use the same function as long as the types are compatible."
- Cross-reference from Ch. 35: "Nested Function is the better choice for mandatory clauses."

Two design lessons from the recurring-events example are worth keeping even though they're about
another topic *(Ch. 34, "Recurring Events (C#)")*. First, **the DSL can read *opposite* to the model**:
"We say 'first and third Monday' in our language, but in terms of the specification, it's the first
*or* third Monday that matches the Boolean condition. It's an interesting example of where the DSL is
opposite to the model in order for both to read naturally." The fluent layer's job is to read naturally
to the domain reader, not to mirror the model's structure. Second, **name for the reader of the
script**: Fowler named an Expression Builder `Schedule` rather than `ScheduleBuilder` "because I think
it reads better as just 'schedule.'"

#### Relationships

- Opposes Function Sequence / Method Chaining on evaluation order.
- Complemented by **Literal List (Ch. 39)** (varargs), **Literal Map (Ch. 40)** (optionality +
  ordering), **Nested Closure (Ch. 38)** (control of *when* arguments evaluate), **Object Scoping
  (Ch. 36)** (bare calls), **Expression Builder (Ch. 32)** (where the functions live).
- Tokens / subtype tokens are its type-system mechanism; progressive interfaces are the Method Chaining
  equivalent.

> **SDK lens:** This is the "constructor / nested options-object" style, and the only technique in the
> set that can *require* things. **Required parameters and structural hierarchy belong here** — if your
> SDK has parameters that must be present, they belong in the function signature, not in chainable
> setters, which can always be omitted. Sugar wrappers that only label a value improve readability but
> enforce nothing; typed wrappers enforce *and* drive autocomplete — that's the exact tradeoff behind
> newtype/branded-type parameters in modern SDKs. The crucial judgement is the **degradation curve**:
> Nested Function is excellent for a fixed mandatory shape and gets *worse the more optional settings
> you add* — combinatorial overloads, positional ambiguity, unordered heterogeneous arguments. That's
> precisely the region where builders, keyword arguments, and option maps win, and knowing where the
> crossover sits is most of the skill. Practical rule: prefer keyword arguments / options objects
> wherever the host language has them; they give you optionality, ordering freedom, and named arguments
> in one move, and remove the need for tokens entirely.

---

### Method Chaining (Ch. 35)

> **Intent:** "Make modifier methods return the host object, so that multiple modifiers can be invoked
> in a single expression." *(Ch. 35, intent)*

#### The concept

Rather than three separate setter statements, write `new HardDrive().capacity(150).external().speed(7200)`.
Each modifier returns an object — usually itself — so the next call can continue the chain.

Fowler opens with a corrective worth quoting: "Method Chaining rapidly caught on amongst people as an
example of what an internal DSL should look like. It caught on a bit too much — people started to assume
that Method Chaining was synonymous with fluent interfaces and internal DSLs. My view is that Method
Chaining is one of several techniques, but it's still valuable and noticeable" *(Ch. 35, "How It Works")*.

#### How it works

- Mechanically trivial: the modifier returns `this` (or another object) instead of `void`.
- **It breaks command-query separation, knowingly.** "Returning a value from a modifying method breaks
  the principle of command-query separation. Most of the time I follow that principle, and it's served
  me well. A fluent interface is one case when we need to break it."
- **It breaks naming conventions too.** "A method like `sata()` would seem like a query, not a modifier.
  This naming is very problematic, as it will seriously confuse anyone who is expecting a command-query
  API. Taken together, Method Chaining violates many common rules of common (command-query) API design."
  Two independent reasons to fence it inside an Expression Builder.
- **It changes formatting conventions.** Long chains read badly on one line, "particularly if we want to
  suggest a hierarchy," so put each call on its own line. Practical bonus: "Putting methods on separate
  lines also makes debugging easier, as error messages and debugger control usually work on a
  line-by-line basis. Therefore, it's wise to do less on each line."
- **Why constructors aren't the answer.** "DSLs are often about building up configurations of objects,
  and doing so in constructors is often tricky. It's also usually difficult to read, since constructors
  often allow only positional parameters."

**Builders or values.** Fowler's preference is chaining on Expression Builders, "since that reduces the
confusion between the conventions of fluent and command-query APIs." The alternative is chaining on
domain types — `42.grams.flour`, where each step returns a different Value Object, which Neal Ford calls
**type transmogrification**. Fowler is explicitly non-dogmatic: "There are plenty of good developers who
are comfortable with using Method Chaining on domain types like this, so I'm cautious about arguing
against it. My inclination, however, leads me to prefer using Expression Builders as much as possible,
to clearly separate command-query and fluent API styles" *(Ch. 35, "Builders or Values")*.

#### The finishing problem

This is Method Chaining's signature weakness and the most SDK-relevant idea in the chapter *(Ch. 35,
"Finishing Problem")*.

- "It boils down to the lack of a clear end-point to a method chain." Every method must return a builder
  to keep the chain alive, so nothing in the chain signals completion, and the value you actually want —
  the finished domain object — never appears.
- In Fowler's words: "I would like the returned value to be an `Appointment` object, since that would be
  the most natural usage. However, the need to continue the method chain means that each method has to
  return an appointment builder. There's nothing in the chain that tells me when I'm done, so I have to
  put in some kind of marker method to show the end."

The options, ranked:

1. **A natural last clause that returns the finished object.** From the progressive-interfaces example:
   "I have a natural stop method with `Body`, so I'll have that return the message." Best when the
   grammar genuinely has a terminal clause.
2. **An explicit finishing method** (`.end()`, `.build()`). "It isn't too bad, but the use of `End` is
   still a bit of syntactic noise."
3. **An implicit conversion operator** (C#) — "although that does mean you'll forgo `var` for an explicit
   type."
4. **Use a different pattern.** "This is where using Nested Function or Nested Closure can be a valuable
   alternative." Their enclosing call *is* the terminator.

Fowler also notes the ergonomic cost of *not* having a finisher: without one you must break the
expression into a builder statement plus a separate `getValue()` call — two statements and a named
variable *(Ch. 35, "The Simple Computer Configuration Example (Java)")*.

#### Hierarchic structure

- "Tied in with the finishing problem is the problem that Method Chaining doesn't naturally fit a
  hierarchic structure. Hierarchic structures are common in languages, which is why syntax trees are
  valuable for thinking about them" *(Ch. 35, "Hierarchic Structure")*.
- In a chained computer configuration, "There's a definite hierarchy to this, but it's suggested by the
  indentation and not captured in the structure of the code itself. As a result, we have to manage that
  structure ourselves. This problem also occurs with Function Sequence."

Two management strategies: **Context Variables**, or **a child builder per subelement**. The second half
of Fowler's note on child builders is the important part: "A separate builder allows us to limit the
methods available to only those required to provide the information for the disk or a finishing method."
A child builder isn't just data scoping, it's **grammar scoping**.

The worked example deliberately shows both sub-structure strategies side by side — a simple Construction
Builder held in a Context Variable for the processor, and a full delegating child builder for the disks
— and Fowler names the inconsistency and explains it: "A simple Construction Builder works better for
simple cases and full delegation works better for more complicated cases. I've shown both here for
pedagogical reasons, although I lean more to full delegation" *(Ch. 35, "The Simple Computer
Configuration Example (Java)")*. **Punctuation forwarding** recurs here too: a child builder must forward
calls that belong to the parent (starting a sibling, finishing the whole expression).

His summary judgment on the example is the balanced takeaway: "Method Chaining reads very clearly,
without much of the syntactic noise that can clutter Nested Function. However, to pull it off, I have to
do a lot of fiddling around with Context Variables and cope with the finishing problem."

#### Progressive interfaces — type-encoded grammars

The chapter's most important technique for SDK design *(Ch. 35, "Progressive Interfaces")*.

- "A valuable variation to the basic Method Chaining approach is to use multiple interfaces to drive a
  fixed sequence of method-chaining calls."
- The email example forces destination, then Cc's, then subject, then body. You present a *sequence of
  interfaces* over the one Expression Builder: the first exposes only `to`; `to` returns an interface
  exposing only the legal next steps (`to`, `cc`, `subject`); `cc` returns one with only `cc` and
  `subject`; `subject` returns one with only `body`.
- Implementation: the builder implements all the interfaces; each method still returns `this`, but
  *typed as the next interface*. Interfaces can inherit from each other so a later stage picks up an
  earlier stage's legal steps without duplicating declarations.
- **Payoff:** "This can work really well in a statically typed language with IDE support. Autocompletion
  in the IDE can step you through each clause in the DSL by only suggesting the methods that are valid
  for that point in the chain." Honest caveat: "it's not perfect, as methods inherited from `Object`
  also show up."
- **Relationship to child builders:** "This ability to control which methods are valid in which contexts
  is similar to that you get by using a child builder. Indeed, you can use a child builder to do the
  same thing as progressive interfaces, but progressive interfaces are easier if there's no other reason
  to make a child builder."
- **Mandatory elements:** "Progressive interfaces can be used to enforce mandatory elements in a chain;
  for this, define an interface that only takes a single mandatory element."

#### When to use it

- "Method Chaining can add a great deal to the readability of an internal DSL and, as a result, has
  become almost a synonym for internal DSLs in some minds. Method Chaining is best, however, when it's
  used in conjunction with other function combinations" *(Ch. 35, "When to Use It")*.
- **Best for optional clauses.** "Method Chaining works best when using optional clauses in a language.
  Method Chaining easily allows a DSL script writer to pick and choose clauses needed for a particular
  situation. It's difficult to specify in the language that certain clauses must be present. Using
  progressive interfaces allows some ordering of clauses, but in the end clauses can always be left out.
  Nested Function is the better choice for mandatory clauses."
- **Escape hatches.** "The finishing problem crops up from time to time. While there are workarounds,
  usually if you run into this you're better off using a Nested Function or Nested Closure. These
  alternatives are also better choices if you are getting into a mess with Context Variables."

#### Relationships

- Usually hosted on an **Expression Builder**; can be hosted on Value Objects (with **Literal Extension,
  Ch. 46**).
- Needs **Context Variables** and/or child builders for hierarchy.
- Progressive interfaces ≈ subtype tokens (Ch. 34) — both encode grammar in types.
- **Nested Function / Nested Closure** are the recommended escapes from the finishing problem and from
  Context Variable messes.

> **SDK lens:** The highest-density SDK chapter in the book. **The finishing problem is the everyday
> `.build()` question**, and Fowler's ranking translates directly: a natural terminal clause that
> returns the finished object (best), an explicit `build()`/`end()` (acceptable, noisy), an implicit
> conversion (language-specific, costs type inference), or restructure to a function/callback form where
> the enclosing call terminates (often the real answer). **Progressive interfaces are the type-state
> pattern**: returning a narrower interface from each step makes illegal call sequences fail at
> *compile* time and turns IDE autocomplete into documentation — the user is shown only what is legal
> next. That's how modern SDKs enforce "you must set auth before you can send." **Chaining cannot
> express requirement** — required inputs belong in the factory/constructor; chained setters are for
> genuinely optional configuration. **Chain on builders, not on the objects users keep**, or fluent
> conventions leak into types users inspect at runtime. **Hierarchy needs child builders, not
> indentation** — and a child builder must forward the parent's punctuation, or users hit surprising
> "method not found" errors mid-chain. Finally, **formatting is API design**: one call per line isn't
> style, it's what makes stack traces and debugger stepping point at the failing clause.

---

### Object Scoping (Ch. 36)

> **Intent:** "Place the DSL script so that bare references will resolve to a single object." *(Ch. 36,
> intent)*

#### The concept

Nested Function and, to a lesser extent, Function Sequence want *bare* calls — no receiver — for
readability, "but in their basic forms they come with a serious cost: global functions and (worse)
global state" *(Ch. 36, opening)*. Object Scoping removes both by resolving all bare calls against a
single host object: "this avoids cluttering the global namespace with global functions, allowing you to
store any parsing data within the host object. The most common way to do this is to write the DSL script
inside a subclass of a builder that defines the functions."

#### How it works

- "One of the many useful properties of objects is that each object provides a contained scope for
  functions and data. Inheritance allows you to use this scope separately from where it's defined"
  *(Ch. 36, "How It Works")*. So: define the DSL functions on a base class; write DSL programs in
  subclasses. The base class also holds fields for parse data.
- That base class is the natural home of the **Expression Builder**. Clients write DSL programs in a
  subclass of it — "Using inheritance allows them to add other DSL functions in the subclass, or even
  override base functions in the DSL object if they need to."
- **Alternatives to inheritance:** Ruby's **instance evaluation** (`instance_eval`) — "the facility to
  take any program code and execute it within the context of a particular object. This allows a DSL
  writer to write the DSL text without declaring any links to the base class that defines the language"
  — and Java's **instance initializers** (the double-brace idiom), "not well known nor often used, but
  can work well for this case."

The instance-evaluation version has a further capability worth noting: **scope switching down the tree**.
By instance-evaluating *child* builders for nested clauses, the same bare name binds to different
builders at different depths — "This mechanism allows me to handle calls to methods like `gradeAtLeast`
differently in different parts of the DSL" *(Ch. 36, "Using Instance Evaluation (Ruby)")*. That is how
you get multiple Expression Builders *and* bare calls simultaneously.

#### When to use it

- "Object Scoping solves the niggly problems of globalness within Nested Function and Function Sequence
  and as such is always worth considering… Not only does this avoid messing with a global namespace, it
  also allows you to store parsing data in an Expression Builder. I find these advantages quite
  compelling, and thus would always suggest using Object Scoping if you can" *(Ch. 36, "When to Use It")*.

Where you can't, or shouldn't:

- **It requires an OO language.**
- **It constrains where the script can live.** "With the most common inheritance case, it means you must
  put the DSL script within a method in a subclass of an Expression Builder. This isn't too much of a
  problem for self-contained DSL scripts. Such scripts often sit in their own file and are well-separated
  from other code."
- **The real problem is fragmentary DSLs.** "The real problem is with fragmentary DSLs, where using
  Object Scoping forces you into an inheritance relationship that may be awkward or even impossible."
  This **self-contained vs. fragmentary** distinction recurs in Ch. 38 and is one of the most transferable
  ideas in Part IV.
- **Sometimes globals are fine and you don't need it.** "Object Scoping is mostly an antidote to global
  functions, so it's worth remembering that the biggest problems of global functions come with modifying
  global data. A common case where you don't get this problem is when the global function just creates
  and returns a new object… If you can arrange your bare functions to be like this, then there is much
  less need for Object Scoping."
- **Extensibility bonus.** "If the DSL framework is set up to allow a user of the DSL to substitute their
  own subclass of the scoping class for Object Scoping, this also makes the DSL more extensible. A user
  subclass can add more methods to extend the language. Indeed if particular methods are only needed in
  one script, then that script subclass can define those methods directly."

#### "DSL surface deliberately less expressive than the model"

The most important design lesson in the chapter is not about scoping at all *(Ch. 36, "Security Codes
(C#)")*. The security-zone model allows arbitrary Boolean expressions, but the DSL doesn't: "Although the
underlying model allows arbitrary Boolean expressions, the DSL is simpler. Each admission rule is a
conjunction ('and') of its clauses. This is why I need separate refuse statements for the two
departments." And then the general principle:

> "Arbitrary Boolean expressions are powerful, but often difficult for people, particularly non-nerds, to
> follow. So some form of simplified structure can be handy in a DSL."

**Deliberately make the language surface less expressive than the model when that makes it easier to get
right.** The model keeps the full power for programmatic users and for future language growth; the DSL
exposes the subset domain experts can reliably reason about.

The same example also contains a small but instructive lesson about **where boilerplate lives**. Fowler
passes the target object in via a separate build method rather than a constructor, because a constructor
"would force me to add a constructor declaration to the subclass" — i.e. push boilerplate off the *user's*
class and onto the library's. "It's a small thing, but saves me a bit of noise in the DSL text. These
small things add up." He is also honest about the cost of the pattern: "Object Scoping does help in
reducing noise in the DSL, but one problem is that it does introduce noise in the code that declares the
DSL class."

#### Relationships

- Enables bare calls for **Function Sequence** and **Nested Function**; hosts the **Expression Builder**
  and its **Context Variables**.
- Relevant to **Nested Closure (Ch. 38)**, where bare functions inside a closure otherwise resolve in the
  closure's *defining* scope.
- `instance_eval` connects it to **Closure**, **Nested Closure**, and **Dynamic Reception (Ch. 41)**.

> **SDK lens:** This is the "configuration block / DSL block" family — Gradle build files, RSpec, JMock,
> Rails initializers, Kotlin receiver lambdas. It answers a real SDK question: how do you give users terse
> unqualified vocabulary without a global namespace and without global mutable state? Answer: bind the
> vocabulary to an instance and put the user's code inside that instance's scope. **The self-contained vs.
> fragmentary axis is the decision rule** — a standalone configuration file can afford (and benefits from)
> an implicit receiver; a few lines of SDK usage embedded in ordinary application code should not force an
> inheritance relationship or a rebound `this`. **Extensibility falls out for free**: user subclasses of
> the scoping base class extend the language, which maps directly to plugin and extension points,
> including "define a helper only this one config file needs." **Push boilerplate onto the library, not the
> user** — every declaration you force into user code is noise paid on every use site. And **the
> simplified-Boolean lesson generalizes hard**: your SDK's configuration surface does not have to expose
> every combination the model supports; constraining the surface trades expressiveness for a language
> people get right on the first try.

---

### Closure (Ch. 37)

> **Intent:** "A block of code that can be represented as an object (or first-class data structure) and
> placed seamlessly into the flow of code by allowing it to reference its lexical scope." *(Ch. 37,
> intent)*
>
> **Also known as:** lambda, block, anonymous function. *(Ch. 37, "Also known as")*

#### The concept

The motivating problem stated in the pattern header: "You have a collection of objects and want to filter
them in various ways. Writing a method for each filter leads to duplication in the setup and processing of
the filter. By using a Closure, you can factor the setup and processing of the filter and pass in an
arbitrary block of code for each filter condition."

Fowler's working definition: **"A Closure is a code fragment that can be treated as an object."** *(Ch. 37,
"How It Works")*

He develops it from the duplication problem. Two loops — one collecting heavy travelers, one collecting
managers — differ only in a Boolean test. "Removing that duplication is a simple thing to envisage, but
difficult to write in many languages because the thing that varies between the two code fragments is a
chunk of behavior — which is often not easy to parametrize." The classical OO answer is to make the
behavior an object: a filter interface plus a class per predicate. It works, but "there's so much code in
setting up the predicate object that the cure is worse than the disease" — especially when the predicate
needs a parameter, forcing a constructor and a field just to carry a threshold.

#### How it works

- **Terminology is a mess and Fowler says so.** "I use the term Closure in this book, but naturally there
  is no standard term for this language element. You also see them referred to as lambdas, anonymous
  functions, and blocks. Each language that uses them usually has its own term for them."
- **What makes it a closure specifically:** the block simply *uses* a local variable from the enclosing
  scope — "which saves all the faffing around with parameters that the predicate object version needed.
  This reference to variables in scope is what formally makes this expression a Closure. The delegate is
  said to close over the lexical scope of where it's defined. Even if we take the delegate and store it
  somewhere for later execution, those variables are still visible and usable… Both the theory and
  implementation of this are quite tricky — but the result is very natural to use."
- **Terseness is the whole ballgame.** Tracing C#'s evolution from handwritten predicate class to anonymous
  delegates to lambdas with type inference, he concludes: "You'll notice there's really little change here —
  the main factor is that the syntax is much more compact. This may be a small difference but it's a vital
  one. **The usefulness of Closures is directly proportional to how terse they are to use.**"
- **The libraries have to cooperate.** "This is an important point — for Closures to be really useful in a
  language, the libraries need to be written with Closures in mind." A language-level feature is worth
  little if the standard library predates it.
- **Deferred evaluation.** A closure created inside a factory function, capturing that function's
  parameter, can be stored in a field and evaluated arbitrarily later and arbitrarily often. "**This
  ability to create a block of code for later execution is what makes Closures so useful for Adaptive
  Models.**"
- **Language limits shape the API.** Ruby's pretty block syntax can only pass *one* closure into a
  function; passing multiple requires a less elegant syntax.

#### When to use it

Framed at two levels *(Ch. 37, "When to Use It")*:

- **General programming:** "Like many programmers who have used languages with good support for Closures, I
  find I miss them a great deal when using a language without them. They are a valuable tool to take chunks
  of logic and arrange them to eliminate duplication and support custom control structures."
- **In DSLs specifically:** "Closures play a couple of useful roles in DSLs. Most obviously, they are an
  essential element for Nested Closure. They also can make it easier to define an Adaptive Model."

#### Relationships

- Prerequisite for **Nested Closure (Ch. 38)**.
- Enables **Adaptive Model** — behavior held as data in the semantic model, evaluated later.
- The **preferred alternative to Macro (Ch. 15)** for deferred evaluation.
- Interacts with **Object Scoping** in languages that can rebind a closure's execution context.

> **SDK lens:** Callbacks, handlers, predicates, and interceptors as first-class parameters are the single
> most common way SDKs let users inject behavior. Two uses dominate. **Custom control structures**: the SDK
> owns setup and teardown, the user supplies the middle — retry policies, transactions, connection scoping,
> resource lifetimes, instrumentation spans. This is the mechanism behind context-manager-shaped APIs.
> **Deferred/lazy evaluation**: accepting a closure rather than a value lets the SDK decide *whether* and
> *how many times* to evaluate — essential for retries, lazy config, conditional expensive computation, and
> rule engines. Two constraints worth carrying: (1) a closure-taking API is only pleasant if the host
> language's closure syntax is terse, which is a legitimate reason for language-specific SDK surfaces to
> differ; (2) your *whole library* must be designed for closures, not just one entry point, or users get a
> fluent island in an imperative sea.

---

### Nested Closure (Ch. 38)

> **Intent:** "Express statement subelements of a function call by putting them into a closure in an
> argument." *(Ch. 38, intent)*

#### The concept

Nested Closure is Nested Function with the children wrapped in a closure. Fowler's minimal contrast
*(Ch. 38, "How It Works")*:

```
processor(cores(2), i386)        # Nested Function
processor { cores 2; i386 }      # Nested Closure
```

"Instead of passing two Nested Function arguments, I pass a single Nested Closure argument which contains
the two Nested Functions."

#### How it works

**The central mechanic: you control evaluation.** "Placing the subelements in a Nested Closure has an
immediate consequence for my implementation — I have to put in code to evaluate the closure. With a Nested
Function, I don't need to do this since the language automatically evaluates the `cores` and `i386`
functions before calling the `processor` function. With a closure argument, the `processor` function is
called first and the closure is only evaluated when I explicitly program it to. So, usually I'll evaluate
the closure within the body of the `processor` function. **The `processor` function can also carry out
other tasks before and after the closure evaluation, such as setting up Context Variables**" *(Ch. 38,
"How It Works")*.

That before/after capability is the whole value proposition, and its most important application is stated
immediately:

> "One of the problems of a Function Sequence is that the multiple functions communicate using hidden
> Context Variables. While you still have to do this inside a Nested Closure, the `processor` function can
> create the Context Variable before evaluating the closure and tear it down afterwards. This can greatly
> reduce the problem of Context Variables appearing all over the place." *(Ch. 38, "How It Works")*

**What can go inside the closure** — three shapes:

1. **Function Sequence** — the base case; the parent brackets it with Context Variable setup/teardown.
2. **Method Chaining** — "Here, there is the additional benefit that the parent function can set up the
   head of the chain and pass it into the closure as an argument."
3. **Function Sequence with an explicit Context Variable passed as the closure argument** — "In this case,
   we have a Function Sequence but with the Context Variable explicitly present. This often makes it easier
   to follow, without adding too much clutter."

**Scoping.** "Bare functions written inside a Nested Closure are evaluated in the scope where they are
defined — so, again, it's usually wise to use Object Scoping. Passing in an explicit Context Variable or
using Method Chaining allows you to avoid this, as well as to organize the builder code into different
builders."

**Multiple closures.** "It's also possible to use multiple closures. The advantage of this is that it
allows you to evaluate each subclosure independently." The canonical case is a conditional with two
branches, where evaluating both would be wrong.

#### The delimiters are not noise

Fowler puts the Nested Closure script and the plain Function Sequence script side by side; they are
character-for-character identical except for the added closure delimiters *(Ch. 38, "Wrapping a Function
Sequence in a Nested Closure (Ruby)")*:

> "From the script's point of view, the only change with Nested Closure is to add the `do…end` closure
> delimiters. By adding these, I introduce an explicit hierarchic structure to what otherwise is a linear
> sequence with a formatting convention. The extra syntax doesn't strike me as troubling because it's
> marking the structure from the reader's point of view and in a way that makes sense to the reader."

This is the sharpest statement in the part of *why* structure-in-code beats structure-in-indentation: the
delimiters are the reader's own mental structure made real.

A concrete payoff of splitting into child builders inside closures: "it also allows me to use an unqualified
`speed` method for both the processor and the disk without ambiguity" *(Ch. 38, "Using Method Chaining
(Ruby)")*. Compare the Function Sequence version, where `speed()` had to branch on Context Variables to
decide what it meant. **Splitting into builders replaces runtime disambiguation with structural
disambiguation.**

Fowler is also candid that the pattern reads better in some languages than others: "To my eyes, Nested
Closure works much less well in C# than it did in Ruby. Ruby's `do…end` closure delimiters flow more
naturally to me than C#'s `() => {…}`… The more used you are to C# notation, the less that will bother you"
*(Ch. 38, "Simple C# Example (C#)")*.

#### Self-contained vs. fragmentary, and the instance_eval reversal

The chapter's best judgement call *(Ch. 38, "Using Instance Evaluation (Ruby)")*.

Instance evaluation lets you have multiple builders *and* bare calls: each clause method creates the child
builder and evaluates the block against it, so the same bare name means different things at different
depths. "In effect, using `instance_eval` changes what `self` refers to inside the passed-in block." For a
self-contained script file it also removes all the head/tail noise of Object Scoping.

It looks like a free win. It isn't:

> "Using `instance_eval` seems such a good trick that you may wonder if you should ever pass explicit
> closure arguments. As it turns out, there is a very real choice, one that was crystallized for me by Jim
> Weirich's experience with his builder library… In the first version of the library, Jim used
> `instance_eval`, but later switched to explicit parameters. The reason is that **programmers are used to
> the call behavior with closures; redefining `self` causes a lot of confusion and makes it very difficult
> to refer to elements in the static context that you need.**"

Fowler's resolution is the self-contained/fragmentary rule:

> "For me, the choice lies in whether you are using the DSL script in a self-contained or fragmentary
> style. In a fragmentary context, you need to follow the usual conventions with closures, so redefining
> `self` though `instance_eval` is not a good choice. With self-contained DSL scripts, your code style is
> different from regular Ruby code; the redefinition then doesn't cause confusion and is worth it to
> remove the noisy references."

The related tradeoff, stated by Fowler as what real Ruby DSLs actually do: they use Function Sequence
within each closure but pass an explicit closure argument. "Although this adds more text to the statement,
it results in a more regular style of code that rubyists find easier to work with" *(Ch. 38, "Function
Sequence with Explicit Closure Arguments (Ruby)")*. **Explicit receivers cost characters and buy
regularity, multiple builders, and fragmentary usability.**

#### When to use it

- The core claim: "Nested Closure is a useful technique because it combines the explicitly hierarchic
  structure of Nested Function with the ability to control when the arguments are evaluated. Control of
  evaluation provides you with a lot of flexibility, helping you to avoid many of the limitations of Nested
  Function" *(Ch. 38, "When to Use It")*.
- The core limitation is the host language: "Many languages don't provide closures at all. Those that do
  often provide the syntax in a way that doesn't jive terribly well with DSLs, such as with an awkward
  keyword."
- **Best mental model — it's an enhancement, not a rival:** "It's usually worth thinking of Nested Closure
  as an enhancement to Nested Function, Function Sequence, and Method Chaining. The explicit control of
  evaluation gives you different advantages with each technique. All of these, however, boil down to the
  fact that you can do specific setup and tear-down operations on either side of the closure invocations."

#### Relationships

- Built on **Closure (Ch. 37)**.
- An *enhancement* to **Nested Function**, **Function Sequence**, and **Method Chaining**, not a competitor.
- Tames **Context Variables** by scoping their lifetime to the closure invocation.
- Interacts with **Object Scoping**: needed for bare calls inside closures, or bypassed via explicit closure
  arguments.
- Solves Method Chaining's **finishing problem** (the enclosing call terminates) and Function Sequence's
  Context Variable sprawl.

> **SDK lens:** This is the "configuration block" API — `resource("x") { … }`, `with_transaction { … }`,
> Kotlin's receiver lambdas, Gradle's DSL. **Setup/teardown around the closure is the SDK superpower**: it's
> exactly what makes context-manager APIs work, and it's the same mechanism that scopes "which object am I
> configuring" to a lexical block instead of to a mutable field. If you have a builder with a `currentThing`
> field, a block-scoped API removes it. **It fixes hierarchy and finishing at once** — the block delimits the
> subexpression, so there is nothing to `.end()` and the nesting is real; if your chained API is drowning in
> terminator calls and context variables, the block form is the refactoring. **Explicit vs. implicit receiver
> is a genuine, load-bearing decision**: explicit costs characters, preserves normal scoping intuitions, works
> in fragmentary use, and enables multiple cohesive builders; implicit is terser for standalone config files
> but surprises readers and breaks access to the enclosing lexical context. Fowler's rule — implicit for
> self-contained scripts, explicit for fragmentary use — is directly usable, and Weirich's reversal is the
> cautionary tale. Finally, **language ergonomics legitimately drive API shape**: Fowler's own conclusion that
> the pattern works less well in C# than Ruby is permission to design differently per language binding rather
> than mechanically porting one surface everywhere.

---

### Choosing among the fluent techniques

The seven patterns above are not alternatives to be picked by taste. Fowler chooses between them by writing
the grammar production the clause must satisfy and reading off the technique that fits.

#### The grammar → technique mapping

| Grammar shape | Recommended technique | Why |
|---|---|---|
| `parent ::= first second` (fixed, mandatory children) | **Nested Function** | The parent's signature declares exactly the required arguments and, when statically typed, their types *(Ch. 34, "How It Works")* |
| `parent ::= (this \| that)*` (heterogeneous, repeatable, unordered) | Nested Function's **worst case** — forces intermediate tokens or a Context Variable; prefer **Literal Map** / keyword args, or **Method Chaining** | With no keyword arguments, arguments can only be identified by position and type, "downright impossible if `this` and `that` have the same types" *(Ch. 34, "How It Works")* |
| `parent ::= child*` (homogeneous repetition) | **Literal List** / varargs, usually nested inside a Nested Function | *(Ch. 34, "How It Works"; Ch. 39, "When to Use It")* |
| Mostly-optional clauses, any subset | **Method Chaining** | "Method Chaining easily allows a DSL script writer to pick and choose clauses" *(Ch. 35, "When to Use It")* |
| Mandatory clauses, or a required *order* of clauses | **Nested Function**, or Method Chaining + **progressive interfaces** | Plain chaining can never require a clause; progressive interfaces enforce ordering and can enforce a mandatory element via an interface exposing only it *(Ch. 35, "Progressive Interfaces" / "When to Use It")* |
| Hierarchy that must be structural, not cosmetic | **Nested Function** or **Nested Closure** | Function Sequence and Method Chaining only *suggest* hierarchy through indentation *(Ch. 35, "Hierarchic Structure")* |
| A top-level list of statements | **Function Sequence** (with Object Scoping), or a Function Sequence inside a **Nested Closure** | Only one result list and one Context Variable needed *(Ch. 33, "When to Use It")* |

The decision sequence Fowler actually argues, in order:

1. **Start with an Expression Builder.** Default; keep the fluent layer off the Semantic Model *(Ch. 32,
   "When to Use It")*.
2. **You must start the DSL with a Function Sequence of at least one call**, because every other technique
   needs a context to hang off *(Ch. 33, "When to Use It")*.
3. **Below the top level, avoid bare Function Sequence.** It's the least useful combination and it forces
   Context Variables *(Ch. 33, "When to Use It")*.
4. **Mandatory / hierarchical / fixed-shape → Nested Function** *(Ch. 34, "When to Use It")*.
5. **Optional / pick-and-choose → Method Chaining**, accepting that you can't require anything, you'll
   manage hierarchy yourself, and you'll face the finishing problem *(Ch. 35, "When to Use It")*.
6. **Need order or requirement *and* you're chaining → progressive interfaces** (or child builders)
   *(Ch. 35, "Progressive Interfaces")*.
7. **Lots of optional, unordered, heterogeneous arguments → Literal Map / keyword arguments**, not Nested
   Function *(Ch. 34, "When to Use It")*.
8. **Bare calls without globals → Object Scoping** — unless your bare functions are pure value-returning
   statics, in which case you may not need it *(Ch. 36, "When to Use It"; Ch. 34, "How It Works")*.
9. **Need control over *when* things evaluate, or want to bracket setup/teardown, or are drowning in
   Context Variables → Nested Closure** *(Ch. 38, "When to Use It")*.
10. **Fragmentary usage constrains everything.** Inheritance-based Object Scoping and implicit-receiver
    tricks are for self-contained scripts; fragmentary DSLs need explicit receivers and no inheritance
    requirement *(Ch. 36 and Ch. 38, "When to Use It")*.

#### The evaluation-order tradeoff

Every technique here is really a choice about *when* subexpressions run:

- **Function Sequence and Method Chaining evaluate left-to-right.** Natural for a sequence of commands, and
  natural for reading; but nothing is assembled until the end, so structure must be reconstructed from
  accumulated state.
- **Nested Function evaluates arguments before the enclosing call — inside-out.** Perfect for building a
  hierarchy of values (children return fully formed objects that the parent assembles), which is why it
  needs no Context Variables and has no finishing problem. Wrong for command sequences, where it produces
  the Old MacDonald problem *(Ch. 34, "When to Use It")*.
- **Nested Closure lets the parent decide when — and whether, and how often.** That single capability buys
  setup/teardown bracketing, Context Variable lifetimes bounded by a block, chain heads passed in as
  arguments, and independent evaluation of alternative branches *(Ch. 38, "How It Works")*.

#### The context-handling arc

| Pattern | How context is carried | Cost |
|---|---|---|
| Function Sequence | Context Variables on the builder (or, badly, statics) | Ambiguous clause names, runtime dispatch, order-dependence, thread hazards |
| Nested Function | Return values of the argument functions | None — but rigid shape, poor optionality |
| Method Chaining | Context Variables *or* child builders | Fiddly; child builders must forward parent punctuation |
| Object Scoping | Instance fields of the scoping builder | Constrains where the script may live |
| Nested Closure | Closure argument, or Context Variables scoped to the closure's lifetime, or a rebound receiver | Language-dependent syntax; receiver rebinding surprises readers |

The trajectory of the whole part: **push context out of global state, into instances, then into return
values or lexically scoped blocks.** Each step trades a bit of syntax for a large reduction in the class of
bugs available. That arc — globals → instances → return values → lexically scoped blocks — is a usable
maturity ladder for any configuration API.

#### The finishing problem, restated

Only left-to-right techniques have it. Method Chaining must return a builder from every call to keep the
chain alive, so no call can return the finished product and nothing marks the end *(Ch. 35, "Finishing
Problem")*. Nested Function and Nested Closure don't have the problem at all, because the enclosing call's
closing bracket *is* the terminator and its return value *is* the product. When you find yourself designing
a `.end()` or `.build()`, that is the moment to check whether an enclosing-call form would serve better —
Fowler's own recommendation is that "usually if you run into this you're better off using a Nested Function
or Nested Closure" *(Ch. 35, "When to Use It")*.

#### The convention violations Fowler licenses — inside the fence

Fluent layers earn a license to break normal API rules, and the license is granted by — and only by —
isolation in an Expression Builder. The violations he explicitly endorses:

- **Mutators that return values**, breaking command-query separation *(Ch. 35, "How It Works")*.
- **Query-shaped names for commands** — a `sata()` that sets rather than asks *(Ch. 35, "How It Works")*.
- **Property getters that mutate and return `this`** — "this abomination," acceptable only "when clearly
  placed in a fluent context" *(Ch. 35, "Chaining with Properties (C#)")*.
- **Separate methods where a parameter would be correct design** — `First()` and `Third()` rather than one
  method with an index *(Ch. 34, "Recurring Events (C#)")*.
- **A DSL structure that inverts the model's structure** — "and" in the language meaning `Or` in the
  specification, so that both the language and the model read naturally *(Ch. 34, "Recurring Events (C#)")*.
- **A DSL deliberately less expressive than its own model** — conjunction-only rules over a model that
  supports arbitrary Booleans *(Ch. 36, "Security Codes (C#)")*.
- **Naming rules bent for the script reader** — plural type names, builders named for how they read rather
  than what they are *(Ch. 34, "Recurring Events (C#)"; Ch. 44, "How It Works")*.

The unifying rule: **optimize the fluent layer for the reader of the script, and pay for that by
quarantining it away from every object the reader of ordinary code will touch.** The corollary is a
practical review question for any SDK: *if a user obtained this object from somewhere other than the fluent
chain, would its interface confuse them?* If yes, the fluent methods are on the wrong class.

---

## 11. Expressive-vocabulary patterns and their judgement calls

The last eight patterns of Part IV are about *vocabulary* rather than *combination*: how you express lists
and named options, how far you can bend method names and literals, how to attach declarative metadata, and
how much cleverness is too much. Fowler's tone changes noticeably here. Several of these chapters are
warnings dressed as patterns, and the warnings are the most valuable content in them.

---

### Literal List (Ch. 39)

> **Intent:** Represent a language expression with a literal list. *(Ch. 39)*

#### The concept

A Literal List is just the host language's built-in syntax for constructing a list/array inline. As a DSL
construct, you use it to hold the children of some parent element, and a parent function then walks the
list and processes the elements. Because most such syntaxes nest, you can build tree-shaped expressions out
of them — one way of looking at an entire Lisp program is as a nested list.

#### How it works

- The list is almost always **used inside a function call**; the function receives it and interprets it.
  **The list itself carries no semantics — the enclosing function supplies them** *(Ch. 39, "How It Works")*.
- **Not all languages have a usable one.** Mainstream C-derived languages have literal arrays but these
  frequently accept only constants/literals, not arbitrary symbols or expressions, which kills their
  usefulness for DSL work.
- **Varargs as a substitute.** A variadic call — `companions(jo, saraJane, leela)` — is effectively a
  Literal List with the parent function baked into the syntax. In a strongly typed language all elements
  must share a type to fit through a varargs parameter, which is a real constraint on heterogeneous content.

#### When to use it

- Good when the list sits **nested inside another element**, typically a function call, and the grammar you
  want is essentially `parent ::= child*` *(Ch. 39, "When to Use It")*.
- Often the items are themselves function calls, which is exactly what makes **Nested Function** workable —
  the two are natural partners.
- **Prefer varargs over an explicit literal list when the list is an argument.** Fowler is explicit: even
  when the host language *has* literal list syntax, he prefers `companions(jo, saraJane, leela)` to
  `companions([jo, saraJane, leela])`. The brackets are pure noise when the function boundary already
  delimits the list.
- You *can* write an entire DSL using nothing but Literal Lists — that is essentially Lisp. His verdict:
  natural in Lisp, but "little more than a fun exercise in other languages where it's more natural to
  combine lists with other forms of expression."

#### Relationships

- Pairs with **Nested Function (Ch. 34)**.
- Degenerate/adjacent form of **Literal Map (Ch. 40)** — if you have lists but not maps, you can encode maps
  as lists of key/value sublists.
- Contrast with **Method Chaining** and **Function Sequence** as alternative ways to express "a parent with
  many children."

> **SDK lens:** The "prefer varargs to an explicit collection literal" rule is a durable API heuristic: when
> a parameter is conceptually "zero or more of X", a variadic signature reads better than forcing callers to
> build a collection — *provided* the elements are homogeneous. The moment they aren't, the type system
> pushes you toward an options object instead. The deeper point is that a bare list carries no meaning of its
> own; whatever the elements mean comes from the function receiving them, so a list parameter is only as
> clear as the name of the function it sits inside.

---

### Literal Map (Ch. 40)

> **Intent:** Represent an expression as a literal map. *(Ch. 40)*

#### The concept

A Literal Map is the host language's inline dictionary/hash syntax. Used in a DSL, it's the "named options"
construct: a function takes a map and pulls named values out of it. Where Literal List expresses "a sequence
of children", **Literal Map expresses "a set of distinct named attributes, each appearing at most once."**

#### How it works

- Normally used in a function call where the function receives the map and processes it.
- **The central weakness is key validation.** In a dynamically typed language there is no way to communicate
  or enforce the valid set of keys. You must write the checking code yourself, *and* there is no mechanism to
  tell the DSL author which keys are correct — **no discoverability**. A statically typed language can dodge
  this by defining an enum of legal key types *(Ch. 40, "How It Works")*.
- **Keys should be symbols** where the language has them (or strings otherwise). Symbols are the natural
  choice and easy to process; some languages provide shorthand syntax for symbol-keyed maps.
- **Keyword arguments are a superior form of Literal Map.** Just as Fowler treats a varargs call as a form of
  Literal List, he treats a call with keyword arguments as a form of Literal Map — and says keyword arguments
  are *better*, because they often let you declare the valid keywords. "Sadly, keyword arguments are even
  rarer than a literal map syntax."
- **Fallbacks when the language lacks map literals:** encode maps as literal lists, or use alternating
  key/value arguments.
- **Delimiter elision.** Some languages let you drop the braces when the map is the only thing in that
  position. Worth exploiting — it removes a whole layer of punctuation noise.

#### Validate the keys — the actionable rule

Because maps give you no key checking, the worked example adds a `check_keys` helper that diffs the supplied
keys against an explicit whitelist and raises a dedicated exception **naming the unrecognized keys**. Without
it, a typo silently does nothing. Fowler frames this as unavoidable overhead: "The danger with using a map
like this is that it's easy for the caller to introduce an incorrect key by accident, so it's worth doing a
little checking here" *(Ch. 40, "The Computer Configuration Using Lists and Maps (Ruby)")*.

The same example demonstrates that a good internal DSL **mixes techniques**: one function takes a Literal
List (varargs), two take Literal Maps, and the whole script is evaluated with Object Scoping.

#### Greenspun form — purity as a diagnostic, not a goal

Fowler pushes a single technique as far as it goes "just to get a sense of its capabilities," explicitly
framed as an exercise rather than a recommendation *(Ch. 40, "Evolving to Greenspun Form (Ruby)")*:

1. **Lists + maps only.** Replace every function call with a Literal List whose head element is a symbol
   naming the construct and whose tail is the arguments. The script becomes a pure nested data structure,
   processed by evaluating the host-language code to get the structure and handing it to an interpreter
   written as a **Recursive Descent Parser**. Notable consequence: **you gain complete control over order of
   evaluation**, because nothing executes until your interpreter walks the structure. "In many ways, this DSL
   script is like an external DSL encoded in internal literal collection syntax instead of a string."
2. **Lists only ("Greenspun form").** Replace each map with a list of two-element key/value sublists — a wink
   at Greenspun's Tenth Rule. Using only lists yields a *more regular* script, but a list of pairs
   masquerading as a map fits the host language's style badly.
3. **Verdict:** "Either case isn't as good as the earlier example which mixed function calls with literal
   collections." The nested-list style is natural precisely in Lisp, where bare words are symbols by default.

**The extracted principle:** purity in one technique is a diagnostic exercise, not a goal. Mixed-technique
DSLs read better, and when a construct starts fighting the host language's idiom, that friction is the signal
to stop.

#### When to use it

"Literal Map is a great choice when you need a list of different elements where each element should appear no
more than once." The lack of key validation is annoying, but the syntax is usually still the best choice for
this shape of problem: it *communicates clearly* that each subelement is at-most-once, and the map is the
ideal structure for the receiving function. If you don't have Literal Maps, fall back to **Literal List**,
**Nested Function**, or **Method Chaining** *(Ch. 40, "When to Use It")*.

#### Relationships

- Complement of **Literal List**; both usually consumed by **Nested Function**.
- Alternatives when unavailable: **Nested Function**, **Method Chaining**.
- The full-list form leads directly into **Recursive Descent Parser** territory.

> **SDK lens:** This is the **options-object / kwargs API** pattern, and Fowler's critique is exactly the
> modern one: options bags trade discoverability for expressiveness — users cannot see the valid keys, IDEs
> cannot complete them, and typos fail silently. Therefore: **validate keys explicitly and fail loudly with a
> message that names the offending keys.** That is the single most actionable takeaway of the chapter for
> library authors. **Prefer real keyword parameters, a typed options struct, a TypedDict, or an enum-keyed
> map to a free-form map** wherever the language offers them, because they restore the declared-valid-key
> property a raw map throws away. And use the shape rule to decide when an options object is even right: it
> fits "many distinct, independent, at-most-once named attributes" — nothing else.

---

### Dynamic Reception (Ch. 41)

> **Intent:** Handle messages without defining them in the receiving class.
> *Also known as:* overriding `method_missing` / `doesNotUnderstand`. *(Ch. 41)*

#### The concept

Every object has a finite set of defined methods. Statically typed languages catch calls to undefined methods
at compile time; dynamic languages fail at runtime. Dynamic Reception hijacks that failure path: you override
the language's "unknown message" hook so your object can respond meaningfully to method names you never
declared. In effect you are **dynamically altering the rules for reception of method calls**.

#### How it works

- The hook lives at the top of the object hierarchy. You override it in your own class.
- **General (non-DSL) use case:** automatic delegation — define the methods you handle yourself and route
  everything unknown to a delegate.
- **DSL use case 1 — move parameters into the method name.** The canonical example is Active Record's dynamic
  finders: a `find_by_firstname_and_lastname(...)` call is not defined anywhere; the superclass checks for the
  `find_by` prefix, parses the method name to extract property names, and builds a query. You *could* pass the
  names as arguments, but embedding them in the method name reads better — it mimics what an explicitly
  defined method would look like. Conceptually: "Essentially, you are embedding an external DSL in the method
  name" *(Ch. 41, "How It Works")*.
- **DSL use case 2 — a sequence of Dynamic Receptions.** Instead of one parsed name, chain them:
  `find_by.firstname("martin").and.lastname("fowler")`, or fully bare,
  `find_by.firstname.martin.and.lastname.fowler`. Here the first call returns an **Expression Builder** and
  you compose with **Method Chaining** plus Dynamic Reception.
- **Removing quotes.** A major payoff: parameters no longer need quoting. Combined with **Object Scoping**,
  you can accept bare identifiers for arguments by implementing Dynamic Reception in the superclass so that
  after a keyword method is invoked, the *next* unknown method call is captured as the value. **Textual
  Polishing (Ch. 45)** can strip yet more punctuation.

#### When to use it — the governing rule

This is one of the richest "when to use it" sections in Part IV.

**Reasons it's appealing** *(Ch. 41, "When to Use It")*:

1. **It mimics real methods at a fraction of the effort.** It's entirely reasonable for a `Person` class to
   have a `find_by_firstname_and_lastname` method; Dynamic Reception provides it without your writing it — a
   significant time-saver when there are many combinations.
2. **Punctuation consistency.** An all-dots form means users never wonder when to use a dot vs. parentheses
   vs. quotes. **But Fowler dissents on this one:** "For many others, this consistency isn't a virtue; I like
   separating what is schema from what is data, so I prefer the way `find_by.firstname("martin")…` puts field
   names into method calls and the data into parameters." *Structure in the method names, values in the
   arguments.*

**Alternatives to weigh first:** attribute names as parameters; a closure predicate; or a fragmentary external
DSL in a string. Fowler concedes many people nonetheless find the method-name form most fluent.

**The governing rule:**

> "Above all, it's important to remember that Dynamic Reception only pays its way when it allows you to build
> these structures **in general, without any special case handling**." *(Ch. 41, "When to Use It")*

Corollaries he draws:

- It's only worthwhile when there is a **clear, mechanical translation** from the dynamic method name to
  methods that already exist for other purposes. The dynamic finder works precisely *because* the class
  genuinely has those attributes.
- **"If you need to write special methods to handle particular cases of Dynamic Reception, that usually means
  you shouldn't be using Dynamic Reception."** The moment you're special-casing, the generality that justified
  the magic has evaporated.

**The costs and hard limits:**

- **Impossible in static languages** at all.
- **Debuggability.** "Once you override the handler for unknown method invocations, any mistake can lead you
  into deep debugging trouble. **Stack traces often become impenetrable.**" This is the price, and you should
  be sure the fluency gain is worth it.
- **Encoding limits.** Program text and string data often use different encodings; many languages allow only
  ASCII in identifiers, which breaks for non-ASCII personal names. Language grammar rules for method names may
  also exclude legitimate data values.
- **Expressiveness limits.** A comparison like `...greater_than.2` fails because most dynamic languages won't
  allow a digit there; the workaround "obstructs much of the fluency that you're doing it for."
- **Not for complex Boolean composition.** Fine for a two-condition conjunction, but by the time you reach
  nested likes, comparisons, and negations "you're running down a road that forces you to implement a kludgy
  parser in an environment not well-suited for it."

#### The layering principle — the Active Record lesson

The complexity ceiling is *not* an argument against using Dynamic Reception for simple cases. Active Record
deliberately supports dynamic finders for simple cases and *deliberately does not* support more complex
expressions, pushing users to a different mechanism instead.

> "Some people don't like that, preferring a single mechanism, but I think it's good to realize that
> **different solutions may work best at different complexities, so you should provide more than one.**"
> *(Ch. 41, "When to Use It")*

The same lesson appears from the model side: "The underlying model allows me to have any kind of condition as
long as it knows how to match an itinerary." Some conditions come in through the DSL; others through a
closure-backed condition object. "This kind of flexibility can be quite important. It allows people to use the
DSL to handle simple cases simply, but provides an alternative mechanism to handle more complicated cases"
*(Ch. 41, "Promotion Points Using Parsed Method Names (Ruby)")*.

#### Containment techniques from the examples

- **Delegate unknown names upward.** If the prefix doesn't match, call the superclass handler, so genuinely
  unknown methods still produce the language's normal error. Essential hygiene: don't swallow every message.
- **Validate arity and shape yourself.** The example checks that the number of attribute names parsed from the
  method name matches the number of arguments, and throws a clear error otherwise. With dynamic reception you
  are writing your own signature validation.
- **Use the open-ended mechanism only where the vocabulary is open.** In the chaining example, the
  attribute-name and value builders use dynamic reception; the *operator* builder, with its fixed operator
  set, uses ordinary defined methods. "This is the cleanest statement in the chapter of how to keep magic
  proportional" *(Ch. 41, "Promotion Points Using Chaining (Ruby)")*.
- **Scope the magic with per-section builders.** In the state-machine example, each section evaluates its block
  in the context of a *different, tiny* builder whose handler interprets every call as a declaration of that
  one kind. "By using a different builder, I can keep each one simple and clearly scope what each builder is
  recognizing" *(Ch. 41, "Removing Quoting in the Secret Panel Controller (JRuby)")*.
- **Two-stage evaluation handles forward references.** State bodies are not evaluated when declared; the
  closure is stored and processed in a postprocessing pass. "By deferring the evaluation till later, I can
  avoid worrying about the forward references between states" — all states are declared and the Symbol Table
  fully populated before any body referring to another state runs.

#### Two verdicts worth memorizing

- "Making little parse trees like this isn't a common way to do an internal DSL; it's usually easier to just
  build the model up as you go. But with a conditional expression like this, it makes sense."
- **"Overall, however, I'm not too keen on building up expressions using this approach. It seems to me that
  once you start parsing sequences of method calls like this, you might as well just switch to an external DSL
  where you get more flexibility. The desire to build up parse trees is a smell indicating that the internal
  DSL is doing too much work."** *(Ch. 41, "Promotion Points Using Chaining (Ruby)")*

And the honest cost/benefit summary on the state machine: "The question, of course, is whether it's worth the
trouble. To my eye, I like the way the event and command list turn out, but I'm not so keen on the states." His
recommendation is a hybrid — dynamic reception where it genuinely helps, plain symbol references where it
doesn't: **"A mixture of techniques is often the best bet."**

#### Relationships

- Usually combined with **Expression Builder**, **Method Chaining**, **Object Scoping**, **Symbol Table**,
  **Context Variable**.
- **Textual Polishing (Ch. 45)** removes further punctuation once Dynamic Reception has removed the quoting.
- Its failure mode points at **external DSLs** / **Recursive Descent Parser**.

> **SDK lens:** This is the `__getattr__` / `method_missing` / JS `Proxy` dynamic-attribute API pattern, and
> Fowler's rules translate directly. (1) **Only use it when the mapping is fully general** — if you're writing
> `if name == "foo"` inside your hook, define `foo` properly. (2) **Always delegate unhandled names to the
> default error path.** Never let an unknown attribute silently return null or a no-op builder. (3) **Budget
> for debuggability** — impenetrable stack traces are the real recurring cost, paid by every future user
> debugging through your hook. (4) **Scope the magic**: per-section builders, each recognizing one open
> vocabulary, beat one god-object that answers to everything. (5) **Validate arity and shape yourself**, with
> an error message naming the method and what was expected; the compiler is no longer doing it for you.
> (6) **Layer the API deliberately** — provide a magic path for the simple 80% and a distinct explicit
> mechanism (closures, a builder, a query object) for the complex 20%; supporting more than one mechanism at
> different complexity levels is a feature, not an inconsistency. (7) **Data does not belong in identifiers**
> when it may be non-ASCII, contain digits, or otherwise violate identifier grammar — keep schema in names,
> values in arguments.

---

### Annotation (Ch. 42)

> **Intent:** Data about program elements, such as classes and methods, which can be processed during
> compilation or execution. *(Ch. 42)*

#### The concept

We routinely classify data in our programs and write rules about the classifications. Sometimes we want to
classify *elements of the program itself*. Languages already provide some built-in mechanisms — access
controls like public/private mark methods. But we frequently want to mark things beyond what a language
supports, or reasonably *should* support: restrict the values a field may take, mark methods to be run as
tests, indicate that a class can safely be serialized.

> "An Annotation is a piece of information about a program element. … Annotations thus provide a mechanism to
> extend the programming language." *(Ch. 42)*

Crucially, **the concept is broader than any special syntax** — the same benefits are achievable without it.

In DSL terms: the annotation-defining syntax *is* an internal DSL, and it develops a **Semantic Model** by
attaching data to the runtime model of the program that's built into the language. Later processing steps
correspond to running that model — which, as with any DSL, can mean execution or code generation.

#### Defining an annotation — four techniques

In decreasing order of language support *(Ch. 42, "How It Works")*:

1. **Purpose-designed syntax** (`@Test`, `[Test]`), with parameters. Most obvious, often easiest.
2. **Class methods called in the class body** — a declaration call that receives the name of the field plus
   the data, and either stores the raw data or directly constructs processor objects. "Using class methods
   like this can be almost as easy as using purpose-designed syntax." Biggest issue: the call must be given
   the **name of the element it annotates**, adding verbiage. But that also buys freedom: you can **separate
   the annotations from the annotated declarations**. "That is a big payoff for languages that make this easy
   — there's little need to provide a special annotation syntax." Practical gotchas: the annotations must
   actually *execute* to be stored, and class-level storage is often shared between a class and its
   subclasses, which is a real hazard.
3. **Marker interface** (statically typed languages): an interface with no methods; implementing it tags the
   class. **Only works on classes**, not methods or fields.
4. **Naming conventions.** The simplest form — early xUnit tagged test methods by requiring names begin with
   `test`. Works well for simple annotations, but "multiple annotations are difficult to support and
   parameters are practically impossible."

**A structural limitation unique to Annotations.** Beyond the usual internal-DSL limit (your syntax is bounded
by the host language's), annotations carry an additional one: the Semantic Model must be based on the
program's own fundamental representation — classes, fields, methods. The annotation Semantic Model is a
*decoration* of that structure. **"You can't practically build a completely separate and independent Semantic
Model."** *(Ch. 42, "How It Works")*

#### Processing annotations

Annotations are written in source but consumed later — at compilation, at load, or during runtime *(Ch. 42,
"Processing Annotations")*.

- **Runtime processing is the most common case**: a test runner finding and running test methods; a database
  mapper interrogating field annotations to discover the mapping to persistent storage.
- **Processing can be split across phases.** Validation annotations can be *partially* processed at startup to
  create validator objects attached to classes, which then validate objects during execution — cache the
  expensive reflection once, run the cheap check many times.
- **Runtime processing ≈ model execution; the alternative is code generation.** In a dynamic language, code
  generation can happen at runtime, generating new classes or adding methods to existing ones.
- **Compiled languages** make runtime generation awkward. Options: compiler hooks for annotation processing;
  generating code *before* compilation (but "such intimate intermixing of written and generated code can be
  confusing"); or **bytecode postprocessing**.
- **One definition, many processors — the killer application.** In a web app you want field validations
  enforced in the browser (for responsiveness) *and* on the server (because you can never trust the browser).
  With Annotation you create a runtime check for the server and generate JavaScript for the browser without
  duplicating code: "Both checks can be fully derived from a single Annotation."

#### When to use it

Fowler opens with unusual candour: "The wide-scale use of Annotations is still relatively new in mainstream
programming languages. We are still learning when best to use them."

**The key property:**

> "The key feature of Annotations is that they allow you to separate definition from processing." *(Ch. 42,
> "When to Use It")*

The validation example makes the case concrete. The obvious way to enforce a valid range is inside the setter
— but that **fuses the definition of the constraint with the moment it's enforced**, so validation necessarily
happens on every value change. There are many cases where you want to check constraints at other times:
letting a user fill in a form and only validating on submit. A whole-object `validate` method helps, but
you're still defining the constraints in the same place they're checked. **Separating the two lets you:** check
constraints at different times; apply *different subsets* of constraints at different times; and make the code
clearer, because the constraint definitions stand alone.

**The decision rule:** "The strength of Annotations lies where it makes sense to separate definition and
processing." Two motivations qualify — you want the *processing* to vary independently of the definition, or
you want the *definition* to be easier to understand by standing alone.

**The downside:** "it is more awkward to follow both definition and processing. If you need to understand them
together, Annotations force you to look in two disconnected places. The processing code is also generic, which
may make it even harder to follow."

#### The declarative-only corollary

This is a hard design rule for any declarative API:

> "The definition of an Annotation should be **declarative and not involve any logic flow**. Furthermore, it
> shouldn't imply any ties to when the processing logic occurs, or any ordering of processing Annotations
> attached to the same or different program elements." *(Ch. 42, "When to Use It")*

Three prohibitions in one sentence: no control flow inside the declaration; no assumption about *when* the
processor runs; no ordering dependency between annotations. Violate any of them and you have built a trap that
looks like a declaration.

**A related aside worth keeping** *(Ch. 42, Java example)*: having an object validate itself is not always the
right strategy. "When you validate something, you always do so for a context, and that context is usually some
action involving that object." Self-validation implies the validation is correct for every context the code is
used in — sometimes true, often not.

**Decouple annotation from processor.** In the worked example the annotation-to-processor link is a
**dictionary lookup**: a processor reflects over the target's fields, reads their annotations, looks up a
validator per annotation type, and runs it. Fowler names the alternatives — the annotation could implement the
check itself, or carry the name of its validator class — and rejects both: "I generally prefer, at least in
Java, to make annotations independent of the processing mechanism" *(Ch. 42, "Custom Syntax with Runtime
Processing (Java)")*.

**One declaration, N processors, in practice.** The Ruby code-generation example upgrades the processing so
each annotated field automatically gets its own generated predicate method, and the critical observation is:
**"I don't need to modify the annotation calls in the patient visit class; they can remain the same as the
simpler case."** The user-facing declarative surface is unchanged while the processing is upgraded underneath
*(Ch. 42, "Dynamic Code Generation (Ruby)")*. It also guards against clobbering an existing method before
generating.

#### Relationships

- Builds a **Semantic Model (Ch. 11)**, constrained to decorate the language's own program model.
- Alternative to **explicit registration** / imperative configuration calls.
- Related to **Symbol Table (Ch. 12)** (annotation → processor dictionaries) and to code generation patterns.

> **SDK lens:** This chapter is essentially a design brief for **declarative metadata APIs** — decorators,
> attributes, schema classes, ORM field descriptors, serialization tags, validation decorators, DI
> annotations. **When Annotation beats explicit registration:** when definition and processing genuinely want
> to vary independently, or when you want the declaration readable in isolation right next to the thing it
> describes. Explicit registration wins when the reader needs to see *what happens* and *when* in one place.
> **Design rule for any decorator you ship: it must be purely declarative** — no control flow, no ordering
> dependencies between decorators, no implied coupling to when processing runs. The moment your decorator's
> behavior depends on declaration order relative to another, you have built a trap. **Decouple the annotation
> from its processor**: keep the annotation inert data, put behavior in a processor selected via a registry.
> That is what makes multiple processors possible, and **the multi-target payoff is the strongest argument for
> a declarative API**: one declaration, N processors (server-side check plus generated client-side check;
> runtime validation plus generated docs; runtime schema plus generated migrations) with no duplication and no
> drift. **You don't need language-level annotation syntax** — class-body declaration calls, naming
> conventions, and marker interfaces all count, with known costs. And **accept the discoverability cost
> honestly**: the reader must now look in two places, so mitigate with good docs and, especially, good error
> messages from the generic processing code.

---

### Parse Tree Manipulation (Ch. 43)

> **Intent:** Capture the parse tree of a code fragment to manipulate it with DSL processing code. *(Ch. 43)*

#### The concept

When you write code in a closure, that code is available to be *executed* later. Parse Tree Manipulation goes
further: it lets you **examine and modify the code's structure**, not merely run it. The host language's own
expressions become input data to your DSL processor.

#### How it works

- You need an environment that can turn a code fragment into a workable parse tree. "This is a relatively rare
  programming language feature — rare both in that few languages support it and in that, even when it is
  supported, it's rarely used" *(Ch. 43, "How It Works")*.
- Three exemplars: **C# (from 3.0)** via expression trees, **Ruby's ParseTree library**, and **Lisp**.
- **The library-based ones work similarly:** you invoke a call on a source fragment and get back a data
  structure representing its parse tree. C#'s version works only on an **expression inside a lambda** — so you
  cannot capture multi-statement code — and returns a hierarchy of purpose-built expression objects. In both
  you write a **tree walker**; both can turn a subtree back into executable code.
- **Lisp is categorically different:** Lisp source *is* essentially a serialized parse tree of nested lists,
  and syntactic macros let you examine and manipulate any expression.
- **You can't accept arbitrary host-language expressions.** There are always limits on what your walker can
  handle. "In these situations, **it's important to fail fast** should you get an expression that you can't
  handle." Normally when walking a parse tree you know the node shapes conform to expectations; here the tree
  can contain *any* legal host construct, so **all the checking is your responsibility**.
- **Walk only what you must.** "Usually you won't need, or want, to walk the entire parse tree." Walk the parts
  you need to populate your Semantic Model and hand the remaining subtrees back to the language to evaluate as
  soon as you no longer need to navigate them. This keeps you from reimplementing a whole parser.

#### When to use it

- The driving reason: **you want to use a fuller range of the host language's features to express something,
  "instead of the pidgin of the usual internal DSL constructs."**
- The key distinction from the general internal-DSL benefit: you can always intermix full host language with
  DSLish constructs, but "usually, you can only manipulate the executable **results** of the host language —
  you can't dive into host language expressions and manipulate their structure" *(Ch. 43, "When to Use It")*.
- **Not many DSL use cases exist.** The best is LINQ, the driving force behind .NET's support: expressing query
  conditions as ordinary Boolean expressions and turning them into a **SQL query** — writing DB queries without
  knowing SQL, or writing one query executed against different data sources. That requires parsing the host
  condition into a tree, walking it, and emitting SQL: essentially **source-to-source translation**. "Parse
  Tree Manipulation is good for these cases, as it allows you to use a familiar syntax for your conditions when
  your target language is not well known or you want multiple targets."
- Another use: **modify** the tree to perform surgery, e.g. redirect all method calls on one object to another.
  "But it's not clear how useful that kind of surgery is in a DSL context."

**The warning — the real point of the chapter:**

> "I also worry a bit that Parse Tree Manipulation is one of those techniques where **the intricacies of doing
> it may be just too appealing for many programmers. It's an appeal that can blindside people into missing
> other, simpler ways of achieving the same goal.**" *(Ch. 43, "When to Use It")*

#### What the worked example teaches

The example translates a lambda over a criteria object into an IMAP server-side search string *(Ch. 43,
"Generating IMAP Queries from C# Conditions (C#)")*. Beyond the mechanics, four ideas transfer:

- **A "phantom" receiver object.** To write a comparison against a `Subject` property you need an object
  exposing those members. Fowler is explicit that "this object won't ever do anything at runtime; it's only
  there to provide the methods to help me compose the query. As a result, the return values of its methods are
  irrelevant as they'll never actually be called." The type exists purely so the compiler will accept — and the
  IDE will complete — an expression you intend to *inspect* rather than execute.
- **The honest admission about expressiveness:** "despite my desire to allow clients to construct IMAP queries
  in C#, they can't use *any* C#." The model handles only a subset of operators and shapes; the walker throws
  on anything else — fail fast, as the pattern requires.
- **Validate at construction to simplify extraction.** The element builder asserts node validity in its
  constructor, so the later logic that pulls data out of the node stays simple. It also accepts the keyword and
  value on either side, since commutativity is what a host-language reader expects.
- **"Don't parse what you can evaluate."** For the *value* side of each comparison he does not walk the node at
  all — he compiles and invokes that subexpression through the language runtime. "This allows me to put any
  legal C# into the value side of my elements without having to deal with it in my navigation code." This is
  "walk only what you need" in its purest form, and it is the main reason the example stays tractable.

**"Stepping Back" — two meta-lessons** *(Ch. 43, "Stepping Back")*:

1. **Explanation order ≠ construction order.** He explains the example one aspect at a time because that's
   easier to understand, but he *built* it feature by feature, refactoring as he went. "I always advocate
   building software like this, feature by feature, but I don't think that's the best way to explain the final
   result. So don't let the structure of the final result and the way I explain it fool you into thinking that
   it is how it's built."
2. **He wouldn't actually build it this way.** "Although walking a parse tree like this yields that geeky
   pleasure of using fancy parts of a language, I wouldn't actually build an IMAP DSL this way." The
   alternative is plain **Method Chaining**, whose entire implementation is a handful of small methods plus one
   Context Variable. His diagnosis of *why* it's simpler is the transferable insight:

   > "One of the main reasons this is so much simpler is that **the structure of the internal DSL is more
   > similar to the IMAP query itself.** In fact, it's really just the IMAP query expressed as Method Chaining.
   > Its advantage over using IMAP itself boils down to IDE support. Some people might prefer the more C#ish
   > syntax that the Parse Tree Manipulation example gives you, but I must admit I'm happier with the IMAPish
   > version."

#### Relationships

- Populates a **Semantic Model**, like every other pattern here.
- Its main competitor for the same problems is plain **Method Chaining** (+ Expression Builder + Context
  Variable).
- **Macro (Ch. 15)** is the same idea by another route — Lisp macros enable it because Lisp source is
  parse-tree-shaped.

> **SDK lens:** This is the pattern behind LINQ-to-SQL, ORM expression translation, and any API that **inspects
> a lambda instead of calling it** — `.filter(x => x.age > 40)` compiled to a remote query. Fowler's
> constraints all apply: your API accepts only a *subset* of the host language, so you must **fail loudly and
> specifically** on anything outside it — a silent mistranslation is far worse than an exception. **Design the
> surface to mirror the target, not the host**: the IMAP verdict is the lesson, where an API shaped like the
> target query language ended up simpler and better than one shaped like the fanciest available host-language
> feature, with IDE support the only genuine advantage of the fancy version. **Evaluate what you don't need to
> inspect**: define a clear boundary between structure you interpret and sub-expressions you hand back to the
> language; it massively shrinks what you have to support. And **beware technique-attraction** — Fowler's
> warning that intricacy is seductive and "can blindside people into missing other, simpler ways" is the
> general antidote to clever-trick API design.

---

### Class Symbol Table (Ch. 44)

> **Intent:** Use a class and its fields to implement a symbol table in order to support type-aware
> autocompletion in a statically typed language. *(Ch. 44)*

#### The concept

Modern IDEs offer **type-aware autocompletion**: type a variable name, a dot, and get the list of methods on
that object. Fowler — a self-declared enthusiast for dynamic languages — concedes this is a genuine benefit of
static typing. In an internal DSL you don't want to lose it when *typing the name of a symbol* in your
language. But the usual ways of expressing DSL symbols are strings or a built-in symbol type, which carry no
type information at all, so the IDE can offer nothing.

Class Symbol Table makes the DSL's symbols **statically typed host-language entities** by declaring each symbol
as a **field in an Expression Builder**. The field name is the symbol name; the field's declared type tells the
IDE and compiler what that symbol can do.

#### How it works

- **Put the DSL script inside a single Expression Builder class**, usually a subclass of a more general builder
  carrying behavior needed by all scripts. The script's class then consists of a method holding the script plus
  fields declaring the symbols *(Ch. 44, "How It Works")*.
- **Naming conventions get bent for readability.** A plural class name is unconventional; "the readability of
  the DSL is trumping my usual code style rules." Restated later: any OO style book will tell you to avoid
  plural class names and he agrees — "However, here a plural name reads better in the context of the DSL, so
  this is another case of general coding rules being broken to make a good DSL script."
- **The runtime gap.** Declaring fields is not enough. When the script refers to a field, at runtime it refers
  to the **contents** of the field, not the field *definition*. The IDE knows about both while you write; the
  link to the declaration disappears when the program runs. So you must **populate every field with a suitable
  object before the script executes.**
- **The population mechanism.** Make the class instance the active script: code in the constructor or a build
  method populates the fields, and the script lives in an instance method. The field contents are usually
  **small Expression Builders** that link to the underlying Semantic Model object *and also carry the field
  name*, to help with cross-referencing. In Symbol Table terms the field name is the key and the builder is the
  value — but occasionally you need lookup by name too, which is why the builders keep their own name.
- **Reflection is the price.** The script refers to fields by the field literal itself — that's the point. But
  while processing you need the builders in those fields to refer to *each other*, which means looking up
  fields by name or iterating all fields of a given type. "Doing this will require some more tricky code,
  usually using reflection. Usually there's not too much of it and, provided it's well encapsulated, it
  shouldn't make the language too difficult to process."

The worked example orchestrates **three distinct execution stages** from the superclass *(Ch. 44, "Statically
Typed Class Symbol Table (Java)")*: generic field initialization; running the script (an abstract method the
subclass implements); then generic model production. Four further lessons from it:

- **Intermediate builders decouple declaration order.** Storing *builders* rather than finished model objects
  means the script can define things in any order. "However, this would lead to errors if I define a state
  before its action codes. Using the builder as an intermediate object allows me to work it either way."
- **Responsibility-preserving notification.** The first-mentioned state becomes the start state, but only the
  machine builder can know which was first, so the state builder simply notifies it without knowing what will
  be done with the fact. "This is a good example of naming being important in communicating what I think the
  responsibilities and relative knowledge of the objects should be."
- **Only script-visible types pay the readability tax.** The transition builder's type never appears in the DSL
  script, "so I can give it a more meaningful name." Bend naming rules *only* for the types the DSL author
  actually writes.
- Fowler's candid note on the generic initialization: "Doing it this way is more tricky than I'd like… any
  generic code doesn't know about the specific type of the identifier being set up, and so has to determine it
  dynamically."

#### When to use it

- **The benefit:** full static typing of all the DSL's language elements. That unlocks all the IDE machinery
  built on static types — above all type-aware autocompletion — plus compile-time type checking of the script,
  "which matters a lot to many people (but rather less to me)" *(Ch. 44, "When to Use It")*.
- **The scope limit:** "With such a focus on IDE capabilities, I see this technique as much less useful if you
  don't have an IDE that takes advantage of static types. It also does not bring much benefit in a dynamically
  typed language."
- **The cost:** "you have to bend your DSL significantly to fit within the type system. The resulting builder
  classes look very odd; also, you have to put your DSL scripts in a place where they can take advantage of
  these facilities, such as all in the same class. These restrictions may make the DSL harder to read and use."
- **The tradeoff statement:** "So for me, the fundamental tradeoff is between the restrictions on the DSL script
  and the benefits of the IDE support. I've got rather dependent on good IDE support in languages where it's
  available, which would prompt me to use techniques like this to get it."
- **Cheaper alternative:** "If you want this kind of static type support, you can often get what you need by
  using **enums as symbols**."
- **Closing verdict on the example:** "Using a class and its fields as a symbol table does involve a bit of
  tricky code in places, but the benefit is full static typing and IDE support. That's usually a worthwhile
  tradeoff."

#### Relationships

- A specialization of **Symbol Table (Ch. 12)** — field name = key, builder = value.
- Requires **Expression Builder**; often combined with **Object Scoping** (subclassing the builder).
- Cheaper alternative for the same goal: **enums as symbols** *(Ch. 12)*.

> **SDK lens:** The general technique is **turning stringly-typed identifiers into typed program elements so
> tooling can see them.** Every modern equivalent — enums instead of string constants, typed key objects,
> literal-union types, generated client stubs, typed schema classes — is the same trade: more ceremony in the
> declaration in exchange for autocompletion, compile-time checking, rename refactoring, and go-to-definition.
> **Reuse the tradeoff statement directly:** restrictions on how users must write their code vs. the tooling
> benefits. If your users have no IDE that exploits static types, or the language is dynamic, the benefits
> mostly evaporate and the restrictions remain — don't pay the cost. **Reach for the cheap version first**
> (enums, literal unions) before contorting the API into a class-with-fields shape. **Confine ugliness to the
> implementation**: the reflective initialization is acknowledged as ugly, and what matters is that it's
> encapsulated in the framework superclass, not imposed on the user. And note the precise version of
> "readability first": **break naming conventions only on the types the user actually types**; keep normal
> conventions on the types they never see.

---

### Textual Polishing (Ch. 45)

> **Intent:** Perform simple textual substitutions before more serious processing. *(Ch. 45)*
>
> Sketch: `3 hours ago` → `3.hours.ago`

#### The concept

Internal DSLs are often easier to develop — especially if you're not comfortable writing parsers — but the
result is littered with host-language artifacts (dots, colons, parentheses, quotes) that nonprogrammers find
awkward to read. Textual Polishing runs a series of simple **regular expression substitutions** over the script
*before* it reaches the parser/evaluator, converting a domain-expert-friendly surface into a valid internal-DSL
expression.

#### How it works

- A sequence of regex substitutions on the script text. **The output of the polishing is an expression in an
  internal DSL** — polishing does not produce a model, it produces host-language code *(Ch. 45, "How It
  Works")*.
- Specification is easy; correctness is not. "The tricky thing, of course, is getting the regular expressions
  correct so you don't get unwanted substitutions. A space in a quoted string probably should not be turned
  into a dot, but that makes the regex much harder to write."
- **Most natural in dynamic languages**, where the polished text can be evaluated at runtime: read the script,
  polish it, evaluate the result. Possible in static languages by polishing before compiling — "which does
  introduce another step into the build process."
- **Occasionally useful for external DSLs**: when something is hard to spot with the usual lexer/parser chain, a
  polishing preprocess before lexing can help — **semantic indentation** is the example.
- Conceptually: "You can think of Textual Polishing as a simple application of textual **Macros**, with all the
  corresponding problems."

**Tokenization discipline** from the example: because elements are whitespace-separated, "it's valuable to
ensure that all of the regexes have boundary expressions at both ends" *(Ch. 45, "Polished Discount Rules
(Ruby)")*.

#### When to use it

This is the most sceptical "when to use it" in the group — Fowler essentially argues himself out of the pattern
*(Ch. 45, "When to Use It")*:

- > "I confess I'm rather wary of Textual Polishing; my feeling is that if you use a little, it doesn't help
  > much, and if you use a lot, it gets very complicated, so it may then be better to use an external DSL."
- **The hard structural limit:** "Textual Polishing cannot do anything to change the syntactic structure of the
  input, so you are still tied to the basic syntactic structure of the host language." You can only re-skin, not
  re-shape.
- **Keep the two forms recognizably similar.** "I think it's important to keep the prepolished DSL and the
  resulting internal DSL expressions recognizably similar. The resulting internal DSL should be as clear as
  possible for programmers to read — the polishing is only a visual convenience for nonprogrammers." If a reader
  can't map the polished text onto the underlying calls, debugging becomes guesswork.
- **A cheaper alternative: fix it in the editor, not the language.** "If you find the noise characters in an
  internal DSL annoying, an alternative approach to Textual Polishing is to use an editor that supports syntax
  coloring and set it up to color the noise characters with a very gentle color that fades into the background."
  An excellent instance of solving a readability problem in tooling rather than in the language.
- **Escalation rule:** "If you find yourself doing a lot of polishing, I strongly suggest that you explore using
  an external DSL instead. Once you get up the learning curve of writing a parser, you'll get much more
  flexibility, and it will be easier to maintain the parser than the sequence of polishing steps."

The example is instructive because of what it does *before* reaching for regexes *(Ch. 45, "Polished Discount
Rules (Ruby)")*:

1. **Object Scoping removes noise for free** — putting the rules in their own file and evaluating each line in
   the builder's context drops the receiver prefix, with no substitution at all. It also **moves the Method
   Chaining finishing call into the processing code**, out of the user-visible DSL — a general trick: terminator
   calls are an implementation detail and users shouldn't have to type them.
2. **Adjust the DSL's own vocabulary to shorten the distance the polishing must travel.** Where a desired
   keyword collided with a host-language reserved word, Fowler notes you can rename the DSL method instead of
   substituting, since "doing this makes it easier to see the correspondence between the polished text and the
   resulting DSL."
3. **Closing verdict:** "This doesn't look too bad, but the code is only enough to process this one particular
   example. To handle more cases, the code will have to get more complex and much more ugly. So in this case,
   I'd be keeping a careful eye on it, ready to reach for an external DSL to use instead."

#### Relationships

- A degenerate form of **Macro (Ch. 15)**, with macro-like hazards.
- Frequently paired with **Object Scoping (Ch. 36)**, which removes noise without any substitution at all —
  always try this first.
- Its escalation path is an **external DSL** with a real parser.

> **SDK lens:** Mostly a cautionary pattern, with four transferable lessons. **Prefer structural fixes to
> textual ones** — Object Scoping and renaming a method achieved most of the goal with none of the regex risk;
> reach for the language-level fix before the string-rewriting fix. **Hide terminator/finisher calls from users**
> where you can, moving `.build()` into the harness rather than requiring every user line to end with it.
> **Don't let the user-facing surface and the underlying calls diverge**, or you destroy every error message,
> stack trace, and debugging session downstream — exactly the problem with heavy source rewriting,
> transpilation, and macro-based APIs generally. And **solve cosmetic complaints with tooling** (syntax
> highlighting, formatters) rather than by adding a translation layer.

---

### Literal Extension (Ch. 46)

> **Intent:** Add methods to program literals. *(Ch. 46)*
>
> Sketch: `42.grams.flour`

#### The concept

Literals — numbers and strings — often make a natural *starting point* for DSL expressions (`42.grams`,
`3.days.ago`). Traditionally they're built-in types with fixed interfaces so you can't extend them, but more
languages now allow adding methods to third-party classes: C#'s **extension methods**, Ruby's **open classes**.
For DSLs this is particularly handy because it lets you **start a method chain with a literal**.

#### How it works

As with most method chains, a key decision is **whether to use an Expression Builder**. Without one, every
intermediate type in the chain must itself carry the appropriate fluent methods. With one, you avoid that, but
you must ensure you can cleanly get from the builder back to the underlying object *(Ch. 46, "How It Works")*.

**What should `42.grams` return?** Three options, each with distinct consequences:

1. **A number**, in a canonical unit. **Danger: "type transmogrification"** (a term Fowler credits to Neal
   Ford) — the expression starts with an integer and turns into a floating point, meaning every subsequent
   method in the chain must be defined on *multiple* numeric types.
2. **A quantity object** (magnitude plus unit). "In general, I much prefer quantities to simple numbers for
   representing dimensioned values; quantities represent my intent better and also allow me to define useful
   behavior (such as alerting me to problems with `42.grams + 35.cm`)." Almost no platform ships a quantity
   class, but it's easy to write. Because the magnitude is encapsulated, **the type transmogrification problem
   largely disappears**. Cost: the quantity class now carries DSL fluent methods, "which may make the quantity
   class harder to understand."
3. **An Expression Builder.** You get full control over the rest of the expression; the cost is that calling
   code must be able to unpack the subject from the builder — fine inside a scoped ingredients block, a problem
   for arithmetic like `42.grams + 3.oz`. "I tend to prefer an Expression Builder most of the time, but it
   really depends on the context of its use."

#### When to use it

- **Sceptical framing.** "Literal Extension has become a popular illustration of how to make APIs more fluent,
  particularly by advocates of languages which are able to do it. … It can help a good deal in improving
  fluency, although there's also **the suspicion that some of this enthusiasm is fondness of a new toy**"
  *(Ch. 46, "When to Use It")*.
- **The real cost is global interface pollution.** "In some environments, there is a serious concern that adding
  methods like this to literals will bloat the interface of those literal classes. These Literal Extensions are
  only needed in some contexts, so if they appear in more contexts they can make a class's interface much more
  confusing." You must weigh the usefulness of the extension against the confusion it adds everywhere else in
  the program.
- **The mitigation: namespace scoping.** "Some language environments allow you to state that Literal Extensions
  are bound to a namespace, which avoids this problem." In the C# example Fowler departs from his usual practice
  and shows the namespace explicitly, precisely because it means the extension method "will only show up if I'm
  in the right namespace."

#### Keep DSL vocabulary off general-purpose types

The most transferable idea in the chapter comes from the recipe example *(Ch. 46, "Recipe Ingredients (C#)")*.
Fowler wrote the `Quantity` class himself — and still refuses to put the DSL's `Of` method on it:

> "Although quantity is a class I'm writing, I don't think the `Of` method belongs on it — because **`Of` is part
> of a DSL for a limited purpose, while the quantity class can be used as part of a general library.** So I use
> an extension method again."

The rule: a type that serves the general library gets a general interface; DSL-only vocabulary lives in an
opt-in, namespace-scoped extension. (The same example resolves ingredient names to objects via a substance
registry acting as a **Symbol Table**, lazily creating the substance on first request.)

#### Relationships

- Typically the entry point into **Method Chaining (Ch. 35)**; may or may not use **Expression Builder**.
- Its resolution of names to objects uses **Symbol Table (Ch. 12)**.
- The "quantity vs. raw number" discussion connects to the Quantity analysis pattern.

> **SDK lens:** This is **monkey-patching / extension-method API design**, and Fowler's rule is namespace or
> module scoping: extensions to types you don't own should be opt-in and locally scoped, never globally visible.
> A library that adds methods to the integer type for everyone is imposing its vocabulary on the whole program.
> **Keep DSL-specific fluent methods off general-purpose types** — `Of` belongs to a limited-purpose language,
> `Quantity` to the general library; generalized: *don't bolt your framework's fluent vocabulary onto shared
> domain/model classes.* **Watch the return type of every chain step**: type transmogrification forces you to
> define the rest of your fluent vocabulary on every type it might pass through, so a purpose-built wrapper type
> that stays stable through the chain is almost always better — the same reason fluent builders return
> `this`/`Self` rather than shifting types. And **fluency is not free**: Fowler's "fondness of a new toy" line is
> the general caution that a technique's availability and elegance are not reasons to adopt it.

---

### The judgement calls, collected

Across these eight patterns the same handful of decisions recur, and they are the reusable content:

1. **Keep the magic proportional to the benefit.** Dynamic Reception's fluency is paid for in impenetrable stack
   traces *(Ch. 41)*; Parse Tree Manipulation's power is paid for in a walker that must reject most of the host
   language *(Ch. 43)*; Class Symbol Table's autocompletion is paid for in reflective setup and a contorted
   script layout *(Ch. 44)*. In every case Fowler states the exchange rate explicitly and refuses the trade when
   the benefit is thin.
2. **Use the open-ended mechanism only where the vocabulary is genuinely open.** Dynamic dispatch for
   attribute names and values; ordinary declared methods for the fixed operator set *(Ch. 41)*.
3. **Layer the API by complexity; don't stretch one mechanism to cover everything.** "Different solutions may
   work best at different complexities, so you should provide more than one" *(Ch. 41, "When to Use It")*.
4. **When a technique starts requiring special cases, you've outgrown it.** Special-cased Dynamic Reception
   means don't use Dynamic Reception *(Ch. 41)*. A growing pile of polishing regexes means write a parser
   *(Ch. 45)*. A desire to build parse trees out of chained calls "is a smell indicating that the internal DSL
   is doing too much work" *(Ch. 41)*.
5. **Mix techniques; don't chase purity.** Greenspun form *(Ch. 40)* and the fully symbol-free state machine
   *(Ch. 41)* both show that maximizing one technique produces a worse language than a judicious blend. "A
   mixture of techniques is often the best bet."
6. **Discoverability vs. expressiveness is the recurring axis.** Literal Map is expressive but its keys are
   invisible and unvalidated *(Ch. 40)*; Class Symbol Table sacrifices expressiveness and layout freedom to buy
   discoverability *(Ch. 44)*; Literal Extension buys fluency at the cost of polluting a widely-used interface
   *(Ch. 46)*.
7. **Shape the DSL like its domain or target, not like the host language's flashiest feature.** The IMAP
   comparison is the cleanest demonstration: the Method-Chaining version won because it mirrored IMAP's own
   query language *(Ch. 43)*.
8. **Separate definition from processing when — and only when — they should vary independently** *(Ch. 42)*,
   with the corollary discipline that declarations must be purely declarative: no logic flow, no ordering
   dependencies, no implied coupling to when processing runs.
9. **Explanation order is not construction order** *(Ch. 43, "Stepping Back")*. Build feature by feature,
   refactoring as you go; present the result decomposed by concern.
10. **Solve cosmetic problems with tooling before adding machinery** *(Ch. 45)*.
