# Domain-Specific Languages (Fowler & Parsons, 2010) — Part II "Common Topics", Chapters 11–16

Study notes covering the six pattern chapters that apply to both internal and external DSLs.
All citations refer to (Fowler, *DSL book*, Ch. N "Title", section "…").

**Actual PDF page boundaries found (rendered pages, not print page numbers):**

| Chapter | PDF pages |
|---|---|
| 11 Semantic Model | 120 (mid-page, after Ch. 10 ends) – 123 (upper) |
| 12 Symbol Table | 123 (lower) – 130 (upper) |
| 13 Context Variable | 130 (lower) – 133 (upper) |
| 14 Construction Builder | 133 – 135 (upper) |
| 15 Macro | 135 – 142 (upper) |
| 16 Notification | 142 (mid) – 146 (upper) |
| — Part III begins / Ch. 17 Delimiter-Directed Translation | 146 (lower) |

Every chapter in Part II follows Fowler's pattern form: a one-line **intent**, a **sketch** (diagram),
**How It Works**, **When to Use It**, and one or more worked **examples** in Java / C# / Ruby.

---

## Chapter 11: Semantic Model

> **Intent:** "The model that's populated by a DSL." (Fowler, Ch. 11 "Semantic Model", intent line)

This is the keystone pattern of the whole book. Fowler's default advice is to *always* use one, and
nearly every other pattern in the book is described in terms of its relationship to the Semantic Model.

### The core idea

A Semantic Model is a representation — typically an in-memory object model — of the *same subject matter*
that the DSL describes. If the DSL describes a state machine, the Semantic Model is an object model with
classes for `State`, `Event`, `Transition`, and so on. A particular DSL script corresponds to a particular
*population* of that schema: one `Event` instance per event declared in the script, one `State` per state,
etc.

The framing sentence worth remembering: the Semantic Model is **"the library or framework that the DSL
populates"** (Ch. 11, "How It Works"). The DSL is not the thing. The DSL is a *front end* for populating
something that could exist perfectly well without it.

The representation need not be an in-memory object model. It could be a plain data structure with the
behavior supplied by functions acting on that data; it need not even be in-memory — a DSL could populate a
model held in a relational database. Fowler uses in-memory object models throughout the book because that's
what he knows best, not because it's required.

### The decisive design rule

> The Semantic Model **should be usable without a DSL present**. You should be able to populate it through
> an ordinary command-query interface.

Fowler states this as the constraint that keeps the pattern honest: it ensures the Semantic Model fully
captures the semantics of the subject area, and it makes both the model and the parser independently
testable (Ch. 11, "How It Works"). If populating the model requires going through the DSL, you have
smeared semantics into your parser and you have lost the whole benefit.

### The two interfaces (highly relevant to API/SDK design)

Fowler says it is usually helpful to think of the Semantic Model as having **two distinct interfaces**
(Ch. 11, "How It Works"):

1. **Operational interface** — what clients use to *do work with* an already-populated model. This should
   assume the model has already been created and make it easy for the rest of the system to take advantage
   of it.
2. **Population interface** — what the DSL/parser uses to *create instances* of the classes in the model.
   Used only by the parser(s) and by the model's own test code.

His mental trick for API design, which he calls a general rule of thumb for any objects and not just DSL-ish
ones: **assume the model is magically already there, then ask yourself how you would use it.** Define the
operational interface *first*, even though at runtime the population interface necessarily executes first.
He acknowledges this is counterintuitive but insists it produces better designs.

The population interface also acts as a **decoupling seam**. There is always *some* dependency — the parser
obviously has to see the Semantic Model in order to populate it — but by making the population interface an
explicit, deliberately designed boundary, an implementation change inside the Semantic Model is much less
likely to force a change in the parser. Fowler reports exactly this payoff in the introductory example: he
refactored the state machine model's internals without touching the parsing code, because the changes didn't
alter the population interface (Ch. 11, "The Introductory Example (Java)").

### Semantic Model vs. Domain Model

Similar to a Domain Model *[PoEAA]*, but Fowler deliberately uses a separate term:

- Semantic Models are often *subsets* of Domain Models, but don't have to be.
- "Domain Model" implies a behaviorally rich object model; a Semantic Model **may be data alone**.
- A Domain Model captures the core behavior of an application; a Semantic Model may play a supporting role.
- Worked distinction: a DSL that describes object-relational mappings produces a Semantic Model consisting
  of the *Data Mappers* — **not** the Domain Model that is the subject of the mapping.

### Semantic Model vs. syntax tree / AST

They serve separate purposes and this distinction is the crux of the pattern:

- A **syntax tree corresponds to the structure of the DSL script**. Even an abstract syntax tree, which
  simplifies and somewhat reorganizes the input, still takes fundamentally the same form as the input.
