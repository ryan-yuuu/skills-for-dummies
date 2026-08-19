# Study Notes — Fowler, *Domain-Specific Languages* (2010), Chapters 6 (tail) – 10

Source: `Domain-Specific Languages.pdf`, PDF pages 88–120.

Chapter boundaries found in this PDF rendering:

| Chapter | PDF pages |
|---|---|
| Ch. 6 "Choosing Between Internal and External DSLs" (tail only) | 88–90 |
| Ch. 7 "Alternative Computational Models" | 91–96 (top) |
| Ch. 8 "Code Generation" | 96 (mid) – 101 |
| Ch. 9 "Language Workbenches" | 102–112 (top) |
| Part II front matter + Ch. 10 "A Zoo of DSLs" | 112–120 (top) |
| Ch. 11 "Semantic Model" begins | 120 |

---

## 0. Tail of Chapter 6: Choosing Between Internal and External DSLs (PDF 88–90)

Included because it closes out Part I's narrative and sets up Chapters 7–9. Fowler's overall verdict:
neither internal nor external DSLs are generally better; the choice is situational.

### 0.1 Section "Programmer Familiarity"

- The common argument for internal DSLs — "programmers already know the host language" — is real but
  overrated. Fluent-interface style takes getting used to; and an external DSL is, by definition,
  *simple*, so it isn't hard to learn either.
- **Judgement call:** you can lower the learning cost of an external DSL by echoing the syntactic
  conventions of the team's usual programming language.
- **The bigger difference is tooling, not syntax.** With an internal DSL you inherit the host
  language's IDE — refactoring, navigation, type-aware autocompletion. Sometimes you must adopt a
  more elaborate technique (e.g. *Class Symbol Table*) specifically to *preserve* tool support.
  With an external DSL you typically fall back to a plain text editor; syntax highlighting is easy
  to add, but type-aware autocompletion is essentially out of reach.

### 0.2 Section "Communication with Domain Experts"

- Internal DSLs are permanently constrained by host syntax; there is always some **syntactic noise**.
  Programmers barely notice it; domain experts do.
- How much this matters depends on the host language (some languages are far better DSL hosts than
  others) and on the particular domain experts.
- **Judgement call:** Fowler leans toward pushing harder for an external DSL when better
  communication with domain experts looks achievable — the communication channel is that valuable.
- **Escape hatch:** start internal, switch to external later. Because both drive the *same*
  **Semantic Model**, the incremental cost of building the second DSL is modest. This is the single
  most reusable architectural point in the chapter.

### 0.3 Section "Mixing In the Host Language"

- An internal DSL is "nothing more than a convention to use certain fluent methods"; the boundary
  between DSL code and ordinary imperative host code is **wafer-thin**. That thinness is both
  benefit and hazard.
- **Benefit:** when the DSL lacks a construct (arithmetic, abstraction, control flow), just use the
  host language. You get the host's abstraction facilities for free — you can build abstractions
  *on top of* the DSL.
- Motivating example: build languages. Make and Ant are external DSLs over a **Dependency Network**;
  both express dependencies well, but real build tasks need imperative logic and layered
  abstractions. Ant "slid into generality," accumulating imperative constructs that don't suit its
  XML nature. Rake (Ruby internal DSL) mixes Dependency Network with imperative code via
  **Nested Closure**, and uses Ruby objects/methods to build abstractions over the network.
- Mixing external DSLs with host code is possible (**Foreign Code** embeds host code in DSL scripts;
  DSLs embed in host code as strings — as with regexes and SQL) but awkward: tools don't understand
  the embedded language, and symbol integration across the boundary is poor (referring to a host
  variable from inside a DSL fragment is hard).
- **Rule of thumb:** if you want to intermix host and DSL code, an internal DSL is almost always the
  way to go.

### 0.4 Section "Strong Expressiveness Boundary"

The mirror image of the previous section — the argument *for* external DSLs.

- Free mixing only works when DSL users are comfortable with the host language. Dropping lumps of
  host language into a DSL read by domain experts *raises* the communication barrier the DSL existed
  to remove.
- **Restriction as a feature.** "Often the benefit of a DSL is that it produces a restricted range of
  what can be done." A hard boundary:
  - makes it easier to understand what a script does,
  - acts as a **barrier to bugs**,
  - **limits what you have to test for** — pricing rules written in a restricted DSL can't send
    arbitrary messages to your CI server or alter order workflow,
  - can help with **security**.
- With a general-purpose language anything is possible, so the boundary has to be policed by
  convention and code review instead of by the language.
- **SDK relevance:** this is the classic *capability-restriction* argument for narrow APIs. A
  deliberately non-Turing-complete configuration surface reduces the test matrix, the blast radius,
  and the review burden — the same reasoning behind declarative config formats, policy languages,
  and sandboxed plugin APIs.

### 0.5 Section "Runtime Configuration"

- A major reason XML DSLs became popular: they move the execution context from **compile time to
  runtime**. With a compiled host language, an external DSL can be parsed at runtime, translated
  into a Semantic Model, and executed — changing behavior without a recompile. (Moot in an
  interpreted language.)
- Alternative: use an interpreted language alongside the compiled one and write an internal DSL
  there. But this **attenuates** most internal-DSL advantages: the team may not know the dynamic
  language (loses familiarity), tooling is usually poorer, mixing dynamic and static constructs is
  awkward, and a full dynamic language means you can't put firm boundaries around the DSL.
- **Conclusion:** external DSLs mesh better with a static host language.

### 0.6 Section "Sliding into Generality"

- The canonical failure mode of external DSLs, named after Ant. James Duncan Davidson (Ant's
  creator) asked: "How do we prevent disasters like Ant occurring?"
- Ant's real flaw isn't XML syntax; it's that **it steadily grew in capability until it lost the
  limited expressiveness a DSL needs**. Sendmail is the Unix-world equivalent. "Drop by drop, all
  the clarity that a good DSL has leaks out."
- **There is no simple answer** — it takes constant attention and determination to refuse complexity.
- **Alternatives to extending a language:**
  1. Introduce *another* language for the difficult cases instead of growing the first one.
  2. **Layer a second DSL over the base DSL whose output is the base DSL.** This gives you
     abstraction-building in a language that lacks abstraction features. (Fowler later cites SASS
     over CSS as exactly this.)
  3. Switch to an internal DSL when this kind of complexity grows, since you can then mix DSL and
     general-purpose elements.
- Internal DSLs don't suffer this problem (they're already melded with a general language), but they
  have the analogue: mixing gets so intertwined that you lose any sense of "DSLness."
- **SDK relevance:** the strongest generalizable lesson in Part I. A library's declarative surface
  degrades the same way — each "just one more escape hatch" erodes the property that made the
  surface comprehensible. The disciplined response is a *second layer* (a generator, a preprocessor,
  a higher-level API that emits the lower-level one), not a bolt-on to the original.

### 0.7 Section "Composing DSLs"

- Since DSLs should be small and limited, real work requires composing them with general-purpose
  languages and **with each other**.
- **Internal:** composition is as easy as mixing with the host language; you get the host's
  abstraction facilities to glue them.
- **External:** much harder. **Syntax-Directed Translation** would require writing independent
  grammars and composing them, but most **Parser Generators** have no facility for this — a
  consequence of their focus on general-purpose languages. You fall back to **Foreign Code**, which
  is clunkier than it should be.
- **SDK relevance:** composability is a first-class design property. If two of your DSLs/config
  formats can't be nested or referenced from each other, users will glue them with string
  concatenation — the worst possible seam.

### 0.8 Section "Summing Up"

- Explicit non-conclusion: no clear general advantage either way, and Fowler declines to give
  guidelines.
- The one thing he stresses: **experimenting in both directions is cheaper than you think, because
  a Semantic Model lets you layer multiple DSLs — internal and external — over the same model.**
- Glenn Vanderburg's approach, endorsed: use an **internal DSL early**, while you're still figuring
  out what the DSL should do (easy access to host facilities, seamless evolution). Once things
  settle and you need external-DSL advantages, build one. The Semantic Model makes the migration
  cheap.
- A third option — a language workbench — is deferred to Ch. 9.

---

## 1. Chapter 7: Alternative Computational Models (PDF 91–96)

### 1.1 Opening: what "declarative" actually means

- Fowler dislikes the word "declarative" — it's used as a very broad brush. His working definition:
  **declarative means "something other than imperative."**
- Mainstream languages follow the **imperative computational model**: computation as a sequence of
  steps; conditionals and loops vary the steps; steps group into functions. OO adds bundling of data
  with process, plus polymorphism — but is still grounded in the imperative model.
- Imperative gets flak from academics but has survived since the earliest days of computing because
  it's easy to understand: sequences of actions are straightforward to follow.

### 1.2 The two kinds of understanding — the core distinction of the chapter

Fowler splits "ease of understanding" into two things:

1. **Understanding of intent** — what are we trying to achieve?
2. **Understanding of implementation** — how does the code work to satisfy that intent?

The imperative model is *excellent* at (2): you read the code and see what it's doing; the debugger's
step sequence corresponds exactly to source order.

It is often weak at (1). If the intent genuinely *is* a sequence of actions, imperative is fine. When
intent isn't naturally a sequence, a different computational model is worth considering.

**This is the central judgement call of the chapter and it recurs everywhere:** alternative
computational models trade implementation-comprehension for intent-comprehension.

### 1.3 The decision-table example (conceptual)

- A car-insurance scoring rule is naturally expressed as a small table: rows of conditions
  (has cell phone? has red car?) and rows of consequences (points).
- Translating this into imperative code with one `if` per column is *more verbose* than Fowler's
  usual terse conditional style — **and he prefers the verbose version**, because it corresponds
  more closely to the domain expert's tabular way of thinking. Layout mirrors intent.
- **But the correspondence is still imperfect,** and the imperfection is instructive:
  - The imperative model **forces an evaluation order** that the decision table does not imply. That
    order is an **irrelevant implementation artifact** injected into the representation. (Minor for
    decision tables; can matter a lot for other models.)
  - More seriously, imperative encoding **removes opportunities**. A real decision table can be
    checked for missing permutations or accidentally repeated permutations. You can't do that to a
    chain of `if` statements.

