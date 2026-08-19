# Study Notes — Fowler, *Domain-Specific Languages* (2010), Part IV: Internal DSL Topics, Chapters 32–38

Source PDF: `Domain-Specific Languages.pdf` (413 rendered pages). Print page numbers do not match PDF page numbers; all page references below are **PDF page numbers**.

Actual chapter boundaries found:

| Chapter | Title | PDF pages |
|---|---|---|
| — | Part IV opener (pattern list) | 242 (bottom) |
| 32 | Expression Builder | 243–247 |
| 33 | Function Sequence | 248–250 (top) |
| 34 | Nested Function | 250 (bottom)–260 (top) |
| 35 | Method Chaining | 260 (bottom)–268 |
| 36 | Object Scoping | 268 (bottom)–276 (top) |
| 37 | Closure | 276 (bottom)–280 |
| 38 | Nested Closure | 280 (mid)–289 (top) |
| 39 | Literal List (out of scope, boundary marker) | begins 289 |

Part IV's declared contents (Fowler, DSL book, Part IV opener, PDF p. 242): Expression Builder, Function Sequence, Nested Function, Method Chaining, Object Scoping, Closure, Nested Closure, Literal List, Literal Map, Dynamic Reception, Annotation, Parse Tree Manipulation, Class Symbol Table, Textual Polishing, Literal Extension. Chapters 32–38 are the "function combination" core: the ways you glue DSL clauses together in a host language.

---

## Orientation: the frame Fowler is working in

Before the individual patterns, three ideas run through the whole part and are worth stating up front, because every pattern is judged against them.

**1. Fluent interface vs. command-query API.** Fowler explicitly names the *normal* style of API — self-standing methods, each understandable on its own, obeying command-query separation — as a **command-query API**, noting "it's so normal that we don't have a general name for it" (Fowler, DSL book, Ch. 32 "Expression Builder", opening). A **fluent interface** is a different animal: it is designed for readability of *the whole expression*, and as a result "fluent interfaces lead to methods that make little sense individually, and often violate the rules for good command-query APIs." Nearly every design decision in Part IV is downstream of this: fluent methods get license to break normal API rules, and the price of that license is that they must be quarantined somewhere (an Expression Builder).

**2. Fluent API design *is* grammar design.** Fowler repeatedly reasons about which technique to use by writing the production rule the clause has to satisfy, in BNF-ish notation, and then choosing the technique that fits that production. Collected from across the chapters:

| Grammar shape | Fowler's recommended technique | Why |
|---|---|---|
| `parent ::= first second` (fixed, mandatory children) | **Nested Function** | The parent's signature declares exactly the required arguments and, when statically typed, their types (Ch. 34, "How It Works") |
| `parent ::= (this \| that)*` (heterogeneous, repeatable, unordered) | Nested Function's **worst case** — forces intermediate tokens or a Context Variable; prefer **Literal Map** / keyword args, or **Method Chaining** | With no keyword arguments, arguments can only be identified by position and type, "downright impossible if `this` and `that` have the same types" (Ch. 34, "How It Works") |
| `parent ::= child*` (homogeneous repetition) | **Literal List** / varargs, usually nested inside a Nested Function | (Ch. 34, "How It Works"; confirmed Ch. 39 "Literal List", "When to Use It") |
| Mostly-optional clauses, any subset | **Method Chaining** | "Method Chaining easily allows a DSL script writer to pick and choose clauses" (Ch. 35, "When to Use It") |
| Mandatory clauses / a required *order* of clauses | **Nested Function**, or Method Chaining + **progressive interfaces** | Plain chaining can never require a clause; progressive interfaces enforce ordering and can enforce a mandatory element via an interface exposing only it (Ch. 35, "Progressive Interfaces" / "When to Use It") |
| Hierarchy that must be structural, not cosmetic | **Nested Function** or **Nested Closure** | Function Sequence and Method Chaining only *suggest* hierarchy through indentation (Ch. 35, "Hierarchic Structure") |
| A top-level list of statements | **Function Sequence** (with Object Scoping), or a Function Sequence inside a **Nested Closure** | Only one result list and one Context Variable needed (Ch. 33, "When to Use It") |

The tree of Expression Builders you end up with, Fowler observes, "really is a syntax tree for the DSL" (Ch. 32, "How It Works").

**3. Evaluation order is a first-class design variable.** Function Sequence and Method Chaining evaluate left-to-right. Nested Function evaluates arguments *before* the enclosing call (inside-out). Nested Closure lets the parent decide *when* — including before/after setup and teardown. Most of the tradeoffs in this part reduce to which evaluation order you need.

---

## Chapter 32: Expression Builder

