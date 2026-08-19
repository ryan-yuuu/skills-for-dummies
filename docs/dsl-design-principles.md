# Domain-Specific Languages: Design and Implementation Principles

**Distilled from:** Martin Fowler with Rebecca Parsons, *Domain-Specific Languages*, Addison-Wesley Signature Series, 2010 (ISBN 978-0-321-71294-3).

## What this document is

This is a complete distillation of the design and implementation principles in Fowler and Parsons' *Domain-Specific Languages* — the architecture, the seams, the tradeoffs, and the judgement calls — written so that someone who has not read the book can learn the material and apply it to designing software, and especially to designing SDKs, libraries, and APIs.

It deliberately omits the book's code examples. The book's Java, C#, and Ruby are 2010-era and don't translate well to other languages; the *principles* do, and Fowler himself wrote the book to be language-independent ("One of my top priorities is to uncover general principles and patterns that can be used with whatever programming language you happen to be using," Preface). Every technique here is described conceptually, and every major claim carries a citation to its chapter and section in the book in the form *(Ch. N, "Section Name")*.

A note on why a book about *languages* is a book about *SDKs*: Fowler's own framing is that "most DSLs are merely a thin facade over a library or framework" (Preface) and that "Library design is language design" (Ch. 2, quoting the old Bell Labs saying). The book is, among other things, the most systematic treatment in print of what makes a library's calling surface readable, composable, safe, and evolvable — the fluent-interface patterns in Part 2 of this document are the shared vocabulary of modern builder APIs, and the code-generation patterns in Part 3 describe the architecture of every good generated client SDK. Each section below ends with an **SDK lens** callout that makes the transfer explicit.

## How this document is organized

- **Part 1 — Foundations and Strategy** (§1–8): what a DSL is and where the boundaries lie; the central Semantic Model architecture; when to build one and when not to; the lifecycle; the processing pipeline; overviews of internal and external technique families; code generation strategy, language workbenches, and lessons from real-world DSLs (Book Part I, Chapters 1–10).
- **Part 2 — The Pattern Catalog I: Foundations and Fluent APIs** (§9–11): the six foundational patterns every DSL and SDK needs (Semantic Model, Symbol Table, Context Variable, Construction Builder, Macro, Notification); the seven fluent-interface patterns and how to choose among them; the eight expressive-vocabulary patterns and their judgement calls (Book Parts II and IV, Chapters 11–16 and 32–46).
- **Part 3 — The Pattern Catalog II: External DSLs, Computational Models, and Code Generation** (§12–15): parsing strategies and how to choose one; output-production strategies; the five alternative computational models; the six code-generation patterns (Book Parts III, V, and VI, Chapters 17–31 and 47–57).
- **Part 4 — Synthesis: The SDK Designer's Playbook** (§16–19): the cross-cutting principles collected in one place; condensed decision guides; the warnings index; and a master pattern quick-reference table mapping every pattern to its modern SDK analog.

If you are here specifically for SDK/API design, the fast path is: §2 (the central architecture), §9 (Semantic Model and Notification), §10 (the fluent patterns and "Choosing among the fluent techniques"), §11 (options objects, decorators, dynamic APIs), §15 (generated SDKs), then all of Part 4.

---

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

# Part 2 — The Pattern Catalog I: Foundations and Fluent APIs

## 9. Foundational patterns every DSL (and SDK) needs

Fowler's Part II collects the six patterns that apply regardless of whether your language is
internal (written in a host programming language) or external (with its own parser). They are
foundational in a strong sense: the rest of the catalog is largely defined *in terms of* them.
One pattern — Semantic Model — is the hub, and the other five describe how you populate it, how
you track your position while populating it, how you reconcile immutability with gradual
discovery, how you report what went wrong, and one technique (Macro) you should mostly avoid.

If you read nothing else in this part, read the Semantic Model section. It contains the single
most transferable piece of API-design advice in the book.

---

### Semantic Model (Ch. 11)

> **Intent:** "The model that's populated by a DSL." *(Ch. 11, intent line)*

#### The concept, from scratch

Imagine you are building a tool that configures state machines. You could write a parser that
reads a configuration file and, as it reads each line, directly performs the effect — opening a
door, wiring up a callback, emitting code. Most people's first instinct is exactly this: the
parser *is* the program.

Semantic Model says: don't do that. Instead, build an ordinary in-memory object model of the
*same subject matter* the language describes. If your language describes state machines, build
classes for `State`, `Event`, `Transition`. A particular script then corresponds to a particular
**population** of that schema — one `Event` object per event declared, one `State` per state, and
so on. The script is data; the model is the thing that actually knows what a state machine *is*.

The framing sentence worth memorizing: the Semantic Model is **"the library or framework that the
DSL populates"** *(Ch. 11, "How It Works")*. The DSL is not the thing. The DSL is a *front end*
for populating something that could exist perfectly well without it.

The representation is not required to be an in-memory object model. It could be a plain data
structure with behavior supplied by functions over that data. It need not even be in memory — a
DSL could populate a model held in a relational database. Fowler uses in-memory object models
throughout the book because that is what he knows best, not because the pattern requires it
*(Ch. 11, "How It Works")*.

#### The decisive design rule: usable without the DSL

> The Semantic Model **should be usable without a DSL present.** You should be able to populate it
> through an ordinary command-query interface. *(Ch. 11, "How It Works")*

This is the constraint that keeps the pattern honest, and Fowler gives two reasons. First, it
ensures the Semantic Model fully captures the semantics of the subject area — if some concept can
only be expressed by going through the parser, that concept lives in the parser, and the model is
incomplete. Second, it makes the model and the parser **independently testable**: you test
semantics by populating the model directly and asserting on its behavior; you test the parser by
asserting that it produced the right population.

If populating the model requires going through the DSL, you have smeared semantics into your
parser and lost the whole benefit.

Fowler gives a behavioral test for whether you have really achieved this *(Ch. 32, "How It
Works")*: you should be able to write tests for the Semantic Model that use no DSL at all. He
immediately tempers it — the point of an internal DSL is to make these objects *easier* to work
with, so most tests will naturally use the DSL — "But I'd usually include at least some tests that
only use the command-query interface."

#### The two interfaces

It is usually helpful to think of the Semantic Model as having **two distinct interfaces**
*(Ch. 11, "How It Works")*:

1. **Operational interface** — what clients use to *do work with* an already-populated model. It
   assumes the model has been created and makes it easy for the rest of the system to take
   advantage of it.
2. **Population interface** — what the DSL/parser uses to *create instances* of the model's
   classes. Used only by the parser(s) and by the model's own test code.

The population interface also acts as a **decoupling seam**. There is always *some* dependency —
the parser obviously has to see the Semantic Model in order to populate it — but by making the
population interface an explicit, deliberately designed boundary, an implementation change inside
the Semantic Model is much less likely to force a change in the parser. Fowler reports exactly
this payoff in the book's introductory example: he refactored the state machine model's internals
without touching the parsing code, because the changes did not alter the population interface
*(Ch. 11, "The Introductory Example (Java)")*.

#### The "pretend the model is magically already there" trick

This is the API design move that carries furthest beyond DSLs, and Fowler presents it as a general
rule of thumb for *any* objects, not just DSL-ish ones:

> **Assume the model is magically already there, then ask yourself how you would use it.**

Define the operational interface *first*, even though at runtime the population interface
necessarily executes first. Fowler acknowledges this is counterintuitive but insists it produces
better designs *(Ch. 11, "How It Works")*.

The reason it works is that construction concerns are seductive and dominant. If you design
construction first, every subsequent decision is shaped by "how do I get the values in?" — which
is a question your users mostly don't care about. Designing usage first forces you to answer "what
does the caller want to ask this thing?", which is the question that determines whether the
abstraction is any good.

#### Semantic Model vs. Domain Model

The Semantic Model is similar to a Domain Model *[PoEAA]*, but Fowler deliberately uses a separate
term, for four reasons *(Ch. 11, "How It Works")*:

- Semantic Models are often *subsets* of Domain Models, but don't have to be.
- "Domain Model" implies a behaviorally rich object model; a Semantic Model **may be data alone**.
- A Domain Model captures the core behavior of an application; a Semantic Model may play only a
  supporting role.
- The worked distinction: a DSL that describes object-relational mappings produces a Semantic Model
  consisting of the *Data Mappers* — **not** the Domain Model that is the subject of the mapping.

That last one is the clarifying case. The thing your language talks *about* and the thing your
language *builds* are different objects.

#### Semantic Model vs. syntax tree / AST

This distinction is the crux of the pattern *(Ch. 11, "How It Works")*:

- A **syntax tree corresponds to the structure of the DSL script.** Even an *abstract* syntax tree,
  which simplifies and reorganizes the input somewhat, still takes fundamentally the same form as
  the input.
- A **Semantic Model is based on what will be done with the information** in the script. It often
  has a substantially different structure, and is usually **not a tree at all** — graphs with
  cross-references are common. A state machine's transitions point at *shared* state and event
  objects; a tree cannot express that sharing.

Occasionally an AST *is* an effective Semantic Model, but "these are the exception rather than the
rule."

Fowler notes that traditional parsing/compiler literature doesn't use the term, and diagnoses why:
for a general-purpose language, a syntax tree is a perfectly suitable basis for code generation, so
there is less pressure to build something different. Compiler people *do* occasionally build one —
a call-graph representation is very useful for optimization — and they call these **intermediate
representations**.

#### Where the model comes from

Two common origin stories *(Ch. 11, "How It Works")*:

- **The model precedes the DSL.** You already have a Domain Model and decide that some portion of
  it would be better populated from a DSL than through the regular command-query interface. The DSL
  is layered on top.
- **The model and the DSL are built together**, with discussions with domain experts refining both
  the expressions of the language and the structure of the model. Each informs the other.

#### Execution: interpreter style vs. compiler style

The Semantic Model can either **hold the code to execute itself** (interpreter style) or **be the
basis for code generation** (compiler style). Even when generating code, Fowler recommends *also*
providing interpretation — it helps enormously with testing and debugging, and lets you use the
Semantic Model as a **simulator for the generated code** *(Ch. 11, "How It Works")*.

Because the code generator works off the Semantic Model rather than off the parser, multiple code
generators become cheap: independence from the parser avoids duplicating parser logic across
generators.

#### Validation belongs in the model

The Semantic Model is "usually the best place for validation behavior, since you have all the
information and structures in place to express and run the validations" *(Ch. 11, "How It Works")*.
Crucially: run validations *before* either running the interpreter or generating code.

In the introductory state-machine example the validations were things like: no unreachable states,
no states you can't get out of, all events and commands actually used in the definitions of states
and transitions *(Ch. 11, "The Introductory Example (Java)")*. Note that none of these are
*syntactic* — you cannot express them as grammar rules, and you cannot check them one line at a
time. They are properties of the whole populated graph, which is exactly why they belong to the
model and not the parser.

This is also where **Notification (Ch. 16)** joins the picture: validations over a populated model
naturally want to report *all* problems at once rather than aborting on the first.

#### Computational vs. compositional DSLs

Fowler cites Brad Cross's distinction *[cross-comps]* and observes that it is really a distinction
about the *kind of Semantic Model* produced *(Ch. 11, "How It Works")*:

- **Compositional DSL** — describes some composite structure in textual form. XAML describing a UI
  layout is the example; the primary form of the Semantic Model is *how the various elements are
  composed*.
- **Computational DSL** — the Semantic Model "feels more like code than data" and drives
  computation, usually with an alternative computational model instead of the usual imperative one.
  The Semantic Model here is usually an **Adaptive Model**. The state machine is of this kind.

The tradeoff he flags: "You can do a lot more with a computational DSL, but people often find them
more difficult to work with."

This distinction is worth carrying into SDK work directly. A configuration API that assembles a
structure (a pipeline, a schema, a UI tree) is compositional; its model is mostly data and its main
job is composition rules. An API that lets users express *behavior* (rules, policies, predicates,
retry strategies) is computational; its model holds executable fragments and its main job is
evaluation. The second is more powerful and materially harder for users.

#### When to use it — and when not to

Fowler's answer is essentially *always*, and he is self-aware about it: he notes he's uncomfortable
saying "always" because absolute advice is usually a sign of closed-minded thinking, but he can see
very few cases where you wouldn't want one, and those are all very simple situations *(Ch. 11,
"When to Use It")*.

**Arguments for:**

1. **Separate testing of semantics and parsing.** Test semantics against the model directly; test
   the parser by checking it populates the model with the right objects.
2. **Multiple parsers become tractable.** With more than one parser, you can check they're
   semantically equivalent by comparing the populations they produce. Fowler had exactly this
   requirement in the book's introductory example — multiple internal *and* external DSLs over one
   model — and the Semantic Model let him add a new DSL+parser without duplicating code in the
   other parsers or altering the model.
3. **Independent evolution.** More common than multiple DSLs is simply evolving the DSL separately
   from the Semantic Model, and vice versa.
4. **Flexibility in execution.** Direct interpretation, code generation off the model, both at once
   (model-as-simulator), multiple code generators, plus non-execution outputs like visualizations.
5. **The most important reason, in his words:** it "separates thinking about semantics from
   thinking about parsing. Even a simple DSL contains enough complexity to justify dividing it up
   into two simpler problems."

**The exceptions he envisages** *(Ch. 11, "When to Use It")*:

- **Simple imperative interpretation** — you just execute each statement as you parse it. A
  calculator evaluating arithmetic expressions is the canonical case.
- **When the AST already *is* the model.** For arithmetic expressions, even if you don't interpret
  immediately, the AST is pretty much what a Semantic Model would be anyway. Generalized rule:
  *if you can't think of a more useful model than the AST, there's little point creating a separate
  Semantic Model.*
- **Code generation directly off the AST** — the most common real-world case where people skip the
  pattern. Reasonable *provided* the AST is a good model of the underlying semantics **and** you
  don't mind coupling code generation to the AST. If either condition fails, it's often simpler to
  transform the AST into a Semantic Model and do a simpler code generation from that.

**His stated bias:** always *start* by assuming you need a Semantic Model. Even if thinking it
through convinces you one isn't necessary, stay alert to increasing complexity and put one in as
soon as any complication starts creeping into the parsing logic.

**Honest caveat:** Semantic Model is not part of DSL culture in the functional programming world.
The FP community has a long history of DSL thinking, and Fowler admits his experience with modern
functional languages is "no more than occasional experimentation," so he explicitly declines to
claim his inclination applies there.

#### Relationships

- **Symbol Table (Ch. 12)** — its values are usually Semantic Model objects (or builders that will
  produce them); it is how a script's textual identifiers resolve to model objects.
- **Construction Builder (Ch. 14)** — needed when the model's objects are immutable but the parse
  gathers their field values gradually.
- **Context Variable (Ch. 13)** — the "current item" during a parse is typically a model object or a
  builder for one.
- **Notification (Ch. 16)** — the reporting vehicle for validations run over a populated model.
- **Expression Builder (Ch. 32)** — the fluent front end that populates the model; explicitly *not*
  part of the model.
- **Adaptive Model** — the usual form of the Semantic Model for a computational DSL.

> **SDK lens:** This is the most important idea in the book for library authors, and it holds even
> when no DSL is involved. Design a core model that is fully usable and testable through an
> ordinary programmatic interface, and treat *every* other surface — fluent builder, YAML loader,
> CLI, config decorator, code generator — as a second-class front end that merely populates it.
> Everything a front end can express must be expressible directly. This is the same discipline as
> "the CLI is a client of the library, not the other way around." Three concrete practices follow:
> (1) design the operational interface first by pretending the object already exists and writing
> the usage code before the construction code; (2) make the population/construction interface an
> explicit, narrow boundary so internal refactoring doesn't ripple into every loader and adapter;
> (3) put validation in the model, not in the loader, so it applies uniformly regardless of which
> front end produced the object. And treat multiple front ends as a design *test*: if two very
> different surface syntaxes can both populate the model and produce equivalent populations, the
> model is probably factored at the right level.

---

### Symbol Table (Ch. 12)

> **Intent:** "A location to store all identifiable objects during a parse to resolve references."
> *(Ch. 12, intent line)*

#### The concept

Many languages need to refer to the same object at several points in a script. If a DSL defines
tasks and their dependencies, one task's definition must be able to *name* other tasks. So you
invent some form of **symbol** for each task, and while processing the script you put those symbols
into a table that stores the link between the symbol and the underlying object holding the full
information.

The essential purpose is to **map between the symbol used in the DSL script and the object it
refers to** *(Ch. 12, "How It Works")*. That maps naturally onto a dictionary, and the most common
implementation is exactly that: a map with the symbol as key and the **Semantic Model** object as
value.

#### Choice of key type

For many languages the obvious choice is a string, because the text of the DSL *is* a string. The
main reason to use something else is a language with a genuine **symbol data type** *(Ch. 12, "How
It Works")*:

- Symbols are structurally like strings (a sequence of characters) but differ in behavior — many
  string operations (concatenation, substrings) make no sense for a symbol.
- A symbol's principal task is *lookup*, and symbol types are designed with that in mind. Two
  occurrences of `"foo"` are often distinct objects compared by content; two occurrences of a symbol
  literal always resolve to the *same* object and compare much faster.
- Performance can justify symbols, but for small DSLs it may not matter much. **The big reason is
  intent communication**: declaring something as a symbol states clearly what you're using it for.
- Symbol literal syntax also makes symbols visually stand out in an internal DSL — a further reason
  to use them.

#### Choice of value type

Values can be either **final model objects** or **intermediate builders**. Model objects make the
Symbol Table act as *result data*, which is good for simple situations. Putting a **builder** as
the value gives more flexibility at the cost of a bit more work *(Ch. 12, "How It Works")*.

#### One map, several maps, or a special class?

Many languages have different *kinds* of thing to refer to — the book's state machine has states,
commands, and events *(Ch. 12, "How It Works")*:

- **Single map for everything.** All lookups share one map. Immediate consequence: you can't use the
  same symbol name for different kinds of things. That may be a *useful* constraint for reducing
  confusion in the DSL. But it makes the processing code harder to read, because it's less clear
  what kind of thing you're manipulating. **Fowler does not recommend this.**
- **Multiple maps** — one per kind of object. You can think of this as one logical Symbol Table or
  three separate ones. **This is Fowler's preference**, because the processing code now makes clear
  which kind of object is being referred to at each step.
- **A special class** — a single Symbol Table object with kind-specific methods (`getEvent(code)`,
  `registerEvent(code, event)`). Sometimes useful, and gives a natural home for symbol-processing
  behavior. Most of the time Fowler doesn't find a compelling need for it.

#### Forward references

Objects referred to before they are properly defined. DSLs usually *don't* have strict
declare-before-use rules, so forward references often make sense. If you allow them, **any
reference to a symbol must populate the entry in the symbol table if it isn't already there**
*(Ch. 12, "How It Works")*. The mechanic is a `register(name)` helper that **creates the object
lazily if the name isn't in the map yet**, called for both sides of every reference — so the table
is both populated by and consulted by the same code path.

This will often push you toward using builders as values, unless the model objects are very
flexible about being filled in later.

#### Misspelled symbols

If there's no explicit declaration of symbols, misspellings become a frustrating error source — a
typo silently creates a new, unrelated entity. If there's any way to detect misspelled symbols, put
that checking in; it "will prevent a lot of hair-pulling" *(Ch. 12, "How It Works")*. This is one
reason to *require* that all symbols be declared in some way. Note that requiring declaration does
**not** mean requiring declaration *before* usage.

#### Nested scopes

Symbols defined only within a subset of the program. Very common in general-purpose languages,
"much rarer in simpler DSLs." If you need it, use *Symbol Table for Nested Scopes* *[parr-LIP]*.

#### Statically typed symbols

In a statically typed host language you can trivially use a hashmap with string keys and it works,
but Fowler lists four concrete disadvantages *(Ch. 12, "Statically Typed Symbols")*:

1. Strings introduce **syntactic noise** — you have to quote everything.
2. The compiler **can't type check.** Misspelled names surface only at runtime; and with several
   *kinds* of identified object, the compiler can't tell you when you've referred to the wrong kind.
3. **No IDE autocompletion** on strings — you lose a powerful element of programming assistance.
4. **Automated refactorings** may not work well with strings.

The fix is some kind of statically typed symbol. **Enums** are the simple good choice; a **Class
Symbol Table (Ch. 44)** is the other, heavier one.

Fowler is candid that he isn't enthusiastic about static typing *for finding errors* — he thinks it
catches few errors that decent testing wouldn't — but he values it for **IDE support**: type
Control-Space and get the list of all symbols valid at that point *(Ch. 12, "Enums as Statically
Typed Symbols (Java)")*.

Three judgement calls from the enum example worth keeping:

- Enums "don't force inheritance or constraints on where you can write DSL script code — an
  advantage compared to a *Class Symbol Table*."
- If the set of symbols must correspond to some **external data source**, write a build step that
  reads that source and **code-generates the enum declarations**, keeping everything in sync
  *[kabanov-hunger]*.
- A single enum implies a **single namespace of symbols**. Fine when many little scripts share one
  symbol set; not fine when different scripts want different sets. The fix: define the builder in
  terms of an **interface**, have several enums implement it, then selectively import only the group
  you need so the IDE offers only relevant symbols.

#### When to use it

Short and decisive: "Symbol Tables are common to any language-processing exercise, and I expect
you'll almost always need to use them" *(Ch. 12, "When to Use It")*.

The times they aren't strictly necessary: with Tree Construction you can always delve around in the
syntax tree to find things, and often a search on the Semantic Model you're building could do the
job. "But sometimes you need an intermediate store, and even when you don't, it often makes life
easier."

#### Relationships

- **Semantic Model (Ch. 11)** — the usual value type.
- **Construction Builder (Ch. 14)** — the alternative value type, and what makes forward references
  practical.
- **Class Symbol Table (Ch. 44)** — the statically-typed, IDE-oriented specialization.
- **Literal Extension (Ch. 46)** — its substance registry is a Symbol Table with lazy creation.

> **SDK lens:** The string-key critique is a general API critique, not a DSL-specific one. Any
> string-keyed lookup surface — feature flags, metric names, event types, config paths, resource
> identifiers — costs you compile-time checking, autocompletion, and safe rename refactoring. Enums,
> sealed types, literal-union types, or generated constant modules are the fix, and
> **code-generating those constants from the authoritative external source** is how you keep them
> honest as the source changes. Two more directly reusable mechanics: **lazy create-on-reference**
> in a registry is the standard technique for accepting declarations in any order (essential for
> config loaders and dependency registries), and **namespace scoping via interfaces plus selective
> imports** is a low-tech way to give one shared builder several disjoint vocabularies without
> reaching for generics. Finally: if your API accepts free-form identifiers with no declaration
> step, add misspelling detection, because a typo that silently creates a new entity is one of the
> most expensive bug classes you can ship.

---

### Context Variable (Ch. 13)

> **Intent:** "Use a variable to hold context required during a parse." *(Ch. 13, intent line)*

#### The concept

You are parsing a list of items, capturing data about each. Each individual piece of information can
be captured independently, but you also need to know **which item** you're currently capturing
information for. A Context Variable holds the current item in a variable and reassigns it as you
move to a new one.

The sketch is an INI-style file: a `[section]` header assigns `currentProject = new Project(...)`,
and the following `name = …` / `lead = …` lines all operate on `currentProject` *(Ch. 13, sketch)*.

That's the whole mechanism. You have a Context Variable whenever you have a variable named something
like `currentItem` that you update periodically during a parse. The pattern exists mainly to *name*
this thing so its costs can be discussed.

#### What goes in it

A Context Variable can hold either a **Semantic Model object** or a **builder**. A Semantic Model
object is superficially more straightforward, but only if *all* of its properties are mutable at the
moments the parse needs to change them. If they're not, it's usually best to use a builder to gather
the information and create the model object at the end — i.e. a **Construction Builder (Ch. 14)**
*(Ch. 13, "How It Works")*.

#### When to use it — mostly a warning

This chapter is unusual in that its "when to use it" is largely a caution *(Ch. 13, "When to Use
It")*:

- There are many places where you must keep context during a parse, and a Context Variable is the
  obvious choice. It's easy to create and easy to get going with.
- **But they are problematic, particularly as you get more of them.** "By their nature, they are
  mutable state that has to be kept track of, and bugs adore this kind of mutable state." It is easy
  to forget to update the variable at the right moment, and debugging that is difficult.
- There are usually **alternative ways of organizing the parse that reduce the need for Context
  Variables** — in practice: nested closures or nested functions that carry the current object as an
  argument or in lexical scope, or delegating a sub-block to a sub-parser object that owns its own
  item.
- His position: **"While I don't say that any Context Variable is evil, I do prefer to use techniques
  that don't need them."**

The concrete cost is visible in the Function Sequence example *(Ch. 33)*: a `speed()` clause that
could mean processor speed or disk speed must branch on which context variable is currently set, and
throw if neither is. Clause-name resolution degrades from a compile-time question into a runtime
state inspection.

Two smaller lessons from the INI example *(Ch. 13, "Reading an INI File (C#)")*. First, on format
choice: INI can seem old-fashioned, but it remains a lightweight, readable way to handle a **simple
list of items with properties**. XML and YAML handle more complex structures, "but at a cost of
readability and parsing difficulty. If your needs are simple enough for an INI file, it remains a
reasonable choice." Second, the example assigns properties by **reflection** on the property name
rather than a hand-written switch, with the tradeoff stated plainly: "Using reflection makes the code
more complex, but it does mean that I don't need to update the parser when I add more properties to
the Semantic Model."

#### Relationships

- **Construction Builder (Ch. 14)** — the alternative content when the model object isn't freely
  mutable during the parse.
- **Function Sequence (Ch. 33)** — the technique that *forces* Context Variables.
- **Nested Function (Ch. 34)** — eliminates them by passing data through return values.
- **Nested Closure (Ch. 38)** — tames them by scoping their lifetime to a closure invocation.
- **Delimiter-Directed Translation (Ch. 17)** — the parsing style that most often needs them,
  because line-at-a-time parsing has no natural nesting to carry context.

> **SDK lens:** This is the classic critique of **stateful, order-dependent "current object" APIs** —
> `setCurrentX()` followed by a sequence of mutators, or a builder with a `currentThing` field that
> every clause consults. They are easy to write and easy to get wrong: order-dependence,
> thread-safety hazards, ambiguous method names that must dispatch on state, and errors that surface
> at runtime instead of at the call site. Prefer passing the target explicitly, or scoping it with a
> block/closure/context manager so the "current" thing is lexically obvious and cannot leak past its
> region. When you find yourself adding a second context variable to a builder, that is the signal to
> switch to child builders or a block-scoped API.

---

### Construction Builder (Ch. 14)

> **Intent:** "Incrementally create an immutable object with a builder that stores constructor
> arguments in fields." *(Ch. 14, intent line)*

#### The concept

You want the product object to be **immutable**, but you can only discover its field values
**gradually**. Construction Builder resolves that tension: a mutable scratch object accumulates the
values, then hands you a fully-formed immutable product in one shot.

Immutability is a property of the **finished object**, not a constraint on the **construction
process**. That single sentence is the whole pattern.

#### How it works

The recipe is deliberately simple *(Ch. 14, "How It Works")*:

1. Take each of the product's constructor arguments and **make a mutable field for each** on the
   builder.
2. Add further fields for any other attributes of the product you're collecting.
3. Add a method that **creates and returns a new product object** assembled from all the data in the
   builder.

**Optional lifecycle controls** worth adding:

- Check whether you have enough information to create the product before allowing creation.
- Set a flag once you've returned a product, to prevent returning it again — or stash the created
  product in a field.
- Raise an error if someone tries to add attributes to the builder *after* the product was created.

**Composition:** multiple Construction Builders can be combined into deeper structures, so they
produce a *group of related objects* rather than a single object. The example does exactly this — a
flight builder owns a list of leg builders, and the top-level materialization cascades down,
converting each leg builder to an immutable leg on the way *(Ch. 14, "Building Simple Flight Data
(C#)")*.

#### When to use it

Use it whenever you need to create an object with **multiple immutable fields** whose values you
gather **gradually**. The builder gives you "a coherent place to put all this data before you
actually create the product" *(Ch. 14, "When to Use It")*.

**Alternatives Fowler considers and rejects:**

- **Local variables or loose fields.** Capture the pieces in locals until you can call the
  constructor. Fine for one or two products, "but soon gets confusing if you need to create a bunch
  of objects at once, such as when you're parsing." A parse is exactly the case where many half-built
  objects are alive simultaneously.
- **Copy-on-write on the real model object.** Create an actual model object and, each time you learn
  one more immutable attribute, create a new copy with that attribute changed. This saves writing a
  builder but is "generally more awkward to do and follow." The killer objection: **it doesn't work
  if you have multiple references to the object** — you have to chase down and replace every
  reference. This is precisely why it fails for graph-shaped Semantic Models with cross-references.

**The scope limit, stated plainly:** "you only need it when you have immutable fields. If that's not
the case, then just create your product objects directly." Don't reach for a builder reflexively.

#### Construction Builder ≠ Expression Builder

Fowler is emphatic that despite the shared word "builder" these are **different patterns**
*(Ch. 14, "When to Use It")*:

- **Construction Builder** is *purely* about gradually building up constructor arguments. It makes
  **no attempt to provide a fluent interface.**
- **Expression Builder (Ch. 32)** is focused on providing a **fluent interface** — it exists to shape
  the *reading experience* of the DSL.

It is not unusual to find a single object that is both, "but that doesn't mean they are the same
concept."

This separation matters more than it first appears. *Staged construction* and *fluent surface syntax*
are orthogonal design decisions that happen to be frequently combined. Conflating them produces two
failure modes: builders that exist purely for fluency even though the product is mutable (pure
ceremony), and builders whose fluent method names have been contorted to also serve as the
construction API (two jobs, both done badly). Ask separately: *does the product have immutable fields
gathered over time?* (Construction Builder) and *do I want the call site to read as a sentence?*
(Expression Builder).

#### Relationships

- **Semantic Model (Ch. 11)** — the product is typically a model object; the builder is population
  machinery.
- **Symbol Table (Ch. 12)** — putting builders rather than final model objects into the table is what
  makes forward references practical.
- **Context Variable (Ch. 13)** — when the model object isn't mutable enough, the context variable
  holds a Construction Builder instead.
- **Expression Builder (Ch. 32)** — often the same object, conceptually distinct.

> **SDK lens:** This is the canonical justification for **builder types in a library API**: you want
> your public value objects immutable (safe to share, safe to cache, thread-safe, equality-friendly),
> yet callers assemble them over many steps. Don't compromise the product's immutability to make
> construction convenient — add a builder. Put the **lifecycle controls on the builder, not the
> product**: completeness validation at `build()` time, single-use enforcement, and rejecting
> mutation after build. These produce clear, early errors instead of half-built products escaping
> into the system. **Nest builders to mirror nested immutable structures** rather than exposing
> mutable collections on the product. And recognize the rejected alternative in the wild: an API that
> returns a modified copy on every setter looks elegant until objects are referenced from more than
> one place — Fowler's aliasing objection is the precise reason it breaks down at scale.

---

### Macro (Ch. 15)

> **Intent:** "Transform input text into a different text before language processing using Templated
> Generation." *(Ch. 15, intent line)*

This is the chapter where Fowler argues *against* a technique at length. It is the longest of the six
foundational chapters and is essentially a catalogue of failure modes. Understanding *why* he rejects
it is more valuable than the technique itself, because the reasons generalize to every
metaprogramming or code-generation feature you might ship.

#### The concept

A language has a fixed set of forms it can process. Sometimes you can see a way to add abstraction by
manipulating its input text with a purely textual transformation **before** that text is parsed.
Since you know the final form you want, it makes sense to describe the transformation by writing the
desired output with callouts for the parametrizable values — i.e. a template.

Two varieties *(Ch. 15, "How It Works")*:

- **Textual macros** treat text as text. More familiar and easier to understand. A textual macro
  processor can operate on **any** language represented as text — which is essentially all of them.
- **Syntactic macros** are aware of the *syntactic structure* of the host language, so it's easier to
  ensure they operate on syntactically sensible units and produce valid results. A syntactic macro
  processor works with **only a single language**; it's usually baked into that language's tooling or
  its specification.

Historical framing: "In the early days of programming, macros were as prevalent as functions. Since
then, they've largely fallen out of favor, mostly for good reasons." They survive mainly in internal
DSLs, particularly in the Lisp community.

The simplest legitimate form is symbolic substitution. Fowler's example is CSS: a color repeated as a
raw hex code across many rules is hard to update and obscures meaning; a macro processor lets you
name it. Two observations he draws out *(Ch. 15, "Textual Macros")*: the file you now edit **isn't
proper CSS anymore** — "you've enhanced the CSS language with a macro processor," which is precisely
the DSL move; and this particular substitution could equally be done with **Textual Polishing
(Ch. 45)**. The same mechanism handles including common headers and footers into HTML files, which
he concedes is "remarkably handy for small websites."

The critical semantic difference from a function call: **the macro is evaluated at compile time**,
doing textual search-and-replace and substituting arguments as it goes. The compiler never sees the
macro name at all.

#### The four failure modes

These are the heart of the chapter *(Ch. 15, "Textual Macros" / "Syntactic Macros")*:

1. **Mistaken expansion.** A `sqr(x)` macro defined as `x * x`, invoked as `sqr(a + b)`, expands to
   `a + b * a + b` — which, because multiplication binds tighter, is not what you meant. "Expansions
   may work most of the time but only break down in particular cases, leading to surprising bugs that
   are hard to find." Mitigation: "use more parenthesis than a Lisper." **Syntactic macros largely
   avoid this class**, because they know the host grammar.

2. **Multiple evaluation.** You pass an argument with a side effect, and the macro body mentions that
   argument more than once, so it's evaluated more than once — `max(++a, ++b)` increments both twice.
   "It's particularly frustrating because it's hard to predict the various ways macro expansions can
   go wrong. You have to think differently than you do with function calls, and it's harder to see
   through consequences, particularly when you start nesting macros." **Syntactic macros do *not* fix
   this.**

3. **Variable capture (macro declares the name).** A macro body that declares its own local variable
   silently shadows a caller variable of the same name; the passed-in variable is ignored and the
   caller's is left with the wrong value. "The name was expanded into the macro but interpreted by the
   macro as a variable defined within the macro itself."

4. **Reverse variable capture (macro clobbers the caller's name).** The mirror image, in languages
   that don't force variable declaration. The macro body assigns to a name the caller was already
   using, **silently overwriting the caller's variable** while still producing the correct value for
   the named output. The visible behavior looks right, so the bug lands somewhere else, later. "The
   consequences of the capture may be different, indeed worse, than the earlier form of variable
   capture, but both of them stem from the same basic problem."

#### The dominant actual use of macros: deferred evaluation

This is the most transferable insight in the chapter and the reason it earns its place in an SDK
document.

Fowler shows an *Execute-Around Method [beck-sbpp]*: a `safe.open { ... }` call where `open` unlocks
the safe, runs the passed-in block, then locks it again. "**The key point is that the content of the
closure isn't evaluated until the receiver calls `yield`**, so the receiver can open the safe *before*
running the passed-in code." Contrast passing the contents as an ordinary parameter — that fails,
because the parameter is evaluated *before* the call.

> "Deferred evaluation means that the receiving method to a call chooses when, or indeed if, to
> execute the code that's been passed in." *(Ch. 15, "Syntactic Macros")*

In Lisp, writing that call as a plain function requires wrapping the argument in a `lambda`, which
"looks way too messy." A macro restores the clean call syntax. Fowler's conclusion:

> "A large part (perhaps the majority) of the use of Lisp macros is to provide a clear syntax for the
> mechanism of delayed evaluation. **A language with a cleaner closure syntax doesn't need macros for
> this.**" *(Ch. 15, "Syntactic Macros")*

That is the chapter's most important judgement: **most macro use is a workaround for clumsy closure
syntax.** If your language has good block/lambda syntax, you already have most of the benefit with
none of the four failure modes.

He then shows that the Lisp version *still* hits variable capture and multiple evaluation. Lisp's
mitigations are Scheme's **hygienic macros** (the system automatically avoids capture by renaming
symbols behind the scenes) and Common Lisp's **gensyms** (generate guaranteed-unique symbols; more
trouble to use, but they let you *deliberately* use variable capture where that's useful). Fixing both
problems noticeably complicates the macro, and his verdict is: **"Avoiding such issues makes macros a
lot harder to write than they might seem at first sight."**

#### The second use: Parse Tree Manipulation

Beyond deferred evaluation, Lisp macros enable **Parse Tree Manipulation (Ch. 43)**. Lisp's syntax
"seems quirky on first glance, but as you get used to it, you realize that it's a good representation
of the parse tree of the program": in each list the first element is the node type and the rest are
its children. Manipulating Lisp code before evaluation *is* parse tree manipulation.

The worked example is `setf`, which takes an **access expression** and automatically computes and
applies the corresponding **update** — sparing you from remembering an accessor and a mutator for
every data shape. Its limits reduce the magic: it works only on **invertible functions**, with Lisp
keeping a record of inverses. **The load-bearing point:** defining `setf` *requires* macros, because
it depends on the ability to parse the input expression. **"This ability to parse its arguments is
the key advantage of Lisp macros."** *(Ch. 15, "Syntactic Macros")*

Macros aren't the only route: C# supports Parse Tree Manipulation by giving you the parse tree for an
expression plus a library to manipulate it.

#### When to use it

**The appeal:** textual macros work with any text-based language, do all manipulation at compile time,
and can implement impressive behaviors beyond the host language's abilities.

**The costs** *(Ch. 15, "When to Use It")*:

- Subtle bugs — mistaken expansion, variable capture, multiple evaluation — are "often intermittent
  and hard to track down."
- **Macros don't appear in downstream tools.** "The abstractions they provide leak like a sieve
  without the wires, and you get no support from debuggers, intelligent IDEs, or anything else that
  relies on the expanded code."
- **Nested macro expansion is much harder to reason about than nested function calls.** Fowler
  concedes this could be a lack of practice, "but I suspect it's something more fundamental."

**Verdict on textual macros:** "I don't recommend using textual macros in anything but the very
simplest cases." For *Templated Generation* they work acceptably, **provided you avoid trying to be
too clever with them — in particular, avoiding nesting the expansions.** Otherwise "they are simply
not worth the trouble."

**Verdict on syntactic macros:** most of the same reasoning applies. You're less likely to get
mistaken expansions, "but the other problems still crop up. This makes me very wary of them." As an
outsider to Lisp he is reluctant to judge too hard: "they do make sense for Lisp, but I'm not
convinced that the logic of using them there makes sense for other language environments."

**The practical shape of the decision:** most language environments don't support syntactic macros at
all, "so there's no choice to worry about." Where you do have them, "they are often necessary to do
useful things, so you have to become at least a little familiar with them." **The choice on using
syntactic macros is really made for you by your language environment.** The only genuine choice left
is whether macros are a reason to *choose* a language: "For the moment, I see macros as a worse choice
than available alternatives, and thus a point deducted from those environments that use them" —
explicitly hedged.

#### Relationships

- **Templated Generation** — the only use Fowler blesses for textual macros.
- **Textual Polishing (Ch. 45)** — the simplest substitution cases can just be search-and-replace;
  Fowler calls polishing "a simple application of textual Macros, with all the corresponding problems."
- **Closure (Ch. 37) / Nested Closure (Ch. 38)** — the *preferred alternative* for the
  deferred-evaluation use case that motivates most Lisp macros.
- **Parse Tree Manipulation (Ch. 43)** — the other Lisp-macro use case.
- **Nested Function (Ch. 34)** — what makes Lisp code parse-tree-shaped in the first place.

> **SDK lens:** Three rules fall out. (1) **Prefer closures over macros or codegen for deferred
> evaluation.** Execute-around, resource scoping, retry wrappers, transaction blocks, instrumentation
> spans — all of these should be higher-order functions taking a callback, not generated code.
> Fowler's strongest claim is that most macro usage compensates for poor closure syntax; if your
> language has terse lambdas, you already have the feature. (2) **"Leaks like a sieve without the
> wires" is a general test for any metaprogramming feature you ship**: does the abstraction survive
> into the debugger, the stack trace, the type checker, and the IDE? If it disappears from downstream
> tooling, your users pay for it during every incident. (3) **Document evaluation cardinality
> explicitly** for any API that takes an expression or thunk and may run it zero, one, or many times —
> multiple evaluation and name capture generalize far beyond macros. And whatever generation you do
> permit, **don't nest it**; nesting is where reasoning collapses.

---

### Notification (Ch. 16)

> **Intent:** "Collects errors and other messages to report back to the caller." *(Ch. 16, intent
> line)*

#### The concept

You've carried out operations that made significant changes to an object model, and now you want to
check the result is valid. You initiate a validation command. You want the answer as a **simple
Boolean**, but if there *are* errors you want to know more — and in particular you want to know about
**all** the errors rather than having validation stop at the first one.

A Notification is an object that **collects errors**. When a check fails it adds an error to the
Notification. When the command finishes, it **returns the Notification**. The caller can then ask
whether everything was OK, and if not, delve into the errors.

#### How it works

- The basic form is simply **a collection of errors**. During the notified task you need the ability
  to add an error: as simple as a message string, or as involved as a structured error object.
- When the task is done, the Notification goes back to the caller, who invokes a **simple Boolean
  query method** to see if all is well, and interrogates further if not.
- **Getting the Notification to where errors happen.** It usually needs to be available to several
  methods in the model. Two options *(Ch. 16, "How It Works")*: pass it in as an argument — a
  **Collecting Parameter** *[beck-ip]* — or **stash it in a field** if there's an object corresponding
  to the task at hand (a validator object, a parse-helper object) that can own it for the duration.
- **Beyond errors.** The primary purpose is collecting errors, but it's sometimes useful to capture
  **warnings** and **informational messages** too. Fowler's definitions: an **error** indicates the
  requested command has *failed*; a **warning** occurs for something that doesn't fail but is still a
  matter of potential concern; an **informational message** is just potentially handy information.
- **"In many ways, a Notification is an object acting like a log file, so many of the features
  commonly found in logging can be useful here."** *(Ch. 16, "How It Works")* — severity levels,
  formatting, filtering, structured payloads, report rendering.

#### When to use it — the fail-fast vs. collect-all decision rule

The tradeoff is crisp *(Ch. 16, "When to Use It")*:

- Use a Notification "whenever there is a complicated operation that may trigger multiple errors and
  you don't want to fail at the first error."
- **"If you do want to fail at the first error, then you can simply throw an exception."** A
  Notification is what you use when you want to store multiple errors "to give the caller a fuller
  picture of what the request led to."

That is the entire decision rule, and it is refreshingly mechanical: *how many independent problems
can one invocation surface, and does the caller need to see them all before acting?* If the answer is
one, throw. If it's many — validating a document, a schema, a config file, a migration, a whole
populated Semantic Model — collect.

#### The layering argument

The second motivating situation is not about error handling at all. It is about layers *(Ch. 16,
"When to Use It")*:

> **When a user interface initiates an operation at a lower layer:** "The lower layer should not try
> to interact with the user interface directly, so a Notification makes an appropriate messenger."

The lower layer *reports*; it does not *present*. A Notification is the messenger across the layer
boundary — the alternative being that your model layer starts printing, logging at the user, or
reaching up into the presentation layer, which couples the two permanently and makes the lower layer
untestable and unusable in any other context.

#### Design decisions from the examples

**Simple Notification** *(Ch. 16, "A Very Simple Notification (C#)")* — errors stored as plain
strings. Two carry-away decisions:

- The add-error method takes a **format string plus arguments**, formatting internally. "Using a
  format string and parameters makes it a bit easier to use the notification to capture errors, as the
  client code doesn't need to build the format string." Push message assembly *into* the Notification
  so call sites stay one-liners.
- It provides both **`IsOK` and `HasErrors`** Boolean queries (deliberate redundancy so the caller can
  write whichever reads better), **and** an **`AssertOK()`** that throws if there are errors.
  *"Sometimes this fits the flow of usage better than using the Boolean check methods."* — **offer
  both a query-style and a throw-style consumption path** over the same collected data.

**Parsing Notification** *(Ch. 16, "Parsing Notification (Java)")* — more involved, and it accepts
specific *kinds* of error rather than strings:

- It lives in the parse helper, and at the end of the run, if there are errors, the whole parse fails
  with a **single exception carrying the accumulated report**. This is the **collect-then-fail-once**
  shape: gather everything during the operation, raise one well-populated failure at the boundary.
- It handles **two distinct error sources** and unifies them: errors from the parser generator itself
  (hooked by overriding the generator's error-reporting method, delegating to the default so standard
  behavior is preserved) and semantic errors detected by the translation code.
- **Internal structure:** the error list holds message *objects*, not strings, with a small class
  hierarchy — one wrapping the parser's recognition exception, one holding the offending token plus
  the formatted message. The base class exists essentially as a marker to make the generics work ("In
  time, I might add something to it, but for the moment a bare marker suffices"). **"By passing the
  token in, I'm able to provide better diagnostic information."**

**Fowler's closing design principle for the chapter:**

> "I think the most important point here is to build a Notification that makes the calling code as
> simple and compact as possible. Therefore, I pass all the relevant data to the Notification and let
> the Notification sort out how to compose error messages from this data." *(Ch. 16, "Parsing
> Notification (Java)")*

That is: **call sites hand over raw structured context (token, object, values); the Notification owns
formatting and presentation.** Not the reverse.

#### Relationships

- **Semantic Model (Ch. 11)** — validations over a populated model are the archetypal producer of
  Notifications, and Ch. 11 explicitly says validation belongs there and should run *before*
  interpretation or code generation.
- **Collecting Parameter *[beck-ip]*** — the mechanism for threading a Notification through many
  methods.
- **Parse Tree Manipulation (Ch. 43)** — its IMAP example accumulates validation errors in a
  Notification before throwing.

> **SDK lens:** Almost nothing here is DSL-specific. **Batch validation should collect, not fail
> fast.** Any API that validates a document, config, schema, request payload, or migration should
> return *all* the problems in one pass; returning one error at a time forces users into an
> infuriating fix-rerun loop. **Offer both consumption styles** over the same result — an `is_ok()`
> query for callers who want to branch, and an `assert_ok()`/`raise_for_status()` for callers who want
> an exception at their own boundary — and don't force the choice on them. **Structured messages beat
> strings:** carry location (line/column, JSON path, field name) and the offending value as data on the
> message object, and render human text only at the edge; this is what makes errors machine-consumable
> for IDE squiggles and CI annotations as well as readable. **Keep formatting out of call sites** so
> error-raising stays a single line and wording stays centrally changeable. And observe the **layering
> discipline**: a lower layer returns a Notification rather than printing or reaching into the
> presentation layer.

---

## 10. Fluent interface patterns — the grammar of an API

Part IV of the book covers internal DSL techniques, and Chapters 32–38 are its core: the ways you glue
DSL clauses together in a host language. Three ideas run through all of them and are worth stating up
front, because every pattern is judged against them.

**1. Fluent interface vs. command-query API.** Fowler explicitly names the *normal* style of API —
self-standing methods, each understandable on its own, obeying command-query separation — as a
**command-query API**, noting "it's so normal that we don't have a general name for it" *(Ch. 32,
opening)*. A **fluent interface** is a different animal: it is designed for readability of *the whole
expression*, and as a result "fluent interfaces lead to methods that make little sense individually,
and often violate the rules for good command-query APIs." Nearly every decision in this part is
downstream of that: fluent methods get license to break normal API rules, and the price of the license
is that they must be quarantined somewhere.

**2. Fluent API design *is* grammar design.** Fowler repeatedly reasons about which technique to use by
writing the production rule the clause must satisfy, in BNF-ish notation, then choosing the technique
that fits it. The full mapping appears in the synthesis subsection below. He also observes that the
tree of Expression Builders you end up with "really is a syntax tree for the DSL" *(Ch. 32, "How It
Works")*.

**3. Evaluation order is a first-class design variable.** Function Sequence and Method Chaining
evaluate left-to-right. Nested Function evaluates arguments *before* the enclosing call (inside-out).
Nested Closure lets the parent decide *when* — including before/after setup and teardown. Most of the
tradeoffs in this part reduce to which evaluation order you need.

---

### Expression Builder (Ch. 32)

> **Intent:** "An object, or family of objects, that provides a fluent interface over a normal
> command-query API." *(Ch. 32, intent)*

#### The concept

An Expression Builder is a *separate layer* whose only job is to host the fluent, DSL-flavored
methods and translate those calls into ordinary command-query calls on the underlying Semantic Model.
You keep two interfaces to your system: the normal one on your domain objects, and the fluent one on
the builders. Because the fluent one lives somewhere else, it is "clearly isolated, making it easier
to follow" *(Ch. 32, opening)*.

Why the isolation matters: fluent methods *are* strange. They return `this` from mutators (violating
command-query separation). They are named like queries but act like commands. They define separate
`First()` and `Third()` methods where a parameter would be better programming. In C# they may be
implemented as property *getters* that mutate. Fowler's own words about that last trick: it is
something he "would call extremely bad code" — "only acceptable when clearly placed in a fluent
context — again, I would confine this abomination to a securely fenced Expression Builder" *(Ch. 35,
"Chaining with Properties (C#)")*. **The Expression Builder is the fence.**

#### How it works

- Think of the builder as a **translation layer**: fluent interface in, command-query API out.
- It is "often a *Composite* [gof] using child Expression Builders to build subexpressions within an
  overall clause" *(Ch. 32, "How It Works")*.
- Its exact shape depends on which function-combination pattern supplies the fluent surface. With
  Method Chaining, it's a sequence of method calls each returning a builder. With Nested Function, the
  builder may be a superclass (Object Scoping) or a bag of static functions. Fowler declines to give
  general structural rules for that reason.
- **One vs. many builders** is "one of the most notable questions." Multiple builders form a tree that
  mirrors the DSL's syntax tree, and "the more complex the DSL, the more valuable a tree of Expression
  Builders is" *(Ch. 32, "How It Works")*.
- **The key structural tip:** have a well-defined Semantic Model whose objects have command-query
  interfaces and can be manipulated *without any DSL at all* — with at least some tests that touch
  only that interface. Builders are then tested by comparing the model objects they produce, inspected
  through direct command-query calls.

The multiple-builder mechanics are worth internalizing *(Ch. 32, "Using Multiple Builders for the
Calendar (Java)")*. If the model object is immutable, fluent calls have nowhere to write partial data,
so you must accumulate it somewhere. Option A is fields on a single top-level builder — i.e. Context
Variables. Option B, which Fowler prefers, is to give each subexpression its own child builder,
"essentially, using a Construction Builder." The parent holds a *list* of child builders; a call that
starts a new child creates it, registers it, and returns it so the chain continues on the child; the
child holds a back-pointer to the parent, because **the punctuation call that starts the *next* child
arrives at the child and must be forwarded upward**. A final `getContent()` on the parent walks all
children and materializes the entire Semantic Model at once — which is exactly what lets the model be
immutable.

#### When to use it

Fowler is unusually direct: **Expression Builder is a default.** "I consider Expression Builder a
default pattern — meaning I tend to use it pretty much all the time unless there's a good reason not
to" *(Ch. 32, "When to Use It")*.

The alternative is putting the fluent methods on the Semantic Model itself. His objections, in order
of weight:

1. **Separation of concerns (the main one).** It intermingles the API for *building* the model with
   the methods that *run* it. Both are usually substantial: execution logic often requires an
   alternative computational model to understand; fluent interfaces have their own logic to maintain
   flow. "It's easier to understand if we separate building logic from execution logic."
2. **Unfamiliarity.** Mixing fluent and command-query methods on one class mixes two ways of
   representing an API, and because fluent APIs are rarer, developers are less familiar with them,
   "exacerbat[ing] the situation."

The best argument *against*: when the Semantic Model's execution logic is very simple, mixing building
into it adds little complexity. Fowler notes people combine the two frequently — partly from
unawareness of the pattern, partly from unwillingness to add classes — and states his bias plainly: "I
prefer lots of little classes to a few big classes, so my fundamental design philosophy encourages me
to use Expression Builder."

The calendar example makes the cost concrete *(Ch. 32, "A Fluent Calendar with and without a Builder
(Java)")*. Without a builder, fluent methods sit oddly next to genuine queries on the domain class.
Worse: if anyone needs to modify an event *outside* the DSL context, you must *also* supply normal
command-query mutators — so the class ends up carrying two overlapping mutation APIs, and using the
fluent one outside its intended context "would lead to hard-to-read code."

#### Relationships

- Supplies the object that **Method Chaining (Ch. 35)** chains on and the class that **Object Scoping
  (Ch. 36)** scopes to.
- Hosts **Context Variables (Ch. 13)**, keeping parse state out of global/static space.
- Uses **Construction Builder (Ch. 14)** for subexpression data — same object sometimes, different
  concept always.
- Produces the **Semantic Model (Ch. 11)**, which must remain independently usable.
- Multiple Expression Builders ≈ the DSL's syntax tree.

> **SDK lens:** This is *the* foundational SDK-design pattern in the book. Keep the ergonomic/fluent
> surface in dedicated builder types and keep your resource/response/domain objects plain,
> inspectable, and conventional — users hold the domain objects at runtime and should never encounter
> a mutator that returns `this` or a getter that mutates. Make the plain API complete enough that the
> SDK is fully usable without the fluent sugar, and **prove it with tests that touch only the plain
> API**; that's both an architectural constraint and a regression guard against features becoming
> reachable only through the DSL. Model the builder tree on the shape of the *configuration grammar*,
> not on your class hierarchy — one builder per nesting level is the norm for anything non-trivial.
> And note the immutability corollary: immutable model objects and fluent building are compatible only
> if you buffer in builders and construct at the end, which is the direct justification for
> `build()`-style terminal methods in immutable-first SDKs.

---

### Function Sequence (Ch. 33)

> **Intent:** "A combination of function calls as a sequence of statements." *(Ch. 33, intent)*

#### The concept

The simplest combination: a flat run of statements, one call per line. Crucially, "there is no data
relationship between them" *(Ch. 33, "How It Works")* — the calls are related only by their order in
time. Any structure the DSL *appears* to have (nesting, "this size belongs to that disk") is **not in
the code**; it must be reconstructed by the builder from accumulated parse state. Hence: "a heavy use
of Function Sequence means you use a lot of Context Variables."

```
computer()
  processor()
    cores(2)
    speed(2500)
```

Fowler is explicit that the indentation above is a lie in the technical sense: "that's just arbitrary
use of whitespace. The script is really just a sequence of function calls with no deeper relationship
between them. The deeper relationship is built up entirely using Context Variables" *(Ch. 33, "Simple
Computer Configuration (Java)")*.

#### How it works

- For readability you want **bare** function calls — no receiver prefix. The obvious way is global
  functions, which brings two problems: global visibility and static parse data.
- **Global visibility**: mitigate with whatever namespacing the language has, to narrow the scope of
  the calls down to the Expression Builder. In languages with no global-function mechanism at all
  you're stuck writing class-qualified calls, "which often adds noise to the DSL."
- **Static parse data** is the worse problem, and Fowler singles it out: "Static data is often a
  problem because you can never be entirely sure who is using it — particularly with multithreading.
  This problem is particularly pernicious with Function Sequence because you need a lot of Context
  Variables to make it work" *(Ch. 33, "How It Works")*.
- **Object Scoping fixes both.** It hosts the functions on a class in the natural OO way and gives you
  an instance to put parse data in. His recommendation: "I suggest using Object Scoping if you are
  using Function Sequence in all but the very simplest cases."

The most instructive detail in the worked example is that **`speed()` is ambiguous** — it could mean
processor speed or disk speed, so it must branch on which context variable is currently set and throw
if neither is *(Ch. 33, "Simple Computer Configuration (Java)")*. This is the direct, visible cost of
"no data relationship between calls": clause-name resolution becomes runtime state inspection, and
illegal scripts fail at runtime rather than at compile time.

#### When to use it

The bluntest verdict in the part: "On the whole, Function Sequence is the least useful of the function
call combinations to use for DSLs. Using Context Variables to keep track of where you are in a parse is
always awkward, leading to code that's hard to understand and easy to get wrong" *(Ch. 33, "When to Use
It")*.

Where it *is* reasonable:

- **At the top level of a language**, or at the top level inside a Nested Closure, where the DSL is a
  list of high-level statements. There you only need a single result list and one Context Variable —
  the cost stays bounded. Below that level, form expressions with Nested Function or Method Chaining.
- **Because you have to start somehow.** "Perhaps the biggest reason to use Function Sequence is that
  you always have to start your DSL with something, and that something has to be a Function Sequence
  even if there's only one call in the sequence. This is because all the other function call techniques
  require some kind of context."
- Alternative for the simple case: a Function Sequence is a list of elements, so **Literal List
  (Ch. 39)** is the obvious substitute.

#### Relationships

- **Requires** Context Variables; **should** use Object Scoping; uses Construction Builder for the
  accumulated pieces.
- Alternative: Literal List.
- Dramatically improved by wrapping in a **Nested Closure (Ch. 38)**, which lets the parent create the
  Context Variable just before the sequence and tear it down just after.

> **SDK lens:** This is the imperative "statement-style" configuration API — `client.setRegion(...);
> client.setRetries(...);` or, worse, a sequence of top-level calls that implicitly mutate shared
> session state. If your SDK's surface relies on hidden mutable state to answer "which thing am I
> configuring right now?", you are in Function Sequence territory and you inherit its costs:
> thread-safety hazards, order-dependence, ambiguous method names that must dispatch on state, and
> errors surfacing at runtime. **Static/global parse state is the specific thing to refuse** — bind
> state to an instance. The legitimate uses map cleanly: a top-level sequence of independent
> operations is fine; expressing *nested* configuration this way is not.

---

### Nested Function (Ch. 34)

> **Intent:** "Compose functions by nesting function calls as arguments of other calls." *(Ch. 34,
> intent)*

#### The concept

Each clause's subelements are literally the arguments of its function call:

```
computer(processor(cores(2), speed(2500), i386),
         disk(size(150)),
         disk(size(75), speed(7200), SATA))
```

The hierarchy of the DSL becomes the hierarchy of the host language's expression tree. Fowler's
framing: "By representing a DSL clause as a Nested Function, you're able to reflect the hierarchic
nature of the language in a way that's mirrored in the host language, not just in a formatting
convention" *(Ch. 34, "How It Works")*. **The structure is real, not indentation.**

#### How it works

**Evaluation order is the defining property.** "Function Sequence and Method Chaining both evaluate the
functions in a left-to-right sequence. Nested Function evaluates the arguments of a function before the
enclosing function itself." Fowler's mnemonic is the **Old MacDonald problem**: to sing the chorus you
type the vowels inside-out. "This evaluation order has an impact on both how to use Nested Function and
when to choose it instead of alternatives" *(Ch. 34, "How It Works")*.

Three consequences of arguments-first:

- **A built-in context to work with the arguments.** Argument functions return fully formed values that
  the enclosing function assembles into its return value.
- **No finishing problem** (unlike Method Chaining) — the closing bracket of the outermost call *is* the
  end, and that call naturally returns the finished object.
- **No Context Variable needed** (unlike Function Sequence) — the data flows through return values.

**Fit to grammar.** "With mandatory elements in the grammar, along the lines of `parent ::= first
second`, Nested Function works particularly well. A parent function can define exactly the arguments
required in the child functions and, with a statically typed language, can also define the return
types, which enables IDE autocompletion."

**Labeling arguments.** `disk(150, 7200)` is unreadable — "there's no indication what the numbers mean,
unless you have a language with keyword arguments." The fix is a wrapping function that exists only to
name the value: `disk(size(150), speed(7200))`. In its simplest form the wrapper returns its argument
unchanged, "representing pure syntactic sugar." But sugar has a cost: **no enforcement** — "a call to
`disk(speed(7200), size(150))` could easily result in a very slow disk." The fix is to have the nested
functions return intermediate data — a builder or a token — so the type system carries the meaning, at
the cost of more setup.

**Optional arguments.** Use the language's default arguments if it has them. Otherwise define a
different function per combination — "tedious but reasonable" for a couple, but "as the number of
optional arguments increases, so does the tediousness (but not the reasonableness)." Intermediate
data/tokens are one escape; **Literal Map (Ch. 40)** is the cleanest, "the only problem is that C-like
languages don't usually support Literal Map."

**Multiple arguments of the same kind.** Varargs is best where supported; "You can also think of this
as a nested Literal List."

**The worst case.** "The worst case of this is a grammar like `parent ::= (this | that)*`." Without
keyword arguments, the only identification available is position and type — "messy, and downright
impossible if `this` and `that` have the same types." You are forced into returning intermediate
results or into a Context Variable, and the Context Variable route is "particularly difficult here
since the parent function isn't evaluated till the end, forcing you to use the broader context of the
language to properly set up the Context Variable."

**Bare calls: an important asymmetry.** Same question as always — global functions or Object Scoping —
but "global functions can often be much less problematic in Nested Function, because the biggest
problem with global functions is when they come with a global parsing state. A global function that
just returns a value, such as a static method like `DayOfWeek.MONDAY`, is often a good choice." Nested
Function usually needs no parse state, so the danger largely evaporates *(Ch. 34, "How It Works")*.

**Tokens and subtype tokens.** The escape from the worst case is to have every nested function return a
**token** object carrying a type tag plus a value; the parent takes a varargs of tokens, iterates, and
dispatches on the tag *(Ch. 34, "Handling Multiple Different Arguments with Tokens (C#)")*. Tokens
convert "which argument is this?" from a *positional* question into a *data* question, buying arbitrary
ordering and optionality at the cost of a token type and a dispatch switch.

The refinement is sharper *(Ch. 34, "Using Subtype Tokens for IDE Support (Java)")*: "Checking is all
very well, but in a statically typed language with a modern IDE, you want to go further. You want
autocompletion popups to force you to put size before speed. By using subclasses, you can pull this
off." Define a **subtype per clause** — `SizeToken`, `SpeedToken` — so the parent's signature is
`disk(SizeToken, SpeedToken)`; the compiler enforces the right token in the right position and
autocompletion suggests the right function in the right place. This is the Nested Function analogue of
**progressive interfaces** in Method Chaining: encoding grammar constraints in the type system so the
IDE teaches the language.

A useful reframing from the same chapter: C#'s object initializers "can be thought of as Nested
Functions that can take keyword arguments (like a Literal Map) which are restricted to object
construction" *(Ch. 34, "Using Object Initializers (C#)")*.

#### When to use it

- **The strength and the weakness are the same thing: evaluation order.** Arguments-first "is very
  useful for building up a hierarchy of values because you can have the arguments create fully formed
  model objects to be assembled by the parent function. This can avoid much of the mucking about with
  replacements and intermediate data that you get with Function Sequence and Method Chaining."
- **Conversely, it's wrong for command sequences.** "This evaluation order causes problems in a
  sequence of commands, leading to the Old MacDonald problem… So, for a sequence that you want to read
  from left to right, Function Sequence or Method Chaining are usually a better bet. For precise
  control of when to evaluate multiple arguments, use Nested Closure."
- **Weak on optionality and variety.** "Nested Function very much expects you to say what you want and
  in the precise order you want it. If you need greater flexibility you'll need to look to Method
  Chaining or a Literal Map." Literal Map is singled out because "it allows you to get the arguments
  sorted out before calling the parent while giving you the flexibility of ordering and optionality of
  the arguments."
- **Punctuation is the aesthetic cost.** It "usually relies on matching brackets and putting commas in
  the right place. At its worst, this can look like a disfigured Lisp, with all the parentheses and
  added warts. This is less of an issue for DSLs aimed at programmers, who get more used to these
  warts."
- **Name clashes are *less* trouble than with Function Sequence**, "since the parent function provides
  the context to interpret the nested function call. As a result, you can happily use 'speed' for
  processor speed and disk speed and use the same function as long as the types are compatible."
- Cross-reference from Ch. 35: "Nested Function is the better choice for mandatory clauses."

Two design lessons from the recurring-events example are worth keeping even though they're about
another topic *(Ch. 34, "Recurring Events (C#)")*. First, **the DSL can read *opposite* to the model**:
"We say 'first and third Monday' in our language, but in terms of the specification, it's the first
*or* third Monday that matches the Boolean condition. It's an interesting example of where the DSL is
opposite to the model in order for both to read naturally." The fluent layer's job is to read naturally
to the domain reader, not to mirror the model's structure. Second, **name for the reader of the
script**: Fowler named an Expression Builder `Schedule` rather than `ScheduleBuilder` "because I think
it reads better as just 'schedule.'"

#### Relationships

- Opposes Function Sequence / Method Chaining on evaluation order.
- Complemented by **Literal List (Ch. 39)** (varargs), **Literal Map (Ch. 40)** (optionality +
  ordering), **Nested Closure (Ch. 38)** (control of *when* arguments evaluate), **Object Scoping
  (Ch. 36)** (bare calls), **Expression Builder (Ch. 32)** (where the functions live).
- Tokens / subtype tokens are its type-system mechanism; progressive interfaces are the Method Chaining
  equivalent.

> **SDK lens:** This is the "constructor / nested options-object" style, and the only technique in the
> set that can *require* things. **Required parameters and structural hierarchy belong here** — if your
> SDK has parameters that must be present, they belong in the function signature, not in chainable
> setters, which can always be omitted. Sugar wrappers that only label a value improve readability but
> enforce nothing; typed wrappers enforce *and* drive autocomplete — that's the exact tradeoff behind
> newtype/branded-type parameters in modern SDKs. The crucial judgement is the **degradation curve**:
> Nested Function is excellent for a fixed mandatory shape and gets *worse the more optional settings
> you add* — combinatorial overloads, positional ambiguity, unordered heterogeneous arguments. That's
> precisely the region where builders, keyword arguments, and option maps win, and knowing where the
> crossover sits is most of the skill. Practical rule: prefer keyword arguments / options objects
> wherever the host language has them; they give you optionality, ordering freedom, and named arguments
> in one move, and remove the need for tokens entirely.

---

### Method Chaining (Ch. 35)

> **Intent:** "Make modifier methods return the host object, so that multiple modifiers can be invoked
> in a single expression." *(Ch. 35, intent)*

#### The concept

Rather than three separate setter statements, write `new HardDrive().capacity(150).external().speed(7200)`.
Each modifier returns an object — usually itself — so the next call can continue the chain.

Fowler opens with a corrective worth quoting: "Method Chaining rapidly caught on amongst people as an
example of what an internal DSL should look like. It caught on a bit too much — people started to assume
that Method Chaining was synonymous with fluent interfaces and internal DSLs. My view is that Method
Chaining is one of several techniques, but it's still valuable and noticeable" *(Ch. 35, "How It Works")*.

#### How it works

- Mechanically trivial: the modifier returns `this` (or another object) instead of `void`.
- **It breaks command-query separation, knowingly.** "Returning a value from a modifying method breaks
  the principle of command-query separation. Most of the time I follow that principle, and it's served
  me well. A fluent interface is one case when we need to break it."
- **It breaks naming conventions too.** "A method like `sata()` would seem like a query, not a modifier.
  This naming is very problematic, as it will seriously confuse anyone who is expecting a command-query
  API. Taken together, Method Chaining violates many common rules of common (command-query) API design."
  Two independent reasons to fence it inside an Expression Builder.
- **It changes formatting conventions.** Long chains read badly on one line, "particularly if we want to
  suggest a hierarchy," so put each call on its own line. Practical bonus: "Putting methods on separate
  lines also makes debugging easier, as error messages and debugger control usually work on a
  line-by-line basis. Therefore, it's wise to do less on each line."
- **Why constructors aren't the answer.** "DSLs are often about building up configurations of objects,
  and doing so in constructors is often tricky. It's also usually difficult to read, since constructors
  often allow only positional parameters."

**Builders or values.** Fowler's preference is chaining on Expression Builders, "since that reduces the
confusion between the conventions of fluent and command-query APIs." The alternative is chaining on
domain types — `42.grams.flour`, where each step returns a different Value Object, which Neal Ford calls
**type transmogrification**. Fowler is explicitly non-dogmatic: "There are plenty of good developers who
are comfortable with using Method Chaining on domain types like this, so I'm cautious about arguing
against it. My inclination, however, leads me to prefer using Expression Builders as much as possible,
to clearly separate command-query and fluent API styles" *(Ch. 35, "Builders or Values")*.

#### The finishing problem

This is Method Chaining's signature weakness and the most SDK-relevant idea in the chapter *(Ch. 35,
"Finishing Problem")*.

- "It boils down to the lack of a clear end-point to a method chain." Every method must return a builder
  to keep the chain alive, so nothing in the chain signals completion, and the value you actually want —
  the finished domain object — never appears.
- In Fowler's words: "I would like the returned value to be an `Appointment` object, since that would be
  the most natural usage. However, the need to continue the method chain means that each method has to
  return an appointment builder. There's nothing in the chain that tells me when I'm done, so I have to
  put in some kind of marker method to show the end."

The options, ranked:

1. **A natural last clause that returns the finished object.** From the progressive-interfaces example:
   "I have a natural stop method with `Body`, so I'll have that return the message." Best when the
   grammar genuinely has a terminal clause.
2. **An explicit finishing method** (`.end()`, `.build()`). "It isn't too bad, but the use of `End` is
   still a bit of syntactic noise."
3. **An implicit conversion operator** (C#) — "although that does mean you'll forgo `var` for an explicit
   type."
4. **Use a different pattern.** "This is where using Nested Function or Nested Closure can be a valuable
   alternative." Their enclosing call *is* the terminator.

Fowler also notes the ergonomic cost of *not* having a finisher: without one you must break the
expression into a builder statement plus a separate `getValue()` call — two statements and a named
variable *(Ch. 35, "The Simple Computer Configuration Example (Java)")*.

#### Hierarchic structure

- "Tied in with the finishing problem is the problem that Method Chaining doesn't naturally fit a
  hierarchic structure. Hierarchic structures are common in languages, which is why syntax trees are
  valuable for thinking about them" *(Ch. 35, "Hierarchic Structure")*.
- In a chained computer configuration, "There's a definite hierarchy to this, but it's suggested by the
  indentation and not captured in the structure of the code itself. As a result, we have to manage that
  structure ourselves. This problem also occurs with Function Sequence."

Two management strategies: **Context Variables**, or **a child builder per subelement**. The second half
of Fowler's note on child builders is the important part: "A separate builder allows us to limit the
methods available to only those required to provide the information for the disk or a finishing method."
A child builder isn't just data scoping, it's **grammar scoping**.

The worked example deliberately shows both sub-structure strategies side by side — a simple Construction
Builder held in a Context Variable for the processor, and a full delegating child builder for the disks
— and Fowler names the inconsistency and explains it: "A simple Construction Builder works better for
simple cases and full delegation works better for more complicated cases. I've shown both here for
pedagogical reasons, although I lean more to full delegation" *(Ch. 35, "The Simple Computer
Configuration Example (Java)")*. **Punctuation forwarding** recurs here too: a child builder must forward
calls that belong to the parent (starting a sibling, finishing the whole expression).

His summary judgment on the example is the balanced takeaway: "Method Chaining reads very clearly,
without much of the syntactic noise that can clutter Nested Function. However, to pull it off, I have to
do a lot of fiddling around with Context Variables and cope with the finishing problem."

#### Progressive interfaces — type-encoded grammars

The chapter's most important technique for SDK design *(Ch. 35, "Progressive Interfaces")*.

- "A valuable variation to the basic Method Chaining approach is to use multiple interfaces to drive a
  fixed sequence of method-chaining calls."
- The email example forces destination, then Cc's, then subject, then body. You present a *sequence of
  interfaces* over the one Expression Builder: the first exposes only `to`; `to` returns an interface
  exposing only the legal next steps (`to`, `cc`, `subject`); `cc` returns one with only `cc` and
  `subject`; `subject` returns one with only `body`.
- Implementation: the builder implements all the interfaces; each method still returns `this`, but
  *typed as the next interface*. Interfaces can inherit from each other so a later stage picks up an
  earlier stage's legal steps without duplicating declarations.
- **Payoff:** "This can work really well in a statically typed language with IDE support. Autocompletion
  in the IDE can step you through each clause in the DSL by only suggesting the methods that are valid
  for that point in the chain." Honest caveat: "it's not perfect, as methods inherited from `Object`
  also show up."
- **Relationship to child builders:** "This ability to control which methods are valid in which contexts
  is similar to that you get by using a child builder. Indeed, you can use a child builder to do the
  same thing as progressive interfaces, but progressive interfaces are easier if there's no other reason
  to make a child builder."
- **Mandatory elements:** "Progressive interfaces can be used to enforce mandatory elements in a chain;
  for this, define an interface that only takes a single mandatory element."

#### When to use it

- "Method Chaining can add a great deal to the readability of an internal DSL and, as a result, has
  become almost a synonym for internal DSLs in some minds. Method Chaining is best, however, when it's
  used in conjunction with other function combinations" *(Ch. 35, "When to Use It")*.
- **Best for optional clauses.** "Method Chaining works best when using optional clauses in a language.
  Method Chaining easily allows a DSL script writer to pick and choose clauses needed for a particular
  situation. It's difficult to specify in the language that certain clauses must be present. Using
  progressive interfaces allows some ordering of clauses, but in the end clauses can always be left out.
  Nested Function is the better choice for mandatory clauses."
- **Escape hatches.** "The finishing problem crops up from time to time. While there are workarounds,
  usually if you run into this you're better off using a Nested Function or Nested Closure. These
  alternatives are also better choices if you are getting into a mess with Context Variables."

#### Relationships

- Usually hosted on an **Expression Builder**; can be hosted on Value Objects (with **Literal Extension,
  Ch. 46**).
- Needs **Context Variables** and/or child builders for hierarchy.
- Progressive interfaces ≈ subtype tokens (Ch. 34) — both encode grammar in types.
- **Nested Function / Nested Closure** are the recommended escapes from the finishing problem and from
  Context Variable messes.

> **SDK lens:** The highest-density SDK chapter in the book. **The finishing problem is the everyday
> `.build()` question**, and Fowler's ranking translates directly: a natural terminal clause that
> returns the finished object (best), an explicit `build()`/`end()` (acceptable, noisy), an implicit
> conversion (language-specific, costs type inference), or restructure to a function/callback form where
> the enclosing call terminates (often the real answer). **Progressive interfaces are the type-state
> pattern**: returning a narrower interface from each step makes illegal call sequences fail at
> *compile* time and turns IDE autocomplete into documentation — the user is shown only what is legal
> next. That's how modern SDKs enforce "you must set auth before you can send." **Chaining cannot
> express requirement** — required inputs belong in the factory/constructor; chained setters are for
> genuinely optional configuration. **Chain on builders, not on the objects users keep**, or fluent
> conventions leak into types users inspect at runtime. **Hierarchy needs child builders, not
> indentation** — and a child builder must forward the parent's punctuation, or users hit surprising
> "method not found" errors mid-chain. Finally, **formatting is API design**: one call per line isn't
> style, it's what makes stack traces and debugger stepping point at the failing clause.

---

### Object Scoping (Ch. 36)

> **Intent:** "Place the DSL script so that bare references will resolve to a single object." *(Ch. 36,
> intent)*

#### The concept

Nested Function and, to a lesser extent, Function Sequence want *bare* calls — no receiver — for
readability, "but in their basic forms they come with a serious cost: global functions and (worse)
global state" *(Ch. 36, opening)*. Object Scoping removes both by resolving all bare calls against a
single host object: "this avoids cluttering the global namespace with global functions, allowing you to
store any parsing data within the host object. The most common way to do this is to write the DSL script
inside a subclass of a builder that defines the functions."

#### How it works

- "One of the many useful properties of objects is that each object provides a contained scope for
  functions and data. Inheritance allows you to use this scope separately from where it's defined"
  *(Ch. 36, "How It Works")*. So: define the DSL functions on a base class; write DSL programs in
  subclasses. The base class also holds fields for parse data.
- That base class is the natural home of the **Expression Builder**. Clients write DSL programs in a
  subclass of it — "Using inheritance allows them to add other DSL functions in the subclass, or even
  override base functions in the DSL object if they need to."
- **Alternatives to inheritance:** Ruby's **instance evaluation** (`instance_eval`) — "the facility to
  take any program code and execute it within the context of a particular object. This allows a DSL
  writer to write the DSL text without declaring any links to the base class that defines the language"
  — and Java's **instance initializers** (the double-brace idiom), "not well known nor often used, but
  can work well for this case."

The instance-evaluation version has a further capability worth noting: **scope switching down the tree**.
By instance-evaluating *child* builders for nested clauses, the same bare name binds to different
builders at different depths — "This mechanism allows me to handle calls to methods like `gradeAtLeast`
differently in different parts of the DSL" *(Ch. 36, "Using Instance Evaluation (Ruby)")*. That is how
you get multiple Expression Builders *and* bare calls simultaneously.

#### When to use it

- "Object Scoping solves the niggly problems of globalness within Nested Function and Function Sequence
  and as such is always worth considering… Not only does this avoid messing with a global namespace, it
  also allows you to store parsing data in an Expression Builder. I find these advantages quite
  compelling, and thus would always suggest using Object Scoping if you can" *(Ch. 36, "When to Use It")*.

Where you can't, or shouldn't:

- **It requires an OO language.**
- **It constrains where the script can live.** "With the most common inheritance case, it means you must
  put the DSL script within a method in a subclass of an Expression Builder. This isn't too much of a
  problem for self-contained DSL scripts. Such scripts often sit in their own file and are well-separated
  from other code."
- **The real problem is fragmentary DSLs.** "The real problem is with fragmentary DSLs, where using
  Object Scoping forces you into an inheritance relationship that may be awkward or even impossible."
  This **self-contained vs. fragmentary** distinction recurs in Ch. 38 and is one of the most transferable
  ideas in Part IV.
- **Sometimes globals are fine and you don't need it.** "Object Scoping is mostly an antidote to global
  functions, so it's worth remembering that the biggest problems of global functions come with modifying
  global data. A common case where you don't get this problem is when the global function just creates
  and returns a new object… If you can arrange your bare functions to be like this, then there is much
  less need for Object Scoping."
- **Extensibility bonus.** "If the DSL framework is set up to allow a user of the DSL to substitute their
  own subclass of the scoping class for Object Scoping, this also makes the DSL more extensible. A user
  subclass can add more methods to extend the language. Indeed if particular methods are only needed in
  one script, then that script subclass can define those methods directly."

#### "DSL surface deliberately less expressive than the model"

The most important design lesson in the chapter is not about scoping at all *(Ch. 36, "Security Codes
(C#)")*. The security-zone model allows arbitrary Boolean expressions, but the DSL doesn't: "Although the
underlying model allows arbitrary Boolean expressions, the DSL is simpler. Each admission rule is a
conjunction ('and') of its clauses. This is why I need separate refuse statements for the two
departments." And then the general principle:

> "Arbitrary Boolean expressions are powerful, but often difficult for people, particularly non-nerds, to
> follow. So some form of simplified structure can be handy in a DSL."

**Deliberately make the language surface less expressive than the model when that makes it easier to get
right.** The model keeps the full power for programmatic users and for future language growth; the DSL
exposes the subset domain experts can reliably reason about.

The same example also contains a small but instructive lesson about **where boilerplate lives**. Fowler
passes the target object in via a separate build method rather than a constructor, because a constructor
"would force me to add a constructor declaration to the subclass" — i.e. push boilerplate off the *user's*
class and onto the library's. "It's a small thing, but saves me a bit of noise in the DSL text. These
small things add up." He is also honest about the cost of the pattern: "Object Scoping does help in
reducing noise in the DSL, but one problem is that it does introduce noise in the code that declares the
DSL class."

#### Relationships

- Enables bare calls for **Function Sequence** and **Nested Function**; hosts the **Expression Builder**
  and its **Context Variables**.
- Relevant to **Nested Closure (Ch. 38)**, where bare functions inside a closure otherwise resolve in the
  closure's *defining* scope.
- `instance_eval` connects it to **Closure**, **Nested Closure**, and **Dynamic Reception (Ch. 41)**.

> **SDK lens:** This is the "configuration block / DSL block" family — Gradle build files, RSpec, JMock,
> Rails initializers, Kotlin receiver lambdas. It answers a real SDK question: how do you give users terse
> unqualified vocabulary without a global namespace and without global mutable state? Answer: bind the
> vocabulary to an instance and put the user's code inside that instance's scope. **The self-contained vs.
> fragmentary axis is the decision rule** — a standalone configuration file can afford (and benefits from)
> an implicit receiver; a few lines of SDK usage embedded in ordinary application code should not force an
> inheritance relationship or a rebound `this`. **Extensibility falls out for free**: user subclasses of
> the scoping base class extend the language, which maps directly to plugin and extension points,
> including "define a helper only this one config file needs." **Push boilerplate onto the library, not the
> user** — every declaration you force into user code is noise paid on every use site. And **the
> simplified-Boolean lesson generalizes hard**: your SDK's configuration surface does not have to expose
> every combination the model supports; constraining the surface trades expressiveness for a language
> people get right on the first try.

---

### Closure (Ch. 37)

> **Intent:** "A block of code that can be represented as an object (or first-class data structure) and
> placed seamlessly into the flow of code by allowing it to reference its lexical scope." *(Ch. 37,
> intent)*
>
> **Also known as:** lambda, block, anonymous function. *(Ch. 37, "Also known as")*

#### The concept

The motivating problem stated in the pattern header: "You have a collection of objects and want to filter
them in various ways. Writing a method for each filter leads to duplication in the setup and processing of
the filter. By using a Closure, you can factor the setup and processing of the filter and pass in an
arbitrary block of code for each filter condition."

Fowler's working definition: **"A Closure is a code fragment that can be treated as an object."** *(Ch. 37,
"How It Works")*

He develops it from the duplication problem. Two loops — one collecting heavy travelers, one collecting
managers — differ only in a Boolean test. "Removing that duplication is a simple thing to envisage, but
difficult to write in many languages because the thing that varies between the two code fragments is a
chunk of behavior — which is often not easy to parametrize." The classical OO answer is to make the
behavior an object: a filter interface plus a class per predicate. It works, but "there's so much code in
setting up the predicate object that the cure is worse than the disease" — especially when the predicate
needs a parameter, forcing a constructor and a field just to carry a threshold.

#### How it works

- **Terminology is a mess and Fowler says so.** "I use the term Closure in this book, but naturally there
  is no standard term for this language element. You also see them referred to as lambdas, anonymous
  functions, and blocks. Each language that uses them usually has its own term for them."
- **What makes it a closure specifically:** the block simply *uses* a local variable from the enclosing
  scope — "which saves all the faffing around with parameters that the predicate object version needed.
  This reference to variables in scope is what formally makes this expression a Closure. The delegate is
  said to close over the lexical scope of where it's defined. Even if we take the delegate and store it
  somewhere for later execution, those variables are still visible and usable… Both the theory and
  implementation of this are quite tricky — but the result is very natural to use."
- **Terseness is the whole ballgame.** Tracing C#'s evolution from handwritten predicate class to anonymous
  delegates to lambdas with type inference, he concludes: "You'll notice there's really little change here —
  the main factor is that the syntax is much more compact. This may be a small difference but it's a vital
  one. **The usefulness of Closures is directly proportional to how terse they are to use.**"
- **The libraries have to cooperate.** "This is an important point — for Closures to be really useful in a
  language, the libraries need to be written with Closures in mind." A language-level feature is worth
  little if the standard library predates it.
- **Deferred evaluation.** A closure created inside a factory function, capturing that function's
  parameter, can be stored in a field and evaluated arbitrarily later and arbitrarily often. "**This
  ability to create a block of code for later execution is what makes Closures so useful for Adaptive
  Models.**"
- **Language limits shape the API.** Ruby's pretty block syntax can only pass *one* closure into a
  function; passing multiple requires a less elegant syntax.

#### When to use it

Framed at two levels *(Ch. 37, "When to Use It")*:

- **General programming:** "Like many programmers who have used languages with good support for Closures, I
  find I miss them a great deal when using a language without them. They are a valuable tool to take chunks
  of logic and arrange them to eliminate duplication and support custom control structures."
- **In DSLs specifically:** "Closures play a couple of useful roles in DSLs. Most obviously, they are an
  essential element for Nested Closure. They also can make it easier to define an Adaptive Model."

#### Relationships

- Prerequisite for **Nested Closure (Ch. 38)**.
- Enables **Adaptive Model** — behavior held as data in the semantic model, evaluated later.
- The **preferred alternative to Macro (Ch. 15)** for deferred evaluation.
- Interacts with **Object Scoping** in languages that can rebind a closure's execution context.

> **SDK lens:** Callbacks, handlers, predicates, and interceptors as first-class parameters are the single
> most common way SDKs let users inject behavior. Two uses dominate. **Custom control structures**: the SDK
> owns setup and teardown, the user supplies the middle — retry policies, transactions, connection scoping,
> resource lifetimes, instrumentation spans. This is the mechanism behind context-manager-shaped APIs.
> **Deferred/lazy evaluation**: accepting a closure rather than a value lets the SDK decide *whether* and
> *how many times* to evaluate — essential for retries, lazy config, conditional expensive computation, and
> rule engines. Two constraints worth carrying: (1) a closure-taking API is only pleasant if the host
> language's closure syntax is terse, which is a legitimate reason for language-specific SDK surfaces to
> differ; (2) your *whole library* must be designed for closures, not just one entry point, or users get a
> fluent island in an imperative sea.

---

### Nested Closure (Ch. 38)

> **Intent:** "Express statement subelements of a function call by putting them into a closure in an
> argument." *(Ch. 38, intent)*

#### The concept

Nested Closure is Nested Function with the children wrapped in a closure. Fowler's minimal contrast
*(Ch. 38, "How It Works")*:

```
processor(cores(2), i386)        # Nested Function
processor { cores 2; i386 }      # Nested Closure
```

"Instead of passing two Nested Function arguments, I pass a single Nested Closure argument which contains
the two Nested Functions."

#### How it works

**The central mechanic: you control evaluation.** "Placing the subelements in a Nested Closure has an
immediate consequence for my implementation — I have to put in code to evaluate the closure. With a Nested
Function, I don't need to do this since the language automatically evaluates the `cores` and `i386`
functions before calling the `processor` function. With a closure argument, the `processor` function is
called first and the closure is only evaluated when I explicitly program it to. So, usually I'll evaluate
the closure within the body of the `processor` function. **The `processor` function can also carry out
other tasks before and after the closure evaluation, such as setting up Context Variables**" *(Ch. 38,
"How It Works")*.

That before/after capability is the whole value proposition, and its most important application is stated
immediately:

> "One of the problems of a Function Sequence is that the multiple functions communicate using hidden
> Context Variables. While you still have to do this inside a Nested Closure, the `processor` function can
> create the Context Variable before evaluating the closure and tear it down afterwards. This can greatly
> reduce the problem of Context Variables appearing all over the place." *(Ch. 38, "How It Works")*

**What can go inside the closure** — three shapes:

1. **Function Sequence** — the base case; the parent brackets it with Context Variable setup/teardown.
2. **Method Chaining** — "Here, there is the additional benefit that the parent function can set up the
   head of the chain and pass it into the closure as an argument."
3. **Function Sequence with an explicit Context Variable passed as the closure argument** — "In this case,
   we have a Function Sequence but with the Context Variable explicitly present. This often makes it easier
   to follow, without adding too much clutter."

**Scoping.** "Bare functions written inside a Nested Closure are evaluated in the scope where they are
defined — so, again, it's usually wise to use Object Scoping. Passing in an explicit Context Variable or
using Method Chaining allows you to avoid this, as well as to organize the builder code into different
builders."

**Multiple closures.** "It's also possible to use multiple closures. The advantage of this is that it
allows you to evaluate each subclosure independently." The canonical case is a conditional with two
branches, where evaluating both would be wrong.

#### The delimiters are not noise

Fowler puts the Nested Closure script and the plain Function Sequence script side by side; they are
character-for-character identical except for the added closure delimiters *(Ch. 38, "Wrapping a Function
Sequence in a Nested Closure (Ruby)")*:

> "From the script's point of view, the only change with Nested Closure is to add the `do…end` closure
> delimiters. By adding these, I introduce an explicit hierarchic structure to what otherwise is a linear
> sequence with a formatting convention. The extra syntax doesn't strike me as troubling because it's
> marking the structure from the reader's point of view and in a way that makes sense to the reader."

This is the sharpest statement in the part of *why* structure-in-code beats structure-in-indentation: the
delimiters are the reader's own mental structure made real.

A concrete payoff of splitting into child builders inside closures: "it also allows me to use an unqualified
`speed` method for both the processor and the disk without ambiguity" *(Ch. 38, "Using Method Chaining
(Ruby)")*. Compare the Function Sequence version, where `speed()` had to branch on Context Variables to
decide what it meant. **Splitting into builders replaces runtime disambiguation with structural
disambiguation.**

Fowler is also candid that the pattern reads better in some languages than others: "To my eyes, Nested
Closure works much less well in C# than it did in Ruby. Ruby's `do…end` closure delimiters flow more
naturally to me than C#'s `() => {…}`… The more used you are to C# notation, the less that will bother you"
*(Ch. 38, "Simple C# Example (C#)")*.

#### Self-contained vs. fragmentary, and the instance_eval reversal

The chapter's best judgement call *(Ch. 38, "Using Instance Evaluation (Ruby)")*.

Instance evaluation lets you have multiple builders *and* bare calls: each clause method creates the child
builder and evaluates the block against it, so the same bare name means different things at different
depths. "In effect, using `instance_eval` changes what `self` refers to inside the passed-in block." For a
self-contained script file it also removes all the head/tail noise of Object Scoping.

It looks like a free win. It isn't:

> "Using `instance_eval` seems such a good trick that you may wonder if you should ever pass explicit
> closure arguments. As it turns out, there is a very real choice, one that was crystallized for me by Jim
> Weirich's experience with his builder library… In the first version of the library, Jim used
> `instance_eval`, but later switched to explicit parameters. The reason is that **programmers are used to
> the call behavior with closures; redefining `self` causes a lot of confusion and makes it very difficult
> to refer to elements in the static context that you need.**"

Fowler's resolution is the self-contained/fragmentary rule:

> "For me, the choice lies in whether you are using the DSL script in a self-contained or fragmentary
> style. In a fragmentary context, you need to follow the usual conventions with closures, so redefining
> `self` though `instance_eval` is not a good choice. With self-contained DSL scripts, your code style is
> different from regular Ruby code; the redefinition then doesn't cause confusion and is worth it to
> remove the noisy references."

The related tradeoff, stated by Fowler as what real Ruby DSLs actually do: they use Function Sequence
within each closure but pass an explicit closure argument. "Although this adds more text to the statement,
it results in a more regular style of code that rubyists find easier to work with" *(Ch. 38, "Function
Sequence with Explicit Closure Arguments (Ruby)")*. **Explicit receivers cost characters and buy
regularity, multiple builders, and fragmentary usability.**

#### When to use it

- The core claim: "Nested Closure is a useful technique because it combines the explicitly hierarchic
  structure of Nested Function with the ability to control when the arguments are evaluated. Control of
  evaluation provides you with a lot of flexibility, helping you to avoid many of the limitations of Nested
  Function" *(Ch. 38, "When to Use It")*.
- The core limitation is the host language: "Many languages don't provide closures at all. Those that do
  often provide the syntax in a way that doesn't jive terribly well with DSLs, such as with an awkward
  keyword."
- **Best mental model — it's an enhancement, not a rival:** "It's usually worth thinking of Nested Closure
  as an enhancement to Nested Function, Function Sequence, and Method Chaining. The explicit control of
  evaluation gives you different advantages with each technique. All of these, however, boil down to the
  fact that you can do specific setup and tear-down operations on either side of the closure invocations."

#### Relationships

- Built on **Closure (Ch. 37)**.
- An *enhancement* to **Nested Function**, **Function Sequence**, and **Method Chaining**, not a competitor.
- Tames **Context Variables** by scoping their lifetime to the closure invocation.
- Interacts with **Object Scoping**: needed for bare calls inside closures, or bypassed via explicit closure
  arguments.
- Solves Method Chaining's **finishing problem** (the enclosing call terminates) and Function Sequence's
  Context Variable sprawl.

> **SDK lens:** This is the "configuration block" API — `resource("x") { … }`, `with_transaction { … }`,
> Kotlin's receiver lambdas, Gradle's DSL. **Setup/teardown around the closure is the SDK superpower**: it's
> exactly what makes context-manager APIs work, and it's the same mechanism that scopes "which object am I
> configuring" to a lexical block instead of to a mutable field. If you have a builder with a `currentThing`
> field, a block-scoped API removes it. **It fixes hierarchy and finishing at once** — the block delimits the
> subexpression, so there is nothing to `.end()` and the nesting is real; if your chained API is drowning in
> terminator calls and context variables, the block form is the refactoring. **Explicit vs. implicit receiver
> is a genuine, load-bearing decision**: explicit costs characters, preserves normal scoping intuitions, works
> in fragmentary use, and enables multiple cohesive builders; implicit is terser for standalone config files
> but surprises readers and breaks access to the enclosing lexical context. Fowler's rule — implicit for
> self-contained scripts, explicit for fragmentary use — is directly usable, and Weirich's reversal is the
> cautionary tale. Finally, **language ergonomics legitimately drive API shape**: Fowler's own conclusion that
> the pattern works less well in C# than Ruby is permission to design differently per language binding rather
> than mechanically porting one surface everywhere.

---

### Choosing among the fluent techniques

The seven patterns above are not alternatives to be picked by taste. Fowler chooses between them by writing
the grammar production the clause must satisfy and reading off the technique that fits.

#### The grammar → technique mapping

| Grammar shape | Recommended technique | Why |
|---|---|---|
| `parent ::= first second` (fixed, mandatory children) | **Nested Function** | The parent's signature declares exactly the required arguments and, when statically typed, their types *(Ch. 34, "How It Works")* |
| `parent ::= (this \| that)*` (heterogeneous, repeatable, unordered) | Nested Function's **worst case** — forces intermediate tokens or a Context Variable; prefer **Literal Map** / keyword args, or **Method Chaining** | With no keyword arguments, arguments can only be identified by position and type, "downright impossible if `this` and `that` have the same types" *(Ch. 34, "How It Works")* |
| `parent ::= child*` (homogeneous repetition) | **Literal List** / varargs, usually nested inside a Nested Function | *(Ch. 34, "How It Works"; Ch. 39, "When to Use It")* |
| Mostly-optional clauses, any subset | **Method Chaining** | "Method Chaining easily allows a DSL script writer to pick and choose clauses" *(Ch. 35, "When to Use It")* |
| Mandatory clauses, or a required *order* of clauses | **Nested Function**, or Method Chaining + **progressive interfaces** | Plain chaining can never require a clause; progressive interfaces enforce ordering and can enforce a mandatory element via an interface exposing only it *(Ch. 35, "Progressive Interfaces" / "When to Use It")* |
| Hierarchy that must be structural, not cosmetic | **Nested Function** or **Nested Closure** | Function Sequence and Method Chaining only *suggest* hierarchy through indentation *(Ch. 35, "Hierarchic Structure")* |
| A top-level list of statements | **Function Sequence** (with Object Scoping), or a Function Sequence inside a **Nested Closure** | Only one result list and one Context Variable needed *(Ch. 33, "When to Use It")* |

The decision sequence Fowler actually argues, in order:

1. **Start with an Expression Builder.** Default; keep the fluent layer off the Semantic Model *(Ch. 32,
   "When to Use It")*.
2. **You must start the DSL with a Function Sequence of at least one call**, because every other technique
   needs a context to hang off *(Ch. 33, "When to Use It")*.
3. **Below the top level, avoid bare Function Sequence.** It's the least useful combination and it forces
   Context Variables *(Ch. 33, "When to Use It")*.
4. **Mandatory / hierarchical / fixed-shape → Nested Function** *(Ch. 34, "When to Use It")*.
5. **Optional / pick-and-choose → Method Chaining**, accepting that you can't require anything, you'll
   manage hierarchy yourself, and you'll face the finishing problem *(Ch. 35, "When to Use It")*.
6. **Need order or requirement *and* you're chaining → progressive interfaces** (or child builders)
   *(Ch. 35, "Progressive Interfaces")*.
7. **Lots of optional, unordered, heterogeneous arguments → Literal Map / keyword arguments**, not Nested
   Function *(Ch. 34, "When to Use It")*.
8. **Bare calls without globals → Object Scoping** — unless your bare functions are pure value-returning
   statics, in which case you may not need it *(Ch. 36, "When to Use It"; Ch. 34, "How It Works")*.
9. **Need control over *when* things evaluate, or want to bracket setup/teardown, or are drowning in
   Context Variables → Nested Closure** *(Ch. 38, "When to Use It")*.
10. **Fragmentary usage constrains everything.** Inheritance-based Object Scoping and implicit-receiver
    tricks are for self-contained scripts; fragmentary DSLs need explicit receivers and no inheritance
    requirement *(Ch. 36 and Ch. 38, "When to Use It")*.

#### The evaluation-order tradeoff

Every technique here is really a choice about *when* subexpressions run:

- **Function Sequence and Method Chaining evaluate left-to-right.** Natural for a sequence of commands, and
  natural for reading; but nothing is assembled until the end, so structure must be reconstructed from
  accumulated state.
- **Nested Function evaluates arguments before the enclosing call — inside-out.** Perfect for building a
  hierarchy of values (children return fully formed objects that the parent assembles), which is why it
  needs no Context Variables and has no finishing problem. Wrong for command sequences, where it produces
  the Old MacDonald problem *(Ch. 34, "When to Use It")*.
- **Nested Closure lets the parent decide when — and whether, and how often.** That single capability buys
  setup/teardown bracketing, Context Variable lifetimes bounded by a block, chain heads passed in as
  arguments, and independent evaluation of alternative branches *(Ch. 38, "How It Works")*.

#### The context-handling arc

| Pattern | How context is carried | Cost |
|---|---|---|
| Function Sequence | Context Variables on the builder (or, badly, statics) | Ambiguous clause names, runtime dispatch, order-dependence, thread hazards |
| Nested Function | Return values of the argument functions | None — but rigid shape, poor optionality |
| Method Chaining | Context Variables *or* child builders | Fiddly; child builders must forward parent punctuation |
| Object Scoping | Instance fields of the scoping builder | Constrains where the script may live |
| Nested Closure | Closure argument, or Context Variables scoped to the closure's lifetime, or a rebound receiver | Language-dependent syntax; receiver rebinding surprises readers |

The trajectory of the whole part: **push context out of global state, into instances, then into return
values or lexically scoped blocks.** Each step trades a bit of syntax for a large reduction in the class of
bugs available. That arc — globals → instances → return values → lexically scoped blocks — is a usable
maturity ladder for any configuration API.

#### The finishing problem, restated

Only left-to-right techniques have it. Method Chaining must return a builder from every call to keep the
chain alive, so no call can return the finished product and nothing marks the end *(Ch. 35, "Finishing
Problem")*. Nested Function and Nested Closure don't have the problem at all, because the enclosing call's
closing bracket *is* the terminator and its return value *is* the product. When you find yourself designing
a `.end()` or `.build()`, that is the moment to check whether an enclosing-call form would serve better —
Fowler's own recommendation is that "usually if you run into this you're better off using a Nested Function
or Nested Closure" *(Ch. 35, "When to Use It")*.

#### The convention violations Fowler licenses — inside the fence

Fluent layers earn a license to break normal API rules, and the license is granted by — and only by —
isolation in an Expression Builder. The violations he explicitly endorses:

- **Mutators that return values**, breaking command-query separation *(Ch. 35, "How It Works")*.
- **Query-shaped names for commands** — a `sata()` that sets rather than asks *(Ch. 35, "How It Works")*.
- **Property getters that mutate and return `this`** — "this abomination," acceptable only "when clearly
  placed in a fluent context" *(Ch. 35, "Chaining with Properties (C#)")*.
- **Separate methods where a parameter would be correct design** — `First()` and `Third()` rather than one
  method with an index *(Ch. 34, "Recurring Events (C#)")*.
- **A DSL structure that inverts the model's structure** — "and" in the language meaning `Or` in the
  specification, so that both the language and the model read naturally *(Ch. 34, "Recurring Events (C#)")*.
- **A DSL deliberately less expressive than its own model** — conjunction-only rules over a model that
  supports arbitrary Booleans *(Ch. 36, "Security Codes (C#)")*.
- **Naming rules bent for the script reader** — plural type names, builders named for how they read rather
  than what they are *(Ch. 34, "Recurring Events (C#)"; Ch. 44, "How It Works")*.

The unifying rule: **optimize the fluent layer for the reader of the script, and pay for that by
quarantining it away from every object the reader of ordinary code will touch.** The corollary is a
practical review question for any SDK: *if a user obtained this object from somewhere other than the fluent
chain, would its interface confuse them?* If yes, the fluent methods are on the wrong class.

---

## 11. Expressive-vocabulary patterns and their judgement calls

The last eight patterns of Part IV are about *vocabulary* rather than *combination*: how you express lists
and named options, how far you can bend method names and literals, how to attach declarative metadata, and
how much cleverness is too much. Fowler's tone changes noticeably here. Several of these chapters are
warnings dressed as patterns, and the warnings are the most valuable content in them.

---

### Literal List (Ch. 39)

> **Intent:** Represent a language expression with a literal list. *(Ch. 39)*

#### The concept

A Literal List is just the host language's built-in syntax for constructing a list/array inline. As a DSL
construct, you use it to hold the children of some parent element, and a parent function then walks the
list and processes the elements. Because most such syntaxes nest, you can build tree-shaped expressions out
of them — one way of looking at an entire Lisp program is as a nested list.

#### How it works

- The list is almost always **used inside a function call**; the function receives it and interprets it.
  **The list itself carries no semantics — the enclosing function supplies them** *(Ch. 39, "How It Works")*.
- **Not all languages have a usable one.** Mainstream C-derived languages have literal arrays but these
  frequently accept only constants/literals, not arbitrary symbols or expressions, which kills their
  usefulness for DSL work.
- **Varargs as a substitute.** A variadic call — `companions(jo, saraJane, leela)` — is effectively a
  Literal List with the parent function baked into the syntax. In a strongly typed language all elements
  must share a type to fit through a varargs parameter, which is a real constraint on heterogeneous content.

#### When to use it

- Good when the list sits **nested inside another element**, typically a function call, and the grammar you
  want is essentially `parent ::= child*` *(Ch. 39, "When to Use It")*.
- Often the items are themselves function calls, which is exactly what makes **Nested Function** workable —
  the two are natural partners.
- **Prefer varargs over an explicit literal list when the list is an argument.** Fowler is explicit: even
  when the host language *has* literal list syntax, he prefers `companions(jo, saraJane, leela)` to
  `companions([jo, saraJane, leela])`. The brackets are pure noise when the function boundary already
  delimits the list.
- You *can* write an entire DSL using nothing but Literal Lists — that is essentially Lisp. His verdict:
  natural in Lisp, but "little more than a fun exercise in other languages where it's more natural to
  combine lists with other forms of expression."

#### Relationships

- Pairs with **Nested Function (Ch. 34)**.
- Degenerate/adjacent form of **Literal Map (Ch. 40)** — if you have lists but not maps, you can encode maps
  as lists of key/value sublists.
- Contrast with **Method Chaining** and **Function Sequence** as alternative ways to express "a parent with
  many children."

> **SDK lens:** The "prefer varargs to an explicit collection literal" rule is a durable API heuristic: when
> a parameter is conceptually "zero or more of X", a variadic signature reads better than forcing callers to
> build a collection — *provided* the elements are homogeneous. The moment they aren't, the type system
> pushes you toward an options object instead. The deeper point is that a bare list carries no meaning of its
> own; whatever the elements mean comes from the function receiving them, so a list parameter is only as
> clear as the name of the function it sits inside.

---

### Literal Map (Ch. 40)

> **Intent:** Represent an expression as a literal map. *(Ch. 40)*

#### The concept

A Literal Map is the host language's inline dictionary/hash syntax. Used in a DSL, it's the "named options"
construct: a function takes a map and pulls named values out of it. Where Literal List expresses "a sequence
of children", **Literal Map expresses "a set of distinct named attributes, each appearing at most once."**

#### How it works

- Normally used in a function call where the function receives the map and processes it.
- **The central weakness is key validation.** In a dynamically typed language there is no way to communicate
  or enforce the valid set of keys. You must write the checking code yourself, *and* there is no mechanism to
  tell the DSL author which keys are correct — **no discoverability**. A statically typed language can dodge
  this by defining an enum of legal key types *(Ch. 40, "How It Works")*.
- **Keys should be symbols** where the language has them (or strings otherwise). Symbols are the natural
  choice and easy to process; some languages provide shorthand syntax for symbol-keyed maps.
- **Keyword arguments are a superior form of Literal Map.** Just as Fowler treats a varargs call as a form of
  Literal List, he treats a call with keyword arguments as a form of Literal Map — and says keyword arguments
  are *better*, because they often let you declare the valid keywords. "Sadly, keyword arguments are even
  rarer than a literal map syntax."
- **Fallbacks when the language lacks map literals:** encode maps as literal lists, or use alternating
  key/value arguments.
- **Delimiter elision.** Some languages let you drop the braces when the map is the only thing in that
  position. Worth exploiting — it removes a whole layer of punctuation noise.

#### Validate the keys — the actionable rule

Because maps give you no key checking, the worked example adds a `check_keys` helper that diffs the supplied
keys against an explicit whitelist and raises a dedicated exception **naming the unrecognized keys**. Without
it, a typo silently does nothing. Fowler frames this as unavoidable overhead: "The danger with using a map
like this is that it's easy for the caller to introduce an incorrect key by accident, so it's worth doing a
little checking here" *(Ch. 40, "The Computer Configuration Using Lists and Maps (Ruby)")*.

The same example demonstrates that a good internal DSL **mixes techniques**: one function takes a Literal
List (varargs), two take Literal Maps, and the whole script is evaluated with Object Scoping.

#### Greenspun form — purity as a diagnostic, not a goal

Fowler pushes a single technique as far as it goes "just to get a sense of its capabilities," explicitly
framed as an exercise rather than a recommendation *(Ch. 40, "Evolving to Greenspun Form (Ruby)")*:

1. **Lists + maps only.** Replace every function call with a Literal List whose head element is a symbol
   naming the construct and whose tail is the arguments. The script becomes a pure nested data structure,
   processed by evaluating the host-language code to get the structure and handing it to an interpreter
   written as a **Recursive Descent Parser**. Notable consequence: **you gain complete control over order of
   evaluation**, because nothing executes until your interpreter walks the structure. "In many ways, this DSL
   script is like an external DSL encoded in internal literal collection syntax instead of a string."
2. **Lists only ("Greenspun form").** Replace each map with a list of two-element key/value sublists — a wink
   at Greenspun's Tenth Rule. Using only lists yields a *more regular* script, but a list of pairs
   masquerading as a map fits the host language's style badly.
3. **Verdict:** "Either case isn't as good as the earlier example which mixed function calls with literal
   collections." The nested-list style is natural precisely in Lisp, where bare words are symbols by default.

**The extracted principle:** purity in one technique is a diagnostic exercise, not a goal. Mixed-technique
DSLs read better, and when a construct starts fighting the host language's idiom, that friction is the signal
to stop.

#### When to use it

"Literal Map is a great choice when you need a list of different elements where each element should appear no
more than once." The lack of key validation is annoying, but the syntax is usually still the best choice for
this shape of problem: it *communicates clearly* that each subelement is at-most-once, and the map is the
ideal structure for the receiving function. If you don't have Literal Maps, fall back to **Literal List**,
**Nested Function**, or **Method Chaining** *(Ch. 40, "When to Use It")*.

#### Relationships

- Complement of **Literal List**; both usually consumed by **Nested Function**.
- Alternatives when unavailable: **Nested Function**, **Method Chaining**.
- The full-list form leads directly into **Recursive Descent Parser** territory.

> **SDK lens:** This is the **options-object / kwargs API** pattern, and Fowler's critique is exactly the
> modern one: options bags trade discoverability for expressiveness — users cannot see the valid keys, IDEs
> cannot complete them, and typos fail silently. Therefore: **validate keys explicitly and fail loudly with a
> message that names the offending keys.** That is the single most actionable takeaway of the chapter for
> library authors. **Prefer real keyword parameters, a typed options struct, a TypedDict, or an enum-keyed
> map to a free-form map** wherever the language offers them, because they restore the declared-valid-key
> property a raw map throws away. And use the shape rule to decide when an options object is even right: it
> fits "many distinct, independent, at-most-once named attributes" — nothing else.

---

### Dynamic Reception (Ch. 41)

> **Intent:** Handle messages without defining them in the receiving class.
> *Also known as:* overriding `method_missing` / `doesNotUnderstand`. *(Ch. 41)*

#### The concept

Every object has a finite set of defined methods. Statically typed languages catch calls to undefined methods
at compile time; dynamic languages fail at runtime. Dynamic Reception hijacks that failure path: you override
the language's "unknown message" hook so your object can respond meaningfully to method names you never
declared. In effect you are **dynamically altering the rules for reception of method calls**.

#### How it works

- The hook lives at the top of the object hierarchy. You override it in your own class.
- **General (non-DSL) use case:** automatic delegation — define the methods you handle yourself and route
  everything unknown to a delegate.
- **DSL use case 1 — move parameters into the method name.** The canonical example is Active Record's dynamic
  finders: a `find_by_firstname_and_lastname(...)` call is not defined anywhere; the superclass checks for the
  `find_by` prefix, parses the method name to extract property names, and builds a query. You *could* pass the
  names as arguments, but embedding them in the method name reads better — it mimics what an explicitly
  defined method would look like. Conceptually: "Essentially, you are embedding an external DSL in the method
  name" *(Ch. 41, "How It Works")*.
- **DSL use case 2 — a sequence of Dynamic Receptions.** Instead of one parsed name, chain them:
  `find_by.firstname("martin").and.lastname("fowler")`, or fully bare,
  `find_by.firstname.martin.and.lastname.fowler`. Here the first call returns an **Expression Builder** and
  you compose with **Method Chaining** plus Dynamic Reception.
- **Removing quotes.** A major payoff: parameters no longer need quoting. Combined with **Object Scoping**,
  you can accept bare identifiers for arguments by implementing Dynamic Reception in the superclass so that
  after a keyword method is invoked, the *next* unknown method call is captured as the value. **Textual
  Polishing (Ch. 45)** can strip yet more punctuation.

#### When to use it — the governing rule

This is one of the richest "when to use it" sections in Part IV.

**Reasons it's appealing** *(Ch. 41, "When to Use It")*:

1. **It mimics real methods at a fraction of the effort.** It's entirely reasonable for a `Person` class to
   have a `find_by_firstname_and_lastname` method; Dynamic Reception provides it without your writing it — a
   significant time-saver when there are many combinations.
2. **Punctuation consistency.** An all-dots form means users never wonder when to use a dot vs. parentheses
   vs. quotes. **But Fowler dissents on this one:** "For many others, this consistency isn't a virtue; I like
   separating what is schema from what is data, so I prefer the way `find_by.firstname("martin")…` puts field
   names into method calls and the data into parameters." *Structure in the method names, values in the
   arguments.*

**Alternatives to weigh first:** attribute names as parameters; a closure predicate; or a fragmentary external
DSL in a string. Fowler concedes many people nonetheless find the method-name form most fluent.

**The governing rule:**

> "Above all, it's important to remember that Dynamic Reception only pays its way when it allows you to build
> these structures **in general, without any special case handling**." *(Ch. 41, "When to Use It")*

Corollaries he draws:

- It's only worthwhile when there is a **clear, mechanical translation** from the dynamic method name to
  methods that already exist for other purposes. The dynamic finder works precisely *because* the class
  genuinely has those attributes.
- **"If you need to write special methods to handle particular cases of Dynamic Reception, that usually means
  you shouldn't be using Dynamic Reception."** The moment you're special-casing, the generality that justified
  the magic has evaporated.

**The costs and hard limits:**

- **Impossible in static languages** at all.
- **Debuggability.** "Once you override the handler for unknown method invocations, any mistake can lead you
  into deep debugging trouble. **Stack traces often become impenetrable.**" This is the price, and you should
  be sure the fluency gain is worth it.
- **Encoding limits.** Program text and string data often use different encodings; many languages allow only
  ASCII in identifiers, which breaks for non-ASCII personal names. Language grammar rules for method names may
  also exclude legitimate data values.
- **Expressiveness limits.** A comparison like `...greater_than.2` fails because most dynamic languages won't
  allow a digit there; the workaround "obstructs much of the fluency that you're doing it for."
- **Not for complex Boolean composition.** Fine for a two-condition conjunction, but by the time you reach
  nested likes, comparisons, and negations "you're running down a road that forces you to implement a kludgy
  parser in an environment not well-suited for it."

#### The layering principle — the Active Record lesson

The complexity ceiling is *not* an argument against using Dynamic Reception for simple cases. Active Record
deliberately supports dynamic finders for simple cases and *deliberately does not* support more complex
expressions, pushing users to a different mechanism instead.

> "Some people don't like that, preferring a single mechanism, but I think it's good to realize that
> **different solutions may work best at different complexities, so you should provide more than one.**"
> *(Ch. 41, "When to Use It")*

The same lesson appears from the model side: "The underlying model allows me to have any kind of condition as
long as it knows how to match an itinerary." Some conditions come in through the DSL; others through a
closure-backed condition object. "This kind of flexibility can be quite important. It allows people to use the
DSL to handle simple cases simply, but provides an alternative mechanism to handle more complicated cases"
*(Ch. 41, "Promotion Points Using Parsed Method Names (Ruby)")*.

#### Containment techniques from the examples

- **Delegate unknown names upward.** If the prefix doesn't match, call the superclass handler, so genuinely
  unknown methods still produce the language's normal error. Essential hygiene: don't swallow every message.
- **Validate arity and shape yourself.** The example checks that the number of attribute names parsed from the
  method name matches the number of arguments, and throws a clear error otherwise. With dynamic reception you
  are writing your own signature validation.
- **Use the open-ended mechanism only where the vocabulary is open.** In the chaining example, the
  attribute-name and value builders use dynamic reception; the *operator* builder, with its fixed operator
  set, uses ordinary defined methods. "This is the cleanest statement in the chapter of how to keep magic
  proportional" *(Ch. 41, "Promotion Points Using Chaining (Ruby)")*.
- **Scope the magic with per-section builders.** In the state-machine example, each section evaluates its block
  in the context of a *different, tiny* builder whose handler interprets every call as a declaration of that
  one kind. "By using a different builder, I can keep each one simple and clearly scope what each builder is
  recognizing" *(Ch. 41, "Removing Quoting in the Secret Panel Controller (JRuby)")*.
- **Two-stage evaluation handles forward references.** State bodies are not evaluated when declared; the
  closure is stored and processed in a postprocessing pass. "By deferring the evaluation till later, I can
  avoid worrying about the forward references between states" — all states are declared and the Symbol Table
  fully populated before any body referring to another state runs.

#### Two verdicts worth memorizing

- "Making little parse trees like this isn't a common way to do an internal DSL; it's usually easier to just
  build the model up as you go. But with a conditional expression like this, it makes sense."
- **"Overall, however, I'm not too keen on building up expressions using this approach. It seems to me that
  once you start parsing sequences of method calls like this, you might as well just switch to an external DSL
  where you get more flexibility. The desire to build up parse trees is a smell indicating that the internal
  DSL is doing too much work."** *(Ch. 41, "Promotion Points Using Chaining (Ruby)")*

And the honest cost/benefit summary on the state machine: "The question, of course, is whether it's worth the
trouble. To my eye, I like the way the event and command list turn out, but I'm not so keen on the states." His
recommendation is a hybrid — dynamic reception where it genuinely helps, plain symbol references where it
doesn't: **"A mixture of techniques is often the best bet."**

#### Relationships

- Usually combined with **Expression Builder**, **Method Chaining**, **Object Scoping**, **Symbol Table**,
  **Context Variable**.
- **Textual Polishing (Ch. 45)** removes further punctuation once Dynamic Reception has removed the quoting.
- Its failure mode points at **external DSLs** / **Recursive Descent Parser**.

> **SDK lens:** This is the `__getattr__` / `method_missing` / JS `Proxy` dynamic-attribute API pattern, and
> Fowler's rules translate directly. (1) **Only use it when the mapping is fully general** — if you're writing
> `if name == "foo"` inside your hook, define `foo` properly. (2) **Always delegate unhandled names to the
> default error path.** Never let an unknown attribute silently return null or a no-op builder. (3) **Budget
> for debuggability** — impenetrable stack traces are the real recurring cost, paid by every future user
> debugging through your hook. (4) **Scope the magic**: per-section builders, each recognizing one open
> vocabulary, beat one god-object that answers to everything. (5) **Validate arity and shape yourself**, with
> an error message naming the method and what was expected; the compiler is no longer doing it for you.
> (6) **Layer the API deliberately** — provide a magic path for the simple 80% and a distinct explicit
> mechanism (closures, a builder, a query object) for the complex 20%; supporting more than one mechanism at
> different complexity levels is a feature, not an inconsistency. (7) **Data does not belong in identifiers**
> when it may be non-ASCII, contain digits, or otherwise violate identifier grammar — keep schema in names,
> values in arguments.

---

### Annotation (Ch. 42)

> **Intent:** Data about program elements, such as classes and methods, which can be processed during
> compilation or execution. *(Ch. 42)*

#### The concept

We routinely classify data in our programs and write rules about the classifications. Sometimes we want to
classify *elements of the program itself*. Languages already provide some built-in mechanisms — access
controls like public/private mark methods. But we frequently want to mark things beyond what a language
supports, or reasonably *should* support: restrict the values a field may take, mark methods to be run as
tests, indicate that a class can safely be serialized.

> "An Annotation is a piece of information about a program element. … Annotations thus provide a mechanism to
> extend the programming language." *(Ch. 42)*

Crucially, **the concept is broader than any special syntax** — the same benefits are achievable without it.

In DSL terms: the annotation-defining syntax *is* an internal DSL, and it develops a **Semantic Model** by
attaching data to the runtime model of the program that's built into the language. Later processing steps
correspond to running that model — which, as with any DSL, can mean execution or code generation.

#### Defining an annotation — four techniques

In decreasing order of language support *(Ch. 42, "How It Works")*:

1. **Purpose-designed syntax** (`@Test`, `[Test]`), with parameters. Most obvious, often easiest.
2. **Class methods called in the class body** — a declaration call that receives the name of the field plus
   the data, and either stores the raw data or directly constructs processor objects. "Using class methods
   like this can be almost as easy as using purpose-designed syntax." Biggest issue: the call must be given
   the **name of the element it annotates**, adding verbiage. But that also buys freedom: you can **separate
   the annotations from the annotated declarations**. "That is a big payoff for languages that make this easy
   — there's little need to provide a special annotation syntax." Practical gotchas: the annotations must
   actually *execute* to be stored, and class-level storage is often shared between a class and its
   subclasses, which is a real hazard.
3. **Marker interface** (statically typed languages): an interface with no methods; implementing it tags the
   class. **Only works on classes**, not methods or fields.
4. **Naming conventions.** The simplest form — early xUnit tagged test methods by requiring names begin with
   `test`. Works well for simple annotations, but "multiple annotations are difficult to support and
   parameters are practically impossible."

**A structural limitation unique to Annotations.** Beyond the usual internal-DSL limit (your syntax is bounded
by the host language's), annotations carry an additional one: the Semantic Model must be based on the
program's own fundamental representation — classes, fields, methods. The annotation Semantic Model is a
*decoration* of that structure. **"You can't practically build a completely separate and independent Semantic
Model."** *(Ch. 42, "How It Works")*

#### Processing annotations

Annotations are written in source but consumed later — at compilation, at load, or during runtime *(Ch. 42,
"Processing Annotations")*.

- **Runtime processing is the most common case**: a test runner finding and running test methods; a database
  mapper interrogating field annotations to discover the mapping to persistent storage.
- **Processing can be split across phases.** Validation annotations can be *partially* processed at startup to
  create validator objects attached to classes, which then validate objects during execution — cache the
  expensive reflection once, run the cheap check many times.
- **Runtime processing ≈ model execution; the alternative is code generation.** In a dynamic language, code
  generation can happen at runtime, generating new classes or adding methods to existing ones.
- **Compiled languages** make runtime generation awkward. Options: compiler hooks for annotation processing;
  generating code *before* compilation (but "such intimate intermixing of written and generated code can be
  confusing"); or **bytecode postprocessing**.
- **One definition, many processors — the killer application.** In a web app you want field validations
  enforced in the browser (for responsiveness) *and* on the server (because you can never trust the browser).
  With Annotation you create a runtime check for the server and generate JavaScript for the browser without
  duplicating code: "Both checks can be fully derived from a single Annotation."

#### When to use it

Fowler opens with unusual candour: "The wide-scale use of Annotations is still relatively new in mainstream
programming languages. We are still learning when best to use them."

**The key property:**

> "The key feature of Annotations is that they allow you to separate definition from processing." *(Ch. 42,
> "When to Use It")*

The validation example makes the case concrete. The obvious way to enforce a valid range is inside the setter
— but that **fuses the definition of the constraint with the moment it's enforced**, so validation necessarily
happens on every value change. There are many cases where you want to check constraints at other times:
letting a user fill in a form and only validating on submit. A whole-object `validate` method helps, but
you're still defining the constraints in the same place they're checked. **Separating the two lets you:** check
constraints at different times; apply *different subsets* of constraints at different times; and make the code
clearer, because the constraint definitions stand alone.

**The decision rule:** "The strength of Annotations lies where it makes sense to separate definition and
processing." Two motivations qualify — you want the *processing* to vary independently of the definition, or
you want the *definition* to be easier to understand by standing alone.

**The downside:** "it is more awkward to follow both definition and processing. If you need to understand them
together, Annotations force you to look in two disconnected places. The processing code is also generic, which
may make it even harder to follow."

#### The declarative-only corollary

This is a hard design rule for any declarative API:

> "The definition of an Annotation should be **declarative and not involve any logic flow**. Furthermore, it
> shouldn't imply any ties to when the processing logic occurs, or any ordering of processing Annotations
> attached to the same or different program elements." *(Ch. 42, "When to Use It")*

Three prohibitions in one sentence: no control flow inside the declaration; no assumption about *when* the
processor runs; no ordering dependency between annotations. Violate any of them and you have built a trap that
looks like a declaration.

**A related aside worth keeping** *(Ch. 42, Java example)*: having an object validate itself is not always the
right strategy. "When you validate something, you always do so for a context, and that context is usually some
action involving that object." Self-validation implies the validation is correct for every context the code is
used in — sometimes true, often not.

**Decouple annotation from processor.** In the worked example the annotation-to-processor link is a
**dictionary lookup**: a processor reflects over the target's fields, reads their annotations, looks up a
validator per annotation type, and runs it. Fowler names the alternatives — the annotation could implement the
check itself, or carry the name of its validator class — and rejects both: "I generally prefer, at least in
Java, to make annotations independent of the processing mechanism" *(Ch. 42, "Custom Syntax with Runtime
Processing (Java)")*.

**One declaration, N processors, in practice.** The Ruby code-generation example upgrades the processing so
each annotated field automatically gets its own generated predicate method, and the critical observation is:
**"I don't need to modify the annotation calls in the patient visit class; they can remain the same as the
simpler case."** The user-facing declarative surface is unchanged while the processing is upgraded underneath
*(Ch. 42, "Dynamic Code Generation (Ruby)")*. It also guards against clobbering an existing method before
generating.

#### Relationships

- Builds a **Semantic Model (Ch. 11)**, constrained to decorate the language's own program model.
- Alternative to **explicit registration** / imperative configuration calls.
- Related to **Symbol Table (Ch. 12)** (annotation → processor dictionaries) and to code generation patterns.

> **SDK lens:** This chapter is essentially a design brief for **declarative metadata APIs** — decorators,
> attributes, schema classes, ORM field descriptors, serialization tags, validation decorators, DI
> annotations. **When Annotation beats explicit registration:** when definition and processing genuinely want
> to vary independently, or when you want the declaration readable in isolation right next to the thing it
> describes. Explicit registration wins when the reader needs to see *what happens* and *when* in one place.
> **Design rule for any decorator you ship: it must be purely declarative** — no control flow, no ordering
> dependencies between decorators, no implied coupling to when processing runs. The moment your decorator's
> behavior depends on declaration order relative to another, you have built a trap. **Decouple the annotation
> from its processor**: keep the annotation inert data, put behavior in a processor selected via a registry.
> That is what makes multiple processors possible, and **the multi-target payoff is the strongest argument for
> a declarative API**: one declaration, N processors (server-side check plus generated client-side check;
> runtime validation plus generated docs; runtime schema plus generated migrations) with no duplication and no
> drift. **You don't need language-level annotation syntax** — class-body declaration calls, naming
> conventions, and marker interfaces all count, with known costs. And **accept the discoverability cost
> honestly**: the reader must now look in two places, so mitigate with good docs and, especially, good error
> messages from the generic processing code.

---

### Parse Tree Manipulation (Ch. 43)

> **Intent:** Capture the parse tree of a code fragment to manipulate it with DSL processing code. *(Ch. 43)*

#### The concept

When you write code in a closure, that code is available to be *executed* later. Parse Tree Manipulation goes
further: it lets you **examine and modify the code's structure**, not merely run it. The host language's own
expressions become input data to your DSL processor.

#### How it works

- You need an environment that can turn a code fragment into a workable parse tree. "This is a relatively rare
  programming language feature — rare both in that few languages support it and in that, even when it is
  supported, it's rarely used" *(Ch. 43, "How It Works")*.
- Three exemplars: **C# (from 3.0)** via expression trees, **Ruby's ParseTree library**, and **Lisp**.
- **The library-based ones work similarly:** you invoke a call on a source fragment and get back a data
  structure representing its parse tree. C#'s version works only on an **expression inside a lambda** — so you
  cannot capture multi-statement code — and returns a hierarchy of purpose-built expression objects. In both
  you write a **tree walker**; both can turn a subtree back into executable code.
- **Lisp is categorically different:** Lisp source *is* essentially a serialized parse tree of nested lists,
  and syntactic macros let you examine and manipulate any expression.
- **You can't accept arbitrary host-language expressions.** There are always limits on what your walker can
  handle. "In these situations, **it's important to fail fast** should you get an expression that you can't
  handle." Normally when walking a parse tree you know the node shapes conform to expectations; here the tree
  can contain *any* legal host construct, so **all the checking is your responsibility**.
- **Walk only what you must.** "Usually you won't need, or want, to walk the entire parse tree." Walk the parts
  you need to populate your Semantic Model and hand the remaining subtrees back to the language to evaluate as
  soon as you no longer need to navigate them. This keeps you from reimplementing a whole parser.

#### When to use it

- The driving reason: **you want to use a fuller range of the host language's features to express something,
  "instead of the pidgin of the usual internal DSL constructs."**
- The key distinction from the general internal-DSL benefit: you can always intermix full host language with
  DSLish constructs, but "usually, you can only manipulate the executable **results** of the host language —
  you can't dive into host language expressions and manipulate their structure" *(Ch. 43, "When to Use It")*.
- **Not many DSL use cases exist.** The best is LINQ, the driving force behind .NET's support: expressing query
  conditions as ordinary Boolean expressions and turning them into a **SQL query** — writing DB queries without
  knowing SQL, or writing one query executed against different data sources. That requires parsing the host
  condition into a tree, walking it, and emitting SQL: essentially **source-to-source translation**. "Parse
  Tree Manipulation is good for these cases, as it allows you to use a familiar syntax for your conditions when
  your target language is not well known or you want multiple targets."
- Another use: **modify** the tree to perform surgery, e.g. redirect all method calls on one object to another.
  "But it's not clear how useful that kind of surgery is in a DSL context."

**The warning — the real point of the chapter:**

> "I also worry a bit that Parse Tree Manipulation is one of those techniques where **the intricacies of doing
> it may be just too appealing for many programmers. It's an appeal that can blindside people into missing
> other, simpler ways of achieving the same goal.**" *(Ch. 43, "When to Use It")*

#### What the worked example teaches

The example translates a lambda over a criteria object into an IMAP server-side search string *(Ch. 43,
"Generating IMAP Queries from C# Conditions (C#)")*. Beyond the mechanics, four ideas transfer:

- **A "phantom" receiver object.** To write a comparison against a `Subject` property you need an object
  exposing those members. Fowler is explicit that "this object won't ever do anything at runtime; it's only
  there to provide the methods to help me compose the query. As a result, the return values of its methods are
  irrelevant as they'll never actually be called." The type exists purely so the compiler will accept — and the
  IDE will complete — an expression you intend to *inspect* rather than execute.
- **The honest admission about expressiveness:** "despite my desire to allow clients to construct IMAP queries
  in C#, they can't use *any* C#." The model handles only a subset of operators and shapes; the walker throws
  on anything else — fail fast, as the pattern requires.
- **Validate at construction to simplify extraction.** The element builder asserts node validity in its
  constructor, so the later logic that pulls data out of the node stays simple. It also accepts the keyword and
  value on either side, since commutativity is what a host-language reader expects.
- **"Don't parse what you can evaluate."** For the *value* side of each comparison he does not walk the node at
  all — he compiles and invokes that subexpression through the language runtime. "This allows me to put any
  legal C# into the value side of my elements without having to deal with it in my navigation code." This is
  "walk only what you need" in its purest form, and it is the main reason the example stays tractable.

**"Stepping Back" — two meta-lessons** *(Ch. 43, "Stepping Back")*:

1. **Explanation order ≠ construction order.** He explains the example one aspect at a time because that's
   easier to understand, but he *built* it feature by feature, refactoring as he went. "I always advocate
   building software like this, feature by feature, but I don't think that's the best way to explain the final
   result. So don't let the structure of the final result and the way I explain it fool you into thinking that
   it is how it's built."
2. **He wouldn't actually build it this way.** "Although walking a parse tree like this yields that geeky
   pleasure of using fancy parts of a language, I wouldn't actually build an IMAP DSL this way." The
   alternative is plain **Method Chaining**, whose entire implementation is a handful of small methods plus one
   Context Variable. His diagnosis of *why* it's simpler is the transferable insight:

   > "One of the main reasons this is so much simpler is that **the structure of the internal DSL is more
   > similar to the IMAP query itself.** In fact, it's really just the IMAP query expressed as Method Chaining.
   > Its advantage over using IMAP itself boils down to IDE support. Some people might prefer the more C#ish
   > syntax that the Parse Tree Manipulation example gives you, but I must admit I'm happier with the IMAPish
   > version."

#### Relationships

- Populates a **Semantic Model**, like every other pattern here.
- Its main competitor for the same problems is plain **Method Chaining** (+ Expression Builder + Context
  Variable).
- **Macro (Ch. 15)** is the same idea by another route — Lisp macros enable it because Lisp source is
  parse-tree-shaped.

> **SDK lens:** This is the pattern behind LINQ-to-SQL, ORM expression translation, and any API that **inspects
> a lambda instead of calling it** — `.filter(x => x.age > 40)` compiled to a remote query. Fowler's
> constraints all apply: your API accepts only a *subset* of the host language, so you must **fail loudly and
> specifically** on anything outside it — a silent mistranslation is far worse than an exception. **Design the
> surface to mirror the target, not the host**: the IMAP verdict is the lesson, where an API shaped like the
> target query language ended up simpler and better than one shaped like the fanciest available host-language
> feature, with IDE support the only genuine advantage of the fancy version. **Evaluate what you don't need to
> inspect**: define a clear boundary between structure you interpret and sub-expressions you hand back to the
> language; it massively shrinks what you have to support. And **beware technique-attraction** — Fowler's
> warning that intricacy is seductive and "can blindside people into missing other, simpler ways" is the
> general antidote to clever-trick API design.

---

### Class Symbol Table (Ch. 44)

> **Intent:** Use a class and its fields to implement a symbol table in order to support type-aware
> autocompletion in a statically typed language. *(Ch. 44)*

#### The concept

Modern IDEs offer **type-aware autocompletion**: type a variable name, a dot, and get the list of methods on
that object. Fowler — a self-declared enthusiast for dynamic languages — concedes this is a genuine benefit of
static typing. In an internal DSL you don't want to lose it when *typing the name of a symbol* in your
language. But the usual ways of expressing DSL symbols are strings or a built-in symbol type, which carry no
type information at all, so the IDE can offer nothing.

Class Symbol Table makes the DSL's symbols **statically typed host-language entities** by declaring each symbol
as a **field in an Expression Builder**. The field name is the symbol name; the field's declared type tells the
IDE and compiler what that symbol can do.

#### How it works

- **Put the DSL script inside a single Expression Builder class**, usually a subclass of a more general builder
  carrying behavior needed by all scripts. The script's class then consists of a method holding the script plus
  fields declaring the symbols *(Ch. 44, "How It Works")*.
- **Naming conventions get bent for readability.** A plural class name is unconventional; "the readability of
  the DSL is trumping my usual code style rules." Restated later: any OO style book will tell you to avoid
  plural class names and he agrees — "However, here a plural name reads better in the context of the DSL, so
  this is another case of general coding rules being broken to make a good DSL script."
- **The runtime gap.** Declaring fields is not enough. When the script refers to a field, at runtime it refers
  to the **contents** of the field, not the field *definition*. The IDE knows about both while you write; the
  link to the declaration disappears when the program runs. So you must **populate every field with a suitable
  object before the script executes.**
- **The population mechanism.** Make the class instance the active script: code in the constructor or a build
  method populates the fields, and the script lives in an instance method. The field contents are usually
  **small Expression Builders** that link to the underlying Semantic Model object *and also carry the field
  name*, to help with cross-referencing. In Symbol Table terms the field name is the key and the builder is the
  value — but occasionally you need lookup by name too, which is why the builders keep their own name.
- **Reflection is the price.** The script refers to fields by the field literal itself — that's the point. But
  while processing you need the builders in those fields to refer to *each other*, which means looking up
  fields by name or iterating all fields of a given type. "Doing this will require some more tricky code,
  usually using reflection. Usually there's not too much of it and, provided it's well encapsulated, it
  shouldn't make the language too difficult to process."

The worked example orchestrates **three distinct execution stages** from the superclass *(Ch. 44, "Statically
Typed Class Symbol Table (Java)")*: generic field initialization; running the script (an abstract method the
subclass implements); then generic model production. Four further lessons from it:

- **Intermediate builders decouple declaration order.** Storing *builders* rather than finished model objects
  means the script can define things in any order. "However, this would lead to errors if I define a state
  before its action codes. Using the builder as an intermediate object allows me to work it either way."
- **Responsibility-preserving notification.** The first-mentioned state becomes the start state, but only the
  machine builder can know which was first, so the state builder simply notifies it without knowing what will
  be done with the fact. "This is a good example of naming being important in communicating what I think the
  responsibilities and relative knowledge of the objects should be."
- **Only script-visible types pay the readability tax.** The transition builder's type never appears in the DSL
  script, "so I can give it a more meaningful name." Bend naming rules *only* for the types the DSL author
  actually writes.
- Fowler's candid note on the generic initialization: "Doing it this way is more tricky than I'd like… any
  generic code doesn't know about the specific type of the identifier being set up, and so has to determine it
  dynamically."

#### When to use it

- **The benefit:** full static typing of all the DSL's language elements. That unlocks all the IDE machinery
  built on static types — above all type-aware autocompletion — plus compile-time type checking of the script,
  "which matters a lot to many people (but rather less to me)" *(Ch. 44, "When to Use It")*.
- **The scope limit:** "With such a focus on IDE capabilities, I see this technique as much less useful if you
  don't have an IDE that takes advantage of static types. It also does not bring much benefit in a dynamically
  typed language."
- **The cost:** "you have to bend your DSL significantly to fit within the type system. The resulting builder
  classes look very odd; also, you have to put your DSL scripts in a place where they can take advantage of
  these facilities, such as all in the same class. These restrictions may make the DSL harder to read and use."
- **The tradeoff statement:** "So for me, the fundamental tradeoff is between the restrictions on the DSL script
  and the benefits of the IDE support. I've got rather dependent on good IDE support in languages where it's
  available, which would prompt me to use techniques like this to get it."
- **Cheaper alternative:** "If you want this kind of static type support, you can often get what you need by
  using **enums as symbols**."
- **Closing verdict on the example:** "Using a class and its fields as a symbol table does involve a bit of
  tricky code in places, but the benefit is full static typing and IDE support. That's usually a worthwhile
  tradeoff."

#### Relationships

- A specialization of **Symbol Table (Ch. 12)** — field name = key, builder = value.
- Requires **Expression Builder**; often combined with **Object Scoping** (subclassing the builder).
- Cheaper alternative for the same goal: **enums as symbols** *(Ch. 12)*.

> **SDK lens:** The general technique is **turning stringly-typed identifiers into typed program elements so
> tooling can see them.** Every modern equivalent — enums instead of string constants, typed key objects,
> literal-union types, generated client stubs, typed schema classes — is the same trade: more ceremony in the
> declaration in exchange for autocompletion, compile-time checking, rename refactoring, and go-to-definition.
> **Reuse the tradeoff statement directly:** restrictions on how users must write their code vs. the tooling
> benefits. If your users have no IDE that exploits static types, or the language is dynamic, the benefits
> mostly evaporate and the restrictions remain — don't pay the cost. **Reach for the cheap version first**
> (enums, literal unions) before contorting the API into a class-with-fields shape. **Confine ugliness to the
> implementation**: the reflective initialization is acknowledged as ugly, and what matters is that it's
> encapsulated in the framework superclass, not imposed on the user. And note the precise version of
> "readability first": **break naming conventions only on the types the user actually types**; keep normal
> conventions on the types they never see.

---

### Textual Polishing (Ch. 45)

> **Intent:** Perform simple textual substitutions before more serious processing. *(Ch. 45)*
>
> Sketch: `3 hours ago` → `3.hours.ago`

#### The concept

Internal DSLs are often easier to develop — especially if you're not comfortable writing parsers — but the
result is littered with host-language artifacts (dots, colons, parentheses, quotes) that nonprogrammers find
awkward to read. Textual Polishing runs a series of simple **regular expression substitutions** over the script
*before* it reaches the parser/evaluator, converting a domain-expert-friendly surface into a valid internal-DSL
expression.

#### How it works

- A sequence of regex substitutions on the script text. **The output of the polishing is an expression in an
  internal DSL** — polishing does not produce a model, it produces host-language code *(Ch. 45, "How It
  Works")*.
- Specification is easy; correctness is not. "The tricky thing, of course, is getting the regular expressions
  correct so you don't get unwanted substitutions. A space in a quoted string probably should not be turned
  into a dot, but that makes the regex much harder to write."
- **Most natural in dynamic languages**, where the polished text can be evaluated at runtime: read the script,
  polish it, evaluate the result. Possible in static languages by polishing before compiling — "which does
  introduce another step into the build process."
- **Occasionally useful for external DSLs**: when something is hard to spot with the usual lexer/parser chain, a
  polishing preprocess before lexing can help — **semantic indentation** is the example.
- Conceptually: "You can think of Textual Polishing as a simple application of textual **Macros**, with all the
  corresponding problems."

**Tokenization discipline** from the example: because elements are whitespace-separated, "it's valuable to
ensure that all of the regexes have boundary expressions at both ends" *(Ch. 45, "Polished Discount Rules
(Ruby)")*.

#### When to use it

This is the most sceptical "when to use it" in the group — Fowler essentially argues himself out of the pattern
*(Ch. 45, "When to Use It")*:

- > "I confess I'm rather wary of Textual Polishing; my feeling is that if you use a little, it doesn't help
  > much, and if you use a lot, it gets very complicated, so it may then be better to use an external DSL."
- **The hard structural limit:** "Textual Polishing cannot do anything to change the syntactic structure of the
  input, so you are still tied to the basic syntactic structure of the host language." You can only re-skin, not
  re-shape.
- **Keep the two forms recognizably similar.** "I think it's important to keep the prepolished DSL and the
  resulting internal DSL expressions recognizably similar. The resulting internal DSL should be as clear as
  possible for programmers to read — the polishing is only a visual convenience for nonprogrammers." If a reader
  can't map the polished text onto the underlying calls, debugging becomes guesswork.
- **A cheaper alternative: fix it in the editor, not the language.** "If you find the noise characters in an
  internal DSL annoying, an alternative approach to Textual Polishing is to use an editor that supports syntax
  coloring and set it up to color the noise characters with a very gentle color that fades into the background."
  An excellent instance of solving a readability problem in tooling rather than in the language.
- **Escalation rule:** "If you find yourself doing a lot of polishing, I strongly suggest that you explore using
  an external DSL instead. Once you get up the learning curve of writing a parser, you'll get much more
  flexibility, and it will be easier to maintain the parser than the sequence of polishing steps."

The example is instructive because of what it does *before* reaching for regexes *(Ch. 45, "Polished Discount
Rules (Ruby)")*:

1. **Object Scoping removes noise for free** — putting the rules in their own file and evaluating each line in
   the builder's context drops the receiver prefix, with no substitution at all. It also **moves the Method
   Chaining finishing call into the processing code**, out of the user-visible DSL — a general trick: terminator
   calls are an implementation detail and users shouldn't have to type them.
2. **Adjust the DSL's own vocabulary to shorten the distance the polishing must travel.** Where a desired
   keyword collided with a host-language reserved word, Fowler notes you can rename the DSL method instead of
   substituting, since "doing this makes it easier to see the correspondence between the polished text and the
   resulting DSL."
3. **Closing verdict:** "This doesn't look too bad, but the code is only enough to process this one particular
   example. To handle more cases, the code will have to get more complex and much more ugly. So in this case,
   I'd be keeping a careful eye on it, ready to reach for an external DSL to use instead."

#### Relationships

- A degenerate form of **Macro (Ch. 15)**, with macro-like hazards.
- Frequently paired with **Object Scoping (Ch. 36)**, which removes noise without any substitution at all —
  always try this first.
- Its escalation path is an **external DSL** with a real parser.

> **SDK lens:** Mostly a cautionary pattern, with four transferable lessons. **Prefer structural fixes to
> textual ones** — Object Scoping and renaming a method achieved most of the goal with none of the regex risk;
> reach for the language-level fix before the string-rewriting fix. **Hide terminator/finisher calls from users**
> where you can, moving `.build()` into the harness rather than requiring every user line to end with it.
> **Don't let the user-facing surface and the underlying calls diverge**, or you destroy every error message,
> stack trace, and debugging session downstream — exactly the problem with heavy source rewriting,
> transpilation, and macro-based APIs generally. And **solve cosmetic complaints with tooling** (syntax
> highlighting, formatters) rather than by adding a translation layer.

---

### Literal Extension (Ch. 46)

> **Intent:** Add methods to program literals. *(Ch. 46)*
>
> Sketch: `42.grams.flour`

#### The concept

Literals — numbers and strings — often make a natural *starting point* for DSL expressions (`42.grams`,
`3.days.ago`). Traditionally they're built-in types with fixed interfaces so you can't extend them, but more
languages now allow adding methods to third-party classes: C#'s **extension methods**, Ruby's **open classes**.
For DSLs this is particularly handy because it lets you **start a method chain with a literal**.

#### How it works

As with most method chains, a key decision is **whether to use an Expression Builder**. Without one, every
intermediate type in the chain must itself carry the appropriate fluent methods. With one, you avoid that, but
you must ensure you can cleanly get from the builder back to the underlying object *(Ch. 46, "How It Works")*.

**What should `42.grams` return?** Three options, each with distinct consequences:

1. **A number**, in a canonical unit. **Danger: "type transmogrification"** (a term Fowler credits to Neal
   Ford) — the expression starts with an integer and turns into a floating point, meaning every subsequent
   method in the chain must be defined on *multiple* numeric types.
2. **A quantity object** (magnitude plus unit). "In general, I much prefer quantities to simple numbers for
   representing dimensioned values; quantities represent my intent better and also allow me to define useful
   behavior (such as alerting me to problems with `42.grams + 35.cm`)." Almost no platform ships a quantity
   class, but it's easy to write. Because the magnitude is encapsulated, **the type transmogrification problem
   largely disappears**. Cost: the quantity class now carries DSL fluent methods, "which may make the quantity
   class harder to understand."
3. **An Expression Builder.** You get full control over the rest of the expression; the cost is that calling
   code must be able to unpack the subject from the builder — fine inside a scoped ingredients block, a problem
   for arithmetic like `42.grams + 3.oz`. "I tend to prefer an Expression Builder most of the time, but it
   really depends on the context of its use."

#### When to use it

- **Sceptical framing.** "Literal Extension has become a popular illustration of how to make APIs more fluent,
  particularly by advocates of languages which are able to do it. … It can help a good deal in improving
  fluency, although there's also **the suspicion that some of this enthusiasm is fondness of a new toy**"
  *(Ch. 46, "When to Use It")*.
- **The real cost is global interface pollution.** "In some environments, there is a serious concern that adding
  methods like this to literals will bloat the interface of those literal classes. These Literal Extensions are
  only needed in some contexts, so if they appear in more contexts they can make a class's interface much more
  confusing." You must weigh the usefulness of the extension against the confusion it adds everywhere else in
  the program.
- **The mitigation: namespace scoping.** "Some language environments allow you to state that Literal Extensions
  are bound to a namespace, which avoids this problem." In the C# example Fowler departs from his usual practice
  and shows the namespace explicitly, precisely because it means the extension method "will only show up if I'm
  in the right namespace."

#### Keep DSL vocabulary off general-purpose types

The most transferable idea in the chapter comes from the recipe example *(Ch. 46, "Recipe Ingredients (C#)")*.
Fowler wrote the `Quantity` class himself — and still refuses to put the DSL's `Of` method on it:

> "Although quantity is a class I'm writing, I don't think the `Of` method belongs on it — because **`Of` is part
> of a DSL for a limited purpose, while the quantity class can be used as part of a general library.** So I use
> an extension method again."

The rule: a type that serves the general library gets a general interface; DSL-only vocabulary lives in an
opt-in, namespace-scoped extension. (The same example resolves ingredient names to objects via a substance
registry acting as a **Symbol Table**, lazily creating the substance on first request.)

#### Relationships

- Typically the entry point into **Method Chaining (Ch. 35)**; may or may not use **Expression Builder**.
- Its resolution of names to objects uses **Symbol Table (Ch. 12)**.
- The "quantity vs. raw number" discussion connects to the Quantity analysis pattern.

> **SDK lens:** This is **monkey-patching / extension-method API design**, and Fowler's rule is namespace or
> module scoping: extensions to types you don't own should be opt-in and locally scoped, never globally visible.
> A library that adds methods to the integer type for everyone is imposing its vocabulary on the whole program.
> **Keep DSL-specific fluent methods off general-purpose types** — `Of` belongs to a limited-purpose language,
> `Quantity` to the general library; generalized: *don't bolt your framework's fluent vocabulary onto shared
> domain/model classes.* **Watch the return type of every chain step**: type transmogrification forces you to
> define the rest of your fluent vocabulary on every type it might pass through, so a purpose-built wrapper type
> that stays stable through the chain is almost always better — the same reason fluent builders return
> `this`/`Self` rather than shifting types. And **fluency is not free**: Fowler's "fondness of a new toy" line is
> the general caution that a technique's availability and elegance are not reasons to adopt it.

---

### The judgement calls, collected

Across these eight patterns the same handful of decisions recur, and they are the reusable content:

1. **Keep the magic proportional to the benefit.** Dynamic Reception's fluency is paid for in impenetrable stack
   traces *(Ch. 41)*; Parse Tree Manipulation's power is paid for in a walker that must reject most of the host
   language *(Ch. 43)*; Class Symbol Table's autocompletion is paid for in reflective setup and a contorted
   script layout *(Ch. 44)*. In every case Fowler states the exchange rate explicitly and refuses the trade when
   the benefit is thin.
2. **Use the open-ended mechanism only where the vocabulary is genuinely open.** Dynamic dispatch for
   attribute names and values; ordinary declared methods for the fixed operator set *(Ch. 41)*.
3. **Layer the API by complexity; don't stretch one mechanism to cover everything.** "Different solutions may
   work best at different complexities, so you should provide more than one" *(Ch. 41, "When to Use It")*.
4. **When a technique starts requiring special cases, you've outgrown it.** Special-cased Dynamic Reception
   means don't use Dynamic Reception *(Ch. 41)*. A growing pile of polishing regexes means write a parser
   *(Ch. 45)*. A desire to build parse trees out of chained calls "is a smell indicating that the internal DSL
   is doing too much work" *(Ch. 41)*.
5. **Mix techniques; don't chase purity.** Greenspun form *(Ch. 40)* and the fully symbol-free state machine
   *(Ch. 41)* both show that maximizing one technique produces a worse language than a judicious blend. "A
   mixture of techniques is often the best bet."
6. **Discoverability vs. expressiveness is the recurring axis.** Literal Map is expressive but its keys are
   invisible and unvalidated *(Ch. 40)*; Class Symbol Table sacrifices expressiveness and layout freedom to buy
   discoverability *(Ch. 44)*; Literal Extension buys fluency at the cost of polluting a widely-used interface
   *(Ch. 46)*.
7. **Shape the DSL like its domain or target, not like the host language's flashiest feature.** The IMAP
   comparison is the cleanest demonstration: the Method-Chaining version won because it mirrored IMAP's own
   query language *(Ch. 43)*.
8. **Separate definition from processing when — and only when — they should vary independently** *(Ch. 42)*,
   with the corollary discipline that declarations must be purely declarative: no logic flow, no ordering
   dependencies, no implied coupling to when processing runs.
9. **Explanation order is not construction order** *(Ch. 43, "Stepping Back")*. Build feature by feature,
   refactoring as you go; present the result decomposed by concern.
10. **Solve cosmetic problems with tooling before adding machinery** *(Ch. 45)*.

# Part 3 — The Pattern Catalog II: External DSLs, Computational Models, and Code Generation

## 12. Parsing an external DSL

An external DSL is text that your program did not write and cannot execute directly. Something has to turn that text into structure your code can act on. The seven patterns in this section are a graded set of answers to that one question, and they line up on a single spectrum: **how explicitly is the structure of the language stated?**

1. **Delimiter-Directed Translation** — no explicit grammar at all; chop the input by delimiters and dispatch on what each chunk looks like.
2. **Recursive Descent Parser** — a grammar exists, but only *implicitly*, in the shape of the functions you wrote.
3. **Parser Combinator** — the grammar is *explicit as composed objects*, though not in BNF syntax.
4. **Parser Generator** — the grammar is *explicit as a declarative DSL* (a BNF file), and the parser is generated from it.

Moving right along that spectrum buys documentation value, easier evolution, and more power on complex languages. It costs a learning curve on grammars and, at the far right, build complexity. Two chapters supply the shared conceptual substrate — Syntax-Directed Translation (the layered architecture) and BNF (the notation) — and one, Regex Table Lexer, supplies the shared front end used by options 2, 3, and optionally 4.

A useful framing before the details: this is not purely a technical decision. Fowler repeatedly makes it a decision about *your team* and *your build*, not only about your language.

---

### 12.1 Delimiter-Directed Translation *(Ch. 17)*

**Intent:** "Translate source text by breaking it up into chunks (usually lines) and then parsing each chunk." *(Ch. 17, intent)*

#### The concept

This is the most naive-but-honest way to parse an external DSL, and the one every working programmer has already improvised at least once. You read the input, split it on some delimiter — almost always the line ending — and run each chunk through code that recognizes and processes it. There is no grammar, no lexer/parser separation, no parse tree. Everything is done with string splitting, regular expressions, and conditionals.

Output goes straight into a Semantic Model (Embedded Translation) or is interpreted on the spot (Embedded Interpretation). Tree Construction is possible in principle, but Fowler says he rarely sees it combined with this pattern.

#### How it works

**Chunking.** Line-at-a-time reading is trivial everywhere. The one complication is *line continuation* — long logical lines you want to break physically in the editor. Quoting the line ending (Unix-style backslash) works but "looks ugly … and is vulnerable to whitespace between the quote and the end of line" *(Ch. 17, "How It Works")*. A dedicated continuation character — if it is the last non-whitespace character on a line, the next line belongs to this one — is usually better. You can get more than one continuation line, so the join must loop or recurse.

**Classifying lines.** How you process lines depends on the language, and Fowler's taxonomy here is the real content of the chapter. It is a complexity ladder:

- **Autonomous + isomorphic lines.** No line affects any other (you could reorder or delete lines without changing how the rest are interpreted), and every line encodes the same kind of information in the same form. Processing is trivial: one line-processing function, run against each line, pulling out the fields you need.
- **Autonomous + polymorphic lines.** Each line still stands alone, but different lines have different forms and need different processing. Handle it with a dispatching conditional — `if isBorder() → parseBorder; else if isHeadline() → parseHeadline; … else throw RecognitionException`. The conditions can be regexes or other string operations, but Fowler "usually prefer[s] using methods" — wrapping each regex in a well-named predicate — over inlining the regex in the conditional. Note the mandatory final `else throw`: unrecognized input must fail loudly.
- **Hybrid: isomorphic lines with polymorphic clauses.** Every line has the same broad structure (say, always `<reward> for <activity> at <location>`), but each clause can take several forms. A single top-level routine identifies the clauses and calls one processing routine per clause; each clause routine then applies the polymorphic conditional pattern internally.
- **Nonautonomous statements.** The hard case. The same syntactic form means different things depending on where in the file it appears — a statement that is legal and meaningful inside an `events` block, means something else in a `commands` block, and is an error inside a `state` block. This forces you to track parse state. Fowler's recommended structure is **a family of line parsers, one per parse state**: a top-level line parser plus one per block type, with the top-level parser swapping in the appropriate line parser when it sees a block keyword. "This, of course, is just an application of the *State [gof]* design pattern." *(Ch. 17, "How It Works")*

**Extracting data from a chunk**, in Fowler's order of preference *(Ch. 17, "How It Works")*:

1. A **string splitter** (split on whitespace, take element *n*). Easiest when the string splits cleanly.
2. A **regular expression with named capture groups**. More expressive power than a split, and it doubles as a syntactic validity check. Downside: regexes are complicated and many people find them awkward to follow.
3. A **composed regex** — Fowler's own term for breaking a large regex into named subexpression constants, defining each separately, and concatenating them. He reaches for it whenever a regex gets complicated: "I find this makes it much easier to understand what's going on."

**Whitespace is a recurring pain.** For a line of the form `property = value` you must decide whether whitespace around the `=` is optional. Optional whitespace complicates line processing; making it mandatory (or forbidding it) makes the DSL harder to use. It gets worse when one-versus-many whitespace characters matter, or tabs versus spaces. Contrast this with Syntax-Directed Translation, where the lexer usually just throws whitespace away.

**The slippery slope to a framework.** There is a recurring shape here: check whether a string matches a pattern, then invoke a processing rule for that pattern. That regularity "naturally raises the thought that this would be amenable to a framework" — a series of objects each holding a regex and processing code, run in turn, plus some indication of overall parser state, and a little DSL on top to configure it. Fowler's punchline is that this is exactly what Lex-inspired lexer generators are, and — this is the key judgement — "once you've got far enough into this to want to use a framework, then the jump to Syntax-Directed Translation is not much further, and you have a wider range of more powerful tools to work with." *(Ch. 17, "How It Works")*

#### It is doing grammar work anyway

Fowler explicitly maps his line taxonomy onto grammar concepts *(Ch. 17, "How It Works")*: polymorphic lines and clauses are **alternatives**; isomorphic lines are **production rules without alternatives**; breaking a line down into clauses with methods is **subrules**. Even the "no grammar" technique is doing grammar work — it just never says so. The same observation returns in the Recursive Descent chapter.

#### When to use it

*(Ch. 17, "When to Use It")*

- **Strength: approachability.** "The great strength of Delimiter-Directed Translation is that it is a technique that is very simple for people to use." The main alternative, Syntax-Directed Translation, requires mounting a learning curve on grammars; this one relies purely on techniques most programmers already have.
- **Weakness: the same approachability.** It does not scale. It works very well for simple languages, "particularly those which don't require much nested context." As complexity increases it "can get messy quickly, particularly since it takes thought to keep the design of the parser clean."
- **Fowler's actual recommendation:** favor it only when you have simple autonomous statements, "or maybe just a single nested context. Even then I'd prefer to use Syntax-Directed Translation unless I'm working with a team that I didn't think was prepared to deal with learning that technique."

That last clause is worth pausing on: this is a **team-capability decision** as much as a technical one, and Fowler says so out loud.

One more judgement from the worked examples: when parse state lives in a context object surrounded by state objects, how much behavior goes where? *Decentralized* (behavior in the line parsers) means those parsers constantly pull data out of a shared symbol table — "Pulling data out of an object repeatedly is usually a bad smell" — and forces the context to expose its internals. *Centralized* (behavior in the context) keeps the symbol table private but concentrates a lot of logic in one place, "which may make it overcomplicated. This would be more of an issue for a larger language." Fowler's verdict: "Both alternatives have their problems, and I'll confess I don't have a strong preference either way." *(Ch. 17, "Miss Grant's Controller")*

#### Relationships

Alternative to Syntax-Directed Translation (12.2). Feeds Embedded Translation or Embedded Interpretation. Its state-machine variant is the *State* pattern. It is the natural fit for Newline Separators (13.8), which are effortless here and fiddly under Syntax-Directed Translation. It is a poor companion for syntactic indentation (13.9). It is also the technique of choice for a *minimal interpreter in a constrained target environment* — see Model-Aware Generation's dynamic-loading example (15.4).

> **SDK lens:** The line taxonomy — autonomous/isomorphic → polymorphic → hybrid → nonautonomous — is a complexity ladder worth stealing for any config or input format you design. If you can keep statements autonomous and isomorphic, the implementation stays trivial and the format stays reorderable and diffable. Context-sensitive statements are precisely what force stateful parsing machinery on you, which is an argument for designing formats where **each statement carries its own context**. Two more transfers: "once you want a framework for this, you should have used the real tool" is a general smell test — when your ad-hoc dispatch table starts wanting configuration, ordering, and state, you have re-derived a worse version of something that already exists. And both of Fowler's examples fail loudly on unrecognized input; a parser that silently ignores what it does not understand is a bug factory.

---

### 12.2 Syntax-Directed Translation *(Ch. 18)*

**Intent:** "Translate source text by defining a grammar and using that grammar to structure translation." *(Ch. 18, intent)*

#### The concept

"Computer languages naturally tend to follow a hierarchical structure with multiple levels of context. We can define the legal syntax of such a language by writing a grammar that describes how elements of a language get broken down into subelements." *(Ch. 18, intro)* Syntax-Directed Translation uses that grammar to define the creation of a parser that turns input text into a **parse tree mirroring the structure of the grammar rules**.

This is the umbrella pattern for everything else in this section. It does not tell you *how* to build the parser; it tells you that a grammar is what structures the translation. Two routes lead from grammar to parser:

1. The grammar as **specification and implementation guide for a handwritten parser** — Recursive Descent Parser and Parser Combinator.
2. The grammar as **a DSL fed to a Parser Generator** that builds the parser automatically. Here you write none of the core parser code.

Crucially, "the grammar only handles part of the problem." It can tell you how to turn input text into a parse tree, and nothing more. You almost always need more, which is why Parser Generators provide ways to embed further behavior. Fowler's summary is also his best one-line argument for DSLs in general: "although the Parser Generator does a lot of work for you, you still have to do a fair bit of programming to create something truly useful. In this way, as in many others, a Parser Generator is an excellent example of a practical use of DSLs. It doesn't solve the whole problem, but does make a significant chunk of it much easier." *(Ch. 18, "How It Works")*

#### The three-layer architecture

The decomposition into layers is the chapter's main design content.

**Layer 1 — the lexer** (tokenizer, scanner). It splits the *characters* of the input into **tokens**, "more reasonable chunks of the input," generally defined with regular expressions. A token has two essential properties: a **type** (the kind of token — a keyword, an identifier) and a **payload** (the text that was matched). For keywords the payload is basically irrelevant; for identifiers the payload is the data that matters downstream. In practice tokens carry more — notably line number and character position, which is essential for error diagnostics.

Why separate lexing from parsing *(Ch. 18, "The Lexer")*:
- *Simplicity* — the parser can be written in terms of tokens rather than raw characters.
- *Efficiency* — the machinery differs. In automata terms, **the lexer is usually a state machine while the parser is usually a push-down stack machine.**
- Fowler notes the traditional split is "being challenged by some more modern developments": some tools use a push-down machine for the lexer, and **scannerless parsers** merge the two stages entirely.

**Ordered rules, first match wins.** Lexer rules are tested in order; the first match succeeds. So a keyword can never also be an identifier. Fowler: "This is generally considered a Good Thing to reduce confusion, avoiding such things as PL/1's notorious `if if = then then then = if;`." When you genuinely need to get round it, that is what Alternative Tokenization is for.

**Whitespace.** For many languages the lexer strips it so the parser never sees it. "This is a big difference to *Delimiter-Directed Translation* where the whitespace usually plays a key structuring role." When whitespace *is* syntactically significant — newlines as separators, indentation as block structure — the lexer must emit tokens indicating what is happening. But languages designed for Syntax-Directed Translation usually try to make whitespace ignorable, and many DSLs need no statement separator at all.

**Comments** are usually discarded by the lexer, and "it's always useful to have comments in even the smallest DSL." You may want to keep them — they are useful for debugging, particularly in generated code — in which case you must decide how to attach them to Semantic Model elements.

**Keep lexing simple — the context argument.** Fowler warns against fine-tuning token matching. Suppose event codes in your DSL are four-character sequences of capitals and digits; it is tempting to define a dedicated `code` token type. Don't. An input like `FAIL FZ17` would tokenize `FAIL` as a code rather than an identifier, "because the lexer only looks at the characters, not the overall context of the expression. This kind of distinction is best left to the parser to deal with, as it has the information to tell the difference between the name and the code." The general rule: **"it's best to keep lexing as simple as possible."** *(Ch. 18, "The Lexer")*

**Three kinds of tokens** *(Ch. 18, "The Lexer")*: **punctuation** (keywords, operators, parens, separators — type matters, payload does not; fixed elements of the language); **domain text** (names, literal values — very generic token types, variable content); **ignorables** (whitespace, comments — usually discarded).

**Generated vs handwritten lexers.** Most Parser Generators generate a lexer from regex rules, but many people write their own with a Regex Table Lexer. Handwritten lexers give "more flexibility for more complex interactions between the parser and the lexer, which can often be useful." The specific interaction Fowler names: **supporting multiple modes in the lexer and letting the parser switch between them** — the mechanism behind Alternative Tokenization.

**Layer 2 — the syntactic analyzer.** Given a token stream, the parser's behavior splits in two:

- **Syntactic analysis** arranges tokens into a parse tree. This work "can be derived entirely from the grammar itself," and a Parser Generator generates it.
- **Actions** take that tree and do something more, such as populating a Semantic Model. "The actions cannot be generated from a grammar, and are usually executed while the parse tree is being built up."

A parser doing syntactic analysis alone produces only success or failure — it tells you whether the input matches the grammar. That is called **recognizing** the input.

**Many grammars match the same language.** Fowler shows two grammars that accept exactly the same inputs but produce *different* parse trees — one flattening a list of declarations, the other introducing an intermediate list node. "It's important to realize that any given language can be matched by many grammars." Which one you pick depends on how you want to control the parse, and on your tool. **The grammar is a design artifact with choices in it, not a transcription of the language.**

**The parse tree usually is not real.** "So far I've talked about the parse tree as if it's something that is explicitly produced by the parser as an output of the parse. However, this is usually not the case." *(Ch. 18, "Syntactic Analyzer")* Typically you never touch it: the parser builds pieces, runs actions mid-parse, and discards each piece when done — historically to save memory. Only with Tree Construction do you actually produce a tree, and then usually a simplified AST rather than a full parse tree.

Terminology, worth pinning down *(Ch. 18, "Syntactic Analyzer")*: a **parse tree** accurately reflects the parse with the grammar you have, with all tokens present. An **abstract syntax tree (AST)** is a simplified tree, discarding unnecessary tokens and reorganized to suit later processing. **Syntax tree** is the supertype, used when either would do. Fowler also flags that academic texts often use "parse" to mean syntactic analysis only; he uses it much more broadly. "As ever, the terminology in software varies rather more than we would like."

**Layer 3 — output production.** The grammar suffices for recognition; you want output. Three broad ways *(Ch. 18, "Output Production")*: **Embedded Translation**, **Tree Construction**, and **Embedded Interpretation** — all covered in section 13. All require code beyond the grammar, woven in differently depending on how you build the parser: into the handwritten code (recursive descent), passed as action objects into combinators (parser combinator), or embedded as Foreign Code in the grammar file (parser generator).

#### Semantic predicates — and why you should never need one

Sometimes recognition rules cannot quite be expressed in the grammar. A **semantic predicate** is "a hunk of general-purpose code that provides a Boolean response to indicate whether a grammar production should be accepted or not — effectively overriding what's expressed by the rule." *(Ch. 18, "Semantic Predicates")* The classic case is parsing C++ and hitting something like `T(6)`: depending on how `T` was declared, this is a function call or a constructor-style cast, and no context-free grammar can tell you which.

Fowler's design position is a directive, not an observation: **"You shouldn't come across the need to use semantic predicates for a DSL, since you should be able to define the language in such a way as to avoid this need."** If you need one, your DSL syntax is probably wrong.

#### When to use it

*(Ch. 18, "When to Use It")*

- It is the alternative to Delimiter-Directed Translation.
- **Principal disadvantage:** "the need to get used to driving parsing via a grammar, while chopping up via delimiters is usually a more familiar approach." But "it doesn't take long … to get used to grammars, and once you do, they provide a technique that is much easier to use as your DSLs get more complex."
- **The key upside, stated as a design principle:** "the grammar file — itself a DSL — provides a clear documentation of the syntactic structure of the DSL it's processing. This makes it easier to evolve the syntax of the DSL over time."

#### Relationships

Umbrella for BNF, Regex Table Lexer, Recursive Descent Parser, Parser Combinator, and Parser Generator. Its output-production layer is section 13. It is the counterpart of Delimiter-Directed Translation, and its lexer/parser boundary is where most of the difficulty in Alternative Tokenization, Newline Separators, and modular grammars ultimately lives.

> **SDK lens:** The layering is the lesson — lexer → syntactic analyzer → actions → semantic model, each raising the level of abstraction, each with one responsibility. The lexer knows characters and nothing about context; the analyzer knows structure and nothing about meaning; the actions know meaning. **Never push a decision into a layer that lacks the context to make it correctly.** The `FAIL FZ17` case is a leaky abstraction that produces subtly wrong answers, not loud errors. Three more transfers: a declarative spec that documents itself is the whole argument for OpenAPI/protobuf/type-stub artifacts in an SDK — the value is not only that a machine reads it, but that a human can see the whole interface shape in one place. "Many grammars, one language" is the same truth as "many resource models express the same capability," and the model you pick determines the shape of every client. And **recognition versus output is validation versus deserialization** — a yes/no answer is cheap, useful, and worth exposing as an independent capability. Finally, treat semantic predicates as a design smell: an escape hatch that lets imperative code override your declarative spec. If users of your schema or config system constantly reach for the escape hatch, the schema is wrong.

---

### 12.3 BNF *(Ch. 19)*

**Intent:** "Formally define the syntax of a programming language." *(Ch. 19, intent)*

#### The concept

BNF — Backus-Naur Form — is a way of writing grammars that define the syntax of a language. It was invented to describe Algol in the 1960s, and since then BNF grammars have been used both to explain languages and to drive Syntax-Directed Translation.

Fowler opens with an irony: "In a wonderful display of irony, BNF, a language for defining syntax, does not itself have a standard syntax." Any BNF grammar will differ, obviously and subtly, from any other you have seen. "As a result, it's not really fair to call BNF a language; rather, I think of it as a family of languages. When people talk about patterns, they say that with a pattern, you see it differently every time — BNF is very much like that." *(Ch. 19, "How It Works")*

#### The core vocabulary

**Production rules** are the one commonality across all variants. Each rule has a **name** and a **body**; the body describes how to decompose the rule into a sequence of **elements**; elements are either other rules or **terminals**. A terminal is something that is not another rule — typically a literal. When you use BNF with Syntax-Directed Translation, "your terminals will usually be the token types that come out of the lexer." *(Ch. 19, "How It Works")*

Syntactic variants abound. Modern generator-style notation looks like `rule : body ;`; original Algol-style looks like `<rule> ::= body` with rules in angle brackets and newline termination. "You'll see all of these elements varied in different BNFs, so don't get hung up on the syntax."

**Alternatives** (`|`) decompose a rule into one option or another. Used alone they look limited, but "alternatives actually unleash an enormous amount of expressive power" — as the EBNF-to-basic-BNF conversion below shows, everything else reduces to alternatives plus recursion.

**Extracting subrules for intent.** Fowler pulls a single terminal out into its own named rule even though "the `username` rule only resolves to a single identifier, but it's worth doing to more clearly show the intent of the grammar — **similarly to extracting a simple method in imperative code**." That is an explicit statement that grammar writing is subject to the same readability discipline as code.

**Multiplicity symbols (Kleene operators)** — `*` none-or-more, `+` one-or-more, `?` optional — are the same symbols you know from regexes. "Using multiplicity symbols like this makes it much easier to understand grammars."

**Grouping** lets you apply a multiplicity rule to several elements at once, so you can inline subrules. Fowler's advice is usually *don't*: "I wouldn't suggest doing this, because the subrules capture intent and make the grammar much more readable. But there are occasions where a subrule adds clutter and grouping operators work out better."

**Formatting.** Most BNFs ignore line endings, so put each logical piece of a complicated rule on its own line, and the terminating semicolon on its own line to mark the end — Fowler's preference "once the rule becomes too complicated to fit easily on a single line."

**basic BNF vs EBNF.** "Adding multiplicity symbols is usually what makes the difference between EBNF (extended BNF) and basic BNF." Terminology in the wild is muddled; in this book "basic BNF" means without multiplicity symbols, and unqualified "BNF" includes any BNF-like language, EBNF included. A bracket style also exists (`[..]` for optional, `{..}` for repetition, with no equivalent of `+`), common in grammars meant for human consumption and used by the ISO EBNF standard; most tools prefer the regex form.

**Other operators** *(Ch. 19)*: **up-to** (`~'}'` matches everything up to but not including a close brace — equivalent to the regex `[^}]*`) and **range** (`'a'..'z'`). Fowler notes ranges "only make sense in lexical rules, not syntactic rules. They are traditionally also rather ASCII-centric, which makes it difficult to support identifiers in languages other than English" — a real internationalization caveat that still bites.

The operator summary, condensed:

| symbol | meaning |
|---|---|
| `\|` | alternative |
| `*` | none or more (Kleene star) |
| `+` | one or more (Kleene plus) |
| `?` | optional |
| `~` | up-to |
| `..` | range |
| `/` | ordered alternative |

**Lexical vs syntactic rules.** Most approaches separate the two. You *can* define lexical analysis in production-rule style, "but there are usually subtle but important differences as to what kinds of operators and combinations are allowed. Lexical rules are more likely to be close to regular expressions, if only because regular expressions are often used for lexical analysis since they use a finite-state machine rather than a parser's push-down machine."

#### Ordered alternatives and PEGs

Most BNF grammars you meet are **context-free grammars (CFGs)**. A more recent style is the **parsing expression grammar (PEG)**. "The biggest difference between a PEG and a CFG is that PEGs have **ordered alternatives**." *(Ch. 19, "Parsing Expression Grammars")*

In a CFG, the order in which you write alternatives does not affect interpretation. That is usually fine, but "occasionally having unordered alternatives leads to ambiguities." Fowler's worked case: you want to recognize a well-formed ten-digit sequence as a structured US telephone number, but capture anything else as an unstructured raw number. `tel : us_number | raw_number ;` is ambiguous for an input both rules match. An **ordered alternative** forces the rules to be tried in order, first match wins — commonly written `tel : us_number / raw_number ;`.

Practical note: some mainstream tools use unordered syntax but behave like ordered ones — reporting a warning on ambiguity and going with the first alternative that matches. That compromise is worth knowing about, because it is a decent pattern to copy.

#### Converting EBNF to basic BNF

Sometimes necessary, because some generators only accept basic BNF. Multiplicity symbols make BNF easier to follow but "they don't increase the expressive power of BNF." **The key to every transformation is alternatives.** *(Ch. 19, "Converting EBNF to Basic BNF")*

- **Optional:** replace `foo?` with `foo | ` — foo or nothing. Fowler annotates the empty branch with a comment to keep it readable.
- **Folding:** if the parent clause is simple you can fold the alternative into it — `a : b? c` becomes `a : c | b c`. With several optional elements "you get into a combinatorial explosion, which, like most explosions, isn't something that's fun to be in the middle of."
- **Repetition:** use recursion. `x : y*` becomes `x : y x | ` . "It's quite common for rules to be recursive."
- **Left vs right recursion:** `x : y*` can become `x : y x` (right-recursive) or `x : x y` (left-recursive). "Usually your parser will tell you to prefer one over the other due to the algorithm it's using. For example, a **top-down parser cannot do left recursion at all**, while Yacc can do either but prefers right recursion." This is the same constraint that returns as recursive descent's hard limit and as the whole difficulty of Nested Operator Expression.
- **One-or-more:** `x : y+` becomes `x : y | x y`, or `x : y | y x` to avoid left recursion.
- **Intermediate rules:** the transformation often forces you to introduce extra subrules purely to make the recursion work, and always does if you had groups.
- **Cost:** the result "works just fine, but … is much harder to follow. Not only do I lose the multiplicity markers, I also have to introduce extra subrules just to make the recursion work properly. As a result, I always prefer to use EBNF if all else is equal."

#### Code actions: getting data out of a parse

BNF defines syntactic structure, and that is not enough. "It provides enough information to generate a parse tree, but not enough to come up with a more useful abstract syntax tree, nor to do further tasks like Embedded Translation or Embedded Interpretation. So the common approach is to place **code actions** into the BNF in order for the code to react." *(Ch. 19, "Code Actions")* Not every tool works this way — some provide a separate DSL for Tree Construction instead.

**Referring to parsed elements.** Actions usually need the data recognized, not just the fact of recognition. Two approaches, and one is clearly better:
- **Positional variables** (classic Yacc's `$1`, `$2`) index the element's position in the rule. "Positional references are brittle to changes in the grammar."
- **Named labels** (label an element, then refer to it by name) are the modern approach and are better.
- Mechanically, "Parser Generators run code actions through a templating system, which replaces expressions like `$e` with the suitable values."

**Rules returning values.** You can also refer to a *rule* rather than a token, but "returning some rule object like this isn't too helpful, particularly when we are matching larger rules." So generators usually let you **define what a rule returns when it is matched**, which the parent rule can then refer to. Fowler's emphasis here is unusually strong, and it is the most transferable idea in the chapter:

> "This facility, combined with code actions, is extremely important. Often, the rule that gives you the best information about a value isn't the best rule to decide what to do with that data. Passing data up the rule stack allows you to capture information at a low level in a parse, and deal with it at a higher level. Without this, you would have to use a lot of *Context Variables* — which would soon get very messy." *(Ch. 19, "Code Actions")*

**Placement determines timing.** "The position of a code action in a grammar determines when it's executed." An action written between two subrules fires after the first is recognized and before the second. "Most of the time it's easiest to put code actions at the end of a rule, but occasionally you need to put them in the middle." The caveat matters: "the sequence of execution of code actions can be hard to understand, because it depends on the algorithm of the parser. **Recursive-descent parsers are usually pretty easy to follow, but bottom-up parsers often cause confusion.**"

**The big danger.** "One of the dangers of code actions is that you can end up putting a lot of code in them. If you do this, the grammar becomes hard to see, and you lose most of the documentation advantage it brings. I thus strongly recommend that you use *Embedment Helper* when using code actions." *(Ch. 19, "Code Actions")*

#### When to use it

*(Ch. 19, "When to Use It")* — short and pointed:

- "You'll need to use BNF whenever you are working with a *Parser Generator*, as these tools use BNF grammars to define how to parse."
- "**It's also very useful as an informal thinking tool to help visualize the structure of your DSL, or to communicate the syntactic rules of your language to other humans.**"

That second sentence is the entire grammar-first-thinking argument in one line. BNF's value is not only as machine input. Even if you will implement with Delimiter-Directed Translation or hand-rolled code, sketching the grammar is how you *design and communicate* the language.

#### Relationships

The notation used by Parser Generator and, informally, by everything else. Its left-recursion constraint shapes Recursive Descent Parser and Parser Combinator, and drives the whole of Nested Operator Expression. Its code-action mechanism is an instance of Foreign Code, and the discipline that keeps it usable is Embedment Helper.

> **SDK lens:** Sketching a grammar before implementing forces you to decide what the units of your language are and how they nest — the same discipline as writing type signatures or an IDL before the implementation. Three specific transfers. **Named references beat positional references**: Yacc's `$1`/`$2` versus modern labels is precisely the argument for keyword arguments over positional ones, or named struct fields over tuples — positional is brittle under change, and here you have a concrete historical example to point at. **Returning values up the stack removes shared mutable state**: capture data at the level that knows it best, hand it upward to the level that decides what to do with it, rather than stashing it in an ambient context. And **expressive sugar with a defined desugaring is legitimate** — EBNF's multiplicity operators add zero expressive power over basic BNF and improve readability enormously, which is exactly the argument for convenience layers in an SDK, provided the desugaring is well defined.

---

### 12.4 Regex Table Lexer *(Ch. 20, by Rebecca Parsons)*

**Intent:** "Implement a lexical analyzer using a list of regular expressions." *(Ch. 20, intent)*

#### The concept

"Parsers primarily deal with the structure of a language, specifically the way components of the language can be combined. The most basic language components — such as keywords, numbers, and names — can clearly be recognized by the parser. However, we generally separate this stage out into a lexical analyzer. **By using a separate pass to recognize these terminal symbols, we simplify the construction of the parser.**" *(Ch. 20, intro)*

Why this is easy: "Lexical analyzers stay firmly in the space of regular languages, which means we can use standard regular expression APIs to implement them." A Regex Table Lexer is literally a list of regexes, each associated with a terminal symbol. The sketch is a two-column table — pattern on the left, token type on the right. You scan the input, match pieces of it against the regexes, and emit a stream of tokens for the parser to consume.

#### How it works

**The scanning algorithm.** Scan the input from the beginning, matching tokens and consuming characters as you go. Regexes are anchored to the start of the *remaining* string. Walk the list of recognizers in order until one matches; on a match, emit the token, advance the input pointer past the match, and **return to the beginning of the list** — because ordering matters. Repeat until the input is consumed.

**Ordering is a design decision.** "The order of checking the patterns is important so that we can properly handle things like keywords. In the state machine grammar, for example, our keywords also match the rules for identifiers. We order the checks for keywords first, so that the proper token will appear for our keywords." *(Ch. 20, "How It Works")*

**Token-set selection is a design decision.** "Selection of appropriate tokens is a design decision for the lexical analyzer." Parsons deliberately does *not* distinguish four-character codes from names, using a single identifier token for both: "This choice is necessary, since the lexer doesn't have the context to know that a four-letter name should match the identifier token, if it isn't in the position where a code is legal." That is the same argument Fowler makes with `FAIL FZ17` in 12.2, arrived at independently from the implementer's side. Typically the token set covers keywords, names, numbers, punctuation, and operators.

**The table.** Each **recognizer** holds three things: the **token type**, the **regular expression** that recognizes it, and a **Boolean** saying whether this token should be emitted into the output stream. The Boolean is how you handle "semantically meaningless whitespace and comments. While these strings are in the input stream and must be handled by the lexer, we don't pass the corresponding tokens on to the parser." Holding recognizers in an ordered table fixes match precedence and "makes it simple to introduce additional token types."

**Matching detail.** On a match the matcher consumes the matched input and sends the token onward if the output flag is set. The token payload is populated whether needed or not — "generally, token values are only needed for identifiers, numbers, and sometimes operators, but this approach saves us another Boolean flag and simplifies the code." If a scan of the remaining string matches nothing, the whole lexical analysis fails.

**Diagnostics.** "To help with error diagnostics, you can add information to the token about where that token was in the character stream — for example, a line number and column position."

**The structural point worth keeping** *(Ch. 20, example)*: "The implementation is split into the specification of the tokens to recognize and the lexical analysis algorithm itself. This approach makes it easy to add additional token types to the lexer." The token types live in a data table; the scanning engine is separate and generic. Adding a token type is a data change, not a code change.

#### When to use it

*(Ch. 20, "When to Use It")* — close to an unconditional recommendation:

- "While lexical analysis generators, such as Lex, do exist, **there is little need to use them given the prevalence of regular expression APIs.**" The named exception is when your Parser Generator integrates lexing and parsing tightly enough that you should use its lexer instead.
- "The implementation described here is an obvious one. Its performance clearly depends on the specifics of the regular expression API used. **The only time I would suggest not using Regex Table Lexer would be if there is no acceptable regular expression API available.**"
- And a genuinely useful shortcut: "Given the simple syntax of many DSLs, it is possible for this approach to be used to recognize the full language. As long as the language is regular, this approach applies for the parser as well." If your DSL is actually a regular language, **the lexer may be the entire implementation.**

#### Relationships

The shared front end for Recursive Descent Parser and Parser Combinator, and an alternative to a generated lexer under Parser Generator. Its ordered, first-match-wins behavior is the mechanism behind the keyword/identifier conflicts that Alternative Tokenization exists to resolve.

> **SDK lens:** This is the archetype of **table-driven design — varying data plus one generic engine**. Adding a case is a data change, not a code change, which is exactly the shape you want for extensible registries, dispatch tables, rule catalogs, and plugin manifests. Three details generalize. **Ordered matching with first-match-wins** is a simple, explainable resolution rule; when you build a registry whose entries can overlap, define and document ordering semantics explicitly (more specific first) rather than leaving it emergent. **Filter at the earliest layer that can do it correctly** — the output Boolean drops whitespace before the parser can be confused by it, but the token-set discussion shows the limit: only filter or classify where the layer has enough context to be right. And **carry provenance through every intermediate representation**: line and column exist on tokens purely so errors can point at the source, and any library transforming user input owes its users the same.

---

### 12.5 Recursive Descent Parser *(Ch. 21, by Rebecca Parsons)*

**Intent:** "Create a top-down parser using control flow for grammar operators and recursive functions for nonterminal recognizers." *(Ch. 21, intent)*

#### The concept

The motivating tradeoff is stated up front: "Many DSLs are quite simple as languages. While the flexibility of external languages is appealing, using a *Parser Generator* to create a parser introduces new tools and languages into a project, complicating the build process. A Recursive Descent Parser supports the flexibility of an external DSL without requiring a Parser Generator." *(Ch. 21, intro)*

You write it in whatever general-purpose language you already use. It uses **control-flow operators to implement the grammar operators**, and **one function per nonterminal symbol** to implement the production rules.

#### How it works

**Still layered.** A Recursive Descent Parser receives a token stream from a lexical analyzer such as a Regex Table Lexer; the lexer/parser split is unchanged.

**Basic structure.** "There is a method for each nonterminal symbol in the grammar. This method implements the various production rules associated with the nonterminal. **The method returns a Boolean value which represents the result of the match.** Failure at any level gets propagated back up the call stack. Each method operates on the token buffer, advancing the pointer through the tokens as it matches some portion of the sentence." *(Ch. 21, "How It Works")*

**The grammar-operator → control-flow mapping.** Because there are only a few grammar operators, the implementation methods take a small number of shapes:

| Grammar rule | Implementation shape |
|---|---|
| `C : A \| B` | try `A`; if it matched, succeed; else try `B`; else fail |
| `C : A B` | if `A` matched, then if `B` matched, succeed; else fail |
| `C : A?` | try `A`; succeed either way |
| `C : A*` | loop `A` until it fails; always succeed |
| `C : A+` | require one `A`, then loop; fail if the first did not match |

Notes on these *(Ch. 21, "How It Works")*: the alternative implementation "clearly checks one alternative and then the other, **acting more like an ordered alternative**. If you truly need to allow for the ambiguity introduced by unordered alternatives, it might be time for a *Parser Generator*." Sequencing is nested conditionals because you stop as soon as a component fails. The optional case is distinctive in that there is no way to fail.

**Two invariants make the whole thing work** *(Ch. 21, "How It Works")*. The approach is only as clean as it is because the methods behave consistently:

1. **Token buffer management.** "If the method matches what it is looking for, the current position in the input token string is advanced to the point just past the matched input. … If the match fails, the position of the buffer should be the same as it was when the method was called. This is of most importance for sequences. At the beginning of the function, we need to save the incoming buffer position, in case the first part of the sequence matches … but the match for B fails. **Managing the buffer thus allows alternatives to be properly handled.**"
2. **Model/tree population.** "As much as possible, each method should manage its own pieces of the model or create its own elements in the syntax tree. Naturally, any actions should only be taken when the full match has been confirmed. As with the token buffer management for sequences, **actions must be deferred until the entire sequence completes**."

Together these constitute a **transactional discipline**: no side effects until the match is confirmed, and exact state restoration on failure. It is the same shape as speculative execution with rollback, and it is the reason ad-hoc backtracking parsers corrupt their output while disciplined ones do not.

**Actions** stay in separate helper functions, keeping recognition and model population in different methods. Both Tree Construction and Embedded Translation are possible.

**The grammar is still there.** Parsons closes with the observation that reframes the chapter: "One complaint about Parser Generators is that they require developers to become familiar with language grammars. While it is quite true that the syntax of the grammar operators does not appear in the recursive descent implementation, **a grammar clearly exists in the methods. Changing the methods changes the grammar. The difference is not in the presence or absence of the grammar but in how the grammar is expressed.**" *(Ch. 21, "How It Works")*

One practical consequence from the worked example: because a single-pass translation cannot see declarations that come later, your helper functions "must allow for a reference to a state that has not yet been defined. **This property holds true for all the implementations that don't use *Tree Construction*.**" Forward references are a design problem you inherit the moment you choose single-pass translation.

#### When to use it

*(Ch. 21, "When to Use It")*

**Strengths:**
- "**The greatest strength of Recursive Descent Parser is its simplicity.** Once you understand the basic algorithm and how to handle various grammar operators, writing a Recursive Descent Parser is a simple programming task."
- "You then have a parser in an ordinary class in your system." No build step, no generated code, no foreign toolchain.
- "**Testing approaches work in the same way they always do; in particular, a unit test makes more sense when the unit is a method, just like any other.**"
- "Since the parser is simply a program, it is easy to reason about its behavior and debug the parser. … making the tracing through the parse much easier to discern." Ordinary debuggers work.

**Weaknesses:**
- "**The most serious shortcoming of Recursive Descent Parser is that there is no explicit representation of the grammar.** By encoding the grammar into the recursive descent algorithm, you lose the clear picture of the grammar, which can only live in documentation or comments. Both *Parser Combinator* and *Parser Generator* have an explicit statement of the grammar, making it easier to understand and evolve."
- "Another problem … is that you have a top-down algorithm that can't handle left-recursion, which makes it more messy to deal with *Nested Operator Expressions*."
- "Performance will also be usually inferior to a Parser Generator. In practice, these disadvantages aren't such a factor for DSLs."
- **The practical tripwire is look-ahead:** "One of the factors that can make it easy to deal with is limited look ahead — that is, how many tokens the parser needs to peek forward to determine what to do next. **Generally, I wouldn't use Recursive Descent Parser for a grammar that requires more than one symbol of look ahead; such grammars are better suited to Parser Generators.**"

#### Relationships

Consumes a lexer (12.4). The hand-written sibling of Parser Combinator (12.6), which factors the same operator logic out into composable objects. Constrained by the left-recursion limit from BNF (12.3), which is what makes Nested Operator Expression (13.7) painful. Some Parser Generators emit recursive descent parsers precisely because the generated code is easy to follow when debugging a grammar.

> **SDK lens:** **"The grammar exists whether or not you write it down."** This generalizes hard: your library has a protocol, a schema, or a state machine whether or not any artifact states it. The only choice is whether it is explicit and reviewable or implicit and scattered through the code. Second: **transactional semantics on failure.** Any library operation that can partially succeed should either fully commit or fully restore — partial mutation on failure is exactly the defect this discipline prevents. Third: **ordinary code has ordinary tooling.** Being "a parser in an ordinary class in your system" means normal unit tests, debuggers, stack traces, and refactoring, which is the standing argument against introducing codegen machinery for problems small enough to solve directly. Finally, **define your complexity tripwire before you start.** "More than one symbol of look-ahead → use a generator" is a concrete, checkable rule for abandoning the hand-rolled approach; every hand-rolled component in an SDK deserves an equivalent stated in advance.

---

### 12.6 Parser Combinator *(Ch. 22, by Rebecca Parsons)*

**Intent:** "Create a top-down parser by a composition of parser objects." *(Ch. 22, intent)*

#### The concept

The positioning is explicit: "Even though our premise is that Parser Generators are not nearly as difficult to work with as they are perceived to be, there are legitimate reasons to avoid them if possible. **The most obvious issue is the additional steps in the build process required to first generate the parser and then build it.** While Parser Generators are still the right choice for more complex context-free grammars, particularly if the grammar is ambiguous or performance is crucial, directly implementing a parser in a general-purpose language is a viable option." *(Ch. 22, intro)*

The pattern itself: "A Parser Combinator implements a grammar using a structure of parser objects. Recognizers for the symbols in the production rules are combined using *Composites [gof]*, which are referred to as combinators. **Effectively, parser combinators represent a *Semantic Model* of a grammar.**" That last sentence is the crux — a parser combinator structure *is* the grammar, alive as objects.

Where the name comes from: "**Combinators are designed to be composed to create more complex operations of the same type as their input.** So, parser combinators are combined to make more complex parser combinators. In functional languages, these combinators are first-class functions, but we can do the same with objects in an object-oriented environment." *(Ch. 22, "How It Works")*

#### How it works

**Still layered** — a lexer produces tokens, and the combinator structure operates on the token stream.

**The build-up.** Start with the base cases: recognizers for terminal symbols. Then use combinators implementing the grammar operators (sequence, alternative, optional, list) to build up the production rules. "Effectively, for each nonterminal in our grammar, we have a combinator for it, just like in Recursive Descent Parser we have a recursive function for each nonterminal."

Each combinator is responsible for "recognizing some portion of the language, determining if there is a match, consuming the relevant tokens from the input buffer for the match, and performing the required actions. **These operations are the same as those required by the recursive functions in Recursive Descent Parser.**"

**The central design insight** *(Ch. 22, "How It Works")*:

> "What's really happening here is that we abstract out the fragments of logic associated with processing the grammar operators for top-down parsing and create the combinators to hold that logic. While a *Recursive Descent Parser* combines those fragments with function calls in inline code, a Parser Combinator combines these by linking together objects in an *Adaptive Model*."

Same algorithm, same operator semantics as recursive descent — but the *composition* moves out of code and into a runtime object graph. It is a refactoring from "control-flow logic duplicated at every rule" to "logic implemented once per operator, composed as data."

**Combinator signature.** A combinator accepts the status of the match so far, the current token buffer, and possibly a set of accumulated action results; it returns a match status, a possibly altered token buffer, and a set of action results.

**The operator combinators** each mirror the recursive descent shape exactly — alternative tries each in turn and returns the first success (leaving the buffer unchanged on total failure); sequence steps through components and resets the buffer if any fails; optional always succeeds; the list forms loop. The invariant everything relies on is the same as recursive descent's: "If the match succeeds, the tokens relating to that match are consumed in the token buffer. If the match fails, the combinator returns an unaltered token buffer."

**Where the power comes from.** "The combinator implementations shown here are direct implementations of specific rules. **The power of parser combinators comes from the fact that we can construct the composite combinators from the component combinators.**" A rule `C : A B` becomes a *declaration* — roughly:

```
C = Sequence(A, B)
```

"**where the logic implementing the sequencing is shared across all such rules.**" That is the payoff sentence for composability: write each operator's logic once, then express any grammar as a declarative assembly of operator instances.

**Actions.** In Tree Construction the actions build AST nodes as the parse proceeds; in Embedded Translation they populate the Semantic Model. Terminal combinators populate a match value on success and invoke the action on it; sequence and list combinators call their action on the *list* of match values from their components; alternatives run only the selected branch's action; optionals run theirs only on match. Building an AST is exactly this: a list combinator's action creates a node and makes the component subtrees its children.

**The language-dependent surface.** "The invocations for the actions are relatively straightforward. **The challenge is getting the proper action methods associated with the combinator.** In languages with closures or other ways of passing functions as parameters, we could simply have the details of the action method passed into the constructor as a function. In languages without closures … we need to be a bit more clever. One approach is to extend the operator classes with classes specific to a particular production rule and override the action method." *(Ch. 22, "Dealing with the Actions")* Same design; two surface syntaxes.

**The functional style.** Relax the assumption that action results and the token buffer live in background state, and "a combinator is a function that maps an input combinator result value to an output combinator result value." *(Ch. 22, "Functional Style of Combinators")* The result value carries three things: the token buffer state, the match status, and the cumulative action results. "In this style, the saves are unnecessary since the input parameter's value remains valid." Threaded immutable state turns "restore on failure" into "return the input unchanged" — there is nothing to restore because nothing was mutated.

Two structural details from the worked implementation worth keeping. First, every recognizer opens with a **guard clause**: if the inbound match status is already false, return the inbound result immediately, so failure short-circuits an entire composite with no special handling at any node. Second, the base combinator carries an **action hook with an empty default body**, so most combinators need no action code at all and domain behavior lives only in the handful of rule-specific overrides. A small, reusable, fully generic operator library plus a thin layer of rule-specific behavior *is* the whole architecture.

A judgement call from the same example: separate classes were made for optional and required sequences, sharing an implementation, "rather than introducing an optional operator and adding another level of production rules to the grammar" — **the implementation structure is allowed to differ from the canonical grammar structure when doing so makes the grammar simpler.**

#### When to use it

*(Ch. 22, "When to Use It")*

- **The positioning line:** "This approach occupies a nice middle ground between *Recursive Descent Parser* and using a *Parser Generator*."
- **Explicit grammar without the build cost.** "The grammar in a Recursive Descent Parser is implied in the functions but is difficult to read as a grammar. With the Parser Combinator approach, **the combinators can be defined declaratively** … So with Parser Combinator, you get a reasonably explicit grammar without the build complications that tend to come with Parser Generator."
- **Language fit.** "**Functional languages are an obvious choice** to implement a Parser Combinator, given their support for functions as first-class objects which allows for passing an action function as a parameter to the combinator constructor. However, implementations in other languages are quite possible too."
- **The same top-down restrictions apply** as for recursive descent: no left recursion, look-ahead limits, weaker performance.
- **The same debugging advantages apply**, "in particular the ease of reasoning about when actions are performed. … the control algorithm of the parsing can be tracked using the same tools we use for debugging other programs."
- **The layering payoff:** "**Indeed, the Parser Combinator approach coupled with an operator library or tested operator implementations allows the language implementer to focus on the actions rather than the parsing.**"
- **Downsides:** "The biggest downside to a Parser Combinator is that **you still have to build it yourself**. In addition, you won't get the more sophisticated parsing and error handling features that a mature Parser Generator gives you out of the box."

#### Relationships

The middle ground between Recursive Descent Parser (12.5) and Parser Generator (12.7). Structurally it is an Adaptive Model (14.1) whose configuration is a grammar. It is also, as Parser Generator notes, the natural implementation for a generator that *interprets* a grammar at runtime instead of generating code.

> **SDK lens:** This is the most directly transferable chapter in the whole parsing section, because a combinator library is a template for composable API design: **(a)** a small set of primitive values, **(b)** a small set of operators that take values of the type and return values of the same type, **(c)** closure under composition, **(d)** a uniform result type threaded through the whole structure. An API with that shape composes without limit and can be learned in an afternoon — contrast it with fifty unrelated methods. **Same-type-in / same-type-out is the constraint to protect above all others**; the moment an operator returns a different type from its inputs, composition stops. The rest follows: implement the logic once per operator and stop duplicating control flow at every case (query builders, validators, middleware chains, retry policies, stream pipelines, test fixtures); prefer **threaded explicit state over ambient mutable state**, because pure `Result → Result` functions need no save/restore and make every value's provenance obvious; use **hook methods with no-op defaults** so users implement only what they care about; and let **guard clauses propagate failure through a composite for free**. Note too that **language capability determines the ergonomic surface** — closures mean "pass the behavior in"; no closures means "subclass and override." When porting an SDK across languages, the model transfers but the idiom for supplying behavior must be adapted.

---

### 12.7 Parser Generator *(Ch. 23)*

**Intent:** "Build a parser driven by a grammar file as a DSL." *(Ch. 23, intent)*

#### The concept

"A grammar file is a natural way of describing the syntactic structure of a DSL. Once you have a grammar, **it's tedious work to turn it into a handwritten parser, and tedious work should be done by a computer.**" *(Ch. 23, intro)* A Parser Generator consumes the grammar file and generates the parser. Two consequences: "The parser can be updated merely by updating the grammar and regenerating," and "The generated parser can use efficient techniques that would be hard to build and maintain by hand."

Note the reflexive structure. The Parser Generator is *itself* a DSL tool: the grammar file is a DSL, and the generator is its code generator. It is Fowler's favourite worked example of a DSL that has demonstrably paid for itself over decades.

Fowler limits his scope deliberately: "Building your own Parser Generator is no simple task, and anyone who is capable of doing such a thing is unlikely to learn anything from this book. So, here I'll only talk about *using* a Parser Generator." *(Ch. 23, "How It Works")*

#### How it works

**The workflow:** write a grammar file in the particular BNF dialect your generator uses; run the tool to produce parser source; compile that source with the rest of your code; parse files. "Don't expect any standardization here; if you change your Parser Generator, you will have to write a new grammar."

**Codegen vs interpretation.** "Most Parser Generators use code generation, which may allow you to generate a parser in different host languages. **There's no reason, of course, why a Parser Generator shouldn't be able to read a grammar file at runtime and interpret it, perhaps by building a *Parser Combinator*.** Parser Generators use code generation due to a mix of tradition and performance considerations — particularly since they are usually aimed at general-purpose languages." *(Ch. 23, "How It Works")* That is an explicit bridge between 12.6 and 12.7: combinators are the runtime-interpretation answer to the same problem.

**Treating generated code.** "Mostly, you treat the generated code as a black box and don't delve into it. It is, however, occasionally useful to follow what the parser is doing — particularly if you are trying to debug your grammar. In this case, there is an advantage in the Parser Generator using an algorithm that's easier to follow, such as generating a *Recursive Descent Parser*."

#### Embedding actions

"Syntactic analysis produces a parse tree; to do something with that tree, we need to embed further code. We place the code in the grammar using *Foreign Code*. **Where we place it in the grammar indicates when the code is executed.**" *(Ch. 23, "Embedding Actions")*

The facilities and the cautions:

- **Referring to tokens:** positional (`$1`, `$2`) versus by name. "With ANTLR, the actions refer to grammar elements by name, which is usually better than by position."
- **Host language coupling:** "The actions are usually woven into the generated parser while it is being generated. As a result, the embedded code is usually in the same language as the generated parser."
- **Returning values from subrules to parents:** "**A common and useful facility is thus to allow a subrule to return data to its parent.** … The ability to return values from rules can make it much easier to write parsers — in particular, **it can remove a lot of *Context Variables***." Some generators can also push data *down* as arguments to subrules, "which allows a lot of flexibility in providing context to subrules."
- **Action placement defines call timing** — an action in the middle of a rule fires after the preceding subrule is recognized.
- **The dominant failure mode, and its fix:** "When using *Syntax-Directed Translation*, a common problem I've seen is to put too much host code in the grammar. When this happens, it's hard to see the structure of the grammar and the host code is difficult to edit — and requires a regeneration to test and debug. **The key pattern here is *Embedment Helper* — shift as much code as you can to a helper object. The only code in the grammar should be single method calls.**" *(Ch. 23, "Embedding Actions")*
- **Semantic predicates**, restated here: "like an action, a block of Foreign Code, but it returns a Boolean that indicates whether the parse for the rule succeeds or fails. **Actions don't affect the parsing, but semantic predicates do.**" They "usually appear in more complicated languages, so they tend to crop up more often in general-purpose languages. But if you're having difficulty getting a grammar to work with the grammar DSL itself, then a semantic predicate opens the door to more complicated processing." Read alongside 12.2's directive: for a DSL you control, needing one means redesigning the DSL.

#### The documented silent-failure traps

The Hello World walkthrough exists for a reason Fowler states plainly: "**It's good to get a really simple thing going just to ensure you know what the moving parts are and how they fit together.**" *(Ch. 23, "Hello World")* Along the way he documents two traps where a mature tool's default behavior is to **silently succeed on bad input** *(Ch. 23, "Writing the Basic Grammar")*:

1. **Define a catch-all illegal-character lexer rule, last.** Without it, "the lexer … quietly ignore[s]" tokens that fit no rule instead of reporting an error.
2. **Put end-of-file at the end of the top rule.** "If you don't put the EOF at the end of the top rule, ANTLR won't report errors. **It effectively stops parsing at the first point of trouble and doesn't think anything went wrong.**" Fowler notes this has "bitten me a couple of times" and is "particularly awkward" because the tool's own interactive interpreter *will* show the error, "so it's easy to get confused, frustrated, and ready to do violent acts against your monitor."

A third trap is about testing rather than grammar hygiene, and it is the important one *(Ch. 23, "Hello World")*: a test that merely runs the parser over *valid* input and passes "isn't very helpful. All it indicates is that the ANTLR parser didn't blow up when it read the file. That, however, may not even tell you that it read the file without problems. **So it's useful to feed the parser some invalid input.**" And that test will initially fail to fail, because the generator's error recovery is designed to keep going: "ANTLR is determined to keep on parsing and recover from errors as much as possible. In general, this is a good thing, but particularly early on it can be frustrating to find ANTLR so tolerant and determined." The fix is to override the error-reporting hook so errors are recorded, then throw if any were recorded.

Two build-integration notes from the same walkthrough: generated sources belong in their own directory, kept apart from core sources and excluded from source control; and a hand-written wrapper class is still worth having to orchestrate the generated lexer and parser, even when using Generation Gap.

#### Delegation vs Generation Gap for attaching your code

Two ways to connect your Embedment Helper to the generated parser *(Ch. 23, "Using Generation Gap")*:

1. **Delegation** — declare a helper object as a field on the generated parser, and have the grammar's actions delegate to it.
2. **Generation Gap** — hand-write an abstract superclass and configure the generator to make the generated parser extend it. The grammar then calls helper methods bare, and you no longer need to override error reporting inside the grammar, because the handwritten superclass does it.

Fowler's verdict: "**Both the inheritance and delegation relationships have their strengths for the Embedment Helper. I don't have a strong opinion on the best one to use, and use both of them in this book's examples.**"

#### When to use it

*(Ch. 23, "When to Use It")*

**Advantages:**
- "**For me, the greatest advantage of using a Parser Generator is that it provides an explicit grammar to define the syntactic structure of the language you're processing. This is, of course, the key advantage of using a DSL.**" The argument for a Parser Generator is a special case of the argument for DSLs generally.
- "Since Parser Generators are primarily designed to handle complicated languages, they also give you much more features and power than you would get by writing your own parser. While these features may require some effort to learn, you can usually start with a simple set and work your way up."
- "Parser Generators may provide good error handling and diagnostics, which … can make a big difference when trying to figure out why your grammar isn't doing what you think it should."

**Downsides:**
- "You may be in a language environment where there isn't a Parser Generator — and it's not the kind of thing you should be writing yourself."
- "Even if there is one, you may balk at introducing a new tool to your mix."
- "Since Parser Generators tend to use code generation, they complicate the build process, **which can be a significant irritant.**"

#### Relationships

The far-right end of the explicitness spectrum. Consumes BNF (12.3) and Foreign Code (13.5); disciplined by Embedment Helper (15.3); can be structured with Generation Gap (15.6). Its runtime-interpretation alternative is Parser Combinator (12.6). All three output strategies in section 13 are typically implemented through its code actions.

> **SDK lens:** "Tedious work should be done by a computer" — with the price named. You gain a declarative source of truth, an efficient generated implementation, and regeneration-on-change; you pay with a new tool, a more complicated build, and generated code you must treat as a black box. Fowler calls build complication "a significant irritant," which is worth taking seriously before adopting codegen in a toolchain. Note also that **the runtime-interpretation alternative is always available**: when tempted by codegen, ask whether an interpreted or combinator implementation gets you the same declarative artifact without the build step, since codegen is often chosen for tradition and performance rather than necessity. **Keep the escape hatch in any declarative artifact thin** — grammar, schema, config, template — because logic embedded in a spec cannot be unit tested without regenerating and destroys the spec's readability. And **design for loud failure**: both documented traps are cases where a mature tool's default is tolerant recovery. A library whose default is tolerant must make strict mode easy and obvious, and its documentation must say loudly that a passing run is not evidence of a correct parse. Test with invalid input, not just valid input — "all it indicates is that the parser didn't blow up" applies to every parser, deserializer, validator, and config loader an SDK ships.

---

### 12.8 Choosing a parsing strategy

Assembled from the "When to Use It" sections of Chapters 17, 18, 21, 22, and 23:

| | Delimiter-Directed | Recursive Descent | Parser Combinator | Parser Generator |
|---|---|---|---|---|
| Grammar explicit? | No grammar at all | Implicit in functions | Explicit as composed objects | Explicit as a BNF DSL |
| Learning curve | Lowest — familiar techniques | Grammar concepts, simple algorithm | Grammar + combinator library | Grammar + a new tool |
| Build complexity | None | None | None (maybe a library) | Codegen step; "a significant irritant" |
| Debuggability | Ordinary code | Ordinary code, easy to trace | Ordinary code + object graph | Black-box generated code |
| Handles complexity | Poorly; messy fast | Simple grammars; ≤1 symbol look-ahead; no left recursion | Same top-down limits as recursive descent | Best: ambiguity, performance, error recovery |
| Error handling | Roll your own | Roll your own | Roll your own | Mature, out of the box |
| Verdict | Only for simple autonomous statements, or a team not ready for grammars | The simplest thing that is a real parser | "A nice middle ground" | Right for complex or ambiguous grammars, or when you want the explicit grammar most |

**The decision tripwires, stated explicitly in the text.** These are the value of the whole section, because each is checkable before you have written much code:

- Your ad-hoc line processing **starts wanting a framework** → you are most of the way to Syntax-Directed Translation anyway; go there *(Ch. 17)*.
- Your grammar needs **more than one symbol of look-ahead** → Parser Generator *(Ch. 21)*.
- Your grammar is genuinely **ambiguous** and you need unordered alternatives → Parser Generator *(Chs. 21, 22)*.
- **Left recursion or nested operator expressions** matter → not a top-down parser *(Chs. 19, 21)*.
- Your DSL is actually a **regular language** → a Regex Table Lexer may be the entire implementation *(Ch. 20)*.
- You find yourself needing a **semantic predicate** for a DSL you control → redesign the DSL instead *(Ch. 18)*.

And the principles that recur across all seven patterns: layer with honest capability boundaries and never push a decision into a layer that lacks the context to make it correctly; make the structure explicit, or at least accept that it is implicit and still there; keep the declarative artifact thin; prefer composition to duplication; use transactional semantics on failure, or thread the state so there is nothing to restore; prefer named references to positional ones; prefer explicit data flow to ambient context; fail loudly by default; and apply the same naming and extraction discipline to specs that you apply to code.

---

## 13. Producing output from a parse

A parser on its own only *recognizes* structure. Something has to produce a result. Chapters 24–26 are the three output-production strategies available once you have chosen Syntax-Directed Translation:

1. **Tree Construction** — the parser builds an AST; a separate tree-walk populates the Semantic Model. Two passes, two simple transformations.
2. **Embedded Translation** — parser actions populate the Semantic Model directly during the parse. One pass, one transformation.
3. **Embedded Interpretation** — parser actions compute the *answer* directly during the parse. No Semantic Model at all.

Chapters 27–30 are supporting tactics and recurring problems: escaping the DSL into another language (Foreign Code), bending the lexer from inside the parser (Alternative Tokenization), the perennial arithmetic-expression difficulty (Nested Operator Expression), and the surprisingly fiddly business of using newlines as separators. Chapter 31 collects two unfinished topics — syntactic indentation and modular grammars — that Fowler flags as more preliminary than the rest of the book.

The through-line for all of them: **the Semantic Model is the centre of gravity**, and each tactic is judged by whether it keeps the grammar clean and the model-population code understandable.

---

### 13.1 Tree Construction *(Ch. 24)*

**Intent:** "The parser creates and returns a syntax tree representation of the source text that is manipulated later by tree-walking code." *(Ch. 24, intent)*

#### The concept

Any Syntax-Directed Translation parser already builds a syntax tree implicitly as it parses — the tree grows on the parse stack and is pruned as each rule completes. Tree Construction says: do not throw that structure away. Add parser actions that assemble an explicit tree in memory as the parse proceeds. When the parse finishes you hold a whole tree representing the script, and you can walk it as many times as you like, most commonly to populate a Semantic Model.

The critical refinement is that the in-memory tree **should not** be a faithful parse tree. It should be an **abstract syntax tree**: a deliberate simplification tuned to how you intend to use it. Fowler's terms *(Ch. 24, "How It Works")*: a *syntax tree* is the general term for any hierarchic structure formed by parsing; a *parse tree* corresponds directly to the input text; an *AST* makes simplifications based on usage.

His illustration: for a block delimited by `events … end`, the parse tree contains nodes for the literal keywords. Those words earned their keep during lexing — they marked the boundaries of the declaration — but once the structure exists as a tree they are pure clutter, so the AST drops them. And the AST is *purpose-relative*: if all you needed were the event codes, you would drop the names and the per-event nodes too. "Obviously, different ASTs might be needed for different reasons."

#### How it works

Two mechanisms for building the tree:

1. **Code actions in the grammar.** Each rule carries an action that constructs the node for that rule and attaches the nodes returned by its subrules. The ability of code actions to *return a value* is what makes this workable — each action assembles its own node and hands it upward. Fowler notes the resulting code is "very regular—indeed rather boring," and offers the maxim that **boring code usually means you need another abstraction** *(Ch. 24, "Tree Construction Using Code Actions")*.
2. **A tree-construction DSL supplied by the Parser Generator.** Some tools provide a rewrite notation where a rule declares the shape of the node it should produce — a node type followed by its children. This "greatly simplifies building up an AST," and is exactly the missing abstraction the boring code was pointing at. Tools with this feature typically hand you the raw parse tree if you supply no rewrite rules — "but you almost never want the parse tree."

A tree built this way consists of **generic** nodes — a node type plus generic tokens as children — not domain objects. You *could* have the actions construct real domain objects directly, but Fowler explicitly prefers not to:

> "I prefer to have a generic AST and then use second-stage processing to transform that into a Semantic Model. I'd rather have two simple transformations than one complicated one." *(Ch. 24, "How It Works")*

The second stage typically runs in phases: build the AST; walk it to build **symbol tables** (name → element maps); then walk it again to assemble the Semantic Model, resolving names through those tables. The AST node type grows a few convenience query methods — get children of a type, get the sole child of a type, get the text of a child of a type — which Fowler observes "feels rather like a dictionary lookup but using the same tree data structure."

#### Design principles from the worked example

These come from the tokenizing and parsing discussion and generalize well beyond any one tool *(Ch. 24, "Tokenizing" and "Parsing")*:

- **Push ambiguity to the layer that has context.** Where names and codes have overlapping lexical shapes, use **one token type for both and let the parser sort it out**. The stated consequence: the parser will no longer catch a malformed code — that check moves into your own semantic processing. A deliberate, acknowledged trade, not an accident.
- **Keywords written as literals in parser rules** are generally easier to read than named lexer rules.
- **Don't add statement separators until you need them.** A grammar that skips all whitespace including newlines lets the script be formatted freely and needs no separators at all. "Often, DSLs can get away with no statement separators because the statements are very limited. … As with most things, don't put them in until you actually need them."
- **Skipping whitespace loses your line and column numbers,** and good error reports need them. The tooling answer is a *hidden channel* — whitespace tokens emitted on a separate channel, available for error handling but invisible to the parsing rules. The general lesson: **discarded input is still needed for diagnostics; route it somewhere rather than dropping it.**
- **Keep tree-construction rules simple and the tree easy to walk.** The stated aim each time is "collecting together appropriate clumps of the DSL and putting them under a node that describes what that clump represents."

#### When to use it

Tree Construction and Embedded Translation are the two ways to populate a Semantic Model while parsing; Embedded Translation does it in one step, Tree Construction in two with the AST as an intermediate. Fowler's decision factors *(Ch. 24, "When to Use It")*:

- **Complexity of the transformation.** The argument for Tree Construction is that it splits one transformation into two simpler ones. Whether that is worth an intermediate model depends entirely on how complex the transformation is: "The more complex the transformation is, the more useful an intermediate model can be."
- **Multiple passes.** This is the big one. If you need several passes over the script — most commonly because of **forward references** — Tree Construction wins easily. "With Tree Construction it's easy to walk the tree many times as part of later processing." Embedded Translation is stuck with a single pass and must resort to find-or-create tricks and context variables.
- **Parser Generator support.** Some tools give you no choice. Most let you choose, but if the tool makes AST building really easy, that tips the balance.
- **Memory.** Tree Construction stores the AST, so it uses more. "In most cases, however, this won't make any appreciable difference. (Although that certainly used to be a big factor in earlier days.)"
- **Reuse.** You can process the same AST several ways to populate different Semantic Models, reusing the parser. Handy — though if tree construction is cheap it may be simpler to build different ASTs for different purposes, or to transform once into a Semantic Model and use *that* as the basis for further transformations.
- **Side-effect safety** (argued from the other side in Ch. 25): a tree-construction action only returns a subtree, so it cannot suffer the "action fired at an unexpected moment" problem that side-effecting actions have.

#### Relationships

Alternative to Embedded Translation (13.2) and Embedded Interpretation (13.3). Populates a Semantic Model, typically via symbol tables for name resolution. Uses Foreign Code (13.5) when built with code actions; the tree-construction DSL is the cleaner alternative. Embedment Helper (15.3) normally keeps the grammar thin, though Fowler skips it when the tree-building actions are so simple that a helper would not read better. Ch. 29 notes it "often reduces" the code-action mangling that Nested Operator Expression grammars suffer.

> **SDK lens:** **Two simple transformations beat one complicated one** is the single most transferable idea here. In SDK terms: wire format → normalized intermediate representation → domain object, rather than deserializing straight into rich domain types. Each stage is independently testable, and the intermediate representation gives you somewhere to stand for validation, diagnostics, and multiple back ends. A generic IR also buys **re-targeting** — one parse, many outputs (validator, formatter, doc generator, executor) — the same argument as a compiler IR or a document tree in a markup library. **Multi-pass resolution is the answer to forward references**: if your builder or config API lets users reference things declared later, you need a collect-then-link design, not a single streaming pass, and retrofitting that is painful. **Boring, highly regular glue code is a missing abstraction** — if every method in a layer is identical modulo a name, generate it or introduce a declarative form. And preserve source positions even for tokens you discard, because users judge a parser by its error messages.

---

### 13.2 Embedded Translation *(Ch. 25)*

**Intent:** "Embed output production code into the parser, so that the output is produced gradually as the parse runs." *(Ch. 25, intent)*

#### The concept

A pure parser builds an internal parse tree and throws it away; something more is needed to get a Semantic Model out. Embedded Translation puts the model-population code *inside* the parser: as each clause of the input language is recognized, an action fires that creates or updates the corresponding Semantic Model objects. By the time the parse finishes, the model is built. One pass, no intermediate tree.

#### How it works

Model-population code is attached where language clauses are recognized. "Most of the time, this implies that the model population code is placed where a clause of the input language is recognized, although in practice you may place hunks of population code at various points." *(Ch. 25, "How It Works")* With a Parser Generator this population code is Foreign Code woven into the grammar file, which nearly all generators support.

**The side-effect hazard.** Actions with side effects "can often be executed in unexpected places, depending on exactly how rules are recognized by the parsing algorithm." Because the parser may backtrack, reorder, or reach a rule by an unexpected path, an action that mutates shared state can fire at a moment you did not intend. Tree Construction is immune, because its actions only return a subtree. Fowler's rule of thumb is worth memorizing verbatim: **"If you find yourself getting into a tangle with Embedded Translation side effects, that's a sign that you should switch to Tree Construction."** *(Ch. 25, "How It Works")*

Two structural problems the worked example exposes *(Ch. 25, "Miss Grant's Controller")*:

**1. Hierarchic context.** An action nested inside an outer construct needs to know which instance of that construct it belongs to. Fowler warns against the mental model that "Embedded Translation is like SAX processing of XML" — it is "somewhat true, in that the embedded code just works with one rule at a time. But it's also misleading, because Parser Generators can give you much more context during the execution of the code so you don't need to keep it around yourself." Concretely, generators that let you pass parameters *into* rules let you push the enclosing context down to nested rules. **Prefer parameter passing to a context variable.**

**2. Forward references.** A construct names something not yet declared. In many DSLs you can arrange the language so nothing refers to an identifier that has not been declared yet, but some domains cannot be arranged that way. Tree Construction solves it with multiple passes; Embedded Translation has no such option, so the fix is an **"obtain" (find-or-create) operation** applied to *both* references and declarations — mentioning something implicitly declares it if it does not already exist.

- The cost: a misspelled name silently produces a blank object as the reference target. You can accept that; but "It's common, however, to check declarations against usage, in which case we need to keep track of the states created by use and ensure that they are all declared too."
- Some context defeats the tool regardless — a rule like "the start state is the first state mentioned" required "what is effectively a context variable," and Fowler says so apologetically.
- Constructs that appear before there is anything to attach them to get accumulated in a field and applied after the parse. Fowler notes that post-parse cleanup following syntactic analysis is normal, and that it is also where **semantic analysis** naturally lives.

#### When to use it

*(Ch. 25, "When to Use It")*

**For:**
- "The biggest appeal of Embedded Translation is that it provides a simple way to handle both syntactic analysis and model population in one pass." With Tree Construction you write both tree-building code *and* a tree-walking populator. "Particularly for simple cases, which many DSLs are, this two-stage process can be more trouble than it's worth."

**Against:**
- **It encourages complex grammar files**, "usually due to a poor use of Foreign Code." Discipline with Foreign Code — that is, an Embedment Helper — mitigates this, "but a strength of Tree Construction is that it helps to enforce the discipline." In other words: **Tree Construction makes the good structure the default; Embedded Translation makes it a matter of willpower.**
- **Single-pass only**, so forward references are tricky and often require a context variable, "which can further complicate parsing."
- Tool support pushes the other way: "The better the tree-building features of your Parser Generator the more appealing Tree Construction becomes."

**The summary rule:** "The upshot of all this is that the simpler the language and parser, the more appealing is Embedded Translation."

#### One observation worth carrying beyond this chapter

"Most of the time, the BNF rules don't vary if you use different parsing patterns; what changes is the supporting code around the BNF." *(Ch. 25, "Miss Grant's Controller")* That is: **the grammar is the stable asset; the output-production strategy is a swappable layer on top of it.** It is why the same DSL can be presented three ways with the same core rules — and why choosing between these three patterns is a reversible decision.

#### Relationships

Direct alternative to Tree Construction (13.1). Depends on Foreign Code (13.5) as the embedding mechanism and on Embedment Helper (15.3) to keep that Foreign Code down to a single call per action. Needs a context variable where the tool cannot supply context. Symbol tables still appear, built incrementally rather than in a dedicated pass.

> **SDK lens:** **Streaming, one-pass APIs trade simplicity for expressiveness.** A SAX-style or event-callback API is cheap and fast, but every cross-cutting relationship becomes hidden mutable state in the consumer. If your format has forward references or hierarchic context, a document/tree API will serve users better. **Find-or-create is the standard trick for forward references in one-pass builders** — and it carries the standard cost, that typos become silently created empty objects. If you use it, add a "declared versus merely referenced" audit at the end; this applies directly to config loaders, identity maps, DI containers, and resource-graph tools. **Push context down as explicit parameters rather than parking it in shared mutable state.** And note the general hazard: **callbacks with side effects can fire at surprising times.** If your API invokes user callbacks from inside a speculative or backtracking process, either document that clearly or restructure so callbacks return values instead of mutating.

---

### 13.3 Embedded Interpretation *(Ch. 26)*

**Intent:** "Embed interpreter actions into the grammar, so that executing the parser causes the text to be directly interpreted to produce the response." *(Ch. 26, intent)*

#### The concept

Sometimes you do not want a model at all — you want an *answer*. Run the script, get the number. Embedded Interpretation interprets the DSL script *during* parsing: the result of the parse *is* the result of the script. Fowler's sketch is `1 + 2 * 3` collapsing to `6` and then `7` as the parse proceeds.

#### How it works

"Embedded Interpretation works by evaluating DSL expressions as soon as possible, collating results together, and returning the overall result." *(Ch. 26, "How It Works")* No Semantic Model is built. As the parse recognizes each fragment it interprets as much as it can, and each rule's action combines the values returned by its subrules — a typed return value propagating up the rule hierarchy.

#### When to use it

*(Ch. 26, "When to Use It")* — Fowler is unusually blunt; this is the pattern he least recommends.

- "I'm a big proponent of a Semantic Model, so I don't usually favor Embedded Interpretation—it is useful when you have relatively small expressions that you just want to evaluate and run."
- "Sometimes, building a Semantic Model just isn't worth the overhead. But I find this is a rare case; even a relatively small DSL is usually simpler to deal with by creating a Semantic Model and interpreting that, rather than trying to do everything in the parser."
- The clinching argument: **"a Semantic Model provides a stronger foundation if the language grows."** The cost of Embedded Interpretation is not paid today; it is paid the first time the language needs a feature that requires looking at more than one fragment at a time.

The one genuinely good fit is the calculator: "It's easy to interpret each expression and compose the results together. It's also a case where the syntax tree for arithmetic is a perfectly good Semantic Model, so there's no gain in trying to create the usual Semantic Model that I prefer." The test, therefore, is: **use it when the syntax tree already *is* the domain model.**

#### The methodological warning

The most important paragraph in the chapter is not about the pattern at all *(Ch. 26, end of "A Calculator")*:

> "Arithmetic expressions are a common choice for illustrating how to use a parser; many articles and papers use some form of calculator example. But I don't think this is very representative of what you have to deal with when working with a DSL. The big problem with using arithmetic expressions as examples is that they force you to deal with a rare problem (Nested Operator Expression) but avoid the common DSL-related problems that encourage the use of Semantic Model and Embedment Helper."

**The canonical tutorial example teaches the rare problem and hides the common ones.** The calculator is so simple that it does not even need an Embedment Helper — which is precisely why it misleads people about what real DSL work involves. Carry that warning beyond DSLs.

#### Relationships

The third alternative to Tree Construction and Embedded Translation. Necessarily entangled with Nested Operator Expression (13.7) in the calculator case, and with the top-down/bottom-up parser distinction. It deliberately *skips* the Semantic Model, which is the whole argument against it.

> **SDK lens:** Eager evaluation with no intermediate representation is the **"just give me the answer" API**. It is the right shape for a one-shot evaluator — a template expression, a filter predicate, a unit conversion — and the wrong shape for anything you will later want to inspect, cache, optimize, serialize, explain, or partially evaluate. The design question to ask is Fowler's: **does your syntax tree already *serve as* your domain model?** If so, an extra model layer is ceremony; if not — and for most real domains it is not — you will want the model. Note that "a stronger foundation if the language grows" is the general argument for keeping a representation layer even when today's use case does not need it, but Fowler only makes it because the cost of that layer is small, not as a blanket "always add a layer."

---

### 13.4 Choosing an output strategy

| | Tree Construction | Embedded Translation | Embedded Interpretation |
|---|---|---|---|
| Produces | AST → then Semantic Model | Semantic Model directly | The answer directly |
| Passes over input | Many (walk the tree freely) | Exactly one | Exactly one |
| Forward references | Easy — later passes resolve | Hard — find-or-create plus context variables | Not applicable / hard |
| Grammar-file cleanliness | Enforced by the mechanism | Depends on your discipline | Depends on your discipline |
| Side-effect risk | None — actions return subtrees | Real — actions may fire unexpectedly | Real |
| Reuse of the parse | High — many walks, many models | None | None |
| Cost | Two stages to write | One stage | One stage |
| Best when | Complex transformation, multiple passes, good AST tooling | Simple language, simple parser, one pass suffices | Small expressions; the syntax tree *is* the model |

The four decision factors, in the order Fowler weights them:

1. **Complexity of the transformation.** The more complex it is, the more an intermediate model earns its keep — "two simple transformations rather than one complicated one" *(Ch. 24, "When to Use It")*.
2. **Number of passes and forward references.** This is decisive. Multiple passes are trivial with a tree and impossible without one. If your language permits forward references, Tree Construction is the honest answer and everything else is a workaround.
3. **Tooling.** "The better the tree-building features of your Parser Generator the more appealing Tree Construction becomes" *(Ch. 25, "When to Use It")*; some tools remove the choice entirely.
4. **Side-effect tangles.** Embedded actions can fire at moments the parsing algorithm chooses, not moments you chose. Getting tangled in that is itself the signal to switch *(Ch. 25, "How It Works")*.

Fowler's default position: **build a Semantic Model** — so Tree Construction or Embedded Translation, not Embedded Interpretation. Choose between the first two on complexity, pass count, and tool support. And switch from Embedded Translation to Tree Construction the moment side effects or forward references get tangled.

---

### 13.5 Foreign Code *(Ch. 27)*

**Intent:** "Embed some foreign code into an external DSL to provide more elaborate behavior than can be specified in the DSL." *(Ch. 27, intent)*

#### The concept

A DSL is, by definition, a limited language that only does a few things. Sooner or later a script needs to say something the DSL cannot express. There are two responses: extend the DSL, or open an escape hatch to another language. "One solution may be to extend the DSL to handle this capability, but taking this path may significantly complicate the DSL, removing much of the simplicity that makes it appealing." *(Ch. 27, opening)* Foreign Code is the escape hatch — a different language, usually a general-purpose one, embedded at designated places in the DSL. The sketch is a small DSL sentence with a general-purpose predicate embedded in braces.

#### How it works — two questions

**Question 1: how do we recognize the foreign pieces and weave them into the grammar?**

Foreign Code only appears in specific places, so the grammar marks the spots where it can occur. The wrinkle is that **your grammar cannot recognize the internal structure of the foreign code**, so you usually need Alternative Tokenization (13.6) to read the whole foreign fragment into the parser as one long string. Then you either (a) embed that raw string in the Semantic Model as-is, or (b) hand it to a separate parser for the foreign language so you can weave it more intimately into the model. Option (b) "is more involved—it's something you'd only consider if your Foreign Code is another DSL. Often, the Foreign Code is a general-purpose language, in which case the pure string is usually enough." *(Ch. 27, "How It Works")* In his own example Fowler explicitly declines to parse the embedded language: parsing would catch only *syntactic* errors, not the semantic ones that matter, so "I don't think it's worth the trouble."

**Question 2: how do we execute it?** "The biggest issue lies in whether the Foreign Code can be interpreted or needs to be compiled."

- **Interpreted foreign code is easiest**, provided the interpreter can interoperate with the host. If the host language is itself interpreted, you can just use the host language as the foreign language. If the host is compiled, you need an interpreted language callable from it with some data transfer. "It's usually a bit fiddly, especially when it comes to moving data around. It also might involve introducing another language to the project, which can sometimes be an issue."
- **Embedding the host (compiled) language** introduces an extra compilation step into the build, exactly like code generation. If you are already generating code you are paying that cost anyway, so compiled Foreign Code adds nothing. "The complexity matters if you're compiling code while interpreting the Semantic Model" — it is the *mixed* mode that hurts.

**The discipline rule.** Stated in full because it is the chapter's operative advice:

> "Whenever you use general-purpose Foreign Code, you should seriously consider using an Embedment Helper. That way, the only Foreign Code in your DSL script should be the minimum required for the context within the DSL, calling out to the Embedment Helper for any more general processing. One of the big problems with Foreign Code is that a lot of foreign code can overwhelm the DSL, thus losing most of the advantages of readability that the DSL offers. Embedment Helper is an easy technique and is worth it in all but the smallest cases." *(Ch. 27, "How It Works")*

**Symbol references.** Occasionally the foreign code must refer to symbols defined in the DSL script itself. That only arises when the DSL has variables or other indirect constructs — "these are omnipresent in general-purpose languages, they are actually not so common in DSLs as DSLs often don't need that kind of expressiveness." Rare, but familiar, because grammars do exactly this: a grammar's code actions reference labelled grammar elements, and the generator resolves those references at generation time.

#### What the worked example adds

Two points of craft and one of architecture *(Ch. 27, example and "Parser")*:

- **The choice of foreign language was driven by the deployment cycle**, not by language preference: an interpreted language was chosen because rules could then be **evaluated at runtime, avoiding recompilation** when someone changes them. Fowler is candid that the resulting predicate "isn't exactly super readable—I suspect I'd have to say 'trust me' to the sales manager."
- **The foreign fragment is stored as an opaque string in the Semantic Model** and evaluated at match time, with the candidate object injected into the script's scope so the snippet can reach its properties.
- **Self-reference:** "the code actions in a grammar are an excellent example of Foreign Code." The two execution strategies — weave-at-generation and eval-at-runtime — appear side by side in the same example.
- **Delimiter selection** matters (and is revisited in 13.6): the obvious brace pair breaks if the embedded code contains braces. Fixes are an unlikely delimiter *pair* of characters, or a push-down lexer that allows nested but balanced braces. Even the nested version is defeated by a brace inside a string literal in the embedded code — "it should do for most cases," a rare and useful admission that a pragmatic 95% solution is acceptable here.
- **Naming:** fully spelled-out labels are used for tokens "because the tokens aren't sufficiently clear," and abbreviations for subrule labels "because those subrule names are clear and a full label would be just duplicating the subrule name and thus add noise." **A name should add information; a name that restates the type is noise.**
- **Where to populate the model:** a child rule *returns a list of objects* rather than populating the model itself, so the parent rule does the populating. Otherwise the child's action would need access to the enclosing object — "This would usually require a Context Variable which I'd like to avoid. … but I prefer to do all the Semantic Model in the one place." **Prefer returning values upward; keep model construction in one place.**
- **Error handling:** a Notification object collects per-token errors and the driver throws only after the whole parse, so users see all errors rather than the first one.

#### When to use it

*(Ch. 27, "When to Use It")* — the framing is always **Foreign Code versus extending the DSL.**

Costs of Foreign Code:
- "By using it, you are breaking the abstraction that the DSL gives you."
- Readers now need to understand the foreign code as well as the DSL, "at least to an extent."
- It complicates the parsing process and probably the Semantic Model too.

Cost of the alternative: "The more powerful the DSL, the harder it is to understand and use."

Three cases that lean toward Foreign Code:
1. **You genuinely need a general-purpose language.** "You certainly don't want to turn your DSL into a general-purpose language, so that pushes you quickly to using Foreign Code."
2. **The capability is needed very rarely.** "A rarely used capability may not be worth extending the DSL for."
3. **Audience.** "If the DSL is only used by programmers, then adding Foreign Code is not a problem—they will be able to understand the Foreign Code as much as the DSL. If nonprogrammers will read the DSL, that argues against Foreign Code as they may not be able to understand, and thus engage with, the foreign code. If the Foreign Code is to handle rare cases, however, this may not be a big problem."

#### Relationships

Requires Alternative Tokenization (13.6) to capture the fragment as one token. Should almost always be paired with Embedment Helper (15.3). It is the mechanism underneath Embedded Translation and Embedded Interpretation when using a Parser Generator, and Ch. 31 recommends it as the current practical substitute for modular grammars.

> **SDK lens:** This chapter is really about **escape hatches in declarative APIs**, and the analysis transfers unchanged. Every declarative config format eventually faces "we need a general-purpose language here," and the choices are always the same three: extend the config language until it becomes a bad programming language, embed a real language, or provide a plugin interface in the host language. **The audience test is the sharpest tool** — if non-engineers read or write the artifacts, an escape hatch fractures the audience; if only engineers use it, it costs little. **The rarely-needed-capability test** is the other one: do not grow the core surface for a long-tail need, give it an extension point. **The runtime-eval versus compile-in decision maps directly to plugin architectures**: interpreted extensions can change without redeploying; compiled ones need a build step but keep one language in the project. Finally: **keep the escape hatch narrow via a helper API** so the user's snippet is one line calling into you rather than a program; **store the foreign fragment opaquely** rather than half-parsing a language you do not own; and **collect errors into a notification and report them all** instead of failing on the first.

---

### 13.6 Alternative Tokenization *(Ch. 28)*

**Intent:** "Alter the lexing behavior from within the parser." *(Ch. 28, intent)*

#### The concept

The textbook picture of a Parser Generator is a one-way pipe: the lexer produces tokens, the parser consumes them. "As it turns out that isn't always the case. There are times when the way the lexer does the tokenizing should change depending on where we are in the parse tree—meaning that the parser has to manipulate the way the lexer does the tokenizing." *(Ch. 28, "How It Works")*

The motivating example is small and very real. A catalog DSL with lines like `item camera;`. Programmers happily write `item small_power_plant;` or camelCase, "but regular human beings are more used to spaces" — they want `item small power plant;`. This works until an item is named "small white item": the lexer sees the word `item` inside the name and returns a *keyword* token. What you actually want is: **everything between the `item` keyword and the terminator should be treated as name text, whatever it looks like.** That requires different tokenization rules at that point in the parse. The other pervasive case is Foreign Code, which is full of tokens meaningful in the foreign language that you want to ignore entirely so you can grab the whole fragment as one string.

#### The four techniques

Not all are available in every tool, and each has a distinct failure mode.

**1. Quoting** *(Ch. 28, "Quoting")*. Put the special text inside quotation characters so the lexer recognizes it as one thing; the quoting rule "gobbles up all the text between the delimiters, so it is never touched by the other lexer rules." The key property and key limitation: **"Quoting doesn't involve the parser at all, so a quoting scheme has to be used everywhere in the language. You can't have specific rules for quoting particular elements of the language."** It is a global decision, not a contextual one — though "in many situations, however, this works out just fine."

Handling delimiters *inside* the quoted text, four tactics:
- **Escaping** — a backslash, or doubling the delimiter. The general lexer trick is delimiters surrounding a repeating group in which one alternative is the *negation* of the delimiter and the others are the escape combinations. Fowler prefers the long-winded, clearly-named form to the compact regex, noting "such clarity is particularly rare when it comes to regular expressions." Caveat: "Escaping works well, but it may be confusing, particularly to nonprogrammers."
- **Unusual delimiters** — a symbol pair unlikely to occur in the quoted text (one real tool uses `{:` and `:}` for code actions precisely because plain braces are ubiquitous in C-family languages). "Using an unlikely delimiter is obviously only as good as the unlikeliness of its use."
- **Multiple delimiter kinds** — allow single *or* double quotes so an embedded delimiter can be handled by switching to the other.
- **Balanced nesting via a push-down lexer** — allows nested braces provided they are matched. Still defeated by a brace inside a string literal in the embedded code. "The biggest downside to this technique is that you can only do it if the lexer is a push-down machine, which is relatively rare."

**2. Lexical State** *(Ch. 28, "Lexical State")*. "Perhaps the most logical way of thinking about this problem": replace the lexer while reading the special text. Once the `item` keyword is seen, switch to a different lexer mode until the terminator, then switch back. Lexer rules are annotated with the state(s) they apply in; unannotated rules apply everywhere. The parser drives the switch through actions.

**The catch — parser lookahead versus lexer state.** Parsers look ahead through the token stream to resolve rules, and **even one token of lookahead breaks this**: the first word of the name is lexed *before* the state change takes effect, so it arrives as a keyword and breaks the parse. A subtler hazard is ordering — the state must be reset *before* the statement separator is recognized, not after, or the next keyword is looked ahead in the wrong state. Fowler's conclusion: "If you use common border tokens (like quotes), you can avoid problems when you only have one token of look ahead. Otherwise, you have to be careful in how the parser look ahead interacts with the lexer's lexical states. As a result, combining parsing and lexical states can easily get pretty messy." Tools that pre-tokenize the entire input before parsing cannot do this at all.

**3. Token Type Mutation** *(Ch. 28, "Token Type Mutation")*. "The parser's rules react not to the full contents of the token, but to the token's type. If we can change the type of a token before it reaches the parser, we can change an `item` keyword into an `item` word." This is the **mirror image of lexical state**: lexical state needs the lexer to feed tokens one at a time, while token type mutation needs the ability to *look ahead in the token stream*. So it suits tools that pre-tokenize and not those with one-token lookahead. The grammar shows nothing unusual; a helper called from an action runs forward along the token stream resetting each token's type until it reaches the sentinel.

The downside is specific and important: **"This technique doesn't capture exactly what was in the original text, as anything that the lexer skips won't be offered up to the parser. For example, whitespace isn't preserved in this method. If that's an issue, then this technique isn't the right one to use."** A real-world instance Fowler cites is an ORM query parser where a word is a keyword in one construct and a column name elsewhere: the lexer returns the keyword by default and a parser action looks ahead for the following keyword, changing the token to an identifier if it is absent.

**4. Ignoring Token Types** *(Ch. 28, "Ignoring Token Types")*. "If the tokens don't make sense and you want the full text, you can ignore the token types completely and grab every token until you reach a sentinel token." The name rule accepts *any* token other than the terminator — trivial with a negation operator, and without one you must enumerate all keywords, "which is more awkward." The tokens still carry correct types; you simply do not use them here, reconstructing the text from token contents. With Tree Construction you do the analogous thing: collect the tokens into a single list node and ignore the types when walking.

#### When to use it

*(Ch. 28, "When to Use It")*

- Relevant when using Syntax-Directed Translation with tokenization separated from syntactic analysis — "which is the common case."
- "You need to consider it when you have a section of special text that shouldn't be tokenized using your usual scheme."
- The three common triggers: **keywords that shouldn't be keywords in a particular context**; **allowing any form of text**, typically for prose descriptions; and **Foreign Code**.

#### Relationships

Prerequisite for Foreign Code (13.5). Interacts badly with Newline Separators (13.8) — Fowler deliberately uses visible separators in this chapter's examples "to deal with one tricky issue at a time." Offered in 13.9 as the constrained workaround for modular grammars when a child grammar needs a different lexer. Its whole existence is a consequence of the lexer/parser boundary described in 12.2.

> **SDK lens:** This is the **context-sensitive input problem**, and it shows up in any format library: a field whose contents must not be interpreted by the enclosing parser — raw blocks in markup, template literals, embedded SQL or JSON, free-prose fields. The four techniques map onto four API design choices: require quoting/escaping (simple and global, but pushes burden onto users and hurts non-programmers); switch modes based on position (contextual and pleasant, but interacts badly with lookahead and streaming); post-process the token stream (loses skipped input — beware if you need round-trip fidelity); or take everything up to a sentinel (simplest and most robust when a clean terminator exists). Two design rules follow. **Round-trip fidelity is a first-class requirement**: token type mutation silently loses whitespace, so if your library must reproduce input — formatters, autofixing linters, config rewriters — choose the technique that keeps every character. And **design for the non-programmer's input habits**: the whole chapter is triggered by users wanting spaces instead of underscores. If your DSL, config, or CLI is authored by non-engineers, the cost of accommodating natural text is real parser complexity; decide deliberately rather than defaulting to identifier rules.

---

### 13.7 Nested Operator Expression *(Ch. 29)*

**Intent:** "An operator expression that can recursively contain the same form of expression (for example, arithmetic and Boolean expressions)." *(Ch. 29, intent)*

#### Framing: this one is not really a pattern

Fowler is upfront: "Calling Nested Operator Expression a pattern is a bit of a stretch, since it isn't so much a solution as it is a common problem in parsing." His "When to Use It" section is a joke at his own expense — it exists only "to flaunt a fixation with consistency which isn't usually something I'm known for."

*(One correction the notes flag: the chapter's opening sentence suggests left recursion is a problem "particularly with bottom-up parsers," but the body demonstrates the opposite. Bottom-up parsers handle left recursion fine; it is **top-down** parsers that must eliminate it. Read the body, not the intro.)*

#### The two difficulties

1. **Recursion** — the rule appears inside its own body.
2. **Precedence** — `1 + 2 * 3` must mean `1 + (2 * 3)`.

Plus **associativity**, which must be declared even where it seems not to matter.

#### Bottom-up parsers

"The easiest to describe." A single production rule with one alternative per operator plus a base case for a bare operand. The recursion is direct and reads clearly — the grammar looks like the structure of the language.

Precedence is not in the grammar rules; it is declared separately, as a list of precedence statements each naming the operators at one level and their associativity, ordered from low to high. Precedence can also be attached to an individual rule: the unary-minus rule uses a **ghost token** that never appears in the input and exists solely to give that rule a different precedence from binary minus — "context-dependent precedence."

Why precedence declarations are needed at all is **ambiguity**: "Without the precedence rules, a parser with this grammar could parse `1 + 2 * 3` as `(1 + 2) * 3` or as `1 + (2 * 3)`, which makes it ambiguous. The same is true for `1 + 2 + 3` even though we (humans) know it doesn't matter in this case. This is why we have to state the direction of associativity as well, even though it doesn't matter for `+` and `*`." *(Ch. 29, "Using Bottom-Up Parsers")* **The parser needs a total order even where the semantics is indifferent.**

Verdict: "The combination of a simple recursive grammar rule and precedence declarations makes it very easy to handle nested expressions in a bottom-up parser."

#### Top-down parsers

"More complicated." You cannot write the simple recursive rule, because it is left-recursive and a top-down parser cannot handle left recursion. The standard fix is a **cascade of rules, one per precedence level**, which simultaneously eliminates the left recursion and encodes precedence. "The resulting grammar, however, is much less clear. Indeed, this lack of clarity is why many people prefer a bottom-up parser." *(Ch. 29, "Top-Down Parsers")*

The three idioms to memorize:

- **Left-associative binary operator:** the rule body starts with a reference to the *next-lower* precedence rule, followed by a repeating group of (operator, next-lower rule). At every point you refer to the next-lower rule, never to yourself.
- **Right-associative binary operator:** the right-hand side is a **recursive reference to the rule itself**, and the group is **optional** rather than repeating. "The recursion allows multiple power expressions to be combined together, and the right recursion like this is inherently right-associative."
- **Unary prefix operator:** recurse into yourself when the sign is present (so repeated signs work), and fall through to the next-lower rule when it is not (avoiding left recursion).

**Atoms** sit at the bottom — literals and parenthesized expressions — and parenthesized expressions "introduce deep recursion as they reference the top-level expression again."

Three consequences of the mangling:

1. **You are not expressing intent any more.** "You're spending your time massaging the Parser Generator rather than expressing intent. The resulting mangled grammars are why many people prefer bottom-up Parser Generators to top-down ones. Advocates of top-down parsing argue that it's only nested expressions that get thus mangled, and that's a worthwhile tradeoff compared to the other problems with bottom-up parsers."
2. **The parse tree fills with clutter nodes.** `1 + 2` should produce an operator node with two operand children; instead each operand carries a chain of one node per precedence level. "This isn't a huge deal in practice; you need to write code to handle these nodes for the cases when they're useful, but sometimes they are just irritating."
3. **Adding output production makes it worse.** With any number of terms at one level you need an accumulator declared at the start of the rule and updated inside the repeating group. And because different operators at the same level must do different things, you have to **widen the alternative** — duplicating the right-hand-side reference in each branch instead of factoring the operator set out. "This introduces some duplication, but this is often the case once you actually do something with your grammar. Tree Construction often reduces this problem, but even so you might want to return a different type of node for plus and minus, which would require widening the alternative."

Closing practical advice: different top-down parsers have slightly different problems and solutions, and they usually document them under "left recursion."

#### Relationships

Forced on you by Embedded Interpretation's calculator example (13.3) — and 13.3 warns that the calculator is unrepresentative precisely *because* it drags in this rare problem. Tree Construction (13.1) mitigates the code-action duplication. The bottom-up/top-down distinction here is the strongest argument in the book about which Parser Generator to choose, and it is the same left-recursion constraint introduced in BNF (12.3) and inherited by Recursive Descent Parser (12.5) and Parser Combinator (12.6).

> **SDK lens:** **Precedence and associativity are ambiguity resolution, not semantics.** Any API accepting user-authored expressions — query filters, rule engines, formula fields, search syntax — must define a total precedence order and document it, even for operators where order is mathematically irrelevant, because *the parser* needs it. Two more: **your grammar's shape is constrained by your tool**, so if the expression grammar has to be mangled, expect a parse tree that does not match the mental model and downstream code full of pass-through node handling — budget for a normalization step that collapses the clutter, because users of the tree should not have to know about your precedence-cascade node types. And take the meta-lesson seriously: expression parsing is the most over-taught and least representative parsing problem there is. Do not design a general library around it.

---

### 13.8 Newline Separators *(Ch. 30)*

**Intent:** "Use newlines as statement separators." *(Ch. 30, intent)*

#### The concept and the core difficulty

Using newlines to end statements is common, and with Delimiter-Directed Translation it is completely natural — the newline is *already* the delimiter used to break up the input, so there is nothing extra to say. With Syntax-Directed Translation it is "rather more tricky, introducing a number of subtle traps."

The root cause is worth internalizing:

> "The reason that newline separators and Syntax-Directed Translation don't go together too well is that newlines play two roles when you use them as separators. Apart from their syntactic role, they also play a formatting role in providing vertical space. As a result, they can appear in spaces where you wouldn't expect a statement separator to pop up." *(Ch. 30, "How It Works")*

#### The four cases that break the naive grammar

Given the obvious grammar — a statement is `keyword identifier EOL`, and the document is a list of statements — all four of these fail:

1. Blank lines *between* statements
2. Blank lines *before* the first statement
3. Blank lines *after* the last statement
4. The last statement having **no end-of-line at all**

The first three are all blank lines but "may need different ways of handling them in the grammar, so should all be tested." And the headline advice:

> "Making sure you have tests for these cases is probably the most important thing to do. I've got some solutions for these problems below, but the good tests are the key to ensuring that the situations are covered properly." *(Ch. 30, "How It Works")*

#### Three grammar shapes for handling it

1. **An end-of-statement rule matching multiple newlines.** Logically this belongs in the lexer (it is a regular expression), but the missing-final-newline case forces you to match end-of-file, which may be impossible in the lexer depending on the tool. Where EOF is exposed to the parser instead, the end-of-statement rule has to live in the parser grammar — a "vertical space" rule of zero-or-more line endings, plus an "end of statement" rule of one-or-more line endings *or* EOF. Fowler adds a general escape: "One option to consider is forcing an end-of-line at the end—either through the lexer (if you can) or perhaps by prelexing. Forcing a final end-of-line can help avoid a few awkward corner cases." **Normalizing the input before parsing is a legitimate and often cheapest fix.**
2. **Treat them as separators rather than terminators** — `statement (separator statement)*`, bracketed by optional vertical space. "I've come to prefer this style. Instead of defining an extra `verticalSpace` rule, I can use `separator?`." This is Fowler's stated preference.
3. **Statement body as an optional element of each line** — a line is either just a line ending, or a statement followed by a line ending, or a statement followed by EOF. Requires explicit EOF matching; an EOF-free variant exists that "doesn't read as clearly to me, but also doesn't need the end-of-file matching."

#### Comments — the other trap

End-of-line comments are very useful and interact badly with newline separators. When newlines are ignored you can happily write a comment rule that consumes the newline. **With newline separators, consuming the newline destroys the statement terminator** — and comments very often sit at the end of a statement. The fix is easy once seen: write the comment rule to match everything up to *but not including* the newline. Line continuation is handled with a lexer rule matching a continuation character followed by optional whitespace and the line ending, skipped entirely.

#### When to use it

*(Ch. 30, "When to Use It")* — Fowler decomposes it into **two separate decisions.**

**Decision 1: should you have statement separators at all?**
- "The limited structure of a DSL often means that you can live without statement separators. The parser can usually figure out the context of the parse from the various keywords you use." His own running example has none and parses fine.
- The argument *for* them is **error localization**: "In order for the parser to localize errors it needs some kind of checkpointing marker to tell where it's supposed to be in the parse. Without checkpointing, an error in one line of the script may not be apparent to the parser until several lines later, leading to confusing error messages. Statement separators can often fulfill this role. (Although they are not the only mechanism that can do this; keywords often do this too.)"

**Decision 2: if yes, newline or a visible character?**
- "The nice thing about using newlines is that most of the time, you have one statement per line anyway, so using a newline separator doesn't add any syntactic noise to the DSL. This is particularly valuable when working with nonprogrammers, although many programmers (including myself) prefer newline separators as well."
- "The downside with newline separators is that Syntax-Directed Translation is made more finicky and you have to use the techniques I've described here. You also need to ensure you have tests to cover the common problem cases."
- Verdict: "On the whole, however, I still prefer to use newlines rather than a visible statement separator."

#### Relationships

Trivial with Delimiter-Directed Translation (12.1); fiddly with Syntax-Directed Translation (12.2). Alternative Tokenization (13.6) deliberately avoids newline separators to isolate one difficulty at a time. Syntactic indentation (13.9) is the next step down this road and is much harder.

> **SDK lens:** **Syntax that is invisible to the eye is expensive to implement.** Whitespace-significant formats are pleasant for authors and painful for the people maintaining the parser; the pleasure is real, so price the implementation cost honestly rather than pretending it away. Fowler's four failure cases are a **ready-made test checklist for any line-oriented format**: leading blank lines, trailing blank lines, interior blank lines, and a missing final newline — plus a comment at the end of the last line with no trailing newline. These are exactly the bugs that ship in hand-rolled config parsers. Two further transfers: **normalize input at the boundary** (appending a final newline before parsing eliminates a whole class of corner cases — canonicalize early so the core logic only ever sees well-formed input), and **checkpointing improves error messages** — any recovery-capable parser or validator needs synchronization points, so either design them into the format or accept vague diagnostics. Finally, note the general smell: **an element carrying two responsibilities invites ambiguity**, and newlines carrying both structure and visual formatting is the archetype.

---

### 13.9 External DSL Miscellany *(Ch. 31)*

Chapter 31 is explicitly a hodgepodge of unfinished topics, and Fowler frames it as a scope-cutting decision: "As with writing software, there is a point at which you have to cut scope in order to ship your software, and the same is true of book writing." He flags that "the thoughts here are more preliminary than much of the other material in this book. By definition, these are all topics that I haven't done enough work on to merit a proper treatment." *(Ch. 31, opening)* — a model of intellectual honesty worth imitating: label the parts you are less sure of.

#### Syntactic indentation

**The idea.** Most languages express hierarchy with nested blocks marked by delimiters. But that is not how humans actually read them:

> "However, when you read the structure, you pay more attention to the formatting. The primary form of structure that we read comes from the indentation, not from the delimiters." *(Ch. 31, "Syntactic Indentation")*

Fowler demonstrates with a nested list formatted so the indentation *contradicts* the braces — the reader is misled, because the eye trusts the indentation. Since we read structure through indentation anyway, the argument goes, let the indentation *be* the structure.

**The usability advantage:** "The definition and the eye are always in sync—you can't mislead yourself by altering the formatting without changing the real structure." He immediately qualifies it: editors with automatic formatting remove much of that advantage for mainstream languages — "but DSLs are less likely to have that kind of support." **The value of syntactic indentation is highest exactly where tooling is weakest, which is where DSLs live.**

**Tabs.** "If you use syntactic indentation, be very careful about the interplay between tabs and spaces. Since tab widths vary depending on how you set the editor, mixing tabs and spaces in a file can cause no end of confusion. My recommendation is to follow the approach of YAML and forbid tabs from any language that uses syntactic indentation. Any inconvenience you'll suffer from not allowing tabs will be much less than the confusion you avoid." That is a clean example of **eliminating a class of user error by removing the ambiguous input rather than by handling it.**

**Why it is hard to parse — and where the cost lands.** "Syntactic indentation is very convenient to use, but presents some real difficulties in parsing. I spent some time looking at Python and YAML parsers and saw plenty of complexity due to the syntactic indentation."

- **The cost lands in the lexer**, because the lexer is the part of a Syntax-Directed Translation system that deals with characters.
- **Delimiter-Directed Translation is a poor companion**, "since syntactic indentation is all about counting the kind of block structure that Delimiter-Directed Translation has problems with." Both are line-oriented, but indentation demands exactly the nesting that delimiter-directed processing handles badly.
- **The effective tactic: imaginary indent/dedent tokens.** Get the lexer to emit special "indent" and "dedent" tokens when it detects an indentation change. "Using these imaginary tokens allows you to write the parser using normal techniques for handling blocks—you just use 'indent' and 'dedent' instead of `{` and `}`." The parser then never knows about indentation at all — a clean separation.
- **But the lexer fights you.** "Doing this in a conventional lexer, however, is somewhere between hard and impossible. Detecting indentation changes isn't something lexers are designed to do, nor are they usually designed to emit imaginary tokens that don't correspond to particular characters in the input text. As a result, you'll probably end up having to write a custom lexer."
- **The alternative Fowler would try first is a preprocessor.** "Another plausible approach—one that I'd certainly be inclined to try—is to preprocess the input text before it hits the lexer. This preprocessing would only focus on the task of recognizing indentation changes and would insert special textual markers into the text when it finds them. These markers can then be recognized by the lexer in the usual way." Two costs: you must pick markers that cannot clash with anything in the language, and you must cope with the effect on **diagnostics that report line and column numbers**, since you have altered the text the user wrote. "But this approach will greatly simplify the lexing of syntactic indentation."

The tradeoff in summary: syntactic indentation is a genuine usability win — structure and appearance can never diverge — bought at a real and non-trivial implementation cost, most of which lands in the lexer, and which usually means writing or heavily customizing a lexer rather than using one off the shelf.

#### Modular grammars

**The motivating principle** is one of the most quotable statements of the book's whole philosophy:

> "DSLs are the better the more limited they are. Limited expressiveness keeps them easy to understand, use, and process. One of the biggest dangers with a DSL is the desire to add expressiveness—leading to the trap of the language inadvertently becoming general-purpose." *(Ch. 31, "Modular Grammars")*

**The proposed escape from the trap** is to stop growing one language and instead **combine several independent DSLs**, which requires parsing the pieces independently — separate grammars per DSL, woven into a single overall parser. The goal is stated in library terms: "You want to be able to reference a different grammar from your grammar, so that if that referenced grammar changes you don't need to change your own. Modular grammars would allow you to use reusable grammars in the same way that we currently use reusable libraries."

**State of the art** (as of writing): "Modular grammars, however useful for DSL work, are not a well-understood area in the language world. There are some people exploring this topic, but nothing that's really mature as I write this."

**The specific technical obstacle is the separate lexer.** "Most Parser Generators use a separate lexer, which further complicates using modular grammars since a different grammar will usually need a different lexer than the parent grammar." The lexer is global and stateless with respect to grammar composition, so two grammars with different lexical conventions cannot simply be glued together. Alternative Tokenization (13.6) is a workaround, "but that places constraints on how the child grammar can fit in with the parent." The promising direction is **scannerless parsers** — "those which don't separate lexical and syntactic analysis—may be more applicable to modular grammars," because if there is no separate lexer, there is no lexer to conflict. Fowler reports "a growing feeling" in that direction rather than a settled conclusion.

**The practical advice for today:**

> "For the moment, the simplest way of dealing with separate languages is to treat them as Foreign Code, pulling the text of the child language into a buffer and then parsing that buffer separately." *(Ch. 31, "Modular Grammars")*

That is: **don't compose grammars — compose parsers.** Capture the sub-language as an opaque string, then run a second, independent parse over it. Simple, robust, and genuinely decoupling; the cost is that the outer grammar cannot validate or interleave with the inner one, and error positions must be mapped back manually.

#### Relationships

Syntactic indentation extends the difficulties of Newline Separators (13.8) and depends on the lexer boundary from Syntax-Directed Translation (12.2); it also explains why Delimiter-Directed Translation (12.1) is a poor host for it. Modular grammars depend on Foreign Code (13.5) and Alternative Tokenization (13.6), and are the composition-level answer to the same pressure Foreign Code answers at the expression level — as well as the structural counterweight to the "DSL creeps toward general-purpose" failure mode.

> **SDK lens:** Two distinct lessons. From syntactic indentation: **translate an implicit property into explicit tokens at the earliest boundary** — convert indentation into indent/dedent markers at the edge so every downstream layer works with ordinary nesting, which generalizes to any API handling implicit structure. And note that **a preprocessing stage is a legitimate architecture but breaks source-position mapping**: if you insert or rewrite text before parsing, you need a source map to keep error messages honest, the same problem transpilers and template engines face. Also: **forbid the ambiguous input** — banning tabs trades a small inconvenience for the removal of an entire class of confusing bugs, and most API surfaces have an equivalent move available (reject ambiguous date formats rather than guessing). From modular grammars: **"limited expressiveness is a feature" is the core API design lesson of the whole book**, stated here most compactly — prefer several small, focused APIs over one that grows to cover everything, and when a surface needs to cover a new area, ask whether it should be a *separate composable module* rather than new syntax in the existing one. Watch also for the structural trap: **anything global and cross-cutting blocks composition.** The lexer/parser split is the example here, but a global registry, a single shared config schema, or a singleton serializer will block plugin composition in exactly the same way — scannerless parsing is the "remove the global layer" answer. Finally, **opaque embedding is the pragmatic composition mechanism**: take the sub-language as a blob and delegate to its own parser. That is how most real systems compose formats, and it works because the interface is a string plus a well-defined boundary.

---

## 14. Alternative computational models

Every programming language is designed with a particular *computational model* in mind. Mainstream languages assume an imperative model with code organized in an object-oriented way, which has proven "a suitable compromise between power and understandability." But that model is not always the best fit for a particular problem, and — this is the key observation that opens the whole of Part V — **"often the desire to use a DSL comes with a desire to use a different computational model."** *(Ch. 47, opening)*

This section has one umbrella pattern, Adaptive Model, plus four concrete computational models that are typically implemented *as* Adaptive Models: Decision Table, Dependency Network, Production Rule System, and State Machine. Fowler is explicit that the list is not exhaustive and that entirely new computational models, while less common, are not unknown.

The recurring bill attached to all of them: they demo beautifully and scale badly without tooling. Every pattern here needs tracing.

---

### 14.1 Adaptive Model *(Ch. 47)*

**Intent:** Arrange blocks of code in a data structure to implement an alternative computational model. *(Ch. 47, intent)*

#### The concept

Most software builds *models* of the world it works with — a catalog system models products and prices, a media site models stories and tags. Those models may be pure data structures or may combine data with the code that manipulates it. But in the ordinary case, **the flow of processing is dictated by the code**. Different data changes the details; the broad flow stays the same.

An Adaptive Model inverts this. The model itself takes the primary behavioral role. Load a different state model into a controller and you get wholly different overall behavior: "Essentially, the instantiation of the state model *is* the program." There is still a general Semantic Model of "a state machine" acting as a constant factor and a constraint on what any particular configuration can do — but the program that actually executes is the *configuration*.

Fowler's own definition of the boundary: **"the essence of using an Adaptive Model is the sense that you are changing the program by altering the instances and their relationships."** *(Ch. 47, "How It Works")* This dissolves the boundary between code and data, which opens up new possibilities and new problems. He notes the Lisp community relishes this duality, but "for many developers it's a world that's both entrancing and scary."

#### How it works

- You define a model whose **links between elements represent the behavioral relationships of the computational model** — states to transitions to target states, rules to conditions and actions, tasks to prerequisites.
- The model usually needs references to sections of imperative code: guards, actions, conditions.
- You run the model either by **executing code over it** (procedural style — an interpreter walks the structure) or by **executing code within the model itself** (object-oriented style — the model's own objects carry the run behavior).
- Adaptive Models often take well-known graph shapes, so textbooks on algorithms and data structures are genuinely useful reference material.

**Adaptive Model and DSL are independent.** You can have an Adaptive Model with no DSL in sight and get most of the benefits. **The DSL's role is to make it easier to program the Adaptive Model**, by providing a language in which you can describe your intentions more clearly. Fowler adds a pointed observation: "One of the hardest parts in using an Adaptive Model is to figure out what it's supposed to do — a DSL can be a big help in overcoming that." *(Ch. 47, "How It Works")*

**Forms it can take:** in-memory object models (all of the book's examples); a data structure interpreted by procedural code; or **stored in a database and interpreted by other applications**, common in workflow systems. When the model lives in a relational database Fowler usually finds it accompanied by a crude projectional editor — forms and fields. Serviceable, but a DSL has real advantages: DSLs are better at giving the whole picture of a behavior, and — his strongest argument for a *textual* DSL — a text DSL lets you easily put the Adaptive Model under version control. "I find it deeply troubling when core system behavior isn't kept under a proper source code control system." *(Ch. 47, "How It Works")*

#### Incorporating imperative code

The book's introductory state machine was deliberately built so that all behavioral elements could be described through simple data. More often you need real imperative code — richer actions, guard conditions. Doing that *inside* the Adaptive Model would mean reinventing a range of imperative expressions the host language already has, so the better move is to **embed regular host-language code into the model's data structure.** Options, in Fowler's order of preference *(Ch. 47, "How It Works")*:

1. **Closures.** The most direct statement of intent; they let you embed arbitrary blocks of code into data structures easily. The drawback he cites is that many languages lacked them at the time of writing — a constraint that has largely evaporated since, which strengthens the recommendation.
2. **Command objects.** Small objects each wrapping a single method — one class for the condition, one for the action. You cut down the number of subclasses by **parametrizing the commands** (a generic `JourneyStartCondition("BOS")` rather than a bespoke `BostonStart` class). In a language without closures, this is where he would go.
3. **Method name plus reflection.** He dislikes this: "it circumvents the mechanisms of the underlying environment just a bit too much."

A nuance worth keeping: commands look like a *workaround* from the Adaptive Model's viewpoint, but **if you are populating the model with a DSL, commands become more attractive**, because the DSL will usually wrap common cases in parameters anyway, which leads naturally to parametrized commands. Using the full expressiveness of closures in the DSL means closures in an internal DSL, or Foreign Code in an external one — "the latter, in particular, is something you should use only rarely."

#### Tools you must build alongside it

A DSL is valuable but "not really enough to work with an Adaptive Model when it gets more complicated." Two supporting tools matter *(Ch. 47, "Tools")*:

- **Tracing.** Because the computational model is unfamiliar, it is hard to follow what the model is doing. Capture how the model processed its inputs, leaving a clear log of why it did what it did. This "greatly helps answering the question, 'Why did the program do that?'"
- **Alternative visualizations.** Have the model produce a descriptive output of an instance — graphical descriptions are often very useful (automatic node-and-arc layout for a state diagram, plus reports showing the model from different perspectives). These are "a simple equivalent of the multiple projections of a language workbench," except not editable, since the cost of making them editable is usually prohibitive. **Build them automatically as part of your build process** and use them to check your understanding of how the model is configured.

#### When to use it

*(Ch. 47, "When to Use It")*

- Adaptive Model is **the key to using an alternative computational model.** Once you have one for, say, a Production Rule System, you can execute any set of rules by loading them in. Fowler's general advice is that any of the alternative computational models in this section should be implemented with an Adaptive Model.
- He acknowledges this is "somewhat of a glib answer," because it begs the question of when you would want an alternative computational model at all. That is a **qualitative decision** with no rigorous approach. His best suggestion: try expressing the behavior in a different computational model and see if it makes the problem easier to think about. Doing that often means **prototyping a DSL to drive the model**, since the Adaptive Model alone may not provide enough clarity.
- Start from the common models; if one seems to fit, it is worth a try. **The realization can also grow out of the way a framework changes over time** — a framework begins by just storing data, and as more behavior worms its way in, an Adaptive Model begins to form.

**The large disadvantage — and it is large.** Adaptive Models "can be very hard to understand." Programmers complain bitterly about being unable to follow how one works: "It's as if a bit of magic is embedded in the program, and a lot of people find this kind of magic rather scary." The root cause is **implicit behavior** — you can no longer reason about what the program does by reading the code; you have to look at a particular model *configuration*. Debugging can be a nightmare. You can build tools to help, but then you are spending time building tools rather than working on the true purpose of the software.

**The sociological failure mode** is the part that gets skipped in most retellings, and it is the most important paragraph in the chapter:

> "Usually, there are a couple of people around who understand the Adaptive Model. They are big fans of it, and can be incredibly productive by using it. Everyone else, however, steers well clear." *(Ch. 47, "When to Use It")*

Fowler is candid that he is one of those people who finds Adaptive Models powerful and productive — and equally candid that they can be an alien artifact to most developers. **Sometimes you have to forgo the gains**, because "it's not good to have a magic section in a system that people are fearful of touching. If the few people who understand the Adaptive Model would move on, nobody will be able to maintain that part of the system." His hope is that DSLs alleviate this by making implicit behavior explicit — capturing the configuration in "a language nature" — and that as DSLs become more common, more people will grow comfortable with Adaptive Models. Note the structure of that hope: **the mitigation for the sociological risk is exactly the tracing and visualization tooling above, plus a readable DSL.** If you build the model without the tooling, you have built the scary magic.

#### Relationships

Umbrella for Decision Table (14.2), Dependency Network (14.3), Production Rule System (14.4), and State Machine (14.5). Uses Command objects and closures for embedded behavior, and Foreign Code (13.5) for embedded behavior in external DSLs. Parser Combinator (12.6) is structurally an Adaptive Model whose configuration is a grammar. Its generated-code counterpart is Model-Aware Generation (15.4), which replicates a simulacrum of the model in a target environment.

> **SDK lens:** This is the pattern behind **configuration-driven frameworks, plugin registries, middleware pipelines, and workflow engines** — anything where the library's behavior is determined by a structure the user assembles rather than by control flow the user writes. Its two tooling recommendations translate directly into **library observability requirements**: a config-driven library must ship a tracing or explain facility ("why did this rule fire? why was this request routed here?") and ideally a dump/visualize facility for the assembled configuration. Build a config-driven API without these and you have built the scary magic. The version-control argument is an API-design argument for **text-based configuration over database-stored or GUI-edited configuration** for anything that constitutes core system behavior. And take the sociological warning as the honest cost-benefit for "magic" APIs generally — heavy annotation frameworks, DI containers, metaprogramming-driven ORMs. They are enormously productive for the people who understand them and opaque to everyone else; weigh maintainer bus-factor, not just expressiveness.

---

### 14.2 Decision Table *(Ch. 48)*

**Intent:** Represent a combination of conditional statements in a tabular form. *(Ch. 48, intent)*

#### The concept

When code composes several conditional statements it becomes hard to follow which combinations of conditions lead to which outcomes. A Decision Table improves understandability by laying the group of conditions out as a table: **each column is one combination of conditions and the outcome for that combination.**

Fowler's sketch has condition rows (*premium customer*, *priority order*, *international order*), consequence rows (*fee*, *alert rep*), and six columns of yes/no/don't-care values. Reading a single column gives you a whole rule: a domestic, regular order from a premium customer costs a particular fee and does not alert a representative.

#### How it works

- The table divides into two sections: **conditions** and **consequences**.
- Each **condition row** states the required value of that condition. With *n* two-valued Booleans you need 2ⁿ columns to cover everything.
- Each **consequence row** represents the values of a single output. A Decision Table needs only one consequence but can happily accept several.
- **Three-valued Boolean logic** is common, where the third value is "don't care" — the column is valid for any value of that condition. Don't-care values remove a lot of repetition and keep the table compact.
- **Completeness checking is a valuable property.** Because the columns are enumerable, you can determine whether all permutations of conditions have been captured and report the missing ones to the user. Some combinations genuinely cannot happen; capture those as an *error column*, or define the table's semantics so that missing columns are treated as errors.
- **Beyond Booleans:** if you want arbitrary enumerations, numeric ranges, or string matches, you can capture each such case as a Boolean — but the table then has to know about mutual exclusion, since conditions like `100 > x > 50` and `50 >= x` cannot both be true. The alternative is a **single condition row for the value of `x` with ranges typed into the cells**, which "is usually easier to work with." With more complex condition values, computing all permutations gets awkward, and it may be better to just treat an unmatched case as an error.

**Building it.** As usual Fowler advises a separate Semantic Model and parser, and for both you must decide **how generic to make them** *(Ch. 48, "How It Works")*. A model and parser for a *single* case fixes the condition rows in code along with the number and types of consequences — though you would usually still want the column values configurable. A *generic* Decision Table lets you configure the condition and consequence types; each condition then needs some way of indicating the code to run to evaluate it (a method name or a closure), and in a strongly typed language you also need the input and consequence types configured at compile time. The parser can likewise be fixed for one table even while the model is generic; to be more flexible you need "something akin to a simple grammar for the table structure so the parser can properly interpret the input data."

Two design points from the worked example worth keeping. The **three-valued Boolean is implemented polymorphically**, with a *matches* method rather than an *equals* method, **because the relation is not symmetric** — don't-care matches true, but true does not match don't-care. And **the parser operates against a tiny table abstraction** (cell, row count, column count) rather than being coupled to any particular spreadsheet mechanism; it also **verifies the condition row names** against what it expects, so a table whose rows get reordered or renamed fails loudly instead of silently mis-parsing.

One general lesson Fowler attaches to the completeness-checking code, which is worth lifting out of context: *"I'm quite happy to use the data structure that makes it easiest to write some code and then transform the result into the data structure I actually want to consume."* He compares it to changing coordinate systems in engineering — transform the problem into a system where it is easy to solve, solve it, transform back.

#### The spreadsheet angle

Decision Tables "are very simple to follow, and indeed edit, and so are particularly suited to capturing information from domain experts." Many domain experts already live in spreadsheets, so **a good tactic is to let them edit the tables in a spreadsheet and import it into the system** *(Ch. 48, "How It Works")*. The options run from crude to sophisticated: save as CSV (crude but often effective, and it works because the table is pure values with no formulae); interoperate with a running spreadsheet program; or use the spreadsheet's own programming language to receive, edit, and transmit the data to a remote program.

#### When to use it

*(Ch. 48, "When to Use It")*

- Very effective for capturing the results of a **set of interacting conditions**. It communicates well to both programmers and domain experts, and the tabular form lets domain experts manipulate it with familiar tools.
- **Biggest disadvantage:** it takes some effort to set things up so tables can be edited and displayed easily. But "this effort is usually quite small compared to the communicative benefit they provide."
- **Complexity ceiling:** "Decision Tables can only handle a certain degree of complexity — no more than what you can capture in a single (if complex) conditional expression. If you need to combine multiple kinds of conditionals, consider a *Production Rule System*."

#### Relationships

An instance of Adaptive Model (14.1). Escalates to Production Rule System (14.4) when a single conditional expression is no longer enough. Its parser is written "in the spirit of Delimiter-Directed Translation (12.1) but using rows and columns instead of a stream of delimiter-separated tokens." Its conditions are the canonical place to embed closures per 14.1's guidance.

> **SDK lens:** This is the natural shape for **pricing matrices, permission and authorization matrices, feature-flag combinations, and rate or discount schedules** exposed through a library. If your API takes five booleans and returns a policy, a decision table is very likely a better public surface than five nested conditionals or an options object. **Completeness checking is a genuine API feature**, not a nicety: a table-based API can tell the caller "you have not specified what happens when A and B are both true" at configuration time rather than failing in production — a validation guarantee an imperative conditional simply cannot offer. The **spreadsheet round-trip** is a real integration design, and it works precisely because the table contains only values; if non-engineers own the values, offer the ingestion path. And note that the generic-versus-specific decision — fixed conditions in code versus fully configurable conditions and types — is the classic tension between a narrow, statically typed, easy-to-use API and a general, dynamically configured, harder-to-use one. Fowler declines to declare a winner; he insists you make the choice consciously.

---

### 14.3 Dependency Network *(Ch. 49)*

**Intent:** A list of tasks linked by dependency relationships. To run a task, you invoke its dependencies, running those tasks as prerequisites. *(Ch. 49, intent)*

#### The concept

The canonical example is a build: to run tests you need an up-to-date compilation; to compile you need code generation done first. A Dependency Network organizes functionality into a **directed acyclic graph of tasks and their dependencies**. When you request a task, the system first finds the tasks it depends on and ensures those execute first if needed. Navigating the network guarantees all prerequisites are executed, and — critically — that **even if a task is reached more than once via different dependency paths, it executes only once.**

#### Task-oriented versus product-oriented — the central design axis

- **Task-oriented:** the network is a set of *tasks* with dependencies between tasks. "We have a code generation task and a compilation task, with the compilation task depending on the code generation task."
- **Product-oriented:** focus on the *products* you want to create and the dependencies between them. "We have an executable which is created by a compilation process, and some generated source files that are created by code generation. We then state the dependencies by saying that the code-generated source files are a prerequisite to building the executable."

Fowler admits the difference "may seem oversubtle at the moment," and then makes it consequential.

#### How it runs

You request a task or a product; either way the requested thing is the **target**. The system finds all its prerequisites, then their prerequisites, transitively, until it has the full list, then invokes each using the dependency relationships to ensure nothing runs before its prerequisites. No task executes more than once even if the traversal reaches it several times. His non-build illustration is a potion-manufacturing chain in which one intermediate substance sits on two paths into the final product and must be produced only once.

**The two failure modes** *(Ch. 49, "How It Works")*:

- **Missed prerequisite** — the most serious error. You end up with an erroneous answer, and it is nasty because it is hard to spot: "everything looks like it works correctly but the data is all wrong because we didn't get a prerequisite."
- **Unnecessary build** — recomputing something already current. In most cases this just means slower execution, "as the tasks are often idempotent. It can cause more serious errors if they aren't."

**Last-modified dates, and invoke versus execute.** A common feature, particularly in the product-oriented case, is that each product tracks when it was last updated. When you request a product, the system only actually executes the process if the output's last-modified date is earlier than any prerequisite's — which means the prerequisites must be invoked first so they can rebuild if necessary. Fowler draws a distinction that is easy to miss and worth memorizing:

> **Every transitive prerequisite is *invoked*, but a prerequisite is only *executed* if it's necessary.**

In a **task-oriented** network, last-modified dates are often not used at all; instead each task tracks whether it has already executed during the current target request and executes only on first invocation.

**The argument for product-orientation:** it is easier to work with persistent last-modified dates in the product-oriented style, and that "is a strong reason to prefer the product-oriented style to the task-oriented." You *can* use last-modified information in a task-oriented system, but then each task has to handle that responsibility itself. Product-orientation lets the *network* decide on execution.

**The price, stated plainly:** "This capability doesn't come for free; it only works if the output will always be the same if none of the prerequisites change. **Thus everything that could make a change to the output needs to be declared in prerequisites.**" *(Ch. 49, "How It Works")*

**In real build tools** the distinction surfaces directly: Make is product-oriented (its products are files); Ant is task-oriented. One real problem with product-oriented systems is that **there is not always a natural product** — running tests is the classic case, where you have to invent something like a test report to keep track of things. Sometimes outputs exist only to fit into the dependency system; the canonical pseudo-output is a **touch file**, an empty file that exists solely for its last-modified date.

The worked example adds one more practical detail: the behavior lives in the getter. Asking for a derived value first passes the invocation back along the inputs so every transitive input is invoked; then each node checks whether it is out of date and recalculates only if necessary. Out of date means: no result at all, *or* the result predates the node's own definition, *or* any input was updated after the result. "If a substance appears more than once in the input chain, it will be invoked many times, but it only calculates its profile once. This is essential, since the profiling service call is expensive."

#### When to use it

*(Ch. 49, "When to Use It")*

- Works for problems where you can **divide the computation into tasks with well-defined inputs and outputs**.
- The ability to execute only what is needed makes it suitable for **resource-intensive tasks, or tasks that take an effort to get going — such as remote operations.**
- As with any alternative model, it is **tricky to debug**, so it is important to **log invocations and executions** so you can see what is going on.
- That debugging concern, combined with the desire to execute only when needed, produces a concrete recommendation: **prefer relatively coarse-grained tasks for the network.**

#### Relationships

An instance of Adaptive Model (14.1), and therefore subject to its tracing requirement — here specialized into "log invocations and executions." In the book it is populated by an internal DSL, but nothing about the model requires that.

> **SDK lens:** This is the model behind **build tools, task runners, and incremental pipeline libraries**. If you are designing one, the task-versus-product decision determines whether your library or your users own staleness logic — and Fowler's verdict is that product-orientation lets the framework own it. **"Everything that could make a change to the output needs to be declared in prerequisites" is the fundamental correctness contract of any incremental or caching API.** It is why modern build systems demand full input declarations down to tool versions and environment variables, and why hidden inputs produce the missed-prerequisite silent-wrong-answer failure — the worst kind, because nothing looks broken. Three corollaries: the **touch-file / pseudo-output trick** is the standard workaround when your API is product-keyed but a task has no natural artifact (test runs, deploys, lint checks); **idempotence is what makes the unnecessary-build error benign**, so if you expose a task API, document idempotence expectations, because non-idempotent tasks turn a performance annoyance into a correctness bug; and **coarse-grained tasks** is good default guidance for public task APIs, since fine granularity multiplies both bookkeeping overhead and debugging surface.

---

### 14.4 Production Rule System *(Ch. 50)*

**Intent:** Organize logic through a set of production rules, each having a condition and an action. *(Ch. 50, intent)*

#### The concept

Many situations are naturally thought of as a set of conditional tests *(Ch. 50, opening)*:

- **Validation** — each validation is a condition where you raise an error if it is false.
- **Qualification or eligibility** — a chain of conditions where you qualify if you make it all the way up the chain.
- **Diagnosis** — a series of questions, each leading to new questions and hopefully to the root fault.

The sketch is a set of `if <conditions> then <consequence>` rules about a membership candidate, deliberately written so that the consequence of one rule is the condition of another — which is inference chaining.

A Production Rule System implements a set of rules, each with a condition and a consequential action. The system runs the rules on the data it has **through a series of cycles**; each cycle identifies the rules whose conditions match, then executes those rules' actions. "A Production Rule System is usually at the heart of an expert system."

#### How it works

The rule structure is simple: a Boolean condition and an action. The action can be anything, **but may be constrained by context** — if the system is only doing validation, actions may only raise errors, so an action just specifies which error and what data to attach.

The complex part is **deciding how to execute the rules.** Doing this for general expert systems is very involved, which is why a whole community and a market of tools exist. But — a recurring Fowler theme — "the fact that a general Production Rule System is very complicated doesn't mean that you can't build a simple Production Rule System for limited cases." *(Ch. 50, "How It Works")*

**The rule engine.** A Production Rule System puts all control of rule execution into a single component — a rule engine, inference engine, or scheduler. A simple engine runs a series of **inference cycles**:

1. Run all the conditions of the available rules.
2. Each rule whose condition returns true is **activated**.
3. Activated rules go onto a list called the **agenda**.
4. When condition checking is done, the engine executes the actions of the rules on the agenda. Executing a rule's action is called **firing** it.

**Firing sequence** can be determined several ways *(Ch. 50, "How It Works")*:

- **Arbitrary sequence** — the simplest. The order in which rules are written does not determine the order of firing. "This can help keep the computation simple."
- **Definition order** — always fire in the order the rules are defined. Email filter rules are the classic example: the first matching filter processes the message and later matching rules never fire.
- **Priority** (in expert-system circles, *salience*) — the engine picks the highest-priority rule on the agenda first. **Fowler's warning: "Using priorities is often considered a smell; if you find yourself using priorities a lot, you should reconsider whether a Production Rule System is the appropriate computational model for your problem."**

Another engine variation: whether to re-check rules for activation **after each rule fires**, or to fire everything on the agenda before rechecking. Depending on how rules are structured, this can change system behavior.

**Rule sets.** Rule bases usually contain distinct groups, each a logical part of the overall problem. Divide the rules into separate rule sets and evaluate them in a particular order — run the basic-data-validation set first, and only if there are no errors, run the qualification set.

#### Chaining

- **No chaining** — validation rules are the simplest kind. You scan all the rules; those that fire add an error or warning to a log or Notification. **One cycle of activation and firing is enough**, because the actions do not change the state of the data the system works with.
- **Forward chaining** — when rule actions *do* change the state of the world, you must reevaluate the conditions to see if any have become true, adding them to the agenda. "You start with some facts, use rules to infer more facts, these facts activate more rules, which create more facts, and so on. The engine stops only when there are no more rules on the agenda."
- **Backward chaining** — work the other way: begin with a goal, examine the rule base for rules whose actions would make the goal true, then make those rules' conditions subgoals, and so on. "It is less common in simple Production Rule Systems as it's much more involved to get a simple case working."

#### Contradictory inferences — the hard problem

"One of the great advantages of rules is that you can state each rule independently and let the Production Rule System figure out the consequences. But this strength comes with a problem. What if you get chains of inferences that contradict each other?" *(Ch. 50, "Contradictory Inferences")* His example: a reenactment club where one set of rules says an over-18 American citizen with a musket may join one army, and a separate rule elsewhere says British citizens may only join the other. A dual citizen activates both.

**The biggest danger is that you may not notice at all.** If the consequence is setting a Boolean, whichever rule runs last wins. Without a defined sequence or priority values, this leads to an incorrect inference, "or even different inferences depending on hidden qualities in the rule execution sequence."

Two broad approaches:

1. **Design the rule structure to avoid contradictions.** Ensure the way the rules run avoids contradiction — through how rules update data, by organizing rule sets, or by playing with priorities. Fowler's concrete convention: **start with all eligibility conditions set to false and only allow them to be changed to true.** That monotone discipline forces anyone wanting to *exclude* a group to write the rule a different way, "surfacing the potential contradiction while writing the rules." Caveat: "You have to be careful because a mistake can sneak in a rule that will potentially subvert the design."
2. **Record all inferences in a way that tolerates contradiction**, so you can spot one if it occurs. Instead of a Boolean for eligibility, create a separate **fact object** whose key is the conclusion and whose value is the Boolean. After running the rules, look for all facts with the key you care about — you can then spot facts with the same key but different values. The *Observation* pattern is one way to handle this.

Also: **beware circles in the rule structure**, where multiple rules keep each other firing endlessly — both from contradictory rules that keep arguing with each other and from positive feedback loops. Dedicated tools have their own techniques for these.

#### Three recurring rule structures

From limited observation, Fowler names three shapes *(Ch. 50, "Patterns in Rule Structure")*:

- **Validation** — common and simple. All rules have a simple consequence (raise a validation error) and there is little or no chaining. "I suspect most people who work seriously with Production Rule Systems wouldn't consider these to be rule systems since they are so simple — and, certainly, it seemed an overkill to me to use a specialized rules tool for something like this. However, this kind of simple structure is a nice one for you to write yourself."
- **Eligibility** — somewhat more involved: assessing whether a candidate qualifies for one or more agreements. Rules structure as **a progression of steps where lower-level rules lead to higher-level inferences**. You can avoid contradictions by keeping all the inferences positive, "perhaps with some separate route for disqualifications."
- **Diagnostic** — observe problems and determine root cause. "Here, you're much more likely to get contradictions, so having something like *Observation* is more important."

#### Put the smarts in the Semantic Model, not the builder

The most transferable design principle in the chapter comes out of evolving a validation DSL. Having written several null checks by hand, you realize the null-check logic belongs in the rule so the script just names the property. Fowler shows two ways to capture that property reference — a name string plus reflection, or a lambda expression whose *code text* can be printed back in the error message — and then makes the point that matters *(Ch. 50, "Evolving the DSL")*:

> "I want to stress here that I didn't need to change the *Semantic Model* to support this. Instead, I could easily put this code in the builder... It's often an easy reflex to put this kind of logic in the builder, but I urge you not to fall for it. If I put the logic in the Semantic Model, it will be able to make a much better use of the information, since it knows what it's doing."

His example of "better use": a Semantic Model that *knows* a rule is a not-null check can generate client-side code for that validation to embed in a form. A builder that has already flattened the rule into an anonymous predicate cannot — the information is gone. And even absent such a need: "my preference is to put smarts in the Semantic Model as much as possible. It isn't any more work than putting it in the builder, but it keeps the knowledge of the rules where it's most useful."

**The general form of this rule: don't collapse declared intent into an opaque closure at the API boundary.** A closure is a one-way door — you can call it, and that is all. A first-class model object representing *the kind of thing the user declared* can be called, serialized, rendered in another language, documented, introspected, and optimized.

Four more design points from the worked eligibility example *(Ch. 50, "Eligibility Rules")*:

- **Rules are open-ended.** "I can easily add new rules that say what it means to be of good stock, without altering the rules that are already in place." The downside is stated just as plainly: "there's no single spot in the rule base text where I can be sure of finding *all* the conditions." The mitigation is tooling — something capable of finding all the rules with a given consequence.
- **The data class is deliberately monotone** — all properties start false and can only be changed to true. "This enforces some structure in the rules system to avoid undetected contradictions."
- **The engine keeps a fired log.** Activated rules are removed from the available list so they cannot be activated twice, and fired rules move to a log which "later I can use… to provide a trace for diagnostic purposes." This is 14.1's tracing requirement made concrete.
- **Null-safety is moved into the engine.** Activation traps null-reference exceptions and treats them as a failure to activate, so a rule author can navigate a chain of references with no null checking — "moving that responsibility to the model." The library absorbs incidental complexity so user-authored predicates stay declarative.

#### When to use it

*(Ch. 50, "When to Use It")*

- A natural choice **when behavior feels like it is best expressed as a set of if-then statements.** "Indeed, just writing control flow like that is often a good starting point for evolving into a Production Rule System."
- **The big danger: Production Rule Systems are seductive.** A small example is easy to understand and demos well to nonprogrammers. "What isn't clear from simple demos is that it may become very hard to reason about what a Production Rule System is doing as it gets bigger, particularly if you are using chaining. This can make debugging very difficult."
- **Rule engine tools exacerbate this.** "It's very easy to stretch a tool — to use it in lots of places without realizing how difficult it is to modify until you've already built something too large." Hence the argument for **building something simple yourself**, which you can tune to your needs and use to learn about the domain and how a Production Rule System fits it; once you have learned more you can evaluate whether it is worth replacing your simple system with a tool.
- His summary judgement, quoted because it is unusually blunt: **"I'm not saying that rule engines are always a bad idea, although I've yet to see one that's worked well. What is important is that you should treat them with caution and understand what you are getting into when you use them."**

#### Relationships

An instance of Adaptive Model (14.1). The escalation target from Decision Table (14.2) when you must combine multiple kinds of conditionals. Uses Notification and Observation for error and fact collection. In the book it is populated by internal-DSL patterns, but the model is independent of how you configure it.

> **SDK lens:** **Validation libraries, policy and authorization engines, eligibility and pricing-rule services, alerting rules, and lint frameworks** are all this pattern, and Fowler's "validation is the simple, chain-free case that you should just write yourself" applies directly: most validation DSLs do not need a rule engine. **"Put the smarts in the Semantic Model, not the builder" is arguably the single most reusable API-design rule in this whole section.** For fluent and builder APIs, resist collapsing user intent into an opaque closure at the builder boundary; keep the *kind* of thing the user declared as a first-class model object and you retain the ability to serialize it, render it in another language, document it, introspect it, or optimize it. Collapsing to a lambda is a one-way door. Four more: **the agenda and fired log are API surface, not implementation detail** — anything rule-driven needs an explain facility; **open-endedness versus discoverability** is the core tradeoff of any plugin or rule-registration API, and Fowler's answer is tooling (find all rules with this consequence), which maps to introspection APIs and registry-dumping commands; **monotone state design** — fields start false and only ever get set true — is a cheap, general technique for making order-independence safe wherever independent extensions write to shared state; and the warning about tool creep, easy to adopt and hard to modify once large, applies to adopting *any* heavyweight rules or workflow engine as a dependency.

---

### 14.5 State Machine *(Ch. 51)*

**Intent:** Model a system as a set of explicit states with transitions between them. *(Ch. 51, intent)*

#### The concept

"Many systems react to stimuli differently, depending on some internal property. Sometimes it's useful to classify these different internal states and describe both the differences in response and what causes the system to move between these states. A State Machine can be used to describe and perhaps control this behavior." *(Ch. 51, opening)*

The sketch is the trivial one — *on* and *off*, with switch-down and switch-up events and close-circuit and open-circuit entry actions. Fowler is upfront that "the degree to which a State Machine is used varies with the situation, as does the form of State Machine in use."

#### Machine state versus object state — the chapter's most useful idea

To explore a less clear-cut case he models an order: created, then items freely added or removed or the order cancelled, then payment provided, then eligible to ship; before shipping you can still add, remove, or cancel; once shipped you cannot. States: *collecting*, *paid*, *shipped*, *cancelled*.

That sets up a distinction easy to gloss over:

> In general use, "the state of an object" means the combination of the values of its properties — so removing an item from an order changes its state. But the state machine diagram doesn't reflect all these possible states; it only shows a few. **"These are the states that are interesting in terms of the model, in that they affect the behavior of the system. I'll refer to this smaller set of states as *machine states*."** So while removing an item changes the state of the order, it doesn't change its machine state. *(Ch. 51, "How It Works")*

**And the judgement call that follows is the "when NOT to build one" advice:**

> "This state model is a useful way of thinking about the behavior of the order, but this doesn't mean that we want a state machine model in our software."

- The model tells you that `cancel` needs a check that you are in an appropriate state — but that can simply be a **guard clause** in `cancel`.
- Tracking which machine state the order is in could be a status field, "but it could also be completely derived" — you could determine the *paid* state by checking whether the payment authorization amount is at least the total cost.
- **"The diagram may still be a useful way to visualize how the order works, but you don't need the model to be manifest in the software."**

#### Common elements and variations

*(Ch. 51, "How It Works")*

- The essence: **multiple states the machine can be in**, and **multiple transitions defined on each state**, each triggered by an **event** and moving the machine to a **target state** — often, but not necessarily, a different one. "The resulting behavior of the machine is the definition of the states and the events that trigger the movement between states." Multiple transitions can share a target and still be separate transitions.
- **Unhandled events:** "A general question with state machines is how they react to an event that isn't defined on the state that the machine is currently in. Depending on the application, such an event may be an error, or it may be safely ignored." This is a design decision the model must make explicit.
- **Guarded transitions:** Boolean conditions on transitions, so the same event leads different ways depending on data. **"The Boolean conditions on the transitions should not overlap, otherwise the state machine won't know where to go."** Guards need not appear on all State Machines; the book's introductory example has none.
- **Binding actions is what makes it an Adaptive Model.** A state diagram alone is a **passive model** — it describes states and events but does not invoke actions that change the system. To have an Adaptive Model you need a way to bind actions into the machine, and there are two sensible places: **on transitions** (the action executes whenever the transition is taken) or **on states** (most commonly on *entry*, sometimes on *exit*). Some machines also allow **internal actions**, invoked when an event is received in that state — "like a transition back to itself, but perhaps without triggering any entry actions again."
- **Fowler's guidance on choosing:** "Different action-binding approaches suit different problems and different personalities. I don't have any strong guidelines to offer, other than to keep it as simple as it can reasonably be to model your behavior. Many implementations of state machine techniques have gone for the maximum expressiveness of the machine — such as the very expressive state machine models used by the UML. But small state machines suitable for DSLs can often work well with much simpler models."

The book's running example illustrates that restraint deliberately: no guarded transitions, actions bound to state entry only, and actions that do not execute arbitrary code blocks but only send a numeric command code. "This simplifies the state machine model and the DSLs to control it (which is very important for an example like this)." Real machines often need richer actions — which is where 14.1's guidance on embedding closures or commands comes back in.

#### When to use it

*(Ch. 51, "When to Use It")* — refreshingly honest:

> "I have that horrible feeling when I know that almost the only thing I can say is that you should use a State Machine when the behavior you're specifying feels like a State Machine — that is, when you have a sense of movement, triggered by events, from state to state. In many ways, the best way to see if a State Machine is appropriate is to try sketching one on paper, and if it fits well, to try it in action."

One concrete danger area, drawn from the book's language-theory material: **State Machines are limited to parsing regular grammars.** They cannot handle matching arbitrarily nested delimiters. "If your behavior has anything like that, you may run into the same problem."

#### Relationships

An instance of Adaptive Model (14.1) — but only once actions are bound; a pure state diagram is passive. It is the target model for most of the code-generation examples in section 15. Its regular-grammar limit is the same constraint that makes a lexer (12.4) a state machine and a parser a push-down machine.

> **SDK lens:** **Machine state versus object state is a public-API distinction.** When you expose a status or lifecycle enum on a resource, you are choosing which states are behaviorally interesting: exposing too many leaks internals, and exposing a *derived* state (Fowler's "paid means authorization ≥ total") avoids a redundant, drift-prone field. Deciding whether a status is stored or derived is a real API-design choice, not an implementation detail. **"You don't need the model to be manifest in the software"** is a caution against over-modeling — a guard clause in `cancel()` is often the whole of what the state machine buys you. Reach for an explicit state machine model when you need the behavior to be *configurable*, *inspectable*, or *generated*, not merely because the domain has states. Two invariants to enforce at configuration time rather than discover at runtime: **non-overlapping guards**, and an explicit, documented **unhandled-event policy** (error versus ignore) rather than an accident of implementation. Finally, note that State Machine and Production Rule System are the two models here most commonly exposed as API-configured models — workflow and order-status engines, connection and session lifecycles, retry and circuit-breaker state, protocol implementations. The action-binding decision (entry action, transition action, internal action) is exactly the callback-surface design question for such a library, and Fowler's advice is to pick the simplest binding that models your behavior rather than copying UML's maximal expressiveness.

---

## 15. Code generation patterns

Part VI contains six patterns organized along **three independent design axes**:

1. **How you write the generator:** Transformer Generation versus Templated Generation. Roughly — code that emits text, versus text with holes in it.
2. **What the generated code looks like:** Model-Aware Generation versus Model Ignorant Generation. Roughly — generated code that configures a runtime model, versus generated code with the logic inlined into control flow.
3. **Hygiene patterns that cut across both:** Embedment Helper — keep foreign code out of templates and grammars; Generation Gap — keep generated code out of handwritten files.

The axes are genuinely orthogonal. Fowler pairs Transformer Generation with Model-Aware Generation in one example and Templated Generation with Model Ignorant Generation in another, and points out the combinations explicitly. Axis 1 is chosen by the static/dynamic ratio and the structural complexity of the output; axis 2 is chosen by what the target environment can host and afford.

---

### 15.1 Transformer Generation *(Ch. 52)*

**Intent:** Generate code by writing a transformer that navigates the input model and produces output. *(Ch. 52, intent)*

#### The concept

Write a program that takes the Semantic Model as input and produces source code for the target environment as output. The generator is ordinary code — loops over model elements, string formatting, writes to an output stream. Nothing exotic: the sketch is a method that iterates the machine's events and writes one declaration line for each.

#### Input-driven versus output-driven — the key conceptual tool

Fowler frames every routine in a transformer as one of two kinds *(Ch. 52, "How It Works")*:

- **Output-driven transformation** "starts from the required output and dives into the input to gather the data it needs as it goes." Generating a web page from a product catalog, output-driven, looks like `renderHeader(); renderBody(); renderFooter();`.
- **Input-driven transformation** "walks the input data structure and produces output": for each product, render its name, then for each photo, render the photo.

> "Often, transformers use a combination of the two. I seem to regularly run into situations where the outer logic is output-driven, but it calls routines that are more input-driven. The outer logic describes the broad structure of the output document, dividing it into logical sections, while the inner section produces output driven by a particular kind of input data. **In any case, I find it useful to think of each routine in the transformation as either input-driven or output-driven and to be conscious of which I'm using.**"

The worked example shows why the outer level must be output-driven: **all states have to be declared before any transitions**, because forward-referencing a state is an error in the target language. The output-driven outer routine is where that ordering constraint is enforced — a good illustration of why the outer structure follows the *output's* requirements, not the model's shape.

#### Multistage transforms

Many transformations go directly from Semantic Model to target source, but for more complicated cases it is useful to break the transformation into steps *(Ch. 52, "How It Works")*:

- A **two-step transform** walks the input model and produces an **output model** — a model, not a text, but oriented towards the generated output. A second step walks the output model and produces the output text.
- It is useful when the transform is complicated, **or when you have multiple output texts to produce from the same input that share some characteristics.** With multiple outputs, the first-stage transform produces a single output model with the common elements, and the differences go in varying second stages.
- **You can mix techniques across stages** — Transformer Generation for the first, Templated Generation for the second.

#### When to use it

*(Ch. 52, "When to Use It")*

- **Single-stage Transformer Generation** is a good choice when the output text has a **simple relationship with the input model and most of the output text is generated.** In that case it is very easy to write "and doesn't require introducing a templating tool."
- **Multi-stage** is very useful when the input/output relationship is more complex, "as each stage can handle a different aspect of the problem."
- **It pairs naturally with Model-Aware Generation:** "If you use *Model-Aware Generation*, you can usually populate the model with a simple sequence of calls, which is easy to generate with Transformer Generation." The example makes the pairing explicit: "Using Model-Aware Generation often goes with Transformer Generation as the separation between generated code and static code is clear, allowing any sections of generated code to have very little static code."
- The implicit contrast, stated fully in 15.2: when the output is mostly *static* text with occasional simple dynamic bits, use Templated Generation instead.

One small craft note from the example, easy to overlook: the generator emits **comments containing dynamic data** — generated code carrying orientation for the humans who will later read it in a debugger.

#### Relationships

Alternative and complement to Templated Generation (15.2); the two mix within a multistage transform, and printf-style formatting means they intermix at fine grain too. Pairs naturally with Model-Aware Generation (15.4). Consumes the Semantic Model.

> **SDK lens:** This is how most **client-SDK generators** work — spec model in, source out — and the input-driven/output-driven distinction is a practical way to organize one: the file skeleton (imports, class shell, footer) is output-driven; the per-operation and per-model-type sections are input-driven. **The multistage transform with an intermediate output model is the standard answer to multi-language SDK generation:** one first stage normalizes the spec into a language-agnostic output model (resolved types, naming conventions, pagination shape), and per-language second stages render it. That is exactly Fowler's "multiple output texts from the same input that share some characteristics," and it is why mature generators have an intermediate representation rather than templates that read the spec directly. The transformer-versus-template choice reduces to a single question — **is the generated file mostly boilerplate scaffolding, or mostly synthesized structure?** Most SDK generators do both, and the advice is to stay conscious of which mode each routine is in.

---

### 15.2 Templated Generation *(Ch. 53)*

**Intent:** Generate output by handwriting an output file and placing template callouts to generate variable portions. *(Ch. 53, intent)*

#### The concept

The inverse framing to Transformer Generation: **write the output file you want, then insert callouts for the bits that vary.** A template processor combines the template file with a *context* that fills the callouts, producing the real output file.

Fowler roots it historically: "Templated Generation is a very old technique, familiar to anyone who has used mail-merge facilities in a word processor." It is very common in web development, where the *entire document* is a template — but templating also works in smaller contexts. "**The old faithful `printf` function in C is an example of using Templated Generation to print out a single string at a time.**" He usually reserves the term for the whole-document case, "but `printf` reminds us that Templated Generation and *Transformer Generation* can be very intermixed." Textual macro processors are another form.

#### The three components

*(Ch. 53, "How It Works")*

- **Template** — the source text of the output file, with dynamic parts represented by callouts that reference the context.
- **Context** — the source for dynamic data; "essentially, the data model for the template generation." It may be a simple data structure or a more complex programmatic context.
- **Templating engine** — the tool that brings template and context together. A controlling program runs the engine with a particular context and template, "and may run the same template with multiple contexts to produce multiple outputs."

#### Callout languages: host code versus a templating language

- **The most general form allows arbitrary host code expressions in the callouts.** "Like any form of *Foreign Code*, it needs to be used with care, otherwise the structure of the host code can overwhelm the template." Fowler's strong recommendation: **"if you have a template processor that embeds arbitrary host code, you confine yourself to simple function calls within the callouts, preferably using an *Embedment Helper*."**
- Because template files so commonly get "thoroughly messed up due to too much host code," many processors instead provide a restricted **templating language**, "usually quite restricted to encourage simpler callouts and preserve the clarity of the template structure."
- The **simplest** templating language treats the context as a map and provides expressions to look up values and insert them. Sufficient for simple templates, but three common needs push further: **iteration** ("a common driver for more complex templating"), **conditionals**, and **subroutines** (duplicated chunks of template source suggest the need for some subroutine mechanism inside the template language).
- **The governing advice:** "My general advice here is to be as minimalist as possible, **since the strength of Templated Generation is directly proportional to how easy it is to visualize the output file by looking at the template.**" *(Ch. 53, "How It Works")*

#### When to use it

*(Ch. 53, "When to Use It")*

- **The great strength:** "you can look at the template file and easily understand what the generated output will look like." Most useful when there is **quite a lot of static content** in the output while the dynamic content is **occasional and simple**.
- **First indicator:** the proportion of static content. "The greater the proportion of static content, the more likely that it will be easier to use Templated Generation."
- **Second consideration:** the complexity of the dynamic content. "The more you use iterations, conditionals, and advanced templating language features, the harder it is to comprehend what the output will look like from the template file. When this happens, you should consider *Transformer Generation* instead."

So the two patterns sit at opposite ends of one spectrum: **static-heavy plus simple dynamics → template; generated-heavy plus complex structure → transformer.**

#### Practical points from the example

*(Ch. 53, example)*

- **The context is a single Embedment Helper.** Rather than pushing model objects and loose values into the template context, he places just one helper object initialized with the model, and the template reaches everything through it.
- **Where the line falls between model and helper:** simple properties come straight off Semantic Model objects, but derived names and identifiers are helper methods — building the constant names, assigning integer identifiers. Logic that would be ugly in the template goes in the helper, including assembling a state's full transition list by combining the model's own transitions with derived ones.
- **A generator and its target can compete for the same syntax.** In his example the C preprocessor is itself a form of Templated Generation, and both it and the template engine use `#` as a command marker; the engine happens to pass through commands it does not recognize. That is luck, not design. **Choose a template delimiter that does not collide with your target language's syntax.**
- Two asides that reveal his values: he generates named constants rather than raw codes **"because I prefer even my generated code to be readable"**; and he cheerfully recomputes a sorted list every time he needs an identifier, noting he would cache it if it were a performance issue, but it is not.

#### Relationships

The opposite end of a spectrum from Transformer Generation (15.1), and combinable with it in a multistage transform. Strongly associated with Embedment Helper (15.3) — templating with arbitrary host code should almost always use one. A form of Foreign Code (13.5) embedded in a foreign representation. The book's example generates Model Ignorant Generation output (15.5).

> **SDK lens:** Templates are the right tool for the **boilerplate-heavy files in a generated SDK** — package manifests, README scaffolds, client class shells, per-endpoint method bodies with a fixed shape. Transformers are better for anything with structural variation: type mapping, union and discriminator handling, nested schema flattening. Fowler's line — **"the strength of Templated Generation is directly proportional to how easy it is to visualize the output by looking at the template"** — is a usable acceptance criterion for a generator's maintainability. A template that has become unreadable to someone who knows the target language has stopped paying for itself, and that is the signal to move logic into a helper or switch to a transformer. And treat delimiter collision as a real hazard, not a curiosity: template syntax inside YAML, inside HTML-like targets, or inside another templating language is a recurring source of unreadable escaping.

---

### 15.3 Embedment Helper *(Ch. 54)*

**Intent:** An object that minimizes code in a templating system by providing all needed functions to that templating mechanism. *(Ch. 54, intent)*

#### The concept — the separation principle

"Many systems allow you to extend the capability of a simple representation by embedding general-purpose code into that representation to do things that otherwise would not be possible." *(Ch. 54, opening)* Fowler's three examples span the whole book: embedding code into **web page templates**, putting **code actions into grammar files**, and putting **callouts into code generation templates**.

This mechanism of general-purpose Foreign Code "adds a lot of power to the representation it's embedded into, without complicating the basic representation itself. **However, a common problem when you do this is that the Foreign Code can end up being quite involved and obscure the representation that it's embedded into.**"

The pattern: **move all the complex code into a helper class, leaving only simple method calls in the host representation. "This allows the host representation to be dominant and retain its clarity."**

That is the separation principle in one line: *the foreign representation — grammar, template, config — should read as itself, not as host-language code with a bit of grammar sprinkled in.*

#### How it works

- Mechanically it is "similar to a refactoring": create the helper, make it visible to the host representation, and move all the code out of the host representation into the helper, leaving just a method call behind.
- **The one tricky technical aspect is getting an object into the visible scope** when the host representation is processed. "Most systems give you some mechanism to do this — they need to in order to call libraries — but it's sometimes a bit messy." In a templating engine the helper is placed in the context; in a parser generator it is declared as a field on the generated parser, or made the generated parser's superclass.
- Once the helper is visible, **"any code that's more than a simple method call should move into the Embedment Helper, so the only code left in the host representation is simple calls."**
- **The remaining complication is not technical:** how do you make it clear what the helper's code is doing? "The key to this, as with any abstraction, is careful naming of the methods, so they clearly state the intention of the called code without revealing its implementation. This is the same basic skill as method and function naming in any context — a central skill of a good programmer." *(Ch. 54, "How It Works")*

The "before" in Fowler's grammar example is worth stating, because it is the concrete damage the pattern prevents: a grammar whose rules carry inline code that stuffs elements into maps, looks up or creates model objects, constructs the top-level model on first use, and wires relationships, with symbol tables and general helper functions in the grammar's members section. His summary: **"With such inlined code, grammar files can have more lines of [host language] than the grammar DSL."** The "after" is one call per rule — add this event, add this state, add this transition — and the grammar reads as a grammar again. A related trick keeps it even thinner: **pass the raw tokens to the helper rather than extracting text in the grammar**, "to keep the amount of code in the grammar file to the minimum."

#### A naming judgement worth its own note

Should helper methods be **command-oriented** (`addEvent`, `addState`) or **event-oriented** (`eventRecognized`, `stateNameRecognized`)? *(Ch. 54, "Secret Panel States")*

> "The argument for event-oriented names is that it doesn't imply any action on the helper, leaving it up to the helper to decide what to do. This is particularly handy if you use different helpers with the same parser that do different things in reaction to the parse. The problem with event-oriented names is that you can't tell what's going on by just reading the grammar. In a case where I'm only using the grammar for one activity, I'd rather be able to read the grammar and see from the naming what's happening at each step."

The tiebreaker is therefore: *how many differently-behaving consumers will there be, and does the call-site reader need to know what happens?*

#### Should the helper generate output? — a genuine debate

When combined with Templated Generation, a common question is whether the helper should generate output. "I often hear this as an absolute point: **Helpers must never generate output.** I don't agree with this absoluteness." *(Ch. 54, "Should a Helper Generate HTML?")*

- **The real cost:** "there is a problem with generating output in the helper — any such output isn't visible from the template. Since the whole point of Templated Generation is that you see the output with holes, such hiding of generated material is, without doubt, a problem."
- **The counterweight:** "this problem has to be weighed against the complexity of retaining the output in the template and the more complicated constructs of *Foreign Code* you may need if you want to avoid generating output in it. This is a balance that you have to consider in each case, and although I would say it's good to avoid generating from the Embedment Helper, I'm not inclined to agree that it is always better than the alternative."
- **The middle ground is the point of the example:** the helper can take the *logic* without taking the *output*. Expose predicates and derived values to the template — "does this item have a link? what is its target?" — and the template keeps its own markup while no longer containing the precedence rules that decide between link kinds. "This is where some of the logic can go into the Embedment Helper without having it generate output."
- **His conclusion:** "putting some output generation in the Embedment Helper is a reasonable choice. **The more complicated the logic and the more complicated the overall template, the more I gain by moving output generation to the Embedment Helper where I can factor it better.**"
- **The strongest objection, and its scope:** "The biggest objection to this occurs when you have separate people working on the template (such as an HTML designer) and the code. This leads to a coordination cost for some changes. … **Of course, this is only a problem if you have different people working on the different files; when generating code for a DSL, this is usually not the case.**" The deciding variable is organizational, not technical.

#### When to use it

*(Ch. 54, "When to Use It")* — a near-universal recommendation, unusually for Fowler:

- "I'm very suspicious of patterns that someone claims should always be used, but Embedment Helper is one of those things I would always suggest doing, except in really trivial cases."
- The justification is empirical: "I've looked at a fair bit of code using *Foreign Code* in my time, and I see a huge difference if Embedment Helper is present. Without it, it's hard to see the host representation, so much so that it rather defeats the purpose of using an alternative representation at all. For instance, **a grammar file with lots of Foreign Code in actions makes it very hard to see the basic flow of the grammar.**"
- **A second benefit: tooling.** With a sophisticated IDE, embedded code cannot be edited with the IDE's tooling; move it to a helper and "you're back in your full editing environment. Even simple text editors benefit a bit by simple things such as code coloring, which usually won't work properly for embedded code."
- **The one situation where you do not need one:** "where you are using classes that act as a natural home for providing this kind of information. An example of this is if you are doing *Templated Generation* with a *Semantic Model*. In this case, much of the behavior that you would have in an Embedment Helper can reasonably be part of the Semantic Model itself — **provided this doesn't make the Semantic Model too complex.**"

#### Relationships

Applies to Foreign Code (13.5) wherever it appears: parser-generator actions in grammar files, Templated Generation callouts (15.2), web templates. Explicitly required by Parser Generator (12.7) — "the only code in the grammar should be single method calls" — and by BNF's code-action discussion (12.3). Can be omitted when a Semantic Model naturally provides the needed behavior, as in the Generation Gap example (15.6).

> **SDK lens:** The general principle — **keep foreign code out of the foreign representation** — is a config and DSL surface design rule. Anywhere a library lets users embed host code into a declarative artifact (build config, CI YAML with inline scripts, query DSLs with raw-SQL escape hatches, schema files with hooks), offer a way to *name and call out to* real code rather than inline it. If your API forces users to inline logic, their declarative files stop being readable as declarations. Three specific transfers. **Command-oriented versus event-oriented naming is a general callback and hook API question**: event names keep the emitter decoupled and support multiple differently-behaving listeners; command names make the call site self-documenting. **The tooling argument is a real developer-experience argument for extension APIs** — code in a normal source file gets refactoring, autocomplete, type checking, and highlighting; code inside a string or config file gets none of it, which alone often justifies a "reference a function by name" mechanism over an "inline a snippet" one. And the should-the-helper-generate-output debate generalizes to **how much a helper or formatter layer should own**: pulling logic out is nearly always good, but pulling *the visible artifact* out trades reviewability for factoring — and Fowler's tiebreaker is whether different people own the two files.

---

### 15.4 Model-Aware Generation *(Ch. 55)*

**Intent:** Generate code with an explicit simulacrum of the semantic model of the DSL, so that the generated code has generic-specific separation. *(Ch. 55, intent)*

#### The concept

When you generate code, you embed the semantics of the DSL script within that code. **Model-Aware Generation replicates some form of the Semantic Model in the generated code in order to preserve the separation of generic and specific code within the generated code.**

The sketch shows the split clearly. On the DSL-processor side of the line sits the Semantic Model, which *generates* a small body of code — a handful of declaration calls such as `declare_state("idle")` and `declare_transition("idle", "doorClosed", "active")` — that lives on the target-environment side and *uses* a second semantic model that also lives in the target environment.

So the target environment gets **a hand-written generic runtime model** plus **a small generated configuration script that populates it**.

#### How it works

- **"The most important aspect of Model-Aware Generation is that it preserves the principle of generic-specific separation. The actual form that the model takes in the generated code is much less important, which is why I like to say that the generated code contains a *simulacrum* of the Semantic Model."** *(Ch. 55, "How It Works")*
- It is a simulacrum for good reasons: "Usually, you are generating code because of limitations in the target environment — these limitations often make it harder to express a Semantic Model than you would like. As a result, lots of compromises will need to be made, which makes the Semantic Model less effective as a statement of the intent of the system. **However, it's important to realize that this isn't such a big deal as long as you keep the generic-specific separation.**"
- **The testability property is the most practically valuable part of the pattern:**

  > "Since the simulacrum model is a self-standing version of the Semantic Model, you can, and should, build and test the model without using any code generation. **Ensure the model has a simple API to populate it.** The code generation will then generate configuration code that calls this API. You can then test the simulacrum model using testing scripts that use this same API. This allows you to build, test, and refine the core behavior of the target environment with running the code-generation process. You can do this with a relatively simple test population of the model, which should be easier to understand and debug." *(Ch. 55, "How It Works")*

  In other words: the generator and the runtime become **independently testable**, joined only by a small, stable API.

#### What the worked example makes concrete

The scenario is generating C for a constrained controller from an existing Semantic Model, and the chapter deliberately concentrates on **what the final code — generated and handwritten together — looks like** rather than on generating it.

- **Implementation shape:** a data structure plus routines that navigate it, with all memory allocated up front and integer references representing every link between parts of the model — the C-flavored simulacrum of object references.
- **Encapsulation:** all the data definitions live in a single file, "encapsulate[d]… behind a bunch of externally declared functions. **The specific code only knows about these functions and is, rightly, ignorant about the data structure itself. In this case, ignorance is truly bliss.**" Those declaration functions constitute the model's population API — precisely the "simple API to populate it" the pattern calls for.
- **The consequence of that encapsulation is the payoff, and it is a versioning payoff:** the model's internals are primitive (linear scans to look up names). "In running the machine we might be better off replacing the linear search with a hash function. **Since the state machine is well encapsulated, this is easy to do… Changing such implementation details of the model doesn't affect the interface of the configuration functions that define new state machines. This is an important encapsulation.**"
- **Readability of generated code, stated as a principle:** "I believe that generated code should be readable even if it isn't edited, because it will often be used for debugging. **To make it readable, you have to understand your target audience, such as who is doing the debugging.**" He therefore avoids pointer arithmetic in favor of array indices, even though many C programmers would prefer the former — "even if you as a generator writer are comfortable with pointer arithmetic, you should be wary of using it in the generated code if the people reading that code aren't comfortable."
- **A deliberate loss of intent:** the target model has no notion of one of the DSL's concepts (reset events); those are translated into extra ordinary transitions. "This makes running the state machine simpler, and is **an example of a typical tradeoff where I prefer simplicity of operation to clearly stating intent. For the true Semantic Model, I prefer to keep as much intent as I can, but for a model in a generated target environment I value capturing intent a little less.**"
- **Where he stops simplifying:** he could strip all the names, since they are only used while configuring. He keeps them because he prefers even generated code to be readable, "but more importantly it allows the state machine to produce more useful diagnostics when things go wrong. I'd sacrifice this, however, if space was really tight in the target environment."

**The second example is the payoff case.** Generating C means recompiling to set up a new machine. But Model-Aware Generation also lets you build the model **at runtime**, by driving population through a data file rather than compiled calls: a plain line-oriented text file is generated from the Semantic Model, and a small interpreter in the target reads it with Delimiter-Directed Translation, dispatching each line to the very same declaration functions. Two lessons *(Ch. 55, "Loading the State Machine Dynamically")*:

- On the file format: "I don't consider this textual format a DSL, as I designed it to make it easy to interpret, not for readability by humans. It's useful to have a certain amount of human readability … as that helps in debugging. Still, in this case human readability was a distant second to ease of interpretation." A clean statement of the difference between **a DSL and a wire/config format.**
- The general lesson: "**code generation for a static target language does not mean you cannot use runtime interpretation.** … **By generating a file that's designed for ease of interpretation in the environment I have available, I can minimize the cost of the interpreter.**" And the boundary of the pattern is named too: you could go a step further and put the full DSL processor in the target, "but this would raise the processing demands … and we would no longer be in the world of Model-Aware Generation."

#### When to use it

*(Ch. 55, "When to Use It")*

**Advantages over Model Ignorant Generation:**
- The simulacrum model, built without generation, "is easier to build and test, because you don't have to rerun and comprehend code generation while working on the simulacrum model."
- "Since the generated code is now made up of API calls on the simulacrum model, that code is much easier to generate, which makes the generator simpler to build and maintain."

**The two reasons not to use it — both about the target environment:**
- "Either it's too hard to express even a simulacrum model" in the target, **or** "there are performance problems with having a simulacrum model at runtime."

**A framing sentence worth remembering:** "In many cases, you are using DSLs as a front end to an existing model. **If you are generating code to work with the model, then you are using Model-Aware Generation.**"

#### Relationships

The counterpart to Model Ignorant Generation (15.5), and Fowler's default preference. Pairs naturally with Transformer Generation (15.1), since the generated output is a simple sequence of API calls. The target-side simulacrum is an Adaptive Model (14.1) living in the target environment. The dynamic-loading variant uses Delimiter-Directed Translation (12.1) in the target.

> **SDK lens:** This is the most directly SDK-relevant pattern in the whole of Part VI. **"A thin generated layer over a fat hand-written runtime" is the dominant architecture of good generated client SDKs.** The generated code should be a declarative configuration or registration surface — endpoint descriptors, type registrations, method stubs that call a shared request pipeline — while retry logic, auth, serialization, pagination, and error mapping belong in a hand-written, versioned runtime library that the generated code calls. Fowler's argument for the split is exactly the argument for that architecture: the runtime is testable without running the generator, and the generator becomes trivial because it only emits API calls. **"Ensure the model has a simple API to populate it"** is a concrete requirement on that runtime's public (or internal-but-stable) surface: the population API is the contract between generator and runtime, and keeping it small and stable is what lets each side evolve. **The encapsulation payoff is a versioning payoff** — because the generated code only knows the declaration functions, the runtime can change its internals without regenerating anything; conversely, if generated code reaches into runtime internals, every runtime change forces a full regeneration across all consumers. Two more: **generated code is read constantly** (stack traces, "what does this method actually send?"), so calibrate readability to whoever will debug it — named constants, provenance comments, idioms familiar to the target language's users. And **the dynamic-loading example is the "ship a spec file, not a recompile" pattern**: generate a machine-readable descriptor that a compiled runtime interprets, so behavior changes do not require rebuilding and redistributing. Note the design guidance attached to it — *that generated file is optimized for ease of interpretation, not human readability.* It is a serialization format, not a DSL, and conflating the two makes both worse. Lastly, the deliberate loss of intent in the target model is a good general reminder: **the fidelity you demand of your true Semantic Model need not be demanded of a derived artifact.**

---

### 15.5 Model Ignorant Generation *(Ch. 56)*

**Intent:** Hardcode all logic into the generated code so that there's no explicit representation of the Semantic Model. *(Ch. 56, intent)*

#### The concept

The opposite pole from Model-Aware Generation. The sketch shows a Semantic Model generating, straight into the target environment, an event-handling function containing a switch on the current state and nested conditionals on the incoming event. **There is no model data structure in the target at all** — the model's content has been dissolved into control flow.

#### How it works

The enabling insight: "One of the advantages of code generation is that it allows you to produce code that would be too repetitive to write by hand in a controlled way. **This opens up implementation options that, usually, you would wisely shy away from because of duplicating code. In particular, this allows you to take behavior usually represented through data structures and encode them in control flow.**" *(Ch. 56, "How It Works")*

The method: "start by writing an implementation of a particular DSL script in the target environment. **I prefer to start with a very simple and minimal script.** The implementation code should be clear, but can freely intermingle generic and specific code, and I don't have to worry about repetition in the specific elements, since these will be generated. **This means I don't have to think about clever data structures, usually preferring procedural code and simple structures.**"

That is the distinctive freedom of the pattern: because a machine is writing it, you can relax the normal don't-repeat-yourself discipline and prefer flat, obvious, repetitive code. In the worked example the states, events, commands, and every transition and action are **baked into identifiers and control flow** — there is nothing at runtime that could be called a state machine model. Fowler's closing note captures it exactly: "**While this code would be too repetitive to write by hand for different machines, when generated it is quite easy to follow.**"

#### When to use it

*(Ch. 56, "When to Use It")* — two reasons to use it:

1. **Target-environment limitations.** "Target environments often involve languages with limited facilities for structuring programs and building a good model. In these situations, it's not possible to use *Model-Aware Generation*, so Model Ignorant Generation is pretty much the only option."
2. **Runtime resource pressure.** "When using Model-Aware Generation results in an implementation that demands too much runtime resources. Encoding logic in control flow may reduce memory needs or increase performance; if these are sufficiently critical, then Model Ignorant Generation is a good way to get there."

**Fowler's preference and the honest counterweight:**

> "On the whole, however, I prefer to see Model-Aware Generation if it's possible. It's usually easier to generate code with Model-Aware Generation, which results in a generation program that's simpler to understand and modify. Having said that, **using Model Ignorant Generation often makes the generated code easier to follow. This has the converse effect that it can be easier to figure out what to generate, although harder to write the code to generate it.**"

That last sentence is the crisp statement of the tradeoff: **Model Ignorant Generation moves complexity from the generated artifact into the generator; Model-Aware Generation moves it from the generator into a hand-written runtime.**

#### Relationships

Counterpart to Model-Aware Generation (15.4), which Fowler prefers where possible. Generated in the book's example by Templated Generation (15.2) — static-heavy output with simple dynamic parts is exactly what this pattern produces, mirroring the Transformer plus Model-Aware pairing in 15.1.

> **SDK lens:** This is the right choice when **the target cannot host a runtime library**: embedded or constrained environments, generated code that must be dependency-free, single-file drop-in artifacts, or environments where adding a runtime dependency is politically or technically impossible. "Zero-dependency generated client" is a real product requirement, and it forces this pattern. It is also right when **inlining wins on performance or size** — the classic generated-serializer or generated-parser case where a table-driven runtime is slower or bigger than unrolled control flow. But state the costs, because they are the mirror image: **every behavior fix requires regenerating and redistributing to all consumers**, since there is no shared runtime to patch. With Model-Aware Generation you ship a runtime patch; here the bug is baked into every user's checked-in generated files, and that is usually the decisive argument for Model-Aware in library ecosystems. The one genuine counterweight is trust: fully inlined generated code is auditable by the consumer without learning your runtime, which some consumers value highly.

---

### 15.6 Generation Gap *(Ch. 57)*

**Intent:** Separate generated code from non-generated code by inheritance. *(Ch. 57, intent)*

#### The concept

"One of the difficulties of code generation is that generated code and handwritten code need to be treated differently. **Generated code should never be edited by hand, otherwise you can't safely regenerate it.**" *(Ch. 57, opening)*

Generation Gap keeps the generated and handwritten parts separate **by putting them in different classes linked by inheritance.** The sketch: a schema generates a class carrying the declared fields; a handwritten class extends it and adds a derived member.

Fowler attributes the pattern carefully: "This pattern was first described by the late John Vlissides. In his formulation, the handwritten class was a subclass of the generated class. My description is a little different, based on the use I've seen; I really wish I were able to talk it through with him."

#### How it works

**Basic form:** generate a superclass and hand-code a subclass.

- "This way you can always override any aspect of the generated code that you like in the subclass."
- "The handwritten code can easily call any generated features, and the generated code can call hand-coded features by using **abstract methods** — which the compiler can check are implemented by the subclass — or **hook methods** which are only overridden when needed."
- **"When you refer to these classes from outside, you always refer to the handwritten concrete class. The generated class is effectively ignored by the rest of the code."**

**The three-class structure.** A common variation adds a third class: a **handwritten class that is a superclass of the generated class**, to pull out any logic that does not depend on the variations triggered by code generation.

| Class | Kind | Contains |
|---|---|---|
| Handwritten base class | handwritten | logic that doesn't vary based on the parameters to code generation |
| Generated class | generated | logic that can be generated automatically from the generation parameters |
| Handwritten concrete class | handwritten | logic that can't be generated and relies on generated features — **"the only one that should be mentioned by other code"** |

The rationale for the base class: "Instead of generating the nonvarying code, having it in a superclass allows it to be better tracked by tools, particularly IDEs." And behind that sits the general principle *(Ch. 57, "How It Works")*:

> "**In general, my suggestion with code generation is to generate as little code as possible.** This is because any generated code is more awkward to edit than handwritten code. Whenever you change generated code, you need to rerun the code generation system. Refactoring capabilities of modern IDEs won't work properly with generated code."

You do not always need all three. "If you don't have any unvarying logic, you don't need the handwritten base class. Similarly, if you never need to override the generated code, you can skip the handwritten concrete class. Thus another reasonable variation of Generation Gap is a handwritten superclass and a generated subclass." And a candid admission: "Often, you find more complex structures of generated and handwritten classes, related by both inheritance and general calling use. **The interplay of code generation and handwriting does lead to a more complicated class structure — this is the price you pay for the convenience of code generation.**"

**The empty-concrete-class rule.** What do you do when you have handwritten concrete classes *some* of the time but not all? You must decide what happens for the ones with nothing to override. You could make the generated class the named class used by calling code, "but that causes a lot of confusion over naming and usage. **As a result, I prefer to always create a concrete class, leaving it empty if it has nothing to override.**" Who creates the empty ones is a volume question: "If there's only a few and they change rarely, then it's fine to leave it to a programmer. However, if you have a lot of them and they change frequently, then it's good to tweak the code generation system to check if there's an existing concrete class and generate an empty one if not."

#### The extension-point recipe from the example

The schema-to-data-class example demonstrates generated-to-handwritten collaboration in a way worth lifting whole *(Ch. 57, "Generating Classes from a Data Schema")*:

- The **handwritten base class** defines the validation entry point, which creates a Notification, calls an **abstract** per-field check method and an **empty hook** class-level check method, and returns the notification.
- The **generated class** implements the abstract method by calling one check per field — generated from the same information used to generate the fields, so **it can never drift out of sync with the field list.**
- Those per-field checks are themselves **generated as empty hook methods**, so the **handwritten concrete class** can override any of them to add real validation.
- The class-level hook is for validations involving several fields together, overridden only in the handwritten concrete class.
- Net effect: **the abstract method gives compiler-enforced completeness; the hooks give opt-in extensibility; and the handwritten code never has to enumerate the fields.**

Two further notes from the same example. The **Semantic Model plays the Embedment Helper role** — the template calls type-mapping and name-deriving methods directly on model objects, which is exactly the exemption 15.3 carved out. And a build-process aside with practical weight: "When generating code is in a compiled language …, the build process can often get in the way. … **An alternative approach is to use a scripting language for code generation; then I only have to run a script to generate code. This simplifies the build process at the cost of introducing another language.**"

#### When to use it

*(Ch. 57, "When to Use It")*

- "Generation Gap is a very effective technique that allows you to create one logical class split into separate files to keep your generated code separate."
- **Language requirement:** "You do need a language with inheritance to pull it off. Using inheritance means that any members that can be overridden need to have sufficiently relaxed access controls to make them visible to subclasses — that is, not private." Generation Gap therefore forces protected or package visibility on anything overridable.
- **Alternative — partial or open classes.** "If your language allows you to put code for one class in multiple files … then this is an alternative to Generation Gap. The advantage of partial class files is that it allows you to separate generated and handwritten code without using inheritance — everything is in one class." But the mechanisms differ in power: partial classes are "good for adding features to generated classes" but give you "no mechanism to override features," whereas open classes "do handle this by evaluating the handwritten code after the generated code — which allows you to replace a generated method with a handwritten one."
- **The anti-pattern it replaced.** "The common early alternative to Generation Gap was generating code into a marked area of a file between comments that said something like `code gen start` and `code gen end`. The trouble with this was that it was confusing, leading to people modifying the generated code and awkward source control diffs. **Keeping generated code in separate files is almost always a better idea if you can find a way to do it.**"
- **Prefer collaboration to inheritance when you can.** "Although Generation Gap is a nice approach, it isn't the only way to keep generated code separate from handwritten code. Often, it works well just to put the two in separate classes with calls between them. **Collaborating classes are a simpler mechanism to use and understand, so in general I prefer them. I am only pushed to Generation Gap when the call interaction becomes more complicated — for example, when there is a default behavior in the generated class that I want to override for special cases.**"

That last paragraph is the actual decision rule: **inheritance only when you need to override defaults; otherwise plain collaboration.**

#### Relationships

Applies to any code generation — orthogonal to Transformer versus Templated Generation (15.1, 15.2) and to Model-Aware versus Model Ignorant Generation (15.4, 15.5). Its "handwritten base class" layer is, in a generated-SDK architecture, the same thing as Model-Aware Generation's hand-written runtime. It is also one of the two ways to attach an Embedment Helper (15.3) to a generated parser, per Parser Generator (12.7).

> **SDK lens:** Generation Gap is the canonical answer to "how do users customize a generated client SDK?" **The invariant to enforce is that generated files are never hand-edited** — every generated-SDK ecosystem that violates it ends up with users' local edits silently lost on regeneration, or users pinning to an old generator version. Generation Gap makes the boundary a *file and class* boundary rather than a comment marker, and Fowler's dismissal of the marked-region style ("confusing, leading to people modifying the generated code and awkward source control diffs") is a direct verdict on tooling that still ships it. **The three-layer structure maps cleanly onto generated SDKs:** hand-written runtime and base (transport, auth, retry, serialization — the non-varying logic, which is also 15.4's runtime); generated layer (per-endpoint methods, per-schema models); hand-written concrete layer (convenience methods, an override for one weird endpoint) — and **only the last is what user code names.** **"Generate as little code as possible"** is the load-bearing guidance: every generated line is a line your users' IDEs cannot refactor, that bloats their diffs, and that you must regenerate to fix, so push everything invariant down into the runtime. **Always emit the concrete class, even empty** — otherwise user code sometimes names the generated class and sometimes the handwritten one, and adding a customization later becomes a breaking rename at every call site; that rule is precisely the stability guarantee a public SDK needs. Two more: **visibility constraints are a real API consequence** — designing a generated class means deciding up front which members are extension points and which are sealed; and **the abstract-method plus hook-method pairing is a reusable extension-point recipe** — abstract where the compiler should enforce that generated code supplied something over an enumerable set, empty hooks where extension is optional. Finally, for multi-language generators, remember that the separation mechanism must be idiomatic per target (partial classes, open classes, declaration merging, embedding) rather than forcing inheritance everywhere — and **prefer collaboration over inheritance unless you genuinely need per-case default overrides.**








# Part 4 — Synthesis: The SDK Designer's Playbook

Everything below is assembled from Parts 1–3; nothing is new. This part exists so that the cross-cutting
principles — which the book scatters across 57 chapters because each chapter is written to stand alone —
are stated once, together, in the form you would apply them while designing a library.

## 16. The core principles, collected

### 16.1 Ship the model, not the syntax

The single most important idea in the book. Build a core model (the **Semantic Model**) that is fully
usable and testable through an ordinary programmatic interface, and treat every other surface — fluent
builder, config-file loader, CLI, generated client, YAML schema, diagram renderer — as a thin,
second-class front end that merely *populates* that model *(Ch. 1, "Languages and Semantic Model"; Ch. 11)*.
Everything a caller actually values — reuse, reconfiguration without redeployment, multiple execution
targets, testability, docs and diagrams — is a property of the model, not of any surface. Fowler's
attribution discipline follows: whenever you weigh the benefits of a convenience layer, be honest about
which benefits belong to the layer and which to the model underneath; "it's a common mistake to confuse
the two" *(Ch. 2, "Why Use a DSL?")*. Three operational tests:

- The model must be independently usable: a test suite that touches only the plain API must be able to
  exercise everything *(Ch. 11, "When to Use It")*.
- Validation lives in the model, not in any loader or builder, so it applies identically no matter which
  front end produced the objects *(Ch. 11)*.
- If two very different surfaces can both populate the model and produce equivalent populations, the model
  is factored at the right level — multiple front ends are a design test, not just a feature *(Ch. 1)*.

### 16.2 Library design is language design

An API whose methods each make sense alone in an autocomplete list is a *vocabulary* (a command-query
API); an API whose methods only make sense inside a larger call sequence has a *grammar* (a fluent
interface / internal DSL) *(Ch. 2, "Boundaries of DSLs", quoting Mike Roberts)*. The moment your API has a
grammar you owe it language-grade treatment: a defined set of legal compositions, documentation of phrases
rather than words, error messages that talk about phrases, and a deliberate answer to what happens when
the grammar is violated. The most expensive version of this obligation is the accidental one: a
serialization format or config file that users begin hand-editing has become a language "by accident" and
now needs versioning, migration, diagnostics, and a readability budget whether you planned it or not
*(Ch. 2, "Boundaries of DSLs")*.

### 16.3 Extract the seam before you design the surface

Separate the invariant engine (library) from the per-use configuration code *first*; "this separation is
the vital step," worth having before and independently of any fluent surface *(Ch. 2, "DSL Lifecycle")*.
Once the seam exists, every later option — a builder layer, a config format, a plugin API, a generated
client — becomes cheap. Then grow the surface in thin end-to-end slices against real usage scenarios
written the way you wish callers could write them, bending the surface for implementability only with the
consent of the audience it was built for *(Ch. 2, "DSL Lifecycle")*.

### 16.4 Two layers, never mixed

Keep the ergonomic/fluent surface in dedicated builder types (**Expression Builder**) and keep the model's
objects plain, conventional, and inspectable. Never mix fluent and command-query methods on the same class
— each style's conventions make the other's confusing *(Ch. 4, "The Need for a Parsing Layer"; Ch. 32)*.
Inside the fenced-off fluent layer, Fowler explicitly licenses breaking normal API conventions (mutators
returning `this`, query-shaped names that set, deliberately restricted expressiveness, naming bent for the
script reader) — the license is *granted by the fence*: optimize the fluent layer for the reader of the
call site, and pay for it by quarantining it from every object users hold at runtime *(Ch. 35; Ch. 36)*.
The review question: *if a user obtained this object from somewhere other than the fluent chain, would its
interface confuse them?* If yes, the fluent methods are on the wrong class.

### 16.5 Choose call shapes from the grammar of what the caller must supply

Fowler selects among fluent techniques by writing the BNF production a clause must satisfy and reading off
the construct *(Ch. 4, "Using Grammars to Choose Internal Elements"; §10)*. The durable mapping: mandatory,
fixed-shape arguments → function signature / nested calls (the only technique that can *require*);
optional pick-and-choose settings → chained builder methods or keyword arguments; homogeneous repetition →
varargs/lists; heterogeneous unordered attributes → options object / keyword arguments with explicit key
validation; real hierarchy → nesting or child builders, never indentation alone; required *ordering* in a
chain → progressive interfaces (type-state). Each choice leaves an enforcement gap — know which one, and
close it *(Ch. 34; Ch. 35)*.

### 16.6 Limited expressiveness is a feature — police scope relentlessly

"The limited expressiveness of DSLs makes it harder to say wrong things and easier to see when you've made
an error" *(Ch. 2, "Improving Development Productivity")*. A constrained surface bounds the failure
surface, the test matrix, the review burden, and what users can get wrong; a configuration surface does
not have to expose every combination the model supports *(Ch. 36, "Security Codes")*. The corresponding
failure mode is drift toward generality: "today you add conditional expressions, another day you add
loops, and whoops — you're Turing-complete" *(Ch. 2, "Ghetto Language")* — and the same failure afflicts
libraries ("If your product pricing library includes an implementation of the HTTP protocol, you're
suffering from essentially the same failure"). The remedies: question every feature outside the mission;
compose several small focused languages/APIs rather than growing one; and for the long tail of rare needs,
provide a *narrow escape hatch* (Foreign Code — a plugin point, an embedded snippet that is one call into
real code) rather than new core surface *(Ch. 27; Ch. 31, "Modular Grammars")*.

### 16.7 Errors: collect, structure, and layer them

For batch validation of anything — a script, a config, a request payload, a schema — collect *all* the
problems into a **Notification** rather than failing on the first, so users escape the fix-rerun loop
*(Ch. 16)*. Structure messages as data (location, offending value, field path) and render text only at the
edge. Offer both consumption styles: a query for callers who branch, a raiser for callers who want an
exception at their own boundary. Layer responsibility the way Ch. 3 layers error handling: the domain
layer owns invariants and produces semantic errors; the boundary layer initiates validation and enriches
errors with source context (line number, field path); neither duplicates the other *(Ch. 3, "Handling
Errors"; Ch. 16)*. And fail loudly by default everywhere: parsers that silently ignore unrecognized input,
options bags that silently drop misspelled keys, dynamic APIs that swallow unknown names, and generators
whose default error recovery tolerates broken input are all the same bug factory *(Ch. 17; Ch. 40; Ch. 41;
Ch. 23)* — "test with invalid input, not just valid input."

### 16.8 Anything you publish is a published interface

Config schemas, DSL syntax, generated-code shapes, and wire formats are published interfaces the moment
outsiders depend on them. Put a version marker in any format from day one — "it is nearly impossible to
retrofit" — plan migrations as many small steps rather than one big one, consider keeping a compatibility
path that simply continues accepting old input, and keep every script and config under version control
like the code it is *(Ch. 3, "Migrating DSLs"; Ch. 2, "DSL Lifecycle")*.

### 16.9 Magic must pay its way — in tooling survival

Every metaprogramming convenience is judged by whether the abstraction survives into the debugger, the
stack trace, the type checker, and the IDE. Macros fail this test — "abstractions leak like a sieve
without the wires" — which is why Fowler prefers closures for essentially every historical macro use
*(Ch. 15)*. Dynamic Reception (method_missing / `__getattr__` / Proxy) passes only when the mapping is
fully general with no special cases, unknown names still reach the default error path, and you budget for
the impenetrable stack traces users will debug through *(Ch. 41)*. Parse Tree Manipulation (inspecting
lambdas instead of calling them) demands loud, specific failures on the unsupported subset of the host
language *(Ch. 43)*. Two supporting rules: prefer structural fixes to textual ones (Textual Polishing is
the last resort, and a growing pile of rewrite regexes means you need a real parser) *(Ch. 45)*; and scope
extensions to types you don't own — opt-in, locally visible, never global, and never bolt DSL vocabulary
onto general-purpose types *(Ch. 46)*.

### 16.10 Declarative surfaces owe an explanation mechanism

When you move behavior out of imperative code into a model — rules, state machines, dependency networks,
decision tables, any config-driven framework — you trade away the debuggability imperative code gives for
free (stepping, stack traces, print statements). That trade is often right, but it creates an obligation:
ship a tracing/explain facility ("why did this rule fire?", "why was this state entered?") and ideally a
dump/visualize facility for the assembled configuration *(Ch. 47, "Adaptive Model"; Ch. 50)*. Fowler's
sociological warning belongs here too: adaptive models concentrate understanding in a few heads and read
as scary magic to everyone else — weigh maintainer bus-factor, not just expressiveness *(Ch. 47)*.

### 16.11 Generated SDKs: thin generated layer, fat handwritten runtime, never hand-edited

The architecture of a good generated client SDK, assembled from Part VI of the book: put all invariant
logic (transport, auth, retry, serialization, pagination, error mapping) in a handwritten, versioned
runtime library; generate only the thin declarative layer that describes the spec (endpoint descriptors,
model types, method stubs calling the shared pipeline) — **Model-Aware Generation** *(Ch. 55)*; "generate
as little code as possible" *(Ch. 57)*. Give the runtime a small, stable population API — that API is the
contract between generator and runtime, and its encapsulation is a *versioning* property: the runtime can
be patched without regenerating anything *(Ch. 55)*. Let users customize via **Generation Gap**: generated
code in classes/files that are never hand-edited, user extensions in subclasses (or the idiomatic
per-language equivalent), and always emit the concrete user-facing class even when empty, so customizing
later is never a breaking rename *(Ch. 57)*. Generated output is read constantly during debugging, so
optimize it for readability and debuggability — not modifiability — with provenance comments pointing back
at the model *(Ch. 8, "Generating Readable Code")*. Reserve **Model Ignorant Generation** (fully inlined,
zero-dependency output) for targets that cannot host a runtime, and accept its cost: every fix must be
regenerated and redistributed to all consumers *(Ch. 56)*.

### 16.12 Let types and tooling enforce the grammar

Where the host language has a type system, spend it: **progressive interfaces** make illegal call
sequences fail at compile time and turn autocompletion into documentation — the user is shown only what is
legal next *(Ch. 35, "Progressive Interfaces"; Ch. 10, JMock)*. Turn stringly-typed identifiers into
declared, typed symbols (enums, literal unions, generated constants — **Class Symbol Table** in spirit) to
buy completion, safe rename, and compile-time checking; generate those constants from the authoritative
source to keep them honest *(Ch. 44; Ch. 4, "Providing Some Type Checking")*. The tradeoff is stated, not
assumed: if your users have no tooling that exploits the types, the restrictions remain and the benefits
evaporate — don't pay *(Ch. 44, "When to Use It")*.

## 17. Decision guides

### 17.1 Should you build a DSL / fluent layer at all?

The decision rule: build it only if you can name which benefit you are buying and it is worth the cost
*(Ch. 2, "Problems with DSLs")*. The four benefits on offer: (1) clearer intent at the call site /
improved productivity; (2) domain experts who can *read* the artifact (the COBOL fallacy warns against
expecting them to write it; read-first is the low-risk adoption path); (3) execution in a context the host
language can't reach (runtime config, generating SQL/C for another environment); (4) an alternative
computational model made programmable *(Ch. 2, "Why Use a DSL?")*. If a plain command-query API already
serves, an extra surface has negative value. "Not every library benefits from having a DSL wrapper over
it" *(Ch. 2, "Cost of Building")*. And remember the alternative that is often sufficient: if the only goal
is domain-expert comprehension, a generated, read-only *visualization* of the model may beat a language
*(Ch. 2, "Communication with Domain Experts")*.

### 17.2 Internal or external?

Ten factors, no universal verdict *(Ch. 6)* — but the two that most often decide it: **tooling** (an
internal surface inherits the entire IDE: completion, refactoring, type errors — frequently worth more
than syntactic elegance) and **boundary strength** (an external, restricted format bounds the failure
surface and sandboxes untrusted or non-programmer authors; it also cannot silently slide into
general-purpose code). Internal is cheaper to build and familiar to programmers; external buys syntactic
freedom, runtime reconfiguration, and a stronger wall against host-language leakage. Push toward external
when domain experts must read the artifact and host-language noise would spoil it; push toward internal
when programmers are the audience and the IDE matters *(Ch. 6, all sections)*.

### 17.3 Which fluent technique?

Full treatment and tables in §10 ("Choosing among the fluent techniques"). The compressed sequence: start
with an Expression Builder holding the fluent layer; the DSL must open with at least one plain call
(Function Sequence) to establish context; below the top level, prefer Nested Function for
mandatory/fixed/hierarchical shapes, Method Chaining for optional pick-and-choose clauses (adding
progressive interfaces when order or requirement must be enforced), Literal Map/keyword arguments for many
optional heterogeneous attributes, Object Scoping to give bare vocabulary a home without globals, and
Nested Closure when you need control over evaluation time, setup/teardown bracketing, or you are drowning
in Context Variables. The context-carrying maturity ladder — globals → instance fields → return values →
lexically scoped blocks — is the direction of improvement. When you find yourself designing `.end()` or
`.build()`, check whether an enclosing-call form (nested function/closure) would eliminate the finishing
problem instead.

### 17.4 Which parsing strategy?

Full comparison table and tripwires in §12.8. Compressed: Delimiter-Directed only for genuinely simple
autonomous line formats; Recursive Descent as the simplest real parser (≤1 symbol look-ahead, no left
recursion); Parser Combinator as the composable middle ground; Parser Generator when the grammar is
complex or ambiguous, when you need mature error handling, or when you want the explicit grammar artifact
most — accepting the build-step "irritant." The checkable tripwires: ad-hoc line processing that starts
wanting a framework → syntax-directed; >1 symbol look-ahead or genuine ambiguity → generator; left
recursion / operator expressions → not top-down; the language is regular → the lexer may be the whole
parser; you need a semantic predicate for a DSL you control → redesign the DSL.

### 17.5 Which output strategy?

Full table in §13.4. Compressed: default to producing a Semantic Model. Use Embedded Translation (populate
the model in one pass during parsing) for simple languages where one pass suffices; switch to Tree
Construction (build an AST, then walk it) the moment transformation complexity, forward references,
multiple passes, or side-effect tangles appear — "two simple transformations rather than one complicated
one." Reserve Embedded Interpretation (compute the answer during the parse, no representation) for small
expression evaluators where the syntax tree would *be* the model anyway.

### 17.6 Code generation decisions

Three orthogonal choices *(Ch. 8; §15)*: **Whether** — generate only when the execution environment can't
host your runtime (different language/platform) or when static artifacts buy tooling and checking (typed
clients: spec drift becomes compile errors); otherwise interpret the model directly and skip the build
complexity. **How** — Templated Generation when output is mostly static boilerplate you can visualize by
reading the template; Transformer Generation when output is mostly synthesized structure; keep any logic
in templates to single calls into an Embedment Helper, never inline *(Ch. 53; Ch. 54)*. **What** —
Model-Aware target code (generate configuration data consumed by handwritten generic code) as much as
possible; Model-Ignorant (inline everything) only when the target can't hold the runtime; mix generated
and handwritten code via Generation Gap with one-way call direction and no hand edits ever *(Ch. 55–57;
Ch. 8, "Mixing Generated and Handwritten Code")*.

### 17.7 Fail fast, or collect?

Throw immediately on programmer errors against invariants deep in the model (fail fast keeps the defect
near its cause). Collect into a Notification when validating user-supplied batch input — scripts, configs,
documents, payloads — where the author needs the full list of problems in one pass; report through the
layered initiation/detection/reporting split so lower layers never touch presentation *(Ch. 16; Ch. 3,
"Handling Errors")*.

### 17.8 When to reach for an alternative computational model

When the domain's natural mental model is not a sequence of steps but a table (Decision Table — with
completeness checking as a genuine API feature), a graph of prerequisites (Dependency Network — with the
"everything affecting output must be declared" correctness contract), a set of condition-action rules
(Production Rule System — keeping user intent as first-class model objects, never collapsed into opaque
closures at the builder boundary), or states and transitions (State Machine — exposing derived rather than
stored status where possible) *(Ch. 7; Ch. 47–51)*. The price of admission is §16.10's explain facility.
Don't over-model: "you don't need the model to be manifest in the software" — a guard clause is sometimes
the whole benefit; build the explicit model when behavior must be configurable, inspectable, or generated
*(Ch. 51)*.

## 18. Warnings index — the mistakes the book names

- **Confusing model benefits with DSL benefits** when justifying work *(Ch. 2)*.
- **The COBOL fallacy**: expecting non-programmers to write, rather than read, the language *(Ch. 2)*.
- **DSL-by-accident**: a serialization format users hand-edit is now a language without language-grade
  support *(Ch. 2)*.
- **Ghetto language / Turing drift**: incremental growth into a bad general-purpose language; applies
  equally to libraries growing past their mission *(Ch. 2)*.
- **Blinkered abstraction**: spending effort fitting the world to your abstraction instead of evolving it;
  worsens once a comfortable DSL surface exists over it *(Ch. 2)*.
- **Imitating natural language**: AppleScript-style prose syntax adds sugar that obscures semantics —
  target terse and precise, not prose-like *(Ch. 2, "What Makes a Good DSL Design?")*.
- **Skipping the Semantic Model** and parsing straight into generated code — acceptable only for the very
  simplest cases *(Ch. 1; Ch. 8)*.
- **Macros**: textual or syntactic generation whose abstractions vanish from every downstream tool; prefer
  closures *(Ch. 15)*.
- **Static/global parse state** and accumulating Context Variables: order-dependence, thread hazards,
  runtime dispatch on hidden state *(Ch. 13; Ch. 33)*.
- **Chaining on domain objects** users hold at runtime; fluent conventions leaking out of the builder
  fence *(Ch. 35)*.
- **The unguarded options bag**: unvalidated string keys where typos fail silently *(Ch. 40)*.
- **Special-cased magic**: Dynamic Reception with per-name conditionals means define real methods; unknown
  names must reach the error path, never a silent no-op *(Ch. 41)*.
- **Technique attraction**: adopting the intricate mechanism because it is elegant — "can blindside people
  into missing other, simpler ways" *(Ch. 43; Ch. 46)*.
- **Silent tolerance**: parsers/loaders whose default recovery accepts broken input; passing tests on valid
  input proving nothing — "all it indicates is that the parser didn't blow up" *(Ch. 23)*.
- **Hand-edited generated code** and marked-region mixing: edits lost on regeneration, unreviewable diffs
  *(Ch. 8; Ch. 57)*.
- **Logic inlined in declarative artifacts** (grammars, templates, configs): untestable, unreadable — a
  single named call into real code is the ceiling *(Ch. 54; Ch. 27)*.
- **Adaptive-model priesthood**: config-driven magic only its authors understand, shipped without tracing
  or visualization *(Ch. 47)*.

## 19. Master pattern quick-reference

| Pattern (Ch.) | One-line intent | Modern SDK analog |
|---|---|---|
| Semantic Model (11) | The library the DSL populates; the meaning lives here | Core library independent of every API surface |
| Symbol Table (12) | Resolve names to objects during processing | Registries; lazy create-on-reference; typed identifiers |
| Context Variable (13) | Carry "the current object" through processing | Stateful "current" fields — treat as a smell to refactor away |
| Construction Builder (14) | Mutable staging object for an immutable product | Builder types with lifecycle enforcement at `build()` |
| Macro (15) | Textual/syntactic expansion before processing | Avoid; use closures/higher-order functions |
| Notification (16) | Accumulate errors instead of failing fast | Validation result objects; collected diagnostics |
| Delimiter-Directed Translation (17) | Split input on delimiters, process chunks | Line-oriented config parsing |
| Syntax-Directed Translation (18) | Parse via a formal grammar pipeline | Lexer → parser → actions layering |
| BNF (19) | Formal grammar as design artifact | Thinking/communication tool; IDL-first design |
| Regex Table Lexer (20) | Ordered regex table produces tokens | Tokenizers; first-match-wins registries |
| Recursive Descent Parser (21) | Hand-written function-per-rule parser | Hand-rolled parsing with stated complexity tripwires |
| Parser Combinator (22) | Compose parsers from parser values | The archetype of composable API design |
| Parser Generator (23) | Generate the parser from a grammar DSL | ANTLR-class tooling; keep grammar actions thin |
| Tree Construction (24) | Parse to AST, then walk it | Wire format → IR → domain objects |
| Embedded Translation (25) | Populate the model during the parse | Single-pass loaders (until forward references bite) |
| Embedded Interpretation (26) | Compute the result during the parse | One-shot expression evaluators |
| Foreign Code (27) | Escape hatch: host-language snippets in the DSL | Plugin points; keep the hatch narrow, store opaquely |
| Alternative Tokenization (28) | Locally change what counts as a token | Raw blocks, embedded sub-languages, round-trip fidelity |
| Nested Operator Expression (29) | Parse precedence/associativity in expressions | User-facing expression syntax; document total precedence |
| Newline Separators (30) | Line ends as statement separators | Line-based formats; normalize input at the boundary |
| Syntactic Indentation / Modular Grammars (31) | Whitespace structure; composing grammars | Indent formats' hidden cost; global layers block composition |
| Expression Builder (32) | Fluent facade over the command-query model | The separate builder layer — the SDK keystone |
| Function Sequence (33) | Statements as successive calls | Imperative config sequences; refuse global state |
| Nested Function (34) | Arguments composed as nested calls | Constructors/options-objects; the only "required" enforcer |
| Method Chaining (35) | Calls chained on returned builders | Chained builders; type-state via progressive interfaces |
| Object Scoping (36) | Host bare vocabulary inside an instance scope | Config blocks; subclass-extensible DSL bases |
| Closure (37) | Pass behavior as first-class blocks | Callbacks; execute-around; deferred evaluation |
| Nested Closure (38) | Structure expressions via nested blocks | Block/context-manager APIs; receiver lambdas |
| Literal List (39) | Language list literals / varargs as syntax | Variadic parameters for homogeneous "zero or more" |
| Literal Map (40) | Map literals as named optional arguments | Options objects/kwargs — validate keys loudly |
| Dynamic Reception (41) | Intercept undefined method calls | `__getattr__`/Proxy magic — only for open vocabularies |
| Annotation (42) | Declarative metadata attached to code elements | Decorators/attributes; one declaration, N processors |
| Parse Tree Manipulation (43) | Inspect host code instead of running it | LINQ-style lambda translation; fail loudly off-subset |
| Class Symbol Table (44) | Typed fields as the DSL's symbol table | Typed schema classes; strings → typed symbols |
| Textual Polishing (45) | Regex-preprocess before real parsing | Source rewriting — last resort; prefer structural fixes |
| Literal Extension (46) | Add methods to types you don't own | Extension methods — opt-in, namespace-scoped only |
| Adaptive Model (47) | Behavior from a user-assembled structure | Config-driven frameworks; must ship explain/trace |
| Decision Table (48) | Condition/action matrix | Policy matrices with completeness checking |
| Dependency Network (49) | Compute from declared prerequisites | Build/pipeline/caching engines; declare all inputs |
| Production Rule System (50) | Independent condition→action rules | Rule/validation engines; intent stays introspectable |
| State Machine (51) | States, events, transitions as a model | Lifecycle APIs; workflow engines; derived status |
| Transformer Generation (52) | Code that walks input and emits output | Spec-driven generators; IR for multi-language output |
| Templated Generation (53) | Output template with interpolated callouts | Scaffolds and boilerplate-heavy generated files |
| Embedment Helper (54) | One object holding all a template's logic | Keep logic out of templates/grammars — single calls only |
| Model-Aware Generation (55) | Generated code populates a runtime model | Thin generated layer + fat handwritten runtime |
| Model Ignorant Generation (56) | Fully inlined generated code, no runtime | Zero-dependency generated artifacts |
| Generation Gap (57) | Inherit handwritten classes from generated ones | User customization of generated SDKs without hand edits |

