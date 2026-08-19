# Domain-Specific Languages (Fowler & Parsons, 2010) — Part IV: Internal DSL Topics, Chapters 39–46

Study notes covering the second half of Part IV's pattern catalog. Source PDF page boundaries
(rendered PDF pages, *not* print page numbers):

| Ch | Title | PDF pages |
|----|-------|-----------|
| 39 | Literal List | 289 (mid-page) – 289 |
| 40 | Literal Map | 289 (bottom) – 293 |
| 41 | Dynamic Reception | 293 (bottom) – 306 |
| 42 | Annotation | 306 – 312 |
| 43 | Parse Tree Manipulation | 312 – 320 |
| 44 | Class Symbol Table | 320 – 327 |
| 45 | Textual Polishing | 327 – 330 |
| 46 | Literal Extension | 330 – 332 |
| — | (Part V / Ch. 47 Adaptive Model begins) | 332 (bottom) |

All patterns follow Fowler's standard form: one-line intent, a sketch, "How It Works",
"When to Use It", then one or more worked examples. Code is deliberately not transcribed here;
each example is summarized for what it *demonstrates*.

---

## Chapter 39: Literal List

**Intent:** Represent a language expression with a literal list.
(Fowler, DSL book, Ch. 39 "Literal List")

### The concept

A Literal List is just the host language's built-in syntax for constructing a list/array
inline — Lisp's `(first second third)`, Ruby's `[first, second, third]`. As a DSL construct,
you use it to hold the children of some parent element, and a parent function then walks the
list and processes the elements. Because most such syntaxes nest, you can build tree-shaped
expressions out of them. Fowler notes that one way of looking at an entire Lisp program is as
a nested list.

### How it works

- The list is almost always **used inside a function call**; the function receives the list and
  interprets it. The list itself carries no semantics — the enclosing function supplies them.
- **Not all languages have a usable one.** Mainstream C-derived languages have literal arrays
  (`{1, 2, 3}`) but these frequently accept only constants/literals, not arbitrary symbols or
  expressions, which kills their usefulness for DSL work.
- **Varargs as a substitute.** A variadic function call — `companions(jo, saraJane, leela)` —
  is effectively a Literal List with the parent function baked into the syntax. In a strongly
  typed language all the elements must share a type to fit through a varargs parameter, which
  is a real constraint on heterogeneous DSL content.
  (Fowler, DSL book, Ch. 39 "Literal List", section "How It Works")

### When to use it

- Good when the list sits **nested inside another element**, typically a function call, and the
  grammar you want is essentially `parent ::= child*`.
- Often the items in the list are themselves function calls, which is exactly what makes
  **Nested Function** workable — Literal List and Nested Function are natural partners.
- **Prefer varargs over an explicit literal list when the list is an argument.** Fowler is
  explicit: even when the host language *has* literal list syntax, he prefers
  `companions(jo, saraJane, leela)` to `companions([jo, saraJane, leela])`. The brackets are
  pure noise when the function boundary already delimits the list.
- You *can* write an entire DSL using nothing but Literal Lists — that is essentially Lisp.
  Fowler's verdict: natural in Lisp, but "little more than a fun exercise in other languages
  where it's more natural to combine lists with other forms of expression."
  (Fowler, DSL book, Ch. 39 "Literal List", section "When to Use It")

### Relationships

- Pairs with **Nested Function** (the list elements are function calls).
- Degenerate/adjacent form of **Literal Map** — if you have lists but not maps, you can encode
  maps as lists of key/value sublists (see Ch. 40, Greenspun form).
- Contrast with **Method Chaining** and **Function Sequence** as alternative ways to express
  "a parent with many children".

### SDK relevance

The "prefer varargs to an explicit collection literal" rule is a durable API design heuristic:
when a parameter is conceptually "zero or more of X", a variadic signature reads better than
forcing callers to build a collection, *provided* the elements are homogeneous. The moment they
aren't, the type system pushes you toward an options object (Literal Map) instead.

---

## Chapter 40: Literal Map

**Intent:** Represent an expression as a literal map.
(Fowler, DSL book, Ch. 40 "Literal Map")

Sketch: a computer-configuration DSL where `processor(...)` and `disk(...)` each take a map of
named attributes (cores, type, size, speed, interface).

### The concept

A Literal Map is the host language's inline dictionary/hash/associative-array syntax. Used in a
DSL, it's the "named options" construct: a function takes a map and pulls named values out of
it. Where Literal List expresses "a sequence of children", Literal Map expresses "a set of
distinct named attributes, each appearing at most once."

### How it works

- Normally used in a function call where the function receives the map and processes it.
- **The central weakness is key validation.** In a dynamically typed language there is no way to
  communicate or enforce the valid set of keys. You must write the checking code yourself, *and*
  there is no mechanism to tell the DSL author which keys are correct — no discoverability.
  A statically typed language can dodge this by defining an enum of legal key types.
- **Keys should be symbols** where the language has them (or strings otherwise). Symbols are the
  natural choice and easy to process; some languages provide shorthand syntax (Ruby 1.9's
  `{cores: 2}` in place of `{:cores => 2}`).
- **Keyword arguments are a superior form of Literal Map.** Just as Fowler treats a varargs call
  as a form of Literal List, he treats a function call with keyword arguments as a form of
  Literal Map — and says keyword arguments are *better*, because they often let you declare the
  valid keywords. "Sadly, keyword arguments are even rarer than a literal map syntax."
- **Fallbacks when the language lacks map literals:** encode maps as literal lists — Lisp's
  `(processor (cores 2) (type i386))` — or use alternating key/value arguments,
  `processor("cores", 2, "type", "i386")`.
- **Delimiter elision.** Some languages (Ruby) let you drop the braces when the map is the only
  thing in that position, so `processor({:cores => 2, :type => :i386})` shortens to
  `processor(:cores => 2, :type => :i386)`. Worth exploiting — it removes a whole layer of
  punctuation noise.
  (Fowler, DSL book, Ch. 40 "Literal Map", section "How It Works")

### When to use it

- "Literal Map is a great choice when you need a list of different elements where each element
  should appear no more than once." The lack of key validation is annoying, but the syntax is
  usually still the best choice for this shape of problem: it *communicates clearly* that each
  subelement is at-most-once, and the map is the ideal structure for the receiving function.
- If you don't have Literal Maps, fall back to **Literal List**, **Nested Function**, or
  **Method Chaining**.
  (Fowler, DSL book, Ch. 40 "Literal Map", section "When to Use It")

### Example 1 — Computer configuration using lists and maps (Ruby)

Demonstrates that a good internal DSL **mixes techniques**: three functions (`computer`,
`processor`, `disk`); `computer` takes a Literal List (varargs of disks), the other two take
Literal Maps; the whole script is evaluated with **Object Scoping** (`instance_eval`) against a
builder instance, avoiding the need for a subclass.

The design lesson worth carrying away: because maps give you no key checking, the example adds a
`check_keys` helper that diffs the supplied keys against an explicit whitelist and raises a
dedicated exception naming the unrecognized keys. Without it, a typo silently does nothing.
Fowler frames this as unavoidable overhead: "The danger with using a map like this is that it's
easy for the caller to introduce an incorrect key by accident, so it's worth doing a little
checking here."
(Fowler, DSL book, Ch. 40 "Literal Map", section "The Computer Configuration Using Lists and Maps (Ruby)")

### Example 2 — Evolving to Greenspun form (Ruby)

Fowler pushes a single technique as far as it goes "just to get a sense of its capabilities" —
explicitly framed as an exercise, not a recommendation.

1. **Lists + maps only.** Replace every function call with a Literal List whose head element is a
   symbol naming the construct and whose tail is the arguments. The script becomes a pure nested
   data structure. It's processed by evaluating the host-language code to get the structure, then
   handing it to an interpreter written in the shape of a **Recursive Descent Parser**: check the
   head symbol, dispatch, recurse into children, validate argument keys.
   - Notable consequence: **you gain complete control over order of evaluation** of the language's
     elements, because nothing executes until your interpreter walks the structure. Fowler:
     "In many ways, this DSL script is like an external DSL encoded in internal literal collection
     syntax instead of a string."