**Generalizable principle:** a representation that carries less accidental structure carries more
*checkable* structure. Turning declarative data into control flow destroys the ability to analyse it.

### 1.4 Adaptive Model

- The alternative to imperative code: build a **decision-table abstraction** and *configure* it for
  the specific case (add conditions as predicates, add columns as condition/consequence tuples).
- Benefits obtained by doing so:
  - Faithful representation of the original table.
  - No spurious ordering — ordering is internal to the decision table, which may even permit
    exploiting concurrency.
  - **The table can validate itself** — tell you if the condition set is malformed or incomplete.
  - Execution context shifts from **compile time to runtime**: rules change without recompiling.
- **Definition — Adaptive Model:** a style of representation where "the behavior is largely defined
  by the *instances* of the model and how they are wired together." You cannot understand what
  behavior to expect without looking at the configuration of instances.
  - Related to Yoder & Johnson's "adaptive object model" writing, but not restricted to OO —
    behavior-capturing data structures are common in databases too.
  - Contrast with ordinary OO models: those have objects containing behavior *and* data; what makes
    a model *adaptive* is that the behavior lives in the wiring, not the classes.
- **Adaptive Models and DSLs are orthogonal notions** that can be used independently — but they "go
  together like wine and cheese." The Semantic Model a DSL populates is *often* an Adaptive Model
  supplying an alternative computational model for part of the system.

**The big negative of Adaptive Models** (stated bluntly and at length):

- Behavior is **implicit**; you can't read the code and see what happens.
- Intent gets easier to understand; **implementation gets harder** — which bites hardest when
  something breaks and you must debug.
- Reputation for being hard to maintain. Fowler reports people taking *months* to figure out how one
  works; once they do they're very productive, but many never do, and until then "it's a nightmare."
- This is a **real** issue that rightly deters many people.
- **How DSLs mitigate it:** a DSL makes it much easier to see how an Adaptive Model is *configured*.
  It doesn't remove the burden of understanding the generic machinery, but seeing the specific
  configuration clearly "can give you a significant leg up."

### 1.5 Why alternative computational models motivate DSLs at all

Stated explicitly as one of the compelling reasons to use a DSL:

> If your problem can be expressed easily using imperative code, then a regular programming language
> works just fine.

The key DSL benefits — greater productivity and communication with domain experts — "really kick in"
when you're using an alternative computational model. Domain experts often think nonimperatively
(e.g. in decision tables). The **Adaptive Model captures their way of thinking in the program**; the
**DSL communicates that representation back to them (and to you)**.

**SDK relevance:** this is a sharp test for when a declarative API earns its keep. If the domain's
natural mental model is a sequence of steps, ship functions. If the domain's natural mental model is
a table, a graph, a rule set, or a state machine, a declarative/configuration API buys you real
comprehension *and* machine-checkable structure — at the cost of debuggability, which you must then
pay back with tracing.

### 1.6 Section "A Few Alternative Models"

Fowler explicitly declines to be comprehensive; the sample is meant to help in common cases and to
"spark your imagination to come up with specific computational models for your domain."

#### 1.6.1 Decision Table

- Structure: rows of **conditions** followed by rows of **consequences**; each **column** is a case.
- Semantics: take an input, find the column whose conditions all match, apply that column's
  consequences.
- Conditions need not be Boolean — richer tables use numeric ranges etc.
- **When to use:** particularly easy for nonprogrammers to follow, so excellent for communicating
  with domain experts. Their tabular nature makes them natural to edit **in a spreadsheet** — "this
  is one case of a DSL where direct editing by a domain expert is more likely than not."
  (Recall: elsewhere Fowler is skeptical that domain experts author DSL scripts; decision tables are
  his named exception.)

#### 1.6.2 Production Rule System

- **Definition:** modeling logic by dividing it into **rules**, each with a **condition** and a
  **consequent action**. Each rule is specified individually, superficially like a bunch of if-then
  statements.
- The difference from imperative if-then: you specify conditions and actions but **leave it to the
  underlying system to execute them and tie them together**.
- **Chaining** — the defining characteristic. Firing one rule changes whether other rules should
  fire. Chaining lets you write rules individually without thinking about their broader
  consequences, and lets the system work out those consequences.
- **The benefit is also the danger.** Production rule systems rely heavily on **implicit logic**,
  which can do unanticipated things — sometimes beneficial, sometimes harmful. Errors are typically
  precisely because rule authors didn't account for how rules interact.
- **Generalized warning — the most transferable paragraph in the chapter:**
  - Problems from implicit behavior are a **common issue with all alternative computational models**.
    We make plenty of mistakes even in the imperative model we're used to; with alternative models
    we're more prone to problems because we often cannot reason about behavior by reading the code.
  - **Therefore: whenever you implement an alternative computational model, it is important to
    produce a tracing mechanism** so you can see exactly what happened on an execution. For a
    production rule system this means recording which rules fired and surfacing that record on
    demand, so a puzzled user or programmer can follow the chain that led to an unexpected
    conclusion.
- **Build vs. buy:** many mature products exist, but it can still be useful to write a small
  production rule system in your own code. "Like any case where you roll your own alternative
  computational model, you can usually get away with something relatively simple when you do it at a
  small scale with a particular domain in mind."
- **Chaining isn't mandatory.** A rule system *without* chaining is a good fit for **validation
  rules**: a bunch of conditions whose action is raising an error. Thinking of behavior as a set of
  independent rules is still useful.
- **Decision Table vs. Production Rule System.** Formally you can argue a decision table is a rule
  system where each column is a rule — but this "misses the point." With a rule system you focus on
  behavior **one rule at a time**; with a decision table you focus on the **entire table**. That
  shift in thinking is essential; they are **different mental tools**.
  - *Principle:* computational models are distinguished by the unit of attention they impose, not
    just by their expressive power.

#### 1.6.3 State Machine

- Models an object's behavior as a set of **states**, with **events** triggering **transitions**;
  which transition fires depends on the current state.
- Core elements: states, events, transitions. Many variations build on that basic structure,
  particularly in **how the state machine initiates actions**.
- **When to use:** common choice because many systems can be understood as reacting to events by
  going through a series of states.
- The book's running example (Miss Grant's controller) is a state machine.

#### 1.6.4 Dependency Network

- The most familiar alternative model in developers' daily work: it underpins Make, Ant, and
  derivatives.
- Model: **tasks** plus the **prerequisites** of each task. State the dependencies, invoke a target
  task, and the system determines which other tasks must run and in what order.
- Key property: a task listed twice as a prerequisite is still **run only once**.
- **When to use:** "a good choice when you have computationally expensive tasks with dependencies
  between them."

### 1.7 Section "Choosing a Model"

Fowler finds it hard to give guidelines; his honest heuristics:

- It boils down to a sense that the computational model **fits the way you think about your problem**.
- **Best way to determine fit: try it out.** Start on paper — describe behaviors using simple text
  and diagrams. If a model passes that "simple desk check," it's worth building — perhaps as a
  prototype — to see how it works in action.
- **Sequencing principle:** the key thing is to get the **Semantic Model** working properly. A simple
  DSL may help during that process, but **put more effort into tuning the model first, before
  getting a very readable DSL**. Once a reasonable Semantic Model is in place, it's relatively easy
  to experiment with different DSLs to drive it.
- He notes there are many more models than these and that "a book of computational models would be a
  good book for somebody to write."

**SDK relevance:** "model first, surface syntax second" is directly transferable to API design.
Get the object/data model and its invariants right; the fluent surface, the config format, the CLI,
and the RPC schema are all comparatively cheap projections of it. This is the same seam as §0.2/§0.8:
one model, many front ends.

---

## 2. Chapter 8: Code Generation (PDF 96–101)

### 2.1 Opening: why generate code at all

- Default position: parse the DSL, populate a **Semantic Model**, then **execute the Semantic Model
  directly**. That is usually the easiest thing to do and often the whole job.
- Code generation is the fallback for when you can't do that — when the DSL-specified logic must
  execute in a very different environment where building a Semantic Model or a parser is difficult
  or impossible. "By using code generation, you can take the behavior specified in the DSL and run
  it in almost any environment."

### 2.2 The two-environment framing — the chapter's architectural backbone

Code generation means you have **two distinct environments** to think about:

1. **The DSL processor environment** — where the parser, the Semantic Model, and the code generator
   live. This needs to be a *comfortable* environment for developing those things.
2. **The target environment** — the generated code and its surroundings.

> "The point of using code generation is to separate the target environment from your DSL processor
> because you can't reasonably build the DSL processor in the target environment."

**SDK relevance:** this is exactly the codegen-toolchain separation in modern SDKs (OpenAPI/protobuf/
GraphQL generators): the generator runs in a rich environment (typed, tested, IDE-supported) and
emits artifacts for a constrained one. Fowler's framing — "you can't reasonably build the processor
in the target" — is the cleanest justification for that split.

### 2.3 Reasons the target environment forces generation

1. **Resource-constrained targets** — e.g. an embedded system that cannot run a DSL processor.
2. **The target is itself a DSL.** Because DSLs have limited expressiveness, they usually lack
   abstraction facilities needed by a more complex system. Extending the DSL to add abstraction would
   complicate it, perhaps enough to turn it into a general-purpose language (i.e. *sliding into
   generality*, §0.6). Better to do the abstraction in a different environment and **generate code in
   your target DSL**.
   - Canonical example: specify query conditions in a DSL, **generate SQL**. You want the query to
     run efficiently in the database, but SQL isn't the best way for you to represent queries.
3. **Lack of familiarity with the target environment** — it may simply be easier to specify behavior
   in a familiar language and generate the unfamiliar one.
4. **To enforce static checking.** You might characterize a system's interface with a DSL while the
   rest of the system talks to that interface in C#. Generate a **C# API** so callers get
   compile-time checking and IDE support; when the interface definition changes, regenerate and
   **let the compiler point at the damage**.

