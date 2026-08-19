# Foundational Patterns

Condensed from Fowler, *Domain-Specific Languages* (2010), Part II (Ch. 11–16) — the six patterns that apply whether your language is internal or external, and which the rest of the catalog is defined in terms of.

Semantic Model is the hub. The other five describe how you populate it (Construction Builder), how you resolve names into it (Symbol Table), how you track position while populating it (Context Variable), how you report what went wrong (Notification), and one technique to mostly avoid (Macro).

**If you read only one section, read Semantic Model.** It is the most transferable API-design advice in the book, and it holds even when no DSL is involved.

## Contents

- [Semantic Model (Ch. 11)](#semantic-model-ch-11)
- [Symbol Table (Ch. 12)](#symbol-table-ch-12)
- [Context Variable (Ch. 13)](#context-variable-ch-13)
- [Construction Builder (Ch. 14)](#construction-builder-ch-14)
- [Macro (Ch. 15)](#macro-ch-15)
- [Notification (Ch. 16)](#notification-ch-16)

---

## Semantic Model (Ch. 11)

> **Intent:** "The model that's populated by a DSL." *(Ch. 11, intent line)*

### Concept

Don't let the parser *be* the program. Instead of performing effects as you read each line, build an ordinary in-memory object model of the *same subject matter* the language describes — for a state machine DSL, classes for `State`, `Event`, `Transition`. A script then corresponds to a particular **population** of that schema. The script is data; the model is the thing that knows what a state machine *is*.

The sentence to memorize: the Semantic Model is **"the library or framework that the DSL populates"** *(Ch. 11, "How It Works")*. The DSL is not the thing — it is a *front end* for populating something that could exist perfectly well without it.

The representation need not be an in-memory object model. It can be plain data with behavior supplied by functions over it, and it need not be in memory at all (a DSL could populate a model held in a relational database). Fowler uses object models because that is what he knows best, not because the pattern requires it.

### The decisive rule: usable without the DSL

> The Semantic Model **should be usable without a DSL present.** You should be able to populate it through an ordinary command-query interface. *(Ch. 11, "How It Works")*

Two reasons:

1. **Completeness.** If a concept can only be expressed by going through the parser, that concept lives *in the parser* and the model is incomplete.
2. **Independent testability.** Test semantics by populating the model directly and asserting on behavior; test the parser by asserting it produced the right population.

If populating the model requires going through the DSL, you have smeared semantics into your parser and lost the whole benefit.

**Behavioral test** *(Ch. 32, "How It Works")*: you should be able to write tests for the Semantic Model that use no DSL at all. Fowler tempers this — the point of an internal DSL is to make these objects *easier* to work with, so most tests will naturally use the DSL — "But I'd usually include at least some tests that only use the command-query interface."

### The two interfaces

Think of the Semantic Model as having **two distinct interfaces** *(Ch. 11, "How It Works")*:

1. **Operational interface** — what clients use to *do work with* an already-populated model. Assumes the model exists; makes it easy for the rest of the system to exploit.
2. **Population interface** — what the DSL/parser uses to *create* instances. Used only by parsers and by the model's own tests.

The population interface is also a **decoupling seam**. Some dependency is unavoidable — the parser must see the model to populate it — but making the population interface an explicit, deliberately designed boundary means an implementation change inside the model rarely forces a parser change. Fowler reports exactly this payoff: he refactored the state machine model's internals without touching parsing code, because the population interface didn't change *(Ch. 11, "The Introductory Example (Java)")*.

### The "pretend the model is magically already there" trick

Fowler presents this as a rule of thumb for *any* objects, not just DSL-ish ones:

> **Assume the model is magically already there, then ask yourself how you would use it.**

Define the operational interface **first**, even though at runtime the population interface necessarily executes first. Counterintuitive, but it produces better designs *(Ch. 11, "How It Works")*.

Why it works: construction concerns are seductive and dominant. Design construction first and every later decision is shaped by "how do I get the values in?" — a question your users mostly don't care about. Designing usage first forces "what does the caller want to ask this thing?", which is what determines whether the abstraction is any good.

### Semantic Model vs. Domain Model

Similar to Domain Model *[PoEAA]*, but a separate term for four reasons *(Ch. 11, "How It Works")*:

- Semantic Models are often *subsets* of Domain Models, but need not be.
- "Domain Model" implies behaviorally rich objects; a Semantic Model **may be data alone**.
- A Domain Model captures an application's core behavior; a Semantic Model may play only a supporting role.
- The clarifying case: a DSL describing object-relational mappings produces a Semantic Model consisting of the *Data Mappers* — **not** the Domain Model that is the subject of the mapping.

The thing your language talks *about* and the thing your language *builds* are different objects.

### Semantic Model vs. syntax tree / AST

This distinction is the crux of the pattern *(Ch. 11, "How It Works")*:

- A **syntax tree corresponds to the structure of the DSL script.** Even an *abstract* syntax tree, which simplifies and reorganizes somewhat, still takes fundamentally the same form as the input.
- A **Semantic Model is based on what will be done with the information.** It often has a substantially different structure and is usually **not a tree at all** — graphs with cross-references are common. A state machine's transitions point at *shared* state and event objects; a tree cannot express that sharing.

Occasionally an AST *is* an effective Semantic Model, but "these are the exception rather than the rule." Compiler literature lacks the term because for a general-purpose language a syntax tree is a fine basis for code generation; where compiler people do build one (e.g. a call graph for optimization) they call it an **intermediate representation**.

### Where the model comes from

Two origin stories *(Ch. 11, "How It Works")*:

- **Model precedes the DSL.** You have a Domain Model and decide some portion is better populated from a DSL than through the regular command-query interface. The DSL layers on top.
- **Model and DSL built together**, with domain-expert discussions refining both the language's expressions and the model's structure. Each informs the other.

### Execution: interpreter vs. compiler style

The model can **hold the code to execute itself** (interpreter style) or **be the basis for code generation** (compiler style). Even when generating code, *also* provide interpretation — it helps enormously with testing and debugging, and lets you use the model as a **simulator for the generated code** *(Ch. 11, "How It Works")*.

Because the generator works off the model rather than the parser, multiple code generators become cheap — no duplicating parser logic per generator.

### Validation belongs in the model

The Semantic Model is "usually the best place for validation behavior, since you have all the information and structures in place to express and run the validations" *(Ch. 11, "How It Works")*. Run validations **before** interpreting or generating code.

The state-machine validations were: no unreachable states, no states you can't get out of, all events and commands actually used *(Ch. 11, "The Introductory Example (Java)")*. None are *syntactic* — you cannot express them as grammar rules or check them one line at a time. They are properties of the whole populated graph, which is exactly why they belong to the model, not the parser.

This is where **Notification (Ch. 16)** joins: validations over a populated model naturally want to report *all* problems at once rather than aborting on the first.

### Computational vs. compositional

Fowler cites Brad Cross's distinction *[cross-comps]* and observes it is really about the *kind of Semantic Model* produced *(Ch. 11, "How It Works")*:

- **Compositional** — describes a composite structure in textual form (XAML describing a UI layout). The primary form of the model is *how elements are composed*.
- **Computational** — the model "feels more like code than data" and drives computation, usually with an alternative computational model instead of the usual imperative one. Typically an **Adaptive Model**. The state machine is of this kind.

> "You can do a lot more with a computational DSL, but people often find them more difficult to work with."

Carry this into SDK work: a configuration API assembling a structure (pipeline, schema, UI tree) is compositional — its model is mostly data and its job is composition rules. An API letting users express *behavior* (rules, policies, predicates, retry strategies) is computational — its model holds executable fragments and its job is evaluation. The second is more powerful and materially harder for users.

### When to use it — and when not

Fowler's answer is essentially *always*, and he is self-aware about it: absolute advice usually signals closed-minded thinking, but he sees very few cases where you wouldn't want one, and those are all very simple *(Ch. 11, "When to Use It")*.

**Arguments for:**

1. **Separate testing of semantics and parsing.**
2. **Multiple parsers become tractable** — check two parsers are semantically equivalent by comparing the populations they produce. Fowler added a new DSL+parser over one model without duplicating code in the other parsers or altering the model.
3. **Independent evolution** — more common than multiple DSLs is simply evolving DSL and model separately.
4. **Flexibility in execution** — interpretation, code generation off the model, both at once (model-as-simulator), multiple generators, plus non-execution outputs like visualizations.
5. **The most important reason, in his words:** it "separates thinking about semantics from thinking about parsing. Even a simple DSL contains enough complexity to justify dividing it up into two simpler problems."

**The exceptions he envisages** *(Ch. 11, "When to Use It")*:

- **Simple imperative interpretation** — you execute each statement as you parse it. A calculator evaluating arithmetic expressions is the canonical case.
- **When the AST already *is* the model.** For arithmetic expressions the AST is pretty much what a Semantic Model would be anyway. Generalized: *if you can't think of a more useful model than the AST, there's little point creating a separate Semantic Model.*
- **Code generation directly off the AST** — the most common real-world skip. Reasonable *provided* the AST is a good model of the underlying semantics **and** you don't mind coupling code generation to the AST. If either condition fails, it's often simpler to transform the AST into a Semantic Model and generate from that.

**His stated bias:** always *start* by assuming you need one. Even if you conclude otherwise, stay alert to increasing complexity and add one as soon as any complication creeps into the parsing logic.

**Honest caveat:** Semantic Model is not part of DSL culture in the functional programming world. Fowler's experience with modern FP is "no more than occasional experimentation," so he explicitly declines to claim his inclination applies there.

### Relationships

- **Symbol Table (Ch. 12)** — its values are usually Semantic Model objects (or builders for them); it is how textual identifiers resolve to model objects.
- **Construction Builder (Ch. 14)** — needed when model objects are immutable but the parse gathers field values gradually.
- **Context Variable (Ch. 13)** — the "current item" during a parse is typically a model object or a builder for one.
- **Notification (Ch. 16)** — the reporting vehicle for validations over a populated model.
- **Expression Builder (Ch. 32)** — the fluent front end that populates the model; explicitly *not* part of the model.
- **Adaptive Model** — the usual form for a computational DSL.

> **SDK lens:** The most important idea in the book for library authors, and it holds with no DSL in sight. Design a core model fully usable and testable through an ordinary programmatic interface, and treat *every* other surface — fluent builder, YAML loader, CLI, config decorator, code generator — as a second-class front end that merely populates it. Everything a front end can express must be expressible directly. Same discipline as "the CLI is a client of the library, not the other way around." Three practices follow: (1) design the operational interface first by pretending the object already exists and writing usage code before construction code; (2) make the population interface an explicit, narrow boundary so internal refactoring doesn't ripple into every loader and adapter; (3) put validation in the model, not the loader, so it applies regardless of which front end produced the object. Treat multiple front ends as a design *test*: if two very different surface syntaxes both populate the model and produce equivalent populations, the model is probably factored at the right level.

---

## Symbol Table (Ch. 12)

> **Intent:** "A location to store all identifiable objects during a parse to resolve references." *(Ch. 12, intent line)*

### Concept

Scripts refer to the same object at several points — one task's definition must *name* other tasks. Invent a **symbol** per object and, while processing, store the link between symbol and the object holding the full information. The essential purpose is to **map between the symbol used in the script and the object it refers to** *(Ch. 12, "How It Works")*. That maps onto a dictionary; the common implementation is a map from symbol to **Semantic Model** object.

### Judgement calls

**Key type.** Strings are the obvious choice because DSL text *is* string. Prefer a genuine **symbol data type** where the host language has one *(Ch. 12, "How It Works")*: symbols are structurally like strings but many string operations (concatenation, substring) make no sense for them; a symbol's principal task is lookup, and two occurrences of a symbol literal always resolve to the *same* object and compare much faster than two `"foo"` string objects compared by content. Performance may not matter for small DSLs — **the big reason is intent communication**, plus symbol literals make symbols visually stand out in an internal DSL.

**Value type.** Either **final model objects** (Symbol Table acts as *result data* — good for simple situations) or **intermediate builders** (more flexibility at the cost of a bit more work) *(Ch. 12, "How It Works")*.

**One map, several maps, or a special class?** When the language has different *kinds* of referent (states, commands, events) *(Ch. 12, "How It Works")*:

- **Single map for everything** — you cannot reuse a name across kinds, which may be a *useful* constraint for reducing confusion, but processing code gets harder to read because the kind being manipulated is unclear. **Fowler does not recommend this.**
- **Multiple maps, one per kind** — **Fowler's preference**; processing code makes clear which kind is referenced at each step.
- **A special class** with kind-specific methods (`getEvent(code)`, `registerEvent(code, event)`) — sometimes useful, gives a natural home for symbol-processing behavior; most of the time Fowler sees no compelling need.

**Forward references.** DSLs usually don't have declare-before-use rules, so forward references often make sense. If you allow them, **any reference to a symbol must populate the entry if it isn't already there** *(Ch. 12, "How It Works")*. Mechanic: a `register(name)` helper that **creates the object lazily** if absent, called for *both sides* of every reference — the table is populated by and consulted by the same code path. This pushes you toward builders as values, unless model objects are very flexible about being filled in later.

**Misspelled symbols.** Without explicit declaration, a typo silently creates a new unrelated entity. If there's any way to detect misspellings, put that checking in; it "will prevent a lot of hair-pulling" *(Ch. 12, "How It Works")*. One reason to *require* symbol declaration — which does **not** mean requiring declaration *before* usage.

**Nested scopes.** Common in general-purpose languages, "much rarer in simpler DSLs." If needed, use *Symbol Table for Nested Scopes* *[parr-LIP]*.

**Statically typed symbols.** A string-keyed hashmap works in a statically typed host, but has four costs *(Ch. 12, "Statically Typed Symbols")*: (1) **syntactic noise** from quoting; (2) **no compile-time checking** — misspellings surface at runtime, and the compiler can't catch a reference to the wrong *kind* of object; (3) **no IDE autocompletion**; (4) **automated refactorings** may not work. Fix with a statically typed symbol: **enums** (simple, good) or a **Class Symbol Table (Ch. 44)** (heavier). Fowler isn't enthusiastic about static typing *for finding errors* — decent testing catches most — but values it for **IDE support**: Control-Space gives the list of symbols valid at that point.

Three judgement calls from the enum example:

- Enums "don't force inheritance or constraints on where you can write DSL script code — an advantage compared to a *Class Symbol Table*."
- If symbols must correspond to an **external data source**, write a build step that reads it and **code-generates the enum declarations** *[kabanov-hunger]*.
- A single enum implies a **single namespace**. Fine when many small scripts share one symbol set; not when scripts need different sets. Fix: define the builder against an **interface**, have several enums implement it, then selectively import only the group needed so the IDE offers only relevant symbols.

### When to use it

"Symbol Tables are common to any language-processing exercise, and I expect you'll almost always need to use them" *(Ch. 12, "When to Use It")*. Not strictly necessary when Tree Construction lets you delve the syntax tree, or a search over the Semantic Model would do — "But sometimes you need an intermediate store, and even when you don't, it often makes life easier."

### Relationships

- **Semantic Model (Ch. 11)** — the usual value type.
- **Construction Builder (Ch. 14)** — the alternative value type, and what makes forward references practical.
- **Class Symbol Table (Ch. 44)** — the statically-typed, IDE-oriented specialization.
- **Literal Extension (Ch. 46)** — its substance registry is a Symbol Table with lazy creation.

> **SDK lens:** The string-key critique is a general API critique. Any string-keyed lookup surface — feature flags, metric names, event types, config paths, resource identifiers — costs compile-time checking, autocompletion, and safe rename refactoring. Enums, sealed types, literal-union types, or generated constant modules are the fix, and **code-generating those constants from the authoritative external source** keeps them honest as it changes. Two reusable mechanics: **lazy create-on-reference** in a registry is the standard technique for accepting declarations in any order (essential for config loaders and dependency registries), and **namespace scoping via interfaces plus selective imports** gives one shared builder several disjoint vocabularies without generics. Finally: if your API accepts free-form identifiers with no declaration step, add misspelling detection — a typo that silently creates a new entity is one of the most expensive bug classes you can ship.

---

## Context Variable (Ch. 13)

> **Intent:** "Use a variable to hold context required during a parse." *(Ch. 13, intent line)*

### Concept

While parsing a list of items, each piece of information can be captured independently, but you also need to know **which item** you're capturing for. A Context Variable holds the current item and is reassigned as you move on. Canonical sketch: an INI file where a `[section]` header assigns `currentProject = new Project(...)` and following `name = …` / `lead = …` lines all operate on `currentProject` *(Ch. 13, sketch)*.

That's the whole mechanism. You have a Context Variable whenever a variable named like `currentItem` is updated periodically during a parse. The pattern exists mainly to *name* the thing so its costs can be discussed.

### What goes in it

Either a **Semantic Model object** or a **builder**. A model object is superficially more straightforward, but only if *all* its properties are mutable at the moments the parse needs to change them. Otherwise use a **Construction Builder (Ch. 14)** to gather information and create the model object at the end *(Ch. 13, "How It Works")*.

### When to use it — mostly a warning

The "when to use it" is largely a caution *(Ch. 13, "When to Use It")*:

- There are many places where you must keep context during a parse, and a Context Variable is the obvious choice — easy to create, easy to get going with.
- **But they are problematic, particularly as you get more of them.** "By their nature, they are mutable state that has to be kept track of, and bugs adore this kind of mutable state." It's easy to forget to update the variable at the right moment, and debugging that is difficult.
- There are usually **alternative ways of organizing the parse that reduce the need** — nested closures or nested functions carrying the current object as an argument or in lexical scope, or delegating a sub-block to a sub-parser that owns its own item.
- His position: **"While I don't say that any Context Variable is evil, I do prefer to use techniques that don't need them."**

The concrete cost shows up in Function Sequence *(Ch. 33)*: a `speed()` clause that could mean processor speed or disk speed must branch on which context variable is currently set and throw if neither is. Clause-name resolution degrades from a compile-time question into a runtime state inspection.

Two smaller lessons from the INI example *(Ch. 13, "Reading an INI File (C#)")*. On format choice: INI remains a lightweight, readable way to handle a **simple list of items with properties**; XML and YAML handle more complex structures "but at a cost of readability and parsing difficulty. If your needs are simple enough for an INI file, it remains a reasonable choice." On assignment: the example uses **reflection** on the property name rather than a hand-written switch — "Using reflection makes the code more complex, but it does mean that I don't need to update the parser when I add more properties to the Semantic Model."

### Relationships

- **Construction Builder (Ch. 14)** — the alternative content when the model object isn't freely mutable during the parse.
- **Function Sequence (Ch. 33)** — the technique that *forces* Context Variables.
- **Nested Function (Ch. 34)** — eliminates them by passing data through return values.
- **Nested Closure (Ch. 38)** — tames them by scoping their lifetime to a closure invocation.
- **Delimiter-Directed Translation (Ch. 17)** — the parsing style that most often needs them; line-at-a-time parsing has no natural nesting to carry context.

> **SDK lens:** This is the classic critique of **stateful, order-dependent "current object" APIs** — `setCurrentX()` followed by mutators, or a builder with a `currentThing` field every clause consults. Easy to write, easy to get wrong: order-dependence, thread-safety hazards, ambiguous method names that must dispatch on state, and errors surfacing at runtime instead of at the call site. Prefer passing the target explicitly, or scoping it with a block/closure/context manager so the "current" thing is lexically obvious and cannot leak past its region. When you find yourself adding a *second* context variable to a builder, that is the signal to switch to child builders or a block-scoped API.

---

## Construction Builder (Ch. 14)

> **Intent:** "Incrementally create an immutable object with a builder that stores constructor arguments in fields." *(Ch. 14, intent line)*

### Concept

You want the product **immutable**, but can only discover its field values **gradually**. A mutable scratch object accumulates values, then hands you a fully-formed immutable product in one shot.

Immutability is a property of the **finished object**, not a constraint on the **construction process**. That sentence is the whole pattern.

### How it works

*(Ch. 14, "How It Works")*

1. Make a **mutable field on the builder for each** of the product's constructor arguments.
2. Add fields for any other attributes of the product you're collecting.
3. Add a method that **creates and returns a new product object** assembled from the builder's data.

**Optional lifecycle controls** worth adding:

- Check you have enough information to create the product before allowing creation.
- Set a flag once a product has been returned, to prevent returning it again — or stash the created product in a field.
- Raise an error if someone adds attributes to the builder *after* the product was created.

**Composition:** builders combine into deeper structures, producing a *group of related objects* rather than one. In the example a flight builder owns a list of leg builders, and top-level materialization cascades down, converting each leg builder to an immutable leg on the way *(Ch. 14, "Building Simple Flight Data (C#)")*.

### When to use it

Use it whenever you create an object with **multiple immutable fields** whose values you gather **gradually**. The builder gives "a coherent place to put all this data before you actually create the product" *(Ch. 14, "When to Use It")*.

**Alternatives considered and rejected:**

- **Local variables or loose fields** — capture pieces in locals until you can call the constructor. Fine for one or two products, "but soon gets confusing if you need to create a bunch of objects at once, such as when you're parsing." A parse is exactly the case where many half-built objects are alive simultaneously.
- **Copy-on-write on the real model object** — create a model object and, each time you learn one more immutable attribute, copy it with that attribute changed. Saves writing a builder but is "generally more awkward to do and follow." The killer objection: **it doesn't work if you have multiple references to the object** — you must chase down and replace every reference. Precisely why it fails for graph-shaped Semantic Models with cross-references.

**Scope limit, plainly:** "you only need it when you have immutable fields. If that's not the case, then just create your product objects directly." Don't reach for a builder reflexively.

### Construction Builder ≠ Expression Builder

Despite the shared word, **different patterns** *(Ch. 14, "When to Use It")*:

- **Construction Builder** is *purely* about gradually building up constructor arguments. It makes **no attempt to provide a fluent interface.**
- **Expression Builder (Ch. 32)** is focused on a **fluent interface** — it exists to shape the *reading experience*.

A single object is often both, "but that doesn't mean they are the same concept." Staged construction and fluent surface syntax are orthogonal decisions that happen to be frequently combined. Conflating them produces two failure modes: builders existing purely for fluency though the product is mutable (pure ceremony), and builders whose fluent method names have been contorted to also serve as the construction API (two jobs, both done badly). Ask separately: *does the product have immutable fields gathered over time?* (Construction Builder) and *do I want the call site to read as a sentence?* (Expression Builder).

### Relationships

- **Semantic Model (Ch. 11)** — the product is typically a model object; the builder is population machinery.
- **Symbol Table (Ch. 12)** — putting builders rather than final model objects into the table is what makes forward references practical.
- **Context Variable (Ch. 13)** — when the model object isn't mutable enough, the context variable holds a builder instead.
- **Expression Builder (Ch. 32)** — often the same object, conceptually distinct.

> **SDK lens:** The canonical justification for **builder types in a library API**: you want public value objects immutable (safe to share, safe to cache, thread-safe, equality-friendly), yet callers assemble them over many steps. Don't compromise the product's immutability to make construction convenient — add a builder. Put the **lifecycle controls on the builder, not the product**: completeness validation at `build()` time, single-use enforcement, and rejecting mutation after build; these give clear early errors instead of half-built products escaping. **Nest builders to mirror nested immutable structures** rather than exposing mutable collections on the product. And recognize the rejected alternative in the wild: an API returning a modified copy on every setter looks elegant until objects are referenced from more than one place — Fowler's aliasing objection is exactly why it breaks down at scale.

---

## Macro (Ch. 15)

> **Intent:** "Transform input text into a different text before language processing using Templated Generation." *(Ch. 15, intent line)*

This is the chapter where Fowler argues *against* a technique at length. Understanding *why* he rejects it matters more than the technique, because the reasons generalize to every metaprogramming or code-generation feature you might ship.

### Concept

A language has a fixed set of forms. Sometimes you can add abstraction by transforming its input text **before** parsing. Since you know the final form you want, you describe the transformation as a template — the desired output with callouts for parametrizable values.

Two varieties *(Ch. 15, "How It Works")*:

- **Textual macros** treat text as text. More familiar, easier to understand, and work on **any** language represented as text.
- **Syntactic macros** know the host language's *syntactic structure*, so they more easily operate on sensible units and produce valid results — but work with **only a single language**, usually baked into that language's tooling or specification.

"In the early days of programming, macros were as prevalent as functions. Since then, they've largely fallen out of favor, mostly for good reasons." They survive mainly in internal DSLs, particularly in Lisp.

The simplest legitimate form is symbolic substitution — e.g. naming a color repeated as a raw hex code across CSS rules. Two observations *(Ch. 15, "Textual Macros")*: the file you now edit **isn't proper CSS anymore** — "you've enhanced the CSS language with a macro processor," which is precisely the DSL move; and this substitution could equally be **Textual Polishing (Ch. 45)**.

Critical semantic difference from a function call: **the macro is evaluated at compile time**, doing textual search-and-replace; the compiler never sees the macro name at all.

### The four failure modes

*(Ch. 15, "Textual Macros" / "Syntactic Macros")*

1. **Mistaken expansion.** `sqr(x)` defined as `x * x`, invoked as `sqr(a + b)`, expands to `a + b * a + b`. "Expansions may work most of the time but only break down in particular cases, leading to surprising bugs that are hard to find." Mitigation: "use more parenthesis than a Lisper." **Syntactic macros largely avoid this class.**
2. **Multiple evaluation.** An argument with a side effect mentioned more than once in the body is evaluated more than once — `max(++a, ++b)` increments both twice. "You have to think differently than you do with function calls, and it's harder to see through consequences, particularly when you start nesting macros." **Syntactic macros do *not* fix this.**
3. **Variable capture (macro declares the name).** A macro body declaring its own local silently shadows a caller variable of the same name; the passed-in variable is ignored and the caller's is left wrong.
4. **Reverse variable capture (macro clobbers the caller's name).** In languages without forced declaration, the macro body assigns to a name the caller was already using, **silently overwriting it** while still producing the correct named output. The visible behavior looks right, so the bug lands somewhere else, later.

### The dominant actual use: deferred evaluation

The most transferable insight in the chapter. Fowler shows an *Execute-Around Method [beck-sbpp]*: `safe.open { ... }` unlocks the safe, runs the block, relocks it. "**The key point is that the content of the closure isn't evaluated until the receiver calls `yield`**, so the receiver can open the safe *before* running the passed-in code." An ordinary parameter fails — it is evaluated *before* the call.

> "Deferred evaluation means that the receiving method to a call chooses when, or indeed if, to execute the code that's been passed in." *(Ch. 15, "Syntactic Macros")*

In Lisp, writing that as a plain function requires wrapping the argument in a `lambda`, which "looks way too messy"; a macro restores clean call syntax. Hence:

> "A large part (perhaps the majority) of the use of Lisp macros is to provide a clear syntax for the mechanism of delayed evaluation. **A language with a cleaner closure syntax doesn't need macros for this.**" *(Ch. 15, "Syntactic Macros")*

**Most macro use is a workaround for clumsy closure syntax.** With good block/lambda syntax you already have most of the benefit and none of the four failure modes. The Lisp version still hits variable capture and multiple evaluation; mitigations are Scheme's **hygienic macros** (automatic renaming to avoid capture) and Common Lisp's **gensyms** (guaranteed-unique symbols — more trouble, but they let you *deliberately* use capture where useful). Fixing both noticeably complicates the macro: **"Avoiding such issues makes macros a lot harder to write than they might seem at first sight."**

### The second use: Parse Tree Manipulation

Lisp's syntax "is a good representation of the parse tree of the program" — first element is node type, rest are children — so manipulating Lisp code before evaluation *is* **Parse Tree Manipulation (Ch. 43)**. The worked example is `setf`, which takes an **access expression** and computes the corresponding **update**, sparing you an accessor/mutator pair per data shape; it works only on **invertible functions**, with Lisp keeping a record of inverses. Defining `setf` *requires* macros because it depends on parsing the input expression: **"This ability to parse its arguments is the key advantage of Lisp macros."** Macros aren't the only route — C# supports Parse Tree Manipulation by handing you an expression's parse tree plus a manipulation library.

### When to use it

**Appeal:** textual macros work with any text-based language, do all manipulation at compile time, and can implement behaviors beyond the host language's abilities.

**Costs** *(Ch. 15, "When to Use It")*:

- Subtle bugs (mistaken expansion, variable capture, multiple evaluation) are "often intermittent and hard to track down."
- **Macros don't appear in downstream tools.** "The abstractions they provide leak like a sieve without the wires, and you get no support from debuggers, intelligent IDEs, or anything else that relies on the expanded code."
- **Nested macro expansion is much harder to reason about than nested function calls.** Fowler concedes this could be lack of practice, "but I suspect it's something more fundamental."

**Verdict, textual macros:** "I don't recommend using textual macros in anything but the very simplest cases." Acceptable for *Templated Generation* **provided you avoid being too clever — in particular, avoid nesting the expansions.** Otherwise "they are simply not worth the trouble."

**Verdict, syntactic macros:** you're less likely to get mistaken expansions, "but the other problems still crop up. This makes me very wary of them." As a Lisp outsider he hedges: "they do make sense for Lisp, but I'm not convinced that the logic of using them there makes sense for other language environments."

**Shape of the decision:** most environments don't support syntactic macros, "so there's no choice to worry about." Where they exist "they are often necessary to do useful things, so you have to become at least a little familiar with them." **The choice on using syntactic macros is really made for you by your language environment.** The only genuine choice is whether macros are a reason to *choose* a language: "For the moment, I see macros as a worse choice than available alternatives, and thus a point deducted from those environments that use them" — explicitly hedged.

### Relationships

- **Templated Generation** — the only use Fowler blesses for textual macros.
- **Textual Polishing (Ch. 45)** — "a simple application of textual Macros, with all the corresponding problems."
- **Closure (Ch. 37) / Nested Closure (Ch. 38)** — the *preferred alternative* for the deferred-evaluation use case that motivates most Lisp macros.
- **Parse Tree Manipulation (Ch. 43)** — the other Lisp-macro use case.
- **Nested Function (Ch. 34)** — what makes Lisp code parse-tree-shaped in the first place.

> **SDK lens:** Three rules. (1) **Prefer closures over macros or codegen for deferred evaluation** — execute-around, resource scoping, retry wrappers, transaction blocks, instrumentation spans should all be higher-order functions taking a callback, not generated code; if your language has terse lambdas, you already have the feature. (2) **"Leaks like a sieve without the wires" is a general test for any metaprogramming feature you ship**: does the abstraction survive into the debugger, the stack trace, the type checker, and the IDE? If it disappears from downstream tooling, your users pay for it during every incident. (3) **Document evaluation cardinality explicitly** for any API taking an expression or thunk that may run zero, one, or many times — multiple evaluation and name capture generalize far beyond macros. And whatever generation you permit, **don't nest it**; nesting is where reasoning collapses.

---

## Notification (Ch. 16)

> **Intent:** "Collects errors and other messages to report back to the caller." *(Ch. 16, intent line)*

### Concept

After operations that significantly changed an object model, you validate. You want the answer as a **simple Boolean**, but if there *are* errors you want more — and in particular you want **all** of them rather than stopping at the first. A Notification is an object that **collects errors**: failed checks add to it, the command returns it, and the caller asks whether everything was OK and delves in if not.

### How it works

*(Ch. 16, "How It Works")*

- The basic form is **a collection of errors**, with an add-error capability — as simple as a message string or as involved as a structured error object.
- When the task ends the Notification goes back to the caller, who invokes a **simple Boolean query** and interrogates further if needed.
- **Getting it to where errors happen.** Two options: pass it as an argument — a **Collecting Parameter** *[beck-ip]* — or **stash it in a field** when an object corresponds to the task at hand (a validator, a parse helper) and can own it for the duration.
- **Beyond errors.** Also useful for **warnings** and **informational messages**. An *error* means the requested command *failed*; a *warning* is something that doesn't fail but is a matter of potential concern; an *informational message* is just potentially handy information.
- **"In many ways, a Notification is an object acting like a log file, so many of the features commonly found in logging can be useful here."** — severity levels, formatting, filtering, structured payloads, report rendering.

### When to use it — the fail-fast vs. collect-all rule

*(Ch. 16, "When to Use It")*

- Use a Notification "whenever there is a complicated operation that may trigger multiple errors and you don't want to fail at the first error."
- **"If you do want to fail at the first error, then you can simply throw an exception."** A Notification is for storing multiple errors "to give the caller a fuller picture of what the request led to."

Mechanical form of the rule: *how many independent problems can one invocation surface, and does the caller need to see them all before acting?* One → throw. Many — validating a document, schema, config file, migration, or a whole populated Semantic Model — → collect.

### The layering argument

The second motivating situation isn't about error handling at all *(Ch. 16, "When to Use It")*:

> **When a user interface initiates an operation at a lower layer:** "The lower layer should not try to interact with the user interface directly, so a Notification makes an appropriate messenger."

The lower layer *reports*; it does not *present*. The alternative — the model layer printing, logging at the user, or reaching up into presentation — couples the two permanently and makes the lower layer untestable and unusable elsewhere.

### Design decisions from the examples

**Simple Notification** *(Ch. 16, "A Very Simple Notification (C#)")* — errors as plain strings:

- The add-error method takes a **format string plus arguments**, formatting internally. "Using a format string and parameters makes it a bit easier to use the notification to capture errors, as the client code doesn't need to build the format string." Push message assembly *into* the Notification so call sites stay one-liners.
- It provides both **`IsOK` and `HasErrors`** (deliberate redundancy so the caller writes whichever reads better) **and** an **`AssertOK()`** that throws — "Sometimes this fits the flow of usage better than using the Boolean check methods." **Offer both a query-style and a throw-style consumption path** over the same collected data.

**Parsing Notification** *(Ch. 16, "Parsing Notification (Java)")* — accepts specific *kinds* of error rather than strings:

- It lives in the parse helper; at the end of the run, if there are errors, the parse fails with a **single exception carrying the accumulated report**. This is the **collect-then-fail-once** shape: gather everything during the operation, raise one well-populated failure at the boundary.
- It unifies **two error sources**: errors from the parser generator (hooked by overriding its error-reporting method and delegating to the default so standard behavior is preserved) and semantic errors from the translation code.
- **Internal structure:** the list holds message *objects*, not strings, with a small class hierarchy — one wrapping the parser's recognition exception, one holding the offending token plus formatted message. The base class is essentially a marker to make generics work ("In time, I might add something to it, but for the moment a bare marker suffices"). **"By passing the token in, I'm able to provide better diagnostic information."**

**Closing principle for the chapter:**

> "I think the most important point here is to build a Notification that makes the calling code as simple and compact as possible. Therefore, I pass all the relevant data to the Notification and let the Notification sort out how to compose error messages from this data." *(Ch. 16, "Parsing Notification (Java)")*

Call sites hand over raw structured context (token, object, values); the Notification owns formatting and presentation. Not the reverse.

### Relationships

- **Semantic Model (Ch. 11)** — validations over a populated model are the archetypal producer of Notifications, and Ch. 11 says validation belongs there and should run *before* interpretation or code generation.
- **Collecting Parameter *[beck-ip]*** — the mechanism for threading a Notification through many methods.
- **Parse Tree Manipulation (Ch. 43)** — its IMAP example accumulates validation errors in a Notification before throwing.

> **SDK lens:** Almost nothing here is DSL-specific. **Batch validation should collect, not fail fast** — any API validating a document, config, schema, request payload, or migration should return *all* problems in one pass; one error at a time forces an infuriating fix-rerun loop. **Offer both consumption styles** over the same result — an `is_ok()` query for callers who branch, and `assert_ok()`/`raise_for_status()` for callers who want an exception at their own boundary. **Structured messages beat strings:** carry location (line/column, JSON path, field name) and the offending value as data on the message object, rendering human text only at the edge — that is what makes errors machine-consumable for IDE squiggles and CI annotations as well as readable. **Keep formatting out of call sites** so error-raising stays a single line and wording stays centrally changeable. And observe the **layering discipline**: a lower layer returns a Notification rather than printing or reaching into the presentation layer.
