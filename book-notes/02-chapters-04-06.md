# Study Notes — Martin Fowler, *Domain-Specific Languages* (2010), Part I, Chapters 4–6

Source PDF: `Domain-Specific Languages.pdf` (413 rendered pages).
Actual PDF page boundaries found while reading:

| Chapter | PDF pages |
|---|---|
| Ch. 4 "Implementing an Internal DSL" | 61 – 75 (Ch. 5 heading appears low on p. 75) |
| Ch. 5 "Implementing an External DSL" | 75 – 86 (Ch. 6 heading appears mid p. 86) |
| Ch. 6 "Choosing between Internal and External DSLs" | 86 – 90 |
| Ch. 7 "Alternative Computational Models" (out of scope, boundary confirmed) | begins p. 91 |

Convention used below: pattern names Fowler cross-references to the Part II–VI pattern
catalogue are written in *Title Case Italics* (e.g. *Method Chaining*), matching the book's
own linking convention. Code examples are described conceptually, not transcribed.

---

# Chapter 4: Implementing an Internal DSL

(Fowler, DSL book, Ch. 4 "Implementing an Internal DSL")

## Framing (chapter opening)

Internal DSLs are the most approachable flavor to write: no grammars, no language parsing,
no special tools, and you stay inside your normal language environment. The price is that you
are **very much constrained by your host language** — every expression in the DSL must be a
legal expression in the host language. Consequently, a great deal of internal-DSL thinking is
really thinking about *host language features*. Fowler credits the Ruby community for the
recent impetus (Ruby has many features that encourage internal DSLs), notes most Ruby
techniques transfer to other languages "if usually not as elegantly," and names **Lisp as the
doyen** of internal DSL thinking — one of the oldest languages, with a limited but very
appropriate feature set for the job.

**Vocabulary — fluent interface.** A term coined by Eric Evans and Fowler for more
language-like APIs. It is "a synonym for an internal DSL looked at from the API direction."
The distinction between an API and a DSL is *language nature*, and it is deliberately fuzzy.
Fowler notes you can have reasonable but ill-defined arguments about whether a given
construction is language-like:

> "The advantage of such arguments is that they encourage reflection on the techniques you are
> using and on how readable your DSL is; the disadvantage is that they can turn into continual
> rehashes of personal preferences."

**SDK relevance:** this whole chapter is effectively a catalogue of API-shaping techniques.
The framing above is the key one: an internal DSL is *just an API you designed for reading*,
and the boundary is a judgement call, not a category.

---

## Section: Fluent and Command-Query APIs

This section is the conceptual heart of the chapter for API/SDK designers.

### The two styles