**SDK relevance (item 4 especially):** this is the strongest argument in the book for generated
client SDKs. The DSL/spec is the source of truth; the generated typed API converts spec drift into
compile errors instead of runtime failures, and gives users autocompletion. Fowler frames generation
as a *checking and tooling* strategy, not merely a portability strategy.

### 2.4 Section "Choosing What to Generate"

Two styles, distinguished by **whether an explicit representation of the Semantic Model exists in the
target environment**:

#### 2.4.1 Model Ignorant Generation

- The model's logic is **embedded into the control flow of the target language** — for a state
  machine, nested conditionals (outer switch on current state, inner switch on event).
- There is **no explicit representation of the Semantic Model** in the generated code.

#### 2.4.2 Model-Aware Generation

- Some representation of the Semantic Model is placed **into the generated code**. It needn't match
  the DSL processor's model exactly; it just needs to be some data representation (for a state
  machine, e.g. nested maps: state → event → target state).
- This may be a "crude" model — perhaps no explicit state/transition/event classes — but the **data
  structure captures the behavior**.
- Because it's data-driven, the generic code is **entirely generic** and must be configured by
  specific code.

#### 2.4.3 The key structural insight

> By putting a representation of the Semantic Model into the generated code, the generated code takes
> on the same split between **generic framework code** and **specific configuration code**.

- **Model-Aware Generation preserves the generic/specific separation.**
- **Model Ignorant Generation folds them together** by representing the Semantic Model in control
  flow.

Consequences:

- With Model-Aware Generation, **the only thing you need to generate is the specific configuration
  code**. The generic machinery (the "basic state machine") can be **built and tested entirely in the
  target environment** by hand.
- With Model Ignorant Generation you must generate much more. You can pull some code out into library
  functions, but **most of the critical behavior has to be generated**.
- Therefore **Model-Aware Generation is much easier**: generated code is usually very simple, and the
  generic section, though you must build it, is independently runnable and testable outside the code
  generation system.

#### 2.4.4 Fowler's recommendation and its exceptions

- **"My inclination, therefore, is to use Model-Aware Generation as much as possible."**
- **When you can't:** often the entire reason for generating is that the target language can't
  represent a model easily as data. Even when it can, there may be **processing limitations** —
  embedded systems commonly use Model Ignorant Generation because the runtime overhead of
  model-aware code would be too great.
- **Deployment bonus of Model-Aware Generation:** because behavior lives in configuration, you can
  replace *only the configuration artifact* to change behavior. E.g. generating C, put configuration
  in a different library from the generic code — you can alter specific behavior without replacing
  the whole system (given some runtime binding mechanism).

#### 2.4.5 Pushing further: runtime-readable representations

- You can go beyond generated configuration *code* and generate a **data file** read entirely at
  runtime (e.g. a small text table of `state event target` triples). This lets you change behavior at
  runtime, at the cost of the generic system needing startup-time load code.
- **Is that just another DSL?** Fowler says no, and the reasoning is a useful definitional test:
  - It **isn't designed for human manipulation**. Textual format makes it human-readable, but that's
    a debugging convenience.
  - It's **primarily designed to be really easy to parse**, so it loads quickly into the target.
  - **"When designing such a format, human readability comes a distant second to simplicity of
    parsing. With a DSL, human readability is a high priority."**

**SDK relevance:** a crisp criterion for separating *interchange formats* from *authoring formats*.
Optimize an interchange format for parse speed and machine simplicity; optimize an authoring format
for human readability. Conflating them produces formats that are bad at both.

### 2.5 Section "How to Generate"

Two main styles for generating textual output:

#### 2.5.1 Transformer Generation

- You **write code that reads the Semantic Model** and generates statements in the target source.
- For a state machine: walk the events, generate declarations for each; walk the commands; walk the
  states, and for each state navigate its transitions and generate code for those.
- **Driven by either input, output, or both.**

#### 2.5.2 Templated Generation

- You **begin by writing a sample output file**, then place **template markers** wherever something
  is specific to the particular model, calling out to the Semantic Model to generate the appropriate
  code. Familiar from ASP/JSP-style templated web pages; processing replaces template references
  with generated code.
- **Driven by the structure of your output.**

#### 2.5.3 Choosing between them

- Both work well; experiment with each and see which suits.
- **Templated Generation works best when there's a lot of static code in the output and only a few
  dynamic bits** — "particularly since I can look at the template file and get a good sense of what
  gets generated."
- **Consequence:** you're more likely to use Templated Generation with **Model Ignorant Generation**
  (lots of static structure). Otherwise — "actually, most of the time" — Fowler likes
  **Transformer Generation**.
- **They mix, and usually do.** Transformer Generation code typically uses string format statements
  for small chunks — miniature Templated Generation. Fowler's caveat is about *consciousness* of the
  choice, not purity:
  > "The moment you stop being thoughtful about what you are doing is the moment when you start
  > making an unmaintainable mess."

#### 2.5.4 Embedment Helper — the key hygiene pattern

**The biggest problem with Templated Generation:** the host code used to generate variable output
starts to **overwhelm the static template code**. If you're generating C from Java, you want the
template to be mostly C with minimal Java.

**Embedment Helper** is the fix, and Fowler calls it a *vital* pattern:

- All the complexity of figuring out how to generate the variable elements should be **hidden in a
  class that's called by simple method calls in the template**.
- **Rule stated explicitly: each callout in a template should be a single method call; anything else
  belongs inside the Embedment Helper.**

Benefits beyond readability:

- **Tooling.** The Embedment Helper is a regular class edited with tools that understand the host
  language. With sophisticated IDEs this is a big difference. Java embedded in a `.c` file gets no
  IDE help — often not even syntax highlighting.
- **Same problem, different context: grammar files.** Fowler reports frequently seeing
  **Syntax-Directed Translation** grammar files "full of long code actions, essentially blocks of
  **Foreign Code**." These blocks are woven into the generated parser, and **their size buries the
  structure of the grammar**. An Embedment Helper keeps code actions small and the grammar readable.

**SDK relevance / generalization:** whenever you embed language A inside language B's file, the
embedded fragments should be *single calls into a real module written in A's native file type*. This
applies to build scripts, IaC templates, SQL in ORMs, JSX-ish embeddings, YAML with inline scripts,
and codegen templates alike. The motivating force is tool support: keep code where the tools can see
it.

### 2.6 Section "Mixing Generated and Handwritten Code"

Sometimes all target code can be generated, but **more often than not you'll mix**.

**The two general rules:**

1. **Don't modify generated code.**
2. **Keep generated code clearly separate from handwritten code.**

#### 2.6.1 Why rule 1 — the authority argument

- The point of generating from a DSL is that **the DSL becomes the authoritative source for that
  behavior**. Any generated code is "just an artifact."
- Hand-editing generated code means losing those edits on regeneration. That causes extra work on
  every generation — and worse, it **introduces a reluctance to change the DSL and regenerate**,
  which undermines the whole point of having a DSL.
- **Exception noted:** inserting trace statements for debugging. Also: generating a *scaffold* to
  start handwritten code is sometimes useful, but "that's not the usual situation with DSLs."

#### 2.6.2 Why rule 2 and how to achieve it

- Since generated code should never be touched, keep it apart. Fowler's preference: **files are
  either all-generated or all-handwritten.**
- **He does not check generated code into the source repository**, since it can be regenerated at will
  during the build; he prefers generated code in **a separate branch of the source tree**.
- **Procedural systems** (files of functions) make this easy. **Object-oriented code** complicates it:
  one logical class often needs some generated parts and some handwritten parts.

Options for splitting a class:

- **Multiple files per class** — easiest when the language allows it. C# supports it via **partial
  classes**; **Java does not**.
- **Marked regions within a file** ("generated" vs "handwritten" areas). Fowler is dismissive: a
  clunky mechanism that leads to mistakes as people edit generated code, and it **forces you to check
  generated code into version control, which confuses the version history**.
- **Generation Gap** — the good solution: split generated and handwritten code **using inheritance**.
  Basic form: **generate a superclass; handwrite a subclass** that augments and overrides generated
  behaviors.
  - Keeps file-level separation *while* allowing flexible combination of both styles in a single
    class.
  - **Disadvantage:** you must **relax visibility rules** — methods that would otherwise be private
    become protected so subclasses can override and call them. Fowler considers this "a small price
    to pay."

#### 2.6.3 The control-flow heuristic

> "The difficulty of keeping the generated and handwritten code separate seems to be proportional to
> the pattern of calls between generated and handwritten code."

- A **simple one-way flow of control** — such as **Model Ignorant Generation** where generated code
  calls handwritten code in one direction — makes separation much easier.
- **Actionable advice:** if you're having trouble keeping the two apart, **think about ways to
  simplify the control flow** between them.

**SDK relevance:** this is the canonical "generated client + user extension" problem. The
recommendations map directly onto modern practice — partial classes / mixins / `_generated` modules,
never edit generated files, don't commit them, and prefer a one-way call direction (generated code
calls user hooks, not the reverse) to keep the seam clean.

### 2.7 Section "Generating Readable Code"

The debate: should generated code be as clear and well-structured as handwritten code, or is that
irrelevant because it should never be modified by hand?

**Fowler leans toward "well-structured and clear"**, with this reasoning:

- Even though you shouldn't hand-edit it, **people will need to understand how it works**. Things go
  wrong and require debugging, and **clear, well-structured code is much easier to debug**.
- Target: generate code "almost as good as that I would write by hand" — clear variable names, good
  structure, most of the habits he'd normally use.

**The explicit exceptions — where he relaxes standards, and why:**

- **Time spent finding the right structure.** He's less inclined to spend time working out or
  creating the best structure for generated code.
- **Duplication.** He doesn't want obvious, easy-to-avoid duplication, but he doesn't agonize about
  it the way he does with handwritten code. The reason is the key insight:
  > "After all, I don't have to worry about modifiability, only the readability."
  If some duplication is clearer, he'll leave it in.
- **Comments.** He is *happier* to use comments in generated code, because **generated comments are
  guaranteed to be kept up to date**. Comments can **refer back to structures in the Semantic
  Model** — i.e. use comments to link generated output back to its source of truth.
- **Performance.** He'll compromise clear structure to meet performance goals — but notes that's true
  of handwritten code too.

