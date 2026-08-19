# Fowler, *Domain-Specific Languages* — Part V (Alternative Computational Models) and Part VI (Code Generation)

Study notes for Chapters 47–57. Source: Martin Fowler with Rebecca Parsons, *Domain-Specific Languages* (Addison-Wesley, 2010).

**PDF page boundaries found (rendered pages, not print page numbers):**

| Chapter | PDF pages |
|---|---|
| Part V header + Ch. 47 Adaptive Model | 332 (bottom) – 337 (top) |
| Ch. 48 Decision Table | 337 – 343 (top) |
| Ch. 49 Dependency Network | 343 – 349 (top) |
| Ch. 50 Production Rule System | 349 – 359 (top) |
| Ch. 51 State Machine | 359 – 361 |
| Part VI header | 361 (bottom) – 362 (top) |
| Ch. 52 Transformer Generation | 362 – 366 (top) |
| Ch. 53 Templated Generation | 366 – 371 (top) |
| Ch. 54 Embedment Helper | 371 – 376 (top) |
| Ch. 55 Model-Aware Generation | 376 – 385 (top) |
| Ch. 56 Model Ignorant Generation | 385 – 387 (top) |
| Ch. 57 Generation Gap | 387 – 392 |
| Index begins | 392 (bottom) |

The body of the book ends on PDF p. 392; there is no further chapter content in the 393–409 range.

---

## Part V: Alternative Computational Models — the framing idea

Fowler's premise for the whole of Part V: every programming language is designed with a particular *computational model* in mind. Mainstream languages assume an imperative model with code organized in an object-oriented way, which has proven "a suitable compromise between power and understandability." But that model is not always the best fit for a particular problem, and — this is the key observation — **"often the desire to use a DSL comes with a desire to use a different computational model."** (Fowler, DSL book, Ch. 47 "Adaptive Model", opening.)

Part V therefore has one umbrella pattern (Adaptive Model, Ch. 47) plus four concrete computational models that are typically implemented *as* Adaptive Models: Decision Table, Dependency Network, Production Rule System, and State Machine. Fowler is explicit that the list is not exhaustive and that entirely new computational models, while less common, are not unknown.

---

## Chapter 47: Adaptive Model

**Intent:** Arrange blocks of code in a data structure to implement an alternative computational model. (Fowler, DSL book, Ch. 47 "Adaptive Model", intent.)

### The concept

Most software builds *models* of the world it works with: a catalog system models products and prices; a media site models news stories, advertising, and tags. Those models may be pure data structures (data models) or may compose data with the code that manipulates it (object models). But in the ordinary case, **the flow of processing is dictated by the code**. Different data changes the details of processing, but the broad flow stays the same.

An Adaptive Model inverts this. The model itself takes the primary behavioral role. Fowler's illustration is the state machine used throughout the book: depending on which state model you load into the controller, you get a wholly different overall behavior. "Essentially, the instantiation of the state model *is* the program." There is still a general Semantic Model of "a state machine" acting as a constant factor and a constraint on what any particular state machine can do — but the program that actually executes is the *configuration* of a particular state machine.

Fowler's own definition of the boundary: **"the essence of using an Adaptive Model is the sense that you are changing the program by altering the instances and their relationships."** (Ch. 47, "How It Works".) This dissolves the boundary between code and data, which opens up new possibilities and new problems. He notes the Lisp community relishes this code/data duality, but "for many developers it's a world that's both entrancing and scary."

### How it works (mechanics)

