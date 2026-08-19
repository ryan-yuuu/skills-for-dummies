# Part 1 — Foundations and Strategy

## 1. What a DSL is — definition and boundaries

### 1.1 The definition, and why each word is load-bearing

Fowler concedes up front that "domain-specific language" has never had a firm definition and that its boundaries are genuinely blurred — but he insists that a working definition is worth having, because the purpose of a definition is to let two people mean the same thing when they talk *(Ch. 2, "Defining Domain-Specific Languages")*. His:

> **Domain-specific language** (noun): a computer programming language of limited expressiveness focused on a particular domain.

Four elements sit inside that sentence, and each does real work:

1. **It is a computer programming language.** Something humans use to instruct a computer. It is structured so a person can understand it, but a machine must still be able to execute it. This is what excludes documentation formats and human jargon.
2. **It has language nature.** Because it is a *language*, it should have a sense of **fluency**, "where the expressiveness comes not just from individual expressions but also from the way they can be composed together." A pile of unrelated statements is not a language.
3. **It has limited expressiveness.** A general-purpose language gives you varied data structures, control structures, and abstraction facilities — all of which make it harder to learn and harder to use. "A DSL supports a bare minimum of features needed to support its domain. You can't build an entire software system in a DSL; rather, you use a DSL for one particular aspect of a system."
4. **It has domain focus.** "A limited language is only useful if it has a clear focus on a small domain. The domain focus is what makes a limited language worthwhile."

The ordering matters and is easy to miss. Domain focus comes *last*, and Fowler says it "is merely a consequence of the limited expressiveness." Most people reach for the literal reading — "a language for a specific domain" — but literal definitions are frequently wrong; his analogy is that we don't call coins "compact discs" merely because they are discs that are more compact than the ones we do name that way *(Ch. 2, "Defining Domain-Specific Languages")*.

### 1.2 The three implementation styles

- **External DSL** — a language separate from the main language of the application. Usually a custom syntax, though borrowing another language's syntax (XML above all) is common. It is parsed by code in the host application using text-parsing techniques. The Unix tradition of little languages fits here. Familiar examples: regular expressions, SQL, Awk, and framework configuration files.
- **Internal DSL** — a particular *way of using* a general-purpose language. Every script is valid code in the host language, but it uses only a subset of the language's features, in a specific style, to handle one small aspect of the system. "The result should have the feel of a custom language, rather than its host language." Lisp is the classic; Ruby developed a strong culture of it, to the point that Rails "is often seen as a collection of DSLs."
- **Language workbench** — a specialized IDE for defining and building DSLs, used not only to determine the structure of a DSL but as a custom editing environment for writing scripts. "The resulting scripts intimately combine the editing environment and the language." *(Ch. 2, "Defining Domain-Specific Languages")*

Fowler adds a community observation with practical bite: these three styles have grown separate communities, and "you'll find people who are very experienced in internal DSLs but have no idea how to build an external DSL. I find this problematic because, as a result, people may not choose the best tool for the job." He recounts a team doing very clever internal-DSL gymnastics to support a custom syntax that would have been far easier as an external DSL — "since they didn't know how to build external DSLs, they didn't have that option open to them."

He also avoids the term **embedded DSL**, a widely used synonym for internal DSL, because "embedded language" already means a scripting language embedded inside an application — VBA in Excel, Scheme in the Gimp *(Ch. 1, "Programming Miss Grant's Controller")*.

### 1.3 A DSL is a front end to a library

In software we build abstractions and then manipulate them. The most common way to build an abstraction is a library or framework; the most common way to manipulate it is command-query API calls. That gives the cleanest statement of what a DSL structurally *is*:

> "In this view a DSL is a front-end to a library providing a different style of manipulation to the command-query API. In this context, the library is the Semantic Model of the DSL. A consequence of this is that DSLs tend to follow libraries, and indeed I consider a Semantic Model to be a necessary adjunct to a well-built DSL." *(Ch. 2, "Defining Domain-Specific Languages")*

And the corollary about where the work actually is:

> "When people talk about DSLs, it's easy to think that building the DSL is the hard work. In fact, usually the hard work is building the model; the DSL then just layers on top of it. It still takes effort to get a DSL that works well, but that effort is usually much smaller than for building the underlying model." *(ibid.)*

### 1.4 Fluent interface vs command-query API — the internal boundary

Once you accept that a DSL is a front end to a library, the boundary between "internal DSL" and "ordinary API" becomes the interesting question. Fowler names both sides. A **fluent interface** is another term for an internal DSL, "emphasizing that an internal DSL is really just a particular kind of API designed with this elusive quality of fluency." A **command-query API** is his coinage for the *non*-fluent style — the dominant, unnamed default, "so dominant that we don't even think of giving it a name," which is exactly why he names it *(Ch. 1, "Programming Miss Grant's Controller"; Ch. 4, "Fluent and Command-Query APIs")*.

The distinguishing characteristic is not domain focus. "As it turns out, the domain focus isn't a good boundary condition — the boundaries more commonly revolve around limited expressiveness and the language nature" *(Ch. 2, "Boundaries of DSLs")*. And in the internal case:

> "In many ways, an internal DSL is nothing more than a quirky API (as the old Bell labs saying goes, 'Library design is language design')." *(Ch. 2, "Boundaries of DSLs")*

The sharpest formulation Fowler quotes is Mike Roberts':

> "a command-query API defines the vocabulary of the abstraction, whereas an internal DSL adds a grammar." *(Ch. 2, "Boundaries of DSLs")*

That yields a usable test. The standard way to document a class with a command-query API is to list its methods, and **each method should make sense on its own** — a list of "words," each with a somewhat self-sufficient meaning. In an internal DSL, "the methods... often only make sense in the context of a larger expression in the DSL." His example is the method `to` in a chain like `.transition(lightOn).to(unlockedPanel)`: "Such a method would be a bad name in a command-query API, but fits inside a phrase."

> "As a result, an internal DSL should have the feel of putting together whole sentences, rather than a sequence of disconnected commands. This is the basis for calling these kinds of APIs fluent interfaces." *(ibid.)*

Limited expressiveness for an internal DSL obviously can't come from the host language, which is general-purpose by definition. It comes from *how you use it*: "When forming a DSL expression, you limit yourself to a small subset of the general language features. It's common to avoid conditions, looping constructs, and variables." Piers Cawley called this a **pidgin** use of the host language.

Fowler is careful that this is a spectrum with two named points, not two categories. The original plain Java configuration code for the state-machine example he explicitly declines to call a DSL — "That code feels like stitching things together with an API" — while a Java builder subclass using chained calls he *does* call one: "It's formatted oddly, and uses some unusual programming conventions, but it is valid Java... it still has that declarative flow that a DSL needs" *(Ch. 1, "Programming Miss Grant's Controller")*. The difference "comes down to the rather fuzzy notion of a language-like flow." Fowler is relaxed about the fuzziness, and honest about its cost:

> "The advantage of such arguments is that they encourage reflection on the techniques you are using and on how readable your DSL is; the disadvantage is that they can turn into continual rehashes of personal preferences." *(Ch. 4, opening)*

### 1.5 The external boundary — domain focus is not enough

A language can be domain-focused and still be general-purpose. **R** is Fowler's example: squarely targeted at statistics, but with all the expressiveness of a general-purpose language — "despite its domain focus, I would not call it a DSL." Regular expressions are the clearer case: domain focus (matching text) coupled with a deliberately restricted feature set. "One common indicator of a DSL is that it isn't Turing-complete. DSLs usually avoid the regular imperative control structures (conditions and loops), don't have variables, and can't define subroutines" *(Ch. 2, "Boundaries of DSLs")*.

Why insist on limited expressiveness when many disagree? "it is what makes the distinction between DSLs and general-purpose languages useful. The limited expressiveness gives DSLs different characteristics, both in using them and in implementing them."

**Usage can move a language across the line.** XSLT is domain-focused (transforming XML documents) but has all the features of a regular programming language. "If XSLT is being used to transform XML, then I would call it a DSL. However, if it's being used to solve the eight queens problem, I would call it a general-purpose language. A particular usage of a language can put it on either side of the DSL line" *(ibid.)*.

### 1.6 Config files, serialized data, and DSL-by-accident

Is a flat list of property assignments (`color = blue`) a DSL? No: "I think that here, the boundary condition is the language nature. A series of assignments lacks fluency, so it doesn't fit the criteria." Fowler later distinguishes a **property list** — key/value pairs, maybe grouped, with "none of that mysterious language nature that's key to something being a DSL" — from configuration files that genuinely have language nature and therefore *are* DSLs; done in XML, those are external DSLs *(Ch. 2, "Boundaries of DSLs"; Ch. 5, "XML DSLs")*.

Many XML configuration files are effectively DSLs. But not all: sometimes XML is produced by other tools purely for serialization and is never meant to be touched by a person. "In that case, since humans aren't expected to use it, I wouldn't classify it as a DSL." The test he gives is precise:

> "The question isn't whether it's human-readable or not, but whether the representation is a human's main way of interacting with that aspect of the system." *(Ch. 2, "Boundaries of DSLs")*

Followed immediately by the warning that matters most in practice: "One of the biggest issues with these kinds of configuration files is that, even though they aren't intended to be human-edited, they end up being the primary editing mechanism in practice. In this case the XML becomes a DSL **by accident**."

The same definitional test resurfaces in the code-generation chapter, from the other direction. If you generate a small tabular data file to be read at startup by the target system, is that another DSL? Fowler says no — it isn't designed for human manipulation, and it is primarily designed to be trivial to parse. "When designing such a format, human readability comes a distant second to simplicity of parsing. With a DSL, human readability is a high priority" *(Ch. 8, "Choosing What to Generate")*.

### 1.7 Two more boundary cases: workbenches and human jargon

The **language workbench boundary** runs up against any application that lets a user define their own data structures and forms — Microsoft Access, for instance. Two separate questions: is Access a language workbench, and is the thing you build with it a DSL? On the second: forms and tables usually lack any language-like feel. Tables *can* have it — FIT and Excel both use tabular representations and both have language nature (FIT domain-specific, Excel general-purpose) — "But most applications do not try to achieve that kind of fluency; they just create forms and windows that don't stress the interconnections." On the first, **design intent** decides: "Access wasn't designed to be a language workbench, although you can use it that way if you really want. Look at how many people use Excel as a database — even though it wasn't designed to be one" *(Ch. 2, "Boundaries of DSLs")*.

**Human jargon** fails the first element of the definition, not the others. A Starbucks order — "Venti, half-caf, nonfat, no-foam, no-whip latte" — has limited expressiveness, domain focus, and a genuine sense of grammar as well as vocabulary. But it is a human language, so Fowler reserves "DSL" for computer languages and calls this a **domain language**. "If we implemented a computer language to understand Starbucks expressions, then that would truly be a DSL" *(ibid.)*.

### 1.8 Fragmentary vs stand-alone

An orthogonal axis, and one that determines a great deal about your implementation options *(Ch. 2, "Fragmentary and Stand-alone DSLs")*:

- **Stand-alone DSL** — you can look at a block of script, typically a whole file, and it is all DSL. "If you are familiar with the DSL but not with the host language of the application, you should be able to understand what the DSL does because the host language either isn't there (in the external case) or is subdued by the internal DSL."
- **Fragmentary DSL** — little bits of DSL embedded inside host-language code, enhancing the host language. "you can't really follow what the DSL is doing without understanding the host language." External examples: regular expressions, SQL statements inside a program. Internal examples: the expectation grammars in mock-object libraries — "short bursts of DSLs within a larger host code context." **Annotations** are the archetypal host-language feature for fragmentary internal DSLs, which "makes annotations suitable for fragmentary DSLs but useless for stand-alone ones."
- The same DSL can be used both ways. SQL is the example. "Some DSLs are designed to be used in a fragmentary form, others in a stand-alone form, and still others can swing both ways."

### 1.9 The meta-point about definitions

Fowler closes the boundaries discussion by refusing to over-invest in it: "there are few sharp boundaries. Reasonable people can disagree on what is a DSL... The purpose of a definition is to help in communication so different people can have the same idea of what we're talking about." Excluding something from the definition is not a judgement about its value *(Ch. 2, "Boundaries of DSLs")*.

> **SDK lens:** The line between "an API" and "a language" is the line between vocabulary and grammar. If each method on your type must be comprehensible standing alone in an autocomplete list, you are designing a command-query API; if the methods only make sense inside a call sequence, you have written a language, and you owe it language-grade treatment — a defined set of legal compositions, documentation of phrases rather than words, and error messages that talk about phrases. The most expensive version of this mistake is the accidental one: the serialization format or config file you never intended anyone to hand-edit, which is now the primary way your users interact with your system. The moment that happens, it needs versioning, migration, diagnostics, and a readability budget, whether you planned for it or not.

---

## 2. The central architecture: the Semantic Model and its thin language veneer

Chapter 1 is a single worked example — a building-security controller — shown in five or six notations. Its structure is the whole architectural argument of the book in miniature, so it is worth distilling as a narrative rather than a list.

### 2.1 Start from the axis of variation, not from the language

The fictional company installs security systems: wireless sensors emit four-character event codes, a controller runs a program, control devices respond to four-character command codes. The observation that puts a DSL on the table is structural, not aesthetic:

> "What we have is a family of systems that share most components and behaviors, but have some important differences." *(Ch. 1, "Gothic Security")*

Concretely, the *way* the controller sends and receives messages is identical for every customer; the *sequence* of events and commands differs per customer. The business requirement — install a new system with minimum effort — becomes the software requirement that it must be easy to program a sequence of actions into the controller.

The principle generalizes: **identify the axis of variation before you design anything.** The DSL will express only the varying part; the invariant part belongs in a library. Fowler frames this throughout as "separation of common code from variable code."

Only then does he choose an abstraction. Looking across many customers, a **state machine** emerges as a good way to think about a controller: each sensor sends an event that can change state; entering a state can emit commands. (He is candid that he picked the state machine first and invented the gothic castle around it, because state machines make good examples.)

### 2.2 Build the model first, in domain vocabulary

Once the team agrees a state machine is a good way to *specify* controller behavior, the next step is to put that abstraction into the software itself:

> "If people want to think about controller behavior with events, states, and transitions, then we want that vocabulary to be present in the software code too." *(Ch. 1, "The State Machine Model")*

This is Evans' **Ubiquitous Language** principle, realized as a **Domain Model**. Several design judgements inside the resulting model are worth carrying away independent of DSLs:

- **Don't store what you can derive.** The machine holds a start state and a list of reset events; the other states are whatever is reachable from the start state via a graph walk.
- **Type-separate things that are structurally identical but semantically distinct.** Events and commands both hold a symbolic name and a four-character wire code, and share an abstract superclass — but they stay separate classes because they play different roles in the controller.
- **Prefer symbolic names to wire codes.** The protocol uses four-letter codes; the model refers to events and commands by symbolic names and keeps the codes as data. Even before any DSL exists, the model is already translating machine vocabulary into human vocabulary.
- **Behavior gets small once the structure is right.** Fowler notes the controller's behavior "is really quite simple" once the structure settles: on an incoming code, transition if the current state has a matching transition; else if it's a reset event, return to the start state; else ignore silently. Most of the design effort goes into structure; the interpreter over it is a handful of lines.

There is also an explicit modelling judgement worth preserving, because it is the book's first statement of the form "I know this is redundant and I'm keeping it anyway." The controllers have a distinct idle state, and certain events should snap the machine back to idle from anywhere. This fits no classical state machine formalism, and it is strictly unnecessary — you could synthesize a transition to idle from every state, and Fowler shows the code that would do it. He keeps the explicit concept regardless:

> "I prefer explicit reset events on the machine because that better expresses my intent." *(Ch. 1, "The State Machine Model")*

A redundant construct earns its place if it makes intent clearer, in both the general machine and each particular machine. He acknowledges the cost — "it does complicate the machine a bit" — and accepts it. Design the abstraction to fit the domain, not the textbook, and name the deviation rather than apologizing for it.

### 2.3 The seam: library code vs configuration code

Configuring the model for one customer is a block of code that creates events, commands, and states, then wires transitions and actions. Fowler stops and points at the join:

> "The earlier code described how to build the state machine model; this last bit of code is about configuring that model for one particular controller. You often see divisions like this. On the one hand is the library, framework, or component implementation code; on the other is configuration or component assembly code. Essentially, it is the separation of common code from variable code." *(Ch. 1, "Programming Miss Grant's Controller")*

One compiled library is copied into many installations, each with its own configuration. This is the core architectural statement of the chapter: **a library is the common code; the client's usage is the assembly code; a DSL is an improved notation for the assembly code.** Everything downstream — fluent interfaces, expression builders, config formats — is about making the assembly code readable, not about making the library more capable.

### 2.4 Five surfaces, one model

Fowler then re-expresses the same customer configuration repeatedly, and each representation teaches something different:

**XML.** Advantages: no per-customer compilation (ship one library plus a parser, read the XML at startup); a declarative structure where actions and transitions are subelements of a state, which "in many ways reads much more clearly"; and — importantly — *constraint as a feature*: "We're also limited in that we can only express configuration in this file — limitations like this are often helpful because they can reduce the chances of people making mistakes in the component assembly code." The cost is that many mistakes are now detectable only at runtime. Fowler's mitigation is extensive testing, "which catches most of the errors with compile-time checking, together with other faults that type checking can't spot. With this kind of testing in place, I worry much less about moving error detection to runtime." Note the shape of that judgement: the tradeoff of compile-time safety for runtime reconfigurability is accepted *conditionally on having a strong testing practice*, not absolutely *(Ch. 1, "Programming Miss Grant's Controller")*.