**SDK relevance:** a precise, quotable rationale for generated-SDK style. Optimize generated code for
*readability and debuggability*, not for *modifiability*; duplication is cheap when nobody maintains
the output by hand; and generated comments (pointing back to spec/model elements) are unusually
valuable because they can't rot.

### 2.8 Section "Preparse Code Generation"

A less obvious use of code generation: not as *output* of the DSL script, but as **input support for
writing** it.

- Scenario: you need to integrate with external information when writing DSL scripts. Writing a DSL
  about linking territories to salespeople requires the symbols you use to match those in the
  corporate database.
- One way to ensure this: **use code generation to generate the information you need while writing
  your scripts.**
- Often such checking can be done when populating the **Semantic Model** — but sometimes it's useful
  to have the information **in source code too, particularly for code navigation and static typing**.
- Concrete example: writing an internal DSL in Java/C# where symbols referring to salespeople should
  be statically typed. **Code-generate enums listing the salespeople** and import them into your
  script files (cites Kabanov & Hunger).

**SDK relevance:** this is the ancestor of generated typed constants/literal unions from external
data (generated enums for feature flags, metric names, resource IDs, event types). The payoff is
IDE navigation and compile-time validity, not runtime behavior — a distinct and often-overlooked
reason to generate.

### 2.9 Section "Further Reading"

- Herrington — "the most extensive book available on code generation techniques."
- Markus Völter's set of code-generation patterns.

---

## 3. Chapter 9: Language Workbenches (PDF 102–112 top)

### 3.1 Framing and the heavy caveat

- **Definition:** language workbenches are "tools that help you build your own DSLs and provide tool
  support for them in the style of modern IDEs." They don't merely provide an IDE for *creating*
  DSLs; **they support building IDEs for editing those DSLs**, so a DSL script author gets the same
  degree of support a programmer gets from a post-IntelliJ IDE.
- Written in early 2010 when the field was very young — most tools "have barely left beta stage."
  Fowler states plainly that much of what he writes will be out of date on publication.
- **Editorial decision worth noting:** because the area is so volatile, he confines it to a single
  chapter and provides **no patterns in the reference section** for it, covering only the aspects he
  believed were relatively stable. He describes his general method: **look for core principles that
  don't change much** — hard to identify in a rapidly moving field.
- His assessment: "immense potential here — these are tools that could change the face of programming
  as we know it," but unproven.

### 3.2 Section "Elements of Language Workbenches"

Workbenches differ greatly in appearance but let you define **three aspects of a DSL environment**:

1. **Semantic Model schema** — the data structure of the Semantic Model, together with **static
   semantics**, usually via a **meta-model**.
2. **DSL editing environment** — a rich editing experience for DSL script authors, through either
   **source editing** or **projectional editing**.
3. **Semantic Model behavior** — what the DSL script actually does, built off the Semantic Model,
   most commonly via **code generation**.

Key structural observations:

- Workbenches make the **Semantic Model the core of the system**, so they all provide tools to define
  it. Instead of defining it in a programming language (as the rest of the book assumes), they define
  it in a **special meta-modeling structure that allows runtime tools to work on the model** — this
  is what enables their high degree of tooling.
- **Consequence: a separation between schema and behavior.** The Semantic Model schema is essentially
  a **data model without much behavior**; behavioral aspects come from *outside* the data structure,
  mostly as code generation. Some tools expose the model so you can build an interpreter, but code
  generation is by far the most popular way to make the model run.
- The **editing environments** are arguably the key contribution: a much richer range of tools for
  populating and manipulating a Semantic Model — from assisted textual editing, to graphical editors
  where a DSL script is a diagram, to **illustrative programming** (a spreadsheet-like experience).

Fowler then narrows to the two general principles he believes will have lasting relevance:
**schema definition** and **projectional editing**.

### 3.3 Section "Schema Definition Languages and Meta-Models"

#### 3.3.1 The core difference from the rest of the book

- Fowler (self-described "OO bigot") builds **object-oriented Semantic Models combining data and
  behavior**.
- **Language workbenches don't work that way.** They provide an environment for defining the
  **schema** of the model — its data structure — typically using a dedicated DSL for the purpose:
  the **schema definition language**. Behavioral semantics is left as a **separate exercise**,
  usually through code generation.

#### 3.3.2 Definitions

- **Schema** — what you can have in the contents of the model. "This is the same as any data structure
  definition: classes and instances, tables and rows, record types and records. The schema defines
  what goes into the instances." If guards aren't in the schema, you can't put guards on transitions.
- **Meta-model** — "a model whose instances define the schema for another model." In Fowler's worked
  example, the *base model* holds the instances (`MObject`s representing `active`,
  `waiting for draw`, `lightOn`, a transition); the *meta-model* holds the `MClass`es and `MField`s
  describing State, Event, Transition, and their fields. The two are linked by **type–instance
  connections**.
  - The demonstration is that instead of expressing the schema as **Java class definitions**, you can
    express it as **Java objects** (`MClass`, `MField`, `MObject`), which lets you **manipulate the
    schema at runtime**.
- **Schema definition language** — since a meta-model is just another Semantic Model, you can define a
  DSL to populate it. "A schema definition language is really just a form of data model, with some
  way of defining entities and relationships between them." Many exist.

#### 3.3.3 The tradeoff: when NOT to use a meta-model — important and often missed

**When rolling a DSL by hand, there usually isn't much point in creating a meta-model.** Reasons:

1. **Using the host language's own structural definition capability is usually the best bet.** A
   language you have is much easier to follow — you use familiar constructs for *both* the schema
   and the instances.
2. **You lose static help.** In the meta-model version you write `aTransition.get("source")` instead
   of `aTransition.getSource()`. This makes it harder to discover what fields are available, forces
   you to do **your own type checking**, and generally means "I'm working *despite* my language
   rather than *with* it."
3. **Biggest argument:** you lose the ability to make the Semantic Model a **proper OO domain model**.
   The meta-model does a "tolerable, if kludgy" job of defining *structure*, but **it's really hard
   to define behavior**. If you want proper objects combining data and behavior, use the language's
   own schema definition mechanism.

#### 3.3.4 Why the tradeoff inverts for language workbenches

- To provide good tooling, **a workbench must examine and manipulate the schema of any model you
  define** — and that manipulation is much easier with a meta-model.
- Workbench tooling **overcomes many of the common disadvantages** of meta-models.
- Hence most workbenches use meta-models: the workbench **uses the model to drive editor definitions**
  and to help add the behavior that can't exist in the model.

**SDK relevance:** a genuinely transferable rule for reflective/metadata-driven design. Runtime
metadata (schemas-as-data, registries, descriptors) pays off exactly when *tooling* must consume it
generically. When only human programmers consume it, native language constructs win — you keep type
checking, discoverability, and the ability to attach behavior. Metadata-driven frameworks that lack
the tooling to justify it inherit all the costs and none of the benefits.

#### 3.3.5 Bootstrapped workbenches and the meta-regress

- The meta-model is itself a model, so it too has a schema. There's no reason that schema can't be
  defined using a meta-model — which lets you **use the workbench's own modeling tools on the schema
  definition system itself**, creating meta-models with the same tools used to write DSL scripts.
  "In effect, the schema definition language is itself just another DSL in the language workbench."
- **Definition — bootstrapped workbench:** a workbench that takes this approach. **Benefit:** it
  "gives you more confidence that the modeling tools will be sufficient for your own work, since the
  tool can define itself."
- Where the infinite regress stops: in practice the schema definition tools are **special in some
  way**, with some behavior hard-coded into the workbench. "The special thing about a schema
  definition model is that it's capable of defining itself."

#### 3.3.6 Schema definition language vs. grammar — a clean distinction

- **A grammar defines the concrete syntax of a (textual) language.**
- **A schema definition language defines the structure of the schema of a Semantic Model.**
- Therefore a grammar includes lots of things describing the **input language**, while a schema
  definition language is **independent of any DSL used to populate the Semantic Model**.
- A grammar also implies the structure of the **parse tree**; with tree construction rules it can
  define a **syntax tree**. But a syntax tree is usually different from a Semantic Model.

#### 3.3.7 Structural constraints

- A schema is largely about data structures (classes and fields) — thinking about the logical data
  structure in which Semantic Model elements are stored. **But there's a further element:
  structural constraints** — constraints on what makes valid instances of the Semantic Model,
  **equivalent to invariants in Design by Contract** (Meyer).
- **Two kinds, distinguished carefully:**
  - Constraints **implied by the data structure itself**: "we can't say anything in the Semantic
    Model that its schema can't store." If the state model has one target state per transition, you
    can't add a second — nowhere to put it. That constraint is *defined and enforced by the data
    structure*.
  - Constraints **not due to the data structure** — "we can store it, but it's illegal." E.g. a
    person's number of legs must be 0, 1, or 2 even though it's stored in an integer field.
    Constraints can be arbitrarily complicated, involving multiple fields and objects — e.g. a person
    cannot be her own ancestor. **This second kind is what "structural constraints" usually means.**
- Schema definition languages usually offer *some* way to express structural constraints — from
  simple attribute ranges up to a general-purpose constraint language.
- **One usual limitation, stated as a design rule:** structural constraints **cannot change the
  Semantic Model, they can only query it**. In this way they are **a Production Rule System without
  any chaining** (cross-reference to Ch. 7).

**SDK relevance:** the "make illegal states unrepresentable (structure) vs. validate what remains
(constraints)" split, plus the rule that validators must be **pure queries with no side effects**.
That purity rule is what makes constraints re-runnable, order-independent, and safely parallelizable.

### 3.4 Section "Source and Projectional Editing"

#### 3.4.1 Definitions

- **Source-based editing system:** the program is defined using a representation that is **editable
  independently of the tools used to process it** into a running system. In practice that
  representation is **textual**, so it can be read and edited by any text tool. Source is the key
  representation programmers edit and store; a compiler/interpreter turns it into executable form.
