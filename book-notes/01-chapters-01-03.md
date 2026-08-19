# Study Notes — Fowler, *Domain-Specific Languages* (2010), Part I, Chapters 1–3

Source: Martin Fowler with Rebecca Parsons, *Domain-Specific Languages*, Addison-Wesley 2010.
PDF page ranges covered (rendered pages, not print page numbers):

| Chapter | PDF pages |
|---|---|
| Part I front matter | 16 |
| Ch. 1 "An Introductory Example" | 16–30 |
| Ch. 2 "Using Domain-Specific Languages" | 30–43 |
| Ch. 3 "Implementing DSLs" | 43–60 (Ch. 4 begins on p. 61) |

Citation convention used below: (Fowler, DSL book, Ch. N "Title", section "Section Name").

---

## Chapter 1: An Introductory Example

Fowler's stated method for this chapter: start with a concrete example, then generalize into a definition in Ch. 2. The whole chapter is one worked example shown in five or six different notations, which lets him introduce every major concept in the book (semantic model, internal/external DSL, code generation, language workbench, visualization) as a *variation on the same underlying model*.

### 1.1 "Gothic Security" — the setup

A fictional company installs building-security systems: wireless sensors emit four-character event codes (e.g. a drawer opening emits `D2OP`), and control devices respond to four-character command codes (e.g. `D1UL` unlocks a door). At the center sits a controller (a Java-enabled toaster) running a control program.

**The key structural observation, and the reason a DSL is even on the table:**

> "What we have is a family of systems that share most components and behaviors, but have some important differences." (Fowler, DSL book, Ch. 1 "An Introductory Example", section "Gothic Security")

Concretely: the *way the controller sends and receives messages* is the same for every customer; the *sequence of events and commands* differs per customer. The business requirement — install a new system with minimum effort — becomes a software requirement: it must be easy to program the sequence of actions into the controller.

**Principle (variability analysis precedes language design).** Before you design a language, identify the axis of variation. The DSL will express only the varying part; the invariant part belongs in a library. This framing recurs throughout the chapter as "separation of common code from variable code."

**Choosing the abstraction.** Looking across many customers, a state machine emerges as a good way to think about the controller: each sensor sends an event that can change state; entering a state can emit command messages. Fowler is candid that he picked the state machine first and invented the gothic castle around it, because a state machine makes a good DSL example.

### 1.2 "Miss Grant's Controller" — the concrete instance

Miss Grant's secret compartment opens when she closes the door, then opens the second drawer and turns on the bedside light *in either order*. This yields the classic diamond-shaped state diagram: `idle → active → (waitingForDrawer | waitingForLight) → unlockedPanel`.

**Reset events — a judgement call worth noting.** The customers' controllers have a distinct idle state where they spend most of their time. Certain events (here, `doorOpened`) should snap the machine back to idle from anywhere. This does not fit any classical state machine model — Fowler starts from a well-known variant and adds a twist unique to this context.

He is explicit that reset events are **not strictly necessary**: you could add a `doorOpened` transition to every state leading to idle, and he even shows the code that would synthesize exactly that. He keeps the explicit reset-event concept anyway:

> "I prefer explicit reset events on the machine because that better expresses my intent." (Fowler, DSL book, Ch. 1, section "The State Machine Model")

**Principle (intent over minimality).** A redundant modeling construct earns its place if it makes the intent of both the general machine and each particular machine clearer. He acknowledges the cost — "it does complicate the machine a bit" — and accepts it. This is the first of many explicit cost/benefit judgements in the book, and the pattern of *stating the tradeoff rather than asserting a rule* is characteristic.

**Principle (design the abstraction to fit the domain, not the textbook).** The domain justified deviating from the standard state machine formalism. Fowler doesn't apologize for the deviation; he names it.

### 1.3 "The State Machine Model" — building the model first

Once the team decides a state machine is a good abstraction for *specifying* how controllers work, the next step is to put that abstraction into the software itself.

> "If people want to think about controller behavior with events, states, and transitions, then we want that vocabulary to be present in the software code too." (Fowler, DSL book, Ch. 1, section "The State Machine Model")

Cross-references: this is the **Ubiquitous Language** principle from Evans' *Domain-Driven Design* [evans-ddd] — a shared language between domain people and programmers. The natural Java realization is a **Domain Model** [poeaa].

**What the model looks like conceptually** (deliberately not transcribing code):

- `StateMachine` — holds the start state and a list of reset events. Other states are *derived*, not stored: they're whatever is reachable from the start state (a graph walk). Nice judgement: don't store what you can compute from the object graph.
- `State` — a name, an ordered list of commands to execute on entry, and a map from event code to `Transition`.
- `Transition` — source state, trigger event, target state. A first-class object rather than a bare map entry.
- `Event` and `Command` — both hold a symbolic name and a four-character wire code. They share an `AbstractEvent` superclass but are **kept as separate classes** because they play different roles in the controller. (Principle: type-separate things that are structurally identical but semantically distinct, when they occupy different roles in the design.)
- `Controller` — holds the current state, the machine, and a command channel. Its behavior is tiny: on an incoming event code, transition if the current state has a matching transition; else if it's a reset event, go to the start state; else *ignore silently*. On entering a state, execute that state's commands.

**Principle (symbolic names over wire codes).** The wire protocol uses four-letter codes; the model refers to events and commands by symbolic names and keeps the codes as data. This is the first layer of the "DSL as a more humane surface" idea — even the plain object model is already translating from machine vocabulary to human vocabulary.

**Principle (behavior can be trivially small once the structure is right).** Fowler notes the behavior "is really quite simple" after the structure is settled. Most of the design effort goes into the structure of the model; the interpreter over it is a handful of lines.

### 1.4 "Programming Miss Grant's Controller" — configuration vs. framework

Configuring the model for one customer means a block of Java that creates events, commands and states, then wires transitions and actions. Fowler stops and points at the seam:

> "The earlier code described how to build the state machine model; this last bit of code is about configuring that model for one particular controller. You often see divisions like this. On the one hand is the library, framework, or component implementation code; on the other is configuration or component assembly code. Essentially, it is the separation of common code from variable code." (Fowler, DSL book, Ch. 1, section "Programming Miss Grant's Controller")

Figure 1.3 in the book shows one compiled library copied into many installations, each with its own configuration code.

**SDK relevance (high).** This is the core library/SDK architecture statement of the chapter: a library is the common code; the client's usage is the configuration/assembly code; a DSL is an improved notation for the assembly code. Everything downstream (fluent interfaces, expression builders) is about making that assembly code readable, not about making the library more capable.

#### Representation 1: XML

The same configuration expressed as XML. Advantages Fowler lists:

1. **No per-customer compilation.** Ship one JAR (state machine components plus a parser) plus an XML file read at startup. Behavior changes require no new JAR distribution.
2. **Expressiveness.** No variable shuffling; a declarative structure where actions and transitions are subelements of a state, which "in many ways reads much more clearly."
3. **Constrained expressiveness as a feature.** "We're also limited in that we can only express configuration in this file — limitations like this are often helpful because they can reduce the chances of people making mistakes in the component assembly code."

Costs:

- Many syntax mistakes are only detectable at runtime. XML schema helps somewhat. Fowler's mitigation is extensive testing: "which catches most of the errors with compile-time checking, together with other faults that type checking can't spot. With this kind of testing in place, I worry much less about moving error detection to runtime."
- **Tradeoff articulated:** compile-time safety vs. runtime reconfigurability. He accepts moving error detection later *because* he has a strong testing practice; the judgement is conditional on that practice, not absolute.

**On "declarative".** He notes the term is cloudy: "it generally applies to approaches that move away from the imperative model." The XML step is *a* step in that direction (subelements instead of variable shuffling), not a binary switch.

He observes drily that these advantages are why so many Java/C# frameworks are configured with XML — "it sometimes feels like you're doing more programming with XML than with your main programming language."

#### Representation 2: a custom textual syntax

An invented terse syntax with `events ... end`, `state idle ... end`, `doorClosed => active`, `actions {unlockDoor lockPanel}`. Fowler's claims: easier to write and above all easier to *read* than XML; terser; avoids quoting and noise characters. "You probably wouldn't have done it exactly the same way, but the point is that you can construct whatever syntax you and your team prefer." Load at runtime if you want, or at compile time if you prefer.

**Characteristics that make this a DSL** (this is the first working definition, by enumeration):

- Suitable only for a very narrow purpose — it can't do anything other than configure this particular kind of state machine.
- Very simple — no control structures. **Not Turing-complete.**
- You couldn't write a whole application in it; it describes one small aspect of an application, so it **must be combined with other languages** to get anything done.
- That simplicity makes it easy to edit and process.

**The communication benefit, hedged carefully.** The people who install systems may be able to read the DSL and understand how it's supposed to work, even without understanding the Java controller. "Even if they only read the DSL, that may be enough to have to spot errors or to communicate effectively with the Java developers."

> "While there are many practical difficulties in building a DSL that acts as a communication medium with domain experts and business analysts like this, the benefit of bridging the most difficult communication gap in software development is usually worth the attempt." (Fowler, DSL book, Ch. 1, section "Programming Miss Grant's Controller")

**Is the XML version a DSL?** Fowler says yes — it's "wrapped in an XML carrier syntax, but it's still a DSL." The XML-vs-custom-syntax choice is a *design* issue, not a definitional one. XML is easier to parse because people are familiar with parsing XML, though he notes it took him about the same amount of time to write either parser. He contends the custom syntax is much easier to read here. Whichever you choose, "the core tradeoffs of DSLs are the same. Indeed, you can argue that most XML configuration files are essentially DSLs."

#### Representation 3: Ruby (internal DSL)

The same configuration in a subset of Ruby, using symbols and blocks so it reads almost like the custom syntax. Noisier than the custom language, still clear.

> "I'm embedding the DSL into Ruby, using a subset of Ruby as my syntax. To an extent, this is more a matter of attitude than of anything else. I'm choosing to look at the Ruby code through DSL glasses." (Fowler, DSL book, Ch. 1, section "Programming Miss Grant's Controller")

**Definitions introduced here:**

- **External DSL** — a DSL represented in a language separate from the main programming language it works with. May use a custom syntax or follow another representation such as XML.
- **Internal DSL** — a DSL represented within the syntax of a general-purpose language; a stylized use of that language for a domain-specific purpose.
- **Embedded DSL** — a widely used synonym for internal DSL that Fowler *avoids*, because "embedded language" also means scripting languages embedded within applications (VBA in Excel, Scheme in the Gimp).

#### Representation 4: Java (internal DSL) — and the API/DSL boundary

Is the original Java configuration code a DSL? Fowler says **no**: "That code feels like stitching things together with an API, while the Ruby code above has more of the feel of a declarative language." He then shows a Java version — a subclass of a `StateMachineBuilder` with declared fields and a `defineStateMachine()` method using chained calls like `.transition(doorClosed).to(active)` — which he *does* call a DSL: "It's formatted oddly, and uses some unusual programming conventions, but it is valid Java... it still has that declarative flow that a DSL needs."

**Definitions:**

- **Fluent interface** — another term for an internal DSL, emphasizing that an internal DSL is really just a particular kind of API designed with this elusive quality of fluency.
- **Command-query API** — Fowler's name for a *non*-fluent API, coined because the distinction needs a name for the other side.