2. **Lists only ("Greenspun form").** Replace each map with a list of two-element key/value
   sublists. (The name is a wink at Greenspun's Tenth Rule — he leaves working out why as an
   exercise for the reader.) Using only lists yields a *more regular* script, but a list of pairs
   masquerading as a map fits Ruby's style badly.
3. **Verdict:** "Either case isn't as good as the earlier example which mixed function calls with
   literal collections." The nested-list style is natural precisely in Lisp, where bare words are
   symbols by default and every expression is an atom or a list, so no commas are needed.
   (Fowler, DSL book, Ch. 40 "Literal Map", section "Evolving to Greenspun Form (Ruby)")

**Design principle extracted:** purity in one technique is a diagnostic exercise, not a goal.
Mixed-technique DSLs read better. When a construct starts fighting the host language's idiom
(list-of-pairs-as-map in Ruby), that friction is the signal to stop.

### Relationships

- Complement of **Literal List**; both are usually consumed by **Nested Function**.
- Alternatives when unavailable: **Nested Function**, **Method Chaining**.
- The full-list form leads directly into **Recursive Descent Parser** territory (an external-DSL
  pattern applied to an internal data structure).

### SDK relevance (high)

This is the **options-object / kwargs API** pattern, and Fowler's critique is exactly the modern
one:

- Options bags trade discoverability for expressiveness. Users cannot see the valid keys, IDEs
  cannot complete them, and typos fail silently.
- **Therefore: validate keys explicitly and fail loudly with a message that names the offending
  keys.** This is the single most actionable takeaway of the chapter for library authors.
- **Prefer real keyword parameters (or a typed options struct / TypedDict / enum-keyed map) to a
  free-form map** wherever the language offers them, because they restore the declared-valid-key
  property that a raw map throws away.
- Options maps are the right shape when the parameter set is "many distinct, independent,
  at-most-once named attributes" — the same rule of thumb applies to config objects today.

---

## Chapter 41: Dynamic Reception

**Intent:** Handle messages without defining them in the receiving class.
*Also known as:* Overriding `method_missing` / `doesNotUnderstand`.
(Fowler, DSL book, Ch. 41 "Dynamic Reception")

Sketch: `when_from("BOS")` arriving at a builder's `method_missing`, which checks whether the
name starts with `when_`, processes it if so, and throws otherwise.

### The concept

Every object has a finite set of defined methods. Statically typed languages catch calls to
undefined methods at compile time; dynamic languages fail at runtime. Dynamic Reception hijacks
that failure path: you override the language's "unknown message" hook so your object can respond
meaningfully to method names you never declared. In effect you are **dynamically altering the
rules for reception of method calls**.

### How it works

- The hook lives at the top of the object hierarchy: `doesNotUnderstand` in Smalltalk,
  `method_missing` in Ruby. You override it in your own class.
- **General (non-DSL) use case:** automatic delegation — define the methods you want to handle
  yourself, and route everything unknown to a delegate object.
- **DSL use case 1 — move parameters into the method name.** The canonical example is Rails
  Active Record's dynamic finders: `find_by_firstname("martin")`,
  `find_by_firstname_and_lastname("martin", "fowler")`. Active Record's superclass overrides
  `method_missing`, checks for the `find_by` prefix, parses the method name to extract property
  names, and builds a query. You *could* pass the names as arguments
  (`find_by("firstname", "martin", ...)`) but embedding them in the method name reads better —
  it mimics what an explicitly defined method would look like.
  - Conceptually: "Essentially, you are embedding an external DSL in the method name."
- **DSL use case 2 — a sequence of Dynamic Receptions.** Instead of one parsed name, chain them:
  `find_by.firstname("martin").and.lastname("fowler")`, or fully bare,
  `find_by.firstname.martin.and.lastname.fowler`. Here `find_by` returns an **Expression
  Builder** and you compose with **Method Chaining** plus Dynamic Reception.
- **Removing quotes.** A major payoff: parameters no longer need quoting — `martin` instead of
  `"martin"`. Combined with **Object Scoping**, you can accept bare symbols for arguments
  (`state idle` rather than `state :idle`) by implementing Dynamic Reception in the superclass so
  that after `state` is invoked, the *next* unknown method call is captured as the state name.
  **Textual Polishing** can strip yet more punctuation.
  (Fowler, DSL book, Ch. 41 "Dynamic Reception", section "How It Works")

### When to use it — the tradeoffs

This is one of the richest "when to use it" sections in Part IV. The judgement calls:

**Reasons it's appealing**

1. **It mimics real methods at a fraction of the effort.** It's entirely reasonable for a Person
   class to have a `find_by_firstname_and_lastname` method; Dynamic Reception provides it without
   your writing it. A significant time-saver when there are many combinations.
2. **Punctuation consistency.** `find.by.firstname.martin.and.lastname.fowler` uses only dots, so
   users never wonder when to use a dot vs. parentheses vs. quotes.
   - **But Fowler dissents on this one:** "For many others, this consistency isn't a virtue; I like
     separating what is schema from what is data, so I prefer the way
     `find_by.firstname("martin").and.lastname("fowler")` puts field names into method calls and
     the data into parameters." A genuinely useful distinction — *structure in the method names,
     values in the arguments*.

**Alternatives you should weigh first**

Attribute names as parameters (`find(:firstname, "martin", :lastname, "fowler")`); a closure
predicate; or a fragmentary external DSL in a string (`find("firstname == martin lastname ==
fowler")`). Fowler concedes that many people nonetheless find the method-name form most fluent.

**The governing rule**

> "Above all, it's important to remember that Dynamic Reception only pays its way when it allows
> you to build these structures in general, without any special case handling."

Corollaries he draws:

- It's only worthwhile when there is a **clear, mechanical translation** from the dynamic method
  name to methods that already exist for other purposes. `find_by_firstname_and_lastname` works
  precisely *because* `Person` genuinely has `firstname` and `lastname` attributes. Conditions
  are a good fit because they usually call attributes on domain model objects.
- **"If you need to write special methods to handle particular cases of Dynamic Reception, that
  usually means you shouldn't be using Dynamic Reception."** The moment you're special-casing,
  the generality that justified the magic has evaporated.

**The costs and hard limits**

- **Impossible in static languages** at all.
- **Debuggability.** "Once you override the handler for unknown method invocations, any mistake
  can lead you into deep debugging trouble. Stack traces often become impenetrable." This is the
  price you pay, and you should be sure the fluency gain is worth it.
- **Encoding limits.** Program text and string data often use different encodings; many languages
  allow only ASCII in identifiers, which breaks for non-ASCII personal names. Language grammar
  rules for method names may also exclude legitimate data values.
- **Expressiveness limits.** `find_by.age.greater_than.2` fails because most dynamic languages
  won't allow a digit there; the workaround (`...greater_than.n2`) "obstructs much of the fluency
  that you're doing it for."
- **Not for complex Boolean composition.** Fine for `find_by.firstname("martin").and.lastname("fowler")`,
  but by the time you reach
  `find_by.firstname.like("m*").and.age.greater_than(40).and.not.employer.like("thought*")`
  "you're running down a road that forces you to implement a kludgy parser in an environment not
  well-suited for it."

**The layering principle (a major, transferable idea)**

The complexity ceiling is *not* an argument against using Dynamic Reception for simple cases.
Active Record deliberately supports dynamic finders for simple cases and *deliberately does not*
support more complex expressions, pushing users to a different mechanism instead.

> "Some people don't like that, preferring a single mechanism, but I think it's good to realize
> that different solutions may work best at different complexities, so you should provide more
> than one."

(Fowler, DSL book, Ch. 41 "Dynamic Reception", section "When to Use It")

### Example 1 — Promotion points using parsed method names (Ruby)

Domain: itineraries of items (flights, hotels); promotions award points, e.g. 300 points for a
flight out of Boston. DSL forms shown: `builder.score(300).when_from("BOS")`;
several `score` lines for independent rules; `builder.score(140).when_from_and_airline("BOS","NW")`
for a compound rule.

Conceptually demonstrates:

- **Semantics of the two forms.** Two separate `score` lines = one promotion with two independent
  rules (either can match). One `when_from_and_airline` = one rule with two conditions (both must
  match). The DSL surface makes an AND/OR distinction legible.