- **Projectional editing system:** the **core representation of the program is held in a format
  specific to the tool** — a persistent representation of the tool's **Semantic Model**. To edit, you
  start the tool's editing environment, and the tool **projects editable representations** of its
  Semantic Model for you to read and update. Projections may be text, diagrams, tables, or forms.
- Everyday example: **Microsoft Access**. You never see, let alone edit, textual source code for an
  entire Access program; you use tools to examine schema, reports, queries, etc.

#### 3.4.2 Advantages of projectional editing

- **Editing through different representations.** A state machine is best *thought of* diagrammatically;
  a projectional editor renders it as a diagram and lets you edit it directly. With source, you can
  only edit text — you can run it through a visualizer to *see* a diagram, but you can't **edit** that
  diagram.
- **Control over the editing experience** to make correct input easy and incorrect input impossible.
  A textual projection can, given a method call on an object, show only the legal methods for that
  class and allow only valid method names. Result: **a much tighter feedback cycle between editor and
  program**, and more assistance to the programmer.
- **Multiple projections**, simultaneously or as alternatives.
  - Intentional Software's demo: show a conditional expression in C-like syntax, then switch the same
    expression to a **Lisp-like syntax** or a **tabular form** via a menu command. You pick whichever
    projection fits the task at hand or an individual programmer's preference.
  - Simultaneous projections of the same information — e.g. a class's superclass as a field in a form
    *and* in a class hierarchy in another pane. **Editing either updates the core model, which in turn
    updates all projections.**
- **Semantic transformations.** Because representations are projections of an underlying model, they
  encourage transformations *of the model*. Renaming a method is captured as an operation on the
  model rather than in textual terms. "This is particularly helpful for doing refactorings in a safe
  and efficient manner."

#### 3.4.3 Why source-based editing still dominates — the counterarguments

Fowler notes projectional editing "is hardly new; it's been around for at least as long as I've been
programming," has many advantages, "yet most serious programming we do is still source-based." His
reasons:

- **Tool lock-in.** Projectional systems lock you into a specific tool. Beyond vendor-lock-in nerves,
  it **makes it hard to create an ecosystem where multiple tools collaborate over a common
  representation.** "Text, despite its many faults, is a common format; so tools that manipulate text
  can be used widely."
- **Source code management is the killer example.** The last few years produced concurrent editing,
  diff representation, automated merging, transactional repository updates, and distributed version
  control — all of which work across a wide range of programming environments **because they operate
  only on text files**. "We see a sad situation where many tools that could really use intelligent
  repositories, diffs, and merges are unable to do so." This is a big deal for larger projects, and is
  one reason larger systems still use source-based editing.
- **Pragmatic advantages of text.** Emailing a snippet to explain something is trivial; explaining via
  projections and screenshots is much more trouble. Text-processing tools automate transformations
  that a projectional system may not provide.
- **The subtle one — "helpful restriction vs. constraints on thinking."** A projectional system's
  ability to only allow *valid* input can be helpful, but "it's often useful to type in something
  that doesn't work immediately, as a temporary step, while thinking through a solution." Fowler
  explicitly flags that **the difference between helpful restriction and constraints on thinking is
  often a subtle one.**

#### 3.4.4 Model-assisted source editing — "have your cake and eat it"

- Named as one of the **triumphs of modern IDEs**: you work fundamentally in a source-based way, with
  all the advantages that implies, but when you load your source into the IDE **it creates a semantic
  model** that lets it use projectional techniques to make editing easier.
- **Cost:** a lot of resources — the tool must parse all sources and hold the semantic model in
  memory. Keeping the model updated as the programmer edits is "a difficult task."
- **Result "comes close to the best of both worlds."**

**SDK relevance:** the deep, durable lesson here is about **representation choice and ecosystem
effects**. Text-as-interchange wins not on merit of the representation but because it makes the
*surrounding tool ecosystem* possible (diff, merge, grep, review, email, CI). Any API/format decision
that makes the artifact opaque to generic tooling incurs this same ecosystem cost — a strong argument
for text-based config, text-based IaC, and human-diffable lockfiles, and against binary or
proprietary-store-only representations.

#### 3.4.5 Subsection "Multiple Representations" — representational roles

A vocabulary Fowler finds useful for reasoning about the flow of source and projectional editing:

- **Editing representation** — the representation of the program that we edit.
- **Storage representation** — the representation we store in persistent form.
- **Executable representation** — one we can run on our machine.
- **Abstract representation** — a purely computer-oriented construct generated at some point (e.g.
  during compilation) to make the program easier to process.

Applied:

- **Source-based:** source code plays **two roles at once** — editing representation *and* storage
  representation. A compiler turns it into an executable representation. With an interpreted
  language, **source is also an executable representation**.
- Abstract representations are generated during compilation. A modern IDE generates its *own* abstract
  representation to assist editing — and **there may be several**: the IDE's editing representation
  may differ from the compiler's syntax tree, and modern compilers often build multiple abstract
  representations for different purposes (a syntax tree for some things, a call graph for others).
- **Projectional:** the roles are arranged differently. The **core representation is the Semantic
  Model**, projected into **multiple editing representations**. The model is stored using a
  **separate storage representation**, which may be human-readable at some level (e.g. serialized to
  XML) "but isn't a representation any sane person would use for editing."

**SDK relevance:** cleanly separating "what humans edit," "what we persist," "what we execute," and
"what we analyse" is a general architectural discipline. Many painful systems collapse two of these
roles by accident (e.g. persisting the editing format, or executing the storage format).

### 3.5 Section "Illustrative Programming"

- **Definition:** Fowler's term for what projectional editing enables — putting a concrete
  **illustration** of program output in the foreground of the editing experience, with the program
  itself in the background.
- **Framing contrast:** in regular programming we pay most attention to **the program**, "a general
  statement of what should work" — general because it's text describing the general case, yielding
  different results with different inputs.
- **The spreadsheet argument.** The most popular programming environment in the world (by Fowler's
  "unscientific observation") is the spreadsheet, and its popularity is notable because most
  spreadsheet programmers are **lay programmers** — people who don't consider themselves programmers.
  - In a spreadsheet, the most visible thing is an **illustrative calculation with a set of numbers**.
    The program is hidden in the formula bar, visible one cell at a time.
  - **The spreadsheet fuses execution with definition and makes you concentrate on the former.**
  - Providing a concrete illustration of program output helps people understand what the program
    definition does, so they can more easily reason about behavior.
  - Shares a property with heavy use of testing — **but with the difference that in a spreadsheet the
    test output has more visibility than the program.**
- **Why "illustrative" and not "example":** "example" is heavily overused; "illustration" isn't, and
  it reinforces the *explanatory* nature of the example execution. Illustrations explain a concept by
  giving you a different way of looking at it; an illustrative execution helps you see what your
  program does **as you change it**.
- **Boundary cases** (Fowler deliberately sharpening the concept):
  - **IDE projections during editing** (e.g. a continuously updated class hierarchy) are *similar* but
    not the same: the hierarchy can be **derived from static information**. **Illustrative programming
    requires information from the actual running of the program.**
  - **REPL / interpreter snippets** — a beloved dynamic-language feature — are a *narrower* thing.
    Interpreting snippets lets you explore execution, "but it doesn't put the examples front and
    center, the way that a spreadsheet does with its values." Illustrative programming **pushes the
    illustration to the foreground; the program retreats to the background, peeping out only when we
    want to explore part of the illustration.**

#### 3.5.1 The downside — "I don't think illustrative programming is all goodness"

- Spreadsheets and GUI designers do a good job of revealing **what a program does** but
  **de-emphasize program structure**.
- As a result, complicated spreadsheets and UI panels are often **difficult to understand and
  modify**, and "rife with uncontrolled copy-and-paste programming."
- Diagnosis: this is a **consequence of the program being de-emphasized in favor of the
  illustrations** — programmers then don't think to take care of it. We suffer from a lack of care for
  programs even in regular programming, so it's unsurprising this occurs with lay programmers. The
  result: programs that "quickly become unmaintainable as they grow."
- **The stated challenge for future illustrative programming environments: help develop a
  well-structured program behind the illustrations** — "although the illustrations may also force us
  to rethink what a well-structured program is."
- **The hard part is creating new abstractions.** From Fowler's observations of rich-client UI
  software: they get tangled because UI builders think only in terms of **screens and controls**. His
  experiments suggest you need to find the right abstractions for your program, which will take a
  different form — **but the screen builder can't support them, "for it can only illustrate the
  abstractions it knows about."**
- Despite the problem, he argues illustrative programming should be taken more seriously — "we can't
  ignore the fact that spreadsheets have become so popular with lay programmers." Many workbenches
  target lay programmers, and projectional editing leads to illustrative programming, which could be
  vital to their eventual success.

**SDK relevance:** a precise articulation of the *low-code tooling ceiling*. A visual/illustrative
tool can only illustrate the abstractions built into it; the moment users need domain abstractions
the tool doesn't know about, they resort to duplication. Any builder-style API or GUI configurator
should therefore make user-defined abstractions first-class, or accept a hard complexity ceiling.

### 3.6 Section "Tools Tour" (as of early 2010 — historical)

Fowler is reluctant to name tools in such a volatile field and warns the details will be wrong by the
time you read it, but includes them to convey the *variety*.

- **Intentional Workbench (Intentional Software)** — "perhaps the most influential, and certainly the
  most sophisticated." Led by Charles Simonyi (PARC word processors, led Microsoft Office
  development). Vision: a highly collaborative environment where programmers and nonprogrammers work
  in a single integrated tool. Very rich projectional editing plus a sophisticated meta-modeling
  repository. Supports projections as text, tables, diagrams, illustrations, and all combinations.
  **Criticisms:** how long they've taken, how secretive they've been, and their activity on the
  **patent front** ("which alarms many in this field"). Began meaningful public presentations in
  early 2009.
- **MetaEdit (MetaCase)** — believed to be the **oldest released** tool (Intentional is oldest in
  development). Focused on **graphical projections**, also supports tabular (**but not text**).
  Unusually, it **isn't a bootstrapped environment** — a special environment is used for schema and
  projection definition. Microsoft's DSL tools group has a similar style of tool.