The difference between an internal DSL and a normal API "comes down to the rather fuzzy notion of a language-like flow." (Elaborated in Ch. 2, "Boundaries of DSLs".)

**SDK relevance (high).** Two named points on a spectrum, not two categories. The same underlying model supports both; the fluent version is an additional, optional surface.

### 1.5 "Languages and Semantic Model" — the central architectural idea

This is the most important section in the chapter.

**The role of the DSL is to populate the model.** When the parser sees `doorClosed D1CL`, it creates an `Event` object and stashes it in a **Symbol Table** so that when it later sees `doorClosed => active` it can resolve the reference and call `addTransition`.

> "The model is the engine that provides the behavior of the state machine. Indeed you can say that most of the power of this design comes from having this model. All the DSL does is provide a readable way of populating that model — that is the difference from the command-query API I started with." (Fowler, DSL book, Ch. 1, section "Languages and Semantic Model")

**Definition — Semantic Model.** From the DSL's point of view, the object model being populated is the **Semantic Model**. Syntax = the legal expressions of the program (captured by the grammar in the external case); semantics = what the program *means*, what it does when it executes. Here, the model *is* the semantics. If you're used to **Domain Model** [poeaa], think of Semantic Model as very close to the same thing for now — but they are deliberately distinguished (Ch. 3 and the Semantic Model pattern chapter). It is also **not** an abstract syntax tree (see Ch. 3, "The Workings of a Parser").

**Fowler's strongest normative claim in the chapter:**

> "One opinion I've formed is that the Semantic Model is a vital part of a well-designed DSL. In the wild you'll find some DSLs use a Semantic Model and some do not, but I'm very much of the opinion that you should almost always use a Semantic Model." (Fowler, DSL book, Ch. 1, section "Languages and Semantic Model")

He notes he can almost never find a universally applicable rule, hence the "almost."

**Why — the enumerated benefits (these are seam/separation-of-concerns arguments):**

1. **Clear separation of concerns** between parsing a language and the resulting semantics.
2. You can reason about, enhance, and debug the state machine **without worrying about language issues**.
3. You can **test the model** by populating it with a command-query interface — no parser involved.
4. You can **evolve model and DSL independently**: build new features into the model before figuring out how to expose them in the language.
5. "Perhaps the most important point is that I can test the model independently of futzing around with the language."
6. Evidence from the chapter: *every* DSL variation shown (XML, custom syntax, Ruby, Java-fluent) was built on top of the same Semantic Model and created exactly the same configuration of objects.

**Form of the Semantic Model.** Here it's an object model. It can also be "a pure data structure with all behavior in separate functions" — still a Semantic Model, "because the data structure captures the particular meaning of the DSL script in the context of those functions."

**The crucial attribution point — model benefits are not DSL benefits.**

> "Looking at it from this point of view, the DSL merely acts as a mechanism for expressing how the model is configured. Much of the benefits of using this approach comes from the model rather than the DSLs." (Fowler, DSL book, Ch. 1, section "Languages and Semantic Model")

Specifically: easy configuration of a new customer's machine is a property of the model; runtime change without recompiling is a feature of the model; reuse across installations is a property of the model. "Hence the DSL is merely a thin facade over the model."

A model provides many benefits with no DSL present at all — that's why we use libraries and frameworks, and why we build abstractions inside our own software. "Good models, whether published as libraries or frameworks or just serving our own code, can work just fine without any DSL in sight." A DSL *enhances* a model: it makes it easier to understand what a particular machine does, and some DSLs allow runtime configuration. "DSLs are thus a useful adjunct to some models."

**Adaptive Model.** A state machine is a model whose *population acts as the program* for the system: to change behavior, you alter the objects and their interrelationships rather than the code. Fowler calls this an **Adaptive Model**. Consequence: it blurs the code/data distinction — to understand behavior you must look at how object instances are wired together, not just at the code. Every program varies with its data, but here "the presence of the state objects alters the behavior of the system to a significantly greater degree."

> "Adaptive Models can be very powerful, but they are also often difficult to use because people can't see any code that defines the particular behavior. A DSL is valuable because it provides an explicit way to represent that code in a form that gives people the sensation of programming the state machine." (Fowler, DSL book, Ch. 1, section "Languages and Semantic Model")

**Alternative computational models.** A state machine is one; Fowler cross-references **Production Rule System** and **Dependency Network** as others. "Using an Adaptive Model is a good way to provide an alternative computational model, and a DSL is good way to make it easier to program that model." People often call DSLs used this way *declarative programming*.

**Order of construction is not fixed.** He built the model first and layered a DSL over it because that's the easiest way to explain how DSLs fit into software development, and it's a common case — but not the only one. In another scenario you talk with domain experts, posit that the state machine approach is something they understand, and **build the DSL and model simultaneously**. (Expanded in Ch. 2, "DSL Lifecycle".)

### 1.6 "Using Code Generation"

**Definitions:**

- **Interpretation** — parse the text and immediately produce the result you want from the program. (He uses "interpret" strictly to mean this immediate execution, acknowledging the word carries other connotations.)
- **Compilation** — parse the program text and produce an intermediate output, which is then separately processed to provide the desired behavior. "In the context of DSLs, the compilation approach is usually referred to as **code generation**."

Illustrated with an eligibility-rule example (`age between 21 and 40`):

- *Interpreted* (Fig. 1.5): the parser and the Semantic Model both live inside the runtime processor. Rules are parsed at startup; each candidate is run against the Semantic Model.
- *Compiled* (Fig. 1.6): the parser loads the Semantic Model **as part of the build**; a generator emits code (`candidate.age >= 21 && candidate.age <= 40`) which is compiled and packaged into the runtime processor. No parser or model in production.

**Costs of code generation.**

- It usually forces an extra compilation step: compile the framework and parser → run the parser to generate source → compile the generated source. "This makes your build process much more complicated."

**Advantages / when you must.**

- No reason to generate code in the same language you parsed with; you can dodge the second compile step by generating for a dynamic language (JavaScript, JRuby).
- Useful when the target platform has no DSL tooling — generate C for an old toaster that only understands compiled C. Fowler cites recent projects generating MathCAD, SQL, and COBOL.

**Fowler's stance:**

> "Many writings on DSLs focus on code generation, even to the point of making code generation the primary aim of the exercise... In my view, however, code generation is merely an implementation mechanism, one that isn't actually needed in most cases." (Fowler, DSL book, Ch. 1, section "Using Code Generation")

**Anti-pattern called out.** Code generation is the common case where people skip the Semantic Model and parse input text directly into generated code. "Although this is a common way of working with code-generating DSLs, it isn't one I recommend for any but the very simplest cases."

Using a Semantic Model instead lets you separate **parsing**, **execution semantics**, and **code generation** — three concerns, three seams. Concrete payoffs he names:

- Change your DSL from internal to external without altering the code generation routines.
- Generate multiple outputs without complicating the parser.
- Use both an interpreted model *and* code generation off the same Semantic Model.

"As a result, for most of my book, I'm going to assume that a Semantic Model is present and is the center of the DSL effort."

**Two styles of code generation, and a preference.**

1. Generate "first-pass" code intended as a template that is then modified by hand.
2. Ensure generated code is **never touched by hand** (perhaps except tracing during debugging).

> "I almost always prefer the latter because this allows code to be regenerated freely. This is particularly true with DSLs, since we want the DSL to be the primary representation of the logic that the DSL defines." (Fowler, DSL book, Ch. 1, section "Using Code Generation")

Consequence: generated code must not be hand-edited, "although it can call, and be called by, handwritten code." **Principle: preserve a single source of truth; the DSL script is the source, generated artifacts are derived.**

### 1.7 "Using Language Workbenches"

**Definition — language workbench:** "an environment designed to help people create new DSLs, together with high-quality tooling required to use those DSLs effectively."

**The problem it addresses.** A big disadvantage of external DSLs is limited tooling — "setting up syntax highlighting in a text editor is about as far as most people go." You can argue the simplicity and small size of DSL scripts makes that enough, but there's also an argument for the sophisticated tooling modern IDEs provide. Workbenches let you define not just a parser but a **custom editing environment** for the language.

**The genuinely novel part.** Workbenches let a DSL designer go beyond text-based source editing to different *forms* of language — most obviously diagrammatic languages (specify the state machine directly as a state transition diagram). They also allow multiple *projections* of one script: Fig. 1.7 (MetaEdit) shows the same machine as a diagram, a tree of states/events, and a table for entering event codes (which can be omitted from the diagram if it's cluttered). Fowler reports the tool let him define the Semantic Model for state machines, define graphical and tabular editors, and write a code generator from the Semantic Model.

**Skepticism, fairly stated.** "Many developers are naturally suspicious of such doodleware tools. There are some very pragmatic reasons why a textual source representation makes sense." Other tools head the other way — post-IntelliJ capabilities like syntax-directed editing and autocompletion for *textual* languages.

**The spreadsheet argument.** Workbenches are often pitched as letting nonprogrammers program; Fowler sniffs at this ("that was the original intent of COBOL") but concedes spreadsheets are arguably the most successful programming environment we currently know. Two characteristics he draws out:

1. **Close integration of tooling into the programming environment.** "There's no notion of a tool-independent text representation that's processed by a parser. The tools and the language are closely intertwined and designed together."
2. **Illustrative programming** (his coinage). In a spreadsheet, what is most visible is not the formulae but the numbers — an illustration of what the program does when it executes. In most programming languages the program is front-and-center and you only see output when you make a test run; in a spreadsheet the output is front-and-center and you only see the program when you click a cell. Fowler thinks this is an important part of what makes spreadsheets accessible to lay programmers. Disadvantage: "the lack of focus on program structure leads to lots of copy-paste programming and poorly structured programs."

**Prediction / caveat.** "I think that language workbenches have a remarkable potential. If they fulfill this they could entirely change the face of software development." But at the time of writing it's early days, tools evolve rapidly, so the book only sketches them (with a chapter at the end). His suspicion: the languages workbenches produce "won't be anything like what we consider a programming language" — closer to spreadsheets than to the DSLs the book discusses.

### 1.8 "Visualization"

The state diagram in Fig. 1.7 isn't hand-drawn — Fowler **generated it from the Semantic Model** of Miss Grant's controller. The state machine classes not only execute; they render themselves in the DOT language (Graphviz), which lays out the graph automatically.

**Definition — visualization:** an alternative representation of a DSL script, similar to the DSL itself in that it lets a human understand the model, but **not editable**. "The visualization differs from the source in that it isn't editable — but on the other hand, it can do something an editable form cannot, such as render diagram like this."

**Principles:**

- Visualizations need not be graphical. Fowler uses simple *textual* visualizations to debug while writing a parser; he's seen teams generate Excel visualizations to communicate with domain experts.
- "Once you have done the hard work of creating a Semantic Model, adding visualizations is really easy."
- **Visualizations are produced from the model, not from the DSL — so you can build them even if you aren't using a DSL to populate the model.** This is another concrete payoff of the model/language separation, and (per Ch. 2) a genuine *alternative* to a DSL when the only goal is domain-expert comprehension.

**SDK relevance (Ch. 1 overall).** The chapter's architecture — invariant library + variable configuration; a semantic model as the sole source of behavior; multiple front-ends (imperative API, fluent API, config file, generated code, rendered diagram) all projecting onto that one model — is directly transferable to SDK design. Ship the model; make the fluent surface a thin, replaceable facade; keep every derived artifact (docs, diagrams, generated bindings) generated from the model rather than hand-maintained.

---

## Chapter 2: Using Domain-Specific Languages

Purpose: give the general definition, and discuss benefits and problems, *before* implementation techniques, so the reader has context.

### 2.1 "Defining Domain-Specific Languages"

Fowler concedes the term has very blurred boundaries and has never had a firm definition, but insists a definition is valuable for this book.

> **Domain-specific language** (noun): a computer programming language of limited expressiveness focused on a particular domain. (Fowler, DSL book, Ch. 2 "Using Domain-Specific Languages", section "Defining Domain-Specific Languages")

**Four key elements:**

1. **Computer programming language** — used by humans to instruct a computer. Structured to be easy for humans to understand, but still executable by a computer.
2. **Language nature** — it is a *language*, so it should have a sense of **fluency**, "where the expressiveness comes not just from individual expressions but also from the way they can by composed together."
3. **Limited expressiveness** — a general-purpose language provides varied data, control, and abstraction structures, all of which make it harder to learn and use. "A DSL supports a bare minimum of features needed to support its domain. You can't build an entire software system in a DSL; rather, you use a DSL for one particular aspect of a system."
4. **Domain focus** — "A limited language is only useful if it has a clear focus on a small domain. The domain focus is what makes a limited language worthwhile."

**Ordering matters.** Domain focus comes *last* and "is merely a consequence of the limited expressiveness." Many people use a literal definition ("a language for a specific domain") but literal definitions are often incorrect — his analogy: we don't call coins "compact discs" even though they're discs more compact than the ones we do apply the term to.

**Three categories:**

- **External DSL** — separate from the main language of the application. Usually a custom syntax, but another language's syntax is also common (XML being frequent). Parsed by code in the host application using text parsing techniques. The Unix tradition of little languages fits this style. Examples the reader will already know: regular expressions, SQL, Awk, and XML config files for Struts and Hibernate.
- **Internal DSL** — a particular *way of using* a general-purpose language. The script is valid code in the host language but uses only a subset of features in a particular style to handle one small aspect of the system. "The result should have the feel of a custom language, rather than its host language." Classic example: Lisp. Ruby has developed a strong DSL culture; Rails "is often seen as a collection of DSLs."
- **Language workbench** — a specialized IDE for defining and building DSLs; used not just to determine the structure of a DSL but also as a custom editing environment for writing scripts. "The resulting scripts intimately combine the editing environment and the language."

**A community/tooling observation with practical bite.** The three styles have developed separate communities. "You'll find people who are very experienced in internal DSLs but have no idea how to build an external DSL. I find this problematic because, as a result, people may not choose the best tool for the job." He recounts a team using very clever internal DSL processing to support a custom syntax which he's convinced would have been much easier as an external DSL — "since they didn't know how to build external DSLs, they didn't have that option open to them." Hence the book covers both clearly. (He's "rather more sketchy on language workbenches as they are so new and still evolving.")