**Intent (Fowler's one-liner):** "An object, or family of objects, that provides a fluent interface over a normal command-query API." (Ch. 32, intent)

### The concept

An Expression Builder is a *separate layer* whose only job is to host the fluent, DSL-flavored methods, and to translate those calls into ordinary command-query calls on the underlying Semantic Model. You keep two interfaces to your system: the normal one on your domain/model objects, and the fluent one on the builders. Because the fluent one lives somewhere else, it is "clearly isolated, making it easier to follow" (Ch. 32, opening).

Why this matters: fluent methods *are* strange. They return `this` from mutators (violating command-query separation). They are named like queries but act like commands (`sata()`). They define `First()` and `Third()` as separate methods where a parameter would be better programming. In C# they may be implemented as property getters that mutate. All of these are, in Fowler's words about the C# property trick, things he "would call extremely bad code" — "only acceptable when clearly placed in a fluent context — again, I would confine this abomination to a securely fenced Expression Builder" (Ch. 35 "Method Chaining", section "Chaining with Properties (C#)"). The Expression Builder is the fence.

### How it works

- Think of the builder as a **translation layer**: fluent interface in, command-query API out.
- It is "often a *Composite* [gof] using child Expression Builders to build subexpressions within an overall clause" (Ch. 32, "How It Works").
- Its exact shape depends on which function-combination pattern supplies the fluent surface. With Method Chaining, it's a sequence of method calls each returning an Expression Builder. With Nested Function, the builder may be a superclass (Object Scoping) or a bag of global/static functions. Fowler declines to give general structural rules for that reason.
- **One vs. many builders.** This is "one of the most notable questions." Multiple builders form a tree that mirrors the DSL's syntax tree, and "the more complex the DSL, the more valuable a tree of Expression Builders is" (Ch. 32, "How It Works").
- **The key structural tip:** have a well-defined Semantic Model whose objects have command-query interfaces and can be manipulated *without any DSL at all*. Fowler's test for this is behavioral: you should be able to write tests for the Semantic Model that use no DSL. He immediately tempers this — the point of an internal DSL is to make these objects easier to work with, so most tests will naturally use the DSL — "But I'd usually include at least some tests that only use the command-query interface" (Ch. 32, "How It Works").
- Builders are then tested by comparing the Semantic Model objects they produce, using direct command-query calls to inspect them.

### When to use it

Fowler is unusually direct: **Expression Builder is a default.** "I consider Expression Builder a default pattern — meaning I tend to use it pretty much all the time unless there's a good reason not to" (Ch. 32, "When to Use It").

The alternative is putting the fluent methods on the Semantic Model itself. His objections, in order of weight:

1. **Separation of concerns (the main one).** It intermingles the API for *building* the model with the methods that *run* the model. Both are usually substantial: execution logic often requires an alternative computational model to understand; fluent interfaces have their own logic to maintain flow. "It's easier to understand if we separate building logic from execution logic."
2. **Unfamiliarity.** Fluent interfaces are unusual. Mixing fluent and command-query methods on one class mixes two ways of representing an API, and because fluent APIs are rarer, developers are less familiar with them, "exacerbat[ing] the situation."

The best argument *against* Expression Builder: when the Semantic Model's execution logic is very simple, mixing building into it adds little complexity. Fowler notes people combine the two frequently — partly from unawareness of the pattern, partly from unwillingness to add classes — and states his bias: "I prefer lots of little classes to a few big classes, so my fundamental design philosophy encourages me to use Expression Builder."

### What the examples demonstrate (conceptually)

**Fluent calendar with and without a builder (Java)** (Ch. 32, "A Fluent Calendar with and without a Builder (Java)"). Target script: add named events to a calendar, each with `.on(y,m,d).from("09:00").to("16:00").at("Aarhus Music Hall")`.

- *Without* a builder, the fluent methods live directly on the `Event` domain class. They sit oddly next to genuine query methods like `getStartTime()` and `contains(LocalTime)`. Worse: if anyone needs to modify an event *outside* the DSL context, you must also supply normal command-query mutators (`setStartTime`) — so the class ends up carrying two overlapping mutation APIs. Fowler notes that using a fluent interface outside its intended context "would lead to hard-to-read code."
- *With* a `CalendarBuilder`, all the fluent methods move to the builder, which manipulates the domain classes through their ordinary command-query methods. The domain class is clean again.
- A side effect worth noting: the builder holds the thing being built ("content"), so the script now ends with an explicit `builder.getContent()` handoff. That's an early appearance of the finishing problem (Ch. 35).

**Multiple builders for the calendar (Java)** (Ch. 32, "Using Multiple Builders for the Calendar (Java)"). Fowler admits the motivation is contrived — he assumes `Event` becomes **immutable**, all data supplied via constructor — but the problem it creates is genuine and general.

- If the model object is immutable, the fluent calls have nowhere to write partial data. You must accumulate it somewhere until you can construct the object.
- Option A: fields on the single calendar builder (`currentEventStartTime`, …) — i.e. Context Variables.
- Option B (preferred): give each event its own `EventBuilder` — "essentially, using a Construction Builder."
- Mechanics worth internalizing: the parent builder holds a *list* of child builders; `add(name)` creates a child, registers it, and returns it so the chain continues on the child. The child holds a back-pointer to its parent, because the punctuation call that starts the *next* event (`add`) arrives at the child — the child must forward it to the parent. `getContent()` on the parent walks all children and materializes the entire Semantic Model at once.
- **Conceptual takeaways:** (a) child builders give each subexpression its own scope for accumulated data; (b) a child builder must handle "punctuation" calls that belong to its parent by delegating upward; (c) deferring construction to a final `getContent()` is what lets the Semantic Model be immutable.
- Java-specific variation: make the child builder an inner class of the parent, which removes the need for the parent field. Fowler avoided this in the book to keep examples multilanguage.

### Relationships

- Supplies the object that Method Chaining chains on, and the class that Object Scoping scopes to.
- Hosts Context Variables (keeping parse state out of global/static space).
- Uses Construction Builder for subexpression data.
- Produces the Semantic Model; the Semantic Model must remain independently usable.
- Multiple Expression Builders ≈ the DSL's syntax tree.

### SDK relevance

This is *the* foundational SDK-design pattern in the book.

- Keep the ergonomic/fluent surface in dedicated builder types; keep your resource/response/domain objects plain, inspectable, and conventional. Users hold the domain objects at runtime; they should never encounter a mutator that returns `this` or a getter that mutates.
- Make the plain API complete enough that the SDK is fully usable without the fluent sugar, and prove it with tests that touch only the plain API. That's both an architectural constraint and a regression guard: it prevents features from being reachable only through the DSL.
- Model the builder tree on the shape of the configuration grammar, not on your class hierarchy. One builder per nesting level is the norm for anything non-trivial.
- Immutable model objects and fluent building are compatible *only* if you buffer in builders and construct at the end. That is the direct justification for `build()`-style terminal methods in immutable-first SDKs.

---

## Chapter 33: Function Sequence

**Intent:** "A combination of function calls as a sequence of statements." (Ch. 33, intent)

### The concept

The simplest combination: a flat run of statements, one call per line. Crucially, "there is no data relationship between them" (Ch. 33, "How It Works") — the calls are related only by their order in time. Any structure the DSL appears to have (nesting, "this size belongs to that disk") is *not in the code*; it must be reconstructed by the builder from accumulated parse state. Hence: "a heavy use of Function Sequence means you use a lot of Context Variables."

### How it works

- For readability you want **bare** function calls — no receiver prefix. The obvious way is global functions, which brings two problems: global visibility, and static parse data.
- **Global visibility**: mitigate with whatever namespacing the language has, to narrow the scope of the calls down to the Expression Builder — in Java, static import. In languages with no global-function mechanism at all (C#, pre-1.5 Java) you're stuck writing explicit class-qualified calls, "which often adds noise to the DSL."
- **Static parse data** is the worse problem, and Fowler singles it out: "Static data is often a problem because you can never be entirely sure who is using it — particularly with multithreading. This problem is particularly pernicious with Function Sequence because you need a lot of Context Variables to make it work" (Ch. 33, "How It Works").
- **Object Scoping fixes both.** It hosts the functions on a class in the natural OO way and gives you an instance to put the parse data in. Fowler's recommendation: "I suggest using Object Scoping if you are using Function Sequence in all but the very simplest cases."

### When to use it

The bluntest verdict in the part: "On the whole, Function Sequence is the least useful of the function call combinations to use for DSLs. Using Context Variables to keep track of where you are in a parse is always awkward, leading to code that's hard to understand and easy to get wrong" (Ch. 33, "When to Use It").

Where it *is* reasonable:

- **At the top level of a language**, or at the top level inside a Nested Closure, where the DSL is a list of high-level statements. There you only need a single result list and one Context Variable — the cost stays bounded. Below that top level, form expressions with Nested Function or Method Chaining.
- **Because you have to start somehow.** "Perhaps the biggest reason to use Function Sequence is that you always have to start your DSL with something, and that something has to be a Function Sequence even if there's only one call in the sequence. This is because all the other function call techniques require some kind of context." (He acknowledges the quibble about whether a one-element sequence is a sequence, and keeps it for conceptual tidiness.)
- Alternative for the simple case: a Function Sequence is a list of elements, so **Literal List** is the obvious substitute.

### What the example demonstrates

**Simple computer configuration (Java)** (Ch. 33, "Simple Computer Configuration (Java)"). The script is `computer(); processor(); cores(2); speed(2500); i386(); disk(); size(150); disk(); size(75); speed(7200); sata();`, indented to suggest structure.

- Fowler is explicit that the indentation is a lie in the technical sense: "that's just arbitrary use of whitespace. The script is really just a sequence of function calls with no deeper relationship between them. The deeper relationship is built up entirely using Context Variables."
- The builder holds *two kinds* of state: the content being accumulated (processor and disk Construction Builders), and Context Variables saying what it is currently working on (`currentProcessor`, `currentDisk`).
- `computer()` resets both context variables. `processor()` and `disk()` each create a new sub-builder and set their own context variable *while clearing the other* — a hand-rolled state machine.
- The most instructive detail: **`speed()` is ambiguous.** It could mean processor speed or disk speed, so it must branch on which context variable is currently set, and throw `IllegalStateException` if neither is. This is the direct, visible cost of "no data relationship between calls" — clause name resolution becomes runtime state inspection, and illegal scripts fail at runtime rather than compile time. (Contrast Ch. 34: with Nested Function, `speed` inside `processor(...)` vs inside `disk(...)` is unambiguous by construction.)
- To avoid globals, the script itself must be written inside a subclass of the builder (Object Scoping): a `run()` template method calls the abstract `build()` — which is the script — and then returns the assembled value. Fowler: "that's well worth it to avoid using globals."

### Relationships

- **Requires** Context Variables; **should** use Object Scoping; uses Construction Builder for the accumulated pieces.
- Alternative: Literal List.
- Dramatically improved by wrapping in a **Nested Closure**, which lets the parent create the Context Variable just before the sequence and tear it down just after (Ch. 38).

### SDK relevance

This is the imperative "statement-style" configuration API: `client.setRegion(...); client.setRetries(...);` or, worse, a sequence of top-level calls that implicitly mutate shared session state.

- If your SDK's fluent surface relies on hidden mutable state to answer "which thing am I configuring right now?", you are in Function Sequence territory and you inherit its costs: thread-safety hazards, order-dependence, ambiguous method names that must dispatch on state, and errors surfacing at runtime.
- Static/global parse state is the specific thing to refuse. Bind state to an instance.
- The legitimate uses map cleanly: a top-level sequence of independent operations is fine; expressing *nested* configuration this way is not.

---

## Chapter 34: Nested Function

**Intent:** "Compose functions by nesting function calls as arguments of other calls." (Ch. 34, intent)

### The concept

Each clause's subelements are literally the arguments of its function call: `computer(processor(cores(2), speed(2500), i386), disk(size(150)), disk(size(75), speed(7200), SATA))`. The hierarchy of the DSL becomes the hierarchy of the host language's expression tree. Fowler's framing: "By representing a DSL clause as a Nested Function, you're able to reflect the hierarchic nature of the language in a way that's mirrored in the host language, not just in a formatting convention" (Ch. 34, "How It Works"). The structure is *real*, not indentation.

### How it works

**Evaluation order is the defining property.** "Function Sequence and Method Chaining both evaluate the functions in a left-to-right sequence. Nested Function evaluates the arguments of a function before the enclosing function itself." Fowler's mnemonic is the **Old MacDonald problem**: to sing the chorus you type `o(i(e(i(e()))))` — the reading order is inside-out. "This evaluation order has an impact on both how to use Nested Function and when to choose it instead of alternatives."

Consequences of arguments-first:

- **A built-in context to work with the arguments.** Argument functions return fully formed values which the enclosing function assembles into its return value.
- **No finishing problem** (unlike Method Chaining) — the closing bracket of the outermost call *is* the end, and the outermost call naturally returns the finished object.
- **No Context Variable needed** (unlike Function Sequence) — the data flows through return values.

**Fit to grammar.** "With mandatory elements in the grammar, along the lines of `parent ::= first second`, Nested Function works particularly well. A parent function can define exactly the arguments required in the child functions and, with a statically typed language, can also define the return types, which enables IDE autocompletion."

**Labeling arguments.** `disk(150, 7200)` is unreadable — "there's no indication what the numbers mean, unless you have a language with keyword arguments." The fix is a wrapping function that exists only to name the value: `disk(size(150), speed(7200))`. In its simplest form the wrapper returns its argument unchanged — "representing pure syntactic sugar." Fowler jokes about calling such a function a "sucratic" function. But sugar has a cost: **no enforcement.** "a call to `disk(speed(7200), size(150))` could easily result in a very slow disk." Fix: have the nested functions return intermediate data — a builder or a token — so the type system carries the meaning. More setup effort.

**Optional arguments.** Use the language's default arguments if it has them. Otherwise define a different function for each combination of optional arguments — "tedious but reasonable" for a couple, but "as the number of optional arguments increases, so does the tediousness (but not the reasonableness)." Intermediate data / tokens are one escape; **Literal Map** is the cleanest, "the only problem is that C-like languages don't usually support Literal Map."

**Multiple arguments of the same kind.** Varargs is best if the host language supports it; "You can also think of this as a nested Literal List."

**The worst case.** "The worst case of this is a grammar like `parent ::= (this | that)*`." Without keyword arguments, the only identification available is position and type — "messy, and downright impossible if `this` and `that` have the same types." You are forced into returning intermediate results or into a Context Variable, and the Context Variable route is "particularly difficult here since the parent function isn't evaluated till the end, forcing you to use the broader context of the language to properly set up the Context Variable."

**Bare calls.** Same question as always: global functions or Object Scoping. But an important asymmetry: "global functions can often be much less problematic in Nested Function, because the biggest problem with global functions is when they come with a global parsing state. A global function that just returns a value, such as a static method like `DayOfWeek.MONDAY`, is often a good choice." Nested Function usually needs no parse state, so the danger largely evaporates.

### When to use it

- **The strength and the weakness are the same thing: evaluation order.** Arguments-first "is very useful for building up a hierarchy of values because you can have the arguments create fully formed model objects to be assembled by the parent function. This can avoid much of the mucking about with replacements and intermediate data that you get with Function Sequence and Method Chaining."
- **Conversely, it's wrong for command sequences.** "this evaluation order causes problems in a sequence of commands, leading to the Old MacDonald problem... So, for a sequence that you want to read from left to right, Function Sequence or Method Chaining are usually a better bet. For precise control of when to evaluate multiple arguments, use Nested Closure."
- **Weak on optionality and variety.** "Nested Function very much expects you to say what you want and in the precise order you want it. If you need greater flexibility you'll need to look to Method Chaining or a Literal Map." Literal Map is singled out because "it allows you to get the arguments sorted out before calling the parent while giving you the flexibility of ordering and optionality of the arguments, particularly with a hash argument."
- **Punctuation is the aesthetic cost.** It "usually relies on matching brackets and putting commas in the right place. At its worst, this can look like a disfigured Lisp, with all the parentheses and added warts. This is less of an issue for DSLs aimed at programmers, who get more used to these warts."
- **Name clashes are *less* trouble than with Function Sequence**, "since the parent function provides the context to interpret the nested function call. As a result, you can happily use 'speed' for processor speed and disk speed and use the same function as long as the types are compatible." (Direct contrast with the ambiguous `speed()` in Ch. 33.)
- Cross-reference from Ch. 35: "Nested Function is the better choice for mandatory clauses."

### What the examples demonstrate

**Simple computer configuration (Java)** (Ch. 34, "The Simple Computer Configuration Example (Java)"). Each clause returns a Semantic Model object, "so I can use the nested evaluation order to build up the entire expression without using Context Variables." Builder elements are static methods and constants; Java static import removes the class prefix from the script. `cores` and `speed` are pure syntactic sugar — Fowler notes that if the clauses needed *different* return types the sugar could be a problem, but it isn't here. `disk` has two optional arguments, handled by writing all four overloads. Top-level `computer` takes a varargs of disks. Closing observation, which is the real point: "I'm usually a big fan of using Object Scoping to avoid littering the code with global functions and Context Variables. However, with static imports and Nested Function, I can use static elements without introducing global trash."

**Handling multiple different arguments with tokens (C#)** (Ch. 34, same-titled section). A language for on-screen box properties: `box(topBorder(2), bottomBorder(2), leftMargin(3), transparent)`, and another box with a different, shorter, differently ordered set.

- The problem: "we can have any number of a wide variety of properties to set. There's no strong reason to force an order in declaring the properties, so the usual style of argument identification in C# (position) doesn't work too well." This is the `parent ::= (this | that)*` worst case made concrete.
- The solution: every nested function returns a **token** object carrying a type tag plus a value. The parent takes a varargs array of tokens, iterates, and dispatches on the tag to update the target object.
- **Conceptual takeaway:** tokens convert "which argument is this?" from a *positional* question into a *data* question. That buys arbitrary ordering and arbitrary optionality — exactly the two things plain Nested Function is worst at — at the cost of a token type and a dispatch switch.

**Using subtype tokens for IDE support (Java)** (Ch. 34, same-titled section). A refinement of the above.

- Simple tokens give you *error checking*: returning a `[size, 150]` token lets you verify the right argument is in the right position, or accept arguments in any order.
- "Checking is all very well, but in a statically typed language with a modern IDE, you want to go further. You want autocompletion popups to force you to put size before speed. By using subclasses, you can pull this off."
- Instead of one token class with a type field, define a **subtype per clause**: `SizeToken` and `SpeedToken` both extending `IntegerToken`. The parent function's signature is then `disk(SizeToken, SpeedToken)` — the compiler enforces the right token in the right position, and autocompletion suggests the right function in the right place. "With this setup, the IDE will suggest the right functions in the right places, and I'll see comforting red squiggles should I do any reckless typing."
- This is the Nested Function analogue of **progressive interfaces** in Method Chaining: encoding grammar constraints in the type system so the IDE teaches the language. (Fowler notes generics are another route, "left as an exercise for the reader.")

**Using object initializers (C#)** (Ch. 34, same-titled section). For a pure hierarchy of *data*, C# object initializers are the most natural fit. Fowler's conceptual framing is the useful part: "You can think of object initializers as Nested Functions that can take keyword arguments (like a Literal Map) which are restricted to object construction. You can't use them for everything, but they can come in handy for situations like this."

**Recurring events (C#)** (Ch. 34, "Recurring Events (C#)" and its "Semantic Model"/"The DSL" subsections). Fowler's street-cleaning schedule: first and third Monday of the month, April through October. Script: `Schedule.First(DayOfWeek.Monday).And(Schedule.Third(DayOfWeek.Monday)).From(Month.April).Till(Month.October)`.

- **It is deliberately a mix.** "This example combines Method Chaining with Nested Function." Realistic DSLs mix; the interesting content is in the seams. Fowler also notes that because the nested functions here just return a value, he doesn't feel a strong need for Object Scoping.
- Semantic Model: a **Specification** (Evans, DDD) over dates — small composable building blocks (`PeriodInYear`, `DayInMonth`, `Month`) plus composite `And`/`Or`/`Not` specifications. Fowler's stated method: "When building a specification model for a particular type, I like to identify small building blocks that I can combine together."
- **The DSL can read *opposite* to the model.** "We say 'first and third Monday' in our language, but in terms of the specification, it's the first *or* third Monday that matches the Boolean condition. It's an interesting example of where the DSL is opposite to the model in order for both to read naturally." Natural-language "and" is Boolean "or". The fluent layer's job is to read naturally to the domain reader, *not* to mirror the model's structure.
- A modelling aside worth keeping: using `DateTime` (subsecond precision) when you only care about day precision "can easily result in awkward bugs when you compare two `DateTime`s that are different below the level of precision you care about." Over-precise temporal types are a common trap because libraries push you toward them.
- **Starting the chain with a bare function.** `Schedule.First(...)` "is an example of a common feature in these languages — using a bare function to create a starting object to begin the chaining." `Schedule` *is* an Expression Builder; Fowler named it "Schedule" rather than "ScheduleBuilder" "because I think it reads better as just 'schedule.'" Naming for the reader of the script, not for the implementer.
- **Fluent APIs get different rules.** Writing separate `First` and `Third` methods instead of one method with an index parameter is bad general programming — "I would usually argue against writing different methods for something that would be better handled as a parameter, but this is yet another example where you have different rules of good programming when you use an Expression Builder."
- `From`/`Till` need a **Context Variable** (`periodStart`) because a period is assembled across two chained calls — a small, contained instance of Method Chaining's context problem.
- Closing tradeoff note: in C# the static Nested Functions need class qualification (`DayOfWeek.Monday`, `Month.April`). "This reads pretty well, although it does add noise compared to an Object Scoping approach." Object Scoping (or Java static imports) would let it read `Monday`. "The gain isn't huge but would probably be worthwhile."

### Relationships

- Opposes Function Sequence / Method Chaining on evaluation order.
- Complemented by Literal List (varargs), Literal Map / keyword args (optionality + ordering), Nested Closure (control of *when* arguments evaluate), Object Scoping (bare calls), Expression Builder (where the functions live).
- Tokens / subtype tokens are the type-system mechanism; progressive interfaces (Ch. 35) are the Method Chaining equivalent.

### SDK relevance

This is the "constructor / nested options-object" style, and the only technique in the set that can *require* things.

- Required parameters and structural hierarchy belong here. If your SDK has parameters that must be present, they belong in the function signature — not in chainable setters, which can always be omitted.
- Sugar wrappers that only label a value (`size(150)`) improve readability but enforce nothing; typed wrappers (`SizeToken`) enforce and drive autocomplete. That is the exact tradeoff behind newtype/branded-type parameters in modern SDKs.
- The degradation curve is the crucial judgment: Nested Function is excellent for a fixed mandatory shape and gets *worse the more optional settings you add* — combinatorial overloads, positional ambiguity, unordered heterogeneous arguments. That's precisely the region where builders, keyword arguments, and option maps win. Knowing where the crossover is, is most of the skill.
- Practical rule: prefer keyword arguments / options objects (Fowler's Literal Map) wherever the host language has them; they give you optionality, ordering freedom, and named arguments in one move, and remove the need for tokens entirely.

---

## Chapter 35: Method Chaining

**Intent:** "Make modifier methods return the host object, so that multiple modifiers can be invoked in a single expression." (Ch. 35, intent)

### The concept

Rather than `hd.setCapacity(150); hd.setExternal(true); hd.setSpeed(7200);`, write `new HardDrive().capacity(150).external().speed(7200)`. Each modifier returns an object — usually itself — so the next call can continue the chain.

Fowler opens with a corrective: "Method Chaining rapidly caught on amongst people as an example of what an internal DSL should look like. It caught on a bit too much — people started to assume that Method Chaining was synonymous with fluent interfaces and internal DSLs. My view is that Method Chaining is one of several techniques, but it's still valuable and noticeable" (Ch. 35, "How It Works"). Its common form is on an **Expression Builder**.

### How it works

- Mechanically trivial: the modifier returns `this` (or another object) instead of `void`.
- **It breaks command-query separation, knowingly.** "Returning a value from a modifying method breaks the principle of command-query separation. Most of the time I follow that principle, and it's served me well. A fluent interface is one case when we need to break it."
- **It breaks naming conventions too.** "a method like `sata()` would seem like a query, not a modifier. This naming is very problematic, as it will seriously confuse anyone who is expecting a command-query API. Taken together, Method Chaining violates many common rules of common (command-query) API design." Two independent reasons to fence it inside an Expression Builder.
- **It changes formatting conventions.** Long chains read badly on one line, "particularly if we want to suggest a hierarchy," so put each call on its own line. In Java/C# the convention is periods at the *start* of the line — "this makes them more noticeable and thus emphasizes the use of chaining." Languages that use newlines as statement separators are less flexible: Ruby requires the periods at line *ends*. Practical bonus: "Putting methods on separate lines also makes debugging easier, as error messages and debugger control usually work on a line-by-line basis. Therefore, it's wise to do less on each line."
- **Why constructors aren't the answer.** "DSLs are often about building up configurations of objects, and doing so in constructors is often tricky. It's also usually difficult to read, since constructors often allow only positional parameters."

#### Builders or values (Ch. 35, "Builders or Values")

Fowler's preference is chaining on Expression Builders, "since that reduces the confusion between the conventions of fluent and command-query APIs." But he acknowledges the alternative:

- `42.grams.flour` — `grams` is defined on integer (via **Literal Extension**) and returns a quantity **Value Object**, which hosts `flour`, returning an ingredient. "Instead of having a single Expression Builder, we have a sequence of regular objects. Often, when you see this, the objects are Value Objects."
- Each step changes type — Neal Ford's term, **type transmogrification**.
- Fowler is explicitly non-dogmatic here: "There are plenty of good developers who are comfortable with using Method Chaining on domain types like this, so I'm cautious about arguing against it. My inclination, however, leads me to prefer using Expression Builders as much as possible, to clearly separate command-query and fluent API styles."

#### The finishing problem (Ch. 35, "Finishing Problem")

This is Method Chaining's signature weakness and the most SDK-relevant idea in the chapter.

- "It boils down to the lack of a clear end-point to a method chain." Every method must return a builder to keep the chain alive, so nothing in the chain signals completion, and the value you actually want (the finished domain object) never appears.
- The example: `new AppointmentBuilder().From(1300).To(1400).For("dentist")` — "I would like the returned value to be an `Appointment` object, since that would be the most natural usage. However, the need to continue the method chain means that each method has to return an appointment builder. There's nothing in the chain that tells me when I'm done, so I have to put in some kind of marker method to show the end."
- Workaround 1: an explicit finishing method (`.End`, `.build()`). "It isn't too bad, but the use of `End` is still a bit of syntactic noise."
- Workaround 2 (C#): an implicit conversion operator — "although that does mean you'll forgo `var` for an explicit type."
- **Better answer: use a different pattern.** "This is where using Nested Function or Nested Closure can be a valuable alternative." Their enclosing call *is* the terminator.
- A third exit, from the C# progressive-interfaces example: give the grammar a natural last clause and let that clause return the finished object. "I have a natural stop method with `Body`, so I'll have that return the message."

#### Hierarchic structure (Ch. 35, "Hierarchic Structure")

- "Tied in with the finishing problem is the problem that Method Chaining doesn't naturally fit a hierarchic structure. Hierarchic structures are common in languages, which is why syntax trees are valuable for thinking about them."
- In a chained computer configuration, "There's a definite hierarchy to this, but it's suggested by the indentation and not captured in the structure of the code itself. As a result, we have to manage that structure ourselves. This problem also occurs with Function Sequence."
- Two management strategies:
  1. **Context Variables** — e.g. `currentDisk`, updated on every `disk` call, with a list of completed disks.
  2. **A child builder per subelement** — "A separate builder allows us to limit the methods available to only those required to provide the information for the disk or a finishing method." Note the second half: a child builder isn't just data scoping, it's *grammar* scoping.

#### Progressive interfaces (Ch. 35, "Progressive Interfaces" and "Progressive Interfaces (C#)")

The chapter's most important technique for SDK design.

- "A valuable variation to the basic Method Chaining approach is to use multiple interfaces to drive a fixed sequence of method-chaining calls."
- Email example: force destination, then Cc's, then subject, then body. Present a *sequence of interfaces* over the Expression Builder. The first interface exposes only `to`. `to` returns an interface exposing only the legal next steps: `to`, `cc`, `subject`. `cc` returns one with only `cc` and `subject`. `subject` returns one with only `body`.
- Implementation: the Expression Builder implements all the interfaces; each method still returns `this`, but *typed as the next interface*. Interfaces can inherit from each other so a later stage picks up an earlier stage's legal steps without duplicating declarations — "It's not really that worthwhile in this example, but it's often a useful technique."
- **Payoff:** "This can work really well in a statically typed language with IDE support. Autocompletion in the IDE can step you through each clause in the DSL by only suggesting the methods that are valid for that point in the chain." Honest caveat: "it's not perfect, as methods inherited from `Object` also show up."
- **Relationship to child builders:** "This ability to control which methods are valid in which contexts is similar to that you get by using a child builder. Indeed, you can use a child builder to do the same thing as progressive interfaces, but progressive interfaces are easier if there's no other reason to make a child builder."
- **Mandatory elements:** "Progressive interfaces can be used to enforce mandatory elements in a chain; for this, define an interface that only takes a single mandatory element."

### When to use it

- "Method Chaining can add a great deal to the readability of an internal DSL and, as a result, has become almost a synonym for internal DSLs in some minds. Method Chaining is best, however, when it's used in conjunction with other function combinations."
- **Best for optional clauses.** "Method Chaining works best when using optional clauses in a language. Method Chaining easily allows a DSL script writer to pick and choose clauses needed for a particular situation. It's difficult to specify in the language that certain clauses must be present. Using progressive interfaces allows some ordering of clauses, but in the end clauses can always be left out. Nested Function is the better choice for mandatory clauses."
- **Escape hatches.** "The finishing problem crops up from time to time. While there are workarounds, usually if you run into this you're better off using a Nested Function or Nested Closure. These alternatives are also better choices if you are getting into a mess with Context Variables."

### What the examples demonstrate

**Simple computer configuration (Java)** (Ch. 35, "The Simple Computer Configuration Example (Java)"). The fullest worked machinery in the chapter.

- The chain starts with a static `computer()` factory referenced via static import — "To start an expression using Method Chaining, you need some method call to initiate the chain."
- The `ComputerBuilder` holds both the chaining methods and the parse data.
- **Two different sub-structure strategies are shown side by side, deliberately.** The processor is handled with a simple **Construction Builder** held in a Context Variable — the builder just stores data, and the fluent methods stay on the parent. The disks are handled with a full child **DiskBuilder** to which the fluent methods are *delegated*. Fowler names the inconsistency and explains it: "A simple Construction Builder works better for simple cases and full delegation works better for more complicated cases. I've shown both here for pedagogical reasons, although I lean more to full delegation."
- **Punctuation forwarding, again.** A `disk` clause can appear while you're already inside a disk, so `DiskBuilder.disk()` forwards to the parent. Likewise `DiskBuilder.end()` forwards to the parent's `end()`. Every child builder must handle the parent's punctuation.
- The finishing problem is handled with the simplest workaround: an `end()` method that returns the assembled `Computer`.
- Fowler's summary judgment is the takeaway: "Method Chaining reads very clearly, without much of the syntactic noise that can clutter Nested Function. However, to pull it off, I have to do a lot of fiddling around with Context Variables and cope with the finishing problem."
- He also notes the ergonomic cost of *not* having a finisher: without `end()` you must break the expression into `builder … ; Computer c = builder.getValue();` — two statements and a named variable.

**Chaining with properties (C#)** (Ch. 35, same-titled section). C#'s property syntax lets you drop the empty parentheses from no-argument clauses (`.SATA` rather than `.sata()`) by implementing a property *getter* that mutates the builder and returns `this`.

- Fowler's reaction is the point: "This code should make you feel distinctly uneasy: It's a property getter that's really acting as a setter, returning the object itself rather than the value of the property. This violates all our expectations of how property getters should work. In almost all circumstances, I would call this extremely bad code. It's only acceptable when clearly placed in a fluent context — again, I would confine this abomination to a securely fenced Expression Builder."
- Generalizable principle: **the fluent layer's license to violate conventions is granted by, and only by, its isolation.** The more a technique violates expectations, the more strictly it must be quarantined.

**Progressive interfaces (C#)** — described above under "How It Works."

### Relationships

- Usually hosted on an Expression Builder; can be hosted on Value Objects (with Literal Extension).
- Needs Context Variables and/or child builders for hierarchy.
- Progressive interfaces ≈ subtype tokens (Ch. 34) — both encode grammar in types.
- Nested Function / Nested Closure are the recommended escapes from the finishing problem and from Context Variable messes.
- Combines happily with Nested Function (Ch. 34 recurring-events example) and with Nested Closure (Ch. 38).

### SDK relevance

The highest-density SDK chapter in the book.

- **The finishing problem is the everyday `.build()` question.** Every builder-style SDK API faces it. Fowler's ranked options translate directly: a natural terminal clause that returns the finished object (best), an explicit `build()`/`end()` (acceptable, noisy), an implicit conversion (language-specific, costs type inference), or restructure to a function/callback form where the enclosing call terminates (often the real answer).
- **Progressive interfaces are the type-state pattern.** Returning a narrower interface from each step makes illegal call sequences fail at *compile* time, and turns IDE autocomplete into documentation — the user is shown only what is legal next. This is how modern SDKs enforce "you must set auth before you can send", and it composes with builder inheritance to avoid declaring the same method repeatedly.
- **Chaining cannot express requirement.** Required inputs belong in the factory/constructor (Nested Function shape); chained setters are for genuinely optional configuration. Reaching for progressive interfaces to enforce required-ness works, but if the requirement is unconditional, a parameter is simpler.
- **Chain on builders, not on the objects users keep.** Value-object chaining reads nicely but leaks fluent conventions (mutators returning `this`, query-shaped mutators) into types users hold and inspect at runtime.
- **Hierarchy needs child builders, not indentation.** And a child builder must forward the parent's punctuation, or users will hit surprising "method not found" errors mid-chain.
- **Formatting is API design.** One call per line is not merely style: it makes stack traces and debugger stepping point at the failing clause.

---

## Chapter 36: Object Scoping

**Intent:** "Place the DSL script so that bare references will resolve to a single object." (Ch. 36, intent)

### The concept

Nested Function and, to a lesser extent, Function Sequence want *bare* calls — no receiver — for readability. "but in their basic forms they come with a serious cost: global functions and (worse) global state" (Ch. 36, opening). Object Scoping removes both by resolving all bare calls against a single host object: "this avoids cluttering the global namespace with global functions, allowing you to store any parsing data within the host object. The most common way to do this is to write the DSL script inside a subclass of a builder that defines the functions — this allows the parsing data to be captured in that one object."

### How it works

- "One of the many useful properties of objects is that each object provides a contained scope for functions and data. Inheritance allows you to use this scope separately from where it's defined" (Ch. 36, "How It Works"). So: define the DSL functions on a base class; write DSL programs in subclasses. The base class also holds fields for parse data.
- That base class is the natural home of the **Expression Builder**. Clients write DSL programs in a subclass of it — "Using inheritance allows them to add other DSL functions in the subclass, or even override base functions in the DSL object if they need to."
- **Alternative mechanisms to inheritance:**
  - **Ruby instance evaluation** (`instance_eval`) — "the facility to take any program code and execute it within the context of a particular object. This allows a DSL writer to write the DSL text without declaring any links to the base class that defines the language."
  - **Java instance initializers** — "These are not well known nor often used, but can work well for this case." (The double-brace idiom.)

### When to use it

- "Object Scoping solves the niggly problems of globalness within Nested Function and Function Sequence and as such is always worth considering... Not only does this avoid messing with a global namespace, it also allows you to store parsing data in an Expression Builder. I find these advantages quite compelling, and thus would always suggest using Object Scoping if you can" (Ch. 36, "When to Use It").

Where you can't, or shouldn't:

- **It requires an OO language.** (Fowler: not a problem for him.)
- **It constrains where the script can live.** "With the most common inheritance case, it means you must put the DSL script within a method in a subclass of an Expression Builder. This isn't too much of a problem for self-contained DSL scripts. Such scripts often sit in their own file and are well-separated from other code. In this case, there is a little syntactic noise to set up the inheritance structure but it's not too obtrusive. (You can avoid even that syntactic noise with techniques like Ruby's `instance_eval`.)"
- **The real problem is fragmentary DSLs.** "The real problem is with fragmentary DSLs, where using Object Scoping forces you into an inheritance relationship that may be awkward or even impossible." This self-contained-vs-fragmentary distinction recurs in Ch. 38 and is one of the most transferable ideas in Part IV.
- **Sometimes globals are fine and you don't need it.** "Object Scoping is mostly an antidote to global functions, so it's worth remembering that the biggest problems of global functions come with modifying global data. A common case where you don't get this problem is when the global function just creates and returns a new object, such as `Date.today()`. Static methods, which are effectively global, are very effectively return such objects which can either be regular objects or Expression Builders. If you can arrange your bare functions to be like this, then there is much less need for Object Scoping." (This is the same asymmetry noted in Ch. 34.)
- **Extensibility bonus.** "If the DSL framework is set up to allow a user of the DSL to substitute their own subclass of the scoping class for Object Scoping, this also makes the DSL more extensible. A user subclass can add more methods to extend the language. Indeed if particular methods are only needed in one script, then that script subclass can define those methods directly."

### What the examples demonstrate

**Security codes / zone admission rules (C#)** (Ch. 36, "Security Codes (C#)"). A building divided into secure zones; each zone has ordered allow/refuse rules checked when an employee approaches a door.

- Semantic Model: a `Zone` with an ordered list of `AdmissionRule`s. Each rule is an `AllowRule` or a `RefusalRule` with a body that is a composite **Specification** of `RuleElement`s (`MinimumGradeExpr`, `DepartmentExpr`, `EndDateExpr`, `AndExpr`, …). `CanAdmit` returns `ADMIT` / `REFUSE` / `NO_OPINION`; the zone runs rules in order and returns on the first opinion, "If none of the rules give an opinion, the method defaults to refusal."
- **The most important design lesson in the chapter is not about scoping at all.** "Although the underlying model allows arbitrary Boolean expressions, the DSL is simpler. Each admission rule is a conjunction ('and') of its clauses. This is why I need separate refuse statements for the two departments. If I put them in the same clause, it would only refuse people who were in both departments." And then the general principle: "Arbitrary Boolean expressions are powerful, but often difficult for people, particularly non-nerds, to follow. So some form of simplified structure can be handy in a DSL." **Deliberately make the language surface less expressive than the model when that makes it easier to get right.**
- The DSL script is a `doBuild()` method in a subclass of `ZoneBuilder`. "The DSL is comprised of methods which are defined on the base builder class. This allows me to call them in the subclass without any qualification." `Allow` takes a varargs **Literal List** of `RuleElement`s and wraps them in an `AndExpr`.
- **Extending the language** = add a model expression class + a function on the builder. **Extending for one script only** = define the function (and even its private expression class) directly in that script's subclass — shown with a `During(begin, end)` time-of-day clause that only one department wants. And if you can't modify the library: "I can create my own zone builder class that's a subclass of the library zone builder and let my scripts subclass that. I can then put any useful methods into my own abstract zone builder."
- **Honest accounting of the cost.** "Object Scoping does help in reducing noise in the DSL, but one problem is that it does introduce noise in the code that declares the DSL class. The first two lines (and closing braces) are awkward noise." And a small but instructive avoidance: he passes the zone in via a separate `Build(zone)` method rather than a constructor, because a constructor "would force me to add a constructor declaration to the subclass" — i.e. push boilerplate off the *user's* class and onto the library's. "It's a small thing, but saves me a bit of noise in the DSL text. These small things add up."

**Using instance evaluation (Ruby)** (Ch. 36, "Using Instance Evaluation (Ruby)").

- Motivation stated crisply: "While Object Scoping is a very valuable pattern, as it provides good names without global artifacts, using subtyping does introduce limitations. For a stand-alone DSL, the script file needs some head and tail noise to set up the context. For fragmentary DSLs, you need to be in a subclass of the DSL builder to write DSL expressions."
- `instance_eval` takes text/code and evaluates it in the context of a particular object instance; bare method calls resolve to that instance "as if they were inside an instance method of the class itself. This allows you to write a DSL using Object Scoping without needing to bother with any subclassing."
- The script file becomes pure DSL — no class header, no method wrapper. The builder just reads the file and `instance_eval`s it.
- **Scope switching down the tree.** He also `instance_eval`s *child* builders for nested clauses, "so the expressions in the DSL bind to the child builder rather than the parent. This mechanism allows me to handle calls to methods like `gradeAtLeast` differently in different parts of the DSL." This is how you get multiple Expression Builders *and* bare calls simultaneously — instance evaluation lets you rebind the scope as you descend the syntax tree.
- Aside: in Ruby he preferred **Nested Closure** over Nested Function for the multiclause condition, "as that allows the contents of the group to be separated with newlines rather than commas."

**Using an instance initializer (Java)** (Ch. 36, same-titled section). The double-brace idiom: `new ZoneBuilder() {{ allow(department(MF)); … }}`.

- "The trick is the use of double curly brackets in the DSL script. This creates not an instance of the zone builder, but an inner class that's an instance of a *subclass* of the zone builder. This one-off subclass has the code between the double curly braces woven into the constructor... Since the code between the double curlies is in a subclass of zone builder, we have the Object Scoping that we need."
- "A way to use Object Scoping in a relatively unobtrusive inline manner." Popularized by JMock; Fowler admits he'd neglected the language feature until he saw it used.

### Relationships

- Enables bare calls for **Function Sequence** and **Nested Function**; hosts the **Expression Builder** and its **Context Variables**.
- Also relevant to **Nested Closure**, where bare functions inside a closure resolve in the closure's defining scope — Object Scoping (or an explicit closure argument) is the fix.
- Ruby `instance_eval` connects it to **Closure** / **Nested Closure** and (elsewhere) **Dynamic Reception**.

### SDK relevance

This is the "configuration block / DSL block" family — Gradle build files, RSpec, JMock, Rails initializers, Kotlin receiver lambdas.

- It answers a real SDK question: how do you give users terse unqualified vocabulary without a global namespace and without global mutable state? Answer: bind the vocabulary to an instance and put the user's code inside that instance's scope.
- **The self-contained vs. fragmentary axis is the decision rule.** A standalone configuration file can afford (and benefits from) an implicit receiver. A few lines of SDK usage embedded in ordinary application code should not force an inheritance relationship or a rebound `self`/`this`.
- **Extensibility falls out for free** — user subclasses of the scoping base class extend the language. That maps directly to plugin and extension points in SDKs, including "define a helper only this one config file needs."
- **Push boilerplate onto the library, not the user.** The constructor-vs-`Build(zone)` decision is a tiny instance of a general SDK rule: every declaration you force into user code is noise you pay for on every use site.
- **The simplified-Boolean lesson generalizes hard.** Your SDK's configuration surface does not have to expose every combination the model supports. Constraining the surface (e.g. conjunction-only rules, one refusal statement per department) trades expressiveness for a language people get right on the first try.

---

## Chapter 37: Closure

**Intent:** "A block of code that can be represented as an object (or first-class data structure) and placed seamlessly into the flow of code by allowing it to reference its lexical scope." (Ch. 37, intent)

**Also known as:** lambda, block, anonymous function. (Fowler, Ch. 37, "Also known as")

### The concept

The motivating problem stated in the pattern header: "You have a collection of objects and want to filter them in various ways. Writing a method for each filter leads to duplication in the setup and processing of the filter. By using a Closure, you can factor the setup and processing of the filter and pass in an arbitrary block of code for each filter condition."

Fowler's working definition: **"A Closure is a code fragment that can be treated as an object."** (Ch. 37, "How It Works")

He develops it from the duplication problem. Two loops — one collecting heavy travelers, one collecting managers — differ only in a Boolean test. "Removing that duplication is a simple thing to envisage, but difficult to write in many languages because the thing that varies between the two code fragments is a chunk of behavior — which is often not easy to parametrize."

The classical OO answer is to make the behavior an object: a `FilterFunction` interface with a `Passes` method, plus a class per predicate. It works, but "there's so much code in setting up the predicate object that the cure is worse than the disease. This is especially true when we look at the heavy travelers case" — where the predicate needs a parameter, forcing a constructor and a field just to carry a threshold. "Essentially, a Closure is a more elegant solution to this problem — one that makes it much easier to create a hunk of code and pass it around like an object."

### How it works

- **Terminology is a mess and Fowler says so.** "I use the term Closure in this book, but naturally there is no standard term for this language element. You also see them referred to as lambdas, anonymous functions, and blocks. Each language that uses them usually has its own term for them." Lispers say lambda; Smalltalkers and rubyists say block — "Although they are called blocks in Smalltalk and Ruby, it isn't the same as blocks in C-based languages."
- **What makes it a closure specifically.** In the C# delegate version, the predicate simply *uses* the `threshold` local variable from the enclosing scope — "which saves all the faffing around with parameters that the predicate object version needed. This reference to variables in scope is what formally makes this expression a Closure. The delegate is said to close over the lexical scope of where it's defined. Even if we take the delegate and store it somewhere for later execution, those variables are still visible and usable. Essentially, the system needs to take a copy of the stack frame to allow the Closure to still have access to everything it should see. Both the theory and implementation of this are quite tricky—but the result is very natural to use." He notes the word is used inconsistently — some reserve "closure" for an instantiated block that actually closes over lexical variables.
- **Terseness is the whole ballgame.** Tracing C#'s evolution — handwritten predicate class → C# 2 anonymous delegates → C# 3 lambdas with type inference — he concludes: "You'll notice there's really little change here—the main factor is that the syntax is much more compact. This may be a small difference but it's a vital one. **The usefulness of Closures is directly proportional to how terse they are to use.** This syntax makes them far more readable."
- **The libraries have to cooperate.** "C# 2 introduced a number of changes to the libraries that took advantage of delegates. This is an important point—for Closures to be really useful in a language, the libraries need to be written with Closures in mind." A language-level feature is worth little if the standard library predates it.
- **Deferred evaluation.** The `Club` example creates a selector closure inside a factory function, capturing that function's parameter, stores it in a field, and evaluates it arbitrarily later and arbitrarily often. "In this case, the selector Closure isn't actually evaluated when it's created. Instead, we create it, store it, and evaluate it later (possibly multiple times). **This ability to create a block of code for later execution is what makes Closures so useful for Adaptive Models.**"
- **Ruby syntax note.** Closures via `{ }` or `do…end`; "The two syntaxes are almost entirely equivalent. In practice, people use the curlies for one-liners and the `do…end` for multiline blocks." Important limitation: "The sad part about this nice Ruby syntax is that you can only use it to pass a single Closure into a function. If you want to pass multiple Closures, you have to use a less elegant syntax."

### When to use it

The chapter's "When to Use It" is short and framed at two levels:

- **General programming:** "Like many programmers who have used languages with good support for Closures, I find I miss them a great deal when using a language without them. They are a valuable tool to take chunks of logic and arrange them to eliminate duplication and support custom control structures."
- **In DSLs specifically:** "Closures play a couple of useful roles in DSLs. Most obviously, they are an essential element for Nested Closure. They also can make it easier to define an Adaptive Model."

### Relationships

- Prerequisite for **Nested Closure** (Ch. 38).
- Enables **Adaptive Model** (behavior held as data in the semantic model, evaluated later).
- Interacts with **Object Scoping** in languages that can rebind a closure's execution context (Ruby `instance_eval`) — see Ch. 36 and Ch. 38.

### SDK relevance

- Callbacks, handlers, predicates, and interceptors as first-class parameters — the single most common way SDKs let users inject behavior.
- **Custom control structures**: the SDK owns setup and teardown, the user supplies the middle. Retry policies, transactions, connection scoping, resource lifetimes, instrumentation spans. This is the mechanism behind context-manager-shaped APIs, and it is exactly what Nested Closure formalizes for DSLs.
- **Deferred/lazy evaluation**: accepting a closure rather than a value lets the SDK decide *whether* and *how many times* to evaluate — essential for retries, lazy config, conditional expensive computation, and rule engines.
- **Two design constraints worth carrying:** (1) a closure-taking API is only pleasant if the host language's closure syntax is terse — the same API is delightful in Ruby/Kotlin and clumsy in older C#/Java, which is a legitimate reason for language-specific SDK surfaces to differ; (2) your *whole library* must be designed for closures, not just one entry point, or users get a fluent island in an imperative sea.
- Language limits shape the API: Ruby's single-block rule means an SDK method that conceptually wants two callbacks (success/failure) needs a different shape in Ruby than in a language with cheap multiple lambdas.

---

## Chapter 38: Nested Closure

**Intent:** "Express statement subelements of a function call by putting them into a closure in an argument." (Ch. 38, intent)

### The concept

Nested Closure is Nested Function with the children wrapped in a closure. Fowler's minimal contrast (Ch. 38, "How It Works"), in Ruby:

- Nested Function: `processor(cores 2, i386)`
- Nested Closure: `processor do cores 2; i386 end`

"Instead of passing two Nested Function arguments, I pass a single Nested Closure argument which contains the two Nested Functions."

### How it works

**The central mechanic: you control evaluation.** "Placing the subelements in a Nested Closure has an immediate consequence for my implementation—I have to put in code to evaluate the closure. With a Nested Function, I don't need to do this since the language automatically evaluates the `cores` and `i386` functions before calling the `processor` function. With a closure argument, the `processor` function is called first and the closure is only evaluated when I explicitly program it to. So, usually I'll evaluate the closure within the body of the `processor` function. **The `processor` function can also carry out other tasks before and after the closure evaluation, such as setting up Context Variables.**"

That before/after capability is the whole value proposition, and Fowler spells out its most important application immediately:

> "In the example above, the contents of the closure is a Function Sequence. One of the problems of a Function Sequence is that the multiple functions communicate using hidden Context Variables. While you still have to do this inside a Nested Closure, the `processor` function can create the Context Variable before evaluating the closure and tear it down afterwards. This can greatly reduce the problem of Context Variables appearing all over the place." (Ch. 38, "How It Works")

**What can go inside the closure:**

1. **Function Sequence** — the base case above; the parent brackets it with Context Variable setup/teardown.
2. **Method Chaining** — "Here, there is the additional benefit that the parent function can set up the head of the chain and pass it into the closure as an argument." (`processor do |p| p.cores(2).i386 end`)
3. **Function Sequence with an explicit Context Variable passed as the closure argument** — `processor do |p| p.cores 2; p.i386 end`. "In this case, we have a Function Sequence but with the Context Variable explicitly present. This often makes it easier to follow, without adding too much clutter."

**Scoping.** "Bare functions written inside a Nested Closure are evaluated in the scope where they are defined—so, again, it's usually wise to use Object Scoping. Passing in an explicit Context Variable or using Method Chaining allows you to avoid this, as well as to organize the builder code into different builders." Languages that let you manipulate the closure's execution context (Ruby `instance_eval`) let you have bare functions *and* multiple builders at once.

**Multiple closures.** "In the examples I've shown above, I've put all the subelements of the parent function into a single closure. It's also possible to use multiple closures. The advantage of this is that it allows you to evaluate each subclosure independently." The canonical case is a conditional, shown in Smalltalk: `aRoom ifDark: [Light on] ifLight: [Light off]` — where evaluating both branches would be wrong. (Recall from Ch. 37 that Ruby's pretty block syntax handles only one closure.)

### When to use it

- The core claim: "Nested Closure is a useful technique because it combines the explicitly hierarchic structure of Nested Function with the ability to control when the arguments are evaluated. Control of evaluation provides you with a lot of flexibility, helping you to avoid many of the limitations of Nested Function" (Ch. 38, "When to Use It").
- The core limitation is the host language: "Many languages don't provide closures at all. Those that do often provide the syntax in a way that doesn't jive terribly well with DSLs, such as with an awkward keyword."
- **Best mental model — it's an enhancement, not a rival:** "It's usually worth thinking of Nested Closure as an enhancement to Nested Function, Function Sequence, and Method Chaining. The explicit control of evaluation gives you different advantages with each technique. All of these, however, boil down to the fact that you can do specific setup and tear-down operations on either side of the closure invocations. With Function Sequence, this means you can prepare Context Variables right before they are used by the closure. With Method Chaining, you can set up the head of the chain before invoking the closure."

### What the examples demonstrate

**Wrapping a Function Sequence in a Nested Closure (Ruby)** (Ch. 38, same-titled section). Fowler puts the Nested Closure script and the plain Function Sequence script side by side. The scripts are *character-for-character identical* except for the added `do…end` delimiters.

- "From the script's point of view, the only change with Nested Closure is to add the `do…end` closure delimiters. By adding these, I introduce an explicit hierarchic structure to what otherwise is a linear sequence with a formatting convention. The extra syntax doesn't strike me as troubling because it's marking the structure from the reader's point of view and in a way that makes sense to the reader."
- This is the sharpest statement in the part of *why* structure-in-code beats structure-in-indentation: the delimiters are not noise, they are the reader's own mental structure made real.
- Implementation shape: each clause function creates its model object, sets up any context, then invokes the block (`block.call`, or Ruby's more idiomatic implicit `yield`), then tears down.
- He uses Object Scoping so bare functions resolve against the Expression Builder, with a note for rubyists that he'd normally use `instance_eval` rather than subtyping, and is only subclassing for pedagogical clarity.

**Simple C# example** (Ch. 38, "Simple C# Example (C#)"). The identical structure in C# with `() => { … }`.

- "As you can see, the structure is exactly the same as in the Ruby example; the big difference is that there's a lot more punctuation in the script."
- Fowler's honest, subjective verdict: "To my eyes, Nested Closure works much less well in C# than it did in Ruby. Ruby's `do…end` closure delimiters flow more naturally to me than C#'s `() => {…}`, particularly when you also add the mandatory parentheses into the mix... The more used you are to C# notation, the less that will bother you."
- A nice observation about how syntax and content interact: "this example doesn't pass arguments into the closure—which adds more punctuation to the Ruby case but actually makes the C# easier to read since the empty parentheses now have something to surround." The same design choice reads differently in different languages.
- Implementation difference: C# requires you to declare the *delegate type* of the closure. "In this case, the closure has no arguments and no return type, but with a more complicated case we might need several different types."

**Using Method Chaining inside the closures (Ruby)** (Ch. 38, "Using Method Chaining (Ruby)"). Each parent passes an object into the closure to head the chain (`processor do |p| p.cores(2). i386. speed(2.2) end`).

- Costs: "This use of closure arguments may add noise to the DSL script (as does the need to now wrap method arguments in parentheses)."
- Benefits: "one benefit is that you no longer need Object Scoping and thus can easily use the code in a fragmentary style." And: "Another useful part of this approach is that it makes it easy to factor the various builder methods into a group of small, cohesive Expression Builders."
- A concrete, memorable payoff of multiple builders: "it also allows me to use an unqualified `speed` method for both the processor and the disk without ambiguity." Compare the Function Sequence version (Ch. 33), where `speed()` had to branch on Context Variables to decide what it meant. **Splitting into builders replaces runtime disambiguation with structural disambiguation.**

**Function Sequence with explicit closure arguments (Ruby)** (Ch. 38, same-titled section). The style Fowler says real Ruby DSLs actually use: `c.processor do |p| p.cores 2; p.i386; p.speed 2.2 end`.

- Why not the Method Chaining version: "While Method Chaining gives us these advantages, the resulting DSL script can look rather awkward. The interplay between Nested Closure and Method Chaining doesn't necessarily fit will. Certainly, most of the Ruby DSLs I've looked at do not use this style. Instead, they use Function Sequence within each closure but pass an explicit closure argument to allow multiple builders."
- The tradeoff: "The big difference in the DSL script is that you have separate statements for each clause in the DSL. On every statement, you have to state the passed-in object as the receiver of the method call. Although this adds more text to the statement, it results in a more regular style of code that rubyists find easier to work with." Explicit receivers cost characters and buy regularity, multiple builders, and fragmentary usability.

**Using instance evaluation (Ruby)** (Ch. 38, same-titled section). The way to have multiple builders *and* bare calls.

- "When you call a Ruby block, the block is evaluated in the context of where it's defined. In particular, any bare functions (or fields) are resolved to the object in which it's defined. Using `instance_eval`, you can change this by telling some other object to execute the block within its context, which means any bare methods will now resolve to the new object." "In effect, using `instance_eval` changes what `self` refers to inside the passed-in block."
- Each builder's clause method creates the child builder and `instance_eval`s the block against it, so the same bare name means different things at different depths.
- For a self-contained script file, `instance_eval` also removes all the head/tail noise of Object Scoping: the file is nothing but `computer do processor do cores 2 … end end`, and the builder `instance_eval`s the whole file.
- **The crucial caveat, and the chapter's best judgment call.** "Using `instance_eval` seems such a good trick that you may wonder if you should ever pass explicit closure arguments. As it turns out, there is a very real choice, one that was crystallized for me by Jim Weirich's experience with his builder library... In the first version of the library, Jim used `instance_eval`, but later switched to explicit parameters. The reason is that **programmers are used to the call behavior with closures; redefining `self` causes a lot of confusion and makes it very difficult to refer to elements in the static context that you need.**"
- Fowler's resolution is the self-contained/fragmentary rule again: "For me, the choice lies in whether you are using the DSL script in a self-contained or fragmentary style. In a fragmentary context, you need to follow the usual conventions with closures, so redefining `self` though `instance_eval` is not a good choice. With self-contained DSL scripts, your code style is different from regular Ruby code; the redefinition then doesn't cause confusion and is worth it to remove the noisy references."

### Relationships

- Built on **Closure** (Ch. 37).
- An *enhancement* to **Nested Function**, **Function Sequence**, and **Method Chaining** rather than a competitor.
- Tames **Context Variables** by scoping their lifetime to the closure invocation.
- Interacts with **Object Scoping**: needed for bare calls inside closures, or bypassed via explicit closure arguments; Ruby `instance_eval` is the bridge between the two patterns.
- Solves Method Chaining's **finishing problem** (the enclosing call terminates) and Function Sequence's Context Variable sprawl.

### SDK relevance

This is the "configuration block" API — `resource("x") { … }`, `describe(…) do … end`, `with_transaction { … }`, Kotlin's `apply`/receiver lambdas, Gradle's DSL.

- **Setup/teardown around the closure is the SDK superpower.** It's exactly what makes context-manager APIs (`with`, `using`, `try-with-resources`, transactions, spans, retries) work, and it's the same mechanism that lets a config DSL scope "which object am I configuring" to a lexical block instead of to a mutable field. If you have a builder that keeps a `currentThing` field, a block-scoped API removes it.
- **It fixes hierarchy and finishing at once.** The block delimits the subexpression, so there is nothing to "end" and the nesting is real. If your chained SDK API is drowning in `.end()` calls and context variables, the block form is the refactoring.
- **Explicit receiver vs. implicit receiver is a genuine, load-bearing API decision.** Explicit (`do |p| p.cores 2 end`, Kotlin `let`) costs characters, preserves normal scoping intuitions, works fine in fragmentary use, and enables multiple cohesive builders. Implicit (`instance_eval`, Kotlin receiver lambdas) is terser and cleaner for standalone config files, but surprises readers, breaks access to the enclosing lexical context, and is a poor fit inside ordinary application code. Fowler's rule — implicit for self-contained scripts, explicit for fragmentary use — is directly usable as an SDK guideline, and Weirich's reversal is the cautionary tale.
- **Multiple builders beat runtime disambiguation.** Giving each nesting level its own builder type lets the same clause name (`speed`, `size`, `timeout`) mean the right thing in each context, checked structurally rather than by inspecting state.
- **Language ergonomics legitimately drive API shape.** Fowler's own conclusion that the pattern "works much less well in C# than it did in Ruby" is permission to design differently per language binding rather than mechanically porting one surface everywhere.
- **Multiple closures for independent evaluation** maps to success/failure handlers, conditional branches, and any API where evaluating all branches would be wrong or expensive.

---

## Cross-cutting synthesis

### Decision guide (as Fowler actually argues it)

1. **Start with an Expression Builder.** Default. Keep the fluent layer off the Semantic Model (Ch. 32, "When to Use It").
2. **You must start the DSL with a Function Sequence of at least one call**, because every other technique needs a context to hang off (Ch. 33, "When to Use It").
3. **Below the top level, avoid bare Function Sequence.** It's the least useful combination; it forces Context Variables (Ch. 33, "When to Use It").
4. **Mandatory / hierarchical / fixed-shape → Nested Function.** It enforces via signature, evaluates children first, has no finishing problem, and needs no Context Variables (Ch. 34, "When to Use It").
5. **Optional / pick-and-choose → Method Chaining.** But accept: you can't require anything, you'll manage hierarchy yourself, and you'll face the finishing problem (Ch. 35, "When to Use It").
6. **Need order or requirement *and* you're chaining → progressive interfaces** (or child builders) (Ch. 35, "Progressive Interfaces").
7. **Lots of optional, unordered, heterogeneous arguments → Literal Map / keyword arguments**, not Nested Function (Ch. 34, "When to Use It").
8. **Bare calls without globals → Object Scoping.** Unless your bare functions are pure value-returning statics, in which case you may not need it (Ch. 36, "When to Use It"; Ch. 34, "How It Works").
9. **Need control over *when* things evaluate, or want to bracket setup/teardown, or are drowning in Context Variables → Nested Closure** (Ch. 38, "When to Use It").
10. **Fragmentary usage constrains everything.** Object Scoping via inheritance and `instance_eval`-style implicit receivers are for self-contained scripts; fragmentary DSLs need explicit receivers and no inheritance requirement (Ch. 36 and Ch. 38, "When to Use It" / "Using Instance Evaluation").

### The recurring theme: fluent layers earn a license to break rules — by being fenced

Collected violations Fowler explicitly endorses, each conditioned on isolation in an Expression Builder:

- Mutators that return values, breaking command-query separation (Ch. 35, "How It Works").
- Query-shaped names for commands — `sata()` (Ch. 35, "How It Works").
- C# property *getters* that mutate and return `this` — "this abomination" (Ch. 35, "Chaining with Properties (C#)").
- Separate methods `First()`/`Third()` where a parameter would be correct design (Ch. 34, "The DSL" in Recurring Events).
- A DSL structure that inverts the model's structure — "and" in the language meaning `Or` in the specification (Ch. 34, Recurring Events).
- A DSL deliberately less expressive than its own model — conjunction-only rules (Ch. 36, "DSL" in Security Codes).

The unifying rule: **optimize the fluent layer for the reader of the script, and pay for that by quarantining it away from every object the reader of ordinary code will touch.**

### Context handling — the thread through all seven patterns

| Pattern | How context is carried | Cost |
|---|---|---|
| Function Sequence | Context Variables on the builder (or, badly, statics) | Ambiguous clause names, runtime dispatch, order-dependence, thread hazards |
| Nested Function | Return values of the argument functions | None — but rigid shape, poor optionality |
| Method Chaining | Context Variables *or* child builders | Fiddly; child builders must forward parent punctuation |
| Object Scoping | Instance fields of the scoping builder | Constrains where the script may live |
| Nested Closure | Closure argument, or Context Variables scoped to the closure's lifetime, or rebound `self` | Language-dependent syntax; `self` rebinding surprises readers |

The trajectory of the whole part: **push context out of global state, into instances, then into return values or lexically scoped blocks.** Each step trades a bit of syntax for a large reduction in the class of bugs available.