- **MPS — Meta-Programming System (JetBrains)** — another route to projectional editing, preferring a
  **structured text representation**. Targets **programmer productivity** much more than close domain
  expert involvement. JetBrains has strong developer-tooling credibility; they see MPS as a
  foundation for many future tools. **Most MPS code is open source** — Fowler flags this as
  potentially "a vital factor in getting developers to move into a very different kind of programming
  environment."
- **Xtext** (open source, on Eclipse) — notably **uses source editing rather than projectional
  editing**. Uses **ANTLR** as parser back-end and integrates with Eclipse to provide
  **model-assisted source editing** for DSL scripts, in a style similar to editing Java in Eclipse.
- **Microsoft SQL Server Modeling ("Oslo")** — a **mix of textual source and projections**. Modeling
  language "M" defines both a **Semantic Model schema** and a **grammar for a textual DSL**. The tool
  then creates a plugin for an intelligent editor giving model-assisted source editing. Resulting
  models go into a **relational database repository**, with a diagrammatic projectional editor
  (Quadrant) to manipulate them. **Models can be queried at runtime, so the whole system could work
  entirely without code generation.**
- Closing observation, worth remembering: purely on technical sophistication Intentional would take
  the prize, "but as we know it's often a lesser technology hitting the most important targets that
  wins in the end."

### 3.7 Section "Language Workbenches and CASE Tools"

- **CASE** (Computer-Aided Software Engineering): tools that would let you express your software's
  design in diagrammatic notations and generate your software. "They were the future of software
  development in the 90s, but have since faded away."
- **Surface similarities:** central role of a model, use of meta-models to define it, and projectional
  editing with diagrams.
- **The key technological difference: CASE tools did not give you the ability to define your own
  language.** MetaEdit is the workbench closest to a CASE tool, but its facilities to define your own
  language and control code generation from your model "are very different from what CASE tools
  provided."
- **On OMG MDA (Model-Driven Architecture):** some expect it to play a large role in the DSL/workbench
  landscape. Fowler is **skeptical — "I see the OMG MDA standards as too unwieldy for a DSL
  environment."**
- **The most important difference is cultural.** Many in the CASE world **looked down on programming**
  and saw their role as automating something that would then die out. **The language workbench
  community largely comes from a programming background** and aims to make programmers more
  productive (as well as increase collaboration with customers and users).
  - **Consequence, and Fowler's tell for judging such tools:** workbenches "tend to have strong
    support for code generation tools — as this is central to producing a useful output from the
    tool. This aspect tends to get missed during demonstrations, as it's less exciting than the
    projectional editing side, **but it's a sign of how seriously we should take the resulting
    tool**."

**SDK relevance:** the evaluation heuristic generalizes. When assessing a tool/platform, look past the
demo-friendly surface (visual editing, drag-and-drop) at the boring integration machinery (codegen,
export, CI story). Whether the vendor invested there tells you whether the tool is meant to live
inside a real engineering workflow.

### 3.8 Section "Should You Use a Language Workbench?"

- Repeated disclaimer about newness and volatility (early 2010).
- **Potential:** "If language workbenches pull off their vision, they could completely change the face
  of programming, altering our idea of a programming language." But — memorable hedge — this "could
  end up like nuclear fusion's potential to solve all of our energy needs."
- **Reason for caution beyond newness: significant lock-in.** "Any code you write in one language
  workbench is impossible to export into another one." An interoperability standard may come someday
  "but it will be very hard." **Any effort you commit could be lost if you hit a wall or there are
  vendor problems.**

#### 3.8.1 The mitigation strategy — the most practically useful idea in the chapter

**Treat the language workbench as a *parser* rather than as a full DSL environment.**

- **Full DSL environment approach:** design the Semantic Model in the workbench's schema definition
  environment and generate "pretty full-featured code."
- **Workbench-as-parser approach:**
  1. **Build the Semantic Model the usual way**, in your own code, outside the workbench.
  2. Use the workbench **only for the editing environment**, with a model geared to
     **Model-Aware Generation** against *your* Semantic Model.
- **Payoff:** "should you run into issues with your language workbench, it's only the parser that's
  affected. The most valuable stuff is in the Semantic Model which isn't locked in." You'll also find
  it easier to come up with an alternative parser mechanism.
- Fowler concedes this is somewhat speculative, but concludes the tools are worth experimenting with:
  "Although it's a risky investment, the potential returns are considerable."

**SDK relevance — this is a first-class architecture pattern:** *put the vendor at the edge, keep the
model in your own code.* The Semantic Model is the anti-lock-in asset; the parser/editor/UI is the
replaceable component. Exactly the reasoning behind hexagonal architecture, and the same seam Fowler
used in Ch. 6 to make internal→external DSL migration cheap and in Ch. 7 to make DSL experimentation
cheap. **One model, replaceable front ends** is the through-line of Part I.

---

## 4. Part II front matter (PDF 112)

Part II is titled **"Common Topics"** and lists: A Zoo of DSLs, Semantic Model, Symbol Table, Context
Variable, Construction Builder, Macro, Notification.

---

## 5. Chapter 10: A Zoo of DSLs (PDF 112–120 top)

**Purpose:** a brief survey of real DSLs, explicitly *not* chosen as "the best" — just a selection
chosen to show **the variety of different kinds of DSL that exist**. "It's a tiny fraction of DSLs
that exist out there, but I hope even a small sample can give you a taste of the full population."

Reading this chapter as a design study: each entry illustrates one or two distinct architectural or
API-design lessons.

### 5.1 Graphviz

- A library for producing graphical renderings of node-and-arc graphs; its language is **DOT**, an
  **external DSL**. It is "both a good example of a DSL and a useful package for anyone working with
  DSLs."
- **Language shape (conceptually):** two kinds of thing — **nodes** and **arcs**. Nodes are declared
  with a `node` keyword **but don't have to be declared** (they can be brought into existence by
  reference). Arcs are declared with an arrow operator. **Both nodes and arcs can carry attributes**
  listed in brackets. Statement separators are **entirely optional**.
  - *Design points worth noting:* optional declaration and optional separators are deliberate
    concessions to human authoring convenience — a DSL can afford them precisely because its scope is
    narrow.
- **Architecture — the clean-seam exemplar of the chapter:**
  - Graphviz uses a **Semantic Model** in the form of a **C data structure**.
  - The model is populated by a parser using **Syntax-Directed Translation** and
    **Embedded Translation**, written in **Yacc and C**.
  - The parser makes good use of **Embedment Helper** — since it's C, not a helper *object* but a
    **set of helper functions** called in the grammar actions. **Result: the grammar itself is quite
    readable, with short code actions that don't obstruct the grammar.** (This is the concrete
    payoff of the Ch. 8 Embedment Helper advice.)
  - The **lexer is handwritten** — "fairly common with Yacc parsers despite the presence of the Lex
    lexer generator."
  - **The real business of Graphviz occurs once the Semantic Model of nodes and arcs is populated:**
    layout onto a diagram, then rendering code for various graphics formats. **All of this is
    independent of the parser code** — "once the script is turned into the Semantic Model, everything
    else is based on those C data structures."
- **SDK relevance:** the ideal layering. Parser → model → (layout, rendering) with a hard boundary at
  the model. Everything valuable lives past the boundary and is reachable without the DSL at all.
  This is the same conclusion as Ch. 9's "workbench as parser."

### 5.2 JMock — the API-design evolution case study (highest SDK relevance)

Background:

- JMock is a Java library for **Mock Objects** (Meszaros, *xUnit Test Patterns*). Its authors have
  written several mock libraries and **evolved their ideas of a good internal DSL for defining
  expectations on mocks**. Fowler points to Freeman & Pryce's paper on that evolution as excellent.
- **How mock objects work:** you begin a test by declaring **expectations** — methods the object
  expects to be called on it during the test. You plug the mock into the object under test, stimulate
  that object, and the mock then reports whether it received the correct method calls — supporting
  **Behavior Verification**.
- **Why a DSL, and why internal:** "Mock expectations need to be written in with test code as a
  fragmentary DSL, so an internal DSL is a natural choice for them." This is a clear statement of the
  *fragmentary* DSL use case — the DSL is interleaved with ordinary host code, so host-language
  integration is mandatory.

#### 5.2.1 JMock 1 (the "Cenozoic era")

Composition of patterns used (this is the interesting part):

- **Method Chaining** on the mock object itself (`expects(...)` returning something you continue
  calling on).
- **Nested Function** for the argument-shaped parts (e.g. the cardinality `once()`, the argument
  matcher, the return-value specification).
- **Object Scoping** to allow the Nested Function methods to be written **bare** (unqualified).
  **JMock 1 implemented Object Scoping by forcing all tests using mocks to be written in a subclass of
  its library class.**
- **Progressive interfaces** — a deliberate device to make Method Chaining work better with IDEs:
  each chaining method returns a *narrower* interface exposing only what's legal next. Concretely,
  the `with` clause is **only available after `method`**, "which allows the autocompletion in IDEs to
  guide you through writing the expectations in the right way."
  - **This is one of the most transferable API-design ideas in the whole book.** Encode the grammar of
    valid call sequences in the *return types* of a fluent chain, so the IDE's autocompletion becomes
    the language's syntax guide and illegal sequences don't compile. (Modern names: type-state /
    step-builder / phantom-typed builders.)
- **Expression Builder** handles the DSL calls and translates them onto a **Semantic Model** of mocks
  and expectations. Freeman & Pryce's vocabulary for the two layers, which Fowler adopts:
  **Expression Builders = the *syntax layer*; Semantic Model = the *interpreter layer*.**
  - Again the same architectural seam: a thin syntactic façade over a real model that could be driven
    without it.

#### 5.2.2 The extensibility lesson — "an interesting lesson in extensibility"

Fowler flags this explicitly, and it is the sharpest SDK point in the chapter:

> The interplay of **Method Chaining** and **Nested Function** determines who can extend the language.

- **Method Chaining is closed to users.** Chaining methods are defined on the **Expression Builder**,
  so **all the methods you can use are fixed by the library**. Users cannot add to the chain.