**DSL as a way of manipulating an abstraction.** In software we build abstractions and then manipulate them, often on multiple levels. The most common way to build an abstraction is a library or framework; the most common way to manipulate it is command-query API calls.

> "In this view a DSL is a front-end to a library providing a different style of manipulation to the command-query API. In this context, the library is the Semantic Model of the DSL. A consequence of this is that DSLs tend to follow libraries, and indeed I consider a Semantic Model to be a necessary adjunct to a well-built DSL." (Fowler, DSL book, Ch. 2, section "Defining Domain-Specific Languages")

> "When people talk about DSLs, it's easy to think that building the DSL is the hard work. In fact, usually the hard work is building the model; the DSL then just layers on top of it. It still takes effort to get a DSL that works well, but that effort is usually much smaller than for building the underlying model." (ibid.)

**SDK relevance (high).** The DSL is a front-end to a library. Get the library right first; a fluent surface over a bad model just makes the bad model easier to reach.

#### 2.1.1 "Boundaries of DSLs"

The distinguishing characteristics are language nature, domain focus, and limited expressiveness. "As it turns out, the domain focus isn't a good boundary condition — the boundaries more commonly revolve around limited expressiveness and the language nature."

**Internal DSL vs. command-query API.** "In many ways, an internal DSL is nothing more than a quirky API (as the old Bell labs saying goes, 'Library design is language design')." The heart of the difference is the language nature.

> Mike Roberts' formulation, quoted by Fowler: "a command-query API defines the vocabulary of the abstraction, whereas an internal DSL adds a grammar." (Fowler, DSL book, Ch. 2, section "Boundaries of DSLs")

The practical test Fowler gives: a common way to document a class with a command-query API is to list all its methods, and **each method should make sense on its own** — a list of "words," each with a somewhat self-sufficient meaning. By contrast, "the methods of an internal DSL often only make sense in the context of a larger expression in the DSL." His example is `to` in `.transition(lightOn).to(unlockedPanel)`: "Such a method would be a bad name in a command-query API, but fits inside a phrase."

> "As a result, an internal DSL should have the feel of putting together whole sentences, rather than a sequence of disconnected commands. This is the basis for calling these kinds of APIs fluent interfaces." (ibid.)

**Limited expressiveness for internal DSLs** obviously can't come from the host language, which is general-purpose — it comes from *how you use it*. "When forming a DSL expression, you limit yourself to a small subset of the general language features. It's common to avoid conditions, looping constructs, and variables." Piers Cawley called this a **pidgin** use of the host language.

**External DSL vs. general-purpose language.** A language can have domain focus and still be general-purpose. **R** is Fowler's example: very much targeted at statistics work, but it has all the expressiveness of a general-purpose programming language — "despite its domain focus, I would not call it a DSL." Regular expressions are the clearer DSL: domain focus (matching text) coupled with limited features. "One common indicator of a DSL is that it isn't Turing-complete. DSLs usually avoid the regular imperative control structures (conditions and loops), don't have variables, and can't define subroutines."

Why insist on limited expressiveness when many disagree: "it is what makes the distinction between DSLs and general-purpose languages useful. The limited expressiveness gives DSLs different characteristics, both in using them and in implementing them. This leads to a different way of thinking about DSLs compared to general-purpose languages."

**Usage can decide.** XSLT has domain focus (transforming XML documents) but all the features of a regular programming language. "If XSLT is being used to transform XML, then I would call it a DSL. However, if it's being used to solve the eight queens problem, I would call it a general-purpose language. A particular usage of a language can put it on either side of the DSL line."

**Serialized data structures.** Is a list of property assignments (`color = blue`) in a config file a DSL? "I think that here, the boundary condition is the language nature. A series of assignments lacks fluency, so it doesn't fit the criteria."

**Configuration files.** Many XML configurations are effectively DSLs — but not always. Sometimes XML is created by other tools, used purely for serialization, not intended to be used by humans. "In that case, since humans aren't expected to use it, I wouldn't classify it as a DSL."

> "The question isn't whether it's human-readable or not, but whether the representation is a human's main way of interacting with that aspect of the system." (Fowler, DSL book, Ch. 2, section "Boundaries of DSLs")

Warning: "One of the biggest issues with these kinds of configuration files is that, even though they aren't intended to be human-edited, they end up being the primary editing mechanism in practice. In this case the XML becomes a DSL **by accident**." **(SDK relevance: if your serialization format is what users actually hand-edit, it is now a language and needs language-quality treatment — errors, docs, versioning, migration.)**

**Language workbench boundary.** The boundary is with any application that lets a user design their own data structure and forms (e.g., Microsoft Access). Two questions: is Access a language workbench, and is the thing you define a DSL? Answering the second first: with forms and tables there usually isn't a real language-like feel. Tables *can* have language nature — FIT and Excel both use tabular representations and both have a language feel (FIT domain-specific, Excel general-purpose) — "But most applications do not try to achieve that kind of fluency; they just create forms and windows that don't stress the interconnections." On the first question, **design intent** matters: "Access wasn't designed to be a language workbench, although you can use it that way if you really want. Look at how many people use Excel as a database — even though it wasn't designed to be one."

**Human jargon.** The Starbucks order ("Venti, half-caf, nonfat, no-foam, no-whip latte") has limited expressiveness, domain focus, and a sense of grammar as well as vocabulary — but it's a human language. Fowler reserves "DSL" for computer languages and uses **domain language** for a domain-specific human language. "If we implemented a computer language to understand Starbucks expressions, then that would truly be a DSL."

**Meta-point on definitions.** "there are few sharp boundaries. Reasonable people can disagree on what is a DSL... The purpose of a definition is to help in communication so different people can have the same idea of what we're talking about." Excluding something from the definition doesn't mean he considers it unvaluable.

#### 2.1.2 "Fragmentary and Stand-alone DSLs"

- **Stand-alone DSL** — you can look at a block of DSL script, typically a whole file, and it is all DSL. "If you are familiar with the DSL but not with the host language of the application, you should be able to understand what the DSL does because the host language either isn't there (in the external case) or is subdued by the internal DSL." Miss Grant's state machine is stand-alone.
- **Fragmentary DSL** — little bits of DSL used inside host language code, enhancing the host language with additional features. "you can't really follow what the DSL is doing without understanding the host language."
  - External examples: regular expressions; SQL statements inside a larger program.
  - Internal examples: expectation grammars in mock object libraries — "short bursts of DSLs within a larger host code context." **Annotations** are a popular host-language feature for fragmentary internal DSLs (metadata attached to host code elements), which "makes annotations suitable for fragmentary DSLs but useless for stand-alone ones."
- The same DSL can be used in both modes — SQL is the example. "Some DSLs are designed to be used in a fragmentary form, others in a stand-alone form, and still others can swing both ways."

### 2.2 "Why Use a DSL?"

**Framing.** "DSLs are a tool with limited focus. They aren't like object orientation or agile processes which introduce a fundamental shift into the way we think about software development. Instead, DSLs are a very specific tool for very particular conditions. A typical project might use half a dozen or so DSLs in various places — indeed, many already do."

**The recurring caution repeated up front:** a DSL is a thin veneer over a model, so "whenever you think about the benefits (or disadvantages) of a DSL, it's important to separate the benefits provided by the model from the benefits of the DSL. It's a common mistake to confuse the two."

#### 2.2.1 "Improving Development Productivity"