**A custom textual syntax.** Terser, avoids quoting and noise characters, and above all easier to *read*. "You probably wouldn't have done it exactly the same way, but the point is that you can construct whatever syntax you and your team prefer." This is where the first working definition appears by enumeration: suitable only for a very narrow purpose; very simple, with no control structures and **not Turing-complete**; incapable of expressing a whole application, so it **must be combined with other languages**; and easy to edit and process precisely because of that simplicity.

Is the XML version also a DSL? Yes — it's "wrapped in an XML carrier syntax, but it's still a DSL." The choice between XML and a custom syntax is a *design* issue, not a definitional one. Whichever you pick, "the core tradeoffs of DSLs are the same. Indeed, you can argue that most XML configuration files are essentially DSLs."

**Ruby (internal).** The same configuration in a subset of Ruby, using symbols and blocks. Noisier than the custom syntax, still clear. The framing sentence is the important part:

> "I'm embedding the DSL into Ruby, using a subset of Ruby as my syntax. To an extent, this is more a matter of attitude than of anything else. I'm choosing to look at the Ruby code through DSL glasses." *(Ch. 1, "Programming Miss Grant's Controller")*

**Java (internal, fluent).** Discussed in §1.4 above — the plain assembly code is not a DSL; the builder subclass with chained calls is.

**A generated diagram.** Discussed in §2.8 below.

### 2.5 The Semantic Model, defined

From the DSL's point of view, the object model being populated is the **Semantic Model**. Syntax is the set of legal expressions of the program; semantics is what the program *means* and does when it executes. Here the model *is* the semantics. It sits close to a **Domain Model**, but the two are deliberately distinguished, and it is emphatically **not** an abstract syntax tree *(Ch. 1, "Languages and Semantic Model"; Ch. 3, "The Workings of a Parser")*.

The role of the DSL is simply to populate it. When the parser sees an event declaration it creates an event object and stashes it in a **Symbol Table**, so that when it later sees a transition referring to that event by name it can resolve the reference and call the model's ordinary API.

> "The model is the engine that provides the behavior of the state machine. Indeed you can say that most of the power of this design comes from having this model. All the DSL does is provide a readable way of populating that model — that is the difference from the command-query API I started with." *(Ch. 1, "Languages and Semantic Model")*

And the strongest normative claim in the chapter:

> "One opinion I've formed is that the Semantic Model is a vital part of a well-designed DSL. In the wild you'll find some DSLs use a Semantic Model and some do not, but I'm very much of the opinion that you should almost always use a Semantic Model." *(ibid.)*

He notes he can almost never find a universally applicable rule, hence the "almost."

The enumerated benefits are all separation-of-concerns arguments, and every one of them is a seam you can act on: a clear separation between parsing and semantics; the ability to reason about, extend, and debug the state machine without worrying about language issues; the ability to test the model by populating it through a plain command-query interface with no parser involved; and the ability to evolve model and DSL independently — building new features into the model before deciding how to expose them in the language. "Perhaps the most important point is that I can test the model independently of futzing around with the language." The chapter's own evidence is that *every* notation shown — XML, custom syntax, Ruby, Java-fluent — was built on the same Semantic Model and produced exactly the same configuration of objects.

On form: here it is an object model, but it can also be "a pure data structure with all behavior in separate functions" — still a Semantic Model, "because the data structure captures the particular meaning of the DSL script in the context of those functions."

### 2.6 Attribute the benefits correctly

This is the point most easily lost, and Fowler repeats it in three chapters:

> "Looking at it from this point of view, the DSL merely acts as a mechanism for expressing how the model is configured. Much of the benefits of using this approach comes from the model rather than the DSLs." *(Ch. 1, "Languages and Semantic Model")*

Easy configuration of a new customer, runtime change without recompiling, and reuse across installations are all properties of the *model*. "Hence the DSL is merely a thin facade over the model." A model delivers a great deal with no DSL present at all — that is why we use libraries and frameworks in the first place. "Good models, whether published as libraries or frameworks or just serving our own code, can work just fine without any DSL in sight." A DSL *enhances* a model: it makes it easier to see what a particular configuration does, and some DSLs enable runtime configuration. "DSLs are thus a useful adjunct to some models."

### 2.7 Adaptive Models

A state machine is a model whose *population acts as the program*: to change behavior you alter the objects and their interrelationships rather than the code. Fowler calls this an **Adaptive Model**. It blurs the code/data distinction — to understand behavior you must look at how instances are wired together, not just at the classes. Every program varies with its data, but here "the presence of the state objects alters the behavior of the system to a significantly greater degree" *(Ch. 1, "Languages and Semantic Model")*.

> "Adaptive Models can be very powerful, but they are also often difficult to use because people can't see any code that defines the particular behavior. A DSL is valuable because it provides an explicit way to represent that code in a form that gives people the sensation of programming the state machine." *(ibid.)*

That sentence is the tightest statement of *why DSLs and adaptive models go together*, and it recurs in §3.4 below.

### 2.8 Interpretation and code generation are deployment choices off one model

Two ways to get from script to behavior *(Ch. 1, "Using Code Generation")*:

- **Interpretation** — parse the text and immediately produce the result you want. (Fowler uses "interpret" strictly to mean immediate execution.)
- **Compilation** — parse the text, produce an intermediate output, then process that separately. "In the context of DSLs, the compilation approach is usually referred to as **code generation**."

In the interpreted arrangement the parser and Semantic Model both live inside the runtime processor; rules are parsed at startup and evaluated against the model. In the compiled arrangement the parser loads the Semantic Model *as part of the build*, a generator emits source, and that source is compiled into the runtime processor — no parser or model in production at all.

Code generation usually forces an extra compilation step (compile framework and parser → run parser to generate source → compile generated source), which "makes your build process much more complicated." It is worth it when the target platform has no DSL tooling — generating C for hardware that only understands compiled C — and Fowler cites projects generating MathCAD, SQL, and COBOL. You can also dodge the second compile by generating for a dynamic language.

His stance:

> "Many writings on DSLs focus on code generation, even to the point of making code generation the primary aim of the exercise... In my view, however, code generation is merely an implementation mechanism, one that isn't actually needed in most cases." *(Ch. 1, "Using Code Generation")*

And the anti-pattern he calls out: code generation is where people most often skip the Semantic Model and parse input text directly into generated code. "Although this is a common way of working with code-generating DSLs, it isn't one I recommend for any but the very simplest cases." Keeping the model gives you three separable concerns — parsing, execution semantics, and code generation — with concrete payoffs: switch a DSL from internal to external without touching the generators; produce multiple outputs without complicating the parser; run an interpreted model *and* generate code from the same source of truth.

There is also a preference about the *style* of generation, stated here and expanded in Ch. 8: either generate first-pass code intended to be hand-modified, or ensure generated code is never touched by hand. "I almost always prefer the latter because this allows code to be regenerated freely. This is particularly true with DSLs, since we want the DSL to be the primary representation of the logic that the DSL defines." Generated code must not be hand-edited, "although it can call, and be called by, handwritten code."

### 2.9 Visualization: a projection you cannot edit

The state diagram in Chapter 1 is not hand-drawn; Fowler generated it from the Semantic Model. The state machine classes not only execute, they render themselves in a graph-description language which lays the diagram out automatically.

A **visualization** is an alternative representation of a DSL script, similar to the DSL in that it lets a human understand the model, but **not editable**. "The visualization differs from the source in that it isn't editable — but on the other hand, it can do something an editable form cannot, such as render diagram like this" *(Ch. 1, "Visualization")*.

Three consequences worth keeping:

- Visualizations need not be graphical. Fowler uses plain textual visualizations to debug while writing a parser, and has seen teams generate spreadsheet visualizations to talk to domain experts.
- "Once you have done the hard work of creating a Semantic Model, adding visualizations is really easy."
- Visualizations are produced from the *model*, not from the DSL — so you can build them even if you have no DSL at all. This makes visualization a genuine *alternative* to a DSL when the only goal is domain-expert comprehension (a point Fowler presses against himself in §3.2).

> **SDK lens:** Ship the model, not the syntax. Everything a caller values — reuse, reconfiguration without redeployment, multiple execution targets, diagrams and docs — is a property of a well-factored object model with a plain, testable API. A fluent surface, a config file format, a CLI, and a generated client are all thin, replaceable projections of it, and treating them that way is what lets you add or replace one without disturbing the others. Two practical rules follow. First, when you justify a convenience layer, be honest about which benefits belong to the layer and which belong to the model underneath — most of them belong to the model. Second, every derived artifact (diagrams, reference docs, generated bindings, schemas) should be generated from that model rather than hand-maintained, because the moment two representations are maintained by hand they diverge.

---

## 3. Why and why not to build a DSL

### 3.1 Framing

Fowler's framing is deliberately modest: "DSLs are a tool with limited focus. They aren't like object orientation or agile processes which introduce a fundamental shift into the way we think about software development. Instead, DSLs are a very specific tool for very particular conditions. A typical project might use half a dozen or so DSLs in various places — indeed, many already do" *(Ch. 2, "Why Use a DSL?")*.

And the caution from §2.6, repeated before every benefit: a DSL is a thin veneer over a model, so "whenever you think about the benefits (or disadvantages) of a DSL, it's important to separate the benefits provided by the model from the benefits of the DSL. It's a common mistake to confuse the two."

### 3.2 The four reasons to build one

**(a) Improving development productivity.** The heart of the appeal is that a DSL "provides a means to more clearly communicate the intent of a part of a system." Clarity here is not aesthetics: "The easier it is to read a lump of code, the easier it is to find mistakes, and the easier it is to modify the system. So, for the same reason that we encourage meaningful variable names, documentation, clear coding constructs — we should encourage DSL usage." Defect cost is routinely underestimated, because defects hurt external quality *and* "slow developers down by sucking up time in investigations and fixes, sowing confusion about the behavior of the system." The crispest sentence in the book on why constraint pays:

> "The limited expressiveness of DSLs makes it harder to say wrong things and easier to see when you've made an error." *(Ch. 2, "Improving Development Productivity")*

Two secondary productivity arguments are directly relevant to library authors. A DSL **can help people learn an API**, "since it shifts focus to how different API methods should be combined together." And a DSL is a good way to **wrap an awkward third-party library**: "The DSL's usual advantages of a more fluent interface are magnified when the command-query interface is poor. In addition, the DSL only has to support the actual client usage, which can significantly reduce the surface area that the client developers need to learn." Note that the second half of that sentence attributes value to *omission*.

**(b) Communication with domain experts.** "I believe that the hardest part of software projects, the most common source of project failure, is communication with the customers and users of that software." A clear, precise language for the domain can improve that — but only sometimes. Many DSLs are unsuitable for this channel entirely (regular expressions, build dependencies): "Only a subset of stand-alone DSLs really apply to this communication channel" *(Ch. 2, "Communication with Domain Experts")*.

The **COBOL fallacy** is the argument that "now we can get rid of programmers and have business people specify the rules themselves." Fowler's dismissal is short: "It's a common argument, but I don't think it improves with repetition." What actually works is reading, not writing:

> "It's not that domain experts will write the DSLs themselves; but they can read them and thus understand what the system thinks it's doing. By being able to read DSL code, domain experts can spot mistakes. They can also talk more effectively to the programmers who do write the rules, perhaps by writing some rough drafts that can be refined into proper DSL rules." *(Ch. 2, "Communication with Domain Experts")*

He is not dogmatic — he has seen teams get domain experts writing significant behavior — but he keeps the emphasis: "I still think the biggest gain from using a DSL in this way comes when domain experts start reading it. Focusing on reading can be the first step towards writing the DSL, with the advantage that you lose nothing if you don't take that further step." Read-first is a low-risk staged adoption path, and its failure mode costs nothing.

He then raises a genuine counter-argument against himself: if all you want is for domain experts to understand the contents of a Semantic Model, "you can do this just by providing a visualization of the model. It's worth considering whether a visualization alone is a more efficient route than supporting a DSL. And it's useful to have visualizations in addition to a DSL." Involving domain experts in a DSL is close to involving them in building the model, and constructing a **Ubiquitous Language** deepens that; you might find them participating in the model and the DSL, or in the DSL only. "Indeed some people find that trying to describe a domain using a DSL is useful even if the DSL is never implemented. It can be beneficial just as a platform for communication." Net judgement: "involving domain experts in a DSL is difficult to achieve but has a high payoff. And even if you can't get the domain experts' involved, you may still get enough of a gain in developer productivity to make the DSL worth the effort."

**(c) Change in execution context.** The reason XML configuration spread: "we want code to run in a different environment." Shifting logic from compile time to runtime is a very common driver *(Ch. 2, "Change in Execution Context")*. Fowler's worked example: a project needed to trawl databases for contracts matching conditions and tag them. Running the query logic in the host language would have required loading all contracts into memory — far too slow. So the team wrote a DSL for the conditions, populated a Semantic Model, and used the model to **generate SQL** to run in the database. Writing SQL directly "was too difficult for the developers, let alone the business people. However, the business people could read (and in this case, write) the appropriate expressions in the DSL." Generalized: "Using a DSL like this can often make up for limitations in a host language, allowing us to express things in a comfortable DSL and then generate code for the actual execution environment to use."

Two further points from this section. Compared with a forms-based UI for capturing the same rules, a DSL has two concrete advantages: it is usually better at representing complicated logic, and it lets you use ordinary code-management tooling, "especially version control... When rules are entered via a form and stored in a database, version control is often neglected." And one commonly cited benefit is named as spurious: people argue the value of a DSL is that the same behavior can execute in different language environments. "This is a spurious benefit because you can gain this just by using a model; you don't need a DSL at all. A DSL can make it easier to understand these rules, but that's a separate issue."

**(d) Alternative computational model.** Mainstream programming is essentially all imperative — tell the computer what to do in what sequence, with conditionals, loops, and variables. "Imperative computation has become popular because it's relatively easy to understand and easy to apply to lots of problems. However, it isn't always the best choice." Build systems are the everyday example: you can express build logic imperatively, "but after a while most people recognize that it's easier to do with a **Dependency Network**." And again the attribution warning: "You don't need a DSL to use an alternative computational model. The core behavior of an alternative computational model comes from a Semantic Model... However, a DSL can make a big difference as it makes it much easier for people to manipulate declarative programs that populate the Semantic Model" *(Ch. 2, "Alternative Computational Model")*.

### 3.3 What "declarative" actually buys, and what it costs

Fowler dislikes the word "declarative" — it is used as a very broad brush — and his working definition is simply "something other than imperative" *(Ch. 7, opening)*. The chapter devoted to the subject supplies the sharpest test in the book for when a non-imperative surface earns its keep, by splitting "ease of understanding" into two distinct things:

1. **Understanding of intent** — what are we trying to achieve?
2. **Understanding of implementation** — how does the code work to satisfy that intent?

The imperative model is *excellent* at the second: you read the code and see what it does, and the debugger's step sequence corresponds exactly to source order. It is often weak at the first. If the intent genuinely *is* a sequence of actions, imperative code is fine and you should stop there. When intent is not naturally a sequence, another computational model is worth considering. **Alternative computational models trade implementation-comprehension for intent-comprehension** — that is the central judgement of the chapter, and it recurs everywhere *(Ch. 7, "Alternative Computational Models")*.

His decision-table example makes the trade concrete. An insurance scoring rule is naturally a small table: rows of conditions, rows of consequences, one column per case. Translating it into imperative code with one branch per column is *more verbose* than his usual terse style — and he prefers the verbose version, because its layout mirrors the domain expert's tabular thinking. But the correspondence is still imperfect in two instructive ways. The imperative encoding **forces an evaluation order** the table does not imply, injecting an irrelevant implementation artifact into the representation. More seriously, it **removes opportunities**: a real decision table can be checked for missing or duplicated permutations, and you cannot do that to a chain of conditionals. The generalizable principle: *a representation that carries less accidental structure carries more checkable structure.*

### 3.4 Adaptive Models and the mandatory tracing mechanism

The alternative is to build the abstraction (a decision table, a rule set, a state machine) and *configure* it. What you get: a faithful representation of the original; no spurious ordering (which may even permit concurrency); **self-validation**, since the table can tell you if the condition set is malformed or incomplete; and a shift of execution context from compile time to runtime.

An **Adaptive Model** is a representation where "the behavior is largely defined by the *instances* of the model and how they are wired together." You cannot know what behavior to expect without looking at the configuration of instances. Adaptive Models and DSLs are orthogonal notions that can be used independently — but they "go together like wine and cheese" *(Ch. 7, "Adaptive Model")*.

The negative is stated bluntly and at length, and should not be softened. Behavior is **implicit**; you cannot read the code and see what happens. Intent gets easier to understand and **implementation gets harder** — which bites hardest exactly when something breaks and you must debug. Adaptive models have a reputation for being hard to maintain; Fowler reports people taking *months* to figure out how one works, being very productive once they do, and many never getting there — "until then it's a nightmare." This is a real issue that rightly deters people. A DSL mitigates it by making the specific *configuration* easy to see; it does not remove the burden of understanding the generic machinery, but "can give you a significant leg up."