- **The parsing pipeline.** `score` creates a rule (held in a **Context Variable**) and returns a
  condition builder. That builder's `method_missing` regex-matches the `when_` prefix, splits the
  remainder on `_and_` to get attribute names, **checks that the number of names matches the
  number of arguments** and throws a clear error otherwise, then constructs equality conditions.
  Note the arity check: with dynamic reception you must write your own signature validation.
- **Delegating unknown names upward.** If the prefix doesn't match, the handler calls `super`, so
  genuinely unknown methods still produce the language's normal error. This is essential hygiene:
  don't swallow every message.
- **The model is richer than the DSL surface.** "Using equality conditions in the method name like
  this is very limited. However, the underlying model allows me to have any kind of condition as
  long as it knows how to match an itinerary." Some conditions come in through the DSL; others
  through other means, e.g. a closure-backed condition object. "This kind of flexibility can be
  quite important. It allows people to use the DSL to handle simple cases simply, but provides an
  alternative mechanism to handle more complicated cases."
  (Fowler, DSL book, Ch. 41 "Dynamic Reception", section "Promotion Points Using Parsed Method Names (Ruby)")

### Example 2 — Promotion points using chaining (Ruby)

Same domain, expressed as `builder.score(300).when.from.equals.BOS` and
`builder.score(170).when.from.equals.BOS.and.nights.at.least._3`.

Demonstrates:

- **A little parse tree built from a chain.** Each condition has three parts — name, operator,
  value — so there is a builder per part plus a parent builder to tie conditions together. The
  name builder captures the attribute via Dynamic Reception and returns the operator builder; the
  value builder captures the value and tells the parent to populate the model.
- **Use Dynamic Reception only where the vocabulary is open.** The operator builder has a *fixed*
  set of operators, so it uses ordinary defined methods — no magic. Only the attribute-name and
  value builders, whose vocabularies are open-ended, need `method_missing`. This is the cleanest
  statement in the chapter of *how to keep magic proportional*.
- **Pure syntactic sugar is legitimate.** `at` in `nights.at.least._3` simply returns `self`; it
  exists only to make the expression readable.
- **The seams show.** Numbers can't start a method name, so `_3` is used with a parse trick to
  recover `3`. Fowler calls it "jiggery-pokery" and "the kind of smudge you need to make in order
  to pass a numeric parameter as a method name."
- **Two verdicts worth memorizing:**
  - "Making little parse trees like this isn't a common way to do an internal DSL; it's usually
    easier to just build the model up as you go. But with a conditional expression like this, it
    makes sense."
  - **"Overall, however, I'm not too keen on building up expressions using this approach. It seems
    to me that once you start parsing sequences of method calls like this, you might as well just
    switch to an external DSL where you get more flexibility. The desire to build up parse trees
    is a smell indicating that the internal DSL is doing too much work."**
  (Fowler, DSL book, Ch. 41 "Dynamic Reception", section "Promotion Points Using Chaining (Ruby)")

### Example 3 — Removing quoting in the secret panel controller (JRuby)

The book's running state-machine example. The plain internal-DSL version needs Ruby symbol
markers everywhere (`event :doorClosed, "D1CL"`, `state :idle do ... transitions :doorClosed => :active`).
Compared to an external DSL, the colons read as noise. With Dynamic Reception the script becomes
`events do doorClosed "D1CL" ... end` and `state.idle do actions.unlockDoor.lockPanel;
doorClosed.to.active end`.

Demonstrates:

- **Scoped Dynamic Reception via per-section builders.** `events`, `commands`, and `reset_events`
  each evaluate their block in the context of a *different, tiny* builder whose `method_missing`
  interprets every call as a declaration of that one kind. "By using a different builder, I can
  keep each one simple and clearly scope what each builder is recognizing." This is the key
  containment technique: narrow the window in which unknown methods are meaningful.
- **Two-stage evaluation to handle forward references.** State bodies are *not* evaluated when the
  state is declared; the closure is squirreled away in a map and processed in a postprocessing
  pass. "By deferring the evaluation till later, I can avoid worrying about the forward references
  between states" — all states are declared and the **Symbol Table** fully populated before any
  body referring to another state is run.
- **First-declared state becomes the start state**, via a variable populated only while still nil.
- **Mixing keyword-like methods with dynamic ones inside a body.** In the state body, `actions` is a
  real, declared method (analogous to a keyword in an external DSL) that returns a builder
  absorbing all subsequent calls as command names (allowing several actions chained on one line);
  transitions, by contrast, use Dynamic Reception (any unknown method = an event name), with `to`
  as sugar.
- **The honest cost/benefit verdict:** "By doing all of this, I can get rid of all the ':' on
  symbols. The question, of course, is whether it's worth the trouble. To my eye, I like the way
  the event and command list turn out, but I'm not so keen on the states." He recommends a hybrid —
  Dynamic Reception where it genuinely helps, plain symbol references where it doesn't:
  **"A mixture of techniques is often the best bet."** He also notes the quotes around event/command
  codes remain, and could be attacked the same way if desired.
  (Fowler, DSL book, Ch. 41 "Dynamic Reception", section "Removing Quoting in the Secret Panel Controller (JRuby)")

### Relationships

- Usually combined with **Expression Builder**, **Method Chaining**, **Object Scoping**,
  **Symbol Table**, **Context Variable**.
- **Textual Polishing** (Ch. 45) removes further punctuation once Dynamic Reception has removed
  the quoting.
- Its failure mode points at **external DSLs** / **Recursive Descent Parser**.

### SDK relevance (high)

This is the `method_missing` / `__getattr__` / JS `Proxy` / Python `__getattr__` dynamic-attribute
API pattern. Fowler's rules translate directly:

1. **Only use it when the mapping is fully general.** A dynamic accessor that requires special
   cases has already failed. If you're writing `if name == "foo": ...` inside your `__getattr__`,
   define `foo` properly.
2. **Always delegate unhandled names to the default error path** (`super`). Never let an unknown
   attribute silently return `None`/`nil`/a no-op builder.
3. **Budget for debuggability.** Impenetrable stack traces are the real, recurring cost. Weigh the
   fluency gain against every future user who has to debug through your hook.
4. **Scope the magic.** Per-section builders, each recognizing one open vocabulary, beat one
   god-object that answers to everything.
5. **Validate arity and shape yourself**, and produce an error message that names the method and
   what was expected — the compiler is no longer doing it for you.
6. **Layer the API deliberately (the Active Record lesson).** Provide a magic path for the simple
   80% and a distinct explicit mechanism (closures, a builder, a query object) for the complex
   20%. Do *not* stretch the magic path to cover everything; supporting more than one mechanism at
   different complexity levels is a feature, not an inconsistency.
7. **Data does not belong in identifiers** when it may be non-ASCII, contain digits, or otherwise
   violate identifier grammar. Keep schema in names, values in arguments.

---

## Chapter 42: Annotation

**Intent:** Data about program elements, such as classes and methods, which can be processed
during compilation or execution.
(Fowler, DSL book, Ch. 42 "Annotation")

Sketch: Java field declarations decorated with `@ValidRange(lower = 1, upper = 1000, units = Units.LB)`.

### The concept

We routinely classify data in our programs and write rules about the classifications. Sometimes
we want to classify *elements of the program itself*. Languages already provide some built-in
mechanisms for this — access controls like `public`/`private` mark methods. But we frequently want
to mark things beyond what a language supports, or reasonably *should* support: restrict the values
an integer field may take, mark methods to be run as part of testing, indicate that a class can
safely be serialized.

> "An Annotation is a piece of information about a program element. ... Annotations thus provide a
> mechanism to extend the programming language."

Terminology note: Fowler uses the Java term. .NET's equivalent syntax predates Java's, but .NET
calls them "attributes," a word too overloaded to reuse. Crucially, **the concept is broader than
any special syntax** — the same benefits are achievable without it.

In DSL terms: the annotation-defining syntax *is* an internal DSL, and it develops a **Semantic
Model** by attaching data to the runtime model of the program that's built into the language.
Later processing steps correspond to running the Semantic Model — which, as with any DSL, can mean
model execution or code generation.

### How it works

There are two largely independent topics: **defining** annotations and **processing** them. Their
independence matters — the same processing technique works for annotations defined in different
ways.

#### Defining an Annotation

Four techniques, in decreasing order of language support:

1. **Purpose-designed syntax.** Java's `@Test`, C#'s `[Test]`, both supporting parameters. Most
   obvious, and often the easiest.
2. **Class methods called in the class body** (the Ruby approach): `valid_range :height, 1..120`.
   The class method receives the name of the field plus the data and may either store the raw data
   (mirroring what built-in syntax does) or directly construct validator objects.
   - "Using class methods like this can be almost as easy as using purpose-designed syntax."
   - Biggest issue: the call must be given the **name of the element it annotates**, adding
     verbiage. But this also buys freedom: you can **separate the annotations from the annotated
     declarations**. "That is a big payoff for languages that make this easy — there's little need
     to provide a special annotation syntax."
   - Practical gotchas: the annotations must actually *execute* to be stored (Ruby runs class-body
     code at load time; other languages may need extra mechanics). The simplest storage is a class
     variable, but many languages share class variables between a class and its subclasses — benign
     in the book's example but a real hazard elsewhere. (The example accordingly keys a hash by
     class, and then shows the cleaner class-*instance*-variable form.)
   - Not OO-specific: you could define a Lisp structure tagging function names with data; the
     structure can live anywhere later processing can find it.
3. **Marker interface** (statically typed languages): an interface with no methods; implementing it
   tags the class. **Only works on classes**, not methods or fields.
4. **Naming conventions.** The simplest form of annotation — early xUnit implementations tagged test
   methods by requiring names begin with `test`. Works rather well for simple annotations, but
   "multiple annotations are difficult to support and parameters are practically impossible."