- **Nested Function is open to users.** New nested functions are easy to add because **you define them
  on the test class itself** — or on your own subclass of the library superclass used for Object
  Scoping.
- **Therefore the choice between chaining and nested functions is not merely stylistic: it decides
  the extension points of your API.** If you want users to extend a part of the language, express
  that part as functions they can define in their own scope, not as methods on your builder.

**SDK relevance (extra depth):** this generalizes to a rule for fluent/builder APIs:

- Put the **fixed grammar / phase structure** in the chained methods (where you want control, IDE
  guidance, and the ability to reject invalid sequences).
- Put the **open vocabulary / user-extensible values** in free functions or plain arguments (where you
  want third parties to add without touching your library).
- Matchers, predicates, formatters, and codecs belong in the open half; lifecycle and phase
  transitions belong in the closed half.

#### 5.2.3 JMock 2 — what changed and why

- **The problem with JMock 1:** the constraint that **all tests using mocks must be defined in a
  subclass of the JMock library class**, purely so that Object Scoping works. That's an intrusive
  demand on user code — it consumes the single-inheritance slot and dictates test-class structure.
- **JMock 2's fix:** use **Java's instance initialization** to do the Object Scoping instead
  (the double-brace idiom: an anonymous subclass of `Expectations` with an instance initializer
  block).
  - **Cost, acknowledged:** "this does add some noise at the beginning of the expression."
  - **Benefit:** "we can now define expectations **without being in a subclass**."
- **Pattern reclassification, stated by Fowler:** the instance initializer **effectively forms a
  Closure**, making JMock 2's construct a use of **Nested Closure**.
- **Second change worth noting:** instead of using Method Chaining everywhere, JMock 2's expectations
  use **Function Sequence** to **separate the method-call part of the expectation from the
  return-value specification** (two statements in the block rather than one long chain).

**SDK relevance (extra depth) — the generalizable arc of the JMock story:**

1. **Version 1 optimized the expression itself** (terse, chained, bare functions) and paid for it with
   an **intrusive structural constraint on user code** (mandatory subclassing).
2. **Version 2 traded a little syntactic noise for removing that constraint.** Fowler presents this
   as the right trade.
3. **The general principle: a library's scoping mechanism is part of its public API contract.** How
   you get unqualified names into scope (inheritance, closures, imports, context managers, `using`
   blocks, receiver-scoped lambdas) determines how much of the user's structural freedom you consume.
   Prefer mechanisms that are **local and composable** (closures/blocks) over ones that are **global
   and exclusive** (mandatory base classes).
4. **Long chains are not automatically better than sequences of statements.** JMock 2 deliberately
   broke one chain into a **Function Sequence** to separate two distinct concerns (what is called vs.
   what is returned). Chaining should express *ordering/phase constraints*, not be applied
   reflexively.

### 5.3 CSS

Fowler's most-used example when talking about DSLs. What makes it valuable as a case study:

- **Written by non-programmers.** "Most CSS programmers don't call themselves programmers, but web
  designers." CSS is thus a good example of a DSL that is **not just read by domain experts, but also
  written by them.** (Rare — Fowler is generally skeptical of domain experts authoring DSLs.)
- **A genuinely declarative computational model.** There's no sense of "do this, then do that." You
  **declare matching rules for HTML elements**.
- **The dark side of declarative, illustrated.** Because an element can match multiple rules, CSS
  needs a **somewhat complicated specificity scheme** to decide which declaration wins. "Many people
  find it hard to figure out how these rules work — which is the dark side of a declarative model."
  (Directly echoes Ch. 7's implicit-behavior warning: alternative computational models trade
  intent-clarity for implementation-opacity, and need tracing/explanation tools.)
- **Well-focused role in a larger ecosystem.** CSS is essential but "the thought of using only it to
  build an entire web application is ludicrous. It does its job pretty well, and works with a mix of
  other DSLs and general-purpose languages inside a complete solution." — the canonical example of
  Fowler's "small DSLs composed with general-purpose languages" thesis.
- **Limited expressiveness ≠ small.** "CSS is also quite large. There's a lot to it, both in the basic
  language semantics and in the semantics of the various attributes. **DSLs can be limited in what
  they can express, but still have a lot to learn.**" — an important corrective: *limited* means
  *restricted in what it can do*, not *quick to learn*.
- **Limited error handling — a general DSL habit.** "CSS fits in with the general DSL habit of limited
  error handling. Browsers are designed to ignore erroneous input, which usually means that a CSS file
  with a syntax error **misbehaves silently**, often making for some annoying debugging."
  - *SDK relevance:* silent tolerance of malformed input is presented as a real cost, not a virtue.
    Lenient parsing shifts cost onto every future debugging session.
- **No way to create new abstractions** — "a common consequence of the limited expressiveness of
  DSLs." Concrete pain: you can't name colors in your color scheme, so you use meaningless hex
  strings; there are no arithmetic functions for manipulating sizes and margins.
- **The two standard remedies for missing abstraction, both named:**
  1. **Macros** — solve many simple problems such as named colors.
  2. **Layer another DSL on top that generates the base DSL as output.** SASS is the example:
     it adds arithmetic and variables, and uses a very different syntax (syntactic newlines and
     indentation instead of CSS's block structure).
     - **Fowler's stated conditions for the layering approach to work:** "the overlayed DSL needs to
       be similar (SASS uses the same attribute names), and **the user of the overlayed DSL usually
       also understands the underlying DSL**."
     - Cross-reference: this is exactly the remedy proposed in Ch. 6 §"Sliding into Generality" for
       avoiding language bloat.

**SDK relevance:** the "layer a generating DSL on top" pattern is the healthy alternative to growing a
config format. The two stated conditions — *stay similar to the base* and *expect users to understand
the base* — are practical acceptance criteria for any such wrapper layer (and explain why leaky
higher-level SDK wrappers succeed when they mirror the underlying API's vocabulary).

### 5.4 Hibernate Query Language (HQL)

- **Context:** Hibernate is a widely used ORM mapping Java classes onto relational tables. HQL lets you
  write queries in a **SQL-ish form but in terms of Java classes**, which can be mapped to SQL queries
  against a real database.
- **Value delivered:** people think in terms of **Java classes rather than database tables**, and they
  avoid "the various annoying differences between different databases' SQL dialects." (A portability
  and impedance-matching argument.)
- **Implementation — a three-step transformation pipeline:**
  1. HQL input text → **HQL abstract syntax tree (AST)**, using **Syntax-Directed Translation** and
     **Tree Construction**.
  2. **HQL AST → SQL AST.**
  3. **Code generator** produces SQL text from the SQL AST.
- **Tooling note:** ANTLR is used at every stage. Besides taking a token stream as input, **ANTLR can
  take an AST as input** — what ANTLR calls a **"tree grammar."** ANTLR's tree construction syntax
  builds both the HQL and SQL ASTs.
- **The generalizable pattern:**
  > input text → input AST → output AST → output text
  "is a common one with source-to-source transformation. Like in many transformation scenarios, **it's
  good to break down a complex transformation into several small transformations that can be easily
  plugged together.**"
- **The Semantic Model twist — an important nuance.** You can think of the **SQL AST as the Semantic
  Model** here: the meaning of HQL queries is defined by the SQL rendering, and the SQL AST is a model
  of SQL. **But this is an exception, not the rule:**
  > "More often than not, ASTs are not the right structure for a Semantic Model, as the constraints of
  > a syntax tree usually help more than they hinder. But for source-to-source translation, using an
  > AST of the output language makes a great deal of sense."

**SDK relevance:** two lessons. (a) Compile pipelines should be **many small, composable
transformations**, each with a well-defined intermediate representation — the same advice applies to
data pipelines, serializers, and query builders. (b) **Choose the intermediate representation to match
the output**: when your job is emitting language X, model X, not your input.

### 5.5 XAML

- **Problem it addresses:** how to define screen layout. Because it's a graphic medium, people reach
  for graphic layout tools; but greater flexibility is achieved by doing layout in code — and code is
  awkward for this, because **a screen layout is primarily a hierarchic structure, and stitching a
  hierarchy together in code is fiddlier than it ought to be.** Microsoft introduced XAML with WPF as
  a DSL to lay out UIs.
- **Form:** XML files that lay out an object structure; with WPF, a screen. Microsoft is "a fan of
  graphical design surface," so you can use a design surface, a text representation, or both.
- **Assessment of the XML choice:** XAML "does suffer from XML's syntactic noise, but **XML does work
  fairly well on hierarchic structures like this**. The fact that it bears a strong resemblance to
  HTML for laying out screens is also a plus." — i.e. XML is defensible *specifically* when the domain
  is hierarchic and a familiar analogue exists.
- **Definition — compositional vs. computational DSL** (attributed to Brad Cross; expanded in Ch. 11):
  - **Compositional DSL:** about **organizing relatively passive objects into a structure**. XAML is
    the example. "Program behavior usually doesn't depend strongly on the details of how a screen is
    laid out."
  - **Computational DSL:** the state machine example — the Semantic Model it produces "feels more like
    code than data."
  - Ch. 11 (PDF 121) adds: computational DSLs lead to a Semantic Model that **drives computation**,
    usually with an alternative computational model; that model is usually an **Adaptive Model**. "You
    can do a lot more with a computational DSL, but people often find them more difficult to work
    with."
- **A key strength, stated as such:** XAML **encourages separating the screen layout from the code that
  drives the behavior of the screen.**
- **Code generation and the generated/handwritten seam — a live example of Ch. 8's advice:**
  - A XAML document logically defines a C# class, and there **is** code generation.
  - **The code is generated as a `partial` class**; you add behavior by writing another partial class
    definition. This is precisely the "multiple files per class" solution from Ch. 8 §2.6.2, with C#
    partial classes named as the enabling feature.
  - The handwritten side **wires behavior**: for any control defined in XAML you tie an event on that
    control to a handler method in code; the code can also **refer to controls by name** to manipulate
    them.
  - **Why names matter:** "By using names like this, I can keep the references free of the structure
    of the UI layout, **which allows me to change it without having to update the behavior code**."
    - *SDK relevance:* **reference by stable name, not by structural path.** Names decouple consumers
      from layout/structure changes. Same reasoning behind IDs over XPath, keys over indices, and
      named exports over positional ones.
- **Scope note:** XAML is usually discussed with WPF/UI design, but "XAML can be used to wire up
  instances of any CLR classes, so it could be used in many more situations." (A general
  object-graph configuration language.)

#### 5.5.1 Aside: structures DSLs can define — hierarchy vs. graph

- XAML defines a **hierarchy**. DSLs can define hierarchy, "but they can also define other structures
  by mentioning names. **Indeed this is what Graphviz does using references to names to define a
  graph structure.**"
- *Principle:* **nesting expresses trees; names express graphs.** Choosing between them is a primary
  syntax-design decision.

#### 5.5.2 Other graphical-layout DSLs mentioned

- **Swiby** — a **Ruby internal DSL** for screen layout. Uses **Nested Closure**, "which provides a
  natural way of defining a hierarchic structure." (Cross-reference: Nested Closure is the
  internal-DSL counterpart to XML nesting.)