From the discussion of production rule systems comes the single most transferable warning in the chapter, stated as a general obligation rather than a suggestion: problems caused by implicit behavior are common to *all* alternative computational models, because we cannot reason about behavior by reading the code. **Therefore, whenever you implement an alternative computational model, you must also produce a tracing mechanism** that shows exactly what happened on a given execution — for a rule system, which rules fired, surfaced on demand so a puzzled user can follow the chain to an unexpected conclusion *(Ch. 7, "A Few Alternative Models")*.

The four models Fowler samples — **Decision Table**, **Production Rule System**, **State Machine**, and **Dependency Network** — each get a pattern chapter later, so they are covered in depth in Parts 2–3. Two distinctions from the survey are worth carrying forward now. First, chaining is what defines a production rule system (firing one rule changes whether others should fire), it is what makes rules writable one at a time without thinking about their interactions, and it is simultaneously the source of nearly all rule-system defects; a rule system *without* chaining is a good fit for validation rules. Second, a decision table is formally arguable as a rule system where each column is a rule, but that "misses the point": with a rule system you focus on behavior **one rule at a time**, with a decision table you focus on the **entire table**. *Computational models are distinguished by the unit of attention they impose, not just by their expressive power.*

On choosing one, Fowler is honest that he has no strong guidelines. It boils down to a sense that the model fits how you think about the problem; the best way to find out is to try it on paper first, describing behaviors in simple text and diagrams, and if it survives that desk check, build a prototype. And the sequencing rule that echoes §2: get the **Semantic Model** working properly first — a simple DSL may help during that process, but put the effort into tuning the model before chasing a very readable DSL. Once a reasonable model is in place, experimenting with different DSLs over it is comparatively easy *(Ch. 7, "Choosing a Model")*.

### 3.5 The four objections, and how much of each survives

Fowler judges the standard problems "currently overstated, usually because people aren't familiar enough with how to build DSLs and how they fit into the broader software development picture. Also, many commonly stated problems with DSLs stem from the same confusion between DSL and model that plague many stated DSL benefits" *(Ch. 2, "Problems with DSLs")*.

**Language cacophony.** The most common objection: many languages are harder to learn than one, making the system harder to work on and new people harder to onboard. Two misconceptions hide in it. First, mistaking the effort of learning a DSL for the effort of learning a general-purpose language — "DSLs are far simpler than a general-purpose language, and thus far easier to learn." Second, forgetting that projects always have complicated, hard-to-learn areas anyway: "Even if you don't have DSLs, you will typically have many abstractions in your codebase that you need to understand. Usually, these abstractions are captured in libraries in order to make them tractable. Even if you don't have to learn several DSLs, you still have to learn several libraries." The reframed question is how much harder it is to learn a DSL *than to learn the underlying model on its own*, and the incremental cost is small compared with understanding the model — "since the whole point of a DSL is to make it easier to understand and manipulate the model, **having a DSL should reduce the learning cost**."

**Cost of building.** A DSL may be a small increment over its library, "but it's still a cost. There's still code to write and above all to maintain. Thus, like any code, it has to pull its weight." The direct rule for library authors:

> "Not every library benefits from having a DSL wrapper over it. If a command-query API does the job just fine, then there's no value in adding another API on top of it. Even if a DSL might help, sometimes it would just be too much effort to build and maintain for the marginal benefit." *(Ch. 2, "Cost of Building")*

Maintenance factors: "Even a simple internal DSL may cause problems if most of the development team finds it difficult to understand. External DSLs in particular add a lot of moving parts to the process, with parsers that are often intimidating for developers." Unfamiliarity inflates the first estimate, but "learning curve costs can be amortized across multiple times that you might use a DSL in the future." And the accounting rule: the cost is measured against the model, not against nothing — "if it's complicated enough to consider a DSL, it's almost certainly complicated enough to benefit from a model." On the fear that encouraging DSLs produces many bad ones: "Indeed I expect many bad DSLs to be built, just as there are plenty of libraries with bad command-query APIs. The question is whether a DSL will make things worse. A good DSL can wrap a bad library and make it easier to deal with (although I'd rather fix the library if I can). A bad DSL is a waste of resources to build and maintain, but that can be said of any bad code."

**Ghetto language.** The opposite fear: a company builds its systems on an in-house language used nowhere else, making hiring hard and technological change harder. Fowler's first move is definitional: "if you're writing whole systems in a language, that means it isn't a DSL (at least by my definition) but a general-purpose language... Building and maintaining a general-purpose language is a big undertaking that condemns you to a lot of work and a life in a ghetto. Don't do that." Two real issues hide inside the objection:

1. **Scope creep into a general-purpose language.** "There's always a danger for a DSL to accidentally evolve into a general-purpose language. You take your DSL and gradually add new features; today you add conditional expressions, another day you add loops, and whoops — you're Turing-complete." The defense: "guard firmly against it. Make sure you have a clear sense of what narrow problem the DSL is focused on. Question any new features that seem to fall outside that mission. If you need to do more, consider using more than one language and combining them, instead of letting one DSL grow too big." He then generalizes it explicitly to libraries: "The same problem can plague frameworks. A good library has a clear sense of purpose. If your product pricing library includes an implementation of the HTTP protocol, you're suffering from essentially the same failure to separate concerns."
2. **Building yourself what you should take from outside.** Equally true of libraries. "My general rule with software is that if it's not your business, don't write it yourself — always look to take it from somewhere else. In particular, with the rise of open source tools it often makes sense to work on extending an existing open source effort than writing your own from scratch."

**Blinkered abstraction.** The most subtle objection, and the one Fowler concedes most to. The value of a DSL is the abstraction it gives you for thinking about a subject area — "However, any abstraction, be it a DSL or a model, always carries with it a danger — that of putting blinkers on your thinking. With a blinkered abstraction, you spend more effort on fitting the world into your abstraction than the other way around. You see this when you come across something that doesn't fit in with the abstraction — and you burn time trying to make it fit, instead of changing the abstraction to easily absorb the new behavior." When it happens: "Blinkering tends to occur once you've got comfortable with an abstraction and you feel it's bedded down — at this point it's natural to be worried by the prospect of uprooting it." Why a DSL makes it worse: "Since a DSL provides a more comfortable way of manipulating an abstraction, it can make you more reluctant to change it. This problem can be exacerbated when using the DSL with domain experts, who often are even more reluctant to change an abstraction once they get used to it." The remedy is an attitude, not a technique: "As with any abstraction, you should always look at a DSL as something that's evolving, not finished" *(Ch. 2, "Blinkered Abstraction")*.

### 3.6 The decision rule

> "Fundamentally, the only reason to not use a DSL is if you don't see any of the benefits of a DSL apply to your situation — or at least, you don't see the benefits being worth the cost of building the DSL." *(Ch. 2, "Problems with DSLs")*

### 3.7 Language-processing techniques are useful beyond DSLs

Worth noting because it widens the applicability of everything in Part 1: "90% of the use of language processing techniques in an average development team is for DSLs. But these techniques can be used for some other things as well." Fowler's example is a team that had to exchange messages whose payloads were defined by COBOL copybooks; a colleague built a parser for the subset of copybook syntax in use and generated classes to interface to those records. Payoffs: they could interface to as many copybooks as needed, "none of the rest of the code needed to know about COBOL data structures, and any changes could be handled with a simple regeneration." Fowler: "It would be an appalling stretch to call COBOL copybooks a DSL — but the same basic techniques that we use for external DSLs did the trick" *(Ch. 2, "Wider Language Processing")*.

> **SDK lens:** Build the fluent or declarative layer only when you can name which benefit you are buying — clearer intent at the call site, a smaller learnable surface over an awkward dependency, a rule format your users' non-programmers can *read*, or execution in a context your host language can't reach. If a plain command-query API already does the job, adding another API on top has negative value: more to maintain, more to document, more ways to say the same thing. When you do build a declarative surface, the deciding test is whether the domain's natural mental model is a sequence of steps (ship functions) or a table, graph, rule set, or state machine (a declarative surface buys real comprehension *and* machine-checkable structure). If you take that route, you owe your users a tracing/explanation mechanism, because you have just traded away the debuggability that imperative code gave them for free. And police scope relentlessly: the pricing library that grows an HTTP implementation and the config format that grows loops are the same failure.

---

## 4. The DSL lifecycle

### 4.1 Two starting points

The book's presentation order — describe a framework and its command-query API, then layer a DSL over it — is pedagogical, "but it's not the only way that people use DSLs in practice" *(Ch. 2, "DSL Lifecycle")*.