**A structural limitation unique to Annotations.** Beyond the usual internal-DSL limit (your syntax
is bounded by the host language's), annotations carry an additional one: the Semantic Model must be
based on the program's own fundamental representation. In an OO program that means classes, fields,
and methods; the annotation Semantic Model is a *decoration* of that structure. "You can't
practically build a completely separate and independent Semantic Model."
(Fowler, DSL book, Ch. 42 "Annotation", section "How It Works")

#### Processing Annotations

Annotations are written in source but consumed later — at compilation, at program load, or during
regular runtime.

- **Runtime processing is the most common case**: using the annotations to control some aspect of an
  object's behavior. Examples: an xUnit test runner finding and running test methods; a database
  mapper interrogating field annotations to discover the mapping to persistent storage.
- **Processing can be split across phases.** Validation annotations can be *partially* processed at
  program startup to create validator objects attached to classes, which are then used to validate
  objects during execution. (Cache the expensive reflection once; run the cheap check many times.)
- **Runtime processing ≈ model execution; the alternative is code generation.** In a dynamic
  language, code generation can happen at runtime — usually at load — either generating new classes
  or adding methods to existing ones.
- **Compiled languages** make runtime generation awkward (you can invoke the compiler and link
  dynamically, but it's fiddly). Options: compiler hooks for annotation processing (as Java has);
  generating code *before* compilation (but "such intimate intermixing of written and generated code
  can be confusing"); or **bytecode postprocessing** — let the compiler run, then manipulate the
  bytecode to add the generated steps.
- **One definition, many processors — the killer application.** In a web app you want field
  validations enforced in the browser (for responsiveness) *and* on the server (because you can never
  trust the browser). With Annotation you create a runtime check for the server and generate
  JavaScript for the browser without duplicating code: "Both checks can be fully derived from a
  single Annotation."
  (Fowler, DSL book, Ch. 42 "Annotation", section "Processing Annotations")

### When to use it

Fowler opens with unusual candour: "The wide-scale use of Annotations is still relatively new in
mainstream programming languages. We are still learning when best to use them."

**The key property:**

> "The key feature of Annotations is that they allow you to separate definition from processing."

The validation example makes the case concrete:

- The obvious way to enforce a valid range is inside the setter. But that **fuses the definition of
  the constraint with the moment it's enforced** — validation now necessarily happens on every value
  change.
- There are many cases where you want to check constraints at other times: letting a user fill in a
  form and only validating on submit. A whole-object `validate` method helps, but you're still
  defining the constraints in the same place they're checked.
- **Separating the two lets you:** check constraints at different times; apply *different subsets*
  of constraints at different times; and make the code clearer, because the constraint definitions
  stand alone rather than being tangled with the mechanics of running the checks.

**So the decision rule:** "The strength of Annotations lies where it makes sense to separate
definition and processing." Two motivations qualify — you want the *processing* to vary independently
of the definition, or you want the *definition* to be easier to understand by standing alone.

**The downside:** "it is more awkward to follow both definition and processing. If you need to
understand them together, Annotations force you to look in two disconnected places. The processing
code is also generic, which may make it even harder to follow."

**The corollary — a hard design rule for declarative APIs:**

> "the definition of an Annotation should be declarative and not involve any logic flow. Furthermore,
> it shouldn't imply any ties to when the processing logic occurs, or any ordering of processing
> Annotations attached to the same or different program elements."

(Fowler, DSL book, Ch. 42 "Annotation", section "When to Use It")

**Aside worth keeping** (from the Java example): having an object validate itself is not always the
right strategy. "When you validate something, you always do so for a context, and that context is
usually some action involving that object." Self-validation implies the validation is correct for
every context the code is used in — sometimes true, often not.

### Example 1 — Custom syntax with runtime processing (Java)

Field annotations with `@Target(FIELD)` and `@Retention(RUNTIME)`. Demonstrates:

- **Java annotation types are effectively objects with only fields, whose values must be literals or
  other annotations. Consequently all processing must live elsewhere.**
- A `ValidationProcessor` reflects over the target object's declared fields, reads their annotations,
  looks up a validator object per annotation type in a **dictionary**, and runs it.
- **The annotation-to-processor link is a dictionary lookup.** Alternatives Fowler names: if your
  language lets annotations contain code, the annotation could implement the check itself; or the
  annotation could carry the name of its validator class as a field. He rejects both for Java:
  "I generally prefer, at least in Java, to make annotations independent of the processing mechanism."
- **Performance:** most of the reflective setup only needs to run once, since annotations don't change
  at runtime — cache it, but only if you know it's a bottleneck.
  (Fowler, DSL book, Ch. 42 "Annotation", section "Custom Syntax with Runtime Processing (Java)")

### Example 2 — Using a class method (Ruby)

Same validation semantics with no custom syntax: `valid_range :height, 1..120` called in the class
body, executed at class load. Demonstrates the class-variable-keyed-by-class storage workaround and
then the cleaner class-instance-variable version. Validators are stored as closures taking the object.
(Fowler, DSL book, Ch. 42 "Annotation", section "Using a Class Method (Ruby)")

### Example 3 — Dynamic code generation (Ruby)

Extends the previous example so that, in addition to a whole-object `valid?`, each annotated field
automatically gets its own `valid_height?` / `valid_weight?` method, generated with `define_method`.

The critical observation: **"I don't need to modify the annotation calls in the patient visit class;
they can remain the same as the simpler case."** The user-facing declarative surface is unchanged
while the processing is upgraded underneath. It also guards with a `respond_to?` check so it never
clobbers an existing method, and stores validators as objects carrying the field name (rather than
bare closures) so validators can be selected per field.
(Fowler, DSL book, Ch. 42 "Annotation", section "Dynamic Code Generation (Ruby)")

### Relationships

- Builds a **Semantic Model** (constrained to decorate the language's own program model).
- Alternative to **explicit registration** / imperative configuration calls.
- Related to **Symbol Table** (annotation → processor dictionaries), **code generation** patterns.

### SDK relevance (very high)

This chapter is essentially a design brief for **declarative metadata APIs** — decorators, attributes,
schema classes, `@Test`/`@Deprecated`, ORM field descriptors, serialization tags, validation
decorators, DI annotations.

- **When Annotation beats explicit registration:** when definition and processing genuinely want to
  vary independently, or when you want the declaration to be readable in isolation, sitting right
  next to the thing it describes. Explicit registration wins when the reader needs to see *what
  happens* and *when* in one place.
- **Design rule for any decorator/attribute you ship: it must be purely declarative.** No control
  flow, no ordering dependencies between annotations, no implied coupling to when processing runs.
  The moment your decorator's behavior depends on declaration order relative to another decorator,
  you have built a trap.
- **Decouple the annotation from its processor.** Keep the annotation as inert data; put the behavior
  in a processor selected via a registry/dictionary. This is what makes multiple processors possible.
- **The multi-target payoff is the strongest argument for a declarative API**: one declaration,
  N processors (server-side check + generated client-side check; runtime validation + generated
  docs; runtime schema + generated migrations). No duplication, no drift.
- **You don't need language-level annotation syntax.** Class-body DSL calls, naming conventions, and
  marker interfaces all count, with a known cost: conventions can't carry parameters or stack;
  marker interfaces only tag types.
- **Accept the discoverability cost honestly:** the reader must now look in two places. Mitigate with
  good docs and good error messages from the generic processing code, which is otherwise the hardest
  part of the system to follow.
- **Self-validation is context-blind.** Validation belongs to an action/context, not intrinsically to
  an object — relevant to any API that offers `obj.validate()`.

---

## Chapter 43: Parse Tree Manipulation

**Intent:** Capture the parse tree of a code fragment to manipulate it with DSL processing code.
(Fowler, DSL book, Ch. 43 "Parse Tree Manipulation")

Sketch: a C# lambda passed to a builder; the builder reaches `Lambda.Body` to get a C# syntax tree,
walks it, and populates a semantic model.

### The concept

When you write code in a closure, that code is available to be *executed* later. Parse Tree
Manipulation goes further: it lets you **examine and modify the code's structure**, not merely run
it. The host language's own expressions become input data to your DSL processor.

### How it works

- You need an environment that can turn a code fragment into a workable parse tree. "This is a
  relatively rare programming language feature — rare both in that few languages support it and in
  that, even when it is supported, it's rarely used."
- Three exemplars: **C# (from 3.0)**, **Ruby's ParseTree library**, and **Lisp**.
- **C# and ParseTree work similarly:** you invoke a library call on a source fragment and get back a
  data structure representing its parse tree.
  - C#: only works on an **expression inside a lambda** — so you cannot capture multi-statement code.
    Returns a hierarchy of purpose-built expression objects with an inheritance hierarchy for
    different operator kinds.
  - ParseTree: can take a class, a method, or a string of Ruby code. Returns nested Ruby arrays with
    simple built-in types (symbols, strings) as leaves.
  - In both you write a **tree walker**. C#'s tree is immutable, but you can transform by copying and
    modifying as you copy. Both libraries can turn a subtree back into executable code.
- **Lisp is categorically different:** Lisp source *is* essentially a serialized parse tree of nested
  lists, and syntactic macros let you examine and manipulate any expression. Different style, much
  the same effects.
- **You can't accept arbitrary host-language expressions.** There are always limits on what your
  walker can handle. "In these situations, it's important to fail fast should you get an expression
  that you can't handle." Normally when walking a parse tree you know the node shapes conform to
  expectations; here the tree can contain *any* legal host construct, so **all the checking is your
  responsibility**.
- **Walk only what you must.** "Usually you won't need, or want, to walk the entire parse tree." Walk
  the parts you need to populate your **Semantic Model** and hand the remaining subtrees back to the
  language to evaluate as soon as you no longer need to navigate them. This keeps you from
  reimplementing a whole parser.
  (Fowler, DSL book, Ch. 43 "Parse Tree Manipulation", section "How It Works")

### When to use it

- The driving reason: **you want to use a fuller range of the host language's features to express
  something, "instead of the pidgin of the usual internal DSL constructs."**
- Fowler is careful to distinguish this from the general internal-DSL benefit: you can always
  intermix full host language with DSLish constructs. "The key difference is that usually, you can
  only manipulate the executable **results** of the host language — you can't dive into host language
  expressions and manipulate their structure."
- **Not many DSL use cases exist.** The best is **Linq**, the driving force behind .NET's support.
  Linq expresses query conditions as ordinary .NET Boolean expressions. Evaluating them against .NET
  data structures is trivial; the interesting part is turning a C# condition into a **SQL query** —
  writing DB queries without knowing SQL, or writing one query executed against different data
  sources. That requires parsing the C# condition into a tree, walking it, and emitting SQL:
  essentially **source-to-source translation**. "Parse Tree Manipulation is good for these cases, as
  it allows you to use a familiar syntax for your conditions when your target language is not well
  known or you want multiple targets."
- Another use: **modify** the tree to perform surgery, e.g. redirect all method calls on one object to
  another. "But it's not clear how useful that kind of surgery is in a DSL context."
- **The warning (this is the real point of the chapter):**
  > "I also worry a bit that Parse Tree Manipulation is one of those techniques where the intricacies
  > of doing it may be just too appealing for many programmers. It's an appeal that can blindside
  > people into missing other, simpler ways of achieving the same goal."
  (Fowler, DSL book, Ch. 43 "Parse Tree Manipulation", section "When to Use It")

### Example — Generating IMAP queries from C# conditions (C#)

Domain: IMAP keeps mail on the server, so searching must happen server-side; the search request is a
string in IMAP's own little query language. Goal: let a C# programmer write the query as a lambda
over a criteria object and translate it to IMAP.

Conceptually demonstrates:

- **A Semantic Model independent of the input syntax:** a query object holding a list of elements,
  with a basic element (keyword + value) and a negation element, each able to render itself to IMAP.
  Validation (legal keywords, correct value types) lives in the model and accumulates errors in a
  Notification before throwing.
- **A "phantom" receiver object.** To write `q.Subject == "..."` you need an object exposing Subject,
  To, Sent, From. Fowler is explicit that "this object won't ever do anything at runtime; it's only
  there to provide the methods to help me compose the query. As a result, the return values of its
  methods are irrelevant as they'll never actually be called." The object exists purely so the
  compiler will accept — and the IDE will complete — the expression that you intend to inspect
  rather than execute. (A striking API idea in its own right: a type whose only purpose is to shape
  a tree you will later read.)
- **The honest admission about expressiveness:**
  > "despite my desire to allow clients to construct IMAP queries in C#, they can't use *any* C#."
  The model handles only a subset: elements joined by `&&`; each element a binary operator with a
  keyword on one side; string keywords only accept `==` and `!=`; date keywords accept any equality
  or comparison operator. The walker throws on anything else — fail fast, as the pattern requires.
- **Validate at construction to simplify extraction.** The element builder asserts node validity in
  its constructor (one child is a keyword; the operator is legal for that keyword's type), so the
  later logic that pulls data out of the node can stay simple. Keyword and value may appear on
  either side, since commutativity is what a host-language reader expects.
- **Don't parse what you can evaluate.** For the *value* side of each comparison, he does not walk
  the node at all — he compiles and invokes that subexpression through the C# runtime. "This allows
  me to put any legal C# into the value side of my elements without having to deal with it in my
  navigation code." This is the "walk only what you need" principle in its purest form, and it's the
  main reason the example stays tractable.
- **Impedance mismatch between host expression and target language.** `q.Sent >= aDate` must become
  IMAP's `sentsince aDate`; some operators require introducing negations. So the correct IMAP keyword
  depends jointly on the keyword method *and* the operator, and the C# date keywords must be checked
  in the *builder* because they belong to the input DSL but not to the Semantic Model. He removes
  duplication with a prefix trick and notes: "The code's a little cleverer than I like, but I think
  it's worth that to avoid duplication."

**"Stepping Back" — two meta-lessons (both important beyond this chapter):**

1. **Explanation order ≠ construction order.** He explains the example one aspect at a time
   (populating the model, generating IMAP, walking the tree) because that's easier to understand and
   is why the code is separated that way. But he built it feature by feature: first simple
   conjunctions, then negations, refactoring each section as he went. "I always advocate building
   software like this, feature by feature, but I don't think that's the best way to explain the final
   result. So don't let the structure of the final result and the way I explain it fool you into
   thinking that it is how it's built."
2. **He wouldn't actually build it this way.** "although walking a parse tree like this yields that
   geeky pleasure of using fancy parts of a language, I wouldn't actually build an IMAP DSL this
   way." The alternative is plain **Method Chaining**:
   `new ChainingBuilder().subject("entity framework").not.from("@thoughtworks.com").since(threshold)` —
   whose entire implementation is a handful of small methods (plus one slightly messy **Context
   Variable** for the negation flag). His diagnosis of *why* it's simpler is the transferable insight:
   > "One of the main reasons this is so much simpler is that the structure of the internal DSL is
   > more similar to the IMAP query itself. In fact, it's really just the IMAP query expressed as
   > Method Chaining. Its advantage over using IMAP itself boils down to IDE support. Some people
   > might prefer the more C#ish syntax that the Parse Tree Manipulation example gives you, but I
   > must admit I'm happier with the IMAPish version."
   (Fowler, DSL book, Ch. 43 "Parse Tree Manipulation", sections "Generating IMAP Queries from C# Conditions (C#)" and "Stepping Back")

### Relationships

- Populates a **Semantic Model**, like every other DSL pattern here.
- Its main competitor for the same problems is plain **Method Chaining** (+ **Expression Builder**,
  **Context Variable**).
- Lisp macros are the same idea by another route; **Macro** is a related pattern.

### SDK relevance

- This is the pattern behind **LINQ-to-SQL, Django/SQLAlchemy expression translation, and any API
  that inspects a lambda instead of calling it** (e.g. `.filter(x => x.Age > 40)` compiled to a
  remote query). Fowler's constraints all apply: your API accepts only a *subset* of the host
  language, so you must fail loudly and specifically on anything outside it — a silent
  mistranslation is far worse than an exception.
- **Design the surface to mirror the target, not the host.** The IMAP verdict is the lesson: an API
  shaped like the domain/target language ended up simpler and, in Fowler's judgement, better than one
  shaped like the fanciest available host-language feature. The only genuine advantage of the fancy
  version was IDE support.
- **"Evaluate what you don't need to inspect."** When building an expression-inspecting API, define a
  clear boundary: structure you interpret vs. sub-expressions you hand back to the language. It
  massively shrinks what you have to support.
- **Beware technique-attraction.** Fowler's warning that intricacy is seductive and "can blindside
  people into missing other, simpler ways of achieving the same goal" is the general antidote to
  clever-trick API design.

---

## Chapter 44: Class Symbol Table

**Intent:** Use a class and its fields to implement a symbol table in order to support type-aware
autocompletion in a statically typed language.
(Fowler, DSL book, Ch. 44 "Class Symbol Table")

Sketch: a Java class extending a state-machine builder, declaring `Events switchUp, switchDown;`
and `States on, off;` as fields, with the DSL script in a `defineStateMachine()` method that uses
those fields as first-class symbols.

### The concept

Modern IDEs offer **type-aware autocompletion**: type a variable name, a dot, and get the list of
methods on that object. Fowler — a self-declared enthusiast for dynamic languages — concedes this is
a genuine benefit of static typing. In an internal DSL you don't want to lose it when *typing the
name of a symbol* in your language. But the usual ways of expressing DSL symbols are strings or a
built-in symbol type, which carry no type information at all, so the IDE can offer nothing.

Class Symbol Table makes the DSL's symbols **statically typed host-language entities** by declaring
each symbol as a **field in an Expression Builder**. The field name is the symbol name; the field's
declared type tells the IDE and compiler what that symbol can do.

### How it works

- **Put the DSL script inside a single Expression Builder class**, usually a subclass of a more
  general Expression Builder that carries the behavior needed by all scripts. The script's class then
  consists of a method holding the script itself plus fields declaring the symbols, e.g.
  `Tasks drinkCoffee, makeCoffee, wash;`
- **Naming conventions get bent for readability.** A class named `Tasks` (plural) is unconventional;
  "the readability of the DSL is trumping my usual code style rules." He restates this later: any OO
  style book will tell you to avoid plural class names and he agrees — "However, here a plural name
  reads better in the context of the DSL, so this is another case of general coding rules being
  broken to make a good DSL script." (He still refers to it as a *builder of events* in prose, since
  the naming doesn't change what it is.)
- **The runtime gap.** Declaring fields is not enough. When the script refers to a field, at runtime
  it refers to the **contents** of the field, not the field *definition*. The IDE knows about both
  while you write; the link to the declaration disappears when the program runs. So you must
  **populate every field with a suitable object before the script executes.**
- **The population mechanism.** A good approach is to make the class instance the active script: code
  in the constructor (or a build method) populates the fields, and the script lives in an instance
  method. The field contents are usually **small Expression Builders** that link to the underlying
  Semantic Model object *and* also carry the field name, to help with cross-referencing. In
  **Symbol Table** terms the field name is the key and the builder is the value — but occasionally
  you need lookup by name too, which is why the builders keep their own name.
- **Reflection is the price.** The script refers to fields by the field literal itself — that's the
  whole point. But while processing you need the builders in those fields to refer to *each other*,
  which means looking up fields by name or iterating all fields of a given type. "Doing this will
  require some more tricky code, usually using reflection. Usually there's not too much of it and,
  provided it's well encapsulated, it shouldn't make the language too difficult to process."
  (Fowler, DSL book, Ch. 44 "Class Symbol Table", section "How It Works")

### When to use it

- **The benefit:** full static typing of all the DSL's language elements. That unlocks all the
  IDE machinery built on static types — above all type-aware autocompletion — plus compile-time type
  checking of the DSL script, "which matters a lot to many people (but rather less to me)."
- **The scope limit:** "With such a focus on IDE capabilities, I see this technique as much less
  useful if you don't have an IDE that takes advantage of static types. It also does not bring much
  benefit in a dynamically typed language."
- **The cost:** "you have to bend your DSL significantly to fit within the type system. The resulting
  builder classes look very odd; also, you have to put your DSL scripts in a place where they can
  take advantage of these facilities, such as all in the same class. These restrictions may make the
  DSL harder to read and use."
- **The tradeoff statement:** "So for me, the fundamental tradeoff is between the restrictions on the
  DSL script and the benefits of the IDE support. I've got rather dependent on good IDE support in
  languages where it's available, which would prompt me to use techniques like this to get it."
- **Cheaper alternative:** "If you want this kind of static type support, you can often get what you
  need by using **enums as symbols**" (see the Symbol Table pattern).
  (Fowler, DSL book, Ch. 44 "Class Symbol Table", section "When to Use It")

### Example — Statically typed Class Symbol Table (Java)

The secret-panel state machine, written as a class whose fields are the events, commands, states, and
reset events, with the script in an overridden `defineStateMachine()` method.

Conceptually demonstrates:

- **Three distinct execution stages**, orchestrated by the superclass's `build()`:
  1. **initializeIdentifiers** (generic) — populate the symbol fields;
  2. **run the DSL script** (specific — an abstract method the subclass implements);
  3. **produceStateMachine** (generic) — walk the populated builders and emit the Semantic Model.
- **Generic field initialization via reflection.** The superclass is handed the list of identifier
  classes; it iterates the script object's declared fields and, when a field's type matches, builds
  the right identifier (name + back-reference to the builder) and assigns it. Fowler's candid note:
  "Doing it this way is more tricky than I'd like, as I want to write generic code for setting up the
  identifiers to avoid duplicating setup code. However, any generic code doesn't know about the
  specific type of the identifier being set up, and so has to determine it dynamically."
- **A small identifier class hierarchy** — a base `Identifier` carrying the responsibilities common to
  all identifiers (name, builder back-reference) with subclasses carrying type-specific behavior.
  Events and Commands are "degenerately simple Expression Builders" (a `code("D1CL")` call is enough
  to create the model object); States is a fuller builder needing several steps.
- **Intermediate builders decouple declaration order.** `actions(Commands... identifiers)` stores the
  *command builders* in the state builder rather than immediately storing the model command objects.
  If the script always defined codes before states you could skip this — "However, this would lead to
  errors if I define a state before its action codes. Using the builder as an intermediate object
  allows me to work it either way." (Same motivation as the deferred-closure trick in Ch. 41.)
- **Responsibility-preserving notification.** The DSL treats the first-mentioned state as the start
  state. Only the machine builder can know which state is first, so the state builder simply notifies
  it ("I'm being defined") without knowing what will be done with that fact.
  > "So I make what is effectively an event notification call from the state builder (since that is
  > all it knows) and let the machine builder decide what to do on that event. This is a good example
  > of naming being important in communicating what I think the responsibilities and relative
  > knowledge of the objects should be."
- **Only script-visible types pay the readability tax.** The transition builder's type never appears
  in the DSL script, "so I can give it a more meaningful name." I.e. bend naming rules *only* for the
  types the DSL author actually writes.
- **Reflection again at the end** to collect all fields of each builder type and get them to produce
  their wired-up model objects.
- **Closing verdict:** "Using a class and its fields as a symbol table does involve a bit of tricky
  code in places, but the benefit is full static typing and IDE support. That's usually a worthwhile
  tradeoff."
  (Fowler, DSL book, Ch. 44 "Class Symbol Table", section "Statically Typed Class Symbol Table (Java)")

### Relationships

- A specialization of **Symbol Table** (field name = key, builder = value).
- Requires **Expression Builder**; often combined with **Object Scoping** (subclassing the builder).
- Alternative, cheaper implementations of the same goal: **enums as symbols**.

### SDK relevance

- The general technique: **turn stringly-typed identifiers into typed program elements** so tooling
  can see them. Every modern equivalent — enums instead of string constants, typed key objects,
  literal-union types, generated client stubs, typed schema classes — is the same trade: you accept
  more ceremony in the declaration in exchange for autocompletion, compile-time checking, rename
  refactoring, and go-to-definition.
- **Explicit statement of the tradeoff to reuse:** restrictions on how users must write their script
  vs. the tooling benefits. If your users have no IDE that exploits static types (or the language is
  dynamic), the benefits mostly evaporate and the restrictions remain — don't pay the cost.
- **Reach for the cheap version first** (enums / literal unions) before contorting the API into a
  class-with-fields shape.
- **Confine ugliness to the implementation.** The reflective initialization is acknowledged as ugly;
  what matters is that it's encapsulated in the framework superclass, not imposed on the user's
  script. That's the right place to absorb complexity in any library.
- **Naming rules are subordinate to the reader of the DSL — but only where the reader sees them.**
  A useful, precise version of "readability first": break the convention on the plural type name the
  user types; keep normal conventions on the types they never see.

---

## Chapter 45: Textual Polishing

**Intent:** Perform simple textual substitutions before more serious processing.
(Fowler, DSL book, Ch. 45 "Textual Polishing")

Sketch: `3 hours ago` → `3.hours.ago`

### The concept

Internal DSLs are often easier to develop — especially if you're not comfortable writing parsers —
but the result is littered with host-language artifacts (dots, colons, parentheses, quotes) that
nonprogrammers find awkward to read. Textual Polishing runs a series of simple **regular expression
substitutions** over the script *before* it reaches the parser/evaluator, converting a
domain-expert-friendly surface into a valid internal-DSL expression.

### How it works

- A sequence of regex substitutions on the DSL script text. `3 hours ago` → `3.hours.ago`;
  `3%` → `percentage(3)`. **The output of the polishing is an expression in an internal DSL** —
  polishing does not produce a model, it produces host-language code.
- Specification is easy (most environments support regexes); correctness is not. "The tricky thing,
  of course, is getting the regular expressions correct so you don't get unwanted substitutions. A
  space in a quoted string probably should not be turned into a dot, but that makes the regex much
  harder to write."
- **Most natural in dynamic languages**, where the polished text can be evaluated at runtime: read the
  script, polish it, evaluate the result. Possible in static languages too, by polishing before
  compiling — "which does introduce another step into the build process."
- **Occasionally useful for external DSLs**: when something is hard to spot with the usual
  lexer/parser chain, a polishing preprocess before lexing can help — **semantic indentation** and
  possibly semantic newlines are the examples given.
- Conceptually: "You can think of Textual Polishing as a simple application of textual **Macros**,
  with all the corresponding problems."
  (Fowler, DSL book, Ch. 45 "Textual Polishing", section "How It Works")

### When to use it

This is the most sceptical "when to use it" in the group. Fowler essentially argues himself out of the
pattern:

- > "I confess I'm rather wary of Textual Polishing; my feeling is that if you use a little, it
  > doesn't help much, and if you use a lot, it gets very complicated, so it may then be better to use
  > an external DSL."
  Repeated substitutions are simple in concept, but "it's very easy to make mistakes in the regular
  expressions."
- **The hard structural limit:** "Textual Polishing cannot do anything to change the syntactic
  structure of the input, so you are still tied to the basic syntactic structure of the host
  language." You can only re-skin, not re-shape.
- **Keep the two forms recognizably similar.** "I think it's important to keep the prepolished DSL and
  the resulting internal DSL expressions recognizably similar. The resulting internal DSL should be as
  clear as possible for programmers to read — the polishing is only a visual convenience for
  nonprogrammers." If a reader can't map the polished text onto the underlying calls, debugging
  becomes guesswork.
- **A cheaper alternative: fix it in the editor, not the language.** "If you find the noise characters
  in an internal DSL annoying, an alternative approach to Textual Polishing is to use an editor that
  supports syntax coloring and set it up to color the noise characters with a very gentle color that
  fades into the background. That way, a reader's eye is more likely to skip over them. If you set it
  to the same color as the background, you make these characters disappear completely." (An
  excellent instance of solving a readability problem in tooling rather than in the language.)
- **Escalation rule:** "If you find yourself doing a lot of polishing, I strongly suggest that you
  explore using an external DSL instead. Once you get up the learning curve of writing a parser,
  you'll get much more flexibility, and it will be easier to maintain the parser than the sequence of
  polishing steps."
  (Fowler, DSL book, Ch. 45 "Textual Polishing", section "When to Use It")

### Example — Polished discount rules (Ruby)

Target internal DSL: a discount builder producing "3% off if the order's value is over $30,000."

Demonstrates, in order of increasing intervention:

1. **Object Scoping removes noise for free.** Putting the rules in their own file and `instance_eval`-ing
   each line drops the receiver prefix. Additionally, the **Method Chaining finishing call (`content`)
   is moved into the processing code**, out of the user-visible DSL — a nice, general trick: terminator
   calls are an implementation detail and users shouldn't have to type them. (A `has_rule?` guard is
   needed because comment lines produce no rule.)
2. **Then polishing for the domain expert's preferred phrasing** `3% if value at least $30000`:
   - `3%` → `percent(3)`
   - `value at least $30000` → `minimum(30000)`
   - `if` → `when` — needed because `if` is a Ruby keyword. Fowler offers the alternative:
     **rename the DSL method to `my_if` or `_if`** instead, since "doing this makes it easier to see
     the correspondence between the polished text and the resulting DSL." (I.e. adjust the internal
     DSL's vocabulary to shorten the distance the polishing must travel.)
   - finally, spaces → dots, yielding valid Ruby.
3. **Tokenization discipline.** Because elements are whitespace-separated, as when tokenizing an
   external DSL, "it's valuable to ensure that all of the regexes have boundary expressions at both
   ends" — usually `\b`, occasionally something else (`\s+`, since `%` isn't a word boundary).
4. **Closing verdict:** "This doesn't look too bad, but the code is only enough to process this one
   particular example. To handle more cases, the code will have to get more complex and much more
   ugly. So in this case, I'd be keeping a careful eye on it, ready to reach for an external DSL to
   use instead."
   (Fowler, DSL book, Ch. 45 "Textual Polishing", section "Polished Discount Rules (Ruby)")

### Relationships

- A degenerate form of **Macro**, with macro-like hazards.
- Frequently paired with **Object Scoping** (which removes noise without any substitution at all —
  always try this first).
- Its escalation path is an **external DSL** with a real parser.

### SDK relevance

Mostly a cautionary pattern, but with transferable lessons:

- **Prefer structural fixes to textual ones.** Object Scoping and renaming a method (`when` → `_if`)
  achieved much of the goal with none of the regex risk. Reach for the language-level fix before the
  string-rewriting fix.
- **Hide terminator/finisher calls from users** where you can — move `.content()`/`.build()` into the
  harness rather than requiring every user line to end with it.
- **Don't let the user-facing surface and the underlying calls diverge**, or you destroy every error
  message, stack trace, and debugging session downstream. This is exactly the problem with heavy
  source rewriting, transpilation, and macro-based APIs generally.
- **Solve cosmetic complaints with tooling** (syntax highlighting/formatting) rather than by adding a
  translation layer.

---

## Chapter 46: Literal Extension

**Intent:** Add methods to program literals.
(Fowler, DSL book, Ch. 46 "Literal Extension")

Sketch: `42.grams.flour`

### The concept

Literals — numbers and strings — often make a natural *starting point* for DSL expressions
(`42.grams`, `3.days.ago`). Traditionally they're built-in types with fixed interfaces so you can't
extend them, but more languages now allow adding methods to third-party classes: C#'s **extension
methods**, Ruby's **open classes**. (Smalltalk always allowed it.) For DSLs this is particularly handy
because it lets you **start a method chain with a literal**.

### How it works

- As with most method chains, a key decision is **whether to use an Expression Builder**. Without one,
  every intermediate type in the chain must itself carry the appropriate fluent methods. With one, you
  avoid that, but you must ensure you can cleanly get from the builder back to the underlying object.
- **What should `42.grams` return?** Three options, each with distinct consequences:

  1. **A number.** Pick a canonical unit (e.g. kilograms), so `42.grams` → 0.042 and `2.oz` → 0.567.
     - **Danger: "type transmogrification"** (a term Fowler credits to Neal Ford). `42.grams` starts
       with an integer and turns into a floating point — meaning every subsequent method in the chain
       must be defined on *multiple* numeric types.
  2. **A quantity object** (magnitude 42, unit grams).
     - "In general, I much prefer quantities to simple numbers for representing dimensioned values;
       quantities represent my intent better and also allow me to define useful behavior (such as
       alerting me to problems with `42.grams + 35.cm`)."
     - Almost no language platform ships a quantity class, but it's easy to write with whatever fluent
       methods you need. Because the magnitude is encapsulated, **the type transmogrification problem
       largely disappears** — all subsequent methods are defined on quantity.
     - Cost: the quantity class now carries DSL fluent methods, "which may make the quantity class
       harder to understand."
  3. **An Expression Builder.** `42.grams` yields a builder; you get full control over the rest of the
     expression. Cost: the calling code must be able to unpack the subject from the builder. Fine for
     `ingredients { 42.grams.flour; 2.grams.nutmeg }`, a problem for `42.grams + 3.oz`.
     - "I tend to prefer an Expression Builder most of the time, but it really depends on the context
       of its use."
  (Fowler, DSL book, Ch. 46 "Literal Extension", section "How It Works")

### When to use it

- **Sceptical framing.** "Literal Extension has become a popular illustration of how to make APIs more
  fluent, particularly by advocates of languages which are able to do it. ... It can help a good deal
  in improving fluency, although there's also the suspicion that some of this enthusiasm is fondness
  of a new toy."
- **The real cost is global interface pollution.** "In some environments, there is a serious concern
  that adding methods like this to literals will bloat the interface of those literal classes. These
  Literal Extensions are only needed in some contexts, so if they appear in more contexts they can
  make a class's interface much more confusing." You must weigh the usefulness of the extension
  against the confusion it adds everywhere else in the program.
- **The mitigation: namespace scoping.** "Some language environments allow you to state that Literal
  Extensions are bound to a namespace, which avoids this problem." (In the C# example he departs from
  his usual practice and shows the namespace explicitly, precisely because it means the extension
  method "will only show up if I'm in the right namespace.")
  (Fowler, DSL book, Ch. 46 "Literal Extension", section "When to Use It")

### Example — Recipe ingredients (C#)

Borrowed from Neal Ford: `var ingredient = 42.Grams().Of("Flour");` — the C# formulation of the
sketch, using domain types rather than an Expression Builder.

Demonstrates:

- An extension method on `int` returning a `Quantity(amount, unit)`; the extension class lives in an
  explicit namespace so the method only appears where it's wanted.
- **A sharp separation between general-purpose library types and DSL-only vocabulary.** The `Of`
  method is *not* put on `Quantity`, even though Fowler wrote `Quantity` himself:
  > "Although quantity is a class I'm writing, I don't think the `Of` method belongs on it — because
  > `Of` is part of a DSL for a limited purpose, while the quantity class can be used as part of a
  > general library. So I use an extension method again."
  This is the most transferable idea in the chapter.
- Ingredient names are given as strings in the DSL and resolved to objects via a substance registry
  **acting as a Symbol Table** (a dictionary that lazily creates the substance on first request).
  (Fowler, DSL book, Ch. 46 "Literal Extension", section "Recipe Ingredients (C#)")

### Relationships

- Typically the entry point into **Method Chaining**; may or may not use **Expression Builder**.
- Its resolution of names to objects uses **Symbol Table**.
- The "quantity vs. raw number" discussion connects to the Quantity analysis pattern.

### SDK relevance

- **This is monkey-patching / extension-method API design**, and Fowler's rule is namespace or module
  scoping: extensions to types you don't own should be opt-in and locally scoped, never globally
  visible. A library that adds methods to `Integer` for everyone is imposing its vocabulary on the
  whole program.
- **Keep DSL-specific fluent methods off general-purpose types.** `Of` belongs to a limited-purpose
  language; `Quantity` belongs to the general library. Mixing them makes the general type confusing
  for everyone who isn't writing the DSL. Generalizes to: *don't bolt your framework's fluent
  vocabulary onto shared domain/model classes.*
- **Watch the return type of every chain step.** Type transmogrification (int → float → …) forces you
  to define the rest of your fluent vocabulary on every type it might pass through. A purpose-built
  wrapper type (quantity, builder) that stays stable through the chain is almost always the better
  choice — the same reason fluent builders return `this`/`Self` rather than shifting types.
- **Fluency is not free; measure it against interface clarity.** Fowler's "fondness of a new toy" line
  is the general caution against clever tricks: a technique's availability and elegance are not
  reasons to adopt it.

---

## Cross-cutting themes in Chapters 39–46

Worth extracting as design principles, since they recur across the eight patterns:

1. **Keep the magic proportional to the benefit.** Dynamic Reception's fluency is paid for in
   impenetrable stack traces (Ch. 41); Parse Tree Manipulation's power is paid for in a walker that
   must reject most of the host language (Ch. 43); Class Symbol Table's autocompletion is paid for in
   reflective setup code and a contorted script layout (Ch. 44). In every case Fowler states the
   exchange rate explicitly and refuses the trade when the benefit is thin.

2. **Use the open-ended mechanism only where the vocabulary is genuinely open.** In the chaining
   example (Ch. 41) the attribute-name and value builders use `method_missing`; the operator builder,
   with its fixed operator set, uses ordinary methods. Restrict dynamic dispatch to the part of the
   grammar that actually varies.

3. **Layer the API by complexity, and don't stretch one mechanism to cover everything.** Active Record
   supports simple dynamic finders and deliberately stops (Ch. 41). IMAP makes conjunctions easy while
   still permitting general Booleans awkwardly (Ch. 43). The promotion model accepts closure-backed
   conditions alongside DSL-generated ones (Ch. 41). "Different solutions may work best at different
   complexities, so you should provide more than one."

4. **When a technique starts requiring special cases, you've outgrown it.** Special-cased Dynamic
   Reception means don't use Dynamic Reception. A growing pile of polishing regexes means write a
   parser. A desire to build parse trees out of chained method calls "is a smell indicating that the
   internal DSL is doing too much work."

5. **Mix techniques; don't chase purity.** Greenspun form (Ch. 40) and the fully symbol-free state
   machine (Ch. 41) both demonstrate that maximizing one technique produces worse DSLs than a
   judicious blend. "A mixture of techniques is often the best bet."

6. **Discoverability vs. expressiveness is the recurring axis.** Literal Map is expressive but its keys
   are invisible and unvalidated (Ch. 40) — so validate them yourself and prefer keyword arguments.
   Class Symbol Table sacrifices expressiveness and script layout freedom to buy discoverability
   (Ch. 44). Literal Extension buys fluency at the cost of polluting a widely-used interface (Ch. 46).

7. **Shape the DSL like its domain/target, not like the host language's flashiest feature.** The IMAP
   comparison (Ch. 43) is the cleanest demonstration: the Method-Chaining version won because it
   mirrored IMAP's own query language.

8. **Separate definition from processing when — and only when — they should vary independently**
   (Ch. 42). The corollary discipline: declarations must be purely declarative, with no logic flow, no
   ordering dependencies, and no implied coupling to when processing runs.

9. **Explanation order is not construction order** (Ch. 43, "Stepping Back"). Build feature by feature,
   refactoring as you go; present the result decomposed by concern.

10. **Solve cosmetic problems with tooling before adding machinery.** Syntax highlighting the noise
    characters into the background beats a regex pipeline (Ch. 45).
