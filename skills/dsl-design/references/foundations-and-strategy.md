# Foundations and Strategy

Condensed from Fowler & Parsons, *Domain-Specific Languages* (2010), Part I (Chapters 1–10). Citations are to the book as *(Ch. N, "Section")*.

## Contents

- [1. What a DSL is — definitions and boundaries](#1-what-a-dsl-is--definitions-and-boundaries)
- [2. The Semantic Model and its thin language veneer](#2-the-semantic-model-and-its-thin-language-veneer)
- [3. Why and why not to build one](#3-why-and-why-not-to-build-one)
- [4. The lifecycle](#4-the-lifecycle)
- [5. Processing architecture: pipeline, testing, errors, migration](#5-processing-architecture-pipeline-testing-errors-migration)
- [6. Internal DSL techniques](#6-internal-dsl-techniques)
- [7. External DSL techniques and the internal-vs-external decision](#7-external-dsl-techniques-and-the-internal-vs-external-decision)
- [8. Code generation, workbenches, lessons from real DSLs](#8-code-generation-workbenches-lessons-from-real-dsls)

## 1. What a DSL is — definitions and boundaries

### 1.1 The definition

> **Domain-specific language** (noun): a computer programming language of limited expressiveness focused on a particular domain. *(Ch. 2, "Defining Domain-Specific Languages")*

Four load-bearing elements:

1. **Computer programming language** — humans instruct a machine with it; excludes documentation formats and human jargon.
2. **Language nature** — it has **fluency**, "where the expressiveness comes not just from individual expressions but also from the way they can be composed together." A pile of unrelated statements is not a language.
3. **Limited expressiveness** — "A DSL supports a bare minimum of features needed to support its domain. You can't build an entire software system in a DSL; rather, you use a DSL for one particular aspect of a system."
4. **Domain focus** — comes *last*, and "is merely a consequence of the limited expressiveness."

Do not reach for the literal reading ("a language for a specific domain"). Literal definitions are frequently wrong; we don't call coins "compact discs."

### 1.2 The three implementation styles

- **External DSL** — separate from the application's language, custom syntax or a borrowed carrier syntax (XML), parsed by host-application code. Regex, SQL, Awk, config files.
- **Internal DSL** — a *way of using* a general-purpose language: valid host code restricted to a subset of features, in a style giving "the feel of a custom language, rather than its host language." Lisp, Ruby/Rails.
- **Language workbench** — a specialized IDE for defining a DSL *and* editing its scripts; "the resulting scripts intimately combine the editing environment and the language."

Warning: these have grown separate communities, so "people may not choose the best tool for the job" — teams do elaborate internal-DSL gymnastics because building an external DSL is not in their repertoire. Fowler avoids "embedded DSL" for internal, because *embedded language* already means a scripting language inside an app (VBA in Excel).

### 1.3 A DSL is a front end to a library

> "In this view a DSL is a front-end to a library providing a different style of manipulation to the command-query API. In this context, the library is the Semantic Model of the DSL… I consider a Semantic Model to be a necessary adjunct to a well-built DSL." *(Ch. 2)*

> "it's easy to think that building the DSL is the hard work. In fact, usually the hard work is building the model; the DSL then just layers on top of it." *(ibid.)*

### 1.4 Fluent interface vs command-query API — the internal boundary

A **fluent interface** is another term for an internal DSL. A **command-query API** is Fowler's name for the non-fluent default, "so dominant that we don't even think of giving it a name" *(Ch. 1; Ch. 4, "Fluent and Command-Query APIs")*. The boundary is not domain focus; it is limited expressiveness and language nature.

> "In many ways, an internal DSL is nothing more than a quirky API (as the old Bell labs saying goes, 'Library design is language design')." *(Ch. 2, "Boundaries of DSLs")*

> "a command-query API defines the vocabulary of the abstraction, whereas an internal DSL adds a grammar." — Mike Roberts, quoted *(ibid.)*

**Usable test:** in a command-query API each method must make sense on its own — a list of "words." In an internal DSL "the methods… often only make sense in the context of a larger expression" (`.transition(lightOn).to(unlockedPanel)` — `to` is a bad command-query name and a good phrase element). "an internal DSL should have the feel of putting together whole sentences, rather than a sequence of disconnected commands."

Limited expressiveness for an internal DSL comes from *how you use the host*: "you limit yourself to a small subset of the general language features. It's common to avoid conditions, looping constructs, and variables" — Piers Cawley's **pidgin** use of the host. This is a spectrum, not two categories: plain assembly code "feels like stitching things together with an API," while a builder subclass with chained calls "still has that declarative flow that a DSL needs." The difference "comes down to the rather fuzzy notion of a language-like flow," whose "advantage… is that they encourage reflection on the techniques you are using and on how readable your DSL is; the disadvantage is that they can turn into continual rehashes of personal preferences" *(Ch. 4, opening)*.

### 1.5 The external boundary

Domain focus alone is not enough: **R** is statistics-focused but fully expressive — not a DSL. "One common indicator of a DSL is that it isn't Turing-complete. DSLs usually avoid the regular imperative control structures… don't have variables, and can't define subroutines." Insist on limited expressiveness because "it is what makes the distinction between DSLs and general-purpose languages useful." **Usage can move a language across the line:** XSLT transforming XML is a DSL; XSLT solving eight queens is a general-purpose language.

### 1.6 Config files, serialized data, DSL-by-accident

A flat property list (`color = blue`) is not a DSL — "A series of assignments lacks fluency." Configuration files with genuine language nature *are* DSLs (external ones, if in XML).

> "The question isn't whether it's human-readable or not, but whether the representation is a human's main way of interacting with that aspect of the system." *(Ch. 2, "Boundaries of DSLs")*

> "even though they aren't intended to be human-edited, they end up being the primary editing mechanism in practice. In this case the XML becomes a DSL **by accident**." *(ibid.)*

Same test from the other direction: a generated tabular data file read at startup is not a DSL — "human readability comes a distant second to simplicity of parsing. With a DSL, human readability is a high priority" *(Ch. 8, "Choosing What to Generate")*.

### 1.7 Remaining boundary cases, and the meta-point

- **Workbench boundary** — decided by **design intent**: "Access wasn't designed to be a language workbench, although you can use it that way… Look at how many people use Excel as a database." Tables *can* have language nature (FIT, Excel), but most form-and-table apps "don't stress the interconnections."
- **Human jargon** ("Venti, half-caf, nonfat… latte") has limited expressiveness, domain focus, and grammar — but is not a computer language, so it is a **domain language**, not a DSL.
- **Meta-point:** "there are few sharp boundaries. Reasonable people can disagree… The purpose of a definition is to help in communication." Excluding something from the definition is not a judgement about its value.

### 1.8 Fragmentary vs stand-alone (orthogonal axis) *(Ch. 2, "Fragmentary and Stand-alone DSLs")*

- **Stand-alone** — a whole block/file is DSL; understandable without knowing the host language.
- **Fragmentary** — bits of DSL inside host code; "you can't really follow what the DSL is doing without understanding the host language." Regex and inline SQL (external); mock expectation grammars (internal). **Annotations** are the archetypal fragmentary construct — "suitable for fragmentary DSLs but useless for stand-alone ones."
- The same DSL can swing both ways (SQL).

> **SDK lens:** The line between "an API" and "a language" is the line between vocabulary and grammar. If each method must be comprehensible standing alone in an autocomplete list, you are designing a command-query API; if methods only make sense inside a call sequence, you have written a language and owe it language-grade treatment — defined legal compositions, documentation of phrases rather than words, errors that talk about phrases. The most expensive version is accidental: the serialization format or config file nobody meant to be hand-edited, now the primary interaction surface. The moment that happens it needs versioning, migration, diagnostics, and a readability budget.

## 2. The Semantic Model and its thin language veneer

### 2.1 Start from the axis of variation, not from the language

> "What we have is a family of systems that share most components and behaviors, but have some important differences." *(Ch. 1, "Gothic Security")*

**Identify the axis of variation before designing anything.** The DSL expresses only the varying part; the invariant part belongs in a library. Fowler's framing throughout: "separation of common code from variable code." Only *then* choose the abstraction (here, a state machine).

### 2.2 Build the model first, in domain vocabulary

> "If people want to think about controller behavior with events, states, and transitions, then we want that vocabulary to be present in the software code too." *(Ch. 1, "The State Machine Model")*

Modelling judgements worth carrying independent of DSLs:

- **Don't store what you can derive** (states are reachable from the start state).
- **Type-separate things structurally identical but semantically distinct** (events vs commands: same shape, different roles).
- **Prefer symbolic names to wire codes**, keeping codes as data. The model translates machine vocabulary into human vocabulary before any DSL exists.
- **Behavior gets small once structure is right** — most effort goes into structure; the interpreter is a handful of lines.
- **A redundant construct earns its place if it clarifies intent.** Explicit reset events are strictly synthesizable, and he keeps them: "I prefer explicit reset events on the machine because that better expresses my intent." Design to fit the domain, not the textbook; name the deviation.

### 2.3 The seam: library code vs configuration code

> "On the one hand is the library, framework, or component implementation code; on the other is configuration or component assembly code. Essentially, it is the separation of common code from variable code." *(Ch. 1, "Programming Miss Grant's Controller")*

**A library is the common code; the client's usage is the assembly code; a DSL is an improved notation for the assembly code.** Everything downstream is about making assembly code readable, not making the library more capable.

### 2.4 Many surfaces, one model

The same configuration is expressed as XML, custom syntax, Ruby (internal), Java-fluent, and a generated diagram — all populating the *same* model. Lessons carried:

- **Constraint is a feature.** "limitations like this are often helpful because they can reduce the chances of people making mistakes in the component assembly code."
- The cost is runtime-only error detection, accepted *conditionally*: extensive testing "catches most of the errors with compile-time checking, together with other faults that type checking can't spot. With this kind of testing in place, I worry much less about moving error detection to runtime."
- Working definition by enumeration (from the custom-syntax pass): narrow purpose; simple; **not Turing-complete**; **must be combined with other languages**; easy to edit and process.
- XML vs custom syntax is a *design* issue, not a definitional one — "the core tradeoffs of DSLs are the same."
- On internal DSLs: "this is more a matter of attitude than of anything else. I'm choosing to look at the Ruby code through DSL glasses."

### 2.5 The Semantic Model, defined

Syntax is the set of legal expressions; semantics is what the program means and does. **The model is the semantics.** It sits close to a **Domain Model**, is deliberately distinguished from it, and is emphatically **not** an abstract syntax tree *(Ch. 1, "Languages and Semantic Model"; Ch. 3, "The Workings of a Parser")*. The DSL's only job is to populate it (declarations stashed in a **Symbol Table**, references resolved against it, then ordinary model API calls).

> "All the DSL does is provide a readable way of populating that model — that is the difference from the command-query API I started with." *(Ch. 1)*

> "One opinion I've formed is that the Semantic Model is a vital part of a well-designed DSL… I'm very much of the opinion that you should almost always use a Semantic Model." *(ibid.)*

**Every benefit is a seam you can act on:** clear separation between parsing and semantics; reasoning about, extending, and debugging behavior without language issues; **testing the model by populating it through the plain command-query interface, no parser involved** ("Perhaps the most important point"); evolving model and DSL independently, building features into the model before deciding how to expose them; supporting **multiple DSLs over one model** without duplication; comparing two syntaxes by comparing how they populate the model.

Form is negotiable: an object model is preferred, but "a pure data structure with all behavior in separate functions" is still a Semantic Model. "**using a data model form of Semantic Model is better than not using a Semantic Model at all**" *(Ch. 3)*.

### 2.6 Attribute the benefits correctly — the discipline

Repeated in three chapters, and the most easily lost point in the book:

> "the DSL merely acts as a mechanism for expressing how the model is configured. Much of the benefits of using this approach comes from the model rather than the DSLs." *(Ch. 1)*

Easy configuration, runtime change without recompiling, and reuse across installations are properties of the **model**. "Hence the DSL is merely a thin facade over the model." "Good models… can work just fine without any DSL in sight. DSLs are thus a useful adjunct to some models." Named spurious benefit: "the same behavior can execute in different language environments… is a spurious benefit because you can gain this just by using a model; you don't need a DSL at all" *(Ch. 2)*.

**Discipline:** whenever you claim a benefit (or a disadvantage), state explicitly whether it belongs to the model or to the language layer. "It's a common mistake to confuse the two."

### 2.7 Adaptive Models

An **Adaptive Model** is one whose *population acts as the program*: behavior changes by rewiring instances, not by editing code. It blurs code and data.

> "Adaptive Models can be very powerful, but they are also often difficult to use because people can't see any code that defines the particular behavior. A DSL is valuable because it provides an explicit way to represent that code in a form that gives people the sensation of programming the state machine." *(Ch. 1)*

### 2.8 Interpretation vs code generation — deployment choices off one model

**Interpretation** parses and immediately produces the result. **Compilation** parses, produces intermediate output, processes it separately — "In the context of DSLs, the compilation approach is usually referred to as **code generation**." Generation usually adds a compile step and "makes your build process much more complicated." Worth it when the target platform can't host DSL tooling (C for hardware, SQL, COBOL, MathCAD).

> "Many writings on DSLs focus on code generation, even to the point of making code generation the primary aim… In my view, however, code generation is merely an implementation mechanism, one that isn't actually needed in most cases." *(Ch. 1, "Using Code Generation")*

Anti-pattern: skipping the Semantic Model and parsing text directly into generated code — "isn't one I recommend for any but the very simplest cases." Keeping the model gives three separable concerns (parsing, execution semantics, generation): switch internal↔external without touching generators, produce multiple outputs without complicating the parser, interpret *and* generate from one source of truth.

Style rule (expanded in Ch. 8): either generate first-pass code meant to be hand-modified, or ensure generated code is never touched. "I almost always prefer the latter because this allows code to be regenerated freely… we want the DSL to be the primary representation of the logic." Generated code "can call, and be called by, handwritten code."

### 2.9 Visualization: a projection you cannot edit

A **visualization** is an alternative representation that helps a human understand the model but **is not editable** — "on the other hand, it can do something an editable form cannot, such as render diagram like this" *(Ch. 1, "Visualization")*. It need not be graphical (textual visualizations for debugging a parser; spreadsheets for domain experts). "Once you have done the hard work of creating a Semantic Model, adding visualizations is really easy." Because they come from the **model**, not the DSL, a visualization is a genuine *alternative* to a DSL when the only goal is domain-expert comprehension.

> **SDK lens:** Ship the model, not the syntax. Everything a caller values — reuse, reconfiguration without redeployment, multiple execution targets, diagrams and docs — is a property of a well-factored object model with a plain, testable API. A fluent surface, a config format, a CLI, and a generated client are thin, replaceable projections of it. Two rules follow. (1) When justifying a convenience layer, be honest about which benefits belong to the layer and which to the model — most belong to the model. (2) Generate every derived artifact (diagrams, reference docs, bindings, schemas) from the model; two hand-maintained representations always diverge.

## 3. Why and why not to build one

### 3.1 Framing

"DSLs are a tool with limited focus. They aren't like object orientation or agile processes which introduce a fundamental shift… Instead, DSLs are a very specific tool for very particular conditions. A typical project might use half a dozen or so DSLs" *(Ch. 2, "Why Use a DSL?")*.

### 3.2 The four reasons to build one

**(a) Development productivity.** A DSL "provides a means to more clearly communicate the intent of a part of a system." Clarity is not aesthetics — easier reading means easier defect-finding and modification, and defect cost is underestimated because defects also "slow developers down by sucking up time in investigations and fixes."

> "The limited expressiveness of DSLs makes it harder to say wrong things and easier to see when you've made an error." *(Ch. 2, "Improving Development Productivity")*

Two sub-arguments aimed at library authors: a DSL **helps people learn an API**, "since it shifts focus to how different API methods should be combined together"; and it **wraps an awkward third-party library** — "the DSL only has to support the actual client usage, which can significantly reduce the surface area that the client developers need to learn." The second half attributes value to *omission*.

**(b) Communication with domain experts.** "the hardest part of software projects, the most common source of project failure, is communication with the customers and users." But "Only a subset of stand-alone DSLs really apply to this communication channel." The **COBOL fallacy** — "now we can get rid of programmers and have business people specify the rules themselves" — is dismissed: "It's a common argument, but I don't think it improves with repetition." What works is **reading, not writing**:

> "It's not that domain experts will write the DSLs themselves; but they can read them and thus understand what the system thinks it's doing. By being able to read DSL code, domain experts can spot mistakes." *(Ch. 2)*

"Focusing on reading can be the first step towards writing the DSL, with the advantage that you lose nothing if you don't take that further step" — a staged adoption path whose failure mode costs nothing. Counter-argument he raises against himself: if you only need experts to understand the model, "you can do this just by providing a visualization… It's worth considering whether a visualization alone is a more efficient route." Also: "some people find that trying to describe a domain using a DSL is useful even if the DSL is never implemented." Net: "involving domain experts in a DSL is difficult to achieve but has a high payoff. And even if you can't… you may still get enough of a gain in developer productivity."

**(c) Change in execution context.** "we want code to run in a different environment" — shifting logic from compile time to runtime. Worked case: contract-matching conditions in a DSL populate a model used to **generate SQL** to run in the database, because writing SQL directly "was too difficult for the developers, let alone the business people." Generalized: "Using a DSL like this can often make up for limitations in a host language." Against a forms-based UI for the same rules, a DSL is better at complicated logic and lets you use ordinary code tooling, "especially version control… When rules are entered via a form and stored in a database, version control is often neglected."

**(d) Alternative computational model.** Imperative "isn't always the best choice"; build systems are the everyday case for a **Dependency Network**. Attribution warning again: "You don't need a DSL to use an alternative computational model. The core behavior… comes from a Semantic Model… However, a DSL… makes it much easier for people to manipulate declarative programs that populate the Semantic Model."

### 3.3 What "declarative" buys and costs

Fowler dislikes the word; his working definition is "something other than imperative" *(Ch. 7)*. The sharpest test in the book splits "ease of understanding" in two: **understanding of intent** (what are we trying to achieve?) and **understanding of implementation** (how does the code satisfy it?). Imperative is excellent at the second — source order matches debugger step order — and often weak at the first. **If intent genuinely is a sequence of actions, imperative code is fine; stop there.** Otherwise: **alternative computational models trade implementation-comprehension for intent-comprehension.** That is the central judgement of Ch. 7.

The decision-table example makes the trade concrete. Imperative encoding of a table **forces an evaluation order** the domain doesn't imply (an implementation artifact injected into the representation) and **removes opportunities** — a real decision table can be checked for missing or duplicated permutations; a chain of conditionals cannot. Principle: *a representation that carries less accidental structure carries more checkable structure.*

### 3.4 Adaptive Models and the mandatory tracing mechanism

Configuring an abstraction instead gives: faithful representation; no spurious ordering (possibly enabling concurrency); **self-validation** (the table reports malformed or incomplete condition sets); and runtime rather than compile-time execution context. Adaptive Models and DSLs are orthogonal but "go together like wine and cheese" *(Ch. 7, "Adaptive Model")*.

The negative must not be softened. Behavior is **implicit**; intent gets easier and **implementation gets harder**, which bites hardest when debugging. Fowler reports people taking *months* to understand an adaptive model, being very productive afterwards, and many never getting there — "until then it's a nightmare." A DSL makes the specific *configuration* visible; it does not remove the burden of understanding the generic machinery, but "can give you a significant leg up."

**The general obligation:** implicit behavior afflicts *all* alternative computational models, because we cannot reason about behavior by reading code. **Whenever you implement an alternative computational model, you must also produce a tracing mechanism** showing exactly what happened in a given execution — for a rule system, which rules fired, available on demand so a puzzled user can follow the chain *(Ch. 7, "A Few Alternative Models")*.

Two distinctions from the survey of **Decision Table**, **Production Rule System**, **State Machine**, **Dependency Network**:

- **Chaining** defines a production rule system: it lets rules be written one at a time without thinking about interactions, and it is the source of nearly all rule-system defects. A rule system *without* chaining fits validation rules well.
- A decision table is formally arguable as a rule system with one rule per column, but that "misses the point": rule systems focus you **one rule at a time**, decision tables on the **entire table**. *Computational models are distinguished by the unit of attention they impose, not just expressive power.*

Choosing one: no strong guidelines — try it on paper first (simple text and diagrams), then prototype. Sequencing rule: **get the Semantic Model working properly first**; a simple DSL may help during that, but tune the model before chasing a readable DSL. "Once a reasonable model is in place, experimenting with different DSLs over it is comparatively easy" *(Ch. 7, "Choosing a Model")*.

### 3.5 The four objections, and how much survives

Fowler judges the standard problems "currently overstated," partly because they repeat the DSL/model confusion *(Ch. 2, "Problems with DSLs")*.

- **Language cacophony.** Two misconceptions: DSL learning cost is not general-purpose-language learning cost — "DSLs are far simpler… and thus far easier to learn"; and projects already have hard-to-learn abstractions — "Even if you don't have to learn several DSLs, you still have to learn several libraries." The right question is how much harder a DSL is *than the underlying model alone*, and "**having a DSL should reduce the learning cost**."
- **Cost of building.** "like any code, it has to pull its weight." *"Not every library benefits from having a DSL wrapper over it. If a command-query API does the job just fine, then there's no value in adding another API on top of it."* Maintenance factors: an internal DSL the team finds hard to read is a problem; "External DSLs in particular add a lot of moving parts… with parsers that are often intimidating." Learning costs amortize across future uses. Accounting rule: measure against the model, not against nothing — "if it's complicated enough to consider a DSL, it's almost certainly complicated enough to benefit from a model." On bad DSLs: "A good DSL can wrap a bad library and make it easier to deal with (although I'd rather fix the library if I can). A bad DSL is a waste… but that can be said of any bad code."
- **Ghetto language.** "if you're writing whole systems in a language, that means it isn't a DSL… Building and maintaining a general-purpose language… condemns you to a lot of work and a life in a ghetto. Don't do that." Two real issues inside it: **(1) scope creep into generality** — "today you add conditional expressions, another day you add loops, and whoops — you're Turing-complete"; defense is "a clear sense of what narrow problem the DSL is focused on. Question any new features that seem to fall outside that mission. If you need to do more, consider using more than one language and combining them," explicitly generalized to libraries — "If your product pricing library includes an implementation of the HTTP protocol, you're suffering from essentially the same failure to separate concerns." **(2) Building what you should take from outside** — "if it's not your business, don't write it yourself."
- **Blinkered abstraction** (conceded most). "you spend more effort on fitting the world into your abstraction than the other way around… you burn time trying to make it fit, instead of changing the abstraction." It strikes "once you've got comfortable with an abstraction and you feel it's bedded down." A DSL worsens it by making the abstraction more comfortable, and domain experts are "even more reluctant to change an abstraction once they get used to it." Remedy is an attitude: "you should always look at a DSL as something that's evolving, not finished."

### 3.6 The decision rule

> "Fundamentally, the only reason to not use a DSL is if you don't see any of the benefits of a DSL apply to your situation — or at least, you don't see the benefits being worth the cost of building the DSL." *(Ch. 2, "Problems with DSLs")*

### 3.7 Language processing beyond DSLs

"90% of the use of language processing techniques in an average development team is for DSLs. But these techniques can be used for some other things as well" — e.g. parsing the used subset of COBOL copybooks and generating interface classes, so "none of the rest of the code needed to know about COBOL data structures, and any changes could be handled with a simple regeneration" *(Ch. 2, "Wider Language Processing")*.

> **SDK lens:** Build the fluent or declarative layer only when you can name which benefit you are buying — clearer intent at the call site, a smaller learnable surface over an awkward dependency, a rule format non-programmers can *read*, or execution in a context your host language can't reach. If a plain command-query API does the job, another API on top has negative value. When you do build a declarative surface, the deciding test is whether the domain's natural mental model is a sequence of steps (ship functions) or a table/graph/rule set/state machine (declarative buys comprehension *and* machine-checkable structure). If you take that route you owe users a tracing/explanation mechanism, because you traded away the debuggability imperative code gave them free. Police scope relentlessly: the pricing library that grows HTTP and the config format that grows loops are the same failure.

## 4. The lifecycle

### 4.1 Two starting points *(Ch. 2, "DSL Lifecycle")*

**Language-first.** "you begin with some scenarios and write those scenarios down in the way you'd like the DSL to look. If the language is part of the domain functionality, it's good to do this with a domain expert." Two drafting styles: insist drafts are already syntactically valid, or "be more informal at the beginning and then take a second pass." Workflow: sit with people who know customer needs, assemble example behaviors from past and expected requests, write each in some DSL form, modify the DSL as you go. Do this stage *outside* any language workbench — text editor, drawing tool, or paper.

**Model-first.** "Usually it is used when you don't think about using a DSL at first… You thus build the framework, work with it for a while, and then decide that a DSL would be a useful addition."

### 4.2 Four artifacts, and the sequencing choice

Four things to implement: the model in the host language; the model's command-query API; the DSL's concrete syntax; the translation between them. Three observed sequencings: (a) thin slices across all four at once; (b) framework first, DSL layered after; (c) DSL first, then library, then fit together. "As I'm an incrementalist, I prefer thin slices of end-to-end functionality, so I go with the first." His loop: simplest case → TDD the library for it → implement and wire the DSL → next case, evolving framework and tests first, then the DSL.

> "I'd be happy to make some changes to the DSL to make it easier to build, although I would run those changes past the domain expert to ensure we still share a common communication medium." *(Ch. 2, "DSL Lifecycle")*

Syntax may be bent for implementability — but not unilaterally. The constraint is the property that made it worth building.

### 4.3 Growing a DSL over an existing model

- **Language-seeded** — "slowly builds the DSL on top of the model, treating the model as a mostly black box." Sketch pseudo-DSL for every existing configuration, implement scenario by scenario, avoid deep model changes (adding supporting methods is fine).
- **Model-seeded** — "add fluent methods to the model first… and then gradually draw them away into a DSL… a heavy refactoring of the model to derive the internal DSL. An appealing aspect… is that it's very gradual, so it doesn't inflict a notable cost."

Note the tension: model-seeding deliberately violates the rule against mixing fluent and command-query methods on one class (§6.2). **Treat fluent methods on the model as a transitional state, not a destination** — the "drawing away" step resolves the violation.

### 4.4 Extract the seam before you design the surface

The most important lifecycle instruction, for the messiest case (several instances built before anyone noticed the commonality):

> "I'd then refactor the system to create separation between the model and the configuration code. **This separation is the vital step.** While I might have a DSL in mind while doing it, I'd be more inclined to get the separation done first, before putting the DSL on top." *(Ch. 2, "DSL Lifecycle")*

### 4.5 Version control

"Do make sure all your DSL scripts are kept under some form of version control… A DSL script becomes part of your code. The great thing about textual DSLs is that they play well with version control systems." The same argument recurs as the reason source editing resists projectional editing (§8.9) and as a DSL advantage over forms-driven rule entry (§3.2c): **text is what makes diff, merge, review, and history possible.**

### 4.6 What makes a good DSL design? *(Ch. 2, "What Makes a Good DSL Design?")*

Fowler concedes he lacks a clear answer. What he offers:

- **Clarity for the reader is the goal.** "You want your typical reader… to be able to understand what the sentences in the DSL mean, as quickly and clearly as possible."
- **Iterate against a real audience.** "Be prepared to provide multiple alternatives and see how people react… Don't worry about wrong turns; the more of those you make and correct, the more likely you are to find a good path."
- **Use domain jargon** — in the DSL *and* in the Semantic Model. "Jargon is there to enhance communication within a domain even if it sounds like gibberish to those outside."
- **Follow the conventions of the surrounding environment** (comment markers, block delimiters of the team's usual language family).
- **Do not imitate natural language:** "such attempts lead to a lot of syntactic sugar which complicates understanding of the semantics. Remember that a DSL is a programming language, so using it should feel like programming, with the greater terseness and precision that programming has compared to a natural language."

> **SDK lens:** Before designing any convenience surface, extract the seam between your invariant engine and the code that configures it for a particular use — that separation is worth having on its own, and every later option (builder, config format, plugin API, generated client) becomes cheap once it exists. Grow the surface in thin end-to-end slices against real usage scenarios written the way you wish callers could write them. You may bend the surface for implementability, but run the bend past the audience you built it for — readability is the asset, and implementation convenience isn't automatically allowed to spend it. The standard failure mode of fluent APIs is chasing English-sentence readability: the target is *terse and precise*, not *prose-like*.

## 5. Processing architecture: pipeline, testing, errors, migration

### 5.1 The reference pipeline

```
DSL script → parse → Semantic Model → [optional] generate → target code
```

The generation step is bracketed because it is explicitly optional *(Ch. 3, "Architecture of DSL Processing")*. "all the important semantic behavior is captured in a model, and the DSL's role is to populate that model via a parsing step." The Semantic Model "is usually a subset of the application's Domain Model" and is "a completely normal object model, which can be manipulated in the same way as any object model you might have."

> "this separation of the Semantic Model and DSL syntax mirrors the separation of domain model and presentation that we see in designing enterprise software. Indeed on a hot day I think of a DSL as another form of user interface." *(Ch. 3)*

Honest limit of the analogy: "If I add new constructs to the DSL, I need to ensure they are supported in the Semantic Model, which often means modifying the two at the same time. However, the separation does mean I can think about semantic issues separately from parsing issues."

### 5.2 Where internal and external differ — the Expression Builder layer

"The difference between internal and external DSLs lies in the parsing step… Both styles… will produce the same kind of Semantic Model."

> "I advocate having an explicit layer of objects (**Expression Builders**) whose job is to provide the necessary fluent interfaces to act as the language. DSL scripts then run by invoking methods on an Expression Builder which then populates the Semantic Model." *(Ch. 3)*

Why "parsing" is fair: "your input is a series of function calls. You still arrange them into a hierarchy (usually implicitly on the stack) in order to produce useful output." Refined internal/external distinction — the "same base language" test is "usually right, but not 100% so":

> "The true distinction… is that internal DSLs are written in an executable language and parsed by executing the DSL within that language. In both JRuby and XML, a DSL is embedded into a carrier syntax, but we execute the JRuby code and just read the XML data structures." *(Ch. 3)*

### 5.3 Execution: run the model, or generate

"The simplest, and usually the best, is just to execute the Semantic Model itself… **Yet DSLs have no inherent need for code generation.**" Strongest case for generating: "when there is a difference between where you want to run the model and where you want to parse the DSL… You don't want to run a parser in your toaster or in SQL." Related: the parser drags unwanted dependencies into production — "which is why language workbenches tend to do code generation."

Even when generating, **keep a runnable model in the parsing environment**: experiment with execution without understanding the generator; test parsing and semantics without generating (faster, better isolated); run validations that catch errors *before* generation. Social argument for generating: "many developers find the kind of logic in a rich Semantic Model difficult to understand. Generating code… makes everything much more explicit and less like magic."

> "code generators are like snowshoes: If I'm hiking in winter over deep snow I really have to have them, but I'd never carry them on a summer day." *(Ch. 3)*

### 5.4 The parser, and the ghostly syntax tree

"parsing is a strongly hierarchical operation. When we parse text, we arrange the chunks into a tree structure." The same hierarchy exists in an internal DSL. Why the Semantic Model is not an AST:

> "people can use the syntax tree as a semantic model. Most of the time I would not do that, because the syntax tree is very tied to the syntax of the DSL script and thus couples the processing of the DSL to its syntax." *(Ch. 3, "The Workings of a Parser")*

The model is also typically much smaller and more meaningful than the tree. The tree is frequently **ghostly** — "formed on the call stack and processed as we walk it… you never see the whole tree, just the branch that you are currently processing." Where there's no strong hierarchy you simulate it with **Context Variables**. "The syntax tree may be ghostly, but it's still a useful mental tool."

### 5.5 Grammars, syntax, semantics

A **grammar** is "a set of rules which describe how a stream of text is turned into a syntax tree," made of **production rules**. "There is no such thing as *the* grammar for a language… we can recognize many different tree structures for a particular piece of language text." A grammar defines syntax only — "Depending on the context, `5 + 3` could mean `8` or `53`." Hence the operational, testable definition of semantics:

> "**if two expressions produce the same structure in the Semantic Model, they have the same semantics, even if their syntax is different.**" *(Ch. 3, "Grammars, Syntax, and Semantics")*

That is what makes "compare two syntaxes by comparing how they populate the model" a technique rather than a slogan. Grammars matter for internal DSLs too: "**This grammar helps you choose which of the various internal DSL patterns you might use.**" (An internal DSL involves two parses and two grammars: the host's, then the notional DSL grammar built as those instructions execute.)

### 5.6 Parsing data — three structures, each with a judgement

The canonical problem: a declaration in one branch is referenced from another, and the call stack has already forgotten it *(Ch. 3, "Parsing Data")*.

- **Symbol Table** — "a dictionary whose key is the identifier… and whose value is an object that represents the command in our parse." Stash on definition, look up on reference. "A crucial tool for making the cross-references."
- **Construction Builder** — a mutable intermediate with the same fields as a model object, for when the model object is read-only after construction but data arrives gradually. "Using a Construction Builder complicates the parser but I'd rather do that than alter the Semantic Model to forgo the benefits of read-only properties."
- **Context Variable** — holds "where you are" when the tree can't tell you. "in general I prefer to avoid them as much as possible… I tend to see them as a smell to be avoided."

### 5.7 Macros

**Textual macros** substitute text for text (naming a hex color once; `sqr(x)` → `x * x`). "macros have a number of awkward problems that make them difficult to use in practice. As a result, textual macros have pretty much fallen out of favor, and most mavens like me advise against them" *(Ch. 3, "Macros")*. **Syntactic macros** operate on valid host-language elements (Lisp, C++ templates) and are a core internal-DSL technique where available — "relatively few languages do."

### 5.8 Testing: three areas, because there are three seams

> "With DSLs, I can break testing down into three separate areas: testing the Semantic Model, testing the parser, and testing the scripts." *(Ch. 3, "Testing DSLs")*

**The model.** "standard testing practice, the same as you would use with any framework of objects… I don't really need the DSL at all — I can populate the model using the basic interface of the model itself." Prefer several *small* fixtures, each a minimal configuration exercising one feature, sharing an abstract superclass with common wiring, utilities, and custom assertions. Ordering rule: "As the test fixtures get more complex, however, I can simplify the test code by using the DSL to create fixtures. **I can do this if I have tests for the parser.**"

**The parser.** "the job of the parser is to populate the Semantic Model. So our testing of the parser is about writing small fragments of DSL and ensuring that they create the right structures." Asserting on individual model objects "may result in breaking encapsulation." Prefer **model comparison**: build the expected model with the command-query API, parse to get the actual, assert equivalence. Two refinements: use a **Notification** to collect every difference ("This way I find all differences instead of stopping at the first one") and make its report the failure message; and **compare in both directions**, since a one-way walk finds missing elements but not extra ones — "usually the code *is* out to get me."

**Invalid input tests.** "The first time you run such a test, it's interesting to see what happens. Often you'll get an obscure but violent error" — which may be acceptable. The real danger is the opposite:

> "It's worse if you supply an invalid DSL, parse it, and get no error at all. This would violate the principle of 'fail fast'… there is a distance between the original fault… and the later failure, and that distance makes it harder to find the fault." *(Ch. 3, "Invalid Input Tests")*

Where the check belongs is a responsibility argument: "Since the problem is that I'm creating an invalid structure in the Semantic Model, the responsibility to check for this problem is that of the Semantic Model." Then assert the resulting exception, which documents the behavior and detects changes to it. Calibrated stance on defensive checks: "In general, I don't do not-null assertions on my method arguments… **The exception is when this leads to a null that doesn't cause an immediate failure.**"

**The scripts.** "the DSL scripts are also code, and we should consider testing them."

> "I see testing as a double-check mechanism. When we write code and tests, we are specifying the same behavior using two different mechanisms, one involving abstractions (the code) and the other using examples (the tests). For anything of lasting value, we should always double-check." *(Ch. 3, "Testing the Scripts")*

Provide a test environment for fixtures, running scripts, and comparing results. Script tests double as integration tests. Visualizations help by the same double-check logic. And: "**testing scripts is a common use of DSLs as they fit well with the need for a limited, declarative language.**"

### 5.9 Handling errors

"There are many topics I'd like to have explored further in this book, but the top of that list is error handling." Compiler lore: "parsing and output generation are the easy part… the hard part was giving good error messages." Reality check: "Good diagnostics are a rarity even in successful DSLs" — a widely used graph tool reports only `syntax error near line 4`. The tradeoff: "Any time spent on improving error handling is time not spent adding other features… people do tolerate poor error diagnostics. After all, DSL scripts are small… But: In a heavily used library, good diagnostics can save a lot of time."

Cheapest practical advice: **support comments** terminated by line endings, enabling "the crudest error-finding technique of all — commenting out."

Where error handling lives: syntactic errors belong to the parser (some come free). Semantic errors are a real choice. For putting them in the model: "The model is really the right place to check the rules of semantically well-formed structures. You have all the information structured the way you need to think about it," and you need it there if more than one front end populates the model. Its disadvantage: "There's no link back to the source of the problem in the DSL script, not even an approximate line number." Three strategies, with verdict:

1. **Detection rules in the parser** — "makes it much harder to write the rules, as you are working on the level of the syntax tree… greater risk of duplicating the rules."
2. **Push syntactic info into the model** (line numbers on model objects) — "can make the Semantic Model much more complicated… the script may not map that cleanly to the model, which could result in error messages that are more confusing than helpful."
3. **(Preferred) Detect in the model; initiate from the parser.** Parse a chunk, populate, tell the model to look for errors; the model reports semantics, the parser adds script context. "**This separates the concerns of syntactic knowledge (in the parser) and semantic knowledge (in the model).**"

> "A useful approach is to divide error handling into initiation, detection, and reporting. This last strategy puts initiation in the parser, detection in the model, and reporting in both." *(Ch. 3, "Handling Errors")*

### 5.10 Migrating DSLs

> "One danger that DSL advocates need to guard against is the notion that first you design a DSL, then people use it. Like any other piece of software, a successful DSL will evolve." *(Ch. 3, "Migrating DSLs")*

"the DSL definition is essentially a published interface, and you have to deal with the consequences just the same." A *published* interface (as opposed to merely public) "is used by code written by a separate team," so you can't just rewrite the callers. Two approaches, no strong preference:

1. **Incremental migration** — ship a migration program with every release. **Keep each change small:** with ten changes, "don't create just one migration script… instead, create at least ten scripts. Change the DSL definition one feature at a time… migrations are much easier to write if they are small, and it's easy to chain multiple migrations together. As a result, you'll be able to write ten scripts much faster than one."
2. **Model-based migration** — available only because you have a Semantic Model. Keep one parser per released version, all populating the same model ("the parser's behavior is pretty simple, so it's not too much trouble to have several of them around"), plus a generator that emits a script from the model. Risk: "it's easy to lose stuff that doesn't matter for the semantics but is something that the script writers want to keep. Comments are the obvious example. This is exacerbated if there's too much smarts in the parser, although then the need to migrate this way may encourage the parsers to stay dumb — **which is a Good Thing.**" If v1 scripts can't produce a v2 model, keep a v1/intermediate model that can emit v2.

**Version statements.** Scripts should record their DSL version so migrations can trigger automatically. "While a version statement may add a bit of noise to the script, **it's something that's very hard to retrofit.**"

**Not migrating is an option.** "keep the version 1 parser and just let it populate the version 2 model… supporting the old scripts directly, if you can, is useful since it allows them to migrate at their own pace." Realism: automated migration schemes "have not been used much" for widely used libraries either.

> **SDK lens:** (1) **Layer validation the way Fowler layers error handling:** the domain layer owns invariants and produces semantic errors; the boundary layer (request parser, config loader, CLI) initiates validation and enriches errors with source context — field path, line number, request id — and neither duplicates the other's knowledge. Accumulate problems into a notification rather than failing on the first; add defensive argument checks only where their absence would *delay* failure. (2) **Absorb mutability into builders** so model objects stay immutable; a builder exists to protect an invariant-holding target, not merely to shorten a constructor. Treat ambient "current object" state — thread-locals, open scopes, implicit context — as the same smell Fowler assigns to Context Variables. (3) **Anything you publish is a published interface**, including your config schema. Plan migrations as many small steps, put a version marker in the format from day one because retrofitting is nearly impossible, and remember that continuing to accept old input is often cheaper and kinder than migrating it.

## 6. Internal DSL techniques

### 6.1 Framing: you are constrained by the host language

Internal DSLs need no grammars or parsing tools, but "every expression in the DSL must be a legal expression in the host," so much internal-DSL thinking is thinking about *host language features*. Ruby drove the recent impetus; most techniques transfer "if usually not as elegantly"; **Lisp is the doyen** *(Ch. 4, opening)*.

> "It's this mental shift that is the core difference between an internal DSL and just calling an API." … "fluency isn't as much about the style of syntax you use as it is about the way you name and factor the methods themselves." *(Ch. 4, "Fluent and Command-Query APIs")*

Two consequences. **Command-query separation** (queries return values and change nothing observable; commands change state and return nothing) is a principle Fowler strongly endorses, yet method chaining breaks it — his resolution is an explicit carve-out, not an excuse: "fluent interfaces follow a different set of rules, so I'm happy to allow it there." Which implies **you must always be able to say which style a given type is in.** **Naming rules differ by style**: command-query names must stand alone because "They are the labels on the buttons," while "With DSL naming, it's the sentence that comes first; the elements are named to fit in with that context."

### 6.2 The need for a parsing layer

Mixing a fluent and a command-query interface on one class is confusing. Use a layer of **Expression Builders** — objects whose *sole* task is to build a model of normal objects via a fluent interface, "effectively translating fluent sentences into a sequence of command-query API calls" *(Ch. 4, "The Need for a Parsing Layer")*.

The primary reason is separation of concerns, not style: language-processing code needs data relevant only *while* parsing, and "You should not have to understand the DSL to understand how the model operates." Payoff of the seam: independent testing of builders and model; **multiple parsers** over one model; independent evolution — "Important because DSLs, like any software, are hardly ever fixed." The one argument against: skip builders when the model objects are themselves fluent, which sometimes suits models used mainly fluently. Fowler usually prefers command-query on the model (more flexible across contexts; fluency often needs temporary parsing data).

> "In particular, I object to mixing a fluent and a command-query interface on the same objects—that's just too confusing." *(ibid.)*

### 6.3 Combining functions

"The difference between a command-query interface and a DSL centers around **how functions are combined**" *(Ch. 4, "Using Functions")*:

- **Method Chaining** — "for many people, the central pattern of a fluent interface." Ordinary OO derides these as "train wrecks," but read fluently they compose many calls without intermediate variables.
- **Function Sequence** — plain call statements; "function" not "method," because it works outside OO.
- **Nested Function** — calls as the *arguments* of higher-level calls.

**First choosing factor is scope.** Chaining contains scope naturally (methods live on the builder). Bare functions need resolution, and globals bring two problems: namespace pollution, and — more seriously — **global variables for parsing data**, since "you can't get away from global data if you use global functions." Cure: **Object Scoping** — put the DSL script in a subclass of an Expression Builder, so bare calls resolve to builder methods and connect to parsing data on the builder instance. "That's a compelling set of advantages for the cost of placing the DSL script in a builder subclass, so that's my default option." Bonus: users can add their own DSL methods by subclassing.

**Nested Function** buys three things: hierarchy echoed by the language constructs themselves; changed evaluation order (arguments first, so sub-objects arrive fully formed, often eliminating a context variable); and safety with global functions, since a global that only returns an object alters no parsing state. It costs four: punctuation noise; the same globalness problems (same cure); **backwards reading order**, inside-out — Neal Ford's "Old MacDonald" chorus renders as `o(i(e(i(e()))))`; and **positional rather than named arguments** — `disk(75, 7200)` doesn't say which is which. Wrapping values in naming functions (`disk(size(75), speed(7200))`) reads better but doesn't prevent misordering; preventing that needs richer token objects — "an annoying complication."

> "In many ways, Method Chaining is a mechanism that helps you supply keyword arguments to a language that lacks them." *(Ch. 4, "Using Functions")*

Fowler builds a hybrid (function sequence at top, nested functions for arguments, chaining for optional sub-values) then **rejects his own hybrid**, on a principle far broader than DSLs: "The punctuational differences are an artifact of the implementation, not the meaning of the DSL itself, so I'm exposing implementation issues to the user—always a suspicious idea." Mixed patterns produce punctuational confusion — commas here, periods there, semicolons elsewhere. A programmer copes; a non-programmer reader is more likely confused. "This tradeoff discussion is a microcosm of the decisions you'll need to make when building your own DSL."

### 6.4 Literal collections *(Ch. 4, "Literal Collections")*

- **Literal List** — same or different types, no fixed size; varargs is the common curly-brace introduction, and a nested function taking variable child calls is already a literal list in disguise. A general list literal syntax is usable in more contexts than only inside a call.
- **Literal Map** — best where an element has multiple optional sub-elements each settable at most once. Chaining names sub-elements well but you must hand-write "at most once"; a map bakes it in.
- **Named parameters** are better still where available (Smalltalk keyword messages) — but "even fewer languages have named parameters than have Literal Map syntax."
- A **symbol** type looks like a string but exists for map/symbol-table lookups: immutable, usually interned, no spaces or string operations. Use symbols where available, strings otherwise.

Lisp's appeal: convenient list literals, the *same* syntax for calls, bare words as symbols — an excellent internal-DSL basis "provided you are happy with your DSL having that fundamental syntax." That simplicity is both strength and weakness.

### 6.5 Using a grammar to choose constructs

Write the *logical grammar*; BNF rule shapes suggest internal constructs *(Ch. 4, "Using Grammars to Choose Internal Elements")*:

| Grammar structure | BNF form | Consider |
|---|---|---|
| Mandatory list | `parent ::= first second third` | Nested Function |
| Optional list | `parent ::= first maybeSecond? maybeThird?` | Method Chaining, Literal Map |
| Homogeneous bag | `parent ::= child*` | Literal List, Function Sequence |
| Heterogeneous bag | `parent ::= (this \| that \| theOther)*` | Method Chaining |
| Set | doesn't fit BNF | Literal Map |

Reasoning matters as much as the table. Mandatory elements match nested-function arguments directly — and with static typing, type-aware autocompletion suggests correct items per position (a *tooling* argument). Optional elements suit chaining because nested functions explode into overload combinations, and the method name says which element you're supplying. Homogeneous repeats suit a literal list — and if the expression defines top-level statements, "that is one of the few places I'd consider *Function Sequence*." Heterogeneous repeats suit chaining. A **set** fits BNF badly; a literal map is logical, and the problem you'll hit is "the inability to communicate and enforce the correct key names." At-least-once maps onto nothing well: use a general multiple-element form plus a check during the parse. **Each choice leaves a specific enforcement gap you must close in code:** uniqueness for chained optionals, key-name validity for maps, at-least-once for repeats.

### 6.6 Closures — Nested Closure

Three separable properties *(Ch. 4, "Closures")*:

1. **Inline nesting** — like a nested function, but you can put **any inline code** inside, so you can nest structures (e.g. a function sequence) impossible inside a nested function.
2. **Deferred evaluation** — "perhaps the most important capability that Nested Closure adds." Reorder, skip, or store closures for later. Especially valuable with an **Adaptive Model**, because the DSL can then include **sections of host code inside the DSL** and put those blocks into the model.
3. **Limited-scope variables** — a closure introduces variables scoped to itself, clarifying what the verbs act on and removing the need for global functions or Object Scoping, since the verbs live on the scoped variables (themselves Expression Builders).

Fowler frames validation as inherently **contextual** — you validate an object *in order to do something to it* — which is why a hard-coded "is this object valid" is insufficient and stored closures pay off. Caveat: Nested Closure is "often frustratingly awkward"; substitutes in languages without closures "require a lot of unwieldy syntax that can add a debilitating amount of noise." **Noise in the host closure syntax is a first-order design cost, not a cosmetic one.**

### 6.7 The remaining techniques, with their judgements

- **Parse Tree Manipulation** — treat a host expression's parse tree as data and emit something else (a query in another language). "a marginal technique — rarely needed, but very handy on the occasions that need arises." Design test: do you need to *retarget* the expression to a different execution engine? If you only need to *run* it, a plain closure is far simpler.
- **Annotation** — metadata on program constructs. Three advantages in the range-check example: reads as a property of the field; decouples *declaring* a rule from *when* it's enforced; and "specifies the validation rule in a form that could be read to configure a GUI widget" — the rule becomes reusable metadata rather than behavior. Think of annotations as new keywords. Being bound to the host language, they suit **fragmentary DSLs, not stand-alone ones**.
- **Literal Extension** — adding methods to library classes so a chain can start on a literal. The danger is that it **adds methods globally** when they should be scoped to DSL usage, sometimes with no way to discover where the extension came from; safer designs require an explicit namespace import.
- **Reducing syntactic noise.** **Textual Polishing** (write near-host syntax and text-substitute) — "not a big fan": "The substitutions get convoluted pretty quickly, and when they do it's much easier to use a full external DSL." **Syntax coloring** — de-emphasize noisy syntax when communicating with domain experts. A tooling answer, not a language answer.
- **Dynamic Reception** — intercept undefined-method calls to move information from arguments into method names. "You don't want to be encoding complicated structures into a sequence of method names. If you need anything more complicated than a single list of things, use something with more structure." Sharp rule: it works when you do the **same basic processing for each call**; if names would be handled differently, write explicit methods.
- **Type checking / Class Symbol Table.** Rather than re-fight static vs dynamic, Fowler raises the **tooling** argument: most DSL symbols are strings in your own table, so you hand-type quoted names with no autocompletion. A **Class Symbol Table** defines each symbol type as a class and declares a script's symbols as fields, buying bare identifiers and type-aware autocompletion. Honest cost is aesthetic: "The result, like many DSL constructs, looks rather strange… But it does result in an editing experience that meshes much more closely with the general experience of Java programming."

> **SDK lens:** Build in two layers — a plain, orthogonal, side-effect-disciplined core (judged one method at a time in an autocomplete list) plus a physically separate ergonomic/builder surface (judged by reading whole call chains aloud). Never put both styles on the same class. Choose your call shape from *the shape of what the caller must supply*: mandatory → positional/nested; optional → builder methods or an options map; repeated homogeneous → lists; sets → maps or named parameters — and close the enforcement gap each choice leaves. Keep the call shape uniform across the surface even at some cost in local elegance, because punctuation variety leaks implementation structure to the reader. Callbacks buy three separable things (nesting, deferred execution, scoped handles), and deferred execution is what lets user code be *stored as data* in your model — the basis of rule engines and configuration-as-code. Strings are the enemy of tooling: typed, declared symbols buy autocompletion, refactoring, and compile-time checks, and a little aesthetic oddity is a fair price.

## 7. External DSL techniques and the internal-vs-external decision

### 7.1 Framing, and a warning about the literature

External DSLs give **greater syntactic freedom — any syntax you like** — because parsing operates on pure text *(Ch. 5, opening)*. Orientation warning: the language community's tools and writings almost always assume a **general-purpose** language; DSLs "are lucky to get a mention in passing." Many principles carry over, but "you don't need to understand as much to work with DSLs."

### 7.2 Syntactic analysis strategy *(Ch. 5, "Syntactic Analysis Strategy")*

**Delimiter-Directed Translation** — chop input on delimiters (usually line endings), dispatch each chunk on a leading keyword. Pro: very simple, uses string splitting and regexes. Decisive con: "it doesn't give you any inherent way to handle the **hierarchic context** of your input… the more hierarchic context you get, the more effort you have to spend managing it yourself."

**Syntax-Directed Translation (SDT)** — start from a formal **grammar** in BNF. A grammar is a good way to think about syntax whether or not you use SDT (see §6.5), but works particularly well here because it translates mechanically into a parser that handles hierarchy.

| Approach | Strengths | Weaknesses |
|---|---|---|
| **Parser Generator** (grammar in, parser out) | Most sophisticated; mature; efficient on complex languages. BNF-as-DSL keeps the language easy to understand and maintain, **automatically tied to the parser**. | Take time to learn; mostly use code generation, so they **complicate the build**; may not exist for your platform. |
| **Recursive Descent Parser** (rule → function) | Easy to understand; clear BNF-operator-to-control-flow patterns; "powerful and efficient enough for a DSL." | **The grammar gets lost in the control flow.** |
| **Parser Combinator** (rule → object, composed) | Fowler's preference when a generator isn't available or feels heavyweight; **represents the grammar explicitly in the composing code** — close to true BNF. | Composition code isn't quite as clear as real BNF. |

"The biggest downside of Syntax-Directed Translation is that it's a technique that isn't as widely known as it should be." The fear "often comes from the fact that Syntax-Directed Translation is usually described in the context of parsing a general-purpose language—which introduces a lot of complexities that you don't face with a DSL."

### 7.3 Output production strategy *(Ch. 5, "Output Production Strategy")*

Know what your output is. Most of the time it should be a **Semantic Model**. Warning: the language community usually builds parsers that **directly produce output code with no Semantic Model in sight** — "bear this difference in mind" when reading their material, "which includes most documentation for tools such as Parser Generators."

1. **Embedded Translation** (single-step) — create the model *during* parsing, with parsing data in symbol tables. (Like SAX.)
2. **Tree Construction** (two-step) — parse into a **syntax tree** plus symbol table, then walk it to populate the model. (Like DOM.)
3. **Embedded Interpretation** — interpret during the parse; the output *is* the result. **Produces no Semantic Model.** Rare.

The real choice is between the first two. For Tree Construction: splits the problem into two simpler tasks; while recognizing text you focus only on building the tree; walking it afterwards is "a more regular programming exercise," and **you have the whole tree available**, whereas embedded translation only sees what has been parsed so far. Against: the memory objection (dismissed — it "withers away when processing small DSLs on modern hardware"), and his real reservation, that you write both tree-building and tree-walking code when often it is easier to build the model there and then.

> "So, I'm conflicted on the choice… My best advice is to try a little of both and see which you prefer." *(Ch. 5)*

Usable heuristic underneath: **the greater the distance between the DSL and the Semantic Model, the more the intermediate tree earns its keep.**

### 7.4 Parsing concepts that change design decisions *(Ch. 5, "Parsing Concepts")*

- **Separated lexing.** SDT usually splits *lexing* (text → typed tokens; a **Regex Table Lexer** is the easy way) from *syntactic analysis*. Two consequences bite. A keyword is a keyword everywhere — naming a state "initial state" collides with a `state` keyword unless you use **Alternative Tokenization**. And whitespace is discarded before parsing, making **syntactic whitespace** hard: it "intermixes the syntactic structure of the language with formatting," which mostly makes sense but has "just enough edge cases where the two needs don't quite line up… This is why many language people really hate syntactic whitespace." Separation exists because it decomposes a complicated task and is faster.
- **A grammar, not the grammar.** Two grammars can recognize the same language while producing **different parse trees, and therefore different output-generation code**. "Just like with any code, you refactor your grammars to make them easier to understand." And: "I often end up altering my grammar to make it easier to organize the code that translates source into the semantic model." **The grammar is code, not a pristine spec.**
- **Chomsky hierarchy, for its practical payoff only.** Regular grammars are finite-state machines and **can't handle nesting** ("regular grammars can't count"). Context-free grammars add hierarchy via a push-down machine — where most generators, recursive-descent, and combinator parsers live; their limit is declare-before-use across branches, "**which is exactly why symbol tables exist**." Context-sensitive: "we don't know how to write general context-sensitive parsers." Threefold payoff: it tells you which tool class you need (nesting ⇒ context-free ⇒ prefer SDT over delimiter-directed); a push-down machine "usually isn't overkill" even for a regular language; and it explains why lexing is separated. **PEGs** handle most context-free and some context-sensitive cases, typically without separated lexing.
- **Top-down (LL) vs bottom-up (LR).** Top-down "uses the rules as **goals** to direct what to look for"; bottom-up shifts and reduces. Bottom-up is harder to understand — you don't write the parser with a generator, "but you do have to understand roughly how it works in order to debug problems." Top-down's main wart is **left recursion**; left-factoring fixes it mechanically at some cost in readability, and you mostly hit it with nested operator expressions.

> "you shouldn't treat the grammar as a fixed definition of the DSL. Often, you'll need to alter the grammar to make the output production work better." *(Ch. 5, "Parsing Concepts")*

### 7.5 The escape hatch: Foreign Code

"One of the biggest dangers that you face with an external DSL is that it may accidentally evolve to become a general-purpose language" — and short of that, a long tail of rare special cases bloats it. **Foreign Code** embeds a small piece of a general-purpose language: "This code isn't parsed by the DSL's parser; rather, it is just slurped as a string and put into the *Semantic Model* for later processing."

> "This isn't as clear as extending the DSL would be, but this mechanism can handle a wide range of cases. **Should regex matching become a common condition, we can always extend the language later.**" *(Ch. 5, "Mixing-in Another Language")*

That is the whole pattern: an escape hatch for the long tail, promoted into first-class syntax once it stops being rare. Notes: dynamic hosts can interpret the fragment at runtime, static hosts need code generation weaving it into output; you must **tokenize foreign code differently** (Alternative Tokenization — simplest is clear delimiters slurped as one string, at some noise cost); the same technique embeds *another DSL*, though composing external DSLs is genuinely hard because parser technologies aren't suited to modular grammars.

### 7.6 XML as a carrier syntax

XML is a **carrier syntax** — "in much the same way that an internal DSL's host language provides a carrier syntax. (An internal DSL also provides **carrier semantics**.)" XML gives syntax only; a host language gives syntax *and* an execution model. Hence DOM ⇒ Tree Construction, SAX ⇒ Embedded Translation *(Ch. 5, "XML DSLs")*. His objection is noise: too many characters spent on structure rather than content, "making it much harder to understand what the code is trying to say — which spoils the whole purpose of DSLs."

The arguments for XML, and his answers: (1) *"Humans shouldn't write XML — it's a serialization behind a UI"* — reasonable, but it leaves DSL territory, and the UI becomes an *alternative to* a DSL; if you spend time reading the XML or its diffs, the UI is incidental. (2) *"XML parsers exist off the shelf"* — flawed, "stemming from a confusion about what parsing is"; parsing is **the whole route from input text to the Semantic Model**, and an XML parser only gets you to a DOM. (3) *Consistent quoting and escaping* — genuine; custom DSLs breed inconsistency. (4) *Error handling* — XML processors do well; custom languages cost more work. (5) *Schemas* — validate without executing, support smarter tools. (6) *Binding interfaces* — less useful, "because the structure of the Semantic Model will rarely match that of the DSL." (7) *Grammar vs schema* — few tools consume grammars while schema tools already exist, yielding: "**Often, an inferior but prevalent approach ends up being more useful than superior technologies.**"

> "The key to a DSL is readability; tooling helps with writing, but it's the reading that really counts." *(Ch. 5, "XML DSLs")*

**JSON and YAML** are less noisy and he likes them more, but "these languages are very much oriented towards structuring data, and as a result lack the flexibility you need to have a truly fluent language."

> "A DSL is different from a data serialization, just like a fluent API is different from a command-query API." *(ibid.)*

That is: **data serialization : DSL :: command-query API : fluent API.**

### 7.7 Choosing between internal and external — ten factors, no verdict

Ch. 6 opens candidly: "One of the great difficulties is the lack of information to base your choice on… my thoughts on this topic are more speculative than I would like."

1. **Learning curve.** Favors internal, but with nuance. SDT introduces genuinely new concepts and grammar-driven parsers "can look like magic"; documentation targets general-purpose language builders — "For many tools, the only documentation is a Ph.D. thesis." Escape routes: delimiter-directed translation (familiar, limited — "most of the time I think it's better to face the learning curve," but keep it for a regular language) and XML carrier syntax (he'd rather learn SDT, "as the resulting language is so much clearer to read"). Counterweight: internal DSLs are "not as easy as you'd think" — a familiar language used oddly, relying on obscure tricks. The structural difference is *when* you pay: internal lets you **mount the curve slowly**; SDT requires learning a lot to get going. **Conclusion: internal DSLs are easier to learn** — and the curve "applies not just to you but to anyone who wants to touch your code."
2. **Cost of building.** First time, the cost is the learning curve, and it goes away. Then separate "the cost of **building the model** from the cost of building the **DSL that layers over it**… the model has its own justification." Internal's extra cost is the Expression Builder layer, where "most of the effort isn't in getting them to work — it's in fiddling with the language." External's is the parser, "actually quite quick" once you're fluent in SDT. **Conclusion: "once you are familiar with the techniques, there's no big difference in cost."**
3. **Programmer familiarity.** True "to some extent" but less marked than assumed. **The biggest difference is tooling, not syntax.** Internal inherits the host IDE (you may need a Class Symbol Table specifically to *preserve* that). External: "you're unlikely to be offered anything but the most basic level of editing support"; syntax highlighting is easy, "but type-aware autocompletion is almost certainly beyond you."
4. **Communication with domain experts.** Internal DSLs are permanently tied to host syntax; programmers barely notice the noise, domain experts do. "such is the value of the communication channel that **I'd be inclined to push that bit harder and use an external DSL if it looks like it could make the difference.**" Hedge: start internal and switch later — "Since you can use the same Semantic Model for both, the incremental cost of building two DSLs isn't really that great."
5. **Mixing in the host language.** The **wafer-thin boundary** is a benefit: use the host where the DSL lacks a construct, use its abstraction facilities to build abstractions *on top of* the DSL, drop imperative chunks inside scripts. Build languages illustrate: Ant "suffered from **sliding into generality**, acquiring all manner of imperative constructs that don't suit its nature or syntax," while Rake mixes the dependency network with imperative code in nested closures. External mixing is possible (Foreign Code inward, strings outward) but awkward — "tools usually don't know what you are doing," and "it's hard to integrate symbols between the two environments." **"If you want to intermix host and DSL code, then an internal DSL is almost always the way to go."**
6. **Strong expressiveness boundary** — the mirror image, and the case *for* external. Free mixing "only really works if the users of the DSL are comfortable with the host language"; otherwise "throwing lumps of a host language into the DSL will usually only raise a communication barrier that the DSL was supposed to avoid." Also unhelpful when a different group writes the scripts. "often the benefit of a DSL is that **it produces a restricted range of what can be done.**" That restriction eases understanding, **serves as a barrier to bugs**, and **limits the kinds of things you need to test for** — "Pricing rules in a DSL aren't going to send arbitrary messages to your integration server." "Most of the time, this is good as it protects you from mistakes, **but it may also help with security.**"
7. **Runtime configuration.** External DSLs shift execution context "from **compile time to runtime**" naturally. Using an interpreted language alongside a compiled one and writing an internal DSL there **attenuates most internal-DSL advantages**: lost familiarity unless the team knows it, poorer tooling, no easy mixing of dynamic and static constructs, and no firm boundary around the DSL (losing factor 6).
8. **Sliding into generality** — the canonical external failure mode. James Duncan Davidson (Ant's creator): **"How do we prevent disasters like Ant occurring?"** Ant is "both a roaring success and a nightmare"; the real issue is that "over time it steadily grew in capability so that it no longer has the limited expressiveness that a DSL needs. This is a common road to heck" (Sendmail is the Unix equivalent) — "drop by drop, all the clarity that a good DSL has leaks out." **No simple answer:** "It needs a constant attention and determination to not let things get too complex." Three alternatives to growing one language: (a) let *other* languages develop for the complicated cases; (b) **layer another language over the base DSL whose output is that base DSL** — "a useful technique to allow abstractions to be built in a language that lacks abstraction-building features"; (c) switch to an internal DSL. Internal DSLs have the symmetric failure: "mixing with the host language gets so intertwined that you lose any sense of DSLness." **External DSLs bloat; internal DSLs dissolve.**
9. **Composing DSLs.** Internally, "composing is as easy as mixing them with the host language," plus the host's abstraction features. Externally it is much harder: most parser generators can't compose grammars — "another consequence of their focus on supporting general-purpose programming languages" — so you fall back to Foreign Code, "which is more clunky than it need be."
10. **Summing up.** *"My conclusion is that there is no conclusion. I don't see a clear, general advantage for internal or external DSLs. I'm not even sure I see some general guidelines to pontificate." (Ch. 6, "Summing Up")* What he does stress: **experimenting in both directions is cheaper than you think** if you have a Semantic Model. He endorses Glenn Vanderburg's approach — use an **internal DSL early, while you're still working out what you want**, then build an external one once things settle and you need its advantages.

> **SDK lens:** Read the ten factors as a checklist for any "should this be code or configuration?" decision. The two that most often decide it are **tooling** and **boundary strength**. A surface in the host language inherits the entire IDE — completion, refactoring, jump-to-definition, type errors — often worth more than syntactic elegance. A surface in a separate restricted format bounds the failure surface, test matrix, review burden, and attack surface, which is the real argument for declarative/sandboxed extension points over "just let them write code," and it says exactly when the argument applies: untrusted or non-programmer authors, or cross-team authorship. For the long tail of rare requirements, provide a general-purpose escape hatch rather than growing dozens of narrow options, and promote a case to first-class API only once demand is proven. Note Fowler's criterion for rejecting XML: *reading*, not writing and not tooling convenience.

## 8. Code generation, workbenches, lessons from real DSLs

### 8.1 Why generate, and the two-environment framing

Default remains: parse, populate, execute the model. Generation is the fallback for when the specified logic must run where a parser or model is difficult or impossible. It gives you **two environments**: the **DSL processor environment** (parser, model, generator — must be comfortable to develop in) and the **target environment**.

> "The point of using code generation is to separate the target environment from your DSL processor because you can't reasonably build the DSL processor in the target environment." *(Ch. 8)*

Four reasons the target forces your hand *(Ch. 8, opening)*: **(1) resource-constrained targets** that can't run a DSL processor; **(2) the target is itself a DSL** — limited expressiveness means it lacks abstraction facilities and extending it risks sliding into generality, so specify conditions in a DSL and **generate SQL**; **(3) lack of familiarity with the target environment**; **(4) to enforce static checking** — characterize an interface in a DSL, generate a typed API in the caller's language, and on change regenerate and **let the compiler point at the damage**.

### 8.2 Choosing what to generate: model-aware vs model-ignorant

Distinguished by whether an explicit model representation exists in the target *(Ch. 8, "Choosing What to Generate")*:

- **Model Ignorant Generation** embeds the model's logic into the target's **control flow** (nested conditionals on state then event). No model in the output.
- **Model-Aware Generation** puts some representation of the model into the output. It need not match the processor's model — nested maps will do — and may have no explicit classes, but **the data structure captures the behavior**.

Key structural insight: putting a model representation into the generated code makes **the generated code take on the same split between generic framework code and specific configuration code** identified in §2.3. Model-aware preserves that seam; model-ignorant folds it together. Consequences: with model-aware generation **the only thing you need to generate is the specific configuration**, and the generic machinery is built and tested by hand in the target environment; model-ignorant forces you to generate most of the critical behavior. "**My inclination, therefore, is to use Model-Aware Generation as much as possible.**"

Real exceptions: the target language may not represent a model as data easily (often the very reason you're generating), and processing limits may forbid it (embedded systems commonly use model-ignorant generation). Deployment bonus of model-aware: **replace only the configuration artifact** to change behavior, given a runtime binding mechanism. Pushed further, generate a **data file read entirely at runtime** — behavior changes at runtime at the cost of load code. Whether that file is "just another DSL" is settled by the authoring-vs-interchange test of §1.6.

### 8.3 How to generate: transformer vs templated, and the Embedment Helper

- **Transformer Generation** — code reads the model and emits target statements. Driven by input, output, or both.
- **Templated Generation** — start from a sample output file, insert markers where content is model-specific. Driven by output structure.

**Templated works best when there's a lot of static code and only a few dynamic bits** — "particularly since I can look at the template file and get a good sense of what gets generated" — so it pairs with model-ignorant generation. Otherwise, "actually, most of the time," Fowler prefers transformer generation. They mix in practice; the caveat is about *consciousness*, not purity:

> "The moment you stop being thoughtful about what you are doing is the moment when you start making an unmaintainable mess." *(Ch. 8, "How to Generate")*

Templated generation's biggest problem is host code **overwhelming the static template**. **Embedment Helper** is the fix, and Fowler calls it *vital*: hide all variable-element complexity in a class called by simple template method calls. **Each callout in a template should be a single method call; anything else belongs inside the helper.** Beyond readability the benefit is tooling — the helper is a normal class with full IDE support, whereas host code inside a foreign-extension file gets none, often not even syntax highlighting. Same problem elsewhere: grammar files "full of long code actions… bury the structure of the grammar."

### 8.4 Mixing generated and handwritten code *(Ch. 8)*

1. **Don't modify generated code.** Authority argument: **the DSL is the authoritative source**; generated code is "just an artifact." Hand-editing loses edits on regeneration and, worse, "introduces a reluctance to change the DSL and regenerate," undermining the whole point. Acknowledged exception: trace statements while debugging.
2. **Keep generated code clearly separate from handwritten code.** Preference: files are either all-generated or all-handwritten. Don't check generated code into the repository if the build can regenerate it; keep it in a separate branch of the source tree.

Three options for splitting a class: **multiple files per class** (easiest where the language supports partial classes); **marked regions within a file** — dismissed as clunky, inviting edits to generated code, and **forcing you to check generated code into version control, which confuses the version history**; and **Generation Gap**, the good solution — split **using inheritance**, generating a superclass and handwriting a subclass that augments and overrides, at the cost of **relaxed visibility rules** ("a small price to pay").

> "The difficulty of keeping the generated and handwritten code separate seems to be proportional to the pattern of calls between generated and handwritten code." *(Ch. 8)*

**A simple one-way flow of control makes separation much easier.** If you're struggling to keep them apart, simplify the control flow between them.

### 8.5 Generating readable code

Aim for readable output even though nobody edits it: **people will need to understand it when things go wrong.** Target: "almost as good as that I would write by hand." Precise exceptions: less inclined to work out the *best* structure; on duplication, avoid the obvious kind but "I don't have to worry about modifiability, only the readability" — if duplication is clearer, keep it; **happier to use comments than in handwritten code**, because **generated comments are guaranteed to stay up to date** and can **refer back to structures in the Semantic Model**; and will compromise structure for performance, as with handwritten code *(Ch. 8, "Generating Readable Code")*.

### 8.6 Preparse code generation

Generation as *input support for writing* scripts rather than output from them: if scripts need symbols matching an external system, generate typed constants for them and import them into script files. Checking can often happen when populating the model, "but sometimes it's useful to have the information in source code too, particularly for code navigation and static typing." **The payoff is IDE navigation and compile-time validity, not runtime behavior.**

### 8.7 Language workbenches — the durable principles

**Definition:** tools that help you build your own DSLs and **support building IDEs for editing those DSLs**, so script authors get programmer-grade support *(Ch. 9, opening)*. Fowler's caveats are heavy — written in early 2010 with most tools "barely left beta stage," deliberately given **no patterns**, covering only "core principles that don't change much." Assessment: "immense potential here — these are tools that could change the face of programming," but it "could end up like nuclear fusion's potential to solve all of our energy needs."

Workbenches define three aspects: **Semantic Model schema** (usually a **meta-model**), **DSL editing environment** (source or projectional), and **Semantic Model behavior** (most commonly code generation). They make the model the core but define it in a **meta-modeling structure that lets runtime tools work on the model**, which is what enables their tooling — and this produces a **separation between schema and behavior**, with behavior arriving from outside.

**Meta-models, and when not to use one.** A **schema** is what the model's contents can be; a **meta-model** is "a model whose instances define the schema for another model," letting you **manipulate the schema at runtime**; a DSL populating a meta-model is a **schema definition language**. **When rolling a DSL by hand, there usually isn't much point in creating a meta-model**: the host language's own structural definitions are easier to follow; you **lose static help** (generic field lookups instead of typed accessors — "I'm working *despite* my language rather than *with* it"); and biggest, you lose a proper OO domain model, since a meta-model does a "tolerable, if kludgy" job on structure but "it's really hard to define behavior." **The tradeoff inverts for workbenches precisely because tooling consumes the schema generically.** Distinction to keep: **a grammar defines the concrete syntax of a textual language; a schema definition language defines the structure of a Semantic Model's schema**, independent of any DSL that populates it.

**Structural constraints** are constraints on valid instances, "equivalent to invariants in Design by Contract" — distinguish those **implied by the data structure** ("we can't say anything in the Semantic Model that its schema can't store") from those **not** ("we can store it, but it's illegal" — a leg count of 7; a person as her own ancestor). The second is what the term means. Design rule: structural constraints **cannot change the Semantic Model, only query it** — "In this way they are a Production Rule System without any chaining."

### 8.8 Source vs projectional editing

**Source-based**: the program is defined in a representation **editable independently of the tools that process it** — in practice, text. **Projectional**: the core representation is a tool-specific persisted Semantic Model, and the tool **projects editable representations** (text, diagrams, tables, forms) *(Ch. 9, "Source and Projectional Editing")*.

Projectional advantages: **editing through different representations** (a state machine is best *thought of* as a diagram; source lets you visualize one but not edit it); **control over the editing experience**, making correct input easy and incorrect input impossible, with a tighter feedback cycle; **multiple projections** that all update from the shared model; and **semantic transformations** — renaming as a model operation, "particularly helpful for doing refactorings in a safe and efficient manner."

Why source still dominates, despite projectional editing being "hardly new":

- **Tool lock-in** — it "makes it hard to create an ecosystem where multiple tools collaborate over a common representation. Text, despite its many faults, is a common format."
- **Source code management is the killer example** — concurrent editing, diff, automated merge, transactional repository updates, and DVCS all work "because they operate only on text files. We see a sad situation where many tools that could really use intelligent repositories, diffs, and merges are unable to do so."
- **Pragmatic advantages of text** — emailing a snippet is trivial; text-processing tools automate transformations a projectional system may not offer.
- **The subtle one** — "it's often useful to type in something that doesn't work immediately, as a temporary step, while thinking through a solution." **The difference between helpful restriction and constraints on thinking is often a subtle one.**

**Model-assisted source editing** is "close to the best of both worlds": fundamentally source-based, with the IDE building a semantic model from sources and using projectional techniques to help. Cost is resources — parsing everything and keeping the model updated as you type.

**Vocabulary worth stealing for any system's artifacts:** the **editing representation** (what we edit), the **storage representation** (what we persist), the **executable representation** (what we run), and the **abstract representation** (a computer-oriented construct generated to ease processing). In source-based systems, source plays editing *and* storage roles at once.

### 8.9 Illustrative programming

Fowler's coinage for what projectional editing enables: putting a concrete **illustration** of program output in the foreground, with the program in the background. The spreadsheet is the argument — by "unscientific observation" the most popular programming environment in the world, mostly used by **lay programmers**; the visible thing is an illustrative calculation, the program hides in the formula bar. **The spreadsheet fuses execution with definition and makes you concentrate on the former.** It shares a property with heavy testing, "but with the difference that in a spreadsheet the test output has more visibility than the program."

Two boundary cases sharpen it: IDE projections are similar but derivable from **static** information, whereas **illustrative programming requires information from the actual running of the program**; and REPL snippets let you explore execution but don't "put the examples front and center." The downside is stated as firmly as the upside: "I don't think illustrative programming is all goodness." Spreadsheets and GUI designers reveal what a program does but **de-emphasize program structure**, so complicated ones are hard to understand and modify, "rife with uncontrolled copy-and-paste programming." The hard part is creating new abstractions: a screen builder "can only illustrate the abstractions it knows about."

### 8.10 Workbenches vs CASE tools, and the anti-lock-in stance

**The key technological difference from 1990s CASE tools: CASE did not give you the ability to define your own language.** The most important difference is cultural — the CASE world often **looked down on programming**, while workbench people come from programming. Evaluation tell: workbenches "tend to have strong support for code generation tools… This aspect tends to get missed during demonstrations, as it's less exciting than the projectional editing side, **but it's a sign of how seriously we should take the resulting tool**."

The concrete risk is **lock-in**: "Any code you write in one language workbench is impossible to export into another one." **The durable mitigation — treat the language workbench as a *parser*, not a full DSL environment.** Build the Semantic Model the usual way in your own code and use the workbench only for the editing environment, generating model-aware output against *your* model. "should you run into issues with your language workbench, it's only the parser that's affected. The most valuable stuff is in the Semantic Model which isn't locked in" *(Ch. 9, "Should You Use a Language Workbench?")*.

### 8.11 Lessons from real DSLs *(Ch. 10)*

- **Graphviz** — the clean-seam exemplar. Narrow scope affords authoring conveniences (nodes need not be declared; separators optional). Semantic Model as a plain data structure, populated by SDT + embedded translation, with helper functions called from grammar actions so **the grammar stays readable with short code actions**. "The real business of Graphviz occurs once the Semantic Model of nodes and arcs is populated" — layout and rendering, all independent of the parser.
- **JMock** — the highest-value entry for library authors. V1 composed **method chaining**, **nested functions** for argument-shaped parts, **object scoping** implemented by **forcing all mock-using tests into a subclass of the library class**, and **progressive interfaces**, where each chaining method returns a *narrower* interface exposing only what is legal next, "which allows the autocompletion in IDEs to guide you through writing the expectations in the right way." Expression Builders translate onto a model — Freeman and Pryce's **syntax layer** and **interpreter layer**.
  **Sharpest API point in the chapter:** the interplay of chaining and nested functions **determines who can extend the language**. Method chaining is **closed to users** (methods fixed on the builder); nested functions are **open** (users add them on their own test class or scoping subclass). *The choice is not stylistic; it decides your extension points.*
  V2 replaced the subclass requirement (which consumed the single-inheritance slot and dictated test-class structure) with an instance-initializer idiom Fowler reclassifies as a **Nested Closure** — "this does add some noise at the beginning of the expression," but "we can now define expectations **without being in a subclass**." It also split the method-call part from the return-value spec using a **function sequence**. The lesson is the arc: v1 optimized the expression and paid with a structural constraint on user code; v2 traded a little syntactic noise to remove it — the right trade.
- **CSS** — **written by non-programmers** ("Most CSS programmers don't call themselves programmers, but web designers"), one of the few exceptions to the read-don't-write rule. Genuinely declarative, and it shows **the dark side of declarative**: multiple matching rules force a specificity scheme, and "Many people find it hard to figure out how these rules work." **Limited expressiveness does not mean small** — "CSS is also quite large… DSLs can be limited in what they can express, but still have a lot to learn." It exhibits the general habit of **limited error handling** — browsers ignore bad input, so a syntax error "misbehaves silently, often making for some annoying debugging" (a cost, not a virtue). Most importantly it has **no way to create new abstractions** — "a common consequence of the limited expressiveness of DSLs" (no named palette colors, no size arithmetic). Two remedies: **macros** for simple cases, and **layering another DSL that generates the base DSL** (SASS), whose acceptance criteria are "the overlayed DSL needs to be similar (SASS uses the same attribute names), and **the user of the overlayed DSL usually also understands the underlying DSL**."
- **HQL** — queries in terms of application classes. Pipeline: input text → input AST → output AST → output text, all with one parser tool. "it's good to break down a complex transformation into several small transformations that can be easily plugged together." Nuance: the **SQL AST can be regarded as the Semantic Model** here, since an HQL query's meaning is its SQL rendering — "But more often than not, ASTs are not the right structure for a Semantic Model… But for source-to-source translation, using an AST of the output language makes a great deal of sense."
- **XAML** — "a screen layout is primarily a hierarchic structure, and stitching a hierarchy together in code is fiddlier than it ought to be." XML is defensible *specifically* when the domain is hierarchic and a familiar analogue exists. Brad Cross's distinction: a **compositional DSL** organizes relatively passive objects into a structure (XAML); a **computational DSL** produces a model that "feels more like code than data" (the state machine) — "You can do a lot more with a computational DSL, but people often find them more difficult to work with." Two implementation lessons: generated code as a **partial class** (the "multiple files per class" solution in the wild), and handwritten code **referring to controls by name**, which "allows me to change it without having to update the behavior code." Generalizes to: **nesting expresses trees; names express graphs** — a primary syntax decision.
- **FIT** — built on the observation "that nonprogrammers are quite comfortable with specifying examples in a tabular form." Tables embedded in documents, with **anything between the tables treated as comments** — "lets a domain expert use prose narrative to describe what they want, with tables providing something that's processable," an inversion of the usual code-to-comment ratio worth stealing. An **action fixture** is "essentially a simple imperative language… no conditionals or loops, just a sequence of verbs" (deliberate non-Turing-completeness); a **row fixture** is declarative; the two compose. Feedback is the input page re-rendered with check rows colored green or red. General claim: "Testing is a natural choice for a DSL… Tests often need to be read by domain experts."
- **Make and descendants** — builds use a **Dependency Network** because "many steps are expensive and don't need to be done every time." But the most interesting thing is *not* the computational model: it's "the fact that they need to **intermix their DSL with a more regular programming language**." Second structural problem: a simple dependency network needs further abstractions as builds grow, and the historical response is the same pattern three times — Automake generates Makefiles, Maven generates Ant scripts, SASS generates CSS. Rake is his preference (internal DSL, target contents in nested closures, host-language abstractions).

> **SDK lens:** Generation is a tooling and checking strategy at least as much as a portability one — the strongest case for a generated typed client is that spec drift becomes compile errors and users get autocompletion. When you generate, prefer emitting **configuration data consumed by hand-written generic code** over emitting control flow: the generic half stays testable in the target environment and only the small specific half is generated. Never hand-edit generated output, keep it in separate files rather than marked regions, don't commit it if you can regenerate it, prefer a one-way call direction between generated and handwritten code, and optimize output for *readability and debuggability* rather than modifiability — duplication is cheap when nobody maintains it, and generated comments pointing back at the model cannot rot. When you embed one language inside another's file, each embedded fragment should be a single call into a real module in its own native file, so tools can still see it. On metadata-driven design: runtime schemas and descriptors pay off exactly when *tooling* must consume them generically; when only human programmers consume them, native language constructs win. Keep any vendor tool at the edge and your model in your own code. Two rules the case studies keep repeating: **method chaining is the closed half of your API and free functions are the open half**, so put phase and ordering constraints in the chain and let users extend the vocabulary in their own scope; and **when a limited declarative surface needs abstraction, layer a generator over it rather than growing it** — provided the upper layer mirrors the base's vocabulary and its users still understand the base.