**Language-first.** "you begin with some scenarios and write those scenarios down in the way you'd like the DSL to look. If the language is part of the domain functionality, it's good to do this with a domain expert — this is a good first step to using the DSL as a communication medium." Two styles for the early drafts: some people insist the drafts already be syntactically valid (host-language syntax for internal DSLs; statements they're confident they can parse for external ones); "Others are more informal at the beginning and then take a second pass through the DSL to get it close to a reasonable syntax." The workflow is to sit with people who understand customers' needs, assemble a set of example behaviors from what has been asked for in the past or is expected in future, write each one in some DSL form, and modify the DSL as you go to support new capabilities. "By the end of the exercise, you'll have worked through a reasonable sample of cases and will have a pseudo-DSL description of each of them." (Tooling note: if you plan to use a language workbench, this stage happens outside it — plain text editor, drawing software, or pen and paper.)

**Model-first.** "Usually it is used when you don't think about using a DSL at first, or aren't sure you'll need one. You thus build the framework, work with it for a while, and then decide that a DSL would be a useful addition." The trigger in the running example: you have a state machine model in use by many customers, and adding a new customer is harder than you'd like.

### 4.2 Four artifacts, and the sequencing choice

Implementing involves four things, and their order is a genuine choice: designing the model in the host language; the command-query API for the model; the concrete syntax of the DSL; and the translation between the DSL and the command-query API. Fowler has observed three sequencing styles — (a) little bits at a time across all four, "building a little bit of the model, adding the DSL to drive it, and hooking that thread all up with tests"; (b) build and test the framework first, then layer the DSL over it; (c) get the DSL in place, then build the library, then fit them together. "As I'm an incrementalist, I prefer thin slices of end-to-end functionality, so I go with the first of the three" *(Ch. 2, "DSL Lifecycle")*.

His own loop: start with the simplest case; write a library supporting that case using test-driven development; then implement the DSL for it and tie it to the framework; then pick the next case, evolving framework and tests first, then the DSL. Inside that loop sits a judgement worth preserving exactly:

> "I'd be happy to make some changes to the DSL to make it easier to build, although I would run those changes past the domain expert to ensure we still share a common communication medium." *(Ch. 2, "DSL Lifecycle")*

Syntax may be bent for implementability — but not unilaterally. The constraint is the property that made the DSL worth building: that it remains a shared communication medium.

### 4.3 Growing a DSL over an existing model

Two approaches, distinguished by which side you push from *(Ch. 2, "DSL Lifecycle")*:

- **Language-seeded.** "slowly builds the DSL on top of the model, treating the model as a mostly black box. We would start by looking at all the controllers we currently have and sketching out pseudo-DSL for each one. Then we'd implement the DSL scenario by scenario... We usually wouldn't make any deep changes to the model, although I would be happy to add methods to the model to help support the DSL."
- **Model-seeded.** "we'd add fluent methods to the model first, to make it easier to configure the model, and then gradually draw them away into a DSL. This approach is more oriented towards internal DSLs; you can think of it as a heavy refactoring of the model to derive the internal DSL. An appealing aspect to the model-seeded approach is that it's very gradual, so it doesn't inflict a notable cost to build the DSL."

Note the tension with the rule from Ch. 4 that you should not mix fluent and command-query methods on the same class (§6.2 below): the model-seeded route deliberately starts by violating it, and the "drawing away into a DSL" step is what resolves the violation. Treat the fluent methods on the model as a transitional state, not a destination.

### 4.4 Extract the seam before you design the surface

The most important lifecycle instruction is about a case that starts messier than either of the above: you build several instances of a thing and only later realize there's a lot of common functionality. "I'd then refactor the system to create separation between the model and the configuration code. **This separation is the vital step.** While I might have a DSL in mind while doing it, I'd be more inclined to get the separation done first, before putting the DSL on top" *(Ch. 2, "DSL Lifecycle")*.

### 4.5 Version control

"Do make sure all your DSL scripts are kept under some form of version control system. A DSL script becomes part of your code and thus should be under version control just like everything else. The great thing about textual DSLs is that they play well with version control systems, allowing you to keep a clear track of the changes to the behavior of your system" *(Ch. 2, "DSL Lifecycle")*. This is the same argument that reappears in Ch. 9 as the reason source-based editing has resisted projectional editing (§8.11) and in Ch. 2 as an advantage of DSLs over forms-driven rule entry (§3.2c) — text is what makes the surrounding ecosystem of diff, merge, review, and history possible.

### 4.6 What makes a good DSL design?

Fowler opens this section by conceding he does not have a clear answer: "I'd love to have a good advice to share, but I confess I don't have a clear idea in my mind." What he does offer *(Ch. 2, "What Makes a Good DSL Design?")*:

- **Clarity for the reader is the goal.** "The overall goal for a DSL, as with any writing, is clarity for the reader. You want your typical reader, which may be a programmer or a domain expert, to be able to understand what the sentences in the DSL mean, as quickly and clearly as possible. While I don't feel I can say much about how to do that, I do think it's valuable to keep that goal in mind as you work."
- **Iterate against a real audience.** "Try out ideas on your target audience. Be prepared to provide multiple alternatives and see how people react. Getting a good language will involve trying and rejecting lots of missteps. Don't worry about wrong turns; the more of those you make and correct, the more likely you are to find a good path."
- **Use domain jargon** — in the DSL *and* in the Semantic Model. "If the users of the DSL are familiar with the jargon, then they should see it in the DSL. Jargon is there to enhance communication within a domain even if it sounds like gibberish to those outside."
- **Follow the conventions of the surrounding environment.** If the team lives in a curly-brace language, use that family's comment markers and block delimiters.
- **The one specific caution — do not imitate natural language.**

> "Don't try to make the DSL read like natural language. There have been various attempts to do that with general-purpose languages, with Applescript as the most obvious example. The trouble is that such attempts lead to a lot of syntactic sugar which complicates understanding of the semantics. Remember that a DSL is a programming language, so using it should feel like programming, with the greater terseness and precision that programming has compared to a natural language. Trying to make a programming language look like natural language puts your head into the wrong context; when you're manipulating a program, you must always remember you're in a programming language environment." *(Ch. 2, "What Makes a Good DSL Design?")*

> **SDK lens:** Before you design any convenience surface, extract the seam between your invariant engine and the code that configures it for a particular use — that separation is worth having on its own, and every later option (a builder, a config format, a plugin API, a generated client) becomes cheap once it exists. Then grow the surface in thin end-to-end slices against real usage scenarios, written the way you wish callers could write them, rather than designing the whole surface up front. You may bend the surface to make it implementable, but if you built it for a specific audience, run the bend past that audience — the readability property is the asset, and implementation convenience is not automatically allowed to spend it. Finally, the standard failure mode of fluent APIs is chasing English-sentence readability: the target is *terse and precise*, not *prose-like*.

---

## 5. Implementing: the processing architecture

### 5.1 The reference pipeline

Everything in the book hangs off one diagram:

```
DSL script → parse → Semantic Model → [optional] generate → target code
```

The generation step is drawn in brackets because it is explicitly optional *(Ch. 3, "Architecture of DSL Processing")*. "all the important semantic behavior is captured in a model, and the DSL's role is to populate that model via a parsing step. This means that the Semantic Model plays a central role in how I think about DSLs — indeed almost all of this book assumes you are using one."

On form, Fowler describes himself as "an OO bigot" who naturally reaches for a rich object model combining data and processing, but explicitly permits the alternative: "a Semantic Model doesn't need to be like that; it can also be just a data structure. While I'd always rather have proper objects if I can, **using a data model form of Semantic Model is better than not using a Semantic Model at all.**"

It is kept distinct from a **Domain Model**: "The Semantic Model of a DSL is usually a subset of the application's Domain Model, as not all parts of the Domain Model are best handled by the DSL. In addition, DSLs may be used for tasks other than populating a Domain Model, even when one is present." And it is "a completely normal object model, which can be manipulated in the same way as any object model you might have... In a sense, it's thus independent of the DSL, although in practice the two are close siblings."

The advantages restate and sharpen those from Ch. 1: you can think about semantics without syntax entanglement (and if you're using a DSL at all, what you're representing is complex enough to deserve its own model); you can test the model by creating objects directly and isolate execution problems without understanding the parser; you can support **multiple DSLs over one model** — "You might start with a simple internal DSL, and later add an external DSL as an alternative version that's easier to read... Since both DSLs can parse into the same Semantic Model, this isn't difficult. It also helps to avoid any duplication between the languages"; and you can evolve the two independently — "I can compare two syntaxes by comparing how they populate the Semantic Model."

The framing analogy is memorable and, for library designers, the most portable sentence in the chapter:

> "In many ways, this separation of the Semantic Model and DSL syntax mirrors the separation of domain model and presentation that we see in designing enterprise software. Indeed on a hot day I think of a DSL as another form of user interface." *(Ch. 3, "Architecture of DSL Processing")*

He immediately states the limit of the analogy, which keeps it honest: "The DSL and the Semantic Model are still connected. If I add new constructs to the DSL, I need to ensure they are supported in the Semantic Model, which often means modifying the two at the same time. However, the separation does mean I can think about semantic issues separately from parsing issues, which simplifies the task."

### 5.2 Where internal and external differ — and the Expression Builder layer

"The difference between internal and external DSLs lies in the parsing step — both in what is parsed and in how the parsing is done. Both styles of DSL will produce the same kind of Semantic Model... there's no reason to not have a single Semantic Model populated by both internal and external DSLs."

For external DSLs the separation between scripts, parser, and model is obvious. For internal DSLs it is easy for things to get mixed up, hence the structural recommendation:

> "I advocate having an explicit layer of objects (**Expression Builders**) whose job is to provide the necessary fluent interfaces to act as the language. DSL scripts then run by invoking methods on an Expression Builder which then populates the Semantic Model. Thus in an internal DSL, parsing the DSL scripts is done by a combination of the host language parser and the Expression Builders." *(Ch. 3, "Architecture of DSL Processing")*

Fowler admits discomfort with calling this "parsing" and defends the parallel: "With traditional parsing, you take a stream of text, arrange that text into a parse tree, and then process that parse tree to produce a useful output. With parsing an internal DSL, your input is a series of function calls. You still arrange them into a hierarchy (usually implicitly on the stack) in order to produce useful output."

He also refines the internal/external distinction. The "written in the base language of your application" test is "usually right, but not 100% so" — a Java application with a DSL written in a JVM-hosted dynamic language is still an internal DSL.

> "The true distinction between the two is that internal DSLs are written in an executable language and parsed by executing the DSL within that language. In both JRuby and XML, a DSL is embedded into a carrier syntax, but we execute the JRuby code and just read the XML data structures." *(Ch. 3, "Architecture of DSL Processing")*

### 5.3 Execution: run the model, or generate code

"The simplest, and usually the best, is just to execute the Semantic Model itself. The Semantic Model is code and as such can run and do all it needs to." Against the widespread assumption otherwise: "In some circles, code generation is seen as an essential part of DSLs... **Yet DSLs have no inherent need for code generation.** A lot of the time the best thing to do is just to execute the Semantic Model."

The strongest case for generating: "when there is a difference between where you want to run the model and where you want to parse the DSL... You don't want to run a parser in your toaster or in SQL, so you implement the parser and Semantic Model in a more suitable language and generate C or SQL." A related case is when the parser drags library dependencies you don't want in production — "This situation is particularly common if you are using a complex tool for your DSL, which is why language workbenches tend to do code generation."

Even when you generate, keep a runnable model in the parsing environment: it lets you experiment with DSL execution without simultaneously understanding the generator, test parsing and semantics without generating (faster tests, easier isolation), and run validations on the model that catch errors *before* generating code. There is even a social argument for generating: "many developers find the kind of logic in a rich Semantic Model difficult to understand. Generating code from the Semantic Model makes everything much more explicit and less like magic. This could be a crucial point in a team with less capable developers."

And the image that fixes the stance in memory:

> "the most important thing to remember about code generation is that it's an *optional* part of the DSL landscape. It's one of those things that are absolutely essential if you need them, yet most of the time you don't. I think of code generators as snowshoes: If I'm hiking in winter over deep snow I really have to have them, but I'd never carry them on a summer day." *(Ch. 3, "Architecture of DSL Processing")*

### 5.4 The workings of a parser — and the ghostly syntax tree

> "parsing is a strongly hierarchical operation. When we parse text, we arrange the chunks into a tree structure." *(Ch. 3, "The Workings of a Parser")*

A **syntax tree** (or parse tree) is that hierarchy. "Any script can be turned into many potential syntax trees — it just depends on how you decide to break it down. A syntax tree is a much more useful representation of the script than the words, for we can manipulate it in many ways by walking the tree." Crucially the same hierarchy exists in an internal DSL, even without any explicit list construct — an event is still a node containing a name and a code.

The key judgement — and the reason the Semantic Model is not an AST:

> "If we are using a Semantic Model, we take the syntax tree and translate it into the Semantic Model. If you read material in the language community, you'll often see more emphasis placed on the syntax tree — people execute the syntax tree directly or generate code off the syntax tree. Effectively, people can use the syntax tree as a semantic model. Most of the time I would not do that, because the syntax tree is very tied to the syntax of the DSL script and thus couples the processing of the DSL to its syntax." *(Ch. 3, "The Workings of a Parser")*

The model is also typically a much smaller, more meaningful structure than the tree.

The tree is frequently **ghostly**: "A lot of the time the syntax tree is formed on the call stack and processed as we walk it. As a result, you never see the whole tree, just the branch that you are currently processing." In an internal DSL it is formed by nested function arguments and chained objects; where there's no strong hierarchy you simulate it with **Context Variables**. External DSLs lead to a more explicit tree — sometimes a real data structure (**Tree Construction**) — but even they are commonly processed with the tree forming and pruning continuously on the stack. "The syntax tree may be ghostly, but it's still a useful mental tool."

### 5.5 Grammars, syntax, and semantics

A **grammar** is "a set of rules which describe how a stream of text is turned into a syntax tree," consisting of **production rules** that name a term and state how it decomposes, referring to each other.

There is no *the* grammar:

> "It's important to realize that a language can have multiple grammars that define it. There is no such thing as *the* grammar for a language. A grammar defines the structure of the syntax tree that's generated for the language, and we can recognize many different tree structures for a particular piece of language text. A grammar just defines one form of a syntax tree; the actual grammar and syntax tree you'll choose will depend on many factors, including the features of the grammar language you're working with and how you want to process the syntax tree." *(Ch. 3, "Grammars, Syntax, and Semantics")*

A grammar defines syntax only. "It doesn't tell you anything about its semantics, that is, what an expression means. Depending on the context, `5 + 3` could mean `8` or `53`; the syntax is the same but the semantics may differ." Which leads to the operational — and testable — definition of semantics:

> "With a Semantic Model, the definition of the semantics boils down to how we populate the Semantic Model from the syntax tree and what we do with the Semantic Model. In particular, we can say that **if two expressions produce the same structure in the Semantic Model, they have the same semantics, even if their syntax is different.**" *(ibid.)*

That definition is what makes "compare two syntaxes by comparing how they populate the model" an actual technique rather than a slogan.

Grammars matter for internal DSLs too, even though there's no explicit one: "it's still useful to think in terms of a grammar for your DSL. **This grammar helps you choose which of the various internal DSL patterns you might use.**" There is a subtlety worth naming: an internal DSL involves *two* parses and two grammars — the host language's parse, which produces executable instructions, and then the notional DSL grammar that comes into play as those instructions execute and build the ghostly tree.

### 5.6 Parsing data

As the parser runs it must store information about the parse. "The parse is inherently a tree walk, and whenever you are processing a part of a DSL script, you'll have some information about the context within the branch of the syntax tree that you're processing. However, often you need information that's outside that branch" *(Ch. 3, "Parsing Data")*. The canonical case: a command is declared in one block and referenced from a state's action clause on a different branch; if the only representation of the tree is the call stack, the declaration has already vanished.

Three structures answer this, each with its own judgement attached (all three get pattern chapters, so they are **covered in depth in Part 2**):

- **Symbol Table** — "essentially a dictionary whose key is the identifier... and whose value is an object that represents the command in our parse." Stash an object when you process a definition; look it up when you process a reference. The stashed object may be a Semantic Model object or an intermediate one local to the parse. "A Symbol Table is thus a crucial tool for making the cross-references."
- **Construction Builder** — a mutable intermediate object with the same fields as a Semantic Model object, used when the model object's data is read-only after construction but you gather that data gradually during the parse. The judgement is the point: "Using a Construction Builder complicates the parser but I'd rather do that than alter the Semantic Model to forgo the benefits of read-only properties." Sometimes you defer *all* model creation until the whole script is processed, giving the parse two distinct phases.
- **Context Variable** — a variable holding "where you are" when the tree can't tell you. "Although a Context Variable is often a straightforward tool to use, in general I prefer to avoid them as much as possible. The parsing code is easier to follow if you can read it without having to mentally juggle Context Variables, just as lots of mutable variables make procedural code more complicated to follow. Certainly there are times when you can't avoid using a Context Variable, but I tend to see them as a smell to be avoided."

### 5.7 Macros, and why Fowler avoids them

Usable with both internal and external DSLs. "They used to be used pretty widely, but are less common now. In most contexts I'd suggest avoiding them, but they are occasionally useful" *(Ch. 3, "Macros")*.

**Textual macros** substitute text for text. The motivating example is a stylesheet language that forces colors to be written as hex codes: the code is meaningless and repeating it is duplication, "like any form of code duplication, is a Bad Thing," so you would rather name it once. Since the language has no facility for that, you can run a macro processor over a source file. More involved processors take parameters — the classic example being a preprocessor macro replacing `sqr(x)` with `x * x`.

> "Macros provide a lot of opportunities to create DSLs, either within a host language (as the C preprocessor does) or as a stand-alone file transformed into a host language. The downside is that macros have a number of awkward problems that make them difficult to use in practice. As a result, textual macros have pretty much fallen out of favor, and most mavens like me advise against them." *(Ch. 3, "Macros")*

**Syntactic macros** also substitute, but they work on syntactically valid elements of the host language, transforming one kind of expression into another. Lisp is famous for them (C++ templates are a better-known instance for many readers), and they are a core internal-DSL technique in Lisp — but "you can only use syntactic macros in a language that supports them; I therefore don't talk about them much in this book, since relatively few languages do."

### 5.8 Testing DSLs: three areas, because there are three seams

> "With DSLs, I can break testing down into three separate areas: testing the Semantic Model, testing the parser, and testing the scripts." *(Ch. 3, "Testing DSLs")*

That three-way split is a direct consequence of the architecture: every seam is a test boundary.

**Testing the Semantic Model.** "These tests are about ensuring that the Semantic Model behaves the way I expect it to... This is standard testing practice, the same as you would use with any framework of objects." The key property: "For this testing, I don't really need the DSL at all — I can populate the model using the basic interface of the model itself." Fowler's preferred factoring is several *small* fixtures, each a minimal configuration exercising one feature, sharing an abstract superclass that sets up the common wiring and supplies test utility methods and custom assertions so the tests read cleanly. An alternative is one larger fixture demonstrating many features, again populated through the command-query interface. And one ordering rule that matters:

> "As the test fixtures get more complex, however, I can simplify the test code by using the DSL to create fixtures. **I can do this if I have tests for the parser.**" *(Ch. 3, "Testing the Semantic Model")*

You may use the DSL as a fixture-construction convenience only once the parser is independently trusted — otherwise a parser bug silently corrupts your model tests.

**Testing the parser.** "the job of the parser is to populate the Semantic Model. So our testing of the parser is about writing small fragments of DSL and ensuring that they create the right structures in the Semantic Model." Reaching into the model to assert on individual objects "is rather awkward, and may result in breaking encapsulation on the objects in the Semantic Model." Better: **model comparison** — build the *expected* model with the command-query API, parse the DSL to get the *actual* model, and assert equivalence. Two refinements. Equivalence is richer than equality and you need more than a boolean, so the comparison uses a **Notification**: a probe walks the model and records every difference, "This way I find all differences instead of stopping at the first one," and the notification's report becomes the failure message. And run the probe in both directions, because a one-directional walk finds missing elements but not extra ones: "You may think I'm being paranoid by doing the equivalence assertion in both directions, but usually the code *is* out to get me."

**Invalid input tests.** Negative tests probe what happens with bad input. "The first time you run such a test, it's interesting to see what happens. Often you'll get an obscure but violent error." That may be acceptable. The real danger is the opposite:

> "It's worse if you supply an invalid DSL, parse it, and get no error at all. This would violate the principle of 'fail fast'... If you populate a model in an invalid state and have no checks for that, you may find out there's a problem till later. At that point, there is a distance between the original fault (loading an invalid input) and the later failure, and that distance makes it harder to find the fault." *(Ch. 3, "Invalid Input Tests")*

His worked case: a script naming an undeclared target state parsed successfully — the test *passed*, which is bad — and then any later use of the model, even printing it, blew up with a null dereference. Where the check belongs is a clean responsibility argument: "Since the problem is that I'm creating an invalid structure in the Semantic Model, the responsibility to check for this problem is that of the Semantic Model — in this case, the method that adds a transition to a state." He then changes the test to expect the resulting exception, which both documents what error invalid input produces and detects if that behavior changes. And a calibrated stance on defensive checks: he deliberately did *not* assert on the trigger event, because a null event fails immediately anyway. "In general, I don't do not-null assertions on my method arguments, as I feel the benefit isn't worth the extra code to read. **The exception is when this leads to a null that doesn't cause an immediate failure.**"

**Testing the scripts.** "the DSL scripts are also code, and we should consider testing them." Against the objection that scripts are too simple to be worth testing:

> "I see testing as a double-check mechanism. When we write code and tests, we are specifying the same behavior using two different mechanisms, one involving abstractions (the code) and the other using examples (the tests). For anything of lasting value, we should always double-check." *(Ch. 3, "Testing the Scripts")*

"The general approach is to provide a test environment that allows you to create text fixtures, run DSL scripts, and compare results. It's usually some effort to prepare such an environment, but just because a DSL is easy to read doesn't mean people won't make mistakes." Script tests double as integration tests, "since any errors in the parser or Semantic Model should cause them to fail," so it is worth sampling a few scripts for that purpose. Visualizations help here too — presenting information in multiple ways helps people find errors, which is the same double-check logic. And a self-referential observation: building readable test scenarios naturally leads to *another* DSL. "That's not uncommon; **testing scripts is a common use of DSLs as they fit well with the need for a limited, declarative language.**"

### 5.9 Handling errors

Fowler opens with a scope confession: "There are many topics I'd like to have explored further in this book, but the top of that list is error handling" *(Ch. 3, "Handling Errors")*. He repeats the compiler-writers' lore that "parsing and output generation are the easy part of compiler writing — the hard part was giving good error messages," and gives a realistic assessment of the state of practice: "Good diagnostics are a rarity even in successful DSLs. More than one highly useful DSL package does little in the way of helpful information," with a widely used graph tool reporting only `syntax error near line 4` — "I feel somewhat lucky even to get a line number."

The tradeoff is stated plainly: "diagnostics are yet another thing to be traded off. Any time spent on improving error handling is time not spent adding other features. The evidence from many DSLs in the wild is that people do tolerate poor error diagnostics. After all, DSL scripts are small, so crude error finding techniques are more reasonable with them than with general-purpose languages." But: "In a heavily used library, good diagnostics can save a lot of time. Every tradeoff is unique, and you have to decide based on your own circumstances."

The cheapest practical advice: support comments, terminated by line endings, so people can use "the crudest error-finding technique of all — commenting out."

The architectural question is where error handling lives. Syntactic errors obviously belong to the parser (and some come free — host language syntax errors for internal DSLs, grammar errors from a parser generator for external ones). Semantic errors are a genuine choice. Arguments for putting them in the model: "The model is really the right place to check the rules of semantically well-formed structures. You have all the information structured the way you need to think about it, so you can write the clearest error checking code here," and "you'll need the checking here if you want to populate the model from more than one place, such as multiple DSLs or using a command-query interface." The serious disadvantage: "There's no link back to the source of the problem in the DSL script, not even an approximate line number."

Three strategies for recovering script context, with his verdict:

1. **Put detection rules in the parser.** "the problem with this strategy is that it makes it much harder to write the rules, as you are working on the level of the syntax tree rather than the semantic model. You also have a much greater risk of duplicating the rules."
2. **Push syntactic information into the model** (line numbers on model objects). "The problem is that this can make the Semantic Model much more complicated as it has to track the information. Additionally, the script may not map that cleanly to the model, which could result in error messages that are more confusing than helpful."
3. **(Preferred) Detect in the model; initiate from the parser.** The parser parses a chunk, populates the model, then tells the model to look for errors; the model reports semantic problems and the parser adds the script context it alone knows. "**This separates the concerns of syntactic knowledge (in the parser) and semantic knowledge (in the model).**"

The organizing frame:

> "A useful approach is to divide error handling into initiation, detection, and reporting. This last strategy puts initiation in the parser, detection in the model, and reporting in both, with the model supplying the semantics of the error and the parser adding syntactic context." *(Ch. 3, "Handling Errors")*

### 5.10 Migrating DSLs

> "One danger that DSL advocates need to guard against is the notion that first you design a DSL, then people use it. Like any other piece of software, a successful DSL will evolve. This means that scripts written in an earlier version of a DSL may fail when run with a later version." *(Ch. 3, "Migrating DSLs")*

The framing is explicitly the library-compatibility problem: "the DSL definition is essentially a published interface, and you have to deal with the consequences just the same." The distinction between *published* and merely *public* is that a published interface "is used by code written by a separate team. Therefore, if the team that defines the interface wants to change it, they can't easily rewrite the calling code." (With nonpublished DSLs, an internal DSL may be easier to change if the language has automated refactoring tools.)

Two broad migration approaches, with no strong preference between them:

1. **Incremental migration** — the evolutionary-database-design tactic. For every change to the DSL definition, write a migration program that converts scripts from the old version to the new, and ship those with the release. **Keep each change small:** "Imagine you are upgrading from version 1 to 2, and have ten changes... don't create just one migration script... instead, create at least ten scripts. Change the DSL definition one feature at a time, and write a migration script for each change... This may sound like more work than a single script, but the point is that migrations are much easier to write if they are small, and it's easy to chain multiple migrations together. As a result, you'll be able to write ten scripts much faster than one."
2. **Model-based migration** — available only because you have a Semantic Model. Keep one parser per released version, all populating the same model. "When you use a semantic model, the parser's behavior is pretty simple, so it's not too much trouble to have several of them around." To actually migrate scripts, write a generator that emits a DSL script from the model: parse a v1 script, populate the model, emit a v2 script. The problem: "it's easy to lose stuff that doesn't matter for the semantics but is something that the script writers want to keep. Comments are the obvious example. This is exacerbated if there's too much smarts in the parser, although then the need to migrate this way may encourage the parsers to stay dumb — **which is a Good Thing.**" If the change is large enough that a v1 script can't produce a v2 model, keep a v1 (or intermediate) model around and give it the ability to emit v2.

**Version statements.** If migrations are to run automatically, the script should record which version of the DSL it is, so the parser can detect it and trigger migrations. "some DSL authors argue that all DSLs should have a mandatory version statement in a script... While a version statement may add a bit of noise to the script, **it's something that's very hard to retrofit.**"

**Not migrating is an option.** "keep the version 1 parser and just let it populate the version 2 model. You should help people migrate, and they will need to if they want to use more features. But supporting the old scripts directly, if you can, is useful since it allows them to migrate at their own pace." And a closing dose of realism: "there is the question of whether they are worth it in practice... the problem is exactly the same as with widely used libraries, and automated migration schemes have not been used much there."

> **SDK lens:** Three transferable rules. **(1) Layer your validation the way Fowler layers error handling:** the domain layer owns the invariants and produces semantic errors; the boundary layer (request parser, config loader, CLI) initiates validation and enriches errors with source context — field path, line number, request id — and neither duplicates the other's knowledge. Accumulate all problems into a notification rather than failing on the first, and add defensive argument checks only where their absence would *delay* the failure, not reflexively. **(2) Absorb mutability into builders** so your model objects can stay immutable; a builder exists to protect an invariant-holding target, not merely to shorten a constructor. And treat ambient "current object" state — thread-locals, open scopes, implicit context — as the same smell Fowler assigns to Context Variables: prefer designs where the call structure itself carries the hierarchy. **(3) Anything you publish is a published interface**, including your config schema. Plan migrations as many small steps rather than one big one, put a version marker in the format from day one because it is nearly impossible to retrofit, and remember that continuing to accept old input is often cheaper and kinder than migrating it.

---

## 6. Internal DSL techniques overview

This section surveys the techniques; each named pattern gets full treatment in Part 2, so the aim here is to convey what the choices *are* and what each one costs.

### 6.1 The framing: you are constrained by the host language

Internal DSLs are the most approachable flavor to write — no grammars, no parsing tools, and you stay inside your normal language environment. The price is that you are **very much constrained by your host language**: every expression in the DSL must be a legal expression in the host. Consequently a great deal of internal-DSL thinking is really thinking about *host language features*. Fowler credits the Ruby community for the recent impetus, notes that most Ruby techniques transfer to other languages "if usually not as elegantly," and names **Lisp as the doyen** of internal DSL thinking *(Ch. 4, opening)*.

The mental shift is the substance:

> "It's this mental shift that is the core difference between an internal DSL and just calling an API." *(Ch. 4, "Fluent and Command-Query APIs")*

And the principle that keeps people from chasing syntax tricks:

> "The point here is that fluency isn't as much about the style of syntax you use as it is about the way you name and factor the methods themselves." *(ibid.)*

Two consequences of the two-styles view. **Command-query separation** (queries return a value and change no observable state; commands change state and return nothing) is a principle Fowler strongly encourages and has "used many decibels disparaging people who don't follow" — yet method chaining in an internal DSL usually breaks it, since each chained call both mutates and returns something to continue on. His resolution is an explicit carve-out, not an excuse: "fluent interfaces follow a different set of rules, so I'm happy to allow it there." Which implies you must always be able to say which style a given type is in. **Naming rules differ by style** for the same reason: command-query names must make sense stand-alone because "They are the labels on the buttons," while fluent names may make no sense in isolation and read properly inside a sentence — "With DSL naming, it's the sentence that comes first; the elements are named to fit in with that context."

### 6.2 The need for a parsing layer

The central architectural principle of internal-DSL implementation, and the internal-DSL form of the seam from §5.2. A fluent interface is a *different kind* of interface from a command-query interface, and mixing both on the same class is confusing. The solution is a layer of **Expression Builders** over regular objects — an object whose *sole* task is to build up a model of normal objects using a fluent interface, "effectively translating fluent sentences into a sequence of command-query API calls" *(Ch. 4, "The Need for a Parsing Layer")*.

The primary reason is separation of concerns, not style. As soon as you introduce a language you must write code that understands that language, and that code often needs to track data relevant only *while* the language is being processed — parsing data — which is not needed once the model is populated. You should not have to understand the DSL to understand how the model operates.

Why call it a parser? Because the parallels hold: the input is a stream of function calls rather than tokens; it is still useful to arrange those calls into a tree; the same parsing structures (symbol tables) apply; and the output is the same Semantic Model.

The payoff of the seam: you can test builders and model independently; you can have **multiple parsers** — mixing internal and external DSLs, or several internal DSLs over one model; and you can evolve builders and model independently, "Important because DSLs, like any software, are hardly ever fixed."

The one argument against: skip the builders when the Semantic Model objects use fluent interfaces themselves, which sometimes makes sense when fluent usage is the main way people interact with the model. In most situations Fowler prefers a command-query interface on the model, because it is more flexible across contexts and because a fluent interface often needs temporary parsing data.

> "In particular, I object to mixing a fluent and a command-query interface on the same objects—that's just too confusing." *(Ch. 4, "The Need for a Parsing Layer")*

### 6.3 Combining functions

"The difference between a command-query interface and a DSL centers around **how functions are combined**." Three combination patterns *(Ch. 4, "Using Functions")*:

- **Method Chaining** — "for many people, the central pattern of a fluent interface." Each call acts on the result of the previous one. Fowler raises the objection himself: in ordinary OO code these are derided as "train wrecks" and usually signal brittleness to interface changes mid-chain. Read fluently, though, chaining composes many calls without intermediate variables, so the code flows.
- **Function Sequence** — a sequence of plain call statements. Laid out well, reads as clearly as chaining. He says "function" rather than "method" deliberately, because it works outside OO.
- **Nested Function** — function calls as the *arguments* of higher-level calls.

The first choosing factor is **scope**. Chaining keeps scope naturally contained: the DSL methods need only exist on the objects in the chain, usually an Expression Builder. Bare functions in a sequence must resolve somehow, and the obvious answer — globals — creates two problems: polluting the global namespace (partly addressable with namespace/static-import features), and, more seriously, **global variables for parsing data**, since any function sequence needs context variables to know where it is in the parse. "you can't get away from global data if you use global functions."

The recommended cure is **Object Scoping**: place the DSL script in a subclass of an Expression Builder so bare calls resolve against methods in the builder superclass. This solves both problems at once — the verbs are localized to the builder class, and being instance methods they connect directly to parsing data on the builder instance. "That's a compelling set of advantages for the cost of placing the DSL script in a builder subclass, so that's my default option." A bonus: if the framework makes the scoping class easy to subclass, users can add their own DSL methods.

**Nested Function** trades differently. It buys three things: hierarchy echoed by the language constructs themselves (rather than merely hinted at by indentation); changed evaluation order, since arguments are evaluated first, so sub-objects arrive fully formed and often eliminate the need for a context variable; and, consequently, it is safer with global functions, because a global that merely returns an object alters no parsing state. It costs four things: punctuation noise from explicit parentheses and commas; the same globalness problems as function sequences (same Object Scoping cure); **backwards reading order** if you think in terms of a sequence of commands, since nested calls evaluate inside-out — Fowler quotes Neal Ford's observation that writing "Old MacDonald Had a Farm" this way renders the chorus as `o(i(e(i(e()))))`; and **positional rather than named arguments**, so `disk(75, 7200)` doesn't say which number is which. The partial fix of wrapping each value in a naming function (`disk(size(75), speed(7200))`) reads better but doesn't stop you writing them in the wrong order; actually preventing that requires returning richer intermediate token objects — "an annoying complication." Which yields a nice reframing:

> "In many ways, Method Chaining is a mechanism that helps you supply keyword arguments to a language that lacks them." *(Ch. 4, "Using Functions")*

You will normally combine patterns, and Fowler works through a hybrid — a top-level function sequence, nested functions for each item's arguments, chaining for optional sub-values — where each part plays to a strength. Then he **rejects his own hybrid**, on a principle that generalizes far beyond DSLs:

> "The punctuational differences are an artifact of the implementation, not the meaning of the DSL itself, so I'm exposing implementation issues to the user—always a suspicious idea." *(Ch. 4, "Using Functions")*

Mixing patterns produces punctuational confusion — some elements separated by commas, others by periods, others by semicolons. A programmer can work it out; a non-programmer merely *reading* the expression is more likely to be confused. His revised choice keeps the uniform shape. "This tradeoff discussion is a microcosm of the decisions you'll need to make when building your own DSL."

### 6.4 Literal collections

A third way to compose, beyond statements and function application *(Ch. 4, "Literal Collections")*:

- **Literal List** — a list of elements, same or different types, no fixed size. In curly-brace languages a varargs call is a common way to introduce one, and a nested function taking a variable set of child calls is already a literal list in disguise. Languages with a general list literal syntax have the advantage that it is usable in more contexts than just inside a call.
- **Literal Map** — especially handy where an element has multiple sub-elements, all optional, each settable at most once. Chaining is good at naming the sub-elements, but you must write your own code to enforce "at most once"; with a map that constraint is baked in and familiar to users of the language.
- **Named parameters** are better still where a language has them (Smalltalk keyword messages express it directly) — but "even fewer languages have named parameters than have Literal Map syntax." If you have them, use them to implement a literal map.
- A **symbol** data type looks like a string but exists primarily for lookups in maps, particularly symbol tables: immutable, usually interned, with a literal form that doesn't support spaces or most string operations because its role is lookup rather than holding text. Use symbols where the language has them, strings where it doesn't.

Fowler also explains Lisp's appeal here: a convenient literal list syntax, the *same* syntax for function calls, and bare words as symbols, so the whole syntax is about representing nested lists of symbols — an excellent basis for an internal DSL, *provided you are happy with your DSL having that fundamental syntax*. That simplicity is both a great strength and a weakness.

### 6.5 Using a grammar to choose constructs

A technique for choosing among the above: write down the *logical grammar* of your DSL, because certain BNF rule shapes suggest certain internal constructs *(Ch. 4, "Using Grammars to Choose Internal Elements")*.

| Grammar structure | BNF form | Consider |
|---|---|---|
| Mandatory list | `parent ::= first second third` | Nested Function |
| Optional list | `parent ::= first maybeSecond? maybeThird?` | Method Chaining, Literal Map |
| Homogeneous bag | `parent ::= child*` | Literal List, Function Sequence |
| Heterogeneous bag | `parent ::= (this \| that \| theOther)*` | Method Chaining |
| Set | doesn't fit BNF | Literal Map |

The reasoning matters as much as the table. Mandatory elements suit nested functions because the arguments match the rule's elements directly — and with static typing, type-aware autocompletion can suggest the correct items per argument position, which is a *tooling* argument for the choice. Optional elements suit chaining because nested functions produce a combinatorial explosion of overloads, and because the method name itself indicates which element you're supplying; the tricky part is enforcing one use of each. Repeated homogeneous children suit a literal list — and if the expression defines the top-level statements of your language, "that is one of the few places I'd consider *Function Sequence*." Repeated heterogeneous children suit chaining, since the method name signals which element you're looking at. A **set** (multiple children, each at most once, any order) is common and fits BNF badly; a literal map is the logical choice, and the problem you will hit is "the inability to communicate and enforce the correct key names." At-least-once rules don't map well onto any internal construct; the best bet is a general multiple-element form plus a check for at least one call during the parse.

Note that each choice leaves a specific enforcement gap you must close in code: uniqueness for chained optionals, key-name validity for maps, at-least-once for repeats.

### 6.6 Closures

Closures let you take inline code, package it as an object, pass it around, and evaluate it when it suits you. In internal DSLs they appear as **Nested Closure**, which has three properties worth separating *(Ch. 4, "Closures")*:

1. **Inline nesting.** Like a nested function, it captures the DSL's hierarchic structure in a way meaningful to the host language. The additional advantage is that you can put **any inline code** into the nesting — most languages restrict what can appear in function arguments, so you can nest structures (a function sequence inside a closure) that would be impossible inside a nested function.
2. **Deferred evaluation** — "perhaps the most important capability that Nested Closure adds." You get complete control over when closures run: reorder them, skip some, or store them all for later. This is particularly valuable when the Semantic Model takes strong control of execution (an **Adaptive Model**), because the DSL can then include **sections of host code inside the DSL** and put those blocks into the model, intermixing DSL and host code freely.
3. **Limited-scope variables.** A closure can introduce variables scoped to itself, making it clearer what the DSL verbs act on — and removing the need for global functions or Object Scoping entirely, since the verbs are defined on the scoped variables, which are themselves Expression Builders.

The worked validation example is instructive about *why* deferred evaluation matters: a closure containing arbitrary host code is stored in the Semantic Model and executed as the model runs. Fowler frames validation as inherently **contextual** — you validate an object *in order to do something to it*, e.g. different rules for eligibility under one policy versus another — which is precisely why a hard-coded "is this object valid" is insufficient.

The honest caveat: Nested Closure is very useful but "often frustratingly awkward." Where a language lacks closures, the substitutes (function pointers, command objects) "require a lot of unwieldy syntax that can add a debilitating amount of noise to a DSL." Even among languages that have them, syntax quality varies enough to change which techniques are practical. Noise in the host closure syntax is a first-order design cost, not a cosmetic one.

### 6.7 The remaining techniques, in brief

Each is covered in depth in Part 2; what matters here is the judgement attached to each.

- **Parse Tree Manipulation** — treat a host-language expression's parse tree as data rather than evaluating it, so you can walk it and emit something else (a query in another language). Its strength is converting host expressions into *different* expressions rather than merely storing and running them. Fowler's assessment: "a marginal technique — rarely needed, but very handy on the occasions that need arises." The design test is whether you need to *retarget* the user's expression to a different execution engine; if you only need to *run* it, a plain closure is far simpler *(Ch. 4, "Parse Tree Manipulation")*.
- **Annotation** — attach metadata to program constructs, readable at compile time or runtime. The worked example (declaring a valid range on a field, rather than range-checking in a setter) yields three advantages: it reads more clearly as a property of the field; it decouples *declaring* the rule from *when* it is enforced; and it "specifies the validation rule in a form that could be read to configure a GUI widget" — the rule becomes reusable metadata rather than behavior. Think of annotations as a way of extending the language with new keywords. Because they are so closely bound to the host language, they suit **fragmentary DSLs, not stand-alone ones** *(Ch. 4, "Annotation")*.
- **Literal Extension** — adding methods to library classes so a chain can begin on a literal. Availability is language-dependent. The danger is that it **adds methods globally** when they should be scoped to DSL usage, compounded in some languages by there being no easy way to discover where an extension was added; the safer design is the one that requires an explicit namespace import. "One of those things that you don't need to use terribly often, but can be very handy when you do" *(Ch. 4, "Literal Extension")*.
- **Reducing syntactic noise.** Two mitigations. **Textual Polishing** — write chunks in a syntax very close to but not exactly the host language and text-substitute — which Fowler is "not a big fan" of: "The substitutions get convoluted pretty quickly, and when they do it's much easier to use a full external DSL." The technique has an unstable middle ground. And **syntax coloring** — when communicating with domain experts, use an editor scheme that de-emphasizes noisy syntax, even coloring it into the background. A tooling answer rather than a language answer *(Ch. 4, "Reducing the Syntactic Noise")*.
- **Dynamic Reception** — intercepting calls to undefined methods, which lets you move information from arguments into method names (a finder per field name, generated on demand). The crux is readability; the danger is that "it can only take you so much. You don't want to be encoding complicated structures into a sequence of method names. If you need anything more complicated than a single list of things, use something with more structure." And a sharp rule: it works best when you do the **same basic processing for each call**; if you'd handle different names differently, write explicit methods instead *(Ch. 4, "Dynamic Reception")*.
- **Type checking and Class Symbol Table.** Fowler declines to re-fight static-versus-dynamic typing and instead raises the **tooling** argument: excellent IDE support depends on static types. Most DSL symbols don't get that support because they're strings or symbols in your own table — so you write quoted names by hand and get no autocompletion for, say, valid target states. What he'd rather have is bare identifiers, which read better, avoid wrapper methods and quotes, and give **type-aware autocompletion**. The technique is a **Class Symbol Table**: define each symbol type as a class, and declare the specific symbols of a script as fields. The honest cost is aesthetic: "The result, like many DSL constructs, looks rather strange. I would never normally advocate a plural name for a class such as used here... But it does result in an editing experience that meshes much more closely with the general experience of Java programming" *(Ch. 4, "Providing Some Type Checking")*.

> **SDK lens:** Build your library in two layers — a plain, orthogonal, side-effect-disciplined core (the model, with command-query naming judged one method at a time in an autocomplete list) plus a physically separate ergonomic/builder surface (judged by reading whole call chains aloud). Never put both styles on the same class. Choose your call shape from the *shape of what the caller must supply*: mandatory arguments → positional/nested calls; optional ones → builder methods or an options map; repeated homogeneous ones → lists; sets → maps or named parameters — and close the enforcement gap each choice leaves. Keep the call shape uniform across the surface even at some cost in local elegance, because punctuation variety leaks your implementation structure to the reader. Callbacks buy you three separable things (nesting, deferred execution, scoped handles), and deferred execution is what lets user code be *stored as data* in your model — the basis of rule engines and configuration-as-code. And remember that strings are the enemy of tooling: turning stringly-typed identifiers into declared, typed symbols buys autocompletion, refactoring, and compile-time checking, and Fowler's precedent says a little aesthetic oddity is a fair price.

---

## 7. External DSL techniques overview and the internal-vs-external decision

### 7.1 Framing, and a warning about the literature

External DSLs give you **greater syntactic freedom — the ability to use any syntax you like** — because parsing operates on pure text, unconstrained by a host language. The techniques are those the programming language community has refined for decades *(Ch. 5, opening)*.

The orientation warning recurs through the chapter and is worth internalizing before you read any parser documentation: the tools and writings of that community almost always assume a **general-purpose** language; DSLs "are lucky to get a mention in passing." Many principles carry over, but not all — and "you don't need to understand as much to work with DSLs." You do not have to climb the whole learning curve built for general-purpose language implementation.

### 7.2 Syntactic analysis strategy

**Syntactic analysis** means taking the stream of text and breaking it into a structure you can use — for instance, recognizing that a line is an event definition rather than a command definition *(Ch. 5, "Syntactic Analysis Strategy")*.

**Delimiter-Directed Translation** picks delimiter characters (usually line endings), chops the input into statements, and feeds each chunk to a processing step, usually keyed off a leading keyword. Pro: very simple, using tools most programmers already know — string splitting and regular expressions. The decisive con: "it doesn't give you any inherent way to handle the **hierarchic context** of your input." As soon as the language nests, a line no longer carries enough information alone; you can manage the context yourself, but "the more hierarchic context you get, the more effort you have to spend managing it yourself."

**Syntax-Directed Translation** starts from a formal **grammar** written in some form of BNF, each **production rule** naming a term and its legal elements. A grammar is a good way to think about a language's syntax *whether or not* you use SDT — it helps for internal DSLs too (§6.5) — but it works particularly well here because it translates fairly mechanically into a parser, and the resulting parsers handle hierarchic structure capably.

Three routes from a grammar to a parser, with their tradeoffs:

| Approach | Strengths | Weaknesses |
|---|---|---|
| **Parser Generator** (grammar as input, parser as output) | Most sophisticated; mature tools; handle complex languages efficiently. BNF-as-DSL makes the language easy to understand and maintain, since its syntax is clearly defined and **automatically tied to the parser**. | Take time to learn; mostly use code generation, so they **complicate the build**; may not exist for your platform. |
| **Recursive Descent Parser** (each rule becomes a function) | Easy to understand; clear patterns for turning each BNF operator into control flow; "powerful and efficient enough for a DSL." | **The grammar gets lost in the control flow**, making the code far less explicit than Fowler would like. |
| **Parser Combinator** (each rule becomes an object; compose them) | Fowler's preference when a generator isn't available or feels too heavyweight. Same algorithm as recursive descent but **represents the grammar explicitly in the composing code** — can get close to true BNF. | Composition code isn't quite as clear as real BNF. |

Overall: with any of the three, SDT makes structured languages much easier than delimiter-directed translation. "The biggest downside of Syntax-Directed Translation is that it's a technique that isn't as widely known as it should be." People fear it is hard, and Fowler argues the fear "often comes from the fact that Syntax-Directed Translation is usually described in the context of parsing a general-purpose language—which introduces a lot of complexities that you don't face with a DSL." The book mostly uses a mature, widely available parser generator, partly because it is itself a sophisticated recursive-descent implementation and therefore meshes with the understanding you get from the hand-written approaches.

### 7.3 Output production strategy

You must know what your output is. Fowler's stance: most of the time it should be a **Semantic Model**, which you then interpret or feed to a generator. He warns explicitly that within the language community, parsers are usually constructed to **directly produce output code with no Semantic Model in sight** — reasonable for general-purpose languages, not what he suggests for DSLs — and that you should bear this difference in mind when reading their material, "which includes most documentation for tools such as Parser Generators" *(Ch. 5, "Output Production Strategy")*.

Three strategies:

1. **Embedded Translation** (single-step) — place calls directly in the parser to create the Semantic Model *during* parsing, building it up as you go, with intermediate parsing data usually held in symbol tables.
2. **Tree Construction** (two-step) — parse into a **syntax tree** capturing the essential structure, plus a symbol table for cross-references between branches; then run a second phase that walks the tree and populates the model.
3. **Embedded Interpretation** — run the interpretation during the parse, with the output *being* the final result (a calculator that yields the answer). **Produces no Semantic Model.** A rare case.

The analogy: Embedded Translation is like SAX; Tree Construction is like DOM. You can do either without a Semantic Model — common when generating code, and what most parser generator examples show — but Fowler recommends it only rarely: "Usually I find the Semantic Model overwhelmingly helpful."

The real choice is between the first two, and it comes down to whether the intermediate syntax tree pays for itself. For it: it splits the parsing problem into two simpler tasks, which matters more as translation complexity grows; while recognizing text you can focus only on building the tree; walking the tree afterwards is "a more regular programming exercise," and **you have the whole tree available to examine**, whereas embedded translation only ever sees what has been parsed so far. Against it: the usual memory objection, which Fowler dismisses — it "withers away when processing small DSLs on modern hardware" — and his actual reservation, that you must write code to build the tree *and* code to walk it, and often it is easier to just build the model there and then.

His verdict is unusually undecided, and worth preserving as such: "So, I'm conflicted on the choice. Other than the vague notion that increasing complexity of translation favors Tree Construction, I have mixed feelings. My best advice is to try a little of both and see which you prefer." The usable heuristic underneath is a *distance* heuristic: the greater the distance between the DSL and the Semantic Model, the more the intermediate tree earns its keep.

### 7.4 Parsing concepts you actually need

Fowler covers the concepts "albeit not to the extent that traditional compiler books assume, since we're dealing with DSLs rather than general-purpose languages" *(Ch. 5, "Parsing Concepts")*. The parts that change design decisions:

- **Separated lexing.** SDT usually splits into *lexing* (text → stream of tokens, each with a type and content) and *syntactic analysis* (tokens → syntax tree). A **Regex Table Lexer** — a list of regex-to-token rules — is the easy way to write the first. Two consequences bite. Because the lexer runs first, a keyword is a keyword everywhere: naming a state "initial state" collides with the `state` keyword unless you use some scheme of **Alternative Tokenization**. And whitespace is generally discarded before the parser sees anything, which makes **syntactic whitespace** (newline separators, Python-style indentation) difficult: it "intermixes the syntactic structure of the language with formatting," which mostly makes sense — our eye uses formatting to infer structure — but "there's just enough edge cases where the two needs don't quite line up, which introduces a lot of complications. This is why many language people really hate syntactic whitespace." Why separate them at all? It decomposes a complicated task into two simpler ones, and it is faster.
- **A grammar, not the grammar.** The same point as §5.5, restated with teeth: two different grammars can recognize the same language while producing **different parse trees, and therefore different output-generation code**. Grammars vary by tool, and by how you factor rules. "Just like with any code, you refactor your grammars to make them easier to understand." A further factor that shapes factoring is the output code itself: "I often end up altering my grammar to make it easier to organize the code that translates source into the semantic model." **The grammar is code, not a pristine spec.**
- **The Chomsky hierarchy, for its practical payoff only.** Regular grammars are finite-state machines — hence regular expressions — and their fatal limitation is that they **can't handle nesting** ("regular grammars can't count"), which rules out ordinary block structure. Context-free grammars add hierarchic context via a push-down machine (a state machine with a stack); most language parsers, most generators, and both recursive-descent and combinator parsers land here. Their limitation is the classic declare-before-use rule, where the declaration sits outside the branch you're in — **which is exactly why symbol tables exist**. Context-sensitive grammars could handle it, "but we don't know how to write general context-sensitive parsers." The payoff of knowing this is threefold: it tells you which tool class you need (nesting ⇒ context-free ⇒ prefer SDT over delimiter-directed); it says you *could* use something weaker for a regular language, though in practice a push-down machine is straightforward enough that it "usually isn't overkill"; and it explains why lexing is separated at all. **PEGs** are a newer form handling most context-free and some context-sensitive situations, typically without separated lexing.
- **Top-down (LL) vs bottom-up (LR).** A top-down parser starts from the highest-level rule and "uses the rules as **goals** to direct what to look for." A bottom-up parser reads tokens, shifting them aside until enough match a rule, then reducing — hence shift-reduce parsing. Bottom-up parsers are generally considered harder to understand; you don't have to write the parser if you use a generator, "but you do have to understand roughly how it works in order to debug problems." The main practical wart of top-down parsing is **left recursion**, which sends the parser into endless recursion; the mechanical fix (left-factoring) yields a grammar that isn't as easy to follow, but you only really hit it with nested operator expressions, and once you know the idiom you can produce it fairly mechanically.

A general point that closes the section, and echoes §5.5:

> "Perhaps the most important point is to realize that you shouldn't treat the grammar as a fixed definition of the DSL. Often, you'll need to alter the grammar to make the output production work better. Like any other code, the grammar will change depending on what you want to do with it." *(Ch. 5, "Parsing Concepts")*

### 7.5 The escape hatch: mixing in another language

"One of the biggest dangers that you face with an external DSL is that it may accidentally evolve to become a general-purpose language." Even short of that, a DSL easily becomes overly complex if you have a long tail of special cases that each need particular treatment but are rarely used *(Ch. 5, "Mixing-in Another Language")*.

The technique is **Foreign Code**: for the rare cases, embed a small piece of a general-purpose language into the DSL. Crucially, "This code isn't parsed by the DSL's parser; rather, it is just slurped as a string and put into the *Semantic Model* for later processing." The tradeoff, stated plainly: "This isn't as clear as extending the DSL would be, but this mechanism can handle a wide range of cases. **Should regex matching become a common condition, we can always extend the language later.**" That is the whole pattern in one sentence — an escape hatch for the long tail, promoted into first-class syntax once it stops being rare.

Implementation notes: a dynamic host language makes this easy because you can interpret the embedded code at runtime; with a static language you must use code generation and weave the host code into the generated output (which is how most parser generators work anyway). You must **tokenize the foreign code differently** from your main language, so you need some form of Alternative Tokenization — the simplest being clear delimiters the tokenizer can spot and slurp as a single string, easy to implement but adding some noise. And the same technique works for embedding *another DSL* rather than host code, which fits the philosophy of several small DSLs rather than one large one — though composing external DSLs is genuinely hard, because current parser technologies are not well suited to modular grammars.

### 7.6 XML as a carrier syntax — the argument, in full

Fowler thinks of XML as a **carrier syntax** for a DSL, "in much the same way that an internal DSL's host language provides a carrier syntax. (An internal DSL also provides **carrier semantics**.)" — XML gives you syntax only; a host language gives you syntax *and* an execution model. XML isn't a programming language; it is a syntactic structure with no semantics, which is why DOM processing is essentially Tree Construction and SAX processing leads to Embedded Translation *(Ch. 5, "XML DSLs")*.

His objection is noise: angle brackets, quotes, slashes, and paired tags for every nesting element mean too many characters are spent on syntactic structure rather than content, "making it much harder to understand what the code is trying to say — which spoils the whole purpose of DSLs."

He then states the arguments in XML's favor and answers each:

1. *"Humans shouldn't write XML — a UI captures the information and XML is just a serialization."* Reasonable, but it takes you out of DSL territory, with XML becoming a serialization mechanism and the forms-based UI becoming an *alternative to* a DSL. He notes he's seen "much talk of having a UI over XML, but not so much action," and that if you spend significant time looking at the XML or its diffs, the UI is incidental.
2. *"XML parsers exist off the shelf."* He thinks this argument is flawed, "stemming from a confusion about what parsing is." He defines parsing as **the whole route from input text to the Semantic Model**. An XML parser takes you only to a DOM; you still write the code that traverses it — and a parser generator can produce a syntax tree too. His experience is that once you are moderately familiar with a parser generator it takes no longer than XML tooling, and the learning cost "is a price worth paying."
3. *Consistency of quoting and escaping.* A genuine point: custom external DSLs breed inconsistency here, and XML provides a single scheme that works solidly.
4. *Error handling and diagnostics.* XML processors usually do a good job; you will work harder for good diagnostics with a custom language.
5. *Schemas.* You can validate structure without executing, and support more intelligent tools.
6. *Binding interfaces.* Less useful for DSLs, "because the structure of the Semantic Model will rarely match that of the DSL to allow binding XML elements to the Semantic Model."
7. *Grammar vs schema.* A parser generator's grammar can define many of the checks a schema provides, but few tools can take advantage of a grammar, whereas schema tools already exist. Which yields a generalizable observation: "**Often, an inferior but prevalent approach ends up being more useful than superior technologies.**"

He concedes the points and holds the verdict:

> "The key to a DSL is readability; tooling helps with writing, but it's the reading that really counts." *(Ch. 5, "XML DSLs")*

On **JSON and YAML**: other carrier syntaxes with much less noise than XML, which he likes more. However, "these languages are very much oriented towards structuring data, and as a result lack the flexibility you need to have a truly fluent language." Which produces the parallel that ties the whole book together:

> "A DSL is different from a data serialization, just like a fluent API is different from a command-query API. Fluency is important for a DSL to be easily readable, and a data serialization format makes too many compromises to work well in that context." *(Ch. 5, "XML DSLs")*

That is: **data serialization : DSL :: command-query API : fluent API.**

### 7.7 Choosing between internal and external — ten headings, no verdict

Chapter 6 exists to make this decision, and opens with an unusually candid epistemic caveat: "One of the great difficulties is the lack of information to base your choice on." Few people do much with DSLs, and those who do tend to use one or two techniques, so they can't compare. "So, my thoughts on this topic are more speculative than I would like" *(Ch. 6, "Choosing between Internal and External DSLs")*.

**1. Learning curve.** At first glance this favors internal DSLs — an internal DSL "is really just a funky kind of API," using a language you already know, whereas external DSLs mean parsers and grammars. But the picture is more nuanced. SDT does introduce genuinely new concepts, and driving parsers with grammars can look like magic; "It's not as bad as many people fear," but if you haven't used these tools, work through trial examples before you estimate real work. The curve is made worse by documentation written for people building general-purpose languages — "For many tools, the only documentation is a Ph.D. thesis. There's a crying need to do more to make Parser Generator tools accessible to those who want to use them for DSL work." Two escape routes exist: delimiter-directed translation (familiar tools, real limits — "most of the time I think it's better to face the learning curve," but keep it in mind particularly for a regular language), and an XML carrier syntax (where he thinks learning SDT is worth the cost, "as the resulting language is so much clearer to read"). The counterweight is that internal DSLs are not as easy as you'd think: you are using a familiar language in a very odd way, often relying on obscure host-language tricks you must go find. The structural difference is *when* you pay: with an internal DSL you can **mount the curve slowly**, learning techniques as you go, whereas SDT requires learning much more just to get going. **Conclusion: internal DSLs are easier to learn** — and remember the curve "applies not just to you but to anyone who wants to touch your code."

**2. Cost of building.** The first time, the major cost is the learning curve, and it goes away. Then comes a critical accounting separation: "it's important to separate the cost of **building the model** from the cost of building the **DSL that layers over it**... the model has its own justification." The internal DSL's extra cost is the Expression Builder layer, where "most of the effort isn't in getting them to work — it's in fiddling with the language so that you have something that works well." (You can avoid that cost by putting fluent methods directly in the model, "but that may lead to other costs if people find these methods confusing compared to a command-query API.") The external equivalent is building the parser, which once you're fluent in SDT is "actually quite quick." **Conclusion: "once you are familiar with the techniques, there's no big difference in cost for building an internal or external DSL."**

**3. Programmer familiarity.** The usual argument is true "to some extent," but less marked than people think: the fluent style takes getting used to, and an external DSL is by definition simple. Echoing the syntactic conventions of the team's usual language makes an external DSL more approachable. **The biggest difference is tooling, not syntax.** An internal DSL inherits the host IDE — you may need a more elaborate technique like a Class Symbol Table specifically to *preserve* that support. With an external DSL "you're unlikely to be offered anything but the most basic level of editing support"; syntax highlighting is easy, "but type-aware autocompletion is almost certainly beyond you."

**4. Communication with domain experts.** Internal DSLs are permanently tied to host syntax, so there is always some constraint and some noise. Programmers barely notice; domain experts do. "Even the best internal DSLs... don't offer the same syntactic flexibility as an external DSL. The size of the comfort gap will depend on particular domain experts, but such is the value of the communication channel that **I'd be inclined to push that bit harder and use an external DSL if it looks like it could make the difference.**" The hedging strategy: if you're not comfortable building an external DSL, start internal and switch later — "Since you can use the same Semantic Model for both, the incremental cost of building two DSLs isn't really that great."

**5. Mixing in the host language.** "An internal DSL is really nothing more than a convention to use certain fluent methods... There's nothing to stop you from arbitrarily mixing DSLish code with regular imperative code." That **wafer-thin boundary** is a benefit here: use the host language when the DSL lacks a construct, use the host's abstraction facilities to build abstractions *on top of* the DSL, and drop chunks of imperative code inside DSL scripts. The build-language case study is the illustration: Make and Ant are external DSLs that express a Dependency Network very well, but the *content* of build tasks needs complex logic and the dependencies themselves need layered abstractions, so Ant "suffered from **sliding into generality**, acquiring all manner of imperative constructs that don't suit its nature or syntax." Rake, an internal DSL, mixes the dependency network with imperative code in nested closures and uses the host's objects and methods to build higher-level structure. Mixing with an external DSL is possible (Foreign Code inward, strings outward — "which is how we typically embed things like regular expressions and SQL today") but awkward: "tools usually don't know what you are doing," and "it's hard to integrate symbols between the two environments." **"If you want to intermix host and DSL code, then an internal DSL is almost always the way to go."**

**6. Strong expressiveness boundary.** The mirror image, and the case *for* external DSLs. Free mixing "only really works if the users of the DSL are comfortable with the host language"; where domain experts read your DSL, "throwing lumps of a host language into the DSL will usually only raise a communication barrier that the DSL was supposed to avoid." Intermixing is also unhelpful where a different group of programmers writes the scripts. "Indeed, often the benefit of a DSL is that **it produces a restricted range of what can be done.**" That restriction makes it easier to understand what to do, **serves as a barrier to bugs**, and **limits the kinds of things you need to test for** — "Pricing rules in a DSL aren't going to send arbitrary messages to your integration server or alter your order processing workflow." With a general-purpose language anything is possible, "so you have to watch the boundaries through convention and review. An external DSL's limitations reduce what you have to watch for. Most of the time, this is good as it protects you from mistakes, **but it may also help with security.**"

**7. Runtime configuration.** Why XML DSLs became popular: "they allow you to alter the execution context of the code from **compile time to runtime**," which matters when you use a compiled language and want to change behavior without recompiling. External DSLs support this naturally — parse at runtime, translate into a model, execute. The alternative of using an interpreted language alongside a compiled one and writing an internal DSL there **attenuates most internal-DSL advantages**: unless the team knows the dynamic language you lose the familiarity benefit; tooling is often poorer; you can't easily mix dynamic and static constructs; and a full dynamic language means you can't put firm boundaries around the DSL, losing the previous factor's benefit. "But this attenuation does lead to more situations where an external DSL meshes better with a static host language."

**8. Sliding into generality.** The canonical failure mode of external DSLs. In a discussion about DSLs, Ant's creator James Duncan Davidson asked: **"How do we prevent disasters like Ant occurring?"** Ant is "both a roaring success and a nightmare"; its XML syntax is the most noticeable flaw, "But the real issue behind Ant is that over time it steadily grew in capability so that it no longer has the limited expressiveness that a DSL needs." This is a general road: "This is a common road to heck," with Sendmail as the Unix equivalent. "It happens because the demands placed on the DSL get steadily greater, leading to more features and greater complexity—and, drop by drop, all the clarity that a good DSL has leaks out." There is **no simple answer**: "It needs a constant attention and determination to not let things get too complex." Three alternatives to growing one language: (a) let *other* languages develop for the complicated cases; (b) **layer another language over the base DSL whose output is that base DSL** — "a useful technique to allow abstractions to be built in a language that lacks abstraction-building features"; (c) switch to an internal DSL, which is "often a good choice when this kind of complexity grows, because they allow you to mix DSL and general-purpose elements." Internal DSLs don't suffer this problem, being already melded with a general-purpose language — but they have the symmetric failure: "mixing with the host language gets so intertwined that you lose any sense of DSLness." External DSLs bloat; internal DSLs dissolve.

**9. Composing DSLs.** Since you want small, limited DSLs, real work means composing them with general-purpose languages *and with each other*. Internally, "composing is as easy as mixing them with the host language. You can also use the host language's abstraction features to help make the composition work." Externally it is much harder: SDT would require writing independent grammars and composing them, and most parser generators have no facility for this — "another consequence of their focus on supporting general-purpose programming languages" — so you fall back to Foreign Code, "which is more clunky than it need be."

**10. Summing up — the non-conclusion.**

> "My conclusion is that there is no conclusion. I don't see a clear, general advantage for internal or external DSLs. I'm not even sure I see some general guidelines to pontificate." *(Ch. 6, "Summing Up")*

The one thing he does stress is that **experimenting in both directions need not be as expensive as you think**: "If you use a *Semantic Model*, it's relatively easy to layer on multiple DSLs, both internal and external. This gives you lots of opportunity for experimentation to find an approach that works well for you." He endorses Glenn Vanderburg's approach: use an **internal DSL early on, while you're still trying to understand what you want to do with it** — easy access to host facilities, a more seamless environment to evolve in — and once things settle and you need external-DSL advantages, build one. "Again, a Semantic Model makes this process much easier." A third option, the language workbench, is deferred to Ch. 9 (§8.8 below).

> **SDK lens:** Read the ten factors as a checklist for any "should this be code or configuration?" decision. The two that most often decide it in practice are **tooling** and **boundary strength**. A surface expressed in the host language inherits the entire IDE — completion, refactoring, jump-to-definition, type errors — and that inheritance is frequently worth more than syntactic elegance. A surface expressed in a separate restricted format bounds the failure surface, the test matrix, the review burden, and the attack surface, which is the real argument for declarative/sandboxed extension points over "just let them write code" plugin APIs — and it tells you exactly when the argument applies: untrusted or non-programmer authors, or cross-team authorship. For the long tail of rare requirements, provide a general-purpose escape hatch rather than growing dozens of narrow declarative options, and promote a case into first-class API only once demand is proven. And note the criterion Fowler uses to reject XML as a DSL carrier: *reading*, not writing and not tooling convenience — the same criterion that separates a config schema from a genuine configuration language.

---

## 8. Code generation strategy, language workbenches, and lessons from real DSLs

### 8.1 Why generate at all, and the two-environment framing

The default remains: parse the DSL, populate the Semantic Model, execute the model directly. Code generation is the fallback for when you *can't* — when the DSL-specified logic must run in an environment where building a parser or model is difficult or impossible. "By using code generation, you can take the behavior specified in the DSL and run it in almost any environment" *(Ch. 8, opening)*.

Generation means you have **two distinct environments** to think about: the **DSL processor environment**, where the parser, model, and generator live and which needs to be *comfortable* for developing them; and the **target environment**, where the generated code runs.

> "The point of using code generation is to separate the target environment from your DSL processor because you can't reasonably build the DSL processor in the target environment." *(Ch. 8)*

Four reasons the target can force your hand *(Ch. 8, opening)*:

1. **Resource-constrained targets** that cannot run a DSL processor.
2. **The target is itself a DSL.** Because DSLs have limited expressiveness, they usually lack the abstraction facilities a complex system needs; extending the DSL to add them risks sliding into generality. Better to do the abstraction elsewhere and generate the target DSL. The canonical case: specify query conditions in a DSL and **generate SQL**, because you want the query to run efficiently in the database but SQL is not the best way for you to represent queries.
3. **Lack of familiarity with the target environment** — easier to specify behavior in a language you know.
4. **To enforce static checking.** Characterize a system's interface in a DSL, generate a typed API in the caller's language so callers get compile-time checking and IDE support, and when the interface changes, regenerate and **let the compiler point at the damage**.

### 8.2 Choosing what to generate: model-aware vs model-ignorant

The two styles are distinguished by whether an explicit representation of the Semantic Model exists in the target *(Ch. 8, "Choosing What to Generate")*:

- **Model Ignorant Generation** embeds the model's logic into the target language's **control flow** — for a state machine, nested conditionals switching on current state and then event. No explicit model exists in the generated code.
- **Model-Aware Generation** puts some representation of the model into the generated code. It needn't match the processor's model; any data representation will do (nested maps from state to event to target state). It may be a crude model with no explicit classes, but **the data structure captures the behavior**.

The key structural insight: by putting a model representation into the generated code, **the generated code takes on the same split between generic framework code and specific configuration code** that §2.3 identified in the source system. Model-aware generation preserves that separation; model-ignorant generation folds it together.

Consequences follow directly. With model-aware generation, **the only thing you need to generate is the specific configuration**; the generic machinery can be built and tested by hand, entirely in the target environment. With model-ignorant generation you must generate much more, and most of the critical behavior has to be generated. Therefore model-aware generation is much easier: the generated code is usually very simple, and the generic portion is independently runnable and testable outside the generation system. "**My inclination, therefore, is to use Model-Aware Generation as much as possible.**"

The exceptions are real. Often the entire reason for generating is that the target language *can't* represent a model as data easily; and even when it can, processing limitations may forbid it — embedded systems commonly use model-ignorant generation because model-aware runtime overhead would be too great. There is also a deployment bonus for the model-aware style: because behavior lives in configuration, you can **replace only the configuration artifact** to change behavior, given some runtime binding mechanism.

Pushed further, you can generate a **data file read entirely at runtime** rather than configuration code, which lets you change behavior at runtime at the cost of load code at startup. Whether that file is "just another DSL" is answered by the authoring-vs-interchange test quoted in §1.6: it isn't designed for human manipulation, it is designed to be trivially parseable, and "human readability comes a distant second to simplicity of parsing. With a DSL, human readability is a high priority."

### 8.3 How to generate: transformer vs templated, and the Embedment Helper

Two styles of producing textual output *(Ch. 8, "How to Generate")*:

- **Transformer Generation** — write code that reads the Semantic Model and emits statements in the target. Driven by input, output, or both.
- **Templated Generation** — begin by writing a sample output file, then place template markers wherever something is model-specific, calling out to the model to generate that piece. Driven by the structure of your output.

Both work; experiment. **Templated generation works best when there's a lot of static code in the output and only a few dynamic bits** — "particularly since I can look at the template file and get a good sense of what gets generated" — so you are more likely to use it with model-ignorant generation. Otherwise, "actually, most of the time," Fowler prefers transformer generation. They mix in practice (transformer code typically uses string formatting for small chunks, which is miniature templating), and his caveat is about *consciousness* of the choice rather than purity:

> "The moment you stop being thoughtful about what you are doing is the moment when you start making an unmaintainable mess." *(Ch. 8, "How to Generate")*

The biggest problem with templated generation is that the host code needed to generate variable output starts to **overwhelm the static template**. If you are generating C from Java, you want the template to be mostly C with minimal Java. **Embedment Helper** is the fix, and Fowler calls it a *vital* pattern: hide all the complexity of generating variable elements in a class called by simple method calls in the template. The rule is stated explicitly: **each callout in a template should be a single method call; anything else belongs inside the helper.**

The benefit beyond readability is tooling. The helper is a regular class edited with tools that understand the host language; host code embedded in a foreign-extension file gets no IDE help, often not even syntax highlighting. Fowler notes the same problem in a different context: SDT grammar files "full of long code actions, essentially blocks of Foreign Code," whose size **buries the structure of the grammar**. An embedment helper keeps the actions small and the grammar readable.

### 8.4 Mixing generated and handwritten code

Two general rules *(Ch. 8, "Mixing Generated and Handwritten Code")*:

1. **Don't modify generated code.**
2. **Keep generated code clearly separate from handwritten code.**

The reasoning behind the first is an authority argument: the point of generating from a DSL is that **the DSL becomes the authoritative source** for that behavior, and generated code is "just an artifact." Hand-editing means losing edits on regeneration — extra work every time, and worse, it "introduces a reluctance to change the DSL and regenerate," which undermines the whole point. The acknowledged exception is inserting trace statements while debugging; generating a scaffold to start handwritten code is sometimes useful but "that's not the usual situation with DSLs."

For the second, Fowler's preference is that **files are either all-generated or all-handwritten**. He does not check generated code into the source repository, since it can be regenerated during the build, preferring it in a separate branch of the source tree. Procedural systems make this easy; object-oriented code complicates it, since one logical class often needs both. Three options for splitting a class:

- **Multiple files per class**, easiest when the language supports it (partial classes).
- **Marked regions within a file**, which he is dismissive of: a clunky mechanism that leads to mistakes as people edit generated code, and it **forces you to check generated code into version control, which confuses the version history**.
- **Generation Gap** — the good solution: split the two **using inheritance**, generating a superclass and handwriting a subclass that augments and overrides. This keeps file-level separation while allowing flexible combination in a single class. The disadvantage is that you must **relax visibility rules** so subclasses can override and call otherwise-private methods — "a small price to pay."

And a heuristic that tells you when you have made the problem harder than it needs to be:

> "The difficulty of keeping the generated and handwritten code separate seems to be proportional to the pattern of calls between generated and handwritten code." *(Ch. 8, "Mixing Generated and Handwritten Code")*

A **simple one-way flow of control** makes separation much easier. If you're struggling to keep the two apart, simplify the control flow between them.

### 8.5 Generating readable code

Should generated code be as clear as handwritten code, given that nobody should modify it? Fowler leans toward yes: even though you shouldn't hand-edit it, **people will need to understand how it works** when things go wrong, and clear, well-structured code is much easier to debug. His target is code "almost as good as that I would write by hand" — clear names, good structure, most of his usual habits *(Ch. 8, "Generating Readable Code")*.

The exceptions are precisely stated, and the reasoning behind them is the useful part:

- He is less inclined to spend time working out the *best* structure for generated code.
- On duplication: he doesn't want obvious, easily-avoided duplication, but he doesn't agonize about it — "After all, I don't have to worry about modifiability, only the readability." If some duplication is clearer, it stays.
- He is *happier* to use comments in generated code than in handwritten code, because **generated comments are guaranteed to stay up to date** — and they can **refer back to structures in the Semantic Model**, linking output to its source of truth.
- He'll compromise structure for performance, noting that's true of handwritten code too.

### 8.6 Preparse code generation

A less obvious use: generation not as *output* of a DSL script but as *input support for writing* one. If writing scripts requires symbols that must match those in an external system (salespeople in a corporate database, say), you can generate the information you need while writing your scripts. Such checking can often be done when populating the Semantic Model, "but sometimes it's useful to have the information in source code too, particularly for code navigation and static typing" — for instance, code-generating typed constants for those symbols and importing them into script files *(Ch. 8, "Preparse Code Generation")*. The payoff is IDE navigation and compile-time validity, not runtime behavior.

### 8.7 Language workbenches: what they are and what they change

**Definition:** tools that help you build your own DSLs and provide tool support for them in the style of modern IDEs. They don't merely provide an IDE for *creating* DSLs; **they support building IDEs for editing those DSLs**, so a script author gets the same class of support a programmer gets *(Ch. 9, opening; Ch. 1, "Using Language Workbenches")*.

Fowler's caveats are heavy and should be preserved: he wrote in early 2010, when most tools "have barely left beta stage," and he states plainly that much of what he writes will be out of date on publication. Because the area was so volatile he confined it to one chapter and provided **no patterns** for it, covering only what he believed was relatively stable — describing his method as looking for core principles that don't change much. His assessment: "immense potential here — these are tools that could change the face of programming as we know it," but unproven.

Workbenches let you define three aspects of a DSL environment *(Ch. 9, "Elements of Language Workbenches")*:

1. **Semantic Model schema** — the data structure of the model plus static semantics, usually via a **meta-model**.
2. **DSL editing environment** — a rich editing experience, through either **source editing** or **projectional editing**.
3. **Semantic Model behavior** — what the script actually does, most commonly via **code generation**.

Two structural observations follow. Workbenches make the Semantic Model the core of the system, but they define it in a **special meta-modeling structure that allows runtime tools to work on the model** rather than in a programming language — which is exactly what enables their tooling. And that produces a **separation between schema and behavior**: the schema is essentially a data model without much behavior, with behavior arriving from outside, mostly as generated code.

### 8.8 Meta-models — and when *not* to use one

A **schema** is what you can have in the contents of the model — "the same as any data structure definition: classes and instances, tables and rows, record types and records. The schema defines what goes into the instances." If guards aren't in the schema, you can't put guards on transitions. A **meta-model** is "a model whose instances define the schema for another model": instead of expressing the schema as class definitions, you express it as objects describing classes and fields, which lets you **manipulate the schema at runtime**. Since a meta-model is just another Semantic Model, you can define a DSL to populate it — a **schema definition language** *(Ch. 9, "Schema Definition Languages and Meta-Models")*.

The tradeoff is the part most often missed. **When rolling a DSL by hand, there usually isn't much point in creating a meta-model**, for three reasons: using the host language's own structural definition capability is usually the best bet, because a language you already have is easier to follow and you use familiar constructs for both schema and instances; you **lose static help**, writing generic field lookups instead of typed accessors, which makes it harder to discover available fields, forces you to do your own type checking, and generally means "I'm working *despite* my language rather than *with* it"; and the biggest argument, you lose the ability to make the Semantic Model a proper OO domain model — the meta-model does a "tolerable, if kludgy" job of defining structure but "it's really hard to define behavior."

The tradeoff inverts for workbenches precisely because **tooling** consumes the schema: to provide good tooling a workbench must examine and manipulate the schema of any model you define, which is much easier with a meta-model, and the workbench's own tooling overcomes many of the usual disadvantages.

Two further points. A **bootstrapped workbench** defines its own schema definition system with a meta-model, so you create meta-models with the same tools you use to write DSL scripts; the benefit is that it "gives you more confidence that the modeling tools will be sufficient for your own work, since the tool can define itself." And a clean distinction: **a grammar defines the concrete syntax of a textual language; a schema definition language defines the structure of the schema of a Semantic Model**, and is therefore independent of any DSL used to populate it.

**Structural constraints** round out the schema story. A schema is largely about data structures, but there is a further element: constraints on what makes a valid instance, "equivalent to invariants in Design by Contract." Two kinds, carefully distinguished: constraints **implied by the data structure itself** — "we can't say anything in the Semantic Model that its schema can't store," so if a transition has one target state you simply cannot add a second — and constraints **not due to the data structure**, where "we can store it, but it's illegal" (a person's leg count must be 0, 1, or 2 even though the field is an integer; a person cannot be her own ancestor). The second kind is what "structural constraints" usually means. And one design rule with real consequences: structural constraints **cannot change the Semantic Model, they can only query it** — "In this way they are a Production Rule System without any chaining."

### 8.9 Source vs projectional editing

A **source-based editing system** defines the program in a representation that is **editable independently of the tools that process it** — in practice, text, so any text tool can read and edit it. A **projectional editing system** holds the core representation in a tool-specific format — a persistent representation of the tool's Semantic Model — and the tool **projects editable representations** of that model, as text, diagrams, tables, or forms *(Ch. 9, "Source and Projectional Editing")*.

Advantages of projectional editing: **editing through different representations** (a state machine is best *thought of* as a diagram; with source you can visualize a diagram but not edit it); **control over the editing experience** to make correct input easy and incorrect input impossible, producing a much tighter feedback cycle; **multiple projections**, simultaneously or as alternatives, where editing any one updates the core model and therefore all the others; and **semantic transformations**, since renaming is captured as an operation on the model rather than in textual terms — "particularly helpful for doing refactorings in a safe and efficient manner."

So why does source-based editing still dominate? Fowler notes projectional editing "is hardly new; it's been around for at least as long as I've been programming," yet "most serious programming we do is still source-based," and gives four reasons:

- **Tool lock-in.** Beyond vendor nerves, it "makes it hard to create an ecosystem where multiple tools collaborate over a common representation. Text, despite its many faults, is a common format; so tools that manipulate text can be used widely."
- **Source code management is the killer example.** Concurrent editing, diff, automated merging, transactional repository updates, and distributed version control all work across a wide range of environments **because they operate only on text files**. "We see a sad situation where many tools that could really use intelligent repositories, diffs, and merges are unable to do so."
- **Pragmatic advantages of text** — emailing a snippet is trivial; explaining via projections and screenshots is much more trouble; text-processing tools automate transformations a projectional system may not provide.
- **The subtle one.** A projectional system's ability to allow only valid input can be helpful, but "it's often useful to type in something that doesn't work immediately, as a temporary step, while thinking through a solution." Fowler explicitly flags that **the difference between helpful restriction and constraints on thinking is often a subtle one.**

**Model-assisted source editing** is named as one of the triumphs of modern IDEs and "comes close to the best of both worlds": you work fundamentally in a source-based way, but the IDE builds a semantic model from your sources and uses projectional techniques to make editing easier. The cost is resources — parsing everything, holding the model in memory, and keeping it updated as you type, "a difficult task."

Fowler also offers a vocabulary worth stealing for reasoning about any system's artifacts: the **editing representation** (what we edit), the **storage representation** (what we persist), the **executable representation** (what we run), and the **abstract representation** (a computer-oriented construct generated to make processing easier). In source-based systems, source plays two roles at once — editing *and* storage — and in interpreted languages a third. In projectional systems the core representation is the Semantic Model, projected into multiple editing representations, and stored in a separate storage representation which may be readable at some level "but isn't a representation any sane person would use for editing."

### 8.10 Illustrative programming

Fowler's coinage for what projectional editing enables: putting a concrete **illustration** of program output in the foreground of the editing experience, with the program itself in the background. In regular programming we pay most attention to the program, "a general statement of what should work" *(Ch. 9, "Illustrative Programming"; Ch. 1, "Using Language Workbenches")*.

The spreadsheet is the argument. By his "unscientific observation" it is the most popular programming environment in the world, and its popularity is notable because most spreadsheet programmers are **lay programmers** who don't consider themselves programmers at all. The most visible thing in a spreadsheet is an illustrative calculation with a set of numbers; the program hides in the formula bar, one cell at a time. **The spreadsheet fuses execution with definition and makes you concentrate on the former.** It shares a property with heavy use of testing, "but with the difference that in a spreadsheet the test output has more visibility than the program." He chooses "illustrative" over "example" because the word reinforces the *explanatory* nature of the execution.

He sharpens the concept with two boundary cases. IDE projections during editing (a continuously updated class hierarchy) are similar but not the same, because they can be derived from **static** information, whereas **illustrative programming requires information from the actual running of the program**. And REPL snippets, beloved in dynamic languages, are narrower: interpreting snippets lets you explore execution, "but it doesn't put the examples front and center, the way that a spreadsheet does with its values."

The downside is stated as firmly as the upside: "I don't think illustrative programming is all goodness." Spreadsheets and GUI designers reveal *what a program does* but **de-emphasize program structure**, so complicated spreadsheets and UI panels are often difficult to understand and modify, "rife with uncontrolled copy-and-paste programming." The stated challenge for future environments is to help develop a well-structured program behind the illustrations — "although the illustrations may also force us to rethink what a well-structured program is." And the hard part is creating new abstractions: UI builders get tangled because they think only in terms of screens and controls, and a screen builder cannot support the abstractions your program actually needs, "for it can only illustrate the abstractions it knows about."

### 8.11 Workbenches vs CASE tools, and whether to use one

The surface similarities with 1990s CASE tools are real: a central model, meta-models, diagrammatic projectional editing. **The key technological difference: CASE tools did not give you the ability to define your own language.** The most important difference, though, is cultural — many in the CASE world **looked down on programming** and saw their role as automating something that would die out, whereas the language workbench community largely comes from a programming background and aims to make programmers more productive. That culture produces a tell Fowler recommends using when evaluating such tools: workbenches "tend to have strong support for code generation tools — as this is central to producing a useful output from the tool. This aspect tends to get missed during demonstrations, as it's less exciting than the projectional editing side, **but it's a sign of how seriously we should take the resulting tool**" *(Ch. 9, "Language Workbenches and CASE Tools")*.

Should you use one? "If language workbenches pull off their vision, they could completely change the face of programming, altering our idea of a programming language" — but that "could end up like nuclear fusion's potential to solve all of our energy needs." The concrete reason for caution beyond newness is **lock-in**: "Any code you write in one language workbench is impossible to export into another one," and any effort you commit could be lost if you hit a wall or the vendor does *(Ch. 9, "Should You Use a Language Workbench?")*.

His mitigation is the most practically useful idea in the chapter: **treat the language workbench as a *parser* rather than as a full DSL environment.** Instead of designing the Semantic Model in the workbench's schema environment and generating full-featured code, build the Semantic Model the usual way in your own code, and use the workbench only for the editing environment, with a model geared to model-aware generation against *your* model. The payoff: "should you run into issues with your language workbench, it's only the parser that's affected. The most valuable stuff is in the Semantic Model which isn't locked in." He concedes this is somewhat speculative, and concludes the tools are worth experimenting with: "Although it's a risky investment, the potential returns are considerable."

### 8.12 Lessons from real DSLs

Chapter 10 surveys real DSLs explicitly *not* chosen as "the best," but to show the variety that exists. Read as a design study, each entry teaches one or two things.

**Graphviz** — the clean-seam exemplar. Its DOT language is an external DSL with two kinds of thing, nodes and arcs; nodes can be declared but don't have to be (a reference brings one into existence), both can carry bracketed attributes, and statement separators are entirely optional. Those concessions to authoring convenience are affordable precisely because the language's scope is narrow. Architecturally: a Semantic Model as a plain data structure, populated by a parser using syntax-directed translation and embedded translation, with helper functions called from the grammar actions so that **the grammar itself stays readable with short code actions** — the concrete payoff of the Embedment Helper advice. And the key point: "The real business of Graphviz occurs once the Semantic Model of nodes and arcs is populated" — layout, then rendering to various formats — and all of it is independent of the parser *(Ch. 10, "Graphviz")*.

**JMock** — the API-design evolution case study, and the highest-value entry for library authors. Mock expectations "need to be written in with test code as a fragmentary DSL, so an internal DSL is a natural choice for them" *(Ch. 10, "JMock")*. Version 1 composed four techniques: **method chaining** on the mock object; **nested functions** for the argument-shaped parts (cardinality, argument matchers, return values); **object scoping** to let those nested functions be written bare, implemented by **forcing all tests using mocks to be written in a subclass of the library class**; and **progressive interfaces**, where each chaining method returns a *narrower* interface exposing only what is legal next — so a `with` clause is available only after a method has been named, "which allows the autocompletion in IDEs to guide you through writing the expectations in the right way." Underneath, Expression Builders translate onto a Semantic Model of mocks and expectations; Freeman and Pryce's vocabulary, which Fowler adopts, calls these the **syntax layer** and the **interpreter layer**.

Fowler flags an extensibility lesson explicitly, and it is the sharpest API point in the chapter: **the interplay of method chaining and nested functions determines who can extend the language.** Method chaining is **closed to users**, because the chaining methods are defined on the Expression Builder and therefore fixed by the library. Nested functions are **open to users**, because new ones are easy to add on the test class itself or on the user's own subclass of the scoping class. The choice between them is not stylistic; it decides your extension points.

JMock 2 then fixed the intrusive part. The v1 requirement that all mock-using tests subclass the library class consumed the user's single-inheritance slot and dictated test-class structure. V2 uses an instance-initializer idiom to achieve object scoping instead, which Fowler reclassifies as effectively a **Nested Closure**. The cost is acknowledged — "this does add some noise at the beginning of the expression" — and the benefit is that "we can now define expectations **without being in a subclass**." A second change: instead of chaining everything, v2 uses a **function sequence** to separate the method-call part of an expectation from the return-value specification. The arc is the lesson: v1 optimized the expression and paid with a structural constraint on user code; v2 traded a little syntactic noise to remove it, and Fowler presents that as the right trade.

**CSS** — Fowler's most-used example. It is notable for being **written by non-programmers** ("Most CSS programmers don't call themselves programmers, but web designers"), which makes it one of his few exceptions to the read-don't- write rule of §3.2b. It is genuinely declarative — you declare matching rules rather than steps — and it illustrates **the dark side of declarative**: because an element can match multiple rules, CSS needs a somewhat complicated specificity scheme, and "Many people find it hard to figure out how these rules work — which is the dark side of a declarative model," exactly the implicit-behavior warning of §3.4. It is well-focused: essential, but "the thought of using only it to build an entire web application is ludicrous. It does its job pretty well, and works with a mix of other DSLs and general-purpose languages inside a complete solution." It also corrects a common misreading: **limited expressiveness does not mean small** — "CSS is also quite large... DSLs can be limited in what they can express, but still have a lot to learn." And it exhibits the general DSL habit of **limited error handling**: browsers ignore erroneous input, so a syntax error "misbehaves silently, often making for some annoying debugging" — presented as a real cost, not a virtue *(Ch. 10, "CSS")*.

Most importantly, CSS has **no way to create new abstractions** — "a common consequence of the limited expressiveness of DSLs" — with the concrete pain that you cannot name the colors in your palette and have no arithmetic for sizes and margins. Fowler names the two standard remedies: **macros**, which solve simple cases like named colors; and **layering another DSL on top that generates the base DSL as output**, with SASS as the example. His stated conditions for that layering to work are the practical acceptance criteria: "the overlayed DSL needs to be similar (SASS uses the same attribute names), and **the user of the overlayed DSL usually also understands the underlying DSL**."

**HQL** — a query language written in terms of application classes rather than database tables, which lets people think in their own domain objects and avoids the annoying differences between SQL dialects. Its implementation is a three-step pipeline: input text → input AST → output AST → output text, all with the same parser tool (which can take an AST as input via a "tree grammar" as well as a token stream). The generalizable point: "it's good to break down a complex transformation into several small transformations that can be easily plugged together." And a nuance about the Semantic Model: you can regard the **SQL AST as the Semantic Model** here, since the meaning of an HQL query is defined by its SQL rendering — "But more often than not, ASTs are not the right structure for a Semantic Model, as the constraints of a syntax tree usually help more than they hinder. But for source-to-source translation, using an AST of the output language makes a great deal of sense" *(Ch. 10, "Hibernate Query Language")*.

**XAML** — a DSL for screen layout, motivated by the observation that "a screen layout is primarily a hierarchic structure, and stitching a hierarchy together in code is fiddlier than it ought to be." On the XML choice, Fowler is notably conciliatory: XAML "does suffer from XML's syntactic noise, but XML does work fairly well on hierarchic structures like this," and its resemblance to markup people already know is a plus — i.e., XML is defensible *specifically* when the domain is hierarchic and a familiar analogue exists. It also introduces a distinction attributed to Brad Cross: a **compositional DSL** organizes relatively passive objects into a structure (XAML), while a **computational DSL** produces a model that "feels more like code than data" (the state machine) — "You can do a lot more with a computational DSL, but people often find them more difficult to work with." Two implementation lessons: the generated code is emitted as a **partial class** so handwritten behavior lives in another file — the "multiple files per class" solution of §8.4 in the wild — and handwritten code **refers to controls by name**, which "allows me to change it without having to update the behavior code." That last point generalizes into a small design rule about structure: **nesting expresses trees; names express graphs** (Graphviz builds graphs precisely by referring to names), and choosing between them is a primary syntax decision *(Ch. 10, "XAML")*.

**FIT** — a testing framework built on the observation "that nonprogrammers are quite comfortable with specifying examples in a tabular form." A FIT program is a collection of tables embedded in documents, and **anything between the tables is treated as comments**, which "lets a domain expert use prose narrative to describe what they want, with tables providing something that's processable" — an inversion of the usual code-to-comment ratio worth stealing. Its table styles are different sub-languages for different jobs: an **action fixture** is "essentially a simple imperative language... simple in that there are no conditionals or loops, just a sequence of verbs" — a clean example of deliberate non-Turing-completeness — and a **row fixture** is declarative, defining expected tabular output; the two compose, navigating the application imperatively and then asserting declaratively. The feedback mechanism is notable: running a table produces output identical to the input page **except that check rows are colored green or red**. Fowler draws the general claim: "Testing is a natural choice for a DSL. Compared to general-purpose programming languages, testing languages often require different kinds of structures and abstractions... Tests often need to be read by domain experts, so a DSL makes a good choice, usually with a DSL purpose-written for the application at hand." And on tables generally: "People like specifying things in tabular form... Many domain experts are very comfortable with editing tables in spreadsheets" *(Ch. 10, "FIT")*.

**Make and its descendants** — builds use a **Dependency Network** because "many steps are expensive and don't need to be done every time," letting you "minimize build times to a bare minimum while ensuring that everything that needs to be built is actually built." But Fowler says the most interesting thing about build languages is *not* the computational model: it's "the fact that they need to **intermix their DSL with a more regular programming language**," since besides declaring targets and dependencies you must say how each target is built, which suggests an imperative approach. The second structural problem is that a simple dependency network needs further abstractions once builds get complex — and the historical responses are the same pattern three times over: Automake *generates* Makefiles; Maven *generates* Ant scripts; SASS *generates* CSS. Rake is Fowler's preference: the same dependency network as an internal DSL, so you can write target contents seamlessly in nested closures and build larger abstractions with the host language's own facilities. (A small vocabulary note worth keeping: Rake targets can be either tasks or files, "supporting both task-oriented and product-oriented styles of Dependency Network.") He also concedes a point to XML here: despite his dislike of it as a carrier syntax, Ant's XML "did avoid Make's horrendous problems caused by allowing tabs and spaces in syntactic indentation" *(Ch. 10, "Make et al.")*.

> **SDK lens:** Generation is a tooling and checking strategy at least as much as a portability one — the strongest case for a generated typed client is that spec drift becomes compile errors and users get autocompletion. When you generate, prefer emitting **configuration data consumed by hand-written generic code** over emitting control flow: the generic half stays testable in the target environment and only the small specific half is generated. Never hand-edit generated output, keep it in separate files rather than marked regions, don't commit it if you can regenerate it, prefer a one-way call direction between generated and handwritten code, and optimize the output for *readability and debuggability* rather than modifiability — duplication is cheap when nobody maintains it, and generated comments pointing back at the model are unusually valuable because they cannot rot. When you embed one language inside another's file, each embedded fragment should be a single call into a real module in its own native file, so the tools can still see it. On metadata-driven design: runtime schemas and descriptors pay off exactly when *tooling* must consume them generically; when only human programmers consume them, native language constructs win. Keep any vendor tool at the edge and your model in your own code. And two rules the case studies keep repeating: **method chaining is the closed half of your API and free functions are the open half**, so put phase and ordering constraints in the chain and let users extend the vocabulary in their own scope; and **when a limited declarative surface needs abstraction, layer a generator over it rather than growing it** — provided the upper layer mirrors the base's vocabulary and its users still understand the base.