- A **Semantic Model is based on what will be done with the information** in the script. It often has a
  substantially different structure, and is usually *not* a tree at all (graphs with cross-references are
  common — the state machine's transitions point at shared state and event objects).
- Occasionally an AST *is* an effective Semantic Model, but "these are the exception rather than the rule."

Fowler notes that traditional parsing/compiler literature doesn't use Semantic Model, and diagnoses why:
for a general-purpose language, a syntax tree is a perfectly suitable basis for code generation, so there's
less pressure to build a different model. Compiler people do occasionally build one — a call-graph
representation is very useful for optimization — and they call these **intermediate representations**,
usually as intermediate steps before code generation.

### Where the Semantic Model comes from

Two common origin stories (Ch. 11, "How It Works"):

- **The model precedes the DSL.** You already have a Domain Model and decide that some portion of it would
  be better populated from a DSL than through the regular command-query interface. The DSL is then layered
  on top.
- **The model and the DSL are built together**, with discussions with domain experts refining both the
  expressions of the DSL and the structure of the model. Each informs the other.

### Execution: interpreter style vs. compiler style

The Semantic Model can either:
- **hold the code to execute itself** (interpreter style), or
- **be the basis for code generation** (compiler style).

Even when you're generating code, Fowler recommends *also* providing interpretation — it helps enormously
with testing and debugging, and lets you use the Semantic Model as a **simulator for the generated code**.
Because the code generator works off the Semantic Model rather than the parser, multiple code generators
become cheap: the independence from the parser avoids duplicating parser code across generators.

### Validation lives here

The Semantic Model is "usually the best place for validation behavior, since you have all the information and
structures in place to express and run the validations" (Ch. 11, "How It Works"). Crucially: run validations
*before* either running the interpreter or generating code. In the introductory state-machine example the
validations were things like: no unreachable states, no states you can't get out of, all events and commands
actually used in the definitions of states and transitions (Ch. 11, "The Introductory Example (Java)").

This is where **Notification (Ch. 16)** joins the picture — validations over a Semantic Model naturally want
to report *all* problems at once rather than aborting on the first.

### Computational vs. compositional DSLs

Fowler cites Brad Cross's distinction *[cross-comps]* and observes it's really a distinction about the kind of
Semantic Model produced:

- **Compositional DSL** — describes some kind of composite structure in textual form. XAML describing a UI
  layout is the example; the primary form of the Semantic Model is *how the various elements are composed*.
- **Computational DSL** — the Semantic Model "feels more like code than data" and drives computation, usually
  with an alternative computational model instead of the usual imperative one. The Semantic Model for this is
  usually an **Adaptive Model**. The state machine example is of this kind.

Tradeoff he flags: "You can do a lot more with a computational DSL, but people often find them more difficult
to work with."

### When to Use It

Fowler's answer is essentially *always*, and he's self-aware about it — he notes he's uncomfortable saying
"always" because absolute advice is usually a sign of closed-minded thinking, but he can only see very few
cases where you wouldn't want one, and those are all very simple situations.

**Arguments for:**

1. **Separate testing of semantics and parsing.** Test semantics by populating the model directly and running
   tests against the model; test the parser by checking that it populates the model with the right objects.
2. **Multiple parsers become tractable.** If you have more than one parser, you can check they're semantically
   equivalent by comparing the populations of the Semantic Model they produce. Fowler had exactly this
   requirement in the book's introductory example — multiple internal *and* external DSLs over one model — and
   the Semantic Model made adding a new DSL+parser possible without duplicating code in the other parsers or
   altering the model.
3. **Independent evolution.** More common than multiple DSLs is simply evolving the DSL separately from the
   Semantic Model (and vice versa).
4. **Flexibility in execution.** Direct interpretation, code generation off the model, both at once
   (model-as-simulator), multiple code generators, plus non-execution outputs like visualizations.
5. **The most important reason, in his words:** it "separates thinking about semantics from thinking about
   parsing. Even a simple DSL contains enough complexity to justify dividing it up into two simpler problems."

**The exceptions he envisages:**

- **Simple imperative interpretation** — you just execute each statement as you parse it. A classic calculator
  evaluating arithmetic expressions is the canonical case.
- **When the AST already *is* the model.** For arithmetic expressions, even if you don't interpret immediately,
  the AST is pretty much what you'd have in a Semantic Model anyway. Generalized rule: *if you can't think of a
  more useful model than the AST, there's little point creating a separate Semantic Model.*
- **Code generation directly off the AST** — the most common real-world case where people skip the pattern.
  Reasonable *provided* the AST is a good model of the underlying semantics and you don't mind coupling the
  code generation logic to the AST. If either condition fails, it's often simpler to transform the AST into a
  Semantic Model and do a simpler code generation from that.

**His stated bias:** always *start* by assuming you need a Semantic Model. Even if thinking it through convinces
you that one isn't necessary, stay alert to increasing complexity and put one in as soon as any complication
starts creeping into the parsing logic.

**Honest caveat he adds:** Semantic Model is not part of DSL culture in the functional programming world. The
FP community has a long history of DSL thinking, and Fowler admits his experience with modern functional
languages is "no more than occasional experimentation," so he explicitly declines to claim confidence that his
inclination applies there.

### Relationships to other patterns

- **Symbol Table (Ch. 12)** — the values in a Symbol Table are usually Semantic Model objects (or builders that
  will produce them). The Symbol Table is how a script's textual identifiers resolve to model objects.
- **Construction Builder (Ch. 14)** — needed when the Semantic Model's objects are immutable but the parse
  gathers their field values gradually.
- **Context Variable (Ch. 13)** — the "current item" during a parse is typically a Semantic Model object or a
  builder for one.
- **Notification (Ch. 16)** — the reporting vehicle for validations run over a populated Semantic Model.
- **Adaptive Model** — the usual form of the Semantic Model for a computational DSL.

### SDK relevance

This is the chapter with the most direct carryover to library/SDK design, even when no DSL is involved:

- **Model/API separation.** Design the core model so it is fully usable and testable through an ordinary
  programmatic interface; treat any DSL, config format, YAML loader, CLI, or fluent builder as a *second-class
  front end that merely populates the model*. Everything the front end can express must be expressible
  directly. This is the same discipline as "the CLI is a client of the library, not the other way around."
- **Design the operational interface before the population/construction interface.** Pretend the object already
  exists and write the usage code first. This is arguably the single most transferable piece of API advice in
  the chapter.
- **Make the population interface an explicit, narrow, deliberately-designed boundary** so internal refactoring
  of the model doesn't ripple out into every loader/parser/adapter.
- **Multiple front ends validate the model.** If two very different surface syntaxes can both populate the same
  model and produce equivalent populations, the model is probably factored at the right level.
- **Put validation in the model, not the parser** — the model has all the information and structure to express
  it, and it then applies uniformly regardless of which front end populated the model.

---

## Chapter 12: Symbol Table

> **Intent:** "A location to store all identifiable objects during a parse to resolve references."
> (Fowler, Ch. 12 "Symbol Table", intent line)

### The core idea

Many languages need to refer to the same object at multiple points in a script. If a DSL defines a
configuration of tasks and their dependencies, one task's definition must be able to name its dependent
tasks. So you invent some form of **symbol** for each task, and while processing the script you put those
symbols into a Symbol Table that stores the link between the symbol and the underlying object holding the
full information.

### How it works

The essential purpose is to **map between the symbol used in the DSL script and the object it refers to**.
That maps naturally onto a dictionary/hash, so the most common implementation is exactly that: a map with the
symbol as key and the **Semantic Model** object as value.

**Choice of key type.** For many languages the obvious choice is a string, because the text of the DSL *is* a
string. The main reason to use something else is a language with a genuine **symbol data type**:

- Symbols are structurally like strings (a sequence of characters) but usually differ in behavior — many
  string operations (concatenation, substrings) make no sense for a symbol.
- A symbol's principal task is *lookup*, and symbol types are designed with that in mind. Two occurrences of
  `"foo"` are often distinct objects compared by content; `:foo` and `:foo` always resolve to the *same*
  object and compare for equality much faster.
- Performance can justify symbols, but for small DSLs it may not matter much. **The big reason is intent
  communication**: declaring something as a symbol states clearly what you're using it for and makes the code
  easier to understand.
- Symbol literal syntax also makes symbols visually stand out in an internal DSL — a further reason to use
  them. (Ruby `:aSymbol`, Smalltalk `#aSymbol`, Lisp treats any bare identifier as a symbol.)

**Choice of value type.** Values can be either **final model objects** or **intermediate builders**. Model
objects make the Symbol Table act as *result data*, which is good for simple situations. Putting a **builder**
object as the value gives more flexibility at the cost of a bit more work.

**One map, several maps, or a special class?** Many languages have different *kinds* of thing to refer to
(the introductory state model has states, commands, and events):

- **Single map for everything** — all lookups share one map. Immediate consequence: you can't use the same
  symbol name for different kinds of things (no event with the same name as a state). That may be a *useful*
  constraint for reducing confusion in the DSL. But it makes the processing code harder to read, because it's
  less clear what kind of thing you're manipulating. **Fowler does not recommend this.**
- **Multiple maps** — one map per kind of object (events, commands, states). You can think of this as one
  logical Symbol Table or three separate ones. **This is Fowler's preference**, because the processing code
  now makes clear which kind of object is being referred to at each step.
- **A special class** — a single Symbol Table object with kind-specific methods (`getEvent(code)`,
  `getState(code)`, `registerEvent(code, event)`). Sometimes useful, and gives a natural home for any
  symbol-processing behavior. Most of the time Fowler doesn't find a compelling need for it.

**Forward references.** Objects referred to before they are properly defined. DSLs usually *don't* have strict
declare-before-use rules, so forward references often make sense. If you allow them, **any reference to a
symbol must populate the entry in the symbol table if it isn't already there**. This will often push you toward
using builders as the values, unless the model objects are very flexible about being filled in later.

**Misspelled symbols.** If there's no explicit declaration of symbols, misspellings become a frustrating source
of errors — a typo silently creates a new, unrelated entity. If there's any way to detect misspelled symbols,
put that checking in; it "will prevent a lot of hair-pulling." This is one reason to *require* that all symbols
be declared in some way. If you go that route, note that requiring declaration does **not** mean requiring
declaration *before* usage.

**Nested scopes.** Symbols defined only within a subset of the program. Very common in general-purpose
languages, "much rarer in simpler DSLs." If you need it, use *Symbol Table for Nested Scopes* *[parr-LIP]*.

### Statically typed symbols

Sub-section of "How It Works". In a statically typed host language (C#, Java) you can trivially use a hashmap
with string keys — e.g. `task("drinkCoffee").dependsOn("make_coffee", "wash")` — and it works, but Fowler lists
four concrete disadvantages:

1. Strings introduce **syntactic noise** — you have to quote everything.
2. The compiler **can't type check**. Misspelled task names only surface at runtime; and if you have several
   *kinds* of identified object, the compiler can't tell you when you've referred to the wrong kind — again a
   runtime discovery.
3. **No IDE autocompletion** on strings — you lose a powerful element of programming assistance.
4. **Automated refactorings** may not work well with strings.

The fix is some kind of statically typed symbol. **Enums** are the simple good choice; a *Class Symbol Table*
is the other.

### When to Use It

Short and decisive: "Symbol Tables are common to any language-processing exercise, and I expect you'll almost
always need to use them" (Ch. 12, "When to Use It").

The times they aren't strictly necessary:
- With **Tree Construction**, you can always delve around in the syntax tree to find things.
- Often a **search on the Semantic Model** you're building up could do the job.
- But sometimes you need an intermediate store, "and even when you don't, it often makes life easier."

### Further reading cited

- *[parr-LIP]* — lots of detail on kinds of Symbol Table for external DSLs; Fowler notes these approaches are
  likely appropriate for internal DSLs too.
- *[kabanov-hunger]* — useful ideas for statically typed symbols in Java, usable in other languages too.

### What the examples demonstrate (concepts only)

1. **Dependency network in an external DSL (Java + ANTLR).** Input is lines like `go_to_work -> drink_coffee
   dress`. Requirements: dependencies may be written in *any order* (so forward references are mandatory), and
   the result is the list of "heads" — tasks that aren't a prerequisite of anything else. The parse uses
   *Embedded Translation*; a hand-written loader class wraps the generated parser and inserts itself as the
   *Embedment Helper*, and it owns the Symbol Table (a simple map of task name → Task). The key mechanic:
   a `registerTask(name)` helper that **creates the Task lazily if the name isn't in the map yet**, called for
   both sides of every dependency — that's how out-of-order/forward references are handled with model objects
   as values. Demonstrates: Symbol Table both *populated by* and *consulted by* the same helper.

2. **Symbolic keys in an internal DSL (Ruby).** Same task/prerequisite domain, written as
   `task :go_to_work => [:drink_coffee, :dress]`. Uses Ruby's native symbol type as the key, a *Function
   Sequence* of `task` calls, a *Literal Map* for the argument, and an *Expression Builder* that uses *Object
   Scoping* via `instance_eval`. The Symbol Table is just a hash on the builder; the same lazy
   create-if-absent trick handles forward references. Fowler's takeaway: implementation is the same as with
   strings, but **use a symbol type if your language has one**.

3. **Enums as statically typed symbols (Java).** Contributed at the urging of reviewer Michael Hunger. Fowler
   is candid that he isn't enthusiastic about static typing *for finding errors* — he thinks it catches few
   errors that decent testing wouldn't — but he values it for **IDE support**: type Control-Space and get the
   list of all symbols valid at that point in the program. Same Semantic Model as before (the model itself
   still holds task names as strings); only the DSL surface uses the enum, giving autocompletion *and* typo
   protection. Techniques stacked in: Java **instance initializer** for *Object Scoping*, plus a **static
   import** of the enum constants so bare task names can be written — together these let the script be written
   in *any* class without inheritance forcing it into a subclass of the Expression Builder. The child builder
   (`PrerequisiteClause`) is a static inner class of the task builder so it can reach the parent's private
   members. Two further judgement calls worth remembering:
   - Enums "don't force inheritance or constraints on where you can write DSL script code — an advantage
     compared to a *Class Symbol Table*."
   - If the set of symbols must correspond to some **external data source**, write a build step that reads
     that source and **code-generates the enum declarations**, keeping everything in sync *[kabanov-hunger]*.
   - Consequence of a single enum: a **single namespace of symbols**. Fine when many little scripts share one
     symbol set, but sometimes different scripts want different sets. Fix: define the builder in terms of an
     **interface** (`TaskName`) and have several enums implement it; then selectively static-import only the
     group you need (morning tasks vs. snow-shoveling tasks) so the IDE offers only relevant symbols. For
     stronger static control you could make the builder generic over the subtype, but if you're primarily
     after IDE usability, selective imports are good enough.

### SDK relevance

- The **string-key critique is a general API critique**, not a DSL-specific one: string-keyed lookup APIs cost
  you compile-time checking, autocompletion, and safe refactoring. Enums, sealed types, literal-union types,
  or generated constant classes are the fix, and **code-generating those constants from an authoritative
  external source** is the pattern for keeping them honest.
- **Lazy create-on-reference** in a registry is the standard technique for accepting declarations in any order
  — worth knowing whenever you build a config loader or dependency registry.
- **Namespace scoping via interfaces + selective imports** is a nice, low-tech way to give a shared builder
  several disjoint vocabularies without generics.

---

## Chapter 13: Context Variable

> **Intent:** "Use a variable to hold context required during a parse."
> (Fowler, Ch. 13 "Context Variable", intent line)

### The core idea

You are parsing a list of items, capturing data about each. Each bit of information about an item can be
captured independently, but you also need to know **which item** you're currently capturing information for.
A Context Variable holds the current item in a variable and reassigns it as you move to a new one.

The sketch is an INI-style file: `[intro]` assigns `currentProject = new Project("intro")`, and the following
`name = …` / `lead = …` lines all operate on `currentProject`.

### How it works

You have a Context Variable whenever you have a variable named something like `currentItem` that you update
periodically during the parse as you move from one item to another in the input script. That's the whole
mechanism — the pattern exists to *name* this thing so its costs can be discussed.

**What goes in it.** A Context Variable can hold either a **Semantic Model object** or a **builder**. A
Semantic Model object is superficially more straightforward, but that's only true if *all* of its properties
are mutable at the moments the parse needs to change them. If they're not, it's usually best to use a builder
to gather the information and create the Semantic Model object at the end — i.e. a **Construction Builder**
(Ch. 14).

### When to Use It

This chapter is unusual in that the "when to use it" is mostly a **warning**:

- There are lots of places where you have to keep context during a parse, and a Context Variable is the
  obvious choice. It's easy to create and easy to get going with.
- **But they are problematic, particularly as you get more of them.** "By their nature, they are mutable state
  that has to be kept track of, and bugs adore this kind of mutable state." It is easy to forget to update the
  Context Variable at the right moment, and debugging that can be quite difficult.
- There are usually **alternative ways of organizing the parse that reduce the need for Context Variables** —
  Fowler notes you'll see mentions of these scattered around the book. (In practice: nested closures / nested
  functions that carry the current object as an argument or lexical scope, or delegating a sub-block to a
  sub-parser object that owns its own item.)
- His position: "While I don't say that any Context Variable is evil, I do prefer to use techniques that don't
  need them."

### What the example demonstrates (concepts only)

**Reading an INI file (C#).** Fowler picks INI deliberately as a minimal illustration. His aside on format
choice is worth keeping: INI can seem old-fashioned — it was "improved" by the Windows Registry — but it
remains a lightweight, readable way to handle a **simple list of items with properties**. XML and YAML handle
more complex structures, "but at a cost of readability and parsing difficulty. If your needs are simple enough
for an INI file, it remains a reasonable choice." (Ch. 13, "Reading an INI File (C#)")

The parse is *Delimiter-Directed Translation*: read a line at a time, strip comments, skip blanks, then
dispatch on whether the line is a section header or a property. The Context Variable `currentProject` is
**assigned** when a section header is recognized and **read** by every property line that follows. The
Semantic Model is trivial (a `Project` with `Code`, `Name`, `Lead`).

One extra technique demonstrated: property assignment is done by **reflection** on the property name rather
than a hand-written switch. Fowler's tradeoff note: "Using reflection makes the code more complex, but it does
mean that I don't need to update the parser when I add more properties to the Semantic Model."

### Relationships to other patterns

- **Construction Builder (Ch. 14)** — the alternative content for the variable when the model object isn't
  freely mutable during the parse.
- **Semantic Model (Ch. 11)** — the usual thing being pointed at.
- **Delimiter-Directed Translation (Ch. 17)** — the parsing style that most often needs Context Variables,
  precisely because line-at-a-time parsing has no natural nesting to carry context.

### SDK relevance

Mild, but real: this is the classic critique of **stateful, order-dependent "current object" APIs** (think
`setCurrentX()` then a sequence of mutators). They're easy to write and easy to get wrong. Prefer passing the
target explicitly, or scoping it with a block/closure/context manager so the "current" thing is lexically
obvious and cannot leak past its region.

---

## Chapter 14: Construction Builder

> **Intent:** "Incrementally create an immutable object with a builder that stores constructor arguments in
> fields." (Fowler, Ch. 14 "Construction Builder", intent line)

### The core idea

You want the product object to be **immutable**, but you can only discover its field values **gradually**.
Construction Builder resolves the tension: a mutable scratch object accumulates the values, then hands you a
fully-formed immutable product in one shot.

### How it works

The recipe is deliberately simple (Ch. 14, "How It Works"):

1. Take each of the product's constructor arguments and **make a mutable field for each** on the builder.
2. Add further fields for any other attributes of the product you're collecting.
3. Add a method that **creates and returns a new product object** assembled from all the data in the builder.

**Optional lifecycle controls** you may want to add:
- Check whether you have enough information to create the product before allowing creation.
- Set a flag once you've returned a product, to prevent returning it again — or stash the created product in a
  field.
- Raise an error if someone tries to add new attributes to the builder *after* the product has been created.

**Composition:** multiple Construction Builders can be combined into deeper structures, so they produce a
*group of related objects* rather than a single object. (The example does exactly this: a flight builder owns a
list of leg builders.)

### When to Use It

Use it whenever you need to create an object with **multiple immutable fields** whose values you gather
**gradually**. The builder gives you "a coherent place to put all this data before you actually create the
product."

**Alternatives Fowler considers and rejects:**

- **Local variables or loose fields.** Capture the pieces in locals until you can call the constructor. This
  works fine for one or two products, "but soon gets confusing if you need to create a bunch of objects at
  once, such as when you're parsing." (The parse case is exactly the one where you have many half-built
  objects alive simultaneously.)
- **Copy-on-write on the real model object.** Create an actual model object, and each time you learn one more
  immutable attribute, create a new copy with that attribute changed and replace the old one. This saves you
  writing a builder, but is "generally more awkward to do and follow." The killer objection: **it doesn't work
  if you have multiple references to the object** — or at minimum it becomes much harder, because you have to
  chase down and replace every reference. (This objection is exactly why it fails for graph-shaped Semantic
  Models with cross-references, e.g. a state machine.)

**The scope limit:** "you only need it when you have immutable fields. If that's not the case, then just create
your product objects directly." Don't reach for a builder reflexively.

### Construction Builder vs. Expression Builder

Fowler is emphatic that despite the shared word "builder" these are **different patterns** (Ch. 14, "When to
Use It"):

- **Construction Builder** is *purely* about gradually building up constructor arguments. It makes **no
  attempt to provide a fluent interface**.
- **Expression Builder** is focused on providing a **fluent interface** — it exists to shape the *reading
  experience* of the DSL.

It's not unusual to find a single object that is both, "but that doesn't mean they are the same concept." This
is a useful separation-of-concerns point: *staged construction* and *fluent surface syntax* are orthogonal
design decisions that happen to be frequently combined.

### What the example demonstrates (concepts only)

**Building simple flight data (C#).** The application only ever *reads* flight data, so the domain classes are
deliberately read-only — `Flight` has readonly fields, getter-only properties, and exposes its legs as a
read-only list; `Leg` is likewise immutable. But the data arrives in a way that makes it awkward to build fully
formed objects via constructors. So a `FlightBuilder` carries plain mutable properties plus a **list of
`LegBuilder`s**, and a `Value` accessor constructs the immutable `Flight` from the accumulated data, converting
each `LegBuilder` to a `Leg` on the way.

What it demonstrates conceptually:
- Immutability is a property of the **finished domain model**, not a constraint on the **construction process**.
- **Nested builders mirror the nested product structure**, and the top-level `Value` cascades down.
- The builder is a genuinely separate type with a different (mutable, permissive) interface from the product.

### Relationships to other patterns

- **Semantic Model (Ch. 11)** — the product is typically a Semantic Model object; the builder is part of the
  population machinery.
- **Symbol Table (Ch. 12)** — putting builders rather than final model objects into the Symbol Table is what
  makes forward references practical.
- **Context Variable (Ch. 13)** — when the model object isn't mutable enough, the Context Variable holds a
  Construction Builder instead.
- **Expression Builder** — often the same object, conceptually distinct.

### SDK relevance

Direct and high:
- This is the canonical justification for **builder types in a library API**: you want your public value
  objects immutable (safe to share, safe to cache, thread-safe, equality-friendly), yet callers assemble them
  over many steps. Don't compromise the product's immutability to make construction convenient — add a builder.
- **Lifecycle controls belong on the builder**, not the product: completeness validation at `build()` time,
  single-use enforcement, and rejecting mutation after build. These give clear, early errors instead of
  half-built products escaping into the system.
- **Nest builders to mirror nested immutable structures**, rather than exposing mutable collections on the
  product.
- Keep **staged construction separate from fluent chaining** in your thinking. Fluency is an ergonomics
  decision layered on top; the builder's job of holding constructor arguments is what actually earns its keep.
- The rejected alternative — "copy the object with one field changed each time" — is a real anti-pattern to
  recognize in the wild, and Fowler's identity/aliasing objection (multiple references to replace) is the
  precise reason it breaks down at scale.

---

## Chapter 15: Macro

> **Intent:** "Transform input text into a different text before language processing using Templated
> Generation." (Fowler, Ch. 15 "Macro", intent line)

This is the chapter where Fowler argues *against* a technique at length. It is the longest of the six and is
essentially a catalogue of failure modes.

### The core idea

A language has a fixed set of forms and structure it can process. Sometimes you can see a way to add
abstraction to a language by manipulating its input text with a purely textual transformation **before** that
text is parsed by the compiler or interpreter. Since you know the final form you want, it makes sense to
describe the transformation by **writing the desired output with callouts for the parametrizable values** —
i.e. a template. A Macro lets you define these transformations, either purely textually or as a **syntactic
macro** that understands the syntax of the underlying language.

### The two varieties

- **Textual macros** — treat text as text. More familiar and easier to understand. A textual macro processor
  can operate on **any** language that's represented as text, which is pretty much any language.
- **Syntactic macros** — aware of the *syntactic structure* of the host language, so it's easier to ensure they
  operate on syntactically sensible units of text and produce syntactically valid results. A syntactic macro
  processor is designed to work with **only a single language**; it's often baked into that language's tooling
  or even into the language specification itself.

Historical framing: macros are one of the oldest abstraction techniques in programming. "In the early days of
programming, macros were as prevalent as functions. Since then, they've largely fallen out of favor, mostly for
good reasons." They survive mainly in internal DSLs, particularly in the Lisp community.

### Textual macros — how they work

Most modern languages don't support them and most developers avoid them, but you can apply textual macros to
*any* language using a generic macro processor such as **m4**. Template engines such as **Velocity** are very
simple macro processors and can be pressed into service. C (and thus C++) has a preprocessor built into the
basic tooling; "C++ gurus mostly tell people to avoid the preprocessor, with good reason, but it's still there."

**Simplest form — symbolic substitution.** The illustrative example is CSS: a color used repeatedly across
table borders, line colors, and text highlighting has to be repeated as a raw hex code everywhere. Duplication
makes updating hard, and the raw code obscures meaning. With a macro processor you define a name
(`MEDIUM_SHADE`) and use that instead. Two important observations Fowler draws out:

- The file you now edit **isn't proper CSS anymore**. The language lacks symbolic constants, "so you've
  enhanced the CSS language with a macro processor." That's precisely the DSL move — the macro processor is the
  language extension mechanism.
- This particular substitution could equally be done with *Textual Polishing* (simple search-and-replace).
  Trivially simple, yet it's a common and genuinely useful use of macros in C. The same mechanism handles
  including **common elements into files** — define a marker in a pre-HTML file, run the substitution, get real
  HTML. "A simple trick like this is remarkably handy for small websites that want a common header and footer
  without duplicating it on every page."

**Parametrized textual macros.** `#define max(x,y) x > y ? x : y`. The critical semantic difference from a
function call: **the macro is evaluated at compile time**, doing a textual search-and-replace and substituting
arguments as it goes; the compiler never sees `max` at all. Historically the appeal was avoiding function-call
overhead, which C programmers worried about a great deal in the early years. (Fowler flags an annoying
terminological collision in passing: some environments use "macro" simply to mean *subroutine*.)

### The four failure modes (the heart of the chapter)

1. **Mistaken expansion.** `#define sqr(x) x * x` invoked as `sqr(a + b)` expands to `a + b * a + b`. Because
   `*` binds tighter than `+`, you get `a + (b * a) + b` rather than `(a + b) * (a + b)`. Fowler's name for it:
   *mistaken expansion* — "expansions may work most of the time but only break down in particular cases, leading
   to surprising bugs that are hard to find." Mitigation: "use more parenthesis than a Lisper" —
   `#define betterSqr(x) ((x) * (x))`. **Syntactic macros largely avoid this class**, because they know the
   host grammar.

2. **Multiple evaluation.** You pass an argument that has a side effect, and the macro body mentions that
   argument more than once, so it's evaluated more than once. `max(++a, ++b)` increments both twice. "It's
   particularly frustrating because it's hard to predict the various ways macro expansions can go wrong. You
   have to think differently than you do with function calls, and it's harder to see through consequences,
   particularly when you start nesting macros." **Syntactic macros do *not* fix this.**

3. **Variable capture (macro-declares-the-name).** A macro body that declares its own local variable — e.g. a
   `cappedTotal(input, cap, result)` macro whose body declares `int total` — silently shadows a caller variable
   of the same name. Calling `cappedTotal(arr1, 10, total)` from a scope with its own `total` means the passed-in
   variable is ignored and the caller's `total` ends up 0. "The name `total` was expanded into the macro but
   interpreted by the macro as a variable defined within the macro itself."

4. **Reverse variable capture (macro-clobbers-the-caller's-name).** The mirror-image problem, which doesn't
   occur in C but does in languages that don't force you to declare variables. Fowler illustrates with Velocity
   textual macros over Ruby code — a deliberately artificial example. The macro body assigns to `total`; when
   expanded into a program that already had a meaningful `total = 35`, the macro **silently overwrites the
   caller's variable** while still producing the correct value for the named output. The visible behavior looks
   right, so the bug lands somewhere else, later. "The consequences of the capture may be different, indeed
   worse, than the earlier form of variable capture, but both of them stem from the same basic problem."

### Syntactic macros — C++ and Lisp

Two notable exceptions that use and encourage syntactic macros:

- **C++ templates** are its syntactic macros, and they've spawned many fascinating approaches to generating
  code at compile time. Fowler declines to discuss them: partly unfamiliarity ("my C++ work predates them
  becoming common"), partly because **C++ isn't a language noted for internal DSLs** — DSLs in the C/C++ world
  are usually external, since C++ is a complex tool even for experienced programmers.
- **Lisp** is the real case. Lispers have talked about internal DSLs since the dawn of Lisp — no surprise, since
  "Lisp is all about symbolic processing—that is, about the manipulation of language." Macros have penetrated
  deeper into Lisp's heart than almost any other language; many core Lisp features are implemented as macros,
  so even a beginning Lisp programmer uses them, usually without realizing. Consequently, whenever people
  discuss language features for internal DSLs, "Lispers will always talk about the importance of macros," and
  "can be counted on to belittle any language that doesn't have macros." Fowler is careful to position himself
  as a dabbler, not a serious Lisper.

### The dominant actual use of Lisp macros: deferred evaluation

This is the most transferable insight in the chapter.

Fowler shows an *Execute-Around Method [beck-sbpp]* in Ruby: `aSafe.open do … end`, where `open` unlocks the
safe, `yield`s to the block, then locks it again. **The key point is that the content of the closure isn't
evaluated until the receiver calls `yield`**, so the receiver can open the safe *before* running the passed-in
code. Contrast `puts aSafe.open(aSafe.contents)` — that doesn't work, because the parameter is evaluated
*before* the call to `open`.

> "Deferred evaluation means that the receiving method to a call chooses when, or indeed if, to execute the code
> that's been passed in." (Ch. 15, "Syntactic Macros")

In Lisp the equivalent call written as a plain function requires wrapping the argument in a `lambda`, which
"looks way too messy." A macro restores the clean call syntax. Fowler's conclusion:

> "A large part (perhaps the majority) of the use of Lisp macros is to provide a clear syntax for the mechanism
> of delayed evaluation. A language with a cleaner closure syntax doesn't need macros for this."

That is the chapter's most important judgement: **most macro use is a workaround for clumsy closure syntax.**
If your language has good block/lambda syntax, you've already got most of the benefit without any of the four
failure modes.

He then shows that the Lisp version *still* hits variable capture (calling it with an argument symbol named
`result` collides with the macro's own local) and multiple evaluation (the `safe` parameter is used at several
points in the expansion). Lisp's mitigations:

- **Scheme: hygienic macros** — the system automatically avoids variable capture by redefining symbols behind
  the scenes.
- **Common Lisp: gensyms** — the ability to generate guaranteed-unique symbols for local variables. Gensyms are
  more trouble to use, "but they give the programmer the ability to deliberately use variable capture, and there
  are some situations when deliberate variable capture is useful" (Fowler points at Paul Graham
  *[graham-onlisp]* for that discussion).

Fixing both problems requires binding the parameter to another gensym'd local, which noticeably complicates the
macro. His verdict: **"Avoiding such issues makes macros a lot harder to write than they might seem at first
sight."** Despite that, Lispers use them heavily because closures are important for creating **new control
abstractions and alternative computational models** — the kind of thing Lispers like doing.

### The second use: Parse Tree Manipulation

Beyond deferred evaluation, Lisp macros enable **Parse Tree Manipulation**. Lisp's syntax "seems quirky on first
glance, but as you get used to it, you realize that it's a good representation of the parse tree of the
program": in each list, the **first element is the type of the parse tree node** and the remaining elements are
its **children**. Lisp programs use *Nested Functions* heavily, and the result is a parse tree. Using macros to
manipulate the Lisp code before evaluation *is* Parse Tree Manipulation.

Few programming environments support Parse Tree Manipulation, so Lisp's support is a distinguishing feature —
and it enables more fundamental manipulations of the language itself. The worked example is Common Lisp's
`setf`:

- Lisp forms lots of different data structures out of nested lists, and for each you must remember both an
  **access** function and a corresponding **update** function (`car` / `rplaca`, and so on) — "valuable brain
  cells are spent remembering an access function and an update function for each."
- `setf` takes an **access expression** and automatically calculates and applies the corresponding **update**.
  `(car (cdr aList))` accesses the second element; `(setf (car (cdr aList)) 8)` updates it.
- Limitations that reduce the magic: it only works on expressions made up of **invertible functions**. Lisp
  keeps a record of inverse functions. The macro **analyzes its first argument expression** and computes the
  update expression by finding the inverse. As you define new functions you can register their inverses and
  then use `setf` on them.
- **The load-bearing point:** to define `setf` you *need* macros, because `setf` depends on the ability to
  parse the input expression. **"This ability to parse its arguments is the key advantage of Lisp macros."**

Macros work well for Parse Tree Manipulation *in Lisp* because Lisp's syntactic structure is so close to the
parse tree. But macros aren't the only route — Fowler cites **C#** as a language that supports Parse Tree
Manipulation by giving you the parse tree for an expression plus a library to manipulate it (i.e. expression
trees).

### When to Use It

**The appeal** on first encounter: textual macros can be used with any text-based language, they do all their
manipulation at compile time, and they can implement very impressive behaviors that are beyond the abilities of
the host language.

**The costs:**
- Subtle bugs — mistaken expansions, variable capture, multiple evaluation — are "often intermittent and hard to
  track down."
- **Macros don't appear in downstream tools.** "The abstractions they provide leak like a sieve without the
  wires, and you get no support from debuggers, intelligent IDEs, or anything else that relies on the expanded
  code."
- **Nested macro expansion is much harder to reason about than nested function calls.** Fowler concedes this
  could be a lack of practice, "but I suspect it's something more fundamental."

**Verdict on textual macros:** "I don't recommend using textual macros in anything but the very simplest cases."
For *Templated Generation* they work acceptably, **provided you avoid trying to be too clever with them — in
particular, avoiding nesting the expansions.** Otherwise "they are simply not worth the trouble."

**Verdict on syntactic macros:** most of the same reasoning applies. You're less likely to get mistaken
expansions, "but the other problems still crop up. This makes me very wary of them." The counterexample is the
heavy, successful use of syntactic macros in Lisp; as an outsider Fowler is reluctant to judge too hard, and his
sense is that "they do make sense for Lisp, but I'm not convinced that the logic of using them there makes sense
for other language environments."

**The practical shape of the decision** (Ch. 15, "When to Use It"):
- Most language environments don't support syntactic macros at all, "so there's no choice to worry about."
- Where you *do* have them (Lisp, C++), "they are often necessary to do useful things, so you have to become at
  least a little familiar with them." **The choice on using syntactic macros is really made for you by your
  language environment.**
- The only genuine choice left is whether syntactic macros are a *reason to choose a language that has them*.
  Fowler's position: "For the moment, I see macros as a worse choice than available alternatives, and thus a
  point deducted from those environments that use them" — explicitly hedged with the rider that he hasn't worked
  closely enough with those languages to be completely sure.

### Relationships to other patterns

- **Templated Generation** — the only use Fowler blesses for textual macros.
- **Textual Polishing** — the simplest substitution cases can just be done with search-and-replace instead.
- **Closures / Nested Closure** — the *preferred alternative* for the deferred-evaluation use case that
  motivates most Lisp macros.
- **Parse Tree Manipulation** — the other Lisp-macro use case; also reachable via C#'s expression trees.
- **Nested Functions** — what makes Lisp code parse-tree-shaped in the first place.

### SDK relevance

- **Prefer closures/blocks/lambdas over macros for deferred evaluation.** Fowler's strongest claim in this
  chapter is that most macro usage is compensating for poor closure syntax. In a modern SDK, "execute-around,"
  resource scoping, retry wrappers, and transaction blocks should all be *higher-order functions taking a
  callback*, not code-generation.
- **The "leaks like a sieve without the wires" objection is a general test for any code-generation or
  metaprogramming feature you ship**: does it survive into the debugger, the stack trace, the type checker, and
  the IDE? If your abstraction disappears from downstream tooling, users pay for it during every incident.
- **Multiple evaluation and name capture generalize** to any API that takes an expression/thunk and may run it
  zero, one, or many times. Document evaluation cardinality explicitly.
- **Avoid nesting generated abstractions.** Even where macro-like generation is acceptable (templating), nesting
  is where reasoning collapses.

---

## Chapter 16: Notification

> **Intent:** "Collects errors and other messages to report back to the caller."
> (Fowler, Ch. 16 "Notification", intent line)

### The core idea

You've carried out operations that made significant changes to an object model, and now you want to check the
result is valid. You initiate a validation command. You want the answer as a **simple Boolean**, but if there
*are* errors you want to know more — and in particular you want to know about **all** the errors rather than
having validation stop at the first one.

A Notification is an object that **collects errors**. When a validation check fails it adds an error to the
Notification. When the validation command finishes, it **returns the Notification**. The caller can then ask
whether everything was OK, and if not, delve into the errors.

### How it works

- The basic form is simply **a collection of errors**. During the notified task you need the ability to add an
  error: as simple as a message string, or as involved as a structured error object.
- When the task is done, the Notification goes back to the caller. The caller invokes a **simple Boolean query
  method** to see if all is well. If there are errors, it may interrogate the Notification further to display
  them.
- **Getting the Notification to where errors happen.** It usually needs to be available to several methods in
  the model. Two options:
  - Pass it in as an argument — a **Collecting Parameter** *[beck-ip]*.
  - **Stash it in a field**, if there's an object corresponding to the task at hand (such as a validator object
    or a parse-helper object) that can own it for the duration.
- **Beyond errors.** The primary purpose is collecting errors, but it's sometimes useful to capture **warnings**
  and **informational messages** too. Fowler's definitions (Ch. 16, "How It Works"):
  - an **error** indicates the requested command has *failed*;
  - a **warning** occurs for something that doesn't fail but is still a matter of potential concern to the
    caller;
  - an **informational message** is just some potentially handy information.
- **"In many ways, a Notification is an object acting like a log file, so many of the features commonly found in
  logging can be useful here."** (severity levels, formatting, filtering, structured payloads, report rendering)

### When to Use It

The tradeoff is crisp and is essentially **fail-fast vs. collect-all**:

- Use a Notification "whenever there is a complicated operation that may trigger multiple errors and you don't
  want to fail at the first error."
- **"If you do want to fail at the first error, then you can simply throw an exception."** A Notification is
  what you use when you want to store multiple errors "to give the caller a fuller picture of what the request
  led to."
- Second motivating situation: **when a user interface initiates an operation at a lower layer.** "The lower
  layer should not try to interact with the user interface directly, so a Notification makes an appropriate
  messenger." (i.e. it's a layering/decoupling device as much as an error-handling one — the lower layer
  *reports*, it doesn't *present*.)

### What the examples demonstrate (concepts only)

**1. A very simple Notification (C#).** Errors stored as plain strings. Two design decisions worth carrying
away:

- `AddError` takes a **format string plus params array**, formatting internally. "Using a format string and
  parameters makes it a bit easier to use the notification to capture errors, as the client code doesn't need
  to build the format string." — i.e. push message assembly *into* the Notification so call sites stay
  one-liners.
- It provides both **`IsOK` and `HasErrors`** Boolean queries (deliberate redundancy so the caller can write
  whichever reads better), **and** an **`AssertOK()`** method that throws a `ValidationException` if there are
  errors. That last one is the important ergonomic point: *"Sometimes this fits the flow of usage better than
  using the Boolean check methods."* — **offer both a query-style and a throw-style consumption path** over the
  same collected data, so callers can choose collect-all or fail-at-the-boundary.

**2. Parsing Notification (Java, from the Foreign Code example).** More involved and more specific: it accepts
specific *kinds* of error rather than strings.

- It lives in the **Embedment Helper** of an ANTLR-generated parser, since it's part of the parse. At the end of
  `run()`, if the notification has errors, the whole parse is failed with a single exception carrying the
  accumulated report. This is the **collect-then-fail-once** shape: gather everything during the operation,
  raise a single well-populated failure at the boundary.
- It handles **two distinct error sources** and unifies them:
  1. **Errors from the parser generator itself** (ANTLR recognition exceptions). ANTLR has default behavior for
     these; Fowler overrides the error-reporting method in the grammar's `members` section so the error is
     *also* captured in the Notification (delegating to `super` so default behavior is preserved).
  2. **Semantic errors detected by the translation code** — e.g. a product ID in the script that doesn't exist
     in the repository. Recorded as "No product for %s" and, importantly, the **offending token is passed in**,
     not just its text.
- **Internal structure:** the error list holds message *objects*, not strings. A `ParserMessage` superclass
  exists essentially as a **marker to make the generics work** ("In time, I might add something to it, but for
  the moment a bare marker suffices"). Two subclasses: one wrapping ANTLR's recognition exception, and one
  (`TranslationMessage`) holding the token plus the formatted message, whose `toString` renders
  `"<message> (near line N char M)"`. **"By passing the token in, I'm able to provide better diagnostic
  information."**
- Usual accessors: `isOk` / `hasErrors`, plus `toString`/`report` to render the whole set of errors as a report.

**Fowler's closing design principle for the chapter:**

> "I think the most important point here is to build a Notification that makes the calling code as simple and
> compact as possible. Therefore, I pass all the relevant data to the Notification and let the Notification sort
> out how to compose error messages from this data." (Ch. 16, "Parsing Notification (Java)")

That is: **call sites hand over raw structured context (token, object, values); the Notification owns
formatting and presentation.** Not the reverse.

### Relationships to other patterns

- **Semantic Model (Ch. 11)** — validations run over a populated Semantic Model are the archetypal producer of
  Notifications; Ch. 11 explicitly says validation belongs in the Semantic Model and should run before
  interpretation or code generation.
- **Collecting Parameter *[beck-ip]*** — the mechanism for threading the Notification through many methods.
- **Embedment Helper / Foreign Code / Embedded Translation** — where the parsing Notification lives in the
  external-DSL examples.

### SDK relevance

Very high — this is a general error-handling pattern with almost nothing DSL-specific about it:

- **Batch validation should collect, not fail fast.** Any API that validates a document, config, schema,
  request payload, or migration should return *all* the problems in one pass. Returning one error at a time
  forces users into an infuriating fix-rerun loop.
- **Offer both consumption styles over the same result**: a Boolean/`is_ok` query for callers who want to branch,
  and an `assert_ok()`/`raise_for_status()`-style method for callers who want an exception at their own
  boundary. Do not force the choice on them.
- **Structured messages beat strings.** Carry the *location* (token, line/column, JSON path, field name) and the
  *offending value* as data on the message object; render human text only at the edge. This is what makes errors
  machine-consumable (IDE squiggles, CI annotations) as well as readable.
- **Keep formatting out of call sites.** Accept a template plus arguments, or raw context, and let the
  collector compose the message — this keeps error-raising code to a single readable line and keeps message
  wording consistent and centrally changeable.
- **Layering discipline:** a lower layer should return a Notification rather than printing, logging at the user,
  or otherwise reaching up into the presentation layer. The Notification is the messenger across the layer
  boundary.
- **It behaves like a log.** Severity levels (error/warning/info), a rendered report, and structured entries are
  all reasonable features to borrow from logging APIs.

---

## Cross-chapter synthesis: how these six fit together

A single mental picture ties Part II together, centered on Semantic Model:

```
DSL script text
      │
      ▼
   Parser  ──── uses ────►  Symbol Table (Ch. 12)   ── holds ──►  model objects
      │                          ▲                                    or builders
      │                          │
      │                     Context Variable (Ch. 13)  ── points at ──┘
      │                     ("current item" during parse)
      │
      ├──── populates via the POPULATION INTERFACE ────►  Semantic Model (Ch. 11)
      │            (using Construction Builder, Ch. 14,                │
      │             when model objects are immutable)                  │
      │                                                                │
      └──── errors during parse ──►  Notification (Ch. 16)  ◄── validation over the model
                                                                       │
                                                          OPERATIONAL INTERFACE
                                                                       │
                                                    ┌──────────────────┴──────────────────┐
                                              interpret directly              generate code / visualize
```

- **Semantic Model** is the hub; every other pattern is defined in terms of populating, referencing, or
  validating it.
- **Symbol Table** resolves script identifiers to model objects; its values are model objects for simple cases
  and **Construction Builders** when forward references or immutability demand it.
- **Context Variable** tracks *which* model object (or builder) the parse is currently filling in — and Fowler
  treats it as a necessary evil, preferring parse organizations that avoid it.
- **Construction Builder** exists solely to reconcile *immutable products* with *gradual discovery of values*,
  and is explicitly **not** the same idea as a fluent Expression Builder.
- **Notification** is how validation over the model, and errors during the parse, get reported back **in bulk**
  rather than one-at-a-time.
- **Macro** is the outlier — a technique Fowler documents mainly so he can recommend against it outside
  Templated Generation and Lisp, and whose main legitimate use case (deferred evaluation) is better served by
  closures.

**The three highest-value takeaways for API/SDK work**, independent of DSLs entirely:

1. **Separate the model from its front ends** (Ch. 11). The model must be complete and usable through an
   ordinary programmatic interface; parsers, config loaders, CLIs, and DSLs are just populators. Design the
   operational interface before the population interface by pretending the object already exists.
2. **Use builders to keep products immutable** (Ch. 14). Immutability is a property of the finished object, not
   a constraint on how it gets assembled — and lifecycle checks (completeness, single-use, post-build mutation)
   belong on the builder.
3. **Collect errors instead of failing fast when the operation is complex** (Ch. 16), carry structured location
   data on each message, let the collector own formatting, and give callers both a query and a throw path.