- **PIC** — "an old, and rather fascinating, DSL" from the very early days of Unix, when graphical
  screens were still unusual. You describe a diagram **in a textual format** and process it to produce
  the image. Boxes, ellipses, movement, and arrows; **connection points on shapes are referred to by
  compass points** (e.g. `A.s` = the "south" point of shape A). Fowler: "Textual descriptions like PIC
  aren't so popular in the days of WYSIWYG environments, but the approach can be rather handy."
  - *Design note worth keeping:* the compass-point convention is a nice example of a small, learnable
    domain vocabulary replacing coordinates — raising the abstraction level with almost no syntax.

### 5.6 FIT

- **What it is:** a testing framework by **Ward Cunningham**, early 2000s. **FIT = Framework for
  Integrated Test.** Aim: **describe testing scenarios in a form a domain expert can understand.**
  Extended by later tools, in particular **Fitnesse**.
- **The first interesting thing — its form.** "At the heart of FIT is the notion that **nonprogrammers
  are quite comfortable with specifying examples in a tabular form**."
  - A FIT program is **a collection of tables, typically embedded in HTML pages.**
  - **Anything between the tables — any other HTML elements — is treated as comments.**
  - **This lets a domain expert use prose narrative to describe what they want, with tables providing
    something that's processable.**
  - *This is a strong, underused design idea:* **invert the comment/code ratio.** Make prose the
    default and structured content the exception, so the artifact reads as a document to domain
    experts while remaining executable. (Compare literate programming and modern executable-spec
    tooling.)
- **Table styles — different sub-languages for different jobs:**
  - **Action fixture** — "the most program-like form... essentially a simple imperative language. It's
    simple in that **there are no conditionals or loops, just a sequence of verbs**." Verbs include
    entering values, pressing things, checking values, and awaiting conditions.
    - **The `check` verb is special: it carries out a comparison.**
    - **Feedback mechanism:** when the table is run, output HTML is created that is the same as the
      input page **except that check rows are colored green or red** depending on whether the
      comparison matched.
    - *Note:* the imperative model is used here deliberately and is kept **deliberately non-Turing-
      complete** — a clean example of "limited expressiveness" as a feature.
  - **Row fixture** — a **declarative** table defining expected tabular output data from a list of
    objects. The header line defines methods to invoke against the collection; each row corresponds to
    an object, giving expected values per column. FIT compares expected against actual, again with
    green/red coloring.
  - **Composition of the two:** an **imperative table (action fixture) to navigate the application**,
    followed by a **declarative table (row fixture) of expected results** to compare against what the
    application displays. Two computational models cooperating in one script.
- **Each table is connected to a fixture** that translates the verbs/columns into actions against the
  system. (The fixture is the adapter layer between DSL and system — the Semantic-Model-equivalent
  seam.)
- **Tables as source code:** "This use of tables as source code is unusual, but it's an approach that
  could be used more often. **People like specifying things in tabular form**, whether it's examples
  for test data or more general processing rules such as a **Decision Table**. Many domain experts are
  very comfortable with editing tables in spreadsheets, which can then be processed into source code."
  (Cross-reference to Ch. 7's decision tables — the one place Fowler expects domain experts to author.)
- **Testing as a natural DSL domain — a general claim:**
  > "Testing is a natural choice for a DSL. Compared to general-purpose programming languages, testing
  > languages often require different kinds of structures and abstractions, such as the simple linear
  > imperative model of FIT's action tables. Tests often need to be read by domain experts, so a DSL
  > makes a good choice, **usually with a DSL purpose-written for the application at hand**."
- Fowler notes considerable growth in automated testing tools with DSLs for organizing tests, many
  influenced by FIT.

**SDK relevance:** FIT and JMock together make the case that **test-facing APIs are DSLs** and should
be designed as such — different abstractions from production APIs, optimized for readability by people
who won't debug them, with **rich, in-place feedback** (FIT's green/red rows in the original document)
rather than stack traces.

### 5.7 Make et al.

- **Origin story / motivation:** trivial programs are trivial to build, but building code soon requires
  several steps. In the early days of Unix, **Make** provided a platform for structuring builds.
- **Why a Dependency Network:** "The issue with builds is that many steps are expensive and don't need
  to be done every time, so a **Dependency Network** is a natural choice of programming model." A Make
  program is several **targets** linked through dependencies; declaring that a target depends on
  others means that if any of them isn't up to date, it is built and then the dependent target is
  built. "A Dependency Network allows me to **minimize build times to a bare minimum while ensuring
  that everything that needs to be built is actually built**." Make is a familiar external DSL.
- **The most interesting thing about build languages, per Fowler, is *not* the computational model:**
  > it's "the fact that they need to **intermix their DSL with a more regular programming language**."
  - Apart from specifying targets and dependencies (a classic DSL scenario), you must also say
    **how each target gets built** — "which suggests a more imperative approach." In Make this means
    **shell script commands** (e.g. invoking the C compiler).
  - This is exactly the Ch. 6 §"Mixing In the Host Language" tension, made concrete.
- **The second structural problem: a simple Dependency Network suffers when builds get complex,
  requiring further abstractions on top of the network.** Two historical responses:
  - **Unix: Automake** — Makefiles are *generated* by the Automake system. (I.e. the "layer another
    DSL on top that generates the base DSL" remedy again — same as SASS/CSS.)
  - **Java: Ant** — external DSL with an XML carrier syntax. Fowler's parenthetical, notable for being
    a concession: XML "despite my dislike of XML carrier syntax, **did avoid Make's horrendous
    problems caused by allowing tabs and spaces in syntactic indentation.**" Ant "started simple, but
    ended up with embedded general-purpose scripts and other systems, like **Maven, generating Ant
    scripts**." (Same layering pattern, a third time.)
- **Rake** — Fowler's personal preference. Same **Dependency Network** core computational model as Make
  and Ant, but **it is an internal DSL in Ruby**. Consequences he names:
  1. You can **write the contents of the targets in a more seamless manner** (imperative build logic
     is just Ruby, contained in a **Nested Closure** after the target declaration).
  2. You can **build larger abstractions more easily** (Ruby's own abstraction facilities apply).
- **A design detail worth recording:** Rake targets can be either **tasks or files**, "supporting both
  **task-oriented and product-oriented styles of Dependency Network**." (Two distinct ways to model
  the same computational model — worth knowing as a vocabulary distinction.)
- The book itself is built with a Rakefile, which Fowler uses as the example.

**SDK relevance:** the recurring three-times-repeated pattern across Make→Automake, CSS→SASS, and
Ant→Maven is the chapter's strongest empirical claim: **when a limited declarative language needs
abstraction, the ecosystem grows a generator on top rather than extending the base.** Plan for that
from the start (make your format machine-generation-friendly), or provide the abstraction facility
yourself before someone else's generator becomes the de facto interface.

---

## 6. Cross-cutting themes across Chapters 6(tail)–10

Collected because they recur and are the most transferable material in this range.

1. **One Semantic Model, many front ends.** Stated in Ch. 6 (internal→external migration), Ch. 7
   (experiment with DSLs once the model is right), Ch. 8 (generated code as one more artifact of the
   model), Ch. 9 (workbench-as-parser to avoid lock-in), Ch. 10 (Graphviz layout/render independent of
   the parser; JMock's syntax layer over interpreter layer). **This is the book's central
   architectural seam.**
2. **Limited expressiveness is the defining, fragile property of a DSL.** Its benefits are
   comprehension, bug-resistance, reduced test surface, and security. Its failure mode is *sliding
   into generality*. Its remedy when abstraction is genuinely needed is **layering another language
   on top**, not growing the base.
3. **Alternative computational models buy intent-clarity and pay in implementation-opacity.**
   Mandatory compensating control: **a tracing/explanation mechanism.**
4. **Structure vs. constraints.** Make illegal states unrepresentable in the schema where you can;
   express the rest as **side-effect-free structural constraints** (query only, never mutate).
5. **Tooling drives representation choices.** Internal DSLs to keep the IDE; text to keep the diff/merge
   ecosystem; Embedment Helper to keep embedded code in files the tools understand; meta-models only
   when tools consume them; progressive interfaces to make autocompletion teach the language.
6. **The generated/handwritten seam.** Never edit generated code; keep it in separate files (partial
   classes, or **Generation Gap** via inheritance); prefer **one-way control flow** between the two;
   optimize generated code for readability/debuggability, not modifiability.
7. **Extension points follow from pattern choice.** Method Chaining = closed (library controls the
   vocabulary); Nested Function/Closure = open (users extend in their own scope). Choose deliberately.
8. **Scoping mechanisms are part of the API contract.** JMock 1's mandatory subclassing was the defect
   JMock 2 paid syntactic noise to remove. Prefer local, composable scoping (closures/blocks) over
   global, exclusive scoping (base classes).
9. **Reference by name, not by structure** (XAML controls, Graphviz nodes) so consumers survive
   structural change.
10. **Design for the reader you actually have.** Domain-expert-authored DSLs are rare; Fowler's named
    exceptions are **tables** (decision tables, FIT) and **CSS**. Tables win because spreadsheets are
    a tool domain experts already own.