- **Command-query interface** (Fowler's coinage). The dominant, unnamed default style: an
  object is a *machine* with a menu of buttons you press and displays you read. Fowler traces
  this to Bertrand Meyer's *Object-Oriented Software Construction* "object as machine"
  metaphor: ovals = query buttons (indicator lights showing state, no state change),
  rectangles = command buttons (change state, no indicator). Fowler notes it is "so dominant
  that we don't even think of giving it a name," hence his coining one.
- **Fluent interface.** Instead of a box of objects each sporting lots of buttons, you think
  *linguistically*: composing sentences out of clauses that weave objects together.

> "It's this mental shift that is the core difference between an internal DSL and just calling
> an API."

### Three ways to get "flow"

- ***Method Chaining*** — "for many people, the central pattern of a fluent interface." A
  sequence of method calls where each call acts on the result of the previous one; methods
  compose by calling one on top of the other. Contrast with a normal API, which would use
  constructors with positional arguments and intermediate local variables.
  - **Caveat Fowler raises himself:** in ordinary OO code these are derided as "train wrecks"
    (methods separated by dots look like train cars) and are usually a sign of code brittle to
    interface changes in the middle of the chain. *Read fluently, though*, chaining composes
    many calls without a lot of variables, so the code seems to flow.
- ***Function Sequence*** — a sequence of plain method/function call *statements*. Laid out
  well, it reads as clearly as *Method Chaining*. He deliberately says "function" not "method"
  because it works in a non-OO context, whereas *Method Chaining* needs OO methods.

The critical principle stated here:

> "The point here is that fluency isn't as much about the style of syntax you use as it is
> about the way you name and factor the methods themselves."

### Command-query separation, and when to break it

**Definition.** *Command-query separation* (Meyer): methods on an object divide into commands
and queries. A **query** returns a value and does *not* change observable state. A **command**
may change observable state but should *not* return a value. Value of the principle: it lets
you identify query methods, which — having no side effects — can be called repeatedly and
reordered without changing the result. Commands demand much more care.

**The judgement call.** Fowler says he strongly encourages teams to use command-query
separation and has "used many decibels disparaging people who don't follow" it. But
*Method Chaining* in an internal DSL **usually breaks it**: each chained method alters state
*and* returns an object to continue the chain. His resolution: "fluent interfaces follow a
different set of rules, so I'm happy to allow it there."

**SDK relevance (high).** This is an explicit, principled carve-out: CQS is the default rule
for ordinary APIs; a fluent builder is the recognized exception. The exception is licensed by
the *style* of the interface, not by convenience — which implies you must be able to say which
style a given type is in.

### Naming rules differ by style

- **Command-query naming:** names must make sense **stand-alone**. People scan a list of
  methods on a doc page or in an IDE menu, so names must convey clearly what they do *in that
  kind of context*. "They are the labels on the buttons."
- **Fluent naming:** you concentrate less on each individual element and more on the **overall
  sentences** you can form. Names may make no sense in an open context but read properly inside
  a DSL sentence. "With DSL naming, it's the sentence that comes first; the elements are named
  to fit in with that context."

Summary of the contrast: DSL names are written with the context of the specific DSL in mind;
command-query names are written to work without any context (equivalently, in any context).

**SDK relevance (high).** A concrete, testable design rule. If you are naming for a fluent
builder, evaluate names by reading whole call chains aloud; if you are naming a command-query
API, evaluate each name in isolation in an autocomplete list. Applying the wrong test produces
either unreadable chains or unusable method lists.

---

## Section: The Need for a Parsing Layer

The central architectural principle of internal DSL implementation.

**The problem.** A fluent interface is a *different kind* of interface from a command-query
interface. Mixing both styles on the same class is confusing.

**The solution.** Keep the language-handling elements of a DSL separate from regular
command-query objects by building a layer of ***Expression Builders*** over regular objects.

**Definition — Expression Builder.** An object whose *sole* task is to build up a model of
normal objects using a fluent interface — "effectively translating fluent sentences into a
sequence of command-query API calls."

**The primary reason is separation of concerns, not style.** As soon as you introduce a
language, even an internal one, you must write code that understands that language. That code
often needs to track data that is only relevant *while the language is being processed* —
**parsing data**. Understanding how the internal DSL works is a reasonable amount of work, and
it is not needed once the underlying model is populated. You do not need to understand the DSL
or how it works in order to understand how the underlying model operates. Therefore keep
language-processing code in a separate layer.

**Mapping onto the general DSL architecture.** The underlying model of command-query objects is
the ***Semantic Model***. The layer of *Expression Builders* is (part of) the **parser**.

**Why "parser" for an internal DSL?** Fowler says he puzzled over the term. Normally "parser"
means parsing text; here the *host language* parser handles the text. The parallels are strong
enough to keep the word:

| Traditional (text) parser | Expression Builder layer |
|---|---|
| Input is a stream of tokens | Input is a **stream of function calls** |
| Arranges tokens into a syntax tree | Still useful to arrange function-call parse nodes into a tree |
| Uses parsing data structures (*Symbol Table*) | Uses the same kinds of structures (*Symbol Table*) |
| Populates a *Semantic Model* | Populates a *Semantic Model* |

**Benefits of separating Semantic Model from Expression Builders** (i.e., the payoff of the seam):

1. You can **test the builders and the model independently**.
2. You can have **multiple parsers** — mixing internal and external DSLs, or supporting several
   internal DSLs with several Expression Builders over one model.
3. You can **evolve the builders and the model independently**. Important because DSLs, like
   any software, are hardly ever fixed: you need to be able to change the underlying framework
   without changing DSL scripts, or vice versa.

**The one argument against Expression Builders.** Skip them only when the *Semantic Model*
objects use fluent interfaces themselves. That sometimes makes sense when fluent usage is the
main way people interact with the model. In most situations Fowler prefers a **command-query
interface on the model**, because it is more flexible across different contexts, and because a
fluent interface often needs temporary parsing data.

> "In particular, I object to mixing a fluent and a command-query interface on the same
> objects—that's just too confusing."

He assumes Expression Builders for the rest of the book, while acknowledging you need not
always use them.

**SDK relevance (very high).** This is the "two-layer library" principle: a plain, orthogonal,
side-effect-disciplined core API (the model), plus a separate ergonomic/fluent/builder surface
(the parser layer). It buys independent testing, multiple front-ends over one core, and
independent evolution of surface vs. core — the standard argument for keeping an SDK's
convenience layer physically separate from its object model. The corollary rule: **do not put
fluent and command-query methods on the same class.**

---

## Section: Using Functions

**Framing.** The function (a.k.a. subroutine, procedure, method) is the most successful
packaging construct we have. Command-query APIs are usually expressed in functions, and DSL
structures are also built primarily on functions. "The difference between a command-query
interface and a DSL centers around **how functions are combined**." The rest of the section is
a comparison of function-combination patterns.

### The combination patterns

- ***Method Chaining*** (see above)
- ***Function Sequence*** (see above)
- ***Nested Function*** — combines functions by making function calls the *arguments* of
  higher-level function calls, producing a nesting of invocations.

### Choosing factor 1: scope of the functions (the globalness problem)

- With *Method Chaining*, the DSL functions are methods that need only be defined on the
  objects taking part in the chain — usually an *Expression Builder*. Scope is naturally
  contained.
- With bare functions in a *Function Sequence*, the calls must resolve. The obvious way is
  **global functions**, which introduces two problems:
  1. **Polluting the global namespace.** Global functions are visible in every part of a
     program; ideally you want them available only within the DSL-processing part. Namespace
     features can help — Java's static imports let functions look global only when you import
     a particular namespace.
  2. **Global variables for parsing data** — the more serious problem. Any *Function Sequence*
     needs ***Context Variables*** to know where you are in the parse (e.g., which disk's size
     is being specified requires tracking "the current disk," updated by the earlier call).
     If the functions are global, that state ends up global too. Containment tricks exist
     (e.g. holding all the data in a singleton) "but you can't get away from global data if you
     use global functions."
- *Method Chaining* avoids most of this: you still need a bare function to *begin* the chain,
  but once started, all parsing data lives on the *Expression Builder* object that the chaining
  methods are defined on.

### The recommended cure: Object Scoping

***Object Scoping*** — in most cases, place the DSL script in a **subclass of an Expression
Builder**, so that bare function calls resolve against methods in the builder superclass.

This handles **both** globalness problems at once: the DSL functions are defined only in the
builder class (localized), and because they are instance methods they connect directly to
parsing data on the builder instance. "That's a compelling set of advantages for the cost of
placing the DSL script in a builder subclass, so that's my default option."

**Bonus: extensibility.** If the DSL framework makes it easy to subclass the scoping class,
users of the DSL can add their own DSL methods to the language.

**SDK relevance.** *Object Scoping* is a general recipe for "ambient/implicit context without
globals": put the API's verbs on a class, and let the user's code live inside a subclass or
block scoped to an instance. It also doubles as the extension point.

### Nested Function: what it buys and what it costs

Both *Function Sequence* and *Method Chaining* require *Context Variables* to track the parse.
*Nested Function* is a third technique that often avoids them.

**Advantages**

1. **Hierarchy is echoed by the language constructs themselves.** Very valuable, since
   hierarchic structure is extremely common in parsing. The nesting of functions reflects the
   logical syntax tree of the DSL. With *Function Sequence* and *Method Chaining* you can only
   *hint* at the syntax tree through strange indentation conventions.
2. **Changed evaluation order.** Arguments are evaluated before the enclosing function, so
   sub-objects arrive fully formed and the enclosing function can construct its object directly
   — often removing the need for a *Context Variable* entirely.
3. As a consequence, **Nested Function makes it safer to use global functions**, because it's
   easier to arrange for the global function to just return an object and not alter parsing state.

**Disadvantages**

1. **Punctuation noise.** Explicit parentheses and commas can feel like noise compared to
   indentation conventions alone. (Lisp scores highly here — its syntax works extremely well
   with *Nested Function*.)
2. **Bare functions**, so the same globalness problems as *Function Sequence* — with the same
   *Object Scoping* cure.
3. **Backwards reading order.** If you think in terms of a *sequence of commands* rather than
   building a hierarchic structure, the evaluation order confuses: a simple chain of nested
   calls evaluates backwards to the order written (`third(second(first()))`). Fowler quotes
   Neal Ford: writing "Old MacDonald Had a Farm" with *Nested Functions* would render the
   chorus as `o(i(e(i(e()))))`. *Function Sequence* and *Method Chaining* both let you write
   the calls in the order they'll be evaluated.
4. **Positional, not named, arguments.** `disk(75, 7200)` doesn't say which number is which.
   Partial fix: nested functions that just return the raw value (`disk(size(75), speed(7200))`)
   — more readable, but nothing stops you writing them in the wrong order and getting a
   surprising disk. To actually prevent that you must return *richer intermediate token objects*
   rather than plain integers — "an annoying complication." Languages with **keyword arguments**
   avoid the problem, but that useful syntactic feature is very rare.

Two important observations that follow:

> "In many ways, Method Chaining is a mechanism that helps you supply keyword arguments to a
> language that lacks them."

and *Literal Map* is another way to overcome the lack of named parameters.

**Perspective.** Heavy use of *Nested Function* looks unusual to most programmers, which
reflects how these combination patterns are used in ordinary programming: mostly *Function
Sequence*, with small dashes of *Nested Function* and (in OO) *Method Chaining*. Lisp
programmers use *Nested Function* often in regular code. These are **general expression-combination
patterns**, not DSL-only ones — what differs for a DSL is *which combination is good*.

### Hybrids and the punctuation trap

You will normally use a combination of these patterns; each has strengths and weaknesses and
different points in a DSL have different needs. Fowler walks through a hybrid: *Function
Sequence* at the top level (one statement per computer), *Nested Function* for each computer's
arguments, *Method Chaining* to build each processor and disk. Each part plays to a strength:

- *Function Sequence* works well for defining each element of a list, keeps each definition
  well separated into statements, and is easy to implement (each statement adds a fully formed
  object to a result list).
- *Nested Function* removes the need for a *Context Variable* for the current computer, and the
  argument list captures the shape "a processor plus a variable number of disks" with types.
- *Method Chaining* works well where an element has multiple **optional** arguments — you call
  whatever values you wish to set.

**But** he then rejects his own hybrid, on a principle worth quoting:

> "The punctuational differences are an artifact of the implementation, not the meaning of the
> DSL itself, so I'm exposing implementation issues to the user—always a suspicious idea."

Mixing patterns produces **punctuational confusion**: some elements separated by commas, others
by periods, others by semicolons. A programmer can figure it out; a non-programmer merely
*reading* the expression is more likely to be confused. His revised choice: use *Method
Chaining* instead of *Nested Function* for the computer function, but keep *Function Sequence*
for the list of computers, as that's a clearer separation for the user.

> "This tradeoff discussion is a microcosm of the decisions you'll need to make when building
> your own DSL."

**SDK relevance (high).** The rule generalizes far past DSLs: **syntactic inconsistency in an
API surface leaks implementation structure to the caller.** Prefer a uniform call shape across
the surface even at some cost in per-site elegance, especially where non-experts read the code.

---

## Section: Literal Collections

Programs usually compose statements into sequences and compose by applying functions. A third
way to compose elements is ***Literal List*** and ***Literal Map***.

- ***Literal List*** — captures a list of elements, of different types or the same type, with
  no fixed size. In curly-brace languages (Java, C#) a **varargs function call is a common way
  to introduce a Literal List**; a *Nested Function* whose arguments are a variable set of
  child calls is already a Literal List in disguise. Ruby's `[...]` literal-list syntax is
  usable in **more contexts than just inside a function call**, which is the advantage.
  C-like languages do have a literal array syntax (`{1,2,3}`) but you are usually quite limited
  as to where you can use it and what you can put in it.
- ***Literal Map*** (also hash or dictionary) — available in scripting languages. Especially
  handy where an element has **multiple sub-elements, all optional, each settable at most once**.
  *Method Chaining* is good at naming the sub-elements, but you must write your own code to
  ensure each is mentioned only once; with a *Literal Map* that constraint is baked in and
  familiar to users of the language.
- **Named parameters** are a still better construct for this (Smalltalk keyword messages
  express it directly). But **even fewer languages have named parameters than have Literal Map
  syntax**. If you have them, use named parameters as the way to implement a *Literal Map*.

**Definition — symbol data type.** A type that at first sight is just like a string, but exists
primarily for **lookups in maps, particularly *Symbol Tables***. Symbols are immutable and
usually implemented so that the same symbol value is the same object (for performance). Their
literal form doesn't support spaces and doesn't support most string operations, because their
role is symbol lookup rather than holding text. Ruby marks them with a leading colon. In
languages without symbols, use strings; in languages with them, use symbols for this purpose.

**Why Lisp is appealing for internal DSLs.** Lisp has a very convenient literal list syntax
`(one two three)`, and uses the *same* syntax for function calls `(max 5 14 2)`. A Lisp program
is all nested lists, and bare words are symbols — so the syntax is entirely about representing
**nested lists of symbols**, an excellent basis for an internal DSL, *provided you are happy
with your DSL having that same fundamental syntax*. This simple syntax is both a great strength
(logical, perfectly consistent once you follow it) and a weakness (an unusual syntactic form;
if you don't make the jump, it all looks like "lots of irritating, silly parentheses").

---

## Section: Using Grammars to Choose Internal Elements

A **technique for choosing among internal DSL constructs**: consider the *logical grammar* of
your DSL. The kinds of grammar rules you write for *Syntax-Directed Translation* also make
sense for reasoning about an internal DSL; certain kinds of *BNF* rule suggest certain internal
DSL structures.

| Grammar structure | BNF form | Consider |
|---|---|---|
| Mandatory list | `parent ::= first second third` | *Nested Function* |
| Optional list | `parent ::= first maybeSecond? maybeThird?` | *Method Chaining*, *Literal Map* |
| Homogeneous bag | `parent ::= child*` | *Literal List*, *Function Sequence* |
| Heterogeneous bag | `parent ::= (this \| that \| theOther)*` | *Method Chaining* |
| Set | n/a (doesn't fit BNF) | *Literal Map* |

Reasoning behind each:

- **Mandatory elements → *Nested Function***. The arguments of a *Nested Function* match the
  rule's elements directly. With strong typing, **type-aware autocompletion can suggest the
  correct items for each argument position** — a tooling argument for this choice.
- **Optional elements → *Method Chaining***. *Nested Function* gets awkward here because you
  can easily end up with a combinatorial explosion of overloads. With *Method Chaining* the
  method call itself indicates which element you are supplying. The tricky part is doing the
  work to ensure only one use of each item in the rule.
- **Many items of the same sub-element (`child*`) → *Literal List***. If the expression defines
  the **statements at the top level of your language**, that is "one of the few places I'd
  consider *Function Sequence*."
- **Many items of differing sub-elements → *Method Chaining***, since the method name is a good
  signal of which element you're looking at.
- **Set of sub-elements** (multiple children, each at most once, any order) is a common case
  that **doesn't fit BNF well**; you can think of it as a mandatory list whose children may
  appear in any order. *Literal Map* is the logical choice; the problem you'll normally run
  into is the **inability to communicate and enforce the correct key names**.
- **At-least-once rules (`child+`)** don't lend themselves well to internal DSL constructs.
  Best bet: use the general multiple-element forms and **check for at least one call during the
  parse**.

**SDK relevance (high).** This is a directly reusable design procedure for API surfaces: write
down the *shape* of what the caller must supply (mandatory / optional / repeated / set), and
let that shape pick the call form — positional constructor args vs. builder methods vs. list
vs. options-map. It also names the enforcement gaps you must cover in code (uniqueness for
chained optionals, key-name validity for maps, at-least-once for repeats).

---

## Section: Closures

**Definition.** Closures (a.k.a. lambdas, blocks, anonymous functions) let you take some inline
code, package it into an object, pass it around, and evaluate it whenever it suits you.

In internal DSLs we use closures as ***Nested Closures*** within DSL scripts. A *Nested Closure*
has **three properties** that make it handy:

1. **Inline nesting.** Like *Nested Function*, it captures the hierarchic structure of the DSL
   in a way meaningful to the host language, rather than merely suggesting hierarchy with
   indentation (as *Function Sequence* and *Method Chaining* must). The additional advantage:
   you can put **any inline code** into the nesting — most languages restrict what can go into
   function arguments, and a *Nested Closure* breaks those limitations. You can therefore nest
   more complicated structures, e.g. a *Function Sequence* inside a *Nested Closure*, which
   would be impossible inside a *Nested Function*. Many languages also make it syntactically
   easier to nest multiple lines inside a closure than inside a function call.
2. **Deferred evaluation** — "perhaps the most important capability that Nested Closure adds."
   With *Nested Function*, arguments are evaluated before the enclosing call; sometimes helpful,
   sometimes confusing (the Old MacDonald problem). With a *Nested Closure* you have **complete
   control over when closures are evaluated**: alter the order, skip some entirely, or store
   them all for later evaluation. This is particularly valuable when the *Semantic Model* takes
   strong control of how a program executes — a form of model Fowler calls an ***Adaptive
   Model*** (Ch. 7). In those cases a DSL can include **sections of host code inside the DSL**
   and put those code blocks into the Semantic Model, letting you intermix DSL and host code
   much more freely.
3. **Limited-scope variables.** A closure can introduce variables whose scope is that closure,
   making it easier to see what the methods in the language are acting on. It also removes the
   need for global functions or *Object Scoping*: the DSL verbs are defined on the
   limited-scope variables, which are themselves *Expression Builders*.

**What the examples demonstrate conceptually.**
- The Ruby builder example (`ComputerBuilder.build do |c| ... c.processor do |p| ... end end`)
  shows inline nesting (each nested block contains several statements of ordinary Ruby) plus
  limited-scope variables for computer/processor/disk. The block parameters "add a bit of noise,
  but can make it easier for people to see what objects are being manipulated," and remove the
  need for globals/*Object Scoping*.
- The C# validation example (a builder subclass overriding `build()`, with
  `Validate("...").With(p => ...)`) shows **deferred evaluation carrying host code into the
  model**: the closure takes a person and contains arbitrary host code; that code is **stored
  in the Semantic Model and executed as the model runs**, giving a lot of flexibility in
  choosing validations. Fowler frames validation itself as usually **contextual** — you validate
  an object *in order to do something to it*, e.g. different rules to check eligibility for one
  insurance policy versus another — which is exactly why hard-coding "is this object valid" is
  insufficient.

**Language-support caveats and workarounds.** *Nested Closure* is very useful but often
frustratingly awkward. Many languages (Java, at the time) don't support closures. Substitutes:
function pointers in C, command objects in an OO language — these are valuable for supporting
*Adaptive Models* in such languages, but they "require a lot of unwieldy syntax that can add a
debilitating amount of noise to a DSL." Even languages that *do* support closures often have
awkward syntax: C# has improved steadily but still isn't as clean as he'd like; Smalltalk's is
very clean; Ruby's is almost as clean as Smalltalk's, which is why Nested Closures are so
common in Ruby. Oddly, Lisp — despite first-class closures — has awkward closure syntax, which
it works around with macros.

**SDK relevance.** Callbacks/lambdas in an API give you three distinct things (nesting/scoping,
deferred execution, scoped handles). Deferred execution is what lets user code be *stored as
data* in your model and run under your control — the basis of rule engines, policy objects,
and configuration-as-code. Noise in the host closure syntax is a real, first-order cost of the
design.

---

## Section: Parse Tree Manipulation

**Basic idea.** Take an expression in the host programming language and, instead of evaluating
it to get its result, **treat its parse tree as data**. A comparison expression can either be
evaluated (yielding a boolean) or processed to yield a parse tree of node objects
(binary expression → member access + constant, etc.).

**What it enables.** With the parse tree in hand you can manipulate it at runtime — e.g. walk
it and generate a query in another query language such as SQL. "This is essentially what .NET's
Linq language does," letting you express many SQL queries in C#, which many programmers prefer.

**Strength.** It lets you write expressions in the host language that are then **converted into
different expressions** which populate the *Semantic Model* — going beyond just storing the
closure itself (contrast with *Nested Closure*, where you keep and later run the host code
as-is).

**Two implementation families.**
- **Object model of the parse tree** (the C#/Linq style).
- **Macro transformations on source code** (Lisp), well suited because Lisp's source structure
  is very close to a syntax tree. *Parse Tree Manipulation* is more widely used in Lisp — "so
  much so that Lispers often wail at the lack of macros in other languages." Fowler's view is
  that manipulating an object model of the parse tree, C#-style, is a more effective way to do
  it than Lisp macros, though he concedes this may reflect his lack of practice with Lisp macros.

**How important is it?** The prominent use is Linq: one C# query can be turned into SQL for
relational databases, XPath for XML structures, or kept in C# for in-memory structures. It is
"essentially a mechanism that allows application code to do runtime code translation,
generating arbitrary code from C# expressions." Powerful but somewhat complex, and historically
not well supported; getting attention due to C# 3 and Ruby. **Fowler's assessment: a marginal
technique — rarely needed, but very handy on the occasions that need arises.** Translating
queries to multiple data targets is the perfect example of its usefulness.

**SDK relevance.** This is the "expression tree" API pattern (LINQ, ORM query builders, tracing
JITs). The design test is whether you need to *retarget* the user's expression to a different
execution engine; if you only need to *run* it, a plain closure is far simpler.

---

## Section: Annotation

**Definition.** An ***Annotation*** (Java) / attribute (C#) allows a programmer to **attach
metadata to programming constructs** such as classes and methods. The annotations can be read
during compilation or at runtime. (Fowler uses the Java name because "attribute" is such an
overloaded term.)

**Worked idea.** Declaring that fields may only hold a limited valid range, via an annotation
on the field carrying lower bound, upper bound, and units. The obvious alternative is putting
range-checking code into the setter. Advantages of the annotation over the setter check:

1. It **reads more clearly** as a bound on the field.
2. It makes it easy to check the range **either when setting the attribute or in a later object
   validation step** — i.e., it decouples the *declaration* of the rule from *when the rule is
   enforced*.
3. It **specifies the validation rule in a form that could be read to configure a GUI widget** —
   the rule becomes reusable metadata, not just behavior.

**Conceptual framing.** Some languages have a dedicated feature for such number ranges (Pascal
did). Think of Annotations as a way of **extending the language to support new keywords and
capabilities**. Fowler goes further: even existing keywords might have been better done with
Annotations — from a green field he'd argue access modifiers (`private`, `public`) would be
better that way.

**When to use.** Because Annotations are so closely bound to the host language, they suit
**fragmentary DSLs, not stand-alone DSLs**. They are particularly good at providing a very
integrated feel of adding domain-specific enhancements to the host language.

**Same concept, different clothing.** Rails' `validates_length_of :last_name, :maximum => 30`
differs in syntax (you name the field rather than placing the annotation next to it) and in
implementation (it's a class method executed when the class is loaded, not a language feature),
but it is still about adding metadata to program elements and is used similarly — so Fowler
counts it as essentially the same concept.

**SDK relevance.** Declarative metadata (decorators, attributes, annotations) turns policy into
data that multiple consumers — validators, serializers, UI generators, docs — can read. The
design test given here is exactly that multi-consumer reuse, not brevity.

---

## Section: Literal Extension

**What it is.** ***Literal Extension*** = the ability to add methods to external library
classes, so that a chain can *begin on a literal*. The famous Rails example is a fragment like
`5.days.ago`: most of it is ordinary *Method Chaining*; the tricky part is that the chain begins
on a **literal integer**, and integers are provided by the language or standard libraries.

**Availability.** May or may not be a capability of the host language. **Java does not support
it. C# does (extension methods) and Ruby does.**

**The danger.** It **adds methods globally**, when they should only be used within the often
limited context of DSL usage. This is a problem in Ruby, compounded by there being no easy
mechanism in the language to find where the extension was added. **C# handles this by putting
extension methods in a namespace you must explicitly import** — an explicit design lesson about
scoping monkey-patched capabilities.

**Verdict.** "One of those things that you don't need to use terribly often, but can be very
handy when you do—it really gives the sense of customizing the language for your domain."

**SDK relevance.** Direct guidance on extension methods / prototype extension / trait imports:
opt-in, namespaced extension is the safe form; unscoped global extension is the hazard, and
discoverability of *who added what* is the deciding criterion.

---

## Section: Reducing the Syntactic Noise

The point of internal DSLs is that they are just expressions in the host language written to
read well — which means they **bring the host language's syntax with them**. That's partly good
(familiar syntax for many programmers) and partly annoying.

Two mitigation techniques, with Fowler's opinion of each:

1. ***Textual Polishing*** — write chunks of DSL in a syntax *very close to but not exactly*
   the host language, then apply simple text substitution to convert it to the host language.
   E.g. converting `3 hours ago` into `3.hours.ago`, or more ambitiously converting
   `3% if value at least $30000` into a chained expression.
   **Fowler is not a big fan:** "The substitutions get convoluted pretty quickly, and when they
   do it's much easier to use a full external DSL." (I.e., the technique has an unstable middle
   ground — once it gets hard, you should have written an external DSL.)
2. **Syntax coloring.** Most text editors provide customizable coloring schemes. When
   communicating with domain experts, use a special scheme that **de-emphasizes noisy syntax** —
   e.g., color it light grey on white, or even color it the same as the background so it
   disappears entirely. (A tooling answer rather than a language answer.)

---

## Section: Dynamic Reception

**Mechanism.** Dynamic languages (Smalltalk, Ruby) process method invocations at runtime, so a
call to an undefined method compiles happily and raises only at runtime (unlike C# or Java,
where you get a compilation error). These languages route the unexpected call to a special
method — `method_missing` in Ruby, `doesNotUnderstand` in Smalltalk — whose default action is
to raise an error. Overriding that method to do something else is what Fowler calls
***Dynamic Reception***: "making a dynamic (runtime) choice about what is a legal method to
receive." It supports useful idioms generally, particularly **proxies**, where you wrap an
object and act on its method invocations without knowing exactly which methods are called.

**The DSL use.** A common use is to **move information from method arguments into the method
name itself**. Rails Active Record "dynamic finders" are the example: instead of defining a
`find` method per field, or a generic finder taking the field name as an argument
(`find_by("firstname", "martin")`), Dynamic Reception lets you write
`find_by_firstname("martin")` without having to define the method in advance. The missing-method
handler checks whether the invoked method begins with the known prefix, extracts the field name
from the method name, and turns it into an invocation of the fully parameterized method. This
can be done in one method, or split across several (`people.find.by.firstname("martin")`).

**The crux and the danger.**

- **Crux:** you get the option to move information from parameters to method names, which in
  some cases makes expressions easier to read and understand.
- **Danger:** "it can only take you so much." You don't want to be encoding complicated
  structures into a sequence of method names. **If you need anything more complicated than a
  single list of things, use something with more structure** — *Nested Function* or
  *Nested Closure*.
- **When it works best:** when you are doing the **same basic processing for each call**, e.g.
  building a query based on property names. If you would handle the dynamically received calls
  *differently* (different code for `firstname` and `lastname`), **write explicit methods
  instead** of relying on Dynamic Reception.

**SDK relevance.** A sharp rule for `__getattr__`/proxy/magic-method APIs: use them only for
uniform, mechanically-derived families of names; the moment per-name behavior diverges, or the
encoding needs structure, you have outgrown the technique. Also a reminder that such APIs
sacrifice discoverability and static checking.

---

## Section: Providing Some Type Checking

The mirror image of the previous section: how **static** languages can benefit from static type
checking in a DSL.

**Framing.** Fowler explicitly declines to re-fight the static-vs-dynamic typing debate (some
value compile-time checking highly; others say such type checking catches few errors that good
tests — always needed — don't). He instead raises the **second argument for static typing:
modern IDEs**. Excellent tool support depends on static typing — type a variable name, hit a
key combination, and get the list of methods available for that variable's type, because the
IDE knows the types of the symbols in the code.

**The problem for DSLs.** Most symbols in a DSL **don't get that support**, because we
represent them as strings or symbol data types held in our own symbol table. The state machine
example makes it concrete:

- In Ruby, states and events are symbols (`:waitingForLight`, `:lightOn`).
- Translated to Java naively, symbols become **primitive strings**: you must wrap the state name
  in a `state("...")` method so you have something to chain onto, you type quoted names by hand,
  and when naming a target state you get **no autocompletion** from a list of valid states.

**What Fowler would rather have:** the state name appearing as a *bare identifier*, with events
and target states also bare identifiers — `waitingForLight.transition(lightOn).to(unlockedPanel)`.
Benefits: it reads better, it avoids both the wrapper method and the noisy quotes, and it gives
**proper type-aware autocompletion for triggering events and target states**, making full use of
the IDE's capabilities.

**How to get it.** You need a way to declare **symbol types** (e.g. `state`, `command`, `event`)
in your DSL processing mechanism, and then declare the specific symbols used in a particular
script (e.g. `lightOn`, `waitingForLight`). One way is a ***Class Symbol Table***: the DSL
processor defines **each symbol type as a class**; when you write a script, you put it in a
class and **declare fields for your symbols**. So to define a list of states you create a
`States` class for the symbol type, and the states used in a script are introduced by a field
declaration naming them.

**Honest cost.** "The result, like many DSL constructs, looks rather strange. I would never
normally advocate a plural name for a class such as used here for `States`. But it does result
in an editing experience that meshes much more closely with the general experience of Java
programming."

**SDK relevance (high).** A generalizable technique: **strings are the enemy of tooling.**
Turning stringly-typed identifiers into declared, typed symbols (enums, constant objects, typed
tokens, literal-union types) buys autocompletion, refactoring, and compile-time checks — at the
cost of a declaration step and some odd-looking type names. Fowler explicitly accepts an
aesthetic cost (a plural class name) in exchange for tool support, which is a useful precedent
for judging similar tradeoffs.

---

# Chapter 5: Implementing an External DSL

(Fowler, DSL book, Ch. 5 "Implementing an External DSL")

## Framing (chapter opening)

With internal DSLs you can achieve flow, but you are ultimately limited by the syntactic
structure of the host language. **External DSLs provide greater syntactic freedom — the ability
to use any syntax you like.** Implementation differs in that parsing operates on **pure text
input, not constrained by any particular language**. The techniques are the ones the programming
language community has used for decades, and there is a long-running community developing these
tools and techniques.

**The catch (an important orientation warning).** The tools and writings of the programming
language community almost always assume you are working with a **general-purpose** language;
DSLs "are lucky to get a mention in passing." Many principles apply equally, but there are
differences. Also, **you don't need to understand as much to work with DSLs** — you don't need
to go all the way up the learning curve required for a general-purpose language. (This warning
recurs throughout the chapter: docs, defaults, and idioms of parser tooling are aimed at a
different problem than yours.)

---

## Section: Syntactic Analysis Strategy

**Definition — syntactic analysis.** Taking the stream of text and breaking it into some kind of
structure you can use to figure out what the text says. E.g., recognizing that a given line is
an *event* definition and telling it apart from a *command* definition.

### Option 1: Delimiter-Directed Translation

***Delimiter-Directed Translation*** — pick some delimiter characters (usually line endings)
that break the input into statements, chop the input into separate statements using that
delimiter, and feed each chunk into a separate processing step to figure out what's on the line.
Usually there's a clear marker in the line (a leading keyword) telling you what kind of
statement you're dealing with.

- **Pros:** very simple; uses tools most programmers already know — **string splitting and
  regular expressions**.
- **Con (the decisive one):** "it doesn't give you any inherent way to handle the **hierarchic
  context** of your input." As soon as the language nests (an `events ... end` block containing
  declarations), a line no longer carries enough information on its own; you can manage the
  context yourself, but **the more hierarchic context you get, the more effort you have to spend
  managing it yourself.**

### Option 2: Syntax-Directed Translation

***Syntax-Directed Translation*** — first define a **formal grammar** for the input language.

**Definitions.**
- **Grammar:** a way of defining the legal syntax of a programming language, almost always
  written in some form of ***BNF***.
- **Production rule:** each line of the grammar; it states a name followed by the legal elements
  of that rule. Items in quotes are literals; `*` indicates the preceding element may appear
  many times.

**Key observation:** a grammar is a good way of thinking about the syntax of a language *whether
or not* you use Syntax-Directed Translation — it is helpful for thinking about internal DSLs
too (cf. Ch. 4's table of internal DSL elements). It works particularly well for SDT because you
can translate it **fairly mechanically into a parser**. The resulting parsers handle hierarchic
structures very capably (essential for general-purpose languages), so things that are awkward
with Delimiter-Directed Translation become much easier.

### Three ways to get from a grammar to a parser

1. ***Recursive Descent Parser*** — the classic conversion. Easy to understand: **each grammar
   rule turns into a function** in the parser, and there are clear patterns for turning each BNF
   operator into control flow.
2. ***Parser Combinator*** — "a more hip and modern way." **Each rule becomes an object**, and
   you compose the objects into a structure that mirrors the grammar. You still need the
   elements of a recursive descent parser, but they're packaged into combinator objects you just
   compose — so you can implement a grammar **without knowing the details of the recursive
   descent algorithms**.
3. ***Parser Generator*** — takes a flavor of BNF and **uses it as a DSL**; you write your
   grammar in that DSL and the generator generates a parser for you. (This is itself "much of
   what this book is about.")

### Tradeoffs among the three

| Approach | Strengths | Weaknesses |
|---|---|---|
| *Parser Generator* | Most sophisticated; tools very mature; handle complex languages efficiently. **BNF-as-DSL makes the language easy to understand and maintain, since its syntax is clearly defined and automatically tied to the parser.** | Take time to learn; mostly use **code generation**, so they **complicate the build process**; may not exist for your platform, and writing one yourself is not trivial. |
| *Recursive Descent Parser* | Less powerful/efficient, but "powerful and efficient enough for a DSL"; a reasonable option when a Parser Generator isn't available or feels too heavyweight. | **The grammar gets lost in the control flow**, which makes the code far less explicit than Fowler would like. |
| *Parser Combinator* | Fowler's preference when you can't or don't want to use a Parser Generator. Same basic algorithm as recursive descent, but **represents the grammar explicitly in the composing code** — can get pretty close to true BNF, particularly if you introduce internal DSL techniques. | Composition code may not be quite as clear as a true BNF. |

**Overall judgement.** With any of the three, SDT makes structured languages much easier than
Delimiter-Directed Translation. "The biggest downside of Syntax-Directed Translation is that it's
a technique that isn't as widely known as it should be." People fear it's hard; Fowler argues
the fear "often comes from the fact that Syntax-Directed Translation is usually described in the
context of parsing a general-purpose language—which introduces a lot of complexities that you
don't face with a DSL."

**Book's choice.** Fowler mostly uses a *Parser Generator* — specifically **ANTLR** (mature,
widely available, open source). One advantage he cites: ANTLR is a **sophisticated form of
Recursive Descent Parser**, so it fits in well with the understanding you get from *Recursive
Descent Parser* or *Parser Combinator*. He recommends ANTLR as a good starting point for people
new to SDT. The maturity of the tooling and the explicitness of the grammar also make it easier
to *talk about* the concepts.

**SDK relevance (moderate).** The grammar-as-DSL point matters beyond parsing: a declarative
spec that is *automatically tied to the implementation* (rather than documented separately) is
the property that makes Parser Generators worth their build-complexity cost. Same argument
applies to schema-driven or IDL-driven SDK surfaces.

---

## Section: Output Production Strategy

**Framing.** You must know what your output is. Fowler's stance: most of the time the output
should be a ***Semantic Model***, which you then either interpret directly or use as input for
code generation.

**Explicit warning about the language community's assumptions:** within that community there is
a strong emphasis on **code generation**, and parsers are usually constructed to **directly
produce output code with no Semantic Model in sight**. That's a reasonable approach for
general-purpose languages, but not what Fowler suggests for DSLs. Bear this difference in mind
when reading material produced by the language community — "which includes most documentation
for tools such as *Parser Generators*."

**The three strategies:**

1. ***Embedded Translation*** (single-step). Place calls **directly in the parser** to create
   the Semantic Model *during* the parsing process. You gradually build up the model as you go
   through the parse: as soon as you understand enough of the input to recognize a part of the
   Semantic Model, you create it. You'll often need **intermediate parsing data** before you can
   actually create the objects — usually stored in ***Symbol Tables***.
2. ***Tree Construction*** (two-step). Parse the input text and produce a **syntax tree**
   capturing the essential structure of that text; also populate a **Symbol Table** to handle
   **cross-references between different parts of the tree**. Then run a **second phase** that
   walks the syntax tree and populates the Semantic Model.
3. ***Embedded Interpretation***. Run an interpretation process **during** the parse, whose
   output *is* the final result — e.g. a calculator that takes arithmetic expressions and
   produces the answer. **Produces no Semantic Model.** Comes up from time to time, but it's a
   rare case.

**Analogy given:** *Embedded Translation* is like **SAX**; *Tree Construction* is like **DOM**.

**Semantic-Model-less variants.** You can use *Embedded Translation* and *Tree Construction*
without a Semantic Model; this is quite common when using code generation, and most Parser
Generator examples do one of these. It may make sense particularly for simpler cases, but Fowler
recommends it only rarely: "Usually I find the Semantic Model overwhelmingly helpful."

**The real choice, and the tradeoff.** Mostly it's *Embedded Translation* vs *Tree Construction*,
and the decision depends on the costs and benefits of that **intermediate syntax tree**.

Arguments **for Tree Construction**:
- It **splits the parsing problem into two simpler tasks**. Usually it's easier to combine two
  simple tasks than to write one more complicated task — and this becomes increasingly true as
  the complexity of the overall translation increases.
- While recognizing the input text you can focus **only** on building the syntax tree; many
  Parser Generators provide a DSL for tree construction that simplifies this further.
- Walking the tree to populate the Semantic Model is then "a more regular programming exercise,"
  and **you have the whole tree available to examine** in order to determine what to do (whereas
  Embedded Translation only ever sees the part parsed so far).
- The more involved the DSL, and **the greater the distance between the DSL and the Semantic
  Model**, the more useful the intermediate syntax tree — particularly if you have tooling
  support to create an abstract syntax tree.

Arguments **against**:
- The common counterargument is **memory** consumed by the syntax tree, which Fowler says
  "withers away when processing small DSLs on modern hardware" — i.e., he does *not* find this
  persuasive.
- His actual reservation: sometimes building and walking the tree feels like more trouble than
  it's worth. You must write the code to create the tree **and** code to walk it; often it's
  easier to just build the Semantic Model right there and then.

**Honest verdict:** "So, I'm conflicted on the choice. Other than the vague notion that
increasing complexity of translation favors Tree Construction, I have mixed feelings. My best
advice is to try a little of both and see which you prefer."

**SDK relevance.** The generalizable principle is the **distance heuristic**: when the input
representation and the target representation are far apart, insert an explicit intermediate
representation; when they're close, translate in one pass. Also the reminder that an
intermediate representation costs you *two* bodies of code (build + consume).

---

## Section: Parsing Concepts

Concepts you'll run into when reading about parsing and using *Parser Generators*. You need
many of them to make sense of *Syntax-Directed Translation* — "albeit not to the extent that
traditional compiler books assume, since we're dealing with DSLs rather than general-purpose
languages."

### Subsection: Separated Lexing

**Definition.** SDT is usually divided into two stages:
- **Lexing** (also scanning or tokenizing) — takes the input text and transforms it into a
  **stream of tokens**. A **token** is a data type with two primary attributes: **type** and
  **content**. E.g. the text `state idle` becomes two tokens: one with content "state" and type
  *state-keyword*, one with content "idle" and type *identifier*.
- **Syntactic analysis** (also, confusingly, called "parsing") — takes the token stream and
  arranges it into a **syntax tree**, based on the grammar rules.

***Regex Table Lexer*** — an easy way to write a lexer: simply a list of rules matching regular
expressions to token types. Read the input stream, find the first regexp that matches, create a
token of the corresponding type, and repeat with the next part of the stream.

**Consequence 1 — the lexer runs first, and that constrains your text.** If you write
`state initial state`, intending to *name* a state "initial state," the lexer will by default
classify the second `state` as a **keyword**, not an identifier. To avoid this you must use some
scheme of ***Alternative Tokenization***; how you do it depends a great deal on your parser tool.

**Consequence 2 — whitespace is generally discarded before the parser sees anything**, which
makes **syntactic whitespace** difficult.
- **Definition — syntactic whitespace:** whitespace that is part of the syntax of the language,
  such as using newlines as statement separators (***Newline Separators***) or using indentation
  to indicate structure in the manner of Python.
- **Why it's knotty:** it **intermixes the syntactic structure of the language with formatting**.
  In many ways it makes sense for these to match — our eye uses formatting to infer structure,
  so it's advantageous for the language to use it the same way. "However, there's just enough
  edge cases where the two needs don't quite line up, which introduces a lot of complications.
  This is why many language people really hate syntactic whitespace." Fowler covers *Newline
  Separators* (a common form) but ran out of time to treat syntactic indentation in depth.

**Why separate the lexer at all?** It "makes it much easier to write each of the two elements" —
another case of **decomposing a complicated task into two simpler tasks**. It also improves
performance, particularly on the more limited hardware these tools were originally designed for.

### Subsection: Grammars and Languages

**Key correction of a common misconception.** Fowler writes *a* grammar for a language, not
*the* grammar. While a grammar formally defines the syntax of a language, **it's quite easy for
more than one grammar to recognize the same language.** He shows two different grammars for the
same events-block input: both valid, both recognize the input, **but the resulting parse trees
differ, and thus the output-generation code differs.**

**Why you get different grammars:**
- Different *Parser Generators* use different grammars, in terms of both syntax and semantics.
- Even with a single Parser Generator, you get different grammars depending on **how you factor
  your rules**.
- "Just like with any code, you refactor your grammars to make them easier to understand."
- Another factor that alters factoring is the **output production code**: "I often end up
  altering my grammar to make it easier to organize the code that translates source into the
  semantic model."

**Principle:** the grammar is *code*, subject to refactoring and shaped by what you need to do
with it — not a pristine spec.

### Subsection: Regular, Context-Free, and Context-Sensitive Grammars

**The Chomsky hierarchy** — developed by linguist Noam Chomsky in the 1950s, based on natural
rather than computer languages, deriving its classification from the **mathematical properties
of a grammar** used to define syntactic structure. Three categories concern us, forming a
hierarchy (regular ⊂ context-free ⊂ context-sensitive). Strictly it applies to grammars, but
people use it for languages too; "a language is regular" means you can write a regular grammar
for it.

**The key practical distinction is what kind of fundamental algorithm the parser needs:**

- **Regular grammar** — can be processed using a **finite-state machine**. Since **regular
  expressions are finite-state machines**, a regular language can be parsed using regular
  expressions.
  - **Fatal limitation:** regular grammars **can't deal with nested elements**. They can parse
    a flat arithmetic expression but not one with nested parentheses. "You may hear people
    saying that regular grammars 'can't count.'" In parsing terms: you can't use a finite-state
    machine to parse a language that has **nested blocks** — which also rules out ordinary block
    structure (nested `for`/`if` braces). So programs with nested blocks are not regular.
- **Context-free grammar** — adds **hierarchic context**, allowing it to "count." Implemented
  using a **push-down machine**: a finite-state machine **with a stack**. Most language parsers
  use context-free grammars, most *Parser Generators* use them, and both *Recursive Descent
  Parser* and *Parser Combinator* produce a push-down machine. Most modern programming languages
  are parsed using context-free grammars.
  - **Its limitation:** it can't handle all syntactic rules you might want. **The common
    exception is the rule that you must declare a variable before you use it** — the declaration
    often occurs *outside* the branch of the hierarchy you're in when you use the variable. A
    context-free grammar can hold hierarchic context, but that's not enough context here —
    **hence the need for *Symbol Tables***.
- **Context-sensitive grammar** — the next step up; *could* handle the declare-before-use case,
  "but we don't know how to write general context-sensitive parsers. In particular, we don't
  know how to generate a parser from a context-sensitive grammar."

**Why Fowler goes into this at all — the practical payoff:**
1. It tells you **which tool to use**: if you use nested blocks you need something that can
   handle a **context-free** language. And if you need nested blocks, you're likely better off
   with *Syntax-Directed Translation* rather than *Delimiter-Directed Translation*.
2. It suggests you don't need a push-down machine for a merely regular language — **but** in
   practice it's easier to use a push-down machine anyway: "once you've got used to using them,
   they are sufficiently straightforward, so it usually isn't overkill to use one even for a
   regular language."
3. It explains **why we see separated lexing**: lexing is usually done with a finite-state
   machine while syntactic analysis uses a push-down machine. This **limits what you can do in
   the lexer but allows the lexer to be faster**. Exceptions exist — **ANTLR uses a push-down
   machine for both lexing and syntactic analysis**.

**Tooling notes.** Some parser tools only handle regular grammars (**Ragel** is a better-known
example); you can also use lexers on their own to recognize a regular grammar. But if you're
getting into SDT, **start with a context-free tool**.

***Parsing Expression Grammar (PEG)*** — a relative newcomer using a different form of grammar
that can handle most context-free situations and some context-sensitive ones. **PEG parsers
don't tend to separate lexing**, and a PEG "is more usable than a context-free grammar in many
situations." At the time of writing, PEGs were still relatively new with rare and immature
tools, hence little coverage in the book. The best-known PEG parsers are **Packrat** parsers.
The line between PEGs and traditional parsers is not solid — **ANTLR has incorporated many ideas
from PEGs**.

### Subsection: Top-Down and Bottom-Up Parsing

One of the biggest distinguishing features among parsers and *Parser Generators*. It affects
both how the parser works **and the kinds of grammars it can work with**.

- **Top-down parser:** begins with the **highest level rule** in the grammar and uses it to
  decide what to try and match. "A top-down parser uses the rules as **goals** to direct what to
  look for."
- **Bottom-up parser:** starts by reading tokens; checks whether the input so far is enough to
  match a rule; if not, it puts it aside (**shifting**) and takes the next token; when enough
  tokens match a rule, it **reduces** them to that rule's element. Hence **shift-reduce parsing**.

**Terminology.** Top-down parsers are called **LL** parsers, bottom-up **LR** parsers. The first
letter refers to the direction in which the input is scanned; the second to how the rules are
recognized (L = left-to-right, i.e. top-down; R = right-to-left, hence bottom-up). Bottom-up is
also called **shift-reduce parsing** — the most likely bottom-up approach you'll run into.
Variants of LR include **LALR, GLR, SLR** (not covered).

**Which is harder?** Bottom-up parsers are usually considered harder to write and understand,
because most people find it harder to visualize the order in which rules are processed. You
don't have to write the parser if you use a Parser Generator, **but you do have to understand
roughly how it works in order to debug problems**. The best-known Parser Generator family is
**Yacc**, which is bottom-up (LALR).

**Where the book's tools sit.** Recursive descent is a top-down algorithm, so *Recursive Descent
Parser* is top-down, as is *Parser Combinator*; ANTLR is based on recursive descent and is thus
top-down.

**The big disadvantage of top-down: left recursion.** A rule of the form `expr : expr '+' expr;`
pushes the parser into endless recursion. People disagree about how big a problem this is in
practice. There's a **simple, mechanical technique called left-factoring** to remove left
recursion, but the result is a grammar that isn't as easy to follow. The good news: you only
really run into this when dealing with ***Nested Operator Expressions***, and once you
understand the idioms for those you can churn them out relatively mechanically. The resulting
grammar still won't be as clear as for a bottom-up parser, but knowing the idiom gets you there
much quicker.

**General point about Parser Generators.** Different generators have various restrictions on the
grammars they can handle, driven by their parsing algorithms. There are plenty of other
differences too: **whether you write actions in the grammar, how you can move data up or down
the parse tree, and what the grammar syntax is like (BNF vs. EBNF)**. All of these affect how you
write your grammar.

> "Perhaps the most important point is to realize that you shouldn't treat the grammar as a fixed
> definition of the DSL. Often, you'll need to alter the grammar to make the output production
> work better. Like any other code, the grammar will change depending on what you want to do
> with it."

**Who needs this.** For people comfortable with these concepts they play an important role in
**deciding which parser tool to use**. For more casual users they probably don't affect tool
choice, but "are useful to bear in mind as they alter how you work with the chosen tool."

---

## Section: Mixing-in Another Language

**The danger being addressed.** "One of the biggest dangers that you face with an external DSL
is that it may accidentally evolve to become a general-purpose language." Even short of that, a
DSL can easily become **overly complex, particularly if you have a lot of special cases that
need particular treatment but are only used rarely.**

**The worked scenario.** A lead-allocation DSL assigns sales leads to salesmen based on product
type and customer state, with simple rules. Then a genuinely special case arrives — assign one
salesman all leads of a certain product whose company names start with a given prefix, in a set
of states. "There may be a dozen special cases like this, all of which need extending the DSL in
a particular direction. But including special tweaks for individual cases may add a lot of
complication to the DSL."

**The technique: Foreign Code.** For those rare cases, handle them with a general-purpose
language using ***Foreign Code*** — **embed a small bit of a general-purpose language into the
DSL**. Crucially: "**This code isn't parsed by the DSL's parser; rather, it is just slurped as a
string and put into the *Semantic Model* for later processing.**" In the example, a JavaScript
regex test is embedded inside curly braces as a `when` clause on an otherwise ordinary rule.

**The tradeoff, stated plainly.** "This isn't as clear as extending the DSL would be, but this
mechanism can handle a wide range of cases. **Should regex matching become a common condition,
we can always extend the language later.**" (I.e., Foreign Code is the escape hatch for the long
tail; promote it into first-class syntax once it stops being a rare case.)

**Static vs dynamic host.** A **dynamic** language is useful for Foreign Code because you can
read and interpret the DSL script at runtime. You *can* use a static language, but then you must
use **code generation** and weave the host code into the generated code — a technique familiar
to Parser Generator users, "since this is how most Parser Generators work."

**Mixing DSLs, not just host code.** The same technique works with **another DSL** rather than
general-purpose code, allowing different DSLs for different aspects of your problem — which
"very much fits the philosophy of using several small DSLs rather than one larger DSL."
**However:** using multiple external DSLs together isn't easy with current technology; current
parser technologies aren't well suited to mixing different languages together with **modular
grammars**.

**Implementation issue.** You must **tokenize the Foreign Code differently** from how you scan
your main language, so you need some approach of ***Alternative Tokenization***. The simplest
approach is to **quote the embedded code inside clear delimiters** the tokenizer can spot and
slurp as a single string (curly brackets, above). Easy to grab the different text, but may add
some noise to the language.

**Alternative Tokenization is not only for Foreign Code.** Depending on parsing context, you may
want to interpret what would usually be a keyword as part of a name (`state initial state`).
Quoting can do the trick, but other implementations of Alternative Tokenization may involve less
syntactic noise.

**SDK relevance.** The "escape hatch, then promote" pattern is directly applicable to
configuration and policy APIs: provide a general-purpose expression/callback hook for the long
tail of rare requirements instead of growing dozens of narrow declarative options, and graduate
the common cases into first-class API once demand is proven.

---

## Section: XML DSLs

**Are configuration files DSLs?** Fowler distinguishes:
- **Property list** — a simple list of key/value pairs, perhaps organized into categories.
  There's not much syntactic structure — "none of that mysterious language nature that's key to
  something being a DSL." (Aside: XML is too noisy even for property lists; he prefers INI files
  for that.)
- **DSL** — many configuration files *do* have a language nature, and are thus DSLs. Done in
  XML, they are **external DSLs**.

**XML's status.** XML isn't a programming language; **it's a syntactic structure with no
semantics**. Therefore we process it by reading the code into tokens rather than interpreting it
for execution.
- **DOM processing is essentially *Tree Construction*.**
- **SAX processing leads to *Embedded Translation*.**

**Definition — carrier syntax.** "I think of XML as a **carrier syntax** for the DSL, in much the
same way that an internal DSL's host language provides a carrier syntax. (An internal DSL also
provides **carrier semantics**.)" — a useful distinction: XML gives you only syntax; a host
language gives you syntax *and* an execution model.

**Fowler's objection.** XML introduces **far too much syntactic noise** — angle brackets, quotes,
slashes; any nesting element needs both opening and closing tags. Too many characters are
expended on syntactic structure as opposed to real content, making it much harder to understand
what the code is trying to say — "which spoils the whole purpose of DSLs."

**The arguments in XML's favor, and his answers:**

1. **"Humans shouldn't write XML — special UIs should capture the information, and XML is just a
   human-readable serialization."** A reasonable argument, but it takes us out of DSL territory,
   with XML becoming a *serialization mechanism* rather than a language; a forms-and-fields UI is
   an **alternative to** using a DSL. Fowler notes he's seen "much talk of having a UI over XML,
   but not so much action," and: if you spend significant time looking at the XML (or diffs of
   it), the fact that you have a UI is incidental.
2. **"XML parsers exist off the shelf, so you don't need to write your own."** Fowler thinks this
   argument is flawed, "stemming from a confusion about what parsing is." **He defines parsing as
   the whole route from input text to the *Semantic Model*.** The XML parser only takes you part
   of the way — typically to a DOM; you still have to write code to traverse the DOM and do
   something useful. A Parser Generator can also produce a syntax tree (the equivalent of the
   DOM). His experience: **once you're moderately familiar with a Parser Generator, it takes no
   longer to use than XML parser tools.** Programmers are typically more familiar with XML
   parsing libraries, but the time cost of learning a Parser Generator "is a price worth paying."
3. **Consistency of quoting and escaping.** A genuine irritation with custom external DSLs is the
   inconsistency they breed around quoting and escaping (anyone who's worked with Unix config
   files appreciates this annoyance); XML provides a single scheme that works very solidly.
4. **Error handling and diagnostics.** XML processors usually do a good job here. You'll have to
   work harder to get good diagnostics with a typical custom language; how hard depends on how
   good your parser toolkit is. (Fowler notes he has generally skimmed over error handling and
   diagnostics in the book, but that shouldn't be a reason to ignore this point.)
5. **Schemas.** DTDs, XML Schema, Relax NG let you check the XML is reasonable **without
   executing it**, and support more intelligent tools. (He wrote the book in XML and welcomed
   Relax NG support in Emacs.)
6. **Binding interfaces** translate XML data into object fields. **Less useful for DSLs**,
   because "the structure of the Semantic Model will rarely match that of the DSL to allow
   binding XML elements to the Semantic Model." You may be able to use binding with a translation
   layer, but it's doubtful this buys much over walking an XML tree.
7. **Grammar vs. schema.** If you use a Parser Generator, the **grammar DSL can define many of
   the checks that an XML schema provides**. But **few tools can take advantage of a grammar**.
   We could write such tools ourselves, but the plus of XML is that they already exist.
   Generalized lesson: "**Often, an inferior but prevalent approach ends up being more useful
   than superior technologies.**"

**Verdict.** He concedes the points but still believes XML's syntactic noise is too much for a
DSL:

> "The key to a DSL is readability; tooling helps with writing, but it's the reading that really
> counts."

XML has virtues — it's really good at text markup — but as a DSL carrier syntax it imposes too
much noise.

**JSON and YAML.** Other carrier syntaxes that have gained traction as ways to textually encode
structured data, carrying much **less syntactic noise than XML**; Fowler likes them more.
**However**, "these languages are very much oriented towards structuring data, and as a result
lack the flexibility you need to have a truly fluent language."

> "A DSL is different from a data serialization, just like a fluent API is different from a
> command-query API. Fluency is important for a DSL to be easily readable, and a data
> serialization format makes too many compromises to work well in that context."

**SDK relevance.** This is the definitive statement of the parallel structure of the whole book:
**data serialization : DSL :: command-query API : fluent API.** The same judgement applies to
choosing between a YAML/JSON config schema and a purpose-built configuration language or fluent
config API — and the criterion is *reading*, not writing or tooling.

---

# Chapter 6: Choosing between Internal and External DSLs

(Fowler, DSL book, Ch. 6 "Choosing between Internal and External DSLs")

## Framing

Having covered the details of implementing both, we can better understand their strengths and
weaknesses — enough to decide which technique to use, "and indeed to decide if a DSL is
appropriate at all."

**Important epistemic caveat.** "One of the great difficulties is the lack of information to base
your choice on." Only a few people do much with DSLs, and those who do tend to use only one or
two techniques, so they can't really compare the different styles. Further complicated by many
of the book's techniques not being widely known. Fowler hopes the book will help people build
DSLs more easily, but until it's been out in the wild we can't tell what effect it has on these
decisions. **"So, my thoughts on this topic are more speculative than I would like."**

---

## Section: Learning Curve

**First-glance answer:** favors internal DSLs. An internal DSL "is really just a funky kind of
API," using facilities of a language you already know; an external DSL requires learning parsers,
grammars, and *Parser Generators*.

**But the picture is more nuanced:**

- There *is* a bunch of new concepts in *Syntax-Directed Translation*, and driving parsers with
  grammars can seem like magic. "It's not as bad as many people fear," but if you haven't worked
  with these tools, **work with trial examples first to become familiar with the tools before you
  make any estimates on doing the real work.**
- **The SDT learning curve is made worse by poor documentation** for most Parser Generator tools.
  What documentation exists tends to be **written for people working on general-purpose languages
  rather than DSLs**. "For many tools, the only documentation is a Ph.D. thesis. There's a crying
  need to do more to make Parser Generator tools accessible to those who want to use them for DSL
  work but don't have a background in the language community."
- **Escape route 1:** *Delimiter-Directed Translation* — much more familiar tools (breaking up
  strings, regular expressions, no grammars). There are limits to how far you can go with it, and
  "most of the time I think it's better to face the learning curve of Syntax-Directed
  Translation," but DDT is an option to keep in mind, **particularly for a regular language**.
- **Escape route 2:** an **XML carrier syntax** avoids the cost of learning SDT. Here Fowler
  thinks **learning SDT is worth the cost**, "as the resulting language is so much clearer to
  read."
- **The counterweight — internal DSLs aren't as easy as you'd think.** Although you're using a
  familiar language, you're using it in a very odd way. Internal DSLs often rely on **obscure
  tricks in the host language** to produce something fluent. Even if you know the language well,
  you may need to spend time finding the tricks available in your particular language. The book
  suggests what to look for, but you'll find language-specific tricks that aren't in it.
  Finding these and sorting out how to use them **presents a learning curve of its own**.
  - **The bright side (a real structural difference):** you can **mount that curve slowly**,
    learning new techniques as you develop the DSL. This contrasts with SDT, "where you have to
    learn much more just to get going." (Incremental vs. up-front learning cost.)

**Conclusion:** despite the difference being smaller than you might initially think, **internal
DSLs are easier to learn**.

**And remember who else pays:** "the learning curve... applies not just to you but to anyone who
wants to touch your code. Using an external DSL is likely to be less approachable for others who
don't want to put much effort into learning how to use it."

---

## Section: Cost of Building

- First time using any DSL technique, the **major cost is ascending the learning curve**. Once
  you're familiar, that cost goes away — but there is still some cost in providing a DSL.
- **Critical accounting separation:** "it's important to separate the cost of **building the
  model** from the cost of building the **DSL that layers over it**." Fowler takes the model as a
  given. "It's true that in many cases the model will be built in conjunction with the DSL, but
  **the model has its own justification**." (I.e., don't charge the model's cost to the DSL when
  making the DSL decision.)
- **Internal DSL extra cost:** creating a layer of *Expression Builders* over the model. The
  builders are relatively straightforward to write, but **most of the effort isn't in getting
  them to work — it's in fiddling with the language so that you have something that works well**.
  This cost won't appear if you put the fluent methods directly in the model, "but that may lead
  to other costs if people find these methods confusing compared to a command-query API."
- **External DSL equivalent cost:** building the parser. Once you're up to speed with SDT, "it's
  actually quite quick to write a grammar and the translation code." Fowler's current sense: the
  **cost of developing a parser is similar to that of building an Expression Builder layer**.
- Once familiar with SDT, it's **no harder than using an XML carrier syntax**, and **easier than
  using *Delimiter-Directed Translation* unless the language is quite simple**.

**Conclusion:** "once you are familiar with the techniques, there's no big difference in cost for
building an internal or external DSL."

---

## Section: Programmer Familiarity

- The usual argument — internal DSL users are working in a language they already know — is true
  "to some extent," but the difference is **not as marked as most people think**. The odd fluent
  interface style takes at least a little getting used to (though rather less than learning how
  to *build* it). An external DSL is also not hard to learn, "as it is, by definition, rather
  simple." **Echoing the syntactic conventions of your usual programming language can help make
  it more approachable** — a concrete design tip for external DSL syntax.
- **The biggest difference is tooling, not syntax.** If your host language has a sophisticated
  IDE, an internal DSL keeps that familiar tooling. You may need a more complicated technique
  like *Class Symbol Table* to preserve the tool's support, but that way you keep enjoying the
  IDE's strengths. With external DSLs, "you're unlikely to be offered anything but the most basic
  level of editing support"; you'll usually fall back to a regular text editor. **Syntax
  highlighting is not too difficult** (most text editors are very configurable in that regard),
  **but type-aware autocompletion is almost certainly beyond you.**

**SDK relevance.** Tooling is a first-class design constraint: an interface expressed in the host
language inherits the whole IDE (completion, refactoring, jump-to-definition, type errors), and
that inheritance is often worth more than syntactic elegance.

---

## Section: Communication with Domain Experts

- Internal DSLs are **always tied to the host language's syntax**, so there will almost always be
  some constraints on how you can express things plus some amount of syntactic noise. **Unlikely
  to be a big factor for programmer users** (who are used to these elements); **domain experts
  are a different matter.** The degree of constraint and noise depends on the language — "some
  languages are better suited to DSLs than others."
- "Even the best internal DSLs... don't offer the same syntactic flexibility as an external DSL.
  The size of the comfort gap will depend on particular domain experts, but such is the value of
  the communication channel that **I'd be inclined to push that bit harder and use an external
  DSL if it looks like it could make the difference.**"
- **Hedging strategy:** if you're not comfortable building an external DSL but unsure how an
  internal one will fly with domain experts, **try an internal DSL first and switch later** if
  worthwhile. "Since you can use the same *Semantic Model* for both, the incremental cost of
  building two DSLs isn't really that great." (The Semantic Model is the thing that makes the
  option cheap — a recurring theme.)

---

## Section: Mixing In the Host Language

**Framing.** "An internal DSL is really nothing more than a convention to use certain fluent
methods to do things. There's nothing to stop you from arbitrarily mixing DSLish code with
regular imperative code." This **wafer-thin boundary** between DSL and host language "has
properties that may be beneficial or problematic—depending on what you are trying to do."

**Benefits of the thin boundary:**
- You can use the host language freely when the internal DSL doesn't have constructs available.
  Need arithmetic? Don't build DSL constructs for it — just use host language features.
- Need to **build abstractions on top of the DSL**? Use the host language's abstraction
  facilities.
- Particularly nice when you need to put **chunks of imperative code inside your DSL**.

**The build-language case study (the chapter's best illustration).**
- Build languages use a ***Dependency Network***. **Make** and **Ant** are external DSLs and are
  both very good at expressing that Dependency Network.
- However, the **content** of many build tasks requires more complex logic, and often the
  **dependencies themselves need abstractions layered on top**. Ant therefore "suffered from
  **sliding into generality**, acquiring all manner of imperative constructs that don't suit its
  nature or syntax."
- Contrast: **Rake**, a Ruby internal DSL for building software. Freely mixing the Dependency
  Network with imperative code in ***Nested Closures*** makes it much easier to describe
  complicated build actions, and using Ruby's objects and methods to build abstractions on top of
  the Dependency Network helps describe the higher-level structure of the build.

**Mixing with an external DSL is possible but awkward.** You can embed host code into DSL scripts
as ***Foreign Code***, and you can embed DSLs into general-purpose code as strings — "which is
how we typically embed things like regular expressions and SQL today." But the mixing is awkward:
**tools usually don't know what you are doing and are clunky in how they work**, and **it's hard
to integrate symbols between the two environments**, so things like referring to a host code
variable within a DSL fragment become difficult.

> "If you want to intermix host and DSL code, then an internal DSL is almost always the way to go."

---

## Section: Strong Expressiveness Boundary

The mirror image of the previous section — the case where the thin boundary is a **liability**.

- Free mixing "only really works if the users of the DSL are comfortable with the host language."
  It doesn't usually apply where **domain experts** read your DSL: "throwing lumps of a host
  language into the DSL will usually only raise a communication barrier that the DSL was supposed
  to avoid."
- Intermixing is also unhelpful where you want DSLs to be **written by a different group of
  programmers**. "Indeed, often the benefit of a DSL is that **it produces a restricted range of
  what can be done.**" That restriction:
  - makes it easier to understand what to do, and
  - **serves as a barrier to bugs**;
  - with strong boundaries, **it limits the kinds of things you need to test for**. Fowler's
    example: "Pricing rules in a DSL aren't going to send arbitrary messages to your integration
    server or alter your order processing workflow."
- With a general-purpose language, anything is possible, "so you have to watch the boundaries
  through convention and review. An external DSL's limitations reduce what you have to watch for.
  Most of the time, this is good as it protects you from mistakes, **but it may also help with
  security.**"

**SDK relevance (high).** A clear articulation of *limitation as a feature*: a constrained
interface bounds the failure and attack surface, bounds the test matrix, and makes review
tractable. This is the standard argument for declarative/sandboxed extension points over
"just let them write code" plugin APIs — and it identifies exactly when it applies (untrusted or
non-programmer authors, cross-team authorship).

---

## Section: Runtime Configuration

- **Why XML DSLs became popular:** "they allow you to alter the execution context of the code
  from **compile time to runtime**." For situations where you're using a compiled language and
  want to alter the behavior of the system without recompiling, this is an important factor.
  External DSLs allow this since you can easily **parse them at runtime, translate into a
  *Semantic Model*, and then execute that model**. (If you're programming in an interpreted
  language everything is at runtime anyway, so this isn't an issue.)
- **Alternative approach:** use an interpreted language in conjunction with a compiled language,
  and write an internal DSL in the interpreted language. **But many of the common benefits of an
  internal DSL are attenuated in this scenario:**
  - unless most of the team is familiar with the dynamic language, you don't get the
    **language-familiarity** benefit;
  - **tooling** for the dynamic language is often poorer;
  - you **can't easily mix the dynamic language and static language constructs**;
  - and a **full dynamic language means you can't put firm boundaries around the DSL** (losing
    the Strong Expressiveness Boundary benefit).
- Not to say you shouldn't do this — there are plenty of cases where these issues don't apply.
  "But this attenuation does lead to more situations where an external DSL meshes better with a
  static host language."

---

## Section: Sliding into Generality

- **The cautionary tale: Ant.** One of the most successful DSLs of modern times — an external DSL
  in XML syntax for specifying Java builds. In a discussion about DSLs, **James Duncan Davidson,
  Ant's creator, asked: "How do we prevent disasters like Ant occurring?"**
- Ant is "both a roaring success and a nightmare." It filled a huge gap in Java development at the
  time, but its success forced many teams to face its flaws. There are many problems; the XML
  syntax is perhaps most noticeable (which Fowler also thought was a good idea at the time). "But
  the real issue behind Ant is that **over time it steadily grew in capability so that it no
  longer has the limited expressiveness that a DSL needs.**"
- **This is a general failure mode:** "This is a common road to heck." Unix people cite
  **Sendmail** as the example. "It happens because the demands placed on the DSL get steadily
  greater, leading to more features and greater complexity—and, drop by drop, all the clarity that
  a good DSL has leaks out."
- **No simple answer.** "This danger always exists with external DSLs and, like most issues in
  design, has no simple answer. It needs a constant attention and determination to not let things
  get too complex."
- **Alternatives to growing one language:**
  1. **Let other languages develop for more complicated cases.** Instead of extending one
     language, introduce other languages for particular and difficult cases.
  2. **Layer another language over the base DSL whose output is that base DSL.** "This can be a
     useful technique to allow abstractions to be built in a language that lacks
     abstraction-building features."
  3. **Switch to an internal DSL.** "Internal DSLs are often a good choice when this kind of
     complexity grows, because they allow you to mix DSL and general-purpose elements."
- **Internal DSLs don't suffer this problem** since they're already melded with a general-purpose
  host language. "An analogous problem may arise when mixing with the host language gets so
  intertwined that you lose any sense of DSLness." (I.e., the failure mode is symmetric but
  differently shaped: external DSLs bloat; internal DSLs dissolve.)

**SDK relevance (high).** The "sliding into generality" failure mode maps directly onto
configuration formats and plugin/policy APIs that accrete conditionals, loops, and variables
until they are a bad programming language. The prescriptions are equally applicable: keep the
declarative core small, add a *separate* layer or escape hatch for complexity, and treat
"features requested for the config format" as a signal to move up a layer rather than to extend.

---

## Section: Composing DSLs

- Recurring theme: you want **small DSLs that are very limited in their capabilities**. To get
  real work done you have to integrate your DSLs with one or more general-purpose languages. You
  can also **compose DSLs together**.
- **Internal:** "composing is as easy as mixing them with the host language. You can also use the
  host language's abstraction features to help make the composition work."
- **External:** composition is more difficult. To compose with *Syntax-Directed Translation*, you
  need to be able to **write independent grammars for different languages and yet compose the
  grammars together**. Most *Parser Generators* don't have facilities to handle this case —
  "another consequence of their focus on supporting general-purpose programming languages." As a
  result you must use ***Foreign Code*** to compose DSLs, "which is more clunky than it need be."
  (Some work was going on to provide tools supporting more composition, but currently rather
  immature.)

---

## Section: Summing Up

> "My conclusion is that there is no conclusion. I don't see a clear, general advantage for
> internal or external DSLs. I'm not even sure I see some general guidelines to pontificate."

The hope is that the preceding sections give you enough information to judge what suits your
particular situation.

**The one thing Fowler wants to stress:** *experimenting in both directions need not be as
expensive as you think.* "If you use a *Semantic Model*, it's relatively easy to layer on
multiple DSLs, both internal and external. This gives you lots of opportunity for
experimentation to find an approach that works well for you."

**Glenn Vanderburg's approach (endorsed):** use an **internal DSL early on, when you're still
trying to understand what you want to do with it** — that way you have easy access to facilities
from the host language and a more seamless environment to evolve in. Once things settle down and
there's a need for some of the advantages of an external DSL, **then build one**. "Again, a
Semantic Model makes this process much easier."

**A third option not yet covered:** a **language workbench** (deferred to a later chapter).

---

# Cross-cutting takeaways (my synthesis of Ch. 4–6)

1. **The Semantic Model is the load-bearing architectural decision of the whole book.** It is
   what makes parsers replaceable, DSLs testable, internal/external experimentation cheap,
   migration from one style to another affordable, and multiple front-ends over one core
   possible. Every "just try both and see" recommendation in Ch. 6 is licensed by it.
2. **Parsing layer as a hard seam.** Never let language-processing concerns (parsing data,
   context tracking, fluent naming, temporary state) bleed into the model. The concrete rule:
   never mix fluent and command-query methods on the same class.
3. **Style determines the rules.** Command-query and fluent interfaces have different naming
   rules, different side-effect rules (CQS applies to one, not the other), and different
   evaluation criteria. Deciding which style a surface is in must come *before* the detailed
   design.
4. **Syntactic uniformity beats local elegance** when non-experts read the code, because
   punctuation variety leaks implementation structure to the reader.
5. **The shape of the data dictates the call form.** Mandatory/optional/repeated/set maps onto
   nested calls / chaining / lists / maps, and each choice leaves a specific validation gap you
   must close in code.
6. **Strings are the enemy of tooling.** Represent DSL/API symbols as declared, typed things when
   you want IDE support — and be willing to accept some aesthetic oddity to get it.
7. **Limitation is a feature.** A restricted language bounds the bug surface, the test matrix,
   the review burden, and the security surface. The corresponding failure mode is *sliding into
   generality*, which requires continuous, deliberate resistance, plus an escape hatch (*Foreign
   Code*) so that rare cases don't force the core language to grow.
8. **Readability is the acceptance criterion.** "The key to a DSL is readability; tooling helps
   with writing, but it's the reading that really counts." This is what disqualifies XML, what
   distinguishes a DSL from a data serialization, and what distinguishes a fluent API from a
   command-query API.