- You define a model whose **links between elements represent the behavioral relationships of the computational model** (states → transitions → target states; rules → conditions/actions; tasks → prerequisites).
- The model usually needs references to sections of imperative code (guards, actions, conditions).
- You run the model either by **executing code over it** (procedural style — an interpreter walks the structure) or by **executing code within the model itself** (object-oriented style — the model's own objects carry the run behavior).
- Adaptive Models often take well-known graph shapes, so textbooks on algorithms and data structures are genuinely useful reference material when building them.

### Adaptive Model vs. DSL — an important distinction

The two are independent. You can have an Adaptive Model with no DSL in sight and get most of the benefits. **The DSL's role is to make it easier to program the Adaptive Model**, by providing a language in which you can describe your intentions more clearly. Fowler adds a pointed observation: "One of the hardest parts in using an Adaptive Model is to figure out what it's supposed to do — a DSL can be a big help in overcoming that." (Ch. 47, "How It Works".)

### Forms an Adaptive Model can take

- In-memory object models (all of the book's examples).
- A data structure interpreted by procedural code.
- **Stored in a database and interpreted by other applications** — common in workflow systems.

When the model lives in a relational database, Fowler usually finds it accompanied by a crude *projectional editor* — forms and fields for editing the model. Serviceable, but a DSL has real advantages: DSLs are better at giving the whole picture of a behavior (visualization techniques can also do this), and — his strongest argument for a **textual** DSL — a text DSL lets you easily put the Adaptive Model under version control. "I find it deeply troubling when core system behavior isn't kept under a proper source code control system." (Ch. 47, "How It Works".)

### Incorporating imperative code into an Adaptive Model

The book's introductory state machine was deliberately built so all behavioral elements could be described through simple data (actions just transmit a command code). More often you need real imperative code — richer actions, guard conditions on transitions. Doing that *inside* the Adaptive Model would mean complicating it with a range of imperative expressions you already have in the host language. Better to **embed regular host-language code into the Adaptive Model data structure**. Options, in Fowler's order of preference:

1. **Closures.** The most direct statement of intent; they let you embed arbitrary blocks of code into data structures easily. The big drawback is that many languages (in 2010) lack them.
2. **Command objects** (*Command* [GoF]) as the workaround. Small objects each wrapping a single method — one class for the condition, one for the action. You can cut down the number of subclasses by **parametrizing the commands** (e.g., a generic `JourneyStartCondition("BOS")` instead of a bespoke `BostonStart` class). In a language without closure support, this is where Fowler would prefer to go.
3. **Method name + reflection.** He dislikes this: "it circumvents the mechanisms of the underlying environment just a bit too much."

Nuance worth keeping: commands look like a *workaround* from the Adaptive Model's viewpoint, but **if you're populating the Adaptive Model with a DSL, commands become more attractive**. The DSL will usually wrap common cases in parameters anyway, which leads naturally to parametrized commands. Using the full expressiveness of closures in the DSL means closures in an internal DSL, or *Foreign Code* in an external DSL — "the latter, in particular, is something you should use only rarely."

### Tools (Ch. 47, "Tools")

A DSL is valuable but "not really enough to work with an Adaptive Model when it gets more complicated." Two supporting tools matter:

- **Tracing.** Because the computational model is unfamiliar, it's hard to follow what an Adaptive Model is doing. Capture how the model processed its inputs, leaving a clear log of why it did what it did. This "greatly helps answering the question, 'Why did the program do that?'"
- **Alternative visualizations.** Have the model produce a descriptive output of an instance. Graphical descriptions are often very useful — Fowler mentions Graphviz for automatically laying out node-and-arc graphs (the state diagram of the secret panel controller is his example), plus reports showing the model from different perspectives. These are "a simple equivalent of the multiple projections of a language workbench," except not editable (the cost of making them editable is usually prohibitive). **Build them automatically as part of your build process** and use them to check your understanding of how the model is configured.

### When to use it (Ch. 47, "When to Use It")

- Adaptive Model is **the key to using an alternative computational model**. Once you have an Adaptive Model for, say, a Production Rule System, you can execute any set of rules by loading them into the model. Fowler's general advice: any of the alternative computational models in this part of the book should be implemented with an Adaptive Model.
- He acknowledges that this is "somewhat of a glib answer" — it begs the question of when you'd want an alternative computational model at all. That's a **qualitative decision** with no rigorous approach. His best suggestion: try expressing the behavior in a different computational model and see if that makes it easier to think about. Doing this often means **prototyping a DSL to drive the model**, since the Adaptive Model alone may not provide enough clarity.
- Start from the common models (the other patterns in Part V); if one seems to fit, it's worth a try. Entirely new computational models are less common but not unknown. **Such a realization can grow out of the way a framework changes over time** — a framework begins by just storing data, and as more behavior worms its way in, an Adaptive Model begins to form.

**The large disadvantage — and it is large:**

- Adaptive Models "can be very hard to understand." Programmers complain bitterly about being unable to understand how one works. "It's as if a bit of magic is embedded in the program, and a lot of people find this kind of magic rather scary."
- The root cause is **implicit behavior**: you can no longer reason about what the program does by reading the code; you have to look at a particular model *configuration*. Debugging can be a nightmare. You can build tools to help — but then you spend time building tools rather than working on the true purpose of the software.
- **The sociological failure mode:** "Usually, there are a couple of people around who understand the Adaptive Model. They are big fans of it, and can be incredibly productive by using it. Everyone else, however, steers well clear." Fowler is candid that he is one of those people who finds Adaptive Models powerful and productive — but he also recognizes they can be an alien artifact to most developers. **Sometimes you have to forgo the gains**, because "it's not good to have a magic section in a system that people are fearful of touching. If the few people who understand the Adaptive Model would move on, nobody will be able to maintain that part of the system."
- His hope is that DSLs alleviate this, by making implicit behavior explicit — capturing the configuration in "a language nature" — and that as DSLs become more common, more people will be comfortable with Adaptive Models.

### Relationships

- Umbrella for **Decision Table, Dependency Network, Production Rule System, State Machine** (Chs. 48–51).
- Uses *Command* [GoF] and closures for embedded behavior; *Foreign Code* for embedded behavior in external DSLs.
- Contrasts with *projectional editor* / language workbench approaches for editing the model.
- The generated-code counterpart in Part VI is *Model-Aware Generation* (Ch. 55), which replicates a simulacrum of the model in the target environment.

### SDK relevance

- This is the pattern behind **configuration-driven frameworks, plugin registries, middleware pipelines, and workflow engines** — anything where the library's behavior is determined by a structure the user assembles rather than by control flow the user writes.
- The two "tools" recommendations translate directly into **library observability requirements**: a config-driven library must ship a tracing/explain facility ("why did this rule fire / why was this request routed here?") and ideally a dump/visualize facility for the assembled configuration. If you build a config-driven API without these, you've built the "scary magic."
- The version-control argument is an API-design argument for **text-based configuration formats over database-stored or GUI-edited configuration** for anything that constitutes core system behavior.
- The sociological warning is the honest cost-benefit for "magic" APIs (heavy annotation/decorator frameworks, DI containers, metaprogramming-driven ORMs): they are enormously productive for the people who understand them and opaque to everyone else. Weigh maintainer bus-factor, not just expressiveness.

---

## Chapter 48: Decision Table

**Intent:** Represent a combination of conditional statements in a tabular form. (Fowler, DSL book, Ch. 48 "Decision Table", intent.)

### The concept

When code composes several conditional statements, it's hard to follow exactly which combinations of conditions lead to which outcomes. A Decision Table improves understandability by laying the group of conditions out as a table: **each column is one combination of conditions and the outcome for that combination.**

The sketch: condition rows *Premium Customer*, *Priority Order*, *International Order*; consequence rows *Fee* and *Alert Rep*; six columns of Y/N/X values. Reading a column gives you the whole rule: a domestic, regular order from a premium customer costs $50 and doesn't alert a representative.

### How it works

- The table divides into two sections: **conditions** and **consequences**.
- Each **condition row** states the required value of that condition. For a simple two-value Boolean, each cell is true or false. With *n* two-value Booleans you need 2ⁿ columns to cover everything.
- Each **consequence row** represents the values of a single output; each cell is the value matching the conditions in that column. A Decision Table needs only a single consequence but can happily accept more.
- **Three-valued Boolean logic** is common, where the third value is "don't care" (X) — the column is valid for any value of that condition. Don't-care values remove a lot of repetition and keep the table compact.
- **Completeness checking is a valuable property**: because the columns are enumerable, you can determine whether all permutations of conditions have been captured and report the missing ones to the user. Some combinations genuinely cannot happen; capture those as an *error column*, or define the table's semantics so missing columns are treated as errors.
- **Beyond Booleans:** if you want arbitrary enumerations, numeric ranges, or string matches, you can capture each such case as a Boolean — but the table then needs to know about mutual exclusion (conditions like `100 > x > 50` and `50 >= x` cannot both be true). The alternative is a **single condition row for the value of `x` with ranges typed into the cells**, which "is usually easier to work with." With more complex condition values, computing all the permutations gets awkward, and it may be better to just treat an unmatched case as an error.

### Building it

As usual, Fowler advises a separate Decision Table *Semantic Model* and parser, and for both you must decide **how generic to make them**:

- A model and parser for a *single* Decision Table case: condition rows are fixed in the table code, along with the number and types of its consequences. You'd usually still want the column values configurable so it's easy to change the consequence values per combination.
- A *generic* Decision Table lets you configure the condition and consequence types. Each condition needs some way of indicating the code to run to evaluate it (a method name or a closure). For a strongly typed language you also need the type of the input and of each consequence, configured at compile time.
- Similarly for the parser: it can be fixed for one table even while configuring a generic Semantic Model. To be more flexible, you need "something akin to a simple grammar for the table structure so the parser can properly interpret the input data."

### The spreadsheet angle (a major practical point)

Decision Tables "are very simple to follow, and indeed edit, and so are particularly suited to capturing information from domain experts." Many domain experts already live in spreadsheets, so **a good tactic is to let them edit the tables in a spreadsheet and import the spreadsheet into the system**. Options, from crude to sophisticated:

- Save as **CSV** — crude but often effective, and it works because the table is pure values with no formulae.
- **Interoperate with the spreadsheet program** — e.g., start up and talk to a running instance of Excel.
- Use the spreadsheet's own programming language to receive, edit, and transmit decision table data to a remote program.

### When to use it (Ch. 48, "When to Use It")

- Very effective for capturing the results of a **set of interacting conditions**. Communicates well to both programmers and domain experts, and the tabular form lets domain experts manipulate it with familiar spreadsheet tools.
- **Biggest disadvantage:** it takes some effort to set things up so tables can be edited and displayed easily. But "this effort is usually quite small compared to the communicative benefit they provide."
- **Complexity ceiling:** "Decision Tables can only handle a certain degree of complexity — no more than what you can capture in a single (if complex) conditional expression. If you need to combine multiple kinds of conditionals, consider a *Production Rule System*."

### What the example demonstrates (C#, "Calculating the Fee for an Order")

Concepts, not code:

- A **generic** `DecisionTable<TIn, TOut>` parametrized by the input type (an order) and output type (a fee result object wrapping several output values). Conditions are parametrized by the input type; columns by the output type.
- Each condition is a description plus **a closure/delegate predicate** — this is exactly the "embed imperative code into the Adaptive Model" technique from Ch. 47.
- The **three-valued Boolean implemented polymorphically** — separate subclasses for True, False, and DontCare, each with a `Matches` method. The crucial design note: this is deliberately a *matches* method, not an *equals* method, **because it is not symmetric** — don't-care matches true, but true does not match don't-care. A "condition block" (one column's worth of values) matches another by pairwise matching its list of three-valued Booleans. This matching of condition blocks is the core mechanism.
- **Running the table:** evaluate all conditions against the input to produce a condition block, scan the columns for the first match, return its result; if nothing matches, throw a missing-permutation exception. Adding a duplicate column is also rejected.
- **Completeness checking:** generate every possible permutation for the given number of conditions and report those not matched by any column. Fowler generated permutations via a two-dimensional matrix and then pulled each column out as a permutation, with a general lesson attached: *"I'm quite happy to use the data structure that makes it easiest to write some code and then transform the result into the data structure I actually want to consume."* He compares it to changing coordinate systems in engineering — transform the problem into a system where it's easy to solve, solve it, transform back.
- **The parser** operates against a tiny `ITable` abstraction (`cell(row, col)`, `RowCount`, `ColumnCount`) rather than being coupled to any particular spreadsheet mechanism. It is written "in the spirit of *Delimiter-Directed Translation* but using rows and columns instead of a stream of delimiter-separated tokens." A nice defensive touch: the parser **verifies the condition row names** against what it expects, so that a table whose rows get reordered or renamed fails loudly instead of silently mis-parsing.

### Relationships

- An instance of *Adaptive Model* (Ch. 47).
- Escalate to *Production Rule System* (Ch. 50) when a single conditional expression is no longer enough.
- Parsing borrows the spirit of *Delimiter-Directed Translation*.

### SDK relevance

- The natural shape for **pricing matrices, permission/authorization matrices, feature-flag combinations, and rate/discount schedules** exposed through a library. If your API takes five booleans and returns a policy, a decision table is likely a better public surface than five nested `if`s or an options object.
- **Completeness checking is a genuine API feature.** A table-based API can tell the caller "you have not specified what happens when A and B are both true" at configuration time rather than failing in production. That's a validation guarantee an imperative conditional cannot offer.
- The **spreadsheet round-trip** is a real integration design: if non-engineers own the values, the library should offer a CSV/spreadsheet ingestion path, and it works precisely because the table contains only values.
- The generic-vs-specific decision (fixed conditions in code vs. fully configurable conditions and types) is the classic library-design tension between a **narrow, statically typed, easy-to-use API** and a **general, dynamically configured, harder-to-use one**. Fowler doesn't declare a winner; he insists you make it consciously.

---

## Chapter 49: Dependency Network

**Intent:** A list of tasks linked by dependency relationships. To run a task, you invoke its dependencies, running those tasks as prerequisites. (Fowler, DSL book, Ch. 49 "Dependency Network", intent.)

### The concept

The canonical example is a build: to run tests you need an up-to-date compilation; to compile you need code generation done first. A Dependency Network organizes functionality into a **directed acyclic graph (DAG) of tasks and their dependencies**. When you request a task, the system first finds the tasks it depends on and ensures those are executed first if needed. Navigating the network guarantees all prerequisite tasks for the requested task are executed, and — critically — that **even if a task is reached more than once via different dependency paths, it is executed only once.**

### Task-oriented vs. product-oriented (the central design axis)

- **Task-oriented:** the network is a set of *tasks* with dependencies between tasks. "We have a code generation task and a compilation task, with the compilation task depending on the code generation task."
- **Product-oriented:** focus on the *products* you want to create and the dependencies between them. "We have an executable which is created by a compilation process, and some generated source files that are created by code generation. We then state the dependencies by saying that the code-generated source files are a prerequisite to building the executable."

Fowler admits the difference "may seem oversubtle at the moment" but it becomes consequential (see below).

### How it runs

You request a task (process-oriented) or a product (product-oriented); either way the requested thing is the **target**. The system finds all the prerequisites of the target, then the prerequisites of the prerequisites, transitively, until it has the full list. It invokes each task, using the dependency relationships to ensure no task is invoked before its prerequisites. No task is executed more than once even if the traversal reaches the same item several times.

His non-build example: a magical-potion production facility. `healthPotion → clarifiedWater, octopusEssence`; `octopusEssence → clarifiedWater, octopus`; `clarifiedWater → dessicatedGlass`. `clarifiedWater` sits on two paths into `healthPotion` and must run only once.

He also observes that the product-oriented framing works for information products as well as physical ones — a *production plan* for a substance is a product too, and you don't want to compute one unless you need it.

### The two failure modes

- **Missed prerequisite** — the most serious error. You end up with an erroneous answer, and it's nasty because it's hard to spot: "everything looks like it works correctly but the data is all wrong because we didn't get a prerequisite."
- **Unnecessary build** — e.g., calculating clarified water twice. In most cases this just means slower execution, "as the tasks are often idempotent. It can cause more serious errors if they aren't."

### Last-modified dates, and invoke vs. execute

A common feature (particularly in the product-oriented case) is that **each product tracks when it was last updated**. When you request a product, the system only actually executes the process if the output product's last-modified date is earlier than any of the prerequisites'. For this to work, the prerequisites must be invoked first so they can rebuild if necessary.

Fowler draws an explicit distinction that is easy to miss:

> **Every transitive prerequisite is *invoked*, but a prerequisite is only *executed* if it's necessary.**

Invoking `octopusEssence` invokes `octopus` and `clarifiedWater` (which in turn invokes `dessicatedGlass`); once all the invocations have finished, `octopusEssence` compares last-modified dates and only executes itself if a prerequisite is now later than it is.

In a **task-oriented** network, last-modified dates are often not used at all. Instead each task tracks whether it has already executed during the current target request, and executes only on the first invocation.

**The argument for product-orientation:** it is easier to work with persistent last-modified dates in the product-oriented style, and that "is a strong reason to prefer the product-oriented style to the task-oriented." You *can* use last-modified information in a task-oriented system, but then each task has to handle that responsibility itself. Product-orientation with last-modified dates lets the *network* decide on execution.

**The price:** "This capability doesn't come for free; it only works if the output will always be the same if none of the prerequisites change. **Thus everything that could make a change to the output needs to be declared in prerequisites.**"

### Task vs. product in real build tools

The distinction surfaces directly in build automation: **Unix Make is product-oriented** (its products are files); **Ant (Java) is task-oriented**. One real problem with product-oriented systems is that **there isn't always a natural product** — running tests is the classic case. You need to make something like a test report to keep track of things. Sometimes the outputs exist only to fit into the dependency system; Fowler's example of such a pseudo-output is a **touch file** — an empty file that exists only for its last-modified date.

### When to use it (Ch. 49, "When to Use It")

- Works for problems where you can **divide the computation into tasks with well-defined inputs and outputs**.
- The ability to execute only the tasks that are needed makes it suitable for **resource-intensive tasks, or tasks that take an effort to get going — such as remote operations.**
- As with any alternative model, it's **tricky to debug** when things go wrong, so it's important to **log invocations and executions** so you can see what's going on.
- That debugging concern, coupled with the desire to only execute when needed, leads to a concrete recommendation: **prefer relatively coarse-grained tasks for the network.**

### What the example demonstrates (C#, "Analyzing Potions")

- The domain: potion recipes are tweaked constantly; the quality-control analyses (a substance's "MacGuffin Profile") are **expensive and time-consuming**, so you can't redo them per potion — only when the recipe changes. And because every substance in the manufacturing chain affects characteristics downstream, changing an upstream substance invalidates all downstream analyses that use its output. This is a textbook motivation for caching-with-invalidation, expressed as a Dependency Network: each substance has its inputs as prerequisites for determining its profile.
- **The DSL** is internal C# using *Object Scoping* and a *Class Symbol Table*: substances are declared as fields of a script class, and the body reads `healthPotion.Needs(octopusEssence, clarifiedWater);`. Reflection over the script class's fields populates the builders, and the substance builders are named `Substances` "so that the DSL reads better" — a small but characteristic naming-for-fluency move.
- **The Semantic Model** is a graph of substances, each holding a list of input substances, a recipe (with a timestamp), and a profile (with a timestamp).
- **The behavior lives in the getter.** Asking for a substance's profile first passes the invocation back along the inputs so that every transitive input is invoked; then each substance checks whether it is out of date and recalculates only if necessary. Out-of-date means: no profile at all, *or* the profile predates the recipe, *or* any input was updated after the profile's timestamp.
- The invoke/execute distinction in practice: "If a substance appears more than once in the input chain, it will be invoked many times, but it only calculates its profile once. This is essential, since the profiling service call is expensive."

### Relationships

- An instance of *Adaptive Model* (Ch. 47).
- Populated by an internal DSL using *Object Scoping*, *Class Symbol Table*, *Method Chaining*.

### SDK relevance

- This is the model behind **build tools, task runners, and incremental pipeline libraries** (Make, Ant, Rake, Gradle, Bazel, and modern JS bundler/monorepo task graphs). If you are designing such an API, the task-vs-product decision determines whether your library or your users own staleness logic — and Fowler's verdict is that product-orientation lets the framework own it.
- **"Everything that could make a change to the output needs to be declared in prerequisites"** is the fundamental correctness contract of any incremental/caching API. It's the reason modern build systems demand full input declarations (including tool versions and env vars) and why hidden inputs produce the "missed prerequisite" silent-wrong-answer failure.
- The **touch-file / pseudo-output** trick is the standard workaround when your API is product-keyed but a task has no natural artifact (test runs, deploys, lint checks).
- **Idempotence of tasks is what makes the "unnecessary build" error benign.** If you expose a task API, document idempotence expectations — non-idempotent tasks turn a performance annoyance into a correctness bug.
- **Coarse-grained tasks** is good default guidance for public task APIs: fine granularity multiplies both the bookkeeping overhead and the debugging surface.

---

## Chapter 50: Production Rule System

**Intent:** Organize logic through a set of production rules, each having a condition and an action. (Fowler, DSL book, Ch. 50 "Production Rule System", intent.)

### The concept

Many situations are naturally thought of as a set of conditional tests:

- **Validation** — each validation is a condition where you raise an error if the condition is false.
- **Qualification/eligibility** — a chain of conditions where you qualify if you make it all the way up the chain.
- **Diagnosis** — a series of questions, each leading to new questions and hopefully to the root fault.

The sketch is a set of `if <conditions> then <consequence>` rules about a club-membership candidate, deliberately written so that the consequence of one rule ("candidate is of good stock") is the condition of another — showing inference chaining.

A Production Rule System implements a set of rules, each with a condition and a consequential action. The system runs the rules on the data it has **through a series of cycles**; each cycle identifies the rules whose conditions match, then executes those rules' actions. "A Production Rule System is usually at the heart of an expert system."

### How it works

The rule structure is simple: a Boolean condition and an action. The action can be anything, **but may be constrained by context** — e.g., if the system is only doing validation, actions may only raise errors, so an action just specifies which error to raise and what data to provide with it.

The complex part is **deciding how to execute the rules.** Doing this for general expert systems is very involved, which is why a whole community and a market of tools exist. But — a recurring Fowler theme — "the fact that a general Production Rule System is very complicated doesn't mean that you can't build a simple Production Rule System for limited cases."

**The rule engine.** A Production Rule System puts all control of rule execution into a single component: a *rule engine*, *inference engine*, or *scheduler*. A simple engine runs a series of **inference cycles**:

1. Run all the conditions of the available rules.
2. Each rule whose condition returns true is **activated**.
3. Activated rules go onto a list called the **agenda**.
4. When condition checking is done, the engine executes the actions of the rules on the agenda. Executing a rule's action is called **firing** the rule.

**Firing sequence** can be determined several ways:

- **Arbitrary sequence** — the simplest. The order in which rules are written doesn't determine the order of firing. "This can help keep the computation simple."
- **Definition order** — always fire in the order the rules are defined. Email filter rules are the classic example: you define filters so the first one that matches processes the email and later matching rules never fire.
- **Priority** (in expert-system circles, **salience**) — the engine picks the highest-priority rule on the agenda first. **Fowler's warning: "Using priorities is often considered a smell; if you find yourself using priorities a lot, you should reconsider whether a Production Rule System is the appropriate computational model for your problem."**

Another engine variation: whether to re-check rules for activation **after each rule fires**, or to fire all the rules on the agenda before rechecking. Depending on how rules are structured, this may change system behavior.

**Rule sets.** Rule bases usually contain distinct groups, each a logical part of the overall problem. Divide rules into separate rule sets and evaluate them in a particular order — e.g., run the basic-data-validation rule set first, and only if there are no errors, run the qualification rule set.

### Chaining

- **No chaining** — validation rules are the simplest kind. You scan all the rules; those that fire add an error or warning to some log or *Notification*. **One cycle of activation and firing is enough**, because the actions don't change the state of the data the system works with.
- **Forward chaining** — when rule actions *do* change the state of the world, you must reevaluate the rule conditions to see if any have become true, adding them to the agenda. "You start with some facts, use rules to infer more facts, these facts activate more rules, which create more facts, and so on. The engine stops only when there are no more rules on the agenda."
- **Backward chaining** — work the other way: begin with a goal, examine the rule base to see which rules have actions that would make this goal true, then take those rules and make their conditions subgoals, finding further rules that support them. "It is less common in simple Production Rule Systems as it's much more involved to get a simple case working." The chapter focuses on forward-chaining or nonchaining engines.

### Contradictory inferences (the hard problem)

"One of the great advantages of rules is that you can state each rule independently and let the Production Rule System figure out the consequences. But this strength comes with a problem. What if you get chains of inferences that contradict each other?" His example: a military reenactment club where one set of rules says an over-18 American citizen with a musket may join the revolutionary army, and a separate rule elsewhere says British citizens may only join the tyrants' army. A dual citizen activates both.

**The biggest danger is that you may not notice this at all.** If the consequence is setting a Boolean, whichever rule runs last wins. Without a defined sequence or priority values, this can lead to an incorrect inference, "or even different inferences depending on hidden qualities in the rule execution sequence."

Two broad approaches:

1. **Design the rule structure to avoid contradictions.** Ensure the way the rules run avoids contradiction — through the way rules update data, by organizing rule sets, or by playing with priorities. His concrete convention: **start with all eligibility conditions set to false and only allow them to be changed to true (monotone).** That forces anyone wanting to exclude the Brits to write the rule a different way, "surfacing the potential contradiction while writing the rules." Caveat: "You have to be careful because a mistake can sneak in a rule that will potentially subvert the design."
2. **Record all inferences in a way that tolerates contradiction**, so you can spot a contradiction if you get one. Instead of a Boolean for eligibility, create a separate **fact object** whose key is `eligibilityForRevolutionaryArmy` and whose value is a Boolean. After running the rules, look for all facts with the key you care about — you can then spot facts with the same key but different values. The *Observation* pattern [fowler-ap] is one way to handle this.

Also: **beware circles in the rule structure** where multiple rules keep each other firing endlessly — from contradictory rules that keep arguing with each other, and from positive feedback loops. Dedicated Production Rule System tools have their own techniques for these problems.

### Patterns in rule structure

From limited observation, Fowler sees three recurring shapes:

- **Validation** — common and simple. All rules have a simple consequence (raise a validation error) and there is little or no chaining. "I suspect most people who work seriously with Production Rule Systems wouldn't consider these to be rule systems since they are so simple — and, certainly, it seemed an overkill to me to use a specialized rules tool for something like this. However, this kind of simple structure is a nice one for you to write yourself."
- **Eligibility** — somewhat more involved. Assessing whether a candidate is eligible for one or more agreements (which insurance policy someone qualifies for, which discount scheme an order falls into). Rules structure as **a progression of steps where lower-level rules lead to higher-level inferences**. You can avoid contradictions by keeping all the inferences positive, "perhaps with some separate route for disqualifications."
- **Diagnostic** — observe problems and determine the root cause. "Here, you're much more likely to get contradictions, so having something like *Observation* is more important."

### When to use it (Ch. 50, "When to Use It")

- Natural choice **when behavior feels like it is best expressed as a set of if-then statements**. "Indeed, just writing control flow like that is often a good starting point for evolving into a Production Rule System."
- **The big danger: Production Rule Systems are seductive.** A small example is easy to understand and demos well to nonprogrammers. "What isn't clear from simple demos is that it may become very hard to reason about what a Production Rule System is doing as it gets bigger, particularly if you are using chaining. This can make debugging very difficult."
- **Rule engine tools exacerbate this.** "It's very easy to stretch a tool — to use it in lots of places without realizing how difficult it is to modify until you've already built something too large." Hence an argument for **building something simple yourself**, which you can tune to your needs and use to learn about the domain and how a Production Rule System fits it; once you've learned more you can evaluate whether it's worth replacing your simple system with a tool.
- His summary judgement, quoted because it's unusually blunt: **"I'm not saying that rule engines are always a bad idea, although I've yet to see one that's worked well. What is important is that you should treat them with caution and understand what you are getting into when you use them."**

### What the examples demonstrate

**Example 1 — Validations for club membership (C#).** Validations are the simple, unchained case. A validation engine holds a list of validation rules; running it produces a *Notification* collecting all failures rather than throwing on the first. The basic rule is a predicate plus a message. The internal DSL uses *Object Scoping* (a superclass so the script can call `Validate` bare) and *Method Chaining* (`Validate("description").With(predicate)`), with a progressive interface for the chained step. Fowler notes the progressive interface "feels a bit of overkill" for a single method, "but I think the interface name helps communicate what the parser is looking for."

*Evolving the DSL* (a sub-section worth its own attention). After writing several null checks by hand, you realize the null-check logic belongs in the rule so the script just names the property. Two successive designs:

- **Property name as a string plus reflection** — `MustHave("University")`. Works in many languages.
- **Lambda expression** — `MustHave(p => p.Nationality)`. In a statically typed environment like C# with good tool support, this "capture[s] the property name with a mechanism that has its place within C#, so we can use autocompletion and static checking." He passes an *expression* of the lambda rather than the plain lambda so that he can print the text of the code in the error message when validation fails.

**The design principle stated in this example is one of the most transferable in the chapter:**

> "I want to stress here that I didn't need to change the *Semantic Model* to support this. Instead, I could easily put this code in the builder... It's often an easy reflex to put this kind of logic in the builder, but I urge you not to fall for it. If I put the logic in the Semantic Model, it will be able to make a much better use of the information, since it knows what it's doing." (Ch. 50, "Evolving the DSL".)

His example of "better use": a Semantic Model that knows a rule is a not-null check can *generate JavaScript* for that validation to embed in a form; a builder that has already flattened it into an anonymous predicate cannot. And even absent such a need: "my preference is to put smarts in the Semantic Model as much as possible. It isn't any more work than putting it in the builder, but it keeps the knowledge of the rules where it's most useful."

**Example 2 — Eligibility rules with forward chaining (C#).** Top-level rule: a candidate is worthy of interview if of good stock *and* a productive member of society; lower-level rules establish "good stock" (father is a member, or militarily accomplished, or Oxbridge) and "productive" (nationality plus income thresholds). Conceptual points:

- **Rules are open-ended.** "I can easily add new rules that say what it means to be of good stock, without altering the rules that are already in place." The downside is stated just as plainly: "there's no single spot in the rule base text where I can be sure of finding *all* the conditions." Mitigation: **a tool capable of finding all the rules that have a consequence of calling `MarkOfGoodStock`.**
- **The data class is deliberately monotone**: all properties are Booleans that start `false` and can only be changed to `true`. "This enforces some structure in the rules system to avoid undetected contradictions."
- **The engine** activates rules, then loops {fire the agenda, re-activate} while the agenda is non-empty — a minimal forward-chaining cycle. Activated rules are *removed* from the available list so they cannot be activated twice; fired rules move to a **fired log**, which "later I can use... to provide a trace for diagnostic purposes."
- **Null-safety moved into the engine.** Activation traps null-reference exceptions and treats them as a failure to activate, so a rule author can write `anApplication.Candidate.Father.IsMember` with no null checking — "moving that responsibility to the model."
- **DSL patterns used:** *Function Sequence* for the list of rules; *Method Chaining* for the `When`/`Then` clauses; *Nested Closure* for the contents of the condition and action; *Object Scoping* via a superclass; progressive interfaces (`WhenParser` → `ThenParser`) to enforce clause order.

### Relationships

- An instance of *Adaptive Model* (Ch. 47).
- The escalation target from *Decision Table* (Ch. 48) when you must combine multiple kinds of conditionals.
- Uses *Notification*, *Observation* [fowler-ap], *Function Sequence*, *Method Chaining*, *Nested Closure*, *Object Scoping*.

### SDK relevance

- **Validation libraries, policy/authorization engines, eligibility and pricing-rule services, alerting rules, and lint/rule frameworks** are all this pattern. Fowler's "validation is the simple, chain-free case that you should just write yourself" is directly applicable: most validation DSLs do not need a rule engine.
- **"Put smarts in the Semantic Model, not the builder"** is arguably the single most reusable API-design rule in these chapters. For fluent/builder APIs, resist collapsing user intent into an opaque closure at the builder boundary. Keep the *kind* of thing the user declared (a not-null check, a range check) as a first-class model object, and you retain the ability to serialize it, render it in another language, document it, introspect it, or optimize it. Collapsing to a lambda is a one-way door.
- **The fired-log/agenda is an API surface, not an implementation detail.** Anything rule-driven needs an explain/trace facility — echoing the tracing advice in Ch. 47.
- **Open-endedness vs. discoverability** is the core tradeoff of any plugin/rule-registration API: users can extend without touching existing code, but no single place tells you the full behavior. Fowler's answer is tooling (find-all-rules-with-this-consequence), which maps to introspection APIs and registry-dumping commands in modern SDKs.
- **Monotone state design** (fields start false, only ever set true) is a cheap, general technique for making order-independence safe in any system where independent extensions write to shared state.
- **Moving null-safety into the engine** is a good example of the library absorbing incidental complexity so user-authored predicates stay declarative.
- The warning about tool creep — easy to adopt, hard to modify once large — applies to adopting *any* heavyweight rules/workflow engine as a dependency.

---

## Chapter 51: State Machine

**Intent:** Model a system as a set of explicit states with transitions between them. (Fowler, DSL book, Ch. 51 "State Machine", intent.)

### The concept

"Many systems react to stimuli differently, depending on some internal property. Sometimes it's useful to classify these different internal states and describe both the differences in response and what causes the system to move between these states. A State Machine can be used to describe and perhaps control this behavior."

The sketch is the trivial one: `On` and `Off`, with `switchDown`/`switchUp` events and `/closeCircuit`, `/openCircuit` entry actions.

State Machines are used throughout the book (the secret panel controller is the running example), and Fowler is upfront that "the degree to which a State Machine is used varies with the situation, as does the form of State Machine in use."

### The order example and the *machine state* distinction

To explore a less clear-cut case, he models an order: created → items freely added/removed or cancelled → payment provided → eligible to ship; before shipping you can still add/remove items or cancel; once shipped you can't do any of that. States: `collecting`, `paid`, `shipped`, `cancelled`.

This sets up a distinction that is easy to gloss over but is the chapter's most useful idea:

> In general use, "the state of an object" means the combination of the values of its properties — so removing an item from an order changes its state. But the state machine diagram doesn't reflect all these possible states; it only shows a few. **"These are the states that are interesting in terms of the model, in that they affect the behavior of the system. I'll refer to this smaller set of states as *machine states*."** So while removing an item changes the state of the order, it doesn't change its machine state. (Ch. 51, "How It Works".)

**And the judgement call that follows from it — this is the "when NOT to build one" advice:**

> "This state model is a useful way of thinking about the behavior of the order, but this doesn't mean that we want a state machine model in our software."

- The model tells us we need a check in the `cancel` method verifying we're in the appropriate state — but that can simply be a **guard clause** in `cancel`.
- Tracking which machine state the order is in could be a status field, "but it could also be completely derived" — you could determine the `paid` state by checking whether the payment authorization amount is greater than or equal to the total cost of the order.
- **"The diagram may still be a useful way to visualize how the order works, but you don't need the model to be manifest in the software."**

### Common elements and variations

- The essence: **multiple states the machine can be in**; **multiple transitions defined on each state**, each triggered by an **event** and moving the machine to a **target state** (often, but not necessarily, a different state). "The resulting behavior of the machine is the definition of the states and the events that trigger the movement between states."
- Multiple transitions can share the same target and still be separate transitions (add item and remove item both return to `collecting`).
- **Unhandled events:** "A general question with state machines is how they react to an event that isn't defined on the state that the machine is currently in. Depending on the application, such an event may be an error, or it may be safely ignored." (A design decision the model must make explicit.)
- **Guarded transitions:** Boolean conditions on transitions — in `paid`, an add-item event goes one way if there's enough money and another if not. **"The Boolean conditions on the transitions should not overlap, otherwise the state machine won't know where to go."** Guards don't have to appear on all State Machines; the introductory example has none.
- **Binding actions (making it an Adaptive Model).** A state diagram alone is a **passive model** — it describes states and events but doesn't invoke actions that change the system. To have an *Adaptive Model* with a State Machine you need a way to bind actions into the machine. Two sensible places:
  - **On transitions** — the action executes whenever the transition is taken.
  - **On states** — most commonly invoked on *entry* to the state; you also see actions bound to *exits* from a state.
  - Some machines also allow **internal actions**, invoked when an event is received in that state — "like a transition back to itself, but perhaps without triggering any entry actions again."
- **Fowler's guidance on choosing:** "Different action-binding approaches suit different problems and different personalities. I don't have any strong guidelines to offer, other than to keep it as simple as it can reasonably be to model your behavior. Many implementations of state machine techniques have gone for the maximum expressiveness of the machine — such as the very expressive state machine models used by the UML. But small state machines suitable for DSLs can often work well with much simpler models."

### When to use it (Ch. 51, "When to Use It")

Refreshingly honest:

> "I have that horrible feeling when I know that almost the only thing I can say is that you should use a State Machine when the behavior you're specifying feels like a State Machine — that is, when you have a sense of movement, triggered by events, from state to state. In many ways, the best way to see if a State Machine is appropriate is to try sketching one on paper, and if it fits well, to try it in action."

One concrete danger area, drawn from the book's earlier language-theory material: **State Machines are limited to parsing regular grammars** — they can't handle matching arbitrarily nested parentheses. "If your behavior has anything like that, you may run into the same problem."

### What the example demonstrates (Java, "Secret Panel Controller")

The book's running example uses a single Semantic Model described in the Introduction. Notably it is deliberately **simple**: no guarded transitions; actions bound to **state entry** only; and the actions "don't involve executing an arbitrary code block but only sending a numeric code message." Fowler flags why: "This simplifies the state machine model and the DSLs to control it (which is very important for an example like this)." That is, the example's restraint is pedagogical — real machines often need richer actions, which is where Ch. 47's guidance on embedding closures/commands comes in.

### Relationships

- An instance of *Adaptive Model* (Ch. 47) — but only once actions are bound; a pure state diagram is passive.
- The target model for most of the code-generation examples in Part VI (Chs. 52, 53, 55, 56).
- Constrained by the regular-grammar limit discussed in the book's language-theory chapter.

### SDK relevance

- **Machine state vs. object state is a public-API distinction.** When you expose a status/lifecycle enum on a resource, you are choosing which states are behaviorally interesting. Exposing too many states leaks internals; exposing a derived state (Fowler's "paid = authorization ≥ total") avoids a redundant, drift-prone field. Deciding whether a status is *stored* or *derived* is a real API-design choice.
- **"You don't need the model to be manifest in the software"** is a caution against over-modeling. A guard clause in `cancel()` is often the whole of what the state machine buys you. Reach for an explicit state machine model when you need the behavior to be *configurable*, *inspectable*, or *generated* — not merely because the domain has states.
- **Non-overlapping guards** is an invariant your API should validate at configuration time, not discover at runtime.
- **Unhandled-event policy (error vs. ignore) must be an explicit, documented option**, not an accident of implementation. Ch. 55's generated C machine chooses "ignore unknown events; shrug if no transition" — a deliberate, documented choice.
- State machines are one of the two models in Part V that most commonly get **exposed as an API-configured model** (the other being Production Rule System): workflow/order-status engines, connection/session lifecycle libraries, retry/circuit-breaker state, protocol implementations. The action-binding decision (entry action vs. transition action vs. internal action) is exactly the callback-surface design question for such a library — and Fowler's advice is to pick the simplest binding that models your behavior rather than copying UML's maximal expressiveness.

---

## Part VI: Code Generation — the framing and design axes

Part VI contains six patterns organized along **three independent design axes**:

1. **How you write the generator:** *Transformer Generation* (Ch. 52) vs. *Templated Generation* (Ch. 53). Roughly: code that emits text vs. text with holes in it.
2. **What the generated code looks like:** *Model-Aware Generation* (Ch. 55) vs. *Model Ignorant Generation* (Ch. 56). Roughly: generated code that configures a runtime model vs. generated code with the logic inlined into control flow.
3. **Hygiene patterns that cut across both:** *Embedment Helper* (Ch. 54) — keep foreign code out of templates and grammars; *Generation Gap* (Ch. 57) — keep generated code out of handwritten files.

The axes are genuinely orthogonal — Fowler pairs Transformer Generation with Model-Aware Generation in one example, and Templated Generation with Model Ignorant Generation in another, and points out the combinations explicitly.

---

## Chapter 52: Transformer Generation

**Intent:** Generate code by writing a transformer that navigates the input model and produces output. (Fowler, DSL book, Ch. 52 "Transformer Generation", intent.)

### The concept

Write a program that takes the *Semantic Model* as input and produces source code for the target environment as output. The generator is ordinary code — loops over model elements, string formatting, writes to an output stream. The sketch shows a method that iterates the machine's events and writes a `declare_event(...)` line for each.

### Input-driven vs. output-driven (the key conceptual tool)

Fowler frames every routine in a transformer as one of two kinds:

- **Output-driven transformation** "starts from the required output and dives into the input to gather the data it needs as it goes." Generating a web page from a product catalog output-driven looks like: `renderHeader(); renderBody(); renderFooter();`.
- **Input-driven transformation** "walks the input data structure and produces output": `foreach product { renderName(product); foreach photo { renderPhoto(photo) } }`.

"Often, transformers use a combination of the two. I seem to regularly run into situations where the outer logic is output-driven, but it calls routines that are more input-driven. The outer logic describes the broad structure of the output document, dividing it into logical sections, while the inner section produces output driven by a particular kind of input data. **In any case, I find it useful to think of each routine in the transformation as either input-driven or output-driven and to be conscious of which I'm using.**" (Ch. 52, "How It Works".)

### Multistage transforms

Many transformations go directly from Semantic Model to target source, but for more complicated cases it's useful to break the transformation into multiple steps:

- A **two-step transform** walks the input model and produces an **output model** — a model, not a text, but oriented towards the generated output. A second step walks the output model and produces the output text.
- Useful when the transform is complicated, **or when you have multiple output texts to produce from the same input that share some characteristics.** With multiple output texts, the first-stage transform produces a single output model with the common elements; the differences between the output texts go in varying second stages.
- **You can mix techniques across stages** — Transformer Generation for the first stage and *Templated Generation* for the second.

### When to use it (Ch. 52, "When to Use It")

- **Single-stage Transformer Generation** is a good choice when the output text has a **simple relationship with the input model and most of the output text is generated.** In that case it's very easy to write "and doesn't require introducing a templating tool."
- **Multi-stage** is very useful when the input/output relationship is more complex, "as each stage can handle a different aspect of the problem."
- **Pairs naturally with Model-Aware Generation:** "If you use *Model-Aware Generation*, you can usually populate the model with a simple sequence of calls, which is easy to generate with Transformer Generation."

(The implicit contrast, stated fully in Ch. 53: when the output is mostly *static* text with occasional simple dynamic bits, use Templated Generation instead.)

### What the example demonstrates (Java generating C, "Secret Panel Controller")

- The pairing with *Model-Aware Generation* is explicit: "Using Model-Aware Generation often goes with Transformer Generation as the separation between generated code and static code is clear, allowing any sections of generated code to have very little static code."
- The generated output is a flat `build_machine()` function consisting of `declare_event` / `declare_command` / `declare_state` / `declare_action` / `declare_transition` calls — i.e., **the generated code is nothing but a sequence of API calls against a hand-written runtime model.** This is what makes the generator trivially simple.
- The generator's structure is "a typical output-driven outer routine of a transformer": write header, generate events, commands, state declarations, state bodies, reset events, write footer. Each sub-routine is input-driven, iterating a model collection.
- A real constraint surfaces: **all states must be declared before any transitions**, because forward-referencing a state is an error in the target. The output-driven outer routine is where that ordering constraint is enforced — a good illustration of why the outer structure follows the output's requirements, not the model's shape.
- Also demonstrates generating a **comment containing dynamic data** (`/* body for %s state */`) — generated code carrying orientation for human readers.

### Relationships

- Alternative/complement to *Templated Generation* (Ch. 53); the two can be mixed within a multistage transform, and `printf`-style usage means they intermix at fine grain too.
- Pairs naturally with *Model-Aware Generation* (Ch. 55).
- Consumes the *Semantic Model*.

### SDK relevance

- This is how most **client-SDK generators** work (spec model in, source out). The input-driven/output-driven distinction is a practical way to organize such a generator: the file skeleton (imports, class shell, footer) is output-driven; the per-operation and per-model-type sections are input-driven.
- **The multistage transform with an intermediate output model is the standard answer to multi-language SDK generation.** One first stage normalizes the spec into a language-agnostic "output model" (resolved types, naming, pagination shape); per-language second stages render it. That is exactly Fowler's "multiple output texts from the same input that share some characteristics."
- The Transformer/Templated choice for a generator maps to: **is the generated file mostly boilerplate scaffolding (template) or mostly synthesized structure (transformer)?** Most SDK generators end up doing both, and Fowler's advice is to be conscious of which mode each routine is in.

---

## Chapter 53: Templated Generation

**Intent:** Generate output by handwriting an output file and placing template callouts to generate variable portions. (Fowler, DSL book, Ch. 53 "Templated Generation", intent.)

### The concept

The inverse framing to Transformer Generation: **write the output file you want, then insert callouts for the bits that vary.** A template processor combines the template file with a *context* that fills the callouts, producing the real output file.

Fowler roots it historically: "Templated Generation is a very old technique, familiar to anyone who has used mail-merge facilities in a word processor." It's very common in web development (dynamic sites). There the *entire document* is a template, but templating also works in smaller contexts — **"the old faithful `printf` function in C is an example of using Templated Generation to print out a single string at a time."** He usually reserves the term for the whole-document case, "but `printf` reminds us that Templated Generation and *Transformer Generation* can be very intermixed." Textual macro processors are another form of Templated Generation.

### The three components

- **Template** — the source text of the output file, with dynamic parts represented by callouts. The callouts reference the context.
- **Context** — the source for dynamic data; "essentially, the data model for the template generation." May be a simple data structure or a more complex programmatic context; different tools use different forms.
- **Templating engine** — the tool that brings template and context together to produce output. A controlling program runs the engine with a particular context and template, "and may run the same template with multiple contexts to produce multiple outputs."

### Callout languages: host code vs. templating language

- **The most general form allows arbitrary host code expressions in the callouts** — the mechanism used by JSP and ASP. "Like any form of *Foreign Code*, it needs to be used with care, otherwise the structure of the host code can overwhelm the template." **Fowler's strong recommendation: "if you have a template processor that embeds arbitrary host code, you confine yourself to simple function calls within the callouts, preferably using an *Embedment Helper*."**
- Because template files so commonly get "thoroughly messed up due to too much host code," many template processors instead provide a restricted **templating language**, "usually quite restricted to encourage simpler callouts and preserve the clarity of the template structure."
- The **simplest** templating language treats the context as a map and provides expressions to look up values and insert them. Sufficient for simple templates, but common needs push further:
  - **Iteration** — generating output for the items in a collection is "a common driver for more complex templating," requiring a loop construct.
  - **Conditionals** — different output depending on a context value.
  - **Subroutines** — duplicated chunks of template source suggest the need for some subroutine mechanism inside the template language.
- **The governing advice:** "My general advice here is to be as minimalist as possible, **since the strength of Templated Generation is directly proportional to how easy it is to visualize the output file by looking at the template.**"

### When to use it (Ch. 53, "When to Use It")

- **The great strength:** "you can look at the template file and easily understand what the generated output will look like." Most useful when there is **quite a lot of static content** in the output while the dynamic content is **occasional and simple**.
- **First indicator:** a lot of static content in the generated file. "The greater the proportion of static content, the more likely that it will be easier to use Templated Generation."
- **Second consideration:** the complexity of the dynamic content. "The more you use iterations, conditionals, and advanced templating language features, the harder it is to comprehend what the output will look like from the template file. When this happens, you should consider *Transformer Generation* instead."

So the two patterns sit at opposite ends of a single spectrum: **static-heavy + simple dynamics → template; generated-heavy + complex structure → transformer.**

### What the example demonstrates (Velocity + Java generating C)

- The chosen case is generating the secret panel state machine **as nested conditionals** (i.e., the *Model Ignorant Generation* output from Ch. 56). Fowler picks it because "the static output is relatively large and the dynamic part is fairly simple — all good indications for Templated Generation."
- Engine: **Apache Velocity** (available for Java and C#), a restricted templating language rather than embedded host code.
- Method: view the whole output file as **segments of dynamic content, each driven by a collection you iterate over** to generate that segment's code.
- A nice practical wrinkle: **the C preprocessor is itself a form of Templated Generation, and both it and Velocity use `#`.** `#foreach` is a Velocity command; `#define` is a C preprocessor command. Velocity ignores commands it doesn't recognize, so it passes `#define` through as text. (A reminder that generator and target can compete for the same syntax.)
- **The context is a single *Embedment Helper*.** Rather than pushing model objects and loose values into the Velocity context, he places just one helper object — a `SwitchHelper` initialized with the state machine — and the template reaches everything through it (`$helper.events`, `$helper.states`, `$helper.stateEnum($s)`, `$helper.getTransitions($s)`).
- **Where the line falls between model and helper:** simple properties come straight off Semantic Model objects (`$e.code`), but derived names and identifiers are helper methods — building `EVENT_<name>` / `STATE_<name>` constants and assigning integer state IDs. Logic that would be ugly in the template goes in the helper: assembling a state's full transition list by combining the model's own transitions with derived reset-event transitions.
- Two asides that reveal Fowler's values: he generates named constants rather than raw codes **"because I prefer even my generated code to be readable"**; and he cheerfully sorts the state list every time he needs an ID, noting he'd cache it if it were a performance issue, but it isn't.

### Relationships

- Opposite end of a spectrum from *Transformer Generation* (Ch. 52); can be combined in a multistage transform.
- Strongly associated with *Embedment Helper* (Ch. 54) — templating with arbitrary host code should almost always use one.
- Relates to *Foreign Code* (embedded host code in a foreign representation).
- The example generates *Model Ignorant Generation* output (Ch. 56).

### SDK relevance

- Templates are the right tool for the **boilerplate-heavy files in a generated SDK** — package manifests, README scaffolds, client class shells, per-endpoint method bodies with a fixed shape. Transformers are better for anything with structural variation (type mapping, union/discriminator handling, nested schema flattening).
- **"The strength of Templated Generation is directly proportional to how easy it is to visualize the output by looking at the template"** is the acceptance criterion for a generator's maintainability. A template that has become unreadable to someone who knows the target language has stopped paying for itself — that's the signal to move logic into a helper or switch to a transformer.
- The `#` collision between Velocity and the C preprocessor generalizes to a real hazard: **choose a template delimiter that doesn't collide with your target language's syntax** (Go templates in YAML, Jinja in Jinja-ish targets, JSX-like syntax in HTML templates).

---

## Chapter 54: Embedment Helper

**Intent:** An object that minimizes code in a templating system by providing all needed functions to that templating mechanism. (Fowler, DSL book, Ch. 54 "Embedment Helper", intent.)

### The concept — the separation principle

"Many systems allow you to extend the capability of a simple representation by embedding general-purpose code into that representation to do things that otherwise would not be possible." Fowler's three examples span the book:

- embedding code into **web page templates**,
- putting **code actions into grammar files** (parser generators),
- putting **callouts into code generation templates**.

This mechanism of general-purpose *Foreign Code* "adds a lot of power to the representation it's embedded into, without complicating the basic representation itself. **However, a common problem when you do this is that the Foreign Code can end up being quite involved and obscure the representation that it's embedded into.**"

The pattern: **move all the complex code into a helper class, leaving only simple method calls in the host representation. "This allows the host representation to be dominant and retain its clarity."**

That's the separation principle in one line: *the foreign representation (grammar, template) should read as itself, not as host-language code with a bit of grammar sprinkled in.*

### How it works

- Mechanically it's "similar to a refactoring": create the helper, make it visible to the host representation, and move all the code from the host representation into the helper, leaving just a method call behind.
- **The one tricky technical aspect is getting an object into the visible scope** when the host representation is processed. "Most systems give you some mechanism to do this — they need to in order to call libraries — but it's sometimes a bit messy." (In the Velocity example, the helper is the only object put in the context; in the ANTLR example, ANTLR's `@members` section declares a helper field on the generated parser, or the `superClass` option makes the helper the parser's superclass.)
- Once the helper is visible, **"any code that's more than a simple method call should move into the Embedment Helper, so the only code left in the host representation is simple calls."**
- **The remaining complication is not technical: how do you make it clear what the helper's code is doing?** "The key to this, as with any abstraction, is careful naming of the methods, so they clearly state the intention of the called code without revealing its implementation. This is the same basic skill as method and function naming in any context — a central skill of a good programmer."

### Should the helper generate output? (a genuine debate)

When Embedment Helper is combined with *Templated Generation*, a common question is whether the helper should generate output. "I often hear this as an absolute point: **Helpers must never generate output.** I don't agree with this absoluteness."

- **The real cost:** "there is a problem with generating output in the helper — any such output isn't visible from the template. Since the whole point of Templated Generation is that you see the output with holes, such hiding of generated material is, without doubt, a problem."
- **The counterweight:** "this problem has to be weighed against the complexity of retaining the output in the template and the more complicated constructs of *Foreign Code* you may need if you want to avoid generating output in it. This is a balance that you have to consider in each case, and although I would say it's good to avoid generating from the Embedment Helper, I'm not inclined to agree that it is always better than the alternative."

### When to use it (Ch. 54, "When to Use It")

- **Near-universal recommendation, unusually for Fowler:** "I'm very suspicious of patterns that someone claims should always be used, but Embedment Helper is one of those things I would always suggest doing, except in really trivial cases."
- The justification is empirical: "I've looked at a fair bit of code using *Foreign Code* in my time, and I see a huge difference if Embedment Helper is present. Without it, it's hard to see the host representation, so much so that it rather defeats the purpose of using an alternative representation at all. For instance, **a grammar file with lots of Foreign Code in actions makes it very hard to see the basic flow of the grammar.**"
- **A second benefit: tooling.** With a sophisticated IDE, embedded code can't be edited with the IDE's tooling; move it to an Embedment Helper and "you're back in your full editing environment. Even simple text editors benefit a bit by simple things such as code coloring, which usually won't work properly for embedded code."
- **The one situation where you don't need one:** "where you are using classes that act as a natural home for providing this kind of information. An example of this is if you are doing *Templated Generation* with a *Semantic Model*. In this case, much of the behavior that you would have in an Embedment Helper can reasonably be part of the Semantic Model itself — **provided this doesn't make the Semantic Model too complex.**" (Ch. 57's schema-generation example does exactly this: the template calls `f.java_type`, `f.getter_name`, `f.checker_name` on the Semantic Model's `Field` objects.)

### What the examples demonstrate

**Example 1 — Secret Panel States (Java and ANTLR).** The clearest demonstration of the problem, because it shows the "before":

- The before: an ANTLR grammar whose rules carry inline Java actions that put events into a map, look up or create states, construct the `StateMachine` on first use, and wire transitions — plus *Symbol Tables* and general helper functions in the grammar's `members` section. Fowler's summary of the damage: **"With such inlined code, grammar files can have more lines of Java than the grammar DSL."**
- The after: each grammar rule carries a single call — `{helper.addEvent($name, $code);}`, `{helper.addState($name);}`, `{helper.addTransition($sourceState, $trigger, $target);}` — and the grammar reads as a grammar again.
- **Mechanism:** ANTLR's `@members` section declares a `StateMachineLoader helper` field in the generated parser (package visibility, so another class can set it). A loader class orchestrates the parse: constructs lexer and parser, sets `parser.helper = this`, runs the parse, and holds the resulting machine. **The loader also acts as the helper** — "the loader is really quite simple, so it seems better to add the helper behavior to the loader than to make them separate classes."
- **Keep the grammar even thinner:** he passes the raw *tokens* into the helper rather than extracting text in the grammar, "to keep the amount of code in the grammar file to the minimum" — the helper extracts the text payload.
- **A naming judgement worth its own note (Ch. 54, "Secret Panel States"):** should helper methods be **command-oriented** (`addEvent`, `addState`) or **event-oriented** (`eventRecognized`, `stateNameRecognized`)? "The argument for event-oriented names is that it doesn't imply any action on the helper, leaving it up to the helper to decide what to do. This is particularly handy if you use different helpers with the same parser that do different things in reaction to the parse. The problem with event-oriented names is that you can't tell what's going on by just reading the grammar. In a case where I'm only using the grammar for one activity, I'd rather be able to read the grammar and see from the naming what's happening at each step."
- **Alternative mechanism:** ANTLR's `superClass` option lets you set any class as the superclass of the generated parser. Make the Embedment Helper that superclass, and the grammar can call `addEvent` bare rather than `helper.addEvent` — a small fluency win.

**Example 2 — Should a Helper Generate HTML? (Java and Velocity).** Deliberately not a DSL example ("it involves creating HTML, but the principles are the same and it saves me having to dream up another contrived example"). Rendering a list of people where each name may be wrapped in a URL link, a mailto link, or no link at all:

- **Template-only version:** a `#foreach` containing `#if`/`#elseif`/`#else` branches, each with its own `<li>`/`<a>` markup. "The problem with this is that I now have a bunch of logic in my template file. This logic can obscure the template layout itself, which is exactly what a Embedment Helper can help with."
- **Full-helper version:** the template collapses to `<ul> #foreach($person in $book.people) <li>$helper.render($person)</li> #end </ul>`, with all the link logic (and the anchor markup) in a helper `render` method. "By moving the logic to the helper, I make it easier to follow the template at the cost of some of the HTML not being visible in the template."
- **The middle ground — the point of the example:** the helper can take the *logic* without taking the *output*. Provide `$helper.hasLink($person)` and `$helper.getHref($person)`; the template keeps the `#if` and the anchor markup but no longer contains the email/URL precedence rules. "This is where some of the logic can go into the Embedment Helper without having it generate output."
- **His conclusion:** "putting some output generation in the Embedment Helper is a reasonable choice. **The more complicated the logic and the more complicated the overall template, the more I gain by moving output generation to the Embedment Helper where I can factor it better.**"
- **The strongest objection, and its scope:** "The biggest objection to this occurs when you have separate people working on the template (such as an HTML designer) and the code. This leads to a coordination cost for some changes. For instance, suppose the HTML designer wants to add a style class to the link output; if the Embedment Helper generates that link, then the designer has to coordinate with a programmer to make that change. **Of course, this is only a problem if you have different people working on the different files; when generating code for a DSL, this is usually not the case.**"

### Relationships

- Applies to *Foreign Code* wherever it appears: parser-generator actions (grammar files), *Templated Generation* callouts, web templates.
- Explicitly recommended by *Templated Generation* (Ch. 53) whenever the template processor allows arbitrary host code.
- Can be omitted when a *Semantic Model* naturally provides the needed behavior (see Ch. 57's example).

### SDK relevance

- **The general principle — "keep foreign code out of the foreign representation" — is a config/DSL-surface design rule.** Any place where a library lets users embed host code into a declarative artifact (build config, CI YAML with inline scripts, ORM query DSLs with raw SQL escape hatches, grammar or schema files with hooks) should offer a way to name and call out to real code rather than inline it. If your API forces users to inline logic, their declarative files stop being readable as declarations.
- **Command-oriented vs. event-oriented naming is a general callback/hook API question.** Event-oriented names (`onXRecognized`) keep the emitter decoupled and allow multiple, differently behaving listeners; command-oriented names (`addX`) make the call site self-documenting. Fowler's tiebreaker — how many different consumers will there be, and does the call-site reader need to know what happens? — is a useful heuristic for naming hooks, visitors, and event handlers.
- **The IDE/tooling argument is a real developer-experience argument for extension APIs:** code that lives in a normal source file gets refactoring, autocomplete, type checking, and syntax highlighting; code living inside a string or a config file gets none of it. That alone often justifies a "reference a function by name" extension mechanism over an "inline a snippet" one.
- The "should the helper generate output" debate generalizes to **how much a helper/formatter layer should own**: pulling logic out is nearly always good; pulling *the visible artifact* out trades reviewability for factoring. Fowler's coordination-cost framing (separate designer/programmer roles) is the deciding variable — and he notes it usually doesn't apply to code generation for a DSL, where one team owns both files.

---

## Chapter 55: Model-Aware Generation

**Intent:** Generate code with an explicit simulacrum of the semantic model of the DSL, so that the generated code has generic-specific separation. (Fowler, DSL book, Ch. 55 "Model-Aware Generation", intent.)

### The concept

When you generate code, you embed the semantics of the DSL script within that code. **Model-Aware Generation replicates some form of the Semantic Model in the generated code in order to preserve the separation of generic and specific code within the generated code.**

The sketch shows the split clearly: on the DSL-processor side of the line sits the Semantic Model, which *generates* a small body of code — `declare_state("idle"); declare_transition("idle", "doorClosed", "active");` — that lives on the target-environment side and *uses* a second semantic model that also lives in the target environment.

So: the target environment gets **a hand-written generic runtime model** plus **a small generated configuration script that populates it**.

### How it works

- **"The most important aspect of Model-Aware Generation is that it preserves the principle of generic-specific separation. The actual form that the model takes in the generated code is much less important, which is why I like to say that the generated code contains a *simulacrum* of the Semantic Model."**
- It is a simulacrum for good reasons: "Usually, you are generating code because of limitations in the target environment — these limitations often make it harder to express a Semantic Model than you would like. As a result, lots of compromises will need to be made, which makes the Semantic Model less effective as a statement of the intent of the system. **However, it's important to realize that this isn't such a big deal as long as you keep the generic-specific separation.**"
- **The testability property — the most practically valuable part of the pattern:**

  > "Since the simulacrum model is a self-standing version of the Semantic Model, you can, and should, build and test the model without using any code generation. **Ensure the model has a simple API to populate it.** The code generation will then generate configuration code that calls this API. You can then test the simulacrum model using testing scripts that use this same API. This allows you to build, test, and refine the core behavior of the target environment with running the code-generation process. You can do this with a relatively simple test population of the model, which should be easier to understand and debug." (Ch. 55, "How It Works".)

  In other words: the generator and the runtime become **independently testable**, joined only by a small, stable API.

### When to use it (Ch. 55, "When to Use It")

**Advantages over *Model Ignorant Generation*:**

- The simulacrum model, built without generation, "is easier to build and test, because you don't have to rerun and comprehend code generation while working on the simulacrum model."
- "Since the generated code is now made up of API calls on the simulacrum model, that code is much easier to generate, which makes the generator simpler to build and maintain."

**The reasons not to use it — both about the target environment:**

- "Either it's too hard to express even a simulacrum model" in the target, **or** "there are performance problems with having a simulacrum model at runtime."

**A framing sentence worth remembering:** "In many cases, you are using DSLs as a front end to an existing model. **If you are generating code to work with the model, then you are using Model-Aware Generation.**"

### What the examples demonstrate

**Example 1 — Secret Panel State Machine (C).** Scenario framing: the Java-enabled toasters have run out and the new batch is only programmable in C, so C code must be generated from the existing Java semantic model. The chapter deliberately doesn't cover *generating* the code (see Ch. 52) — it concentrates on **what the final code, generated and handwritten, looks like.**

- **Implementation shape:** a data structure plus routines that navigate it. Because each physical controller controls a single device, the data structure is static data; heap allocation is avoided entirely and all memory allocated up front, with array sizes set by macro defines. The structures nest: a controller holds a pointer to the state machine plus an integer current state; the machine holds arrays of states, events, and commands; a state holds a name, an array of transitions (integer event/target pairs) and an array of integer action references. **Integer references represent all links between parts of the model** — the C-flavored simulacrum of object references.
- **Readability of generated code (a stated principle):** "I believe that generated code should be readable even if it isn't edited, because it will often be used for debugging. **To make it readable, you have to understand your target audience, such as who is doing the debugging.**" He therefore avoids pointer arithmetic in favor of array indices, even though many C programmers would prefer pointer arithmetic — "even if you as a generator writer are comfortable with pointer arithmetic, you should be wary of using it in the generated code if the people reading that code aren't comfortable."
- **Encapsulation:** all the data definitions live in a single `.c` file, "encapsulate[d]... behind a bunch of externally declared functions. **The specific code only knows about these functions and is, rightly, ignorant about the data structure itself. In this case, ignorance is truly bliss.**" The declaration functions (`declare_event`, `declare_command`, `declare_state`, `declare_action`, `declare_transition`) constitute the model's population API — precisely the "simple API to populate it" the pattern calls for.
- **Consequences of that encapsulation:** the model's internals are primitive (linear array scans to look up names and codes). "In running the machine we might be better off replacing the linear search with a hash function. **Since the state machine is well encapsulated, this is easy to do... Changing such implementation details of the model doesn't affect the interface of the configuration functions that define new state machines. This is an important encapsulation.**" That is the whole payoff of generic/specific separation stated as an API property.
- **A deliberate loss of intent:** the C model has no notion of reset events; the reset events defined in the DSL and the Java Semantic Model are translated into extra ordinary transitions in the C machine. "This makes running the state machine simpler, and is **an example of a typical tradeoff where I prefer simplicity of operation to clearly stating intent. For the true Semantic Model, I prefer to keep as much intent as I can, but for a model in a generated target environment I value capturing intent a little less.**"
- **Where he stops simplifying:** he could go further and strip all names for events, commands, and states (they're only used while configuring), using lookup tables discarded once the machine is defined, or making the declaration functions take bare integers (`declare_action(1,2)`). He keeps the names because he prefers even generated code to be readable, "but more importantly it allows the state machine to produce more useful diagnostics when things go wrong. I'd sacrifice this, however, if space was really tight in the target environment."
- Small craft note: an `assert_error` macro is wrapped in a `do { ... } while(0)` block, which "looks odd, but prevents awkward interactions if the macro is used inside an `if` statement."

**Example 2 — Loading the State Machine Dynamically (C).** The payoff example for the pattern:

- The problem: generating C means you must **recompile** to set up a new state machine.
- The solution: Model-Aware Generation also lets you build state machines **at runtime**, by driving the model population through a data file instead of compiled calls. A plain line-oriented text file (`event doorClosed D1CL`, `state idle`, `transition idle doorClosed active`, `action idle unlockDoor`, ...) is generated from the Java Semantic Model, and a small C interpreter reads it with *Delimiter-Directed Translation* using standard library string functions (`strtok` on whitespace, dispatch on the first keyword to per-keyword interpret functions that call the very same static `declare_*` functions).
- **On the file format:** "I don't consider this textual format a DSL, as I designed it to make it easy to interpret, not for readability by humans. It's useful to have a certain amount of human readability — such as using the names of states, events, and commands — as that helps in debugging. Still, in this case human readability was a distant second to ease of interpretation." (A clean statement of the difference between a DSL and a wire/config format.)
- **The general lesson:** "**code generation for a static target language does not mean you cannot use runtime interpretation.** By using Model-Aware Generation, I can compile just the generic state machine model together with a very simple interpreter. My code generator then just generates the text file to be interpreted. This allows me to use C for my controllers, but without having to recompile to make a change in the state machine. **By generating a file that's designed for ease of interpretation in the environment I have available, I can minimize the cost of the interpreter.**"
- And the boundary of the pattern: "I could, of course, go a step further and put the full DSL processor in C — but this would raise the processing demands of the C system and require more involved C programming. Depending on the particular situation, that may be a viable option, and we would no longer be in the world of Model-Aware Generation."

### Relationships

- The counterpart/alternative to *Model Ignorant Generation* (Ch. 56), and Fowler's default preference.
- Pairs naturally with *Transformer Generation* (Ch. 52), since the generated output is a simple sequence of API calls.
- The target-side simulacrum is an *Adaptive Model* (Ch. 47) living in the target environment.
- The dynamic-loading variant uses *Delimiter-Directed Translation*.

### SDK relevance

This is the most directly SDK-relevant pattern in Part VI.

- **"Thin generated layer over a fat hand-written runtime" is the dominant architecture of good generated client SDKs.** The generated code should be a declarative configuration/registration surface (endpoint descriptors, type registrations, method stubs that call a shared request pipeline); the retry logic, auth, serialization, pagination, and error mapping belong in a hand-written, versioned runtime library that the generated code calls. Fowler's argument for it — the runtime is testable without running the generator, and the generator becomes trivial because it only emits API calls — is exactly the argument for that split.
- **"Ensure the model has a simple API to populate it"** is a concrete requirement on the runtime library's public (or internal-but-stable) surface. That population API is the contract between generator and runtime, and keeping it small and stable is what lets each side evolve.
- **The encapsulation payoff is a versioning payoff:** because the specific/generated code only knows the declaration functions, the runtime can change its internal data structures (linear scan → hash) without regenerating anything. Conversely, if generated code reaches into runtime internals, every runtime change forces a full regeneration across all consumers.
- **Generated code should be readable for debugging, calibrated to who will debug it.** Generated SDKs are read constantly (stack traces, "what does this method actually send?"), so favor named constants, comments carrying model provenance, and idioms familiar to the target language's users over clever compactness.
- **The dynamic-loading example is the "ship a spec file, not a recompile" pattern** — generating a machine-readable descriptor that a compiled runtime interprets, so behavior changes don't require rebuilding and redistributing. This is how schema-driven/plugin-driven runtimes, feature-flag configs, and remote-config-driven clients work. The design guidance is notable: *the generated file is optimized for ease of interpretation, not human readability* — it is a serialization format, not a DSL, and conflating the two makes both worse.
- The reset-events tradeoff is a good general reminder: **the fidelity you demand of your true Semantic Model does not have to be demanded of a derived/target model.** Derived artifacts may legitimately lower expressive fidelity in exchange for runtime simplicity.

---

## Chapter 56: Model Ignorant Generation

**Intent:** Hardcode all logic into the generated code so that there's no explicit representation of the Semantic Model. (Fowler, DSL book, Ch. 56 "Model Ignorant Generation", intent.)

### The concept

The opposite pole from Model-Aware Generation. The sketch shows a Semantic Model generating, straight into the target environment, a `handle_event` function containing a `switch` on the current state and nested `strcmp` conditionals on the event code. **There is no model data structure in the target at all** — the model's content has been dissolved into control flow.

### How it works

- The enabling insight: "One of the advantages of code generation is that it allows you to produce code that would be too repetitive to write by hand in a controlled way. **This opens up implementation options that, usually, you would wisely shy away from because of duplicating code. In particular, this allows you to take behavior usually represented through data structures and encode them in control flow.**"
- The method: "start by writing an implementation of a particular DSL script in the target environment. **I prefer to start with a very simple and minimal script.** The implementation code should be clear, but can freely intermingle generic and specific code, and I don't have to worry about repetition in the specific elements, since these will be generated. **This means I don't have to think about clever data structures, usually preferring procedural code and simple structures.**"

That is the distinctive freedom of the pattern: because a machine is writing it, you can relax the normal DRY discipline and prefer flat, obvious, repetitive code.

### When to use it (Ch. 56, "When to Use It")

**Two reasons to use it:**

1. **Target-environment limitations.** "Target environments often involve languages with limited facilities for structuring programs and building a good model. In these situations, it's not possible to use *Model-Aware Generation*, so Model Ignorant Generation is pretty much the only option."
2. **Runtime resource pressure.** "When using Model-Aware Generation results in an implementation that demands too much runtime resources. Encoding logic in control flow may reduce memory needs or increase performance; if these are sufficiently critical, then Model Ignorant Generation is a good way to get there."

**Fowler's preference and the honest counterweight:**

> "On the whole, however, I prefer to see Model-Aware Generation if it's possible. It's usually easier to generate code with Model-Aware Generation, which results in a generation program that's simpler to understand and modify. Having said that, **using Model Ignorant Generation often makes the generated code easier to follow. This has the converse effect that it can be easier to figure out what to generate, although harder to write the code to generate it.**"

That last sentence is the crisp tradeoff: **Model Ignorant Generation moves complexity from the generated artifact into the generator; Model-Aware Generation moves it from the generator into a hand-written runtime.**

### What the example demonstrates (C, "Secret Panel State Machine as Nested Conditionals")

- One of the classic state machine implementations: "nested conditionals which allow you to evaluate your next step using conditional expressions based on your current state and the received event."
- Two conditions to evaluate — the current state and the incoming event — so the code has two nested layers: an outer `switch` on a static `current_state_id` (with `#define`d state constants and an `ERROR_STATE` sentinel for "not yet initialized"), dispatching to one function per state; and inside each per-state function, a sequence of `strcmp` checks on the event code, each setting the new state and calling `send_command` for the entry actions.
- The states, events, commands, and every transition and action have been **baked into the identifiers and control flow** — there is nothing at runtime that could be called a state machine model.
- Fowler's closing note captures the pattern exactly: "**While this code would be too repetitive to write by hand for different machines, when generated it is quite easy to follow.**"
- The generator for this output is the Velocity template in Ch. 53 — the pairing of Templated Generation with Model Ignorant Generation, mirroring the Transformer + Model-Aware pairing in Ch. 52.

### Relationships

- Counterpart to *Model-Aware Generation* (Ch. 55); Fowler prefers Model-Aware where possible.
- Generated in the book's example by *Templated Generation* (Ch. 53) — static-heavy output with simple dynamic parts is exactly what Model Ignorant Generation produces.

### SDK relevance

- The right choice when **the target cannot host a runtime library**: embedded/constrained environments, generated code that must be dependency-free, single-file drop-in artifacts, or environments where adding a runtime dependency is politically or technically impossible. "Zero-dependency generated client" is a real product requirement, and it forces Model Ignorant Generation.
- Also the right choice when **inlining wins on performance/size** — the classic generated-serializer or generated-parser case where a table-driven runtime is slower or bigger than unrolled control flow.
- The costs are the mirror image and worth stating for SDKs: **every behavior fix requires regenerating and redistributing all consumers**, because there is no shared runtime to patch. With Model-Aware Generation you can ship a runtime patch; with Model Ignorant Generation the bug is baked into every user's checked-in generated files. That is usually the decisive argument for Model-Aware in library ecosystems.
- The "generated code is easier to follow, generator is harder to write" tradeoff also affects **user trust**: fully inlined generated code is auditable by the consumer without learning your runtime, which some consumers value highly.

---

## Chapter 57: Generation Gap

**Intent:** Separate generated code from non-generated code by inheritance. (Fowler, DSL book, Ch. 57 "Generation Gap", intent.)

### The concept

"One of the difficulties of code generation is that generated code and handwritten code need to be treated differently. **Generated code should never be edited by hand, otherwise you can't safely regenerate it.**"

Generation Gap keeps the generated and handwritten parts separate **by putting them in different classes linked by inheritance.**

The sketch: a schema (`firstName: text`, `lastName: text`) generates a class `PersonDataGen` with those fields; a handwritten class `Person` extends `PersonDataGen` and adds `fullName`.

**Attribution:** "This pattern was first described by the late John Vlissides. In his formulation, the handwritten class was a subclass of the generated class. My description is a little different, based on the use I've seen; I really wish I were able to talk it through with him."

### How it works

**Basic form:** generate a superclass (Vlissides's "core class") and hand-code a subclass.

- "This way you can always override any aspect of the generated code that you like in the subclass."
- "The handwritten code can easily call any generated features, and the generated code can call hand-coded features by using **abstract methods** — which the compiler can check are implemented by the subclass — or **hook methods** which are only overridden when needed."
- **"When you refer to these classes from outside, you always refer to the handwritten concrete class. The generated class is effectively ignored by the rest of the code."**

**The three-class variation.** A common variation adds a third class: a **handwritten class that is a superclass of the generated class**, to pull out any logic of the generated class that doesn't depend on the variations triggered by code generation.

- Rationale: "Instead of generating the nonvarying code, having it in a superclass allows it to be better tracked by tools, particularly IDEs."
- **The general principle behind it:** "**In general, my suggestion with code generation is to generate as little code as possible.** This is because any generated code is more awkward to edit than handwritten code. Whenever you change generated code, you need to rerun the code generation system. Refactoring capabilities of modern IDEs won't work properly with generated code."

So the full structure, top to bottom:

| Class | Kind | Contains |
|---|---|---|
| Handwritten base class | handwritten | logic that doesn't vary based on the parameters to code generation |
| Generated class | generated | logic that can be generated automatically from the generation parameters |
| Handwritten concrete class | handwritten | logic that can't be generated and relies on generated features — **"the only one that should be mentioned by other code"** |

- "You don't always need all three of these classes. If you don't have any unvarying logic, you don't need the handwritten base class. Similarly, if you never need to override the generated code, you can skip the handwritten concrete class. Thus another reasonable variation of Generation Gap is a handwritten superclass and a generated subclass."
- "Often, you find more complex structures of generated and handwritten classes, related by both inheritance and general calling use. **The interplay of code generation and handwriting does lead to a more complicated class structure — this is the price you pay for the convenience of code generation.**"

**The empty-concrete-class wrinkle.** What do you do when you have handwritten concrete classes *some* of the time but not all? You must decide what happens for the ones with no handwritten class. You could make the generated class the named class used by calling code, "but that causes a lot of confusion over naming and usage. **As a result, I prefer to always create a concrete class, leaving it empty if it has nothing to override.**" And who creates the empty ones? "If there's only a few and they change rarely, then it's fine to leave it to a programmer. However, if you have a lot of them and they change frequently, then it's good to tweak the code generation system to check if there's an existing concrete class and generate an empty one if not."

### When to use it (Ch. 57, "When to Use It")

- "Generation Gap is a very effective technique that allows you to create one logical class split into separate files to keep your generated code separate."
- **Language requirement:** "You do need a language with inheritance to pull it off. Using inheritance means that any members that can be overridden need to have sufficiently relaxed access controls to make them visible to subclasses — that is, not private in Java or C#'s schemes." (Generation Gap therefore forces protected/package visibility on anything overridable.)
- **Alternative — partial/open classes.** "If your language allows you to put code for one class in multiple files, such as C#'s partial classes or Ruby's open classes, then this is an alternative to Generation Gap. The advantage of partial class files is that it allows you to separate generated and handwritten code without using inheritance — everything is in one class."
  - **C# partial classes downside:** "while it's good for adding features to generated classes, it doesn't give you a mechanism to override features."
  - **Ruby open classes:** "do handle this by evaluating the handwritten code after the generated code — which allows you to replace a generated method with a handwritten one."
- **The anti-pattern it replaced.** "The common early alternative to Generation Gap was generating code into a marked area of a file between comments that said something like `code gen start` and `code gen end`. The trouble with this was that it was confusing, leading to people modifying the generated code and awkward source control diffs. **Keeping generated code in separate files is almost always a better idea if you can find a way to do it.**"
- **Prefer collaboration to inheritance when you can.** "Although Generation Gap is a nice approach, it isn't the only way to keep generated code separate from handwritten code. Often, it works well just to put the two in separate classes with calls between them. **Collaborating classes are a simpler mechanism to use and understand, so in general I prefer them. I am only pushed to Generation Gap when the call interaction becomes more complicated — for example, when there is a default behavior in the generated class that I want to override for special cases.**"

That last paragraph is the actual decision rule: **inheritance only when you need to override defaults; otherwise plain collaboration.**

### What the example demonstrates (Java and a little Ruby, "Generating Classes from a Data Schema")

- **The scenario:** "A common topic for code generation is generating the data definitions for classes based on some form of data schema. If you are writing a *Row Data Gateway* [poeaa] to access a database, you might generate much of this class from the database schema itself." He simplifies to CSV files with a tiny schema file (`firstName : text`, `lastName : text`, `empID : int`), generating a Java *DTO* [poeaa] with the right type per field, getters and setters, and the ability to run validations.
- **A build-process aside with practical weight:** "When generating code is in a compiled language like Java, the build process can often get in the way. If I write my code generator in Java itself, I have to compile my code generator separately from compiling the rest of my code. This makes for a messy build process, particularly when working with an IDE. **An alternative approach is to use a scripting language for code generation; then I only have to run a script to generate code. This simplifies the build process at the cost of introducing another language.** Of course my view is that you should always have a scripting language at hand anyway, since there's always a need to automate tasks with scripts." He uses Ruby with ERB — i.e., *Templated Generation*.
- **Semantic Model:** a `Schema` (name + list of `Field`s), each `Field` a name and a type. "Parsing the schema file is pretty easy... Since this parsing logic is so simple, I don't break the parsing code away from the Semantic Model objects." (A deliberate, size-justified relaxation of the usual parser/model separation.)
- **The three-class structure in practice:** handwritten `AbstractData` (base) → generated `PersonDataGen` → handwritten `PersonData` (concrete).
- **The Semantic Model plays the Embedment Helper role.** The ERB template calls methods on `Field` — `java_type` (mapping `text`→`String`, `int`→`int`, raising on unknown types), `method_suffix`, `getter_name`, `setter_name`, `checker_name`. This is exactly the exemption Ch. 54 carved out: with Templated Generation over a Semantic Model, the model can host the helper behavior.
- **Overriding generated members:** because fields are generated with getters and setters, the handwritten concrete class can override a getter (e.g., capitalize the stored name) and add entirely new derived methods (`getFullName()` combining first and last).
- **Validation via abstract + hook methods — the clearest demonstration of generated↔handwritten collaboration:**
  - The **handwritten base class** defines `validate()`, which creates a *Notification*, calls an **abstract** `checkAllFields(note)` and an **empty hook** `checkClass(note)`, and returns the notification.
  - The **generated class** implements the abstract `checkAllFields` by calling one `checkX(note)` per field — generated from the same information used to generate the fields, so it can never drift out of sync with the field list.
  - Those per-field `checkX` methods are themselves **generated as empty hook methods**, so the **handwritten concrete class** can override any of them to add real validation (e.g., "Employee ID must be positive").
  - `checkClass` is the hook for validations that involve multiple fields together, overridden only in the handwritten concrete class.
  - Net effect: the abstract method gives compiler-enforced completeness; the hooks give opt-in extensibility; and the handwritten code never has to enumerate the fields.

### Relationships

- Applies to any code generation — orthogonal to *Transformer Generation* / *Templated Generation* and to *Model-Aware* / *Model Ignorant Generation*.
- The example uses *Templated Generation* (ERB) with the *Semantic Model* acting as an *Embedment Helper* (Ch. 54).
- References *Row Data Gateway* and *DTO* [poeaa], and *Notification*.

### SDK relevance

Generation Gap is the canonical answer to "how do users customize a generated client SDK?"

- **The invariant to enforce is that generated files are never hand-edited.** Every generated-SDK ecosystem that violates this ends up with users' local edits silently lost on regeneration, or users pinning to an old generator version. Generation Gap makes the boundary a *file and class* boundary rather than a comment marker — and Fowler's dismissal of the `code gen start` / `code gen end` marker approach ("confusing, leading to people modifying the generated code and awkward source control diffs") is a direct verdict on the older style still seen in some tooling.
- **The three-layer structure maps cleanly onto generated SDKs:** hand-written runtime/base (transport, auth, retry, serialization — the non-varying logic, which is also the *Model-Aware Generation* runtime from Ch. 55); generated layer (per-endpoint methods, per-schema models); hand-written concrete/extension layer (custom convenience methods, overridden serialization for one weird endpoint) — and **only the last is what user code names.**
- **"Generate as little code as possible"** is the load-bearing guidance for SDK generators. Every line you generate is a line your users' IDEs can't refactor, that bloats their diffs, and that you must regenerate to fix. Push everything invariant down into the hand-written runtime.
- **Visibility constraints are a real API consequence:** anything you want users to override must not be private. Designing a generated class means deciding, up front, which members are extension points (protected/hook) and which are sealed.
- **Language-specific alternatives matter for multi-language SDKs:** C# partial classes (extend but not override), Ruby open classes / Python monkeypatching (can replace), TypeScript declaration merging, Go embedding — the same intent expressed differently per target. A multi-language generator has to pick the idiomatic separation mechanism per language rather than forcing inheritance everywhere.
- **Always emit the concrete class, even empty.** Otherwise user code sometimes names `FooGen` and sometimes names `Foo`, and adding a customization later becomes a breaking rename for every call site. Fowler's rule — always create a concrete class, empty if it has nothing to override, and have the generator create it if there are many — is precisely the stability guarantee a public SDK needs.
- **The abstract-method + hook-method pairing is a reusable extension-point recipe:** use abstract methods where the compiler should enforce that generated code supplied something (completeness over an enumerable set), and empty hooks where extension is optional. The generated `checkAllFields` that enumerates every field is a good model for any "generated code guarantees exhaustiveness, handwritten code supplies behavior" split.
- **Prefer collaboration over inheritance unless you need to override a default.** For SDKs this often means: a generated descriptor/registry object passed to a hand-written client (collaboration) beats a generated base class the client must extend — unless you genuinely need per-operation default behavior that users override case by case.

---

## Cross-cutting themes worth carrying forward

1. **Declarative model vs. imperative code.** Part V's whole argument is that some behavior is better expressed as a *configured structure* than as control flow — but Fowler never sells it without the bill attached: implicit behavior, hard debugging, and a maintenance population that shrinks to the few people who "get it" (Ch. 47, "When to Use It"). Every alternative-computational-model pattern in Part V repeats this: they demo beautifully and scale badly without tooling.

2. **Tracing is not optional for model-driven behavior.** Ch. 47 asks for it explicitly ("Why did the program do that?"); Ch. 49 asks for logging of invocations and executions; Ch. 50's engine keeps a fired-rule log "to provide a trace for diagnostic purposes." If you ship a config-driven library, ship the explain facility with it.

3. **Put the smarts in the Semantic Model, not the builder/parser** (Ch. 50, "Evolving the DSL"). Preserving the *kind* of thing the user declared, rather than collapsing it into an opaque closure, is what makes a model generable, serializable, introspectable, and documentable later.

4. **The two code-generation axes are independent.** Generator style (transformer vs. template) is chosen by the static/dynamic ratio and structural complexity of the output; generated-code style (model-aware vs. model-ignorant) is chosen by what the target environment can host and afford. Fowler's defaults: prefer Model-Aware when possible; use templates when the output is static-heavy, transformers otherwise.

5. **Two separation principles, one instinct.** *Embedment Helper* keeps foreign code out of a foreign representation so the representation stays readable; *Generation Gap* keeps handwritten code out of generated files so the generated files stay regenerable. Both are about protecting an artifact's ability to be read and rewritten by keeping a different kind of content out of it.

6. **Generated code is read, so make it readable** (Chs. 53, 55) — calibrated to whoever will debug it, not to whoever wrote the generator.

7. **Fowler's recurring "build the simple version yourself" advice.** It appears for Production Rule Systems most forcefully ("build something simple yourself, which you can tune to your particular needs as well as use to learn more about the domain... Once you've learned more, you can evaluate whether it's worth replacing your simple Production Rule System with a tool"), but the same reasoning underlies the Decision Table and Dependency Network chapters: the general version of these models is genuinely hard, and that is not a reason to avoid the limited version.