- The heart of the appeal: a DSL "provides a means to more clearly communicate the intent of a part of a system."
- Clarity is not aesthetic. "The easier it is to read a lump of code, the easier it is to find mistakes, and the easier it is to modify the system. So, for the same reason that we encourage meaningful variable names, documentation, clear coding constructs — we should encourage DSL usage."
- Defect cost is underestimated: defects hurt external quality *and* "slow developers down by sucking up time in investigations and fixes, sowing confusion about the behavior of the system."
- **The limited-expressiveness productivity argument:** "The limited expressiveness of DSLs makes it harder to say wrong things and easier to see when you've made an error." (This is the crispest statement in the book of why constrained languages pay off.)
- Attribution again: the **model alone** provides considerable productivity improvement — avoids duplication by gathering common code, and above all provides an abstraction for thinking about the problem. "A DSL enhances this by providing a more expressive form to read and manipulate that abstraction."
- **A DSL can help people learn an API**, "since it shifts focus to how different API methods should be combined together." **(SDK relevance: a fluent surface doubles as onboarding documentation for the underlying command-query API.)**
- **Wrapping an awkward third-party library.** "The DSL's usual advantages of a more fluent interface are magnified when the command-query interface is poor. In addition, the DSL only has to support the actual client usage, which can significantly reduce the surface area that the client developers need to learn." **(SDK relevance: high — the wrapper's value comes partly from *omission*; design to your clients' actual usage, not to the wrapped library's full surface.)**

#### 2.2.2 "Communication with Domain Experts"

- "I believe that the hardest part of software projects, the most common source of project failure, is communication with the customers and users of that software." A clear yet precise language for the domain can improve this.
- Nuance: many DSLs aren't suitable for domain communication at all — regex, build dependencies. "Only a subset of stand-alone DSLs really apply to this communication channel."
- **The COBOL fallacy.** The argument "Now we can get rid of programmers and have business people specify the rules themselves." "It's a common argument, but I don't think it improves with repetition."
- **What actually works:** "It's not that domain experts will write the DSLs themselves; but they can read them and thus understand what the system thinks it's doing. By being able to read DSL code, domain experts can spot mistakes. They can also talk more effectively to the programmers who do write the rules, perhaps by writing some rough drafts that can be refined into proper DSL rules."
- He's not dogmatic — he's seen teams get domain experts to write significant behavior in a DSL. "However, I still think the biggest gain from using a DSL in this way comes when domain experts start reading it. Focusing on reading can be the first step towards writing the DSL, with the advantage that you lose nothing if you don't take that further step." **(Judgement: read-first is a low-risk staged adoption path.)**
- **A real counter-argument he raises against himself:** if all you want is for domain experts to understand the content of a Semantic Model, "you can do this just by providing a visualization of the model. It's worth considering whether a visualization alone is a more efficient route than supporting a DSL. And it's useful to have visualizations in addition to a DSL."
- Involving domain experts in a DSL ≈ involving them in building a model; constructing a **Ubiquitous Language** [evans-ddd] deepens that communication. "Depending on the circumstances, you might find domain experts participating in the model and the DSL, or the DSL only."
- "Indeed some people find that trying to describe a domain using a DSL is useful even if the DSL is never implemented. It can be beneficial just as a platform for communication."
- Net judgement: "involving domain experts in a DSL is difficult to achieve but has a high payoff. And even if you can't get the domain experts' involved, you may still get enough of a gain in developer productivity to make the DSL worth the effort."

#### 2.2.3 "Change in Execution Context"

- The XML-config reason: "we want code to run in a different environment." Shifting logic from compile time to runtime is a common driver.
- **Worked example:** a project needed to trawl databases for contracts matching conditions and tag them. They wrote a DSL for specifying conditions, populating a Ruby Semantic Model. Running the query logic in Ruby would have required reading all contracts into memory — too slow. So the team used the Semantic Model to **generate SQL** to run in the database. Writing SQL directly "was too difficult for the developers, let alone the business people. However, the business people could read (and in this case, write) the appropriate expressions in the DSL."
- Generalization: "Using a DSL like this can often make up for limitations in a host language, allowing us to express things in a comfortable DSL and then generate code for the actual execution environment to use."
- **The model does the heavy lifting again:** once you have a model, it's easy to execute it directly or generate code from it. Models can also be populated from a forms-style interface.
- **DSL vs. forms — two concrete advantages:** (a) DSLs are often better than forms at representing complicated logic; (b) you can use ordinary code management tools, especially version control, to manage the rules. "When rules are entered via a form and stored in a database, version control is often neglected."
- **A spurious benefit, named as such.** People argue the good thing about a DSL is that the same behavior can be executed in different language environments (rules generating C# and Java; validations running in C# on the server and JavaScript on the client). "This is a spurious benefit because you can gain this just by using a model; you don't need a DSL at all. A DSL can make it easier to understand these rules, but that's a separate issue."

#### 2.2.4 "Alternative Computational Model"

- Mainstream programming is essentially all imperative: tell the computer what to do in what sequence, control flow via conditionals and loops, variables. "Imperative computation has become popular because it's relatively easy to understand and easy to apply to lots of problems. However, it isn't always the best choice."
- State machines are one example. Another: build systems — you can express build logic imperatively, "but after a while most people recognize that it's easier to do with a **Dependency Network** (e.g., to run tests, your compilations must be up-to-date). As a result, languages designed for describing builds (such as Make and Ant) use dependencies between tasks as their primary structuring mechanism."
- These are what people call declarative programming: "declare *what* should happen, rather than work through the imperative statements that describe *how* the behavior works."
- **Attribution once more:** "You don't need a DSL to use an alternative computational model. The core behavior of an alternative computational model comes from a Semantic Model... However, a DSL can make a big difference as it makes it much easier for people to manipulate declarative programs that populate the Semantic Model."

### 2.3 "Problems with DSLs"

**The decision rule:**

> "Fundamentally, the only reason to not use a DSL is if you don't see any of the benefits of a DSL apply to your situation — or at least, you don't see the benefits being worth the cost of building the DSL." (Fowler, DSL book, Ch. 2, section "Problems with DSLs")

He judges the stated problems "currently overstated, usually because people aren't familiar enough with how to build DSLs and how they fit into the broader software development picture. Also, many commonly stated problems with DSLs stem from the same confusion between DSL and model that plague many stated DSL benefits."

#### 2.3.1 "Language Cacophony"

The most common objection: languages are hard to learn, so using many languages will be more complicated than using one; knowing multiple languages makes it harder to work on the system and to onboard new people.

Two misconceptions:

1. **Mistaking the effort of learning a DSL for the effort of learning a general-purpose language.** "DSLs are far simpler than a general-purpose language, and thus far easier to learn."
2. **Forgetting that projects always have complicated hard-to-learn areas.** "Even if you don't have DSLs, you will typically have many abstractions in your codebase that you need to understand. Usually, these abstractions are captured in libraries in order to make them tractable. Even if you don't have to learn several DSLs, you still have to learn several libraries."

The reframed question: "how much harder it is to learn a DSL than to learn the underlying model on its own? I'd argue that the incremental cost of learning the DSL is quite small compared to the cost of understanding the model. Indeed, since the whole point of a DSL is to make it easier to understand and manipulate the model, **having a DSL should reduce the learning cost**."

#### 2.3.2 "Cost of Building"

- A DSL may be a small incremental cost over its library, "but it's still a cost. There's still code to write and above all to maintain. Thus, like any code, it has to pull its weight."
- **"Not every library benefits from having a DSL wrapper over it. If a command-query API does the job just fine, then there's no value in adding another API on top of it. Even if a DSL might help, sometimes it would just be too much effort to build and maintain for the marginal benefit."** (SDK relevance: high — a direct "when *not* to build a fluent layer" rule.)
- Maintenance factors: "Even a simple internal DSL may cause problems if most of the development team finds it difficult to understand. External DSLs in particular add a lot of moving parts to the process, with parsers that are often intimidating for developers."
- Unfamiliarity inflates cost — there are new techniques to learn. "Although you shouldn't ignore these costs, you should remember that learning curve costs can be amortized across multiple times that you might use a DSL in the future."
- **The cost is measured against the model, not against nothing.** "Any complicated area needs some mechanism to manage the complexity, and if it's complicated enough to consider a DSL, it's almost certainly complicated enough to benefit from a model. A DSL may help you think about the model and reduce the cost of building it."
- On the "encouraging DSLs will lead to many bad DSLs" worry: "Indeed I expect many bad DSLs to be built, just as there are plenty of libraries with bad command-query APIs. The question is whether a DSL will make things worse. A good DSL can wrap a bad library and make it easier to deal with (although I'd rather fix the library if I can). A bad DSL is a waste of resources to build and maintain, but that can be said of any bad code."

#### 2.3.3 "Ghetto Language"

The contrasting fear: a company builds a lot of its systems on an in-house language used nowhere else, making it hard to hire and hard to keep up with technological change.

Fowler's first move: "if you're writing whole systems in a language, that means it isn't a DSL (at least by my definition) but a general-purpose language. Although you can use many of the DSL techniques for building general-purpose languages, I would very strongly urge you not to do so. Building and maintaining a general-purpose language is a big undertaking that condemns you to a lot of work and a life in a ghetto. Don't do that."

Two real issues hide inside the ghetto argument:

1. **Scope creep into a general-purpose language.** "There's always a danger for a DSL to accidentally evolve into a general-purpose language. You take your DSL and gradually add new features; today you add conditional expressions, another day you add loops, and whoops — you're Turing-complete."
   - **Defense:** "guard firmly against it. Make sure you have a clear sense of what narrow problem the DSL is focused on. Question any new features that seem to fall outside that mission. If you need to do more, consider using more than one language and combining them, instead of letting one DSL grow too big."
   - **Explicitly generalized to libraries:** "The same problem can plague frameworks. A good library has a clear sense of purpose. If your product pricing library includes an implementation of the HTTP protocol, you're suffering from essentially the same failure to separate concerns." **(SDK relevance: very high — scope discipline as a first-class design constraint, and the composition-over-growth remedy.)**
2. **Building yourself what you should take from outside.** Applies to libraries as much as DSLs. "there's little reason now to build your own object-relational mapping system. My general rule with software is that if it's not your business, don't write it yourself — always look to take it from somewhere else. In particular, with the rise of open source tools it often makes sense to work on extending an existing open source effort than writing your own from scratch."

#### 2.3.4 "Blinkered Abstraction"

- The usefulness of a DSL is the abstraction it provides for thinking about a subject area — genuinely valuable.
- "However, any abstraction, be it a DSL or a model, always carries with it a danger — that of putting blinkers on your thinking. With a blinkered abstraction, you spend more effort on fitting the world into your abstraction than the other way around. You see this when you come across something that doesn't fit in with the abstraction — and you burn time trying to make it fit, instead of changing the abstraction to easily absorb the new behavior."
- **When it happens:** "Blinkering tends to occur once you've got comfortable with an abstraction and you feel it's bedded down — at this point it's natural to be worried by the prospect of uprooting it."
- **Why a DSL can make it worse:** "Since a DSL provides a more comfortable way of manipulating an abstraction, it can make you more reluctant to change it. This problem can be exacerbated when using the DSL with domain experts, who often are even more reluctant to change an abstraction once they get used to it."
- **The remedy is an attitude:** "As with any abstraction, you should always look at a DSL as something that's evolving, not finished."

### 2.4 "Wider Language Processing"

"This book is about domain-specific languages, but it's also about techniques for language processing. The two overlap, because 90% of the use of language processing techniques in an average development team is for DSLs. But these techniques can be used for some other things as well."

**Worked example.** A ThoughtWorks team had to communicate with a third-party system by sending messages whose payload was defined by COBOL copybooks (a record data-structure format). There were many of them, so Brian Egge built a parser for the subset of copybook syntax in use and generated Java classes to interface to those records. Payoffs: he could interface to as many copybooks as needed; "none of the rest of the code needed to know about COBOL data structures, and any changes could be handled with a simple regeneration." Fowler: "It would be an appalling stretch to call COBOL copybooks a DSL — but the same basic techniques that we use for external DSLs did the trick."

**Principle.** Parsing/model/generation techniques are general-purpose engineering tools — schema translation, adapter generation, protocol shims — not just DSL machinery. **(SDK relevance: generating client bindings from an interface description is exactly this pattern.)**

### 2.5 "DSL Lifecycle"

The book's presentation order — describe a framework and its command-query API, then layer a DSL on top — is pedagogical, "but it's not the only way that people use DSLs in practice."

**The common alternative: define the DSL first.**

- "you begin with some scenarios and write those scenarios down in the way you'd like the DSL to look. If the language is part of the domain functionality, it's good to do this with a domain expert — this is a good first step to using the DSL as a communication medium."
- Two styles for the early drafts: some people insist on statements that are already syntactically correct (host-language syntax for internal DSLs; statements they're confident they can parse for external DSLs); "Others are more informal at the beginning and then take a second pass through the DSL to get it close to a reasonable syntax."
- The workflow: sit with people who understand customers' needs; assemble a set of example behaviors based on what people wanted in the past or what you expect they'll want; write each in some DSL form; modify the DSL as you go to support new capabilities. "By the end of the exercise, you'll have worked through a reasonable sample of cases and will have a pseudo-DSL description of each of them."
- Tooling note: "If you're using a language workbench, you'll need to do this stage outside the workbench using a plain text editor, or regular drawing software, or pen and paper."

**What "implementing" then involves** — four artifacts, and the order among them is a choice:

1. designing the state machine model in the host language,
2. the command-query API for the model,
3. the concrete syntax of the DSL,
4. the translation between the DSL and the command-query API.

Observed sequencing styles: (a) little bits at a time across all four, "building a little bit of the model, adding the DSL to drive it, and hooking that thread all up with tests"; (b) build and test the framework first, then layer the DSL over it; (c) get the DSL in place, then build the library, then fit them together. "As I'm an incrementalist, I prefer thin slices of end-to-end functionality, so I go with the first of the three."

**Fowler's own loop:** start with the simplest case; program a library that supports that case using **test-driven development**; then implement the DSL for it, tying it to the framework. "I'd be happy to make some changes to the DSL to make it easier to build, although I would run those changes past the domain expert to ensure we still share a common communication medium." Then pick the next controller; "I would evolve the framework and tests first, then evolve the DSL." **(Judgement: DSL syntax may be bent for implementability, but not unilaterally — the shared-communication property is the constraint.)**

**Model-first is often excellent.** "Usually it is used when you don't think about using a DSL at first, or aren't sure you'll need one. You thus build the framework, work with it for a while, and then decide that a DSL would be a useful addition." The trigger in the example: you have a state machine model in use by many customers and realize it's harder than you'd like to add new customers.

**Two approaches to grow a DSL on top of an existing model:**

- **Language-seeded.** "slowly builds the DSL on top of the model, treating the model as a mostly black box. We would start by looking at all the controllers we currently have and sketching out pseudo-DSL for each one. Then we'd implement the DSL scenario by scenario... We usually wouldn't make any deep changes to the model, although I would be happy to add methods to the model to help support the DSL."
- **Model-seeded.** "we'd add fluent methods to the model first, to make it easier to configure the model, and then gradually draw them away into a DSL. This approach is more oriented towards internal DSLs; you can think of it as a heavy refactoring of the model to derive the internal DSL. An appealing aspect to the model-seeded approach is that it's very gradual, so it doesn't inflict a notable cost to build the DSL."

**When you don't even know you have a framework.** You might build several controllers and only then realize there's a lot of common functionality. "I'd then refactor the system to create separation between the model and the configuration code. **This separation is the vital step.** While I might have a DSL in mind while doing it, I'd be more inclined to get the separation done first, before putting the DSL on top." **(SDK relevance: high — extract the model/configuration seam before designing any fluent surface.)**

**Version control.** "Do make sure all your DSL scripts are kept under some form of version control system. A DSL script becomes part of your code and thus should be under version control just like everything else. The great thing about textual DSLs is that they play well with version control systems, allowing you to keep a clear track of the changes to the behavior of your system."

### 2.6 "What Makes a Good DSL Design?"

Fowler opens by conceding he doesn't have a clear answer: "I'd love to have a good advice to share, but I confess I don't have a clear idea in my mind."

What he does offer:

- **The overall goal is clarity for the reader.** "The overall goal for a DSL, as with any writing, is clarity for the reader. You want your typical reader, which may be a programmer or a domain expert, to be able to understand what the sentences in the DSL mean, as quickly and clearly as possible. While I don't feel I can say much about how to do that, I do think it's valuable to keep that goal in mind as you work."
- **Iterative design against a real audience.** "Try out ideas on your target audience. Be prepared to provide multiple alternatives and see how people react. Getting a good language will involve trying and rejecting lots of missteps. Don't worry about wrong turns; the more of those you make and correct, the more likely you are to find a good path."
- **Use domain jargon** — in the DSL *and* in the Semantic Model. "If the users of the DSL are familiar with the jargon, then they should see it in the DSL. Jargon is there to enhance communication within a domain even if it sounds like gibberish to those outside."
- **Follow the conventions of the surrounding environment.** "If everyone uses Java or C#, then use `//` for your comments and `{` and `}` for any hierarchic structures."
- **The one specific caution — don't imitate natural language.**

  > "Don't try to make the DSL read like natural language. There have been various attempts to do that with general-purpose languages, with Applescript as the most obvious example. The trouble is that such attempts lead to a lot of syntactic sugar which complicates understanding of the semantics. Remember that a DSL is a programming language, so using it should feel like programming, with the greater terseness and precision that programming has compared to a natural language. Trying to make a programming language look like natural language puts your head into the wrong context; when you're manipulating a program, you must always remember you're in a programming language environment." (Fowler, DSL book, Ch. 2, section "What Makes a Good DSL Design?")

  **(SDK relevance: very high — the standard failure mode of fluent APIs is chasing English-sentence readability at the cost of precision and predictability. The target is *terse and precise*, not *prose-like*.)**

---

## Chapter 3: Implementing DSLs

Scope statement: much varies between internal and external DSLs, but much is common. This chapter covers the common issues (specifics come in Ch. 4 and 5); language workbenches are deferred to much later.

### 3.1 "Architecture of DSL Processing"

**The reference architecture** (figure): `DSL script → parse → semantic model → [optional] generate → target code`. The generate step is drawn in brackets, explicitly optional.

**Semantic Model pattern restated.** "all the important semantic behavior is captured in a model, and the DSL's role is to populate that model via a parsing step. This means that the Semantic Model plays a central role in how I think about DSLs — indeed almost all of this book assumes you are using one."

**Form.** Fowler ("an OO bigot") naturally assumes an object model and likes rich object models combining data and processing. But: "a Semantic Model doesn't need to be like that; it can also be just a data structure. While I'd always rather have proper objects if I can, **using a data model form of Semantic Model is better than not using a Semantic Model at all.**"

**Semantic Model vs. Domain Model [poeaa].** Deliberately kept distinct:

- "The Semantic Model of a DSL is usually a subset of the application's Domain Model, as not all parts of the Domain Model are best handled by the DSL."
- "In addition, DSLs may be used for tasks other than populating a Domain Model, even when one is present."
- "The Semantic Model is a completely normal object model, which can be manipulated in the same way as any object model you might have... In a sense, it's thus independent of the DSL, although in practice the two are close siblings."

**Semantic Model ≠ abstract syntax tree.** Flagged here, explained in "The Workings of a Parser."

**Advantages of keeping the Semantic Model separate from the DSL:**

1. **Think about semantics without syntax/parser entanglement.** "If you're using a DSL at all, it's usually because you're representing something pretty complex, for otherwise you wouldn't be using it. Since you're representing something quite complex, that's enough for it to deserve its own model."
2. **Testability.** "this allows you to test the Semantic Model by creating objects in the model and manipulating them directly. I can create a bunch of states and transitions and test to see if the events and commands run, without having to deal with parsing at all. If there are problems in how the state machine executes, I can isolate the problem in the model without having to understand how the parsing works."
3. **Multiple DSLs over one model.** "You might start with a simple internal DSL, and later add an external DSL as an alternative version that's easier to read. Since you have existing scripts and existing users, you might want to keep the existing internal DSL and support both. Since both DSLs can parse into the same Semantic Model, this isn't difficult. It also helps to avoid any duplication between the languages."
4. **Independent evolution.** "If I want to change the model, I can explore that without changing the DSL, adding the necessary constructs to the DSL once I get the model working. Or I can experiment with new syntaxes for the DSL and just verify that they create the same objects in the model. **I can compare two syntaxes by comparing how they populate the Semantic Model.**"

**The framing analogy:**

> "In many ways, this separation of the Semantic Model and DSL syntax mirrors the separation of domain model and presentation that we see in designing enterprise software. Indeed on a hot day I think of a DSL as another form of user interface." (Fowler, DSL book, Ch. 3 "Implementing DSLs", section "Architecture of DSL Processing")

**The honest limitation of the analogy.** "The DSL and the Semantic Model are still connected. If I add new constructs to the DSL, I need to ensure they are supported in the Semantic Model, which often means modifying the two at the same time. However, the separation does mean I can think about semantic issues separately from parsing issues, which simplifies the task."

**Where internal and external differ.** "The difference between internal and external DSLs lies in the parsing step — both in what is parsed and in how the parsing is done. Both styles of DSL will produce the same kind of Semantic Model... there's no reason to not have a single Semantic Model populated by both internal and external DSLs."

**Expression Builders — a key structural recommendation.**

> "With an external DSL, there is a very clear separation between the DSL scripts, the parser, and the Semantic Model... With an internal DSL, it's much easier for things to get mixed up. I advocate having an explicit layer of objects (**Expression Builders**) whose job is to provide the necessary fluent interfaces to act as the language. DSL scripts then run by invoking methods on an Expression Builder which then populates the Semantic Model. Thus in an internal DSL, parsing the DSL scripts is done by a combination of the host language parser and the Expression Builders." (Fowler, DSL book, Ch. 3, section "Architecture of DSL Processing")

**SDK relevance (very high).** Do not put fluent/chaining methods directly on your domain objects. Put them on a separate builder layer that translates a language-shaped surface into ordinary command-query calls on the model. This keeps the model clean and independently testable, allows several fluent surfaces, and prevents the "language" concerns from leaking into semantics.

**On the word "parsing" for internal DSLs.** Fowler admits discomfort but defends the parallel: "With traditional parsing, you take a stream of text, arrange that text into a parse tree, and then process that parse tree to produce a useful output. With parsing an internal DSL, your input is a series of function calls. You still arrange them into a hierarchy (usually implicitly on the stack) in order to produce useful output." Also, several cases don't handle text directly at all: in an internal DSL the host language parser handles the text and the DSL processor handles further constructs; the same occurs with XML DSLs, where the XML parser translates text into elements and the DSL processor works on those.

**Refined internal/external distinction.** The "written in the base language of your application" test is "usually right, but not 100% so" — a Java application with a DSL written in JRuby is still an internal DSL (you'd use internal-DSL techniques).

> "The true distinction between the two is that internal DSLs are written in an executable language and parsed by executing the DSL within that language. In both JRuby and XML, a DSL is embedded into a carrier syntax, but we execute the JRuby code and just read the XML data structures." (Fowler, DSL book, Ch. 3, section "Architecture of DSL Processing")

**Execution: run the model, or generate code.**

- "The simplest, and usually the best, is just to execute the Semantic Model itself. The Semantic Model is code and as such can run and do all it needs to."
- The code-generation myth: "In some circles, code generation is seen as an essential part of DSLs. I've seen talks about code generation assuming that to do any DSL work, you have to generate code. In the rare event that I see someone talking or writing about **Parser Generators**, they inevitably talk about generating code. **Yet DSLs have no inherent need for code generation.** A lot of the time the best thing to do is just to execute the Semantic Model."
- **The strongest case for code generation:** "when there is a difference between where you want to run the model and where you want to parse the DSL. A good example of this is executing code in an environment that has limited language choices, such as on limited hardware or inside a relational database. You don't want to run a parser in your toaster or in SQL, so you implement the parser and Semantic Model in a more suitable language and generate C or SQL."
- **A related case:** "you have library dependencies in your parser that you don't want in the production environment. This situation is particularly common if you are using a complex tool for your DSL, which is why language workbenches tend to do code generation."
- **Even when you generate, keep a runnable model in the parsing environment:** experiment with DSL execution without simultaneously understanding the generator; test parsing and semantics without generating code (faster tests, easier isolation); "You can do validations on the Semantic Model that can catch errors before generating code."
- **A social argument for code generation:** "many developers find the kind of logic in a rich Semantic Model difficult to understand. Generating code from the Semantic Model makes everything much more explicit and less like magic. This could be a crucial point in a team with less capable developers."
- **The stance, with the memorable image:**

  > "the most important thing to remember about code generation is that it's an *optional* part of the DSL landscape. It's one of those things that are absolutely essential if you need them, yet most of the time you don't. I think of code generators as snowshoes: If I'm hiking in winter over deep snow I really have to have them, but I'd never carry them on a summer day." (Fowler, DSL book, Ch. 3, section "Architecture of DSL Processing")
- **Semantic Model decouples generators from the parser:** "I can write a code generator without having to understand anything about the parsing process, and test it independently too. That alone is enough to make the Semantic Model worthwhile. In addition, it makes it easier to support multiple code-generation targets should I need them."

### 3.2 "The Workings of a Parser"

**Core similarity across internal and external:**

> "parsing is a strongly hierarchical operation. When we parse text, we arrange the chunks into a tree structure." (Fowler, DSL book, Ch. 3, section "The Workings of a Parser")

An external `events ... end` block is an event list containing events, each with a name and a code. The Ruby internal version has no explicit list, "but each event is still a hierarchy: an event containing a name symbol and a code string." The same hierarchy is present either way.

**Definition — syntax tree (parse tree).** "Whenever you look at a script like this, you can imagine that script as a hierarchy; such a hierarchy is called a syntax tree (or parse tree). **Any script can be turned into many potential syntax trees — it just depends on how you decide to break it down.** A syntax tree is a much more useful representation of the script than the words, for we can manipulate it in many ways by walking the tree."

**Syntax tree vs. Semantic Model — the key judgement.**

> "If we are using a Semantic Model, we take the syntax tree and translate it into the Semantic Model. If you read material in the language community, you'll often see more emphasis placed on the syntax tree — people execute the syntax tree directly or generate code off the syntax tree. Effectively, people can use the syntax tree as a semantic model. Most of the time I would not do that, because the syntax tree is very tied to the syntax of the DSL script and thus couples the processing of the DSL to its syntax." (Fowler, DSL book, Ch. 3, section "The Workings of a Parser")

A figure shows DSL text → syntax tree → semantic model as three different representations of the same script; notably, the semantic model is a much smaller, more meaningful structure (a Transition object wired between two State objects and an Event) than the tree.

**The "ghostly" syntax tree.** "I've been talking about the syntax tree as if it's a tangible data structure in your system, like the XML DOM. Sometimes it is, but often it isn't. A lot of the time the syntax tree is formed on the call stack and processed as we walk it. As a result, you never see the whole tree, just the branch that you are currently processing (which is similar to the way XML SAX works)."

- Internal DSL: the tree is formed by arguments in a function call (**Nested Function**) and by nested objects (**Method Chaining**). "Sometimes, you don't see a strong hierarchy and you have to simulate it (**Function Sequence** with the hierarchy simulated with **Context Variables**)."
- "The syntax tree may be ghostly, but it's still a useful mental tool."
- External DSLs lead to a more explicit syntax tree; "indeed, sometimes you actually do create a full-blown syntax tree data structure (**Tree Construction**). But even external DSLs are commonly processed with the syntax tree forming and pruning continuously on the call stack."

**SDK relevance.** The mapping from fluent-API call shapes (nested calls, chained calls, flat sequences) to tree shapes is the design vocabulary for fluent interfaces. If your API's calls can't form a coherent hierarchy, you'll be forced into Context Variables (mutable parser state), which Fowler treats as a smell — so choose call shapes that make the hierarchy explicit.

### 3.3 "Grammars, Syntax, and Semantics"

**Definition — grammar.** "A grammar is a set of rules which describe how a stream of text is turned into a syntax tree." It consists of a list of **production rules**, each with a term and a statement of how it gets broken down (`additionStatement := number '+' number`). Rules mention each other (you'd also have a rule for `number`), and you compose a grammar for a language from these rules.

**There is no *the* grammar.**

> "It's important to realize that a language can have multiple grammars that define it. There is no such thing as *the* grammar for a language. A grammar defines the structure of the syntax tree that's generated for the language, and we can recognize many different tree structures for a particular piece of language text. A grammar just defines one form of a syntax tree; the actual grammar and syntax tree you'll choose will depend on many factors, including the features of the grammar language you're working with and how you want to process the syntax tree." (Fowler, DSL book, Ch. 3, section "Grammars, Syntax, and Semantics")

**Grammar defines syntax only, not semantics.** "It doesn't tell you anything about its semantics, that is, what an expression means. Depending on the context, `5 + 3` could mean `8` or `53`; the syntax is the same but the semantics may differ."

**The operational definition of semantics under a Semantic Model:**

> "With a Semantic Model, the definition of the semantics boils down to how we populate the Semantic Model from the syntax tree and what we do with the Semantic Model. In particular, we can say that **if two expressions produce the same structure in the Semantic Model, they have the same semantics, even if their syntax is different.**" (ibid.)

This is a *testable* definition of semantic equivalence, and it's what makes the "compare two syntaxes by comparing how they populate the model" technique from the previous section work.

**Grammars for internal DSLs.** With an external DSL, particularly using **Syntax-Directed Translation**, you make explicit use of a grammar when building the parser. "With internal DSLs, there won't be an explicit grammar, but it's still useful to think in terms of a grammar for your DSL. **This grammar helps you choose which of the various internal DSL patterns you might use.**"

**The two-grammar subtlety for internal DSLs.** "there are two parsing passes and thus two grammars involved. The first is the parsing of the host language itself, which obviously depends on the host grammar. This parsing creates the executable instructions for the host language. As the DSL part of that host language executes, it will create the ghostly syntax tree of the DSL on the call stack. It's only in this second parse that the notional DSL grammar comes into play."

**SDK relevance (high).** "Design the grammar of your API before choosing the call syntax." Write down what phrases are legal, what can nest inside what, and what must precede what — then pick the patterns (chaining, nesting, sequence) that express that grammar in the host language. Modern typed-builder techniques (phantom types, staged builder interfaces) are exactly the act of encoding that grammar into the type system.

### 3.4 "Parsing Data"

**The problem.** "As the parser executes, it needs to store various bits of data about the parse. This data could be a complete syntax tree, but a lot of the time that isn't the case — and even when it is, there's other data that usually needs to be stored to make the parse work well."

"The parse is inherently a tree walk, and whenever you are processing a part of a DSL script, you'll have some information about the context within the branch of the syntax tree that you're processing. However, often you need information that's outside that branch."

**Worked example:** a command is defined in a `commands` block and referred to in a state's `actions` clause. These live on different branches of the syntax tree; "If the only representation of the syntax tree is on the call stack, then the command definition has disappeared by now. As a result, we need to store the command object for later use so we can resolve the reference in the action clause."

**Symbol Table.**

> "a **Symbol Table**... is essentially a dictionary whose key is the identifier `unlockDoor` and whose value is an object that represents the command in our parse." (Fowler, DSL book, Ch. 3, section "Parsing Data")

When processing the definition text, create an object holding that data and stash it under the key. "The object we stash may be the semantic model object for a command, or it could be an intermediate object that's local to the syntax tree." Later, when processing the reference, look it up to capture the relationship. "A Symbol Table is thus a crucial tool for making the cross-references. If you actually do create a full syntax tree during the parse, you can theoretically dispense with a Symbol Table, although usually it's still a useful construct that makes it easier to stitch things together."

**Where parse results live.** "Sometimes all the results can be weaved into a Symbol Table, sometimes a lot of information can be kept on the call stack, sometimes you'll need additional data structures in the parser. In all of these cases the most obvious thing to do is to create Semantic Model objects as your results."

**Construction Builder.**

> "often, however, you'll need to create intermediate objects because you can't create Semantic Model objects till later in the parse. A common example of such an intermediate object is a **Construction Builder** which is an object that captures all the data for a Semantic Model object. This is useful when your Semantic Model object has read-only data after construction, but you gradually gather the data for it during parsing. A Construction Builder has the same fields as the Semantic Model object, but makes them read-write, which gives you somewhere to stash the data. Once you have all the data, you can create the Semantic Model object." (Fowler, DSL book, Ch. 3, section "Parsing Data")

**The judgement call that matters:**

> "Using a Construction Builder complicates the parser but I'd rather do that than alter the Semantic Model to forgo the benefits of read-only properties." (ibid.)

**SDK relevance (very high).** Absorb accumulation/mutability complexity into the builder so the model can stay immutable. This is the design rationale for builder patterns generally — the builder exists to protect an invariant-holding, immutable target object, not merely to reduce constructor arity.

**Phased parsing.** "Indeed sometimes you might defer all creation of Semantic Model objects till you've processed all the DSL script. In this case the parse has distinct phases: first, reading through the DSL script and creating intermediate parsing data, and second, running through that intermediate data and populating the Semantic Model. The choice of how much to do during the text processing and what to do afterwards usually depends on how the Semantic Model needs to be populated."

**Context Variable.** "The way you parse an expression often depends on the context that you are working in." When processing `actions {lockDoor}` you need to know it belongs to `unlockedPanel` and not `idle`. "Often, this context is supplied by the way the parser builds and walks the parse tree, but there are many cases where it's difficult to do that. If we can't find the context by examining the parse tree, then a good way to deal with it is by holding the context, in this case the current state, in a variable. I call this kind of variable a **Context Variable**. This Context Variable, like a Symbol Table, can hold a Semantic Model object or some intermediate object."

**The judgement:**

> "Although a Context Variable is often a straightforward tool to use, in general I prefer to avoid them as much as possible. The parsing code is easier to follow if you can read it without having to mentally juggle Context Variables, just as lots of mutable variables make procedural code more complicated to follow. Certainly there are times when you can't avoid using a Context Variable, but I tend to see them as a smell to be avoided." (ibid.)

**SDK relevance.** Implicit ambient state (thread-locals, "current" objects, open scopes) in a fluent API is the same smell. Prefer designs where the hierarchy is explicit in the call structure so the context is carried by the tree, not by a variable.

### 3.5 "Macros"

Usable with both internal and external DSLs. "They used to be used pretty widely, but are less common now. In most contexts I'd suggest avoiding them, but they are occasionally useful."

**Textual macros.** Substitute some text for some other text. Motivating example: CSS forces you to specify colors as codes like `#FFB595`; the code isn't meaningful, and repeating it in multiple places is duplication — "like any form of code duplication, is a Bad Thing." Better to name it (`MEDIUM_SHADE`) and define it in one place. CSS (at the time) didn't support that, so you can run a macro processor over a CSS-like source file to substitute. More involved macro processors take parameters — "the classic example of this is the C preprocessor that can define a macro to replace `sqr(x)` with `x * x`."

> "Macros provide a lot of opportunities to create DSLs, either within a host language (as the C preprocessor does) or as a stand-alone file transformed into a host language. The downside is that macros have a number of awkward problems that make them difficult to use in practice. As a result, textual macros have pretty much fallen out of favor, and most mavens like me advise against them." (Fowler, DSL book, Ch. 3, section "Macros")

**Syntactic macros.** "also do substitution, but they work on syntactically valid elements of the host language, transforming from one kind of expression to another. The language that's most famous for its heavy use of syntactic macros is Lisp, although C++ templates may be a better-known example. Using syntactic macros for DSLs is a core technique for writing internal DSLs in Lisp, but you can only use syntactic macros in a language that supports them; I therefore don't talk about them much in this book, since relatively few languages do."

### 3.6 "Testing DSLs"

Framing: Fowler is a fan of test-driven development [beck-tdd] "and similar techniques that put testing into the forefront of programming."

> "With DSLs, I can break testing down into three separate areas: testing the Semantic Model, testing the parser, and testing the scripts." (Fowler, DSL book, Ch. 3, section "Testing DSLs")

This three-way split is itself a consequence of the architecture: each seam is a test boundary.

#### 3.6.1 "Testing the Semantic Model"

- "These tests are about ensuring that the Semantic Model behaves the way I expect it to — that, as I execute it, the right outputs happen depending on what I place in the model. This is standard testing practice, the same as you would use with any framework of objects."
- **The key property:** "For this testing, I don't really need the DSL at all — I can populate the model using the basic interface of the model itself. This is good, as it allows me to test the model independently of the DSL and the parser."
- **Factoring test code** (conceptually, not transcribing): build several *small* fixtures, each a minimal machine exercising one feature — e.g. a transition tester with an idle state and two outbound transitions to test that an event triggers a transition; a command tester with just one state off idle to test command emission. Give them a common abstract superclass that sets up the shared fixture (controller plus command channel wired to the supplied machine) and provides **Test Utility Methods** and **Custom Assertions** [meszaros-xunit] so the tests read cleanly (`fire(trigger_a); assertCurrentState(a);`).
- **Alternative fixture strategy:** populate one larger model demonstrating many features and run multiple tests against it — Miss Grant's controller as the fixture. Again populated via the command-query interface.
- **The ordering rule for using the DSL in tests:** "As the test fixtures get more complex, however, I can simplify the test code by using the DSL to create fixtures. **I can do this if I have tests for the parser.**" (You may only use the DSL as a fixture-construction convenience once the parser itself is independently trusted — otherwise a parser bug silently corrupts model tests.)

#### 3.6.2 "Testing the Parser"

- "When we're using a Semantic Model, the job of the parser is to populate the Semantic Model. So our testing of the parser is about writing small fragments of DSL and ensuring that they create the right structures in the Semantic Model."
- **Problem with the naive approach:** reaching into the model to assert on individual states and transitions "is rather awkward, and may result in breaking encapsulation on the objects in the Semantic Model."
- **Better approach — model comparison.** Define methods to compare Semantic Models: build the *expected* model with the command-query API, parse the DSL to get the *actual* model, and assert equivalence.
- **Notification.** "Checking complex structures for equivalence is more involved than the regular notions of equality would suggest. We also need more information than just a Boolean answer, since we want to know what's different between the objects. As a result, I have a comparison that uses a **Notification**." The probe walks the objects in the Semantic Model and records every difference into the Notification — "This way I find all differences instead of stopping at the first one." The assertion then just checks whether the Notification has any errors, and the Notification's report supplies the failure message.
- **Assert in both directions.** He runs the equivalence probe left→right *and* right→left, because a one-directional walk finds missing elements but not extra ones. "You may think I'm being paranoid by doing the equivalence assertion in both directions, but usually the code *is* out to get me."

**SDK relevance.** Notification (accumulate all problems and report them together) rather than fail-on-first is a general API validation idiom worth carrying over — same rationale as returning all validation errors from a request rather than the first one.

#### 3.6.3 "Invalid Input Tests"

- Positive tests ensure valid input creates correct structures; **negative tests** probe what happens with invalid input. Error handling and diagnostics are out of scope for the book, but he covers invalid-input tests briefly.
- "The first time you run such a test, it's interesting to see what happens. Often you'll get an obscure but violent error. Depending on the amount of diagnostic support you want to provide with the DSL, that may be enough."
- **The real danger:**

  > "It's worse if you supply an invalid DSL, parse it, and get no error at all. This would violate the principle of 'fail fast' — that is, that errors should show up as early and loudly as possible. If you populate a model in an invalid state and have no checks for that, you may find out there's a problem till later. At that point, there is a distance between the original fault (loading an invalid input) and the later failure, and that distance makes it harder to find the fault." (Fowler, DSL book, Ch. 3, section "Invalid Input Tests")
- **The worked case:** he wrote a test with an undeclared target state; the test *passed*, which is bad, and then any use of the model (even printing it) blew up with a null pointer exception. "a typo in an input DSL could lead to much lost time debugging."
- **Where the check belongs — a clean responsibility argument:**

  > "Since the problem is that I'm creating an invalid structure in the Semantic Model, the responsibility to check for this problem is that of the Semantic Model — in this case, the method that adds a transition to a state." (ibid.)

  He adds an assertion on the target state in `State.addTransition`. Then he changes the test to expect the resulting exception, which both documents what error invalid input produces and detects if that behavior ever changes.
- **A calibrated stance on null checks:** he deliberately did *not* assert on the trigger event, because a null event causes an immediate NPE from `event.getCode()` — which already fails fast. "In general, I don't do not-null assertions on my method arguments, as I feel the benefit isn't worth the extra code to read. **The exception is when this leads to a null that doesn't cause an immediate failure**, such the null target state."

**SDK relevance (high).** Two transferable rules: (1) validation of structural invariants belongs on the model/aggregate that owns the invariant, not on every entry path; (2) add explicit argument checks only where their absence would delay failure — not reflexively.

#### 3.6.4 "Testing the Scripts"

- "Testing the Semantic Model and the parser does unit testing for the generic code. However, the DSL scripts are also code, and we should consider testing them."
- Rebuttal of "DSL scripts are too simple and obvious to be worth testing":

  > "I see testing as a double-check mechanism. When we write code and tests, we are specifying the same behavior using two different mechanisms, one involving abstractions (the code) and the other using examples (the tests). For anything of lasting value, we should always double-check." (Fowler, DSL book, Ch. 3, section "Testing the Scripts")
- "The general approach is to provide a test environment that allows you to create text fixtures, run DSL scripts, and compare results. It's usually some effort to prepare such an environment, but just because a DSL is easy to read doesn't mean people won't make mistakes. If you don't provide a test environment and thus don't have a double-check mechanism, you greatly increase the risk of errors in the DSL scripts."
- **Script tests double as integration tests.** "since any errors in the parser or Semantic Model should cause them to fail. As a result, it's worth sampling the DSL scripts to use a few for this purpose."
- **Visualizations as a testing/debugging aid.** "Once you have a script captured in the Semantic Model, it's relatively easy to produce different textual and graphical visualizations of the script's logic. Presenting information in multiple ways often helps people find errors — indeed, this notion of a double check is the heart of why writing self-testing code is such a valuable approach."
- **Test scripts tend to want their own DSL.** For the state machine, scenarios are sequences of events sent to the machine, checking the end state and the commands sent. "Building up something like this in a readable way naturally leads me to another DSL. That's not uncommon; **testing scripts is a common use of DSLs as they fit well with the need for a limited, declarative language.**" (The shape shown is a fluent scenario: given a sequence of events, `.endsAt(...)`, `.sends(...)`.)

### 3.7 "Handling Errors"

An explicit scope confession: "as with writing software, I have to cut the scope in order to get the book published... There are many topics I'd like to have explored further in this book, but the top of that list is error handling."

- Compiler-class lore he repeats: "parsing and output generation are the easy part of compiler writing — the hard part was giving good error messages."
- Reality check: "Good diagnostics are a rarity even in successful DSLs. More than one highly useful DSL package does little in the way of helpful information." Graphviz says `syntax error near line 4` and "I feel somewhat lucky even to get a line number." Some tools just fall over, leaving you to binary-search by commenting out lines.
- **The tradeoff, stated plainly:** "diagnostics are yet another thing to be traded off. Any time spent on improving error handling is time not spent adding other features. The evidence from many DSLs in the wild is that people do tolerate poor error diagnostics. After all, DSL scripts are small, so crude error finding techniques are more reasonable with them than with general-purpose languages." But: "In a heavily used library, good diagnostics can save a lot of time. Every tradeoff is unique, and you have to decide based on your own circumstances."
- **Cheapest practical advice:** "the crudest error-finding technique of all — commenting out. If you use an external DSL, make sure that you support comments. Not just for the obvious reasons, but also to help people find problems. Such comments are easiest to work with when they are terminated by line endings. Depending on the audience, I'd use either `#` (script style) or `//` (C style). These can be done with a simple lexer rule."

**Where error handling lives — the architectural question.** With a Semantic Model there are two candidate homes: the model or the parser.

- **Syntactic errors** → obviously the parser. Some are handled for you: host language syntax errors in an internal DSL; grammar errors from a **Parser Generator** in an external DSL.
- **Semantic errors** → genuine choice. Arguments for the model:
  - "The model is really the right place to check the rules of semantically well-formed structures. You have all the information structured the way you need to think about it, so you can write the clearest error checking code here."
  - "Additionally, you'll need the checking here if you want to populate the model from more than one place, such as multiple DSLs or using a command-query interface."
- **The serious disadvantage of model-only error handling:** "There's no link back to the source of the problem in the DSL script, not even an approximate line number. This makes it harder for people to figure out what went wrong, but this may not be an intractable problem. There is some experience that suggests that a purely model-based error message is enough to find the problem in many situations."
- **Three strategies for getting script context, with his verdict:**
  1. **Put error detection rules in the parser.** "the problem with this strategy is that it makes it much harder to write the rules, as you are working on the level of the syntax tree rather than the semantic model. You also have a much greater risk of duplicating the rules, with all the problems that code duplication entails."
  2. **Push syntactic information into the Semantic Model** (e.g., a line-number field on a transition object). "The problem is that this can make the Semantic Model much more complicated as it has to track the information. Additionally, the script may not map that cleanly to the model, which could result in error messages that are more confusing than helpful."
  3. **(Preferred) Detect in the model; initiate from the parser.** "the parser will parse a hunk of DSL script, populate the Semantic Model, and then tell the model to look for errors (if populating the model doesn't do that directly). Should the model find any, the parser can then take those errors and supply the DSL script context it knows. **This separates the concerns of syntactic knowledge (in the parser) and semantic knowledge (in the model).**"
- **The organizing frame:**

  > "A useful approach is to divide error handling into initiation, detection, and reporting. This last strategy puts initiation in the parser, detection in the model, and reporting in both, with the model supplying the semantics of the error and the parser adding syntactic context." (Fowler, DSL book, Ch. 3, section "Handling Errors")

**SDK relevance (high).** The initiation/detection/reporting split is directly reusable for API validation layering: the domain layer owns the rules and produces semantic errors; the boundary layer (request parser, CLI, config loader) triggers validation and enriches errors with source context (field path, line number, request id). Neither layer duplicates the other's knowledge.

### 3.8 "Migrating DSLs"

**The danger to guard against:**

> "One danger that DSL advocates need to guard against is the notion that first you design a DSL, then people use it. Like any other piece of software, a successful DSL will evolve. This means that scripts written in an earlier version of a DSL may fail when run with a later version." (Fowler, DSL book, Ch. 3, section "Migrating DSLs")

- "Like many properties of DSL, good and bad, this is very much the same as what happens with a library. If you take a library from someone, write some code against it, and they upgrade the library, you may end up stuck. DSLs don't really do anything to change that; **the DSL definition is essentially a published interface**, and you have to deal with the consequences just the same."
- **Published interface** (term from *Refactoring* [fowler-ref]): "The difference between published and the more common 'public' interface is that a published interface is used by code written by a separate team. Therefore, if the team that defines the interface wants to change it, they can't easily rewrite the calling code." Changing a published DSL is an issue for both internal and external DSLs. "With nonpublished DSLs, it may be easier to change an internal DSL if the language concerned has automated refactoring tools." **(SDK relevance: very high — the public/published distinction is the core of API compatibility policy.)**
- Migration tools "can be run either during an upgrade, or automatically should you try to run an old-version script."

**Two broad migration approaches:**

1. **Incremental migration** — "essentially the same notion that's used by people doing evolutionary database design [evodb]. For every change you do to your DSL definition, create a migration program that automatically migrates DSL scripts from the old version to the new version. That way, when you release a new version of the DSL, you also provide scripts to migrate any code bases that use the DSL."
   - **Keep the changes small.** "Imagine you are upgrading from version 1 to 2, and have ten changes that you want to make to your DSL definition. In this case, don't create just one migration script to migrate from version 1 to 2; instead, create at least ten scripts. Change the DSL definition one feature at a time, and write a migration script for each change. You may find it useful to break it down even more and add some features with more than one step (and thus more than one migration). This may sound like more work than a single script, but the point is that migrations are much easier to write if they are small, and it's easy to chain multiple migrations together. As a result, you'll be able to write ten scripts much faster than one."
2. **Model-based migration** — "a tactic you can use with a Semantic Model. With model-based migration you support multiple parsers for your language, one for each released version. (So you only do this for versions 1 and 2, not for the intermediate steps.) Each parser populates the semantic model. **When you use a semantic model, the parser's behavior is pretty simple, so it's not too much trouble to have several of them around.** You then run the appropriate parser for the version of script you are working with."
   - That handles multiple versions but doesn't migrate scripts. "To do the migration, you write a generator from the semantic model that generates a DSL script representation. This way, you can run the parser for a version 1 script, populate the semantic model, and then emit a version 2 script from the generator."
   - **Problem:** "it's easy to lose stuff that doesn't matter for the semantics but is something that the script writers want to keep. Comments are the obvious example. This is exacerbated if there's too much smarts in the parser, although then the need to migrate this way may encourage the parsers to stay dumb — **which is a Good Thing.**" (A nice second-order design pressure: round-tripping keeps parsers dumb.)
   - "If the change to the DSL is big enough, you may not be able to transform a version 1 script into a version 2 semantic model. In this case, you may need to keep a version 1 model (or an intermediate model) around and give it the ability to emit a version 2 script."
- **No strong preference between the two.**

**Version statements.** "Migration scripts can be run by script programmers themselves when needed, or automatically by the DSL system. If it's to be run automatically, it's very useful to have the script record which version of the DSL it is so the parser can detect it easily and trigger the resulting migrations. Indeed, some DSL authors argue that all DSLs should have a mandatory version statement in a script so it's easy to detect out-of-date scripts and support the migration of scripts. While a version statement may add a bit of noise to the script, **it's something that's very hard to retrofit.**"

**Not migrating is an option.** "keep the version 1 parser and just let it populate the version 2 model. You should help people migrate, and they will need to if they want to use more features. But supporting the old scripts directly, if you can, is useful since it allows them to migrate at their own pace."

**Closing realism.** "Although techniques like this are quite appealing, there is the question of whether they are worth it in practice. As I said earlier, the problem is exactly the same as with widely used libraries, and automated migration schemes have not been used much there."

---

## Cross-cutting vocabulary index (Chs. 1–3)

Patterns and terms introduced or referenced in these chapters. (Fowler's pattern chapters come later in the book; these are the forward references made in Part I.)

| Term | Meaning as used in Chs. 1–3 |
|---|---|
| **Semantic Model** | The model that captures all important semantic behavior; the DSL's job is to populate it. Central to the whole book. Distinct from Domain Model and from an abstract syntax tree. |
| **Domain Model** [poeaa] | An object model of the domain. The Semantic Model is usually a subset of it. |
| **Ubiquitous Language** [evans-ddd] | Shared vocabulary between domain people and programmers, present in the code. |
| **Adaptive Model** | A model whose object population acts as the program; blurs code/data. State machines are one. |
| **Alternative computational model** | Non-imperative computation styles: State Machine, Production Rule System, Dependency Network. |
| **External DSL** | DSL in a language separate from the host; custom syntax or a carrier syntax like XML. |
| **Internal DSL** | DSL written in an executable host language and parsed by executing it in that language. |
| **Fluent interface** | Synonym for internal DSL, viewed from the API direction. |
| **Command-query API** | Fowler's name for a non-fluent API; defines the *vocabulary* of an abstraction. |
| **Language workbench** | Specialized IDE for defining a DSL *and* its custom editing environment; enables non-textual languages. |
| **Domain language** | A domain-specific *human* language (Starbucks jargon); deliberately not a DSL. |
| **Stand-alone / fragmentary DSL** | Whole-file DSL vs. snippets embedded in host code (regex, SQL, annotations, mock expectations). |
| **Expression Builder** | A layer of objects providing the fluent interface for an internal DSL and populating the Semantic Model. |
| **Symbol Table** | Dictionary from identifier to the object it names; resolves cross-branch references during a parse. |
| **Construction Builder** | Mutable intermediate object accumulating data for an immutable Semantic Model object. |
| **Context Variable** | Variable holding parse context when the tree can't supply it. A smell to be minimized. |
| **Syntax tree / parse tree** | Hierarchical representation of a script; often "ghostly," living on the call stack. |
| **Tree Construction** | Building an explicit, full syntax tree data structure. |
| **Nested Function / Method Chaining / Function Sequence** | Internal-DSL patterns for forming hierarchy via call arguments, chained calls, or flat statement sequences. |
| **Syntax-Directed Translation** | External-DSL technique driven by an explicit grammar. |
| **Parser Generator** | Tool that produces a parser from a grammar; conventionally associated with code generation. |
| **Macros (textual / syntactic)** | Text substitution vs. substitution over syntactically valid host-language elements. Mostly discouraged. |
| **Notification** | Object accumulating multiple errors/differences instead of failing at the first one. |
| **Visualization** | Non-editable alternative representation generated from the Semantic Model (diagram, text, spreadsheet). |
| **Illustrative programming** | Fowler's coinage for the spreadsheet style where sample output, not the program, is front and center. |
| **Published interface** [fowler-ref] | An interface used by code from a separate team; can't be unilaterally changed. |
| **COBOL fallacy** | The belief that a DSL lets business people replace programmers. |
| **Language cacophony / ghetto language / blinkered abstraction** | The three named DSL objections in Ch. 2. |
| **Pidgin** (Piers Cawley) | Using only a small subset of a host language when writing an internal DSL. |

---

## Condensed principle list (for the study doc)

1. **Find the variation axis first.** A DSL expresses the varying part of a family of systems; the invariant part is a library. (Ch. 1)
2. **Separate common code from variable code** — library/framework vs. configuration/assembly. This separation is the vital step, and it is worth doing *before* adding a DSL. (Ch. 1, Ch. 2 "DSL Lifecycle")
3. **Almost always build a Semantic Model.** Parsing, semantics, and code generation become three independently testable, independently evolvable concerns. (Ch. 1, Ch. 3)
4. **The DSL is a thin facade over the model.** Attribute benefits correctly: runtime reconfiguration, reuse, multi-target execution are model properties, not DSL properties. (Ch. 1, Ch. 2)
5. **A DSL is a form of user interface over the domain model.** (Ch. 3)
6. **Limited expressiveness is the point**, not an accident of the domain. It makes it harder to say wrong things and easier to see errors. Guard against creeping toward Turing-completeness; compose multiple small languages instead. (Ch. 2)
7. **Language nature = grammar, not just vocabulary.** A command-query API's methods stand alone; a DSL's methods make sense only inside a phrase. (Ch. 2)
8. **Design the grammar before the syntax.** The notional grammar tells you which internal-DSL patterns fit. (Ch. 3)
9. **Semantic equivalence = same structure in the Semantic Model**, regardless of syntax. This makes syntax experiments cheap and comparable. (Ch. 3)
10. **Isolate mutability in builders** so the Semantic Model can keep read-only properties. Complicate the parser, not the model. (Ch. 3)
11. **Avoid ambient context.** Context Variables are sometimes necessary but are a smell; prefer hierarchy carried by the call structure. (Ch. 3)
12. **Code generation is optional** — snowshoes, not everyday footwear. Use it when the execution environment differs from the parsing environment, or when you must shed parser dependencies. Never hand-edit generated code. (Ch. 1, Ch. 3)
13. **Validate in the model, initiate in the parser, report in both.** Semantic knowledge lives with the model; syntactic context lives with the parser. (Ch. 3)
14. **Fail fast, but only add null checks where absence would delay the failure.** (Ch. 3)
15. **Test the model without the DSL, the parser against the model, and the scripts as integration tests.** Only use the DSL to build fixtures once the parser is itself tested. (Ch. 3)
16. **Treat a released DSL as a published interface.** Plan migrations (incremental scripts or model-based re-emission), record a version in scripts (hard to retrofit), and consider simply supporting old versions. (Ch. 3)
17. **Clarity for the reader is the design goal**; iterate against real readers; use domain jargon; follow host-environment conventions; **do not imitate natural language**. (Ch. 2)
18. **Not every library needs a DSL.** If a command-query API does the job, adding another API on top has no value. Cost is measured against the model, and the DSL must pull its weight. (Ch. 2)
19. **Keep the scope narrow — for languages and for libraries alike.** A pricing library containing an HTTP implementation is the same failure of separation as a DSL that grew loops. (Ch. 2)
20. **Abstractions blinker you; DSLs blinker you harder.** Treat the language as evolving, never finished. (Ch. 2)
