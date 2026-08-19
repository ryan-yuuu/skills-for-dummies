# Study Notes — Fowler, *Domain-Specific Languages* (2010), Part III "External DSL Topics", Chapters 24–31

Source: Martin Fowler with Rebecca Parsons, *Domain-Specific Languages*, Addison-Wesley 2010.
PDF read: pages 202–242 (Ch. 24 starts at the bottom of PDF p. 202; Ch. 31 ends and Part IV's TOC begins on PDF p. 242; Ch. 32 "Expression Builder" starts PDF p. 243).

Chapter → PDF page map (as found):

| Chapter | Title | PDF pages |
|---|---|---|
| 24 | Tree Construction | 202–214 |
| 25 | Embedded Translation | 215–218 |
| 26 | Embedded Interpretation | 219–221 (top) |
| 27 | Foreign Code | 221–228 (top) |
| 28 | Alternative Tokenization | 228–234 |
| 29 | Nested Operator Expression | 234–238 |
| 30 | Newline Separators | 238–240 |
| 31 | External DSL Miscellany | 240–242 |

---

## Orientation: where these chapters sit

Chapters 24–26 are the three **output-production strategies** available once you've decided to use a parser (Syntax-Directed Translation). A parser on its own only *recognizes* structure; something has to actually produce a result. The three options are:

1. **Tree Construction** (Ch. 24) — parser builds an AST; a separate tree-walk populates the Semantic Model. Two passes, two simple transformations.
2. **Embedded Translation** (Ch. 25) — parser actions populate the Semantic Model directly during the parse. One pass, one transformation.
3. **Embedded Interpretation** (Ch. 26) — parser actions compute the *answer* directly during the parse. No Semantic Model at all.

Chapters 27–30 are supporting tactics and problems: escaping the DSL into another language (Foreign Code), bending the lexer from the parser (Alternative Tokenization), the perennial arithmetic-expression problem (Nested Operator Expression), and the surprisingly fiddly business of using newlines as separators. Chapter 31 collects two unfinished topics: syntactic indentation and modular grammars.

The through-line: **the Semantic Model is the centre of gravity**, and everything in these chapters is judged by whether it keeps the grammar clean and the model-population code understandable.

---

## Chapter 24: Tree Construction

**Intent (Fowler's one-liner):** "The parser creates and returns a syntax tree representation of the source text that is manipulated later by tree-walking code." (Fowler, DSL book, Ch. 24 "Tree Construction", intent)

### The concept

Any Syntax-Directed Translation parser already builds a syntax tree implicitly while parsing — it grows on the parse stack and gets pruned as each rule completes. Tree Construction says: don't throw that structure away. Add parser actions that assemble an explicit tree *in memory* as the parse proceeds. When the parse completes you hold a whole tree representing the script, and you can then walk it — as many times as you like — to do whatever you want, most commonly to populate a Semantic Model.

The critical refinement is that the in-memory tree **should not** be a faithful parse tree. It should be an **abstract syntax tree (AST)**: a deliberate simplification tuned to how you intend to use it.

Fowler's terminology (Fowler, DSL book, Ch. 24, "How It Works"):
- *syntax tree* — the general term for any hierarchic data structure formed by parsing input.
- *parse tree* — a syntax tree that corresponds directly to the input text.
- *AST* — a syntax tree that makes simplifications of the input based on usage.

His worked illustration: for input like an `events … end` block, the parse tree contains nodes for the literal `events` and `end` keywords. Those words earned their keep during lexing — they marked the boundaries of the declaration — but once the structure exists as a tree they are pure clutter. The AST drops them. And the AST is *purpose-relative*: if all you needed were the event codes, you'd drop the names and the per-event nodes too. "Obviously, different ASTs might be needed for different reasons" (Fowler, DSL book, Ch. 24, "How It Works").

### How it works (mechanics, no code)

Two mechanisms for building the tree:

1. **Code actions in the BNF.** Each grammar rule carries an action that constructs the node for that rule and attaches the nodes returned by its subrules. The ability of code actions to *return a value* is what makes this workable — each action assembles the representation of its own node and hands it upward. Fowler notes the resulting grammar-file code is "very regular—indeed rather boring" — and offers the maxim that **boring code usually means you need another abstraction** (Fowler, DSL book, Ch. 24, "Tree Construction Using Code Actions").

2. **A tree-construction DSL supplied by the Parser Generator.** ANTLR provides a rewrite notation where a rule declares the shape of the tree node it should produce: a node type followed by the child nodes. This "greatly simplifies building up an AST" and is exactly the missing abstraction the boring code was pointing at. Parser generators with this feature typically hand you the raw parse tree if you supply no rewrite rules — "but you almost never want the parse tree" (Fowler, DSL book, Ch. 24, "How It Works").

A tree built this way consists of **generic** nodes — a node type plus generic tokens as children — not domain objects. You *could* have the code actions construct real domain objects directly (a true Event object with name and code fields), but Fowler explicitly prefers not to:

> "I prefer to have a generic AST and then use second-stage processing to transform that into a Semantic Model. I'd rather have two simple transformations than one complicated one." (Fowler, DSL book, Ch. 24, "How It Works")

The second stage, in his state-machine example, runs in three phases: build the AST; walk it to build **Symbol Tables** (maps of events, commands, states by name); then walk it again to assemble the Semantic Model, resolving names through the symbol tables. The AST node class gets a few convenience query methods (get children of a type, get the sole child of a type, get the text of a child of a type) — Fowler observes this "feels rather like a dictionary lookup but using the same tree data structure" (Fowler, DSL book, Ch. 24, "Populating the Semantic Model").

### When to use it — the central tradeoff

Tree Construction and **Embedded Translation** are the two ways to populate a Semantic Model while parsing. Embedded Translation does the transformation in a single step; Tree Construction does it in two, with the AST as an intermediate model.

Fowler's decision factors (Fowler, DSL book, Ch. 24, "When to Use It"):

- **Complexity of the transformation.** The argument for Tree Construction is that it splits one transformation into two simpler ones. Whether that's worth the intermediate model depends entirely on how complex the transformation is. "The more complex the transformation is, the more useful an intermediate model can be."
- **Multiple passes.** This is the big one. If you need several passes over the script — most commonly because of **forward references** (a transition naming a state declared later) — Tree Construction wins easily. "With Tree Construction it's easy to walk the tree many times as part of later processing." Embedded Translation is stuck with a single pass and must resort to find-or-create tricks and context variables.
- **Parser Generator support.** Some generators give you no choice — you must use Tree Construction. Most let you choose; but if the generator makes AST building really easy, that tips the balance toward Tree Construction.
- **Memory.** Tree Construction uses more memory because it stores the AST. "In most cases, however, this won't make any appreciable difference. (Although that certainly used to be a big factor in earlier days.)"
- **Reuse.** You can process the same AST several ways to populate different Semantic Models, reusing the parser. Handy — but if tree construction is cheap it may be simpler to build different ASTs for different purposes. Alternatively, transform to a single Semantic Model and use *that* as the basis for further transformations.
- **Side-effect safety** (argued from the other side in Ch. 25): Tree Construction only produces a subtree return value, so it doesn't suffer the "action fired at an unexpected moment" problem that side-effecting embedded actions have.

### Design principles picked up from the worked example

These come from the tokenizing/parsing discussion in the ANTLR example and generalize well beyond ANTLR (Fowler, DSL book, Ch. 24, "Tokenizing" and "Parsing"):

- **Push ambiguity to the layer that has context.** In his state-machine DSL, event *names* and event *codes* have different lexical shapes (codes are exactly four uppercase letters), so you *could* write two lexer rules. But a string like `ABC1` is legal as both. The lexer has no context; the parser does. So use **one token type for both and let the parser sort it out**. Consequence, stated plainly: the parser will not catch a five-letter code — that check moves into your own semantic processing. This is a deliberate, acknowledged trade, not an accident.
- **Keywords as literals in parser rules** (rather than named lexer rules) is generally easier to read.
- **Don't add statement separators until you need them.** His state-machine grammar skips *all* whitespace including newlines, so the script can be formatted freely, and it has no statement separators at all. "Often, DSLs can get away with no statement separators because the statements are very limited." Infix expressions force the issue; most DSLs don't. "As with most things, don't put them in until you actually need them."
- **Skipping whitespace loses your line and column numbers.** Good error reports need them. ANTLR's solution is a *hidden channel*: whitespace tokens are emitted on a separate channel so they're available for error handling but invisible to the parsing rules. The general lesson: **discarded input is still needed for diagnostics — route it somewhere rather than dropping it.**
- **Keep tree-construction rules simple and the tree easy to walk.** His stated aim each time is "collecting together appropriate clumps of the DSL and putting them under a node that describes what that clump represents." The AST ends up close to, but not identical with, the parse tree.

### Relationships

- Alternative to **Embedded Translation** (Ch. 25) and **Embedded Interpretation** (Ch. 26).
- Populates a **Semantic Model**; typically via **Symbol Tables** for name resolution.
- Uses **Foreign Code** (Ch. 27) when built with code actions; the tree-construction DSL is the cleaner alternative.
- **Embedment Helper** normally keeps the grammar file thin — but Fowler skips it when tree-building code actions are so simple that a helper wouldn't be easier to read.
- Ch. 29 notes that Tree Construction "often reduces" the code-action mangling that Nested Operator Expression grammars suffer.

### SDK relevance

- **Two simple transformations beat one complicated one.** This is the single most transferable idea in the chapter. In SDK terms: wire format → normalized intermediate representation → domain object, rather than deserializing straight into rich domain types. Each stage is independently testable, and the intermediate representation gives you a place to stand for validation, diagnostics, and multiple back ends.
- **A generic intermediate representation buys you re-targeting.** One parse, many outputs (validator, formatter, doc generator, executor). Same argument as an IR in a compiler or a `Document`/`Node` tree in a markup library.
- **Multi-pass resolution is the answer to forward references.** If your builder/config API lets users reference things declared later, you need a collect-then-link design (build all nodes, then resolve), not a single streaming pass. Design this in early; retrofitting it is painful.
- **Boring, highly regular glue code is a missing abstraction.** If every method in a layer looks the same modulo a name, generate it or introduce the declarative form.
- **Preserve source positions even for tokens you discard.** Users judge a parser/validator by its error messages.

---

## Chapter 25: Embedded Translation

**Intent:** "Embed output production code into the parser, so that the output is produced gradually as the parse runs." (Fowler, DSL book, Ch. 25 "Embedded Translation", intent)

### The concept

A pure parser only builds an internal parse tree and throws it away; something more is needed to get a **Semantic Model** out. Embedded Translation puts the model-population code *inside* the parser: as each clause of the input language is recognized, an action fires that creates or updates the corresponding Semantic Model objects. By the time the parse finishes, the model is built. One pass, no intermediate tree.

### How it works

- Model-population code is attached at the points in the grammar where language clauses are recognized. "Most of the time, this implies that the model population code is placed where a clause of the input language is recognized, although in practice you may place hunks of population code at various points" (Fowler, DSL book, Ch. 25, "How It Works").
- With a Parser Generator, this population code is **Foreign Code** woven into the grammar file. Nearly all parser generators support it; the exception Fowler mentions is one intended to be used with Tree Construction.
- **The side-effect hazard.** Actions with side effects "can often be executed in unexpected places, depending on exactly how rules are recognized by the parsing algorithm." Because the parser may backtrack, re-order, or reach a rule via an unexpected path, an action that mutates shared state can fire at a moment you didn't intend. Tree Construction is immune because its actions only return a subtree. Fowler's rule of thumb: **"If you find yourself getting into a tangle with Embedded Translation side effects, that's a sign that you should switch to Tree Construction."** (Fowler, DSL book, Ch. 25, "How It Works")

Two structural problems the worked example exposes (Fowler, DSL book, Ch. 25, "Miss Grant's Controller"):

**1. Hierarchic context.** An action nested inside a state definition (say, recognizing an action list) needs to know *which* state it belongs to. Fowler warns against the mental model of "Embedded Translation is like SAX processing of XML" — it's "somewhat true, in that the embedded code just works with one rule at a time. But it's also misleading, because Parser Generators can give you much more context during the execution of the code so you don't need to keep it around yourself." Concretely, ANTLR lets you pass parameters *into* rules, pushing the enclosing context down to nested rules. **Prefer parameter passing to a Context Variable.**

**2. Forward references.** Transitions name states not yet declared. In many DSLs you can arrange the language so nothing refers to an identifier that hasn't been declared yet — but a state model can't do that. Tree Construction solves it with multiple passes. Embedded Translation has no such option, so the fix is an **"obtain" (find-or-create) operation** applied to *both* references and declarations: mentioning a state implicitly declares it if it doesn't already exist.
   - Consequence: a misspelled state name silently produces a blank state as the transition target. You can accept that; but "It's common, however, to check declarations against usage, in which case we need to keep track of the states created by use and ensure that they are all declared too."
   - Some context the parser generator handles badly regardless — e.g. "the start state is the first state mentioned" required "what is effectively a context variable."
   - Reset events can appear before any state exists, so before there's a machine to attach them to: they're accumulated in a field and applied after the parse. Fowler notes that post-parse cleanup code following syntactic analysis is normal — and it's also where **semantic analysis** naturally lives.

### When to use it

(Fowler, DSL book, Ch. 25, "When to Use It")

**For:**
- "The biggest appeal of Embedded Translation is that it provides a simple way to handle both syntactic analysis and model population in one pass." With Tree Construction you write both tree-building code *and* a tree-walking populator. "Particularly for simple cases, which many DSLs are, this two-stage process can be more trouble than it's worth."

**Against:**
- **It encourages complex grammar files**, "usually due to a poor use of Foreign Code." Discipline with Foreign Code (i.e. **Embedment Helper**) mitigates this — "but a strength of Tree Construction is that it helps to enforce the discipline." That is: Tree Construction makes the good structure the default; Embedded Translation makes it a matter of willpower.
- **Single-pass only** ⇒ forward references are tricky, often requiring **Context Variable**, "which can further complicate parsing."
- Parser Generator tree-building support pushes the other way: "The better the tree-building features of your Parser Generator the more appealing Tree Construction becomes."

**The summary rule:** "The upshot of all this is that the simpler the language and parser, the more appealing is Embedded Translation."

### Notable observation on grammar stability

"Most of the time, the BNF rules don't vary if you use different parsing patterns; what changes is the supporting code around the BNF." (Fowler, DSL book, Ch. 25, "Miss Grant's Controller") — i.e. **the grammar is the stable asset; the output-production strategy is a swappable layer on top of it.** That's why he can present the same DSL three ways with the same core rules.

### Relationships

- Direct alternative to **Tree Construction** (Ch. 24).
- Depends on **Foreign Code** (Ch. 27) as the embedding mechanism, and on **Embedment Helper** to keep that Foreign Code to a single call per action: "Since I'm using an Embedment Helper, all I do is call a single method on that helper."
- Needs **Context Variable** where the parser generator can't supply the context.
- **Symbol Tables** still appear (a collection of dictionaries on the loader), built incrementally instead of in a dedicated pass.

### SDK relevance

- **Streaming/one-pass APIs trade simplicity for expressiveness.** A SAX-style or event-callback API is cheap and fast, but every cross-cutting relationship becomes hidden mutable state in the consumer. If your format has forward references or hierarchic context, a document/tree API will serve users better.
- **Find-or-create ("obtain") is the standard trick for forward references in one-pass builders** — and it comes with the standard cost: typos become silently-created empty objects. If you use it, add a "declared vs merely referenced" audit at the end. This applies directly to config loaders, ORM/session identity maps, DI containers, and IaC-style resource graphs.
- **Push context down as explicit parameters rather than parking it in shared mutable state.** Fowler's parameterized-rule technique is the parser equivalent of threading a context object through calls instead of using a thread-local or an instance field.
- **Callbacks with side effects can fire at surprising times.** If your API invokes user callbacks from inside a speculative or backtracking process, document it or restructure so callbacks return values instead of mutating.

---

## Chapter 26: Embedded Interpretation

**Intent:** "Embed interpreter actions into the grammar, so that executing the parser causes the text to be directly interpreted to produce the response." (Fowler, DSL book, Ch. 26 "Embedded Interpretation", intent)

### The concept

Sometimes you don't want a model at all — you want an *answer*. Run the script, get the number. Embedded Interpretation interprets the DSL script *during* parsing: the result of the parse *is* the result of the script. Fowler's sketch is `1 + 2 * 3` collapsing to `6` then `7` as the parse proceeds.

### How it works

"Embedded Interpretation works by evaluating DSL expressions as soon as possible, collating results together, and returning the overall result." (Fowler, DSL book, Ch. 26, "How It Works") No **Semantic Model** is built; the interpretation happens directly on the DSL input. As the parse recognizes each fragment it interprets as much as it can, and each grammar rule's action combines the values returned by its subrules.

In the calculator example, each grammar rule recognizes one operator and its embedded code performs the corresponding arithmetic on the sub-results, propagating a typed return value up the rule hierarchy.

### When to use it

(Fowler, DSL book, Ch. 26, "When to Use It")

Fowler is unusually blunt here — this is the pattern he least recommends:

- "I'm a big proponent of a Semantic Model, so I don't usually favor Embedded Interpretation—it is useful when you have relatively small expressions that you just want to evaluate and run."
- "Sometimes, building a Semantic Model just isn't worth the overhead. But I find this is a rare case; even a relatively small DSL is usually simpler to deal with by creating a Semantic Model and interpreting that, rather than trying to do everything in the parser."
- The clinching argument: **"a Semantic Model provides a stronger foundation if the language grows."** The cost of Embedded Interpretation is not paid today, it's paid the first time the language needs a feature that requires looking at more than one fragment at a time.

The one case where it's genuinely a good fit is the calculator: "A calculator is perhaps the best example case for Embedded Interpretation. It's easy to interpret each expression and compose the results together. It's also a case where the syntax tree for arithmetic is a perfectly good Semantic Model, so there's no gain in trying to create the usual Semantic Model that I prefer." — i.e. **use it when the syntax tree already is the domain model.**

### The most important paragraph in the chapter (a critique of the standard teaching example)

> "Arithmetic expressions are a common choice for illustrating how to use a parser; many articles and papers use some form of calculator example. But I don't think this is very representative of what you have to deal with when working with a DSL. The big problem with using arithmetic expressions as examples is that they force you to deal with a rare problem (Nested Operator Expression) but avoid the common DSL-related problems that encourage the use of Semantic Model and Embedment Helper." (Fowler, DSL book, Ch. 26, end of "A Calculator")

This is a methodological warning worth carrying beyond DSLs: **the canonical tutorial example teaches the rare problem and hides the common ones.** The calculator is so simple he doesn't even need an Embedment Helper — which is precisely why it misleads people about what real DSL work involves.

### Relationships

- Third alternative to **Tree Construction** and **Embedded Translation**.
- Necessarily entangled with **Nested Operator Expression** (Ch. 29) in the calculator case, and with the top-down/bottom-up parser distinction.
- Deliberately *skips* **Semantic Model** — which is the whole argument against it.

### SDK relevance

- **Eager evaluation with no intermediate representation is the "just give me the answer" API.** It's the right shape for a one-shot evaluator (a template expression, a filter predicate, a units conversion), and the wrong shape for anything you'll later want to inspect, cache, optimize, serialize, explain, or partially evaluate.
- **Ask whether your syntax tree already *is* your domain model.** If it is, an extra model layer is ceremony. If it isn't (and for most real domains it isn't), you'll want the model.
- **"A stronger foundation if the language grows"** is the general argument for keeping a representation layer in an API even when today's use case doesn't need it — but note Fowler only makes this argument because the cost is small, not as a blanket "always add a layer."

---

## Chapter 27: Foreign Code

**Intent:** "Embed some foreign code into an external DSL to provide more elaborate behavior than can be specified in the DSL." (Fowler, DSL book, Ch. 27 "Foreign Code", intent)

Sketch: `scott handles floor_wax in MA RI CT when {/^Baker/.test(lead.name)};` — a small DSL sentence with a JavaScript predicate embedded in the braces.

### The concept

A DSL is, by definition, a limited language that only does a few things. Sooner or later a script needs to say something beyond what the DSL can express. There are two responses: extend the DSL, or open an escape hatch to another language. "One solution may be to extend the DSL to handle this capability, but taking this path may significantly complicate the DSL, removing much of the simplicity that makes it appealing." (Fowler, DSL book, Ch. 27, opening) Foreign Code is the escape hatch — a different language, usually a general-purpose one, embedded at designated places in the DSL.

### How it works — two questions

**Question 1: How do we recognize the foreign pieces and weave them into the grammar?**

- Foreign Code only appears in specific places, so the grammar marks the spots where it can occur.
- The wrinkle: **your grammar cannot recognize the internal structure of the foreign code.** Consequently you usually need **Alternative Tokenization** (Ch. 28) to read the whole foreign fragment into the parser as one long string.
- Then you either (a) embed that raw string in the **Semantic Model** as-is, or (b) hand it to a separate parser for the foreign language so you can weave it more intimately into the model. Option (b) "is more involved—it's something you'd only consider if your Foreign Code is another DSL. Often, the Foreign Code is a general-purpose language, in which case the pure string is usually enough."
- In the example he explicitly declines to parse the JavaScript: parsing would only catch *syntactic* errors, not semantic ones, so "I don't think it's worth the trouble."

**Question 2: How do we execute it?**

"The biggest issue lies in whether the Foreign Code can be interpreted or needs to be compiled."

- **Interpreted foreign code is easiest**, provided you have a mechanism for the interpreter to interoperate with the host language. If the host language is itself interpreted, you can just use the host language as the foreign language. If the host is compiled, you need an interpreted language callable from the host with some data transfer. Static language environments increasingly support this — "It's usually a bit fiddly, especially when it comes to moving data around. It also might involve introducing another language to the project, which can sometimes be an issue."
- **Embedding the host (compiled) language** introduces an extra compilation step into the build, exactly like code generation. If you're already generating code you're paying that cost anyway, so compiled Foreign Code adds nothing. "The complexity matters if you're compiling code while interpreting the Semantic Model." — i.e. it's the *mixed* mode (interpreted model + compiled fragments) that hurts.

**The discipline rule — Embedment Helper:**

> "Whenever you use general-purpose Foreign Code, you should seriously consider using an Embedment Helper. That way, the only Foreign Code in your DSL script should be the minimum required for the context within the DSL, calling out to the Embedment Helper for any more general processing. One of the big problems with Foreign Code is that a lot of foreign code can overwhelm the DSL, thus losing most of the advantages of readability that the DSL offers. Embedment Helper is an easy technique and is worth it in all but the smallest cases." (Fowler, DSL book, Ch. 27, "How It Works")

**Symbol references.** Sometimes the foreign code must refer to symbols defined in the DSL script itself. This only happens when the DSL has variables or other indirect constructs — "these are omnipresent in general-purpose languages, they are actually not so common in DSLs as DSLs often don't need that kind of expressiveness." Rare in practice, but familiar, because grammars themselves do it: a grammar's code actions reference labelled grammar elements, and the Parser Generator has to resolve those references at generation time.

### When to use it

(Fowler, DSL book, Ch. 27, "When to Use It")

The framing is always **Foreign Code vs. extending the DSL**.

Costs of Foreign Code:
- "By using it, you are breaking the abstraction that the DSL gives you."
- Readers now need to understand the foreign code as well as the DSL — "at least to an extent."
- It complicates the parsing process and probably the **Semantic Model** too.

Costs of extending the DSL:
- "The more powerful the DSL, the harder it is to understand and use."

Cases that lean toward Foreign Code:
1. **You genuinely need a general-purpose language.** "You certainly don't want to turn your DSL into a general-purpose language, so that pushes you quickly to using Foreign Code."
2. **The capability is needed very rarely.** "A rarely used capability may not be worth extending the DSL for."
3. **Audience.** "If the DSL is only used by programmers, then adding Foreign Code is not a problem—they will be able to understand the Foreign Code as much as the DSL. If nonprogrammers will read the DSL, that argues against Foreign Code as they may not be able to understand, and thus engage with, the foreign code. If the Foreign Code is to handle rare cases, however, this may not be a big problem."

### What the example demonstrates conceptually

The lead-allocation DSL assigns sales leads to salesmen by rules matched in order (`scott handles floor_wax in WA;` … `otherwise scott`). A business exception arrives that the DSL can't express: "any lead whose company name starts with 'Baker' in New England goes to Scott." Rather than adding regex/string matching to the DSL — "one of those particular cases that would end up complicating the language" — a JavaScript predicate is embedded.

Key conceptual points from the example:

- **Why JavaScript:** it integrates easily with Java (Rhino) and can be **evaluated at runtime, avoiding recompilation when someone changes the allocation rules.** The choice of foreign language was driven by the deployment/change cycle, not by language preference. Fowler is candid that the JS predicate "isn't exactly super readable—I suspect I'd have to say 'trust me' to the sales manager."
- **Semantic Model shape:** a lead allocator holds an ordered list of items pairing a salesman with a *lead specification*; the specification is a Specification (Evans, DDD) that matches on states, product groups, and an optional predicate string. The predicate is evaluated by the scripting engine with the candidate lead injected into the script scope so the foreign code can reach the lead's properties. **The foreign code is stored as an opaque string in the model and evaluated at match time.**
- **Self-reference:** "the code actions in a grammar are an excellent example of Foreign Code. With ANTLR, the Foreign Code gets woven into the generated parser during code generation, which is a different approach from what I'm doing with the Javascript allocation rule. But the same basic Foreign Code pattern is still in play." The two execution strategies (weave-at-generation vs. eval-at-runtime) appear side by side in the same example.
- **Delimiter selection** (echoed in Ch. 28): `{ … }` is the obvious choice but breaks if the JavaScript contains braces. Fixes: use an unlikely delimiter *pair of characters* (`{:` … `:}`), or exploit a push-down lexer to allow nested but balanced braces. Even the nested version is defeated by a brace inside a JavaScript string literal — "it should do for most cases," which is a rare and useful admission that a pragmatic 95% solution is acceptable here.

Two incidental but valuable craft notes from the same example (Fowler, DSL book, Ch. 27, "Parser"):

- **Naming:** he uses fully spelled-out labels for the tokens (salesman, predicate) "because the tokens aren't sufficiently clear," but abbreviations for the labels of subrules "because those subrule names are clear and a full label would be just duplicating the subrule name and thus add noise." **A name should add information; a name that restates the type is noise.**
- **Where to populate the model:** the product clause *returns a list of product group objects* rather than populating the Semantic Model itself, so the parent rule does the populating. Otherwise the child rule's action would need access to the current allocation rule — "This would usually require a Context Variable which I'd like to avoid. ANTLR has the ability to pass down objects as rule arguments—so I could do that there instead—but I prefer to do all the Semantic Model in the one place." **Prefer returning values upward; keep model construction in one place.**
- **Error handling:** a Notification object collects per-token errors ("Unknown salesman: …") and the driver throws only after the whole parse, so users see all errors rather than the first one.

### Relationships

- Requires **Alternative Tokenization** (Ch. 28) to capture the foreign fragment as one token.
- Should almost always be paired with **Embedment Helper**.
- Is the mechanism underneath **Embedded Translation** and **Embedded Interpretation** when using a Parser Generator.
- Ch. 31 recommends Foreign Code as the current practical substitute for **modular grammars**.

### SDK relevance

This chapter is essentially about **escape hatches in declarative APIs**, and the analysis transfers almost unchanged:

- Every declarative config format eventually faces "we need a general-purpose language here." The choices are the same three: extend the config language (it becomes a bad programming language), embed a real language (JS/Lua/CEL/Starlark/Jsonnet), or provide a plugin interface in the host language.
- **The audience test is the sharpest tool.** If non-engineers read or write the artifacts, an escape hatch fractures the audience. If only engineers use it, it costs little.
- **The "rarely needed capability" test** is the other one: don't grow the core surface for a long-tail need; give it an extension point.
- **The runtime-eval vs. compile-in decision** maps directly to plugin architectures: interpreted extensions can be changed without redeploying; compiled extensions require a build step but keep one language in the project.
- **Keep the escape hatch narrow via a helper API.** The library should expose a small, well-named helper surface so the user's embedded snippet is one line calling into it, not a program. This is exactly the design of good hook/callback APIs.
- **Store the foreign fragment opaquely.** Don't half-parse another language you don't own; you'll catch syntax errors you didn't need to catch and miss the semantic ones that matter.
- **Collect errors into a notification and report them all**, rather than failing on the first.

---

## Chapter 28: Alternative Tokenization

**Intent:** "Alter the lexing behavior from within the parser." (Fowler, DSL book, Ch. 28 "Alternative Tokenization", intent)

### The concept

The textbook picture of a Parser Generator is a one-way pipe: the lexer produces tokens, the parser consumes them. "As it turns out that isn't always the case. There are times when the way the lexer does the tokenizing should change depending on where we are in the parse tree—meaning that the parser has to manipulate the way the lexer does the tokenizing." (Fowler, DSL book, Ch. 28, "How It Works")

The motivating example is small and very real. A catalog DSL with `item camera;` lines. Programmers happily write `item small_power_plant;` or camelCase, "but regular human beings are more used to spaces" — they want `item small power plant;`. This works until an item is named "small white item": the lexer sees `item` and returns a *keyword* token, not an identifier. What you actually want is: **everything between the `item` keyword and the semicolon should be treated as name text, whatever it looks like** — i.e. different tokenization rules at that point in the parse.

The other pervasive case is **Foreign Code**, which is full of tokens meaningful in the foreign language that you want to ignore entirely so you can grab the whole fragment as one string.

### The four techniques

Not all are available in all Parser Generators.

**1. Quoting** (Fowler, DSL book, Ch. 28, "Quoting")

Put the special text inside quotation characters so the lexer can recognize it as one thing. The quoting rule "gobbles up all the text between the delimiters, so it is never touched by the other lexer rules."

Key property and key limitation: **"Quoting doesn't involve the parser at all, so a quoting scheme has to be used everywhere in the language. You can't have specific rules for quoting particular elements of the language."** It's a global decision, not a contextual one. "In many situations, however, this works out just fine."

Handling delimiters *inside* the quoted text — three tactics, all familiar from ordinary programming:
  - **Escaping**: a backslash, or doubling the delimiter. The general lexer trick: delimiters surrounding a repeating group in which one alternative is the *negation* of the delimiter (equivalent to a non-greedy match) and the others are the escape combinations. Fowler prefers the long-winded, clearly-named form over the compact regex, noting "such clarity is particularly rare when it comes to regular expressions." Caveat: "Escaping works well, but it may be confusing, particularly to nonprogrammers."
  - **Unusual delimiters**: pick a symbol pair unlikely to occur in the quoted text. Java CUP uses `{:` and `:}` for code actions precisely because plain curly braces are ubiquitous in C-family languages. "Using an unlikely delimiter is obviously only as good as the unlikeliness of its use. In many DSL situations, you can get away with it because there are only a few things you're likely to run into in the quoted text."
  - **Multiple delimiter kinds**: allow single *or* double quotes so an embedded delimiter can be handled by switching to the other. (Bonus: reduces the confusion caused by languages that give the two quote styles different escaping rules.)
  - **Balanced nesting via a push-down lexer**: ANTLR's lexer is a push-down machine, so you can write a rule that allows nested braces provided they're matched. Still defeated by a brace inside a string literal in the embedded code, which would require additional lexer rules for every embeddable construct. "The biggest downside to this technique is that you can only do it if the lexer is a push-down machine, which is relatively rare."

**2. Lexical State** (Fowler, DSL book, Ch. 28, "Lexical State")

"Perhaps the most logical way of thinking about this problem": replace the lexer entirely while reading the item name — once we see the `item` keyword, switch to a different lexer until the semicolon, then switch back. Flex calls this **start conditions** (a.k.a. *lexical state*): same lexer, different mode, with lexer rules annotated by which state(s) they apply in. Rules without a state annotation apply in all states.

The parser drives the switch: an action on recognizing the `item` keyword switches the lexer into name-gathering mode; an action after the name switches it back.

**ANTLR cannot do this** — "the lexer currently tokenizes the entire input stream before the parser starts working on it." Fowler switches to Java CUP for this example.

**The catch — parser lookahead vs. lexer state:**
- Parsers look ahead through the token stream to resolve rules. ANTLR uses arbitrary lookahead (hence full pre-tokenization). CUP/Yacc use one token of lookahead.
- **Even one token of lookahead breaks this.** For `item item the troublesome`, the first word of the name is lexed *before* the state change takes effect, so it comes through as an `item` keyword and breaks the parser.
- A subtler ordering hazard: the state must be reset *before* the statement separator is recognized, not after — otherwise the next `item` keyword is looked ahead in the wrong state.
- Fowler's conclusion: "If you use common border tokens (like quotes), you can avoid problems when you only have one token of look ahead. Otherwise, you have to be careful in how the parser look ahead interacts with the lexer's lexical states. As a result, combining parsing and lexical states can easily get pretty messy."

**3. Token Type Mutation** (Fowler, DSL book, Ch. 28, "Token Type Mutation")

"The parser's rules react not to the full contents of the token, but to the token's type. If we can change the type of a token before it reaches the parser, we can change an `item` keyword into an `item` word."

This is the **mirror image of lexical state**: lexical state needs the lexer to feed tokens one at a time; token type mutation needs the ability to *look ahead in the token stream*. So it suits ANTLR (which has the whole stream) and not Yacc.

Mechanically: the grammar shows nothing unusual; a helper called from an action runs forward along the token stream, resetting each token's type to the identifier type until it reaches the separator.

Downside: **"This technique doesn't capture exactly what was in the original text, as anything that the lexer skips won't be offered up to the parser. For example, whitespace isn't preserved in this method. If that's an issue, then this technique isn't the right one to use."**

Real-world example cited: Hibernate's HQL parser, where "order" can be a keyword (`order by`) or a column/table name. The lexer returns the keyword by default and a parser action looks ahead for a following `by`; if absent, it changes the token to an identifier.

**4. Ignoring Token Types** (Fowler, DSL book, Ch. 28, "Ignoring Token Types")

"If the tokens don't make sense and you want the full text, you can ignore the token types completely and grab every token until you reach a sentinel token" (here, the separator). The name rule accepts *any* token other than the separator — trivial with ANTLR's negation operator; without negation you must enumerate all keywords in the rule, "which is more awkward." The tokens still carry their correct types; you simply don't use the type in this context, reconstructing the text from the token contents. With **Tree Construction** you'd do the analogous thing: collect all the name tokens into a single list node and ignore the types when walking the tree.

### When to use it

(Fowler, DSL book, Ch. 28, "When to Use It")

- Relevant when using **Syntax-Directed Translation** with tokenization separated from syntactic analysis — "which is the common case."
- "You need to consider it when you have a section of special text that shouldn't be tokenized using your usual scheme."
- The three common triggers: **keywords that shouldn't be keywords in a particular context**; **allowing any form of text (typically for prose descriptions)**; and **Foreign Code**.

### Relationships

- Prerequisite for **Foreign Code** (Ch. 27).
- Interacts badly with **Newline Separators** (Ch. 30) — Fowler deliberately uses semicolons in this chapter's examples "to deal with one tricky issue at a time."
- Offered in Ch. 31 as the (constrained) workaround for **modular grammars** when the child grammar needs a different lexer.
- **Ignoring Token Types** has a natural Tree Construction analogue.

### SDK relevance

- **This is the "context-sensitive input" problem** that shows up in any format library: a field whose contents shouldn't be interpreted by the enclosing parser (raw blocks in markup, template literals, embedded SQL/JSON, prose fields).
- **The four techniques map onto four API design choices**: require quoting/escaping (simple, global, but pushes burden onto users and hurts non-programmers); switch modes based on position (contextual and pleasant, but interacts badly with lookahead/streaming); post-process the token stream (loses skipped input — beware if you need round-trip fidelity); or take everything up to a sentinel (simplest and most robust when a clean terminator exists).
- **Design for the non-programmer's input habits.** The whole chapter is triggered by users wanting spaces instead of `snake_case`. If your DSL/config/CLI is authored by non-engineers, the cost of accommodating natural text is real parser complexity — decide deliberately rather than defaulting to identifier rules.
- **Round-trip fidelity is a first-class requirement.** Token type mutation silently loses whitespace. If your library must reproduce input (formatters, linters with autofix, config rewriters), choose the technique that keeps all the characters.
- **Delimiter choice is a real design decision.** Pick delimiters unlikely to occur in the embedded content, or allow alternatives; accept that no scheme is airtight and document the limits.

---

## Chapter 29: Nested Operator Expression

**Intent:** "An operator expression that can recursively contain the same form of expression (for example, arithmetic and Boolean expressions)." (Fowler, DSL book, Ch. 29 "Nested Operator Expression", intent). Sketch: `2 * (4 + 5)`.

### Framing — this one isn't really a pattern

Fowler is upfront: "Calling Nested Operator Expression a pattern is a bit of a stretch, since it isn't so much a solution as it is a common problem in parsing." His "When to Use It" section is a joke at his own expense: it exists only "to flaunt a fixation with consistency which isn't usually something I'm known for."

*(Note: the opening text says the left-recursion issue arises "particularly … with bottom-up parsers"; the body of the chapter demonstrates the opposite — bottom-up parsers handle left recursion fine and it is the top-down parsers that must eliminate it. Read the body, not the intro sentence.)*

### The two difficulties

1. **Recursion** — the rule appears inside its own body.
2. **Precedence** — `1 + 2 * 3` must mean `1 + (2 * 3)`.

Plus **associativity**, which must be declared even where it seems not to matter.

His example language: `+ - * /`, parenthesized groups, power (`**`) and root (`//`), and unary minus. Precedence, tightest first: unary minus, then power/root, then multiply/divide, then add/subtract. Power and root are **right**-associative; the other binary operators are **left**-associative. He picked power/root specifically to force the right-associative case into the example.

### Bottom-up parsers (Yacc/CUP family)

"The easiest to describe." A single production rule with one alternative per operator plus a base case for a bare number. The recursion is direct and reads clearly — the grammar looks like the structure of the language.

Precedence isn't in the grammar rules; it's declared separately: a list of precedence statements, each naming operators at the same level and their associativity, ordered from low to high. Precedence can also be attached to an individual rule — the unary-minus rule uses a **ghost token** (`UMINUS`) that never appears in the input and exists solely to give that rule a different precedence from binary minus ("context-dependent precedence").

Why precedence declarations exist at all: **ambiguity**. "Without the precedence rules, a parser with this grammar could parse `1 + 2 * 3` as `(1 + 2) * 3` or as `1 + (2 * 3)`, which makes it ambiguous. The same is true for `1 + 2 + 3` even though we (humans) know it doesn't matter in this case. This is why we have to state the direction of associativity as well, even though it doesn't matter for `+` and `*`." (Fowler, DSL book, Ch. 29, "Using Bottom-Up Parsers") — **the parser needs a total order even where semantics is indifferent.**

Verdict: "The combination of a simple recursive grammar rule and precedence declarations makes it very easy to handle nested expressions in a bottom-up parser."

### Top-down parsers (ANTLR family)

"More complicated." You can't write the simple recursive rule because it introduces **left recursion**, which a top-down parser cannot handle. The standard fix is a **cascade of rules, one per precedence level** — which simultaneously eliminates the left recursion and encodes precedence. "The resulting grammar, however, is much less clear. Indeed, this lack of clarity is why many people prefer a bottom-up parser."

The three idioms to memorize (Fowler, DSL book, Ch. 29, "Top-Down Parsers"):

- **Left-associative binary operator**: the rule body starts with a reference to the *next-lower* precedence rule, followed by a repeating group of (operator, next-lower rule). At all points you refer to the next-lower rule, never to yourself.
- **Right-associative binary operator**: the right-hand side is a **recursive reference to the rule itself**, and the group is **optional** rather than repeating. "The recursion allows multiple power expressions to be combined together, and the right recursion like this is inherently right-associative."
- **Unary prefix operator**: recurse into yourself when the sign is present (so multiple minus signs work), and fall through to the next-lower rule when it isn't (avoiding left recursion).
- **Atoms** sit at the bottom (numbers, parenthesized expressions). Parenthesized expressions "introduce deep recursion as they reference the top-level expression again."
- ANTLR-specific: you must add a start rule that nothing else calls, or you get a "no start rule" error.

Three consequences of the mangling:

1. **You're not expressing intent any more.** "You're spending your time massaging the Parser Generator rather than expressing intent. The resulting mangled grammars are why many people prefer bottom-up Parser Generators to top-down ones. Advocates of top-down parsing argue that it's only nested expressions that get thus mangled, and that's a worthwhile tradeoff compared to the other problems with bottom-up parsers."
2. **The parse tree fills with clutter nodes.** `1 + 2` should produce a `+` with two number children; instead each operand carries a chain of one node per precedence level (mult_exp → power_exp → unary_exp → factor_exp → `1`). "This isn't a huge deal in practice; you need to write code to handle these nodes for the cases when they're useful, but sometimes they are just irritating."
3. **Adding output production makes it worse.** With any number of terms at one level (`1 + 2 + 3 + 4`), you need an accumulator variable declared at the start of the rule and accumulated inside the repeating group. And because `+` and `-` must do different things, you have to **widen the alternative** — duplicating the right-hand-side reference in each branch instead of factoring the operator set out. "This introduces some duplication, but this is often the case once you actually do something with your grammar. Tree Construction often reduces this problem, but even so you might want to return a different type of node for plus and minus, which would require widening the alternative."

Closing practical advice: different top-down parsers have slightly different problems and solutions, and they usually document them under "left recursion."

### Relationships

- Forced upon you by **Embedded Interpretation**'s calculator example (Ch. 26) — and Ch. 26 warns that the calculator example is unrepresentative precisely *because* it drags in this rare problem.
- **Tree Construction** (Ch. 24) mitigates the code-action duplication.
- The bottom-up/top-down distinction here is the strongest argument in the book about **Parser Generator** choice.

### SDK relevance

- **Precedence and associativity are ambiguity resolution, not semantics.** Any API that accepts user-authored expressions (query filters, rule engines, formula fields, search syntax) must define a total precedence order and document it — even for operators where order is mathematically irrelevant, because *the parser* needs it.
- **Grammar/DSL shape is constrained by your tool.** If your expression grammar has to be mangled to satisfy the parser, expect (a) a parse tree that doesn't match the mental model and (b) downstream code full of pass-through node handling. Budget for a normalization step that collapses the clutter.
- **When the tool forces you to duplicate structure, add a layer that restores intent.** The cascade is fine as machinery, but users of the resulting tree shouldn't have to know about `mult_exp`/`power_exp` — flatten it.
- **The general lesson about tutorial examples**: expression parsing is the most over-taught and least representative parsing problem. Don't design a general library around it.

---

## Chapter 30: Newline Separators

**Intent:** "Use newlines as statement separators." (Fowler, DSL book, Ch. 30 "Newline Separators", intent)

### The concept and the core difficulty

Using newlines to end statements is a common programming-language feature and, with **Delimiter-Directed Translation**, it's completely natural — the newline is *already* the main delimiter used to break up the input, so there's nothing extra to say. With **Syntax-Directed Translation** it's "rather more tricky, introducing a number of subtle traps."

The root cause is worth internalizing:

> "The reason that newline separators and Syntax-Directed Translation don't go together too well is that newlines play two roles when you use them as separators. Apart from their syntactic role, they also play a formatting role in providing vertical space. As a result, they can appear in spaces where you wouldn't expect a statement separator to pop up." (Fowler, DSL book, Ch. 30, "How It Works")

(He adds: it's possible in principle to use newlines for some syntactic purpose *other* than statement separation, but he's never come across it.)

### The four cases that break the naive grammar

Given the obvious grammar — a statement is `keyword identifier EOL` and a catalog is a list of statements — these all fail:

1. Blank lines *between* statements
2. Blank lines *before* the first statement
3. Blank lines *after* the last statement
4. The last statement having **no end-of-line at all**

The first three are all blank lines but "may need different ways of handling them in the grammar, so should all be tested." And the headline advice:

> "Making sure you have tests for these cases is probably the most important thing to do. I've got some solutions for these problems below, but the good tests are the key to ensuring that the situations are covered properly." (Fowler, DSL book, Ch. 30, "How It Works")

### Three grammar shapes for handling it

1. **End-of-statement rule matching multiple newlines.** Logically this belongs in the lexer (it's a regular expression), but the missing-final-newline case forces you to match end-of-file, which may be impossible in the lexer depending on the Parser Generator. ANTLR exposes EOF to the *parser* as a token, so the end-of-statement rule has to live in the parser grammar: a `verticalSpace` rule of zero-or-more EOLs, plus an `eos` rule of one-or-more EOLs *or* EOF.
   - "A missing end-of-line on the last line is often an awkward case. How awkward depends on how the Parser Generator deals with an end-of-file. … Others make matching an end-of-file very hard or impossible. One option to consider is forcing an end-of-line at the end—either through the lexer (if you can) or perhaps by prelexing. Forcing a final end-of-line can help avoid a few awkward corner cases." **Normalizing the input before parsing is a legitimate and often cheapest fix.**

2. **Treat them as separators rather than terminators**: `statement (separator statement)*` bracketed by optional vertical space. "I've come to prefer this style. Instead of defining an extra `verticalSpace` rule, I can use `separator?`." — This is Fowler's stated preference.

3. **Statement body as an optional element of each line**: a line is either just an EOL, or a statement followed by EOL, or a statement followed by EOF. Requires explicit EOF matching for the missing-final-newline case; there's an EOF-free variant that "doesn't read as clearly to me, but also doesn't need the end-of-file matching."

### Comments — the other trap

Comments that run to end-of-line are very useful, and they interact badly with newline separators. When newlines are ignored, you can happily write a comment rule that consumes the newline (though a final comment with no trailing newline can still trip you). **With newline separators, consuming the newline destroys the statement terminator**, and comments very often sit at the end of a statement (`item laser # explain something`). The fix is easy once seen: write the comment rule to match everything up to *but not including* the newline.

### Line continuation

Long lines need an escape: a lexer rule matching a continuation character followed by optional whitespace and the end-of-line, skipped entirely.

### When to use it

(Fowler, DSL book, Ch. 30, "When to Use It")

Fowler decomposes it into **two separate decisions**:

**Decision 1: should you have statement separators at all?**
- "The limited structure of a DSL often means that you can live without statement separators. The parser can usually figure out the context of the parse from the various keywords you use." His own Miss Grant's controller grammar has none and parses fine.
- The argument *for* separators is **error localization**: "In order for the parser to localize errors it needs some kind of checkpointing marker to tell where it's supposed to be in the parse. Without checkpointing, an error in one line of the script may not be apparent to the parser until several lines later, leading to confusing error messages. Statement separators can often fulfill this role. (Although they are not the only mechanism that can do this; keywords often do this too.)"

**Decision 2: if yes, newline or a visible character?**
- "The nice thing about using newlines is that most of the time, you have one statement per line anyway, so using a newline separator doesn't add any syntactic noise to the DSL. This is particularly valuable when working with nonprogrammers, although many programmers (including myself) prefer newline separators as well."
- "The downside with newline separators is that Syntax-Directed Translation is made more finicky and you have to use the techniques I've described here. You also need to ensure you have tests to cover the common problem cases."
- Verdict: "On the whole, however, I still prefer to use newlines rather than a visible statement separator."

### Relationships

- Trivial with **Delimiter-Directed Translation**; fiddly with **Syntax-Directed Translation**.
- Ch. 28 deliberately avoids newline separators to isolate one difficulty at a time.
- **Syntactic Indentation** (Ch. 31) is the next step down this road and is much harder.

### SDK relevance

- **Syntax that is invisible to the eye is expensive to implement.** Whitespace-significant formats are pleasant for authors and painful for maintainers of the parser. The pleasure is real (no syntactic noise, better for non-programmers) — just price the implementation cost honestly.
- **The four failure cases are a ready-made test checklist** for any line-oriented format: leading blank lines, trailing blank lines, interior blank lines, missing final newline. Also add: comment at end of last line with no trailing newline. These are exactly the bugs that ship in hand-rolled config parsers.
- **Normalize input at the boundary.** Appending a final newline before parsing eliminates a whole class of corner cases — a general principle for input-handling APIs: canonicalize early so the core logic sees only well-formed input.
- **Checkpointing improves error messages.** Any recovery-capable parser or validator needs synchronization points. If your format has no natural ones, error reporting will be vague — design the format with them or accept the diagnostics quality.
- **A dual-role token is a design smell.** Newlines serve both structure and visual formatting; wherever a single element carries two responsibilities, ambiguity follows.

---

## Chapter 31: External DSL Miscellany

Chapter 31 is explicitly a hodgepodge of unfinished topics. Fowler frames it as a scope-cutting decision: "As with writing software, there is a point at which you have to cut scope in order to ship your software, and the same is true of book writing." He flags that "the thoughts here are more preliminary than much of the other material in this book. By definition, these are all topics that I haven't done enough work on to merit a proper treatment." (Fowler, DSL book, Ch. 31 "External DSL Miscellany", opening) *(Worth noting as a model of intellectual honesty in technical writing: label the parts you're less sure of.)*

---

### 31.1 Syntactic Indentation

**The idea.** Most languages express hierarchy with nested blocks marked by delimiters (curly brackets). But that's not how humans actually read it:

> "However, when you read the structure, you pay more attention to the formatting. The primary form of structure that we read comes from the indentation, not from the delimiters." (Fowler, DSL book, Ch. 31, "Syntactic Indentation")

He demonstrates with a nested list of European countries formatted so the indentation *contradicts* the braces — the reader is misled, because the eye trusts the indentation. Since we read structure through indentation anyway, the argument goes, let the indentation *be* the structure. Python is the famous example; YAML is the other.

**The usability advantage.** "The definition and the eye are always in sync—you can't mislead yourself by altering the formatting without changing the real structure." He immediately qualifies it: editors with automatic formatting remove much of that advantage for mainstream languages — "but DSLs are less likely to have that kind of support." **The value of syntactic indentation is highest exactly where tooling is weakest, which is where DSLs live.**

**Tabs.** "If you use syntactic indentation, be very careful about the interplay between tabs and spaces. Since tab widths vary depending on how you set the editor, mixing tabs and spaces in a file can cause no end of confusion. My recommendation is to follow the approach of YAML and forbid tabs from any language that uses syntactic indentation. Any inconvenience you'll suffer from not allowing tabs will be much less than the confusion you avoid." — A clean example of **eliminating a whole class of user error by removing the ambiguous input rather than by handling it.**

**Why it's hard to parse.** "Syntactic indentation is very convenient to use, but presents some real difficulties in parsing. I spent some time looking at Python and YAML parsers and saw plenty of complexity due to the syntactic indentation."

- It has to be handled **in the lexer**, since the lexer is the part of a Syntax-Directed Translation system that deals with characters.
- **Delimiter-Directed Translation is a poor companion** for syntactic indentation, "since syntactic indentation is all about counting the kind of block structure that Delimiter-Directed Translation has problems with." (Both are line-oriented, but indentation demands exactly the nesting that delimiter-directed processing handles badly.)
- **The effective tactic: imaginary INDENT/DEDENT tokens.** Get the lexer to emit special "indent" and "dedent" tokens when it detects an indentation change. "Using these imaginary tokens allows you to write the parser using normal techniques for handling blocks—you just use 'indent' and 'dedent' instead of `{` and `}`." The parser then never knows about indentation at all — a clean separation.
- **But the lexer fights you.** "Doing this in a conventional lexer, however, is somewhere between hard and impossible. Detecting indentation changes isn't something lexers are designed to do, nor are they usually designed to emit imaginary tokens that don't correspond to particular characters in the input text. As a result, you'll probably end up having to write a custom lexer." (ANTLR can do it; he points at Parr's advice for handling Python.)
- **The alternative he'd try first: a preprocessor.** "Another plausible approach—one that I'd certainly be inclined to try—is to preprocess the input text before it hits the lexer. This preprocessing would only focus on the task of recognizing indentation changes and would insert special textual markers into the text when it finds them. These markers can then be recognized by the lexer in the usual way." Two costs: you must pick markers that can't clash with anything in the language, and you must cope with the effect on **diagnostics that report line and column numbers** (you've now altered the text the user wrote). "But this approach will greatly simplify the lexing of syntactic indentation."

**Summary of the tradeoff.** Syntactic indentation is a genuine usability win — structure and appearance can never diverge — bought at a real and non-trivial implementation cost, most of which lands in the lexer, and which usually means writing or heavily customizing a lexer rather than using one off the shelf.

**SDK relevance:**
- **Translating an implicit property into explicit tokens early** is the key move: convert indentation into INDENT/DEDENT at the boundary so every downstream layer works with ordinary nesting. Generalizes to any API dealing with implicit structure — normalize it into an explicit representation at the edge rather than teaching every consumer about it.
- **A preprocessing stage is a legitimate architecture**, but it breaks source-position mapping. If you insert or rewrite text before parsing, you need a source map to keep error messages honest. This is the same problem transpilers and template engines face.
- **Forbid the ambiguous input.** Banning tabs is a design decision that trades a small inconvenience for the removal of an entire class of confusing bugs. Look for the equivalent in your own API surface (e.g. reject ambiguous date formats rather than guessing).

---

### 31.2 Modular Grammars

**The motivating principle** (one of the most quotable statements of the book's philosophy):

> "DSLs are the better the more limited they are. Limited expressiveness keeps them easy to understand, use, and process. One of the biggest dangers with a DSL is the desire to add expressiveness—leading to the trap of the language inadvertently becoming general-purpose." (Fowler, DSL book, Ch. 31, "Modular Grammars")

**The proposed escape from the trap:** rather than growing one language, **combine several independent DSLs**. That requires parsing the different pieces independently. With Syntax-Directed Translation, it means separate grammars per DSL that can be woven into a single overall parser. The goal is explicitly stated in library terms:

> "You want to be able to reference a different grammar from your grammar, so that if that referenced grammar changes you don't need to change your own. Modular grammars would allow you to use reusable grammars in the same way that we currently use reusable libraries."

**State of the art (as of writing, 2010):** "Modular grammars, however useful for DSL work, are not a well-understood area in the language world. There are some people exploring this topic, but nothing that's really mature as I write this."

**The specific technical obstacle — the separate lexer.** "Most Parser Generators use a separate lexer, which further complicates using modular grammars since a different grammar will usually need a different lexer than the parent grammar." The lexer is global and stateless with respect to grammar composition, so two grammars with different lexical conventions can't simply be glued together.
- **Workaround:** **Alternative Tokenization** (Ch. 28) — "but that places constraints on how the child grammar can fit in with the parent."
- **The promising direction:** **scannerless parsers** — "those which don't separate lexical and syntactic analysis—may be more applicable to modular grammars." (Because if there's no separate lexer, there's no lexer to conflict.) He reports "a growing feeling" in this direction rather than a settled conclusion.

**The practical advice for today:**

> "For the moment, the simplest way of dealing with separate languages is to treat them as Foreign Code, pulling the text of the child language into a buffer and then parsing that buffer separately." (Fowler, DSL book, Ch. 31, "Modular Grammars")

That is: **don't try to compose grammars — compose parsers.** Capture the sub-language as an opaque string (Alternative Tokenization / Foreign Code), then run a second, independent parse over that string. Simple, robust, and it keeps the two grammars genuinely decoupled; the cost is that the outer grammar can't validate or interleave with the inner one, and error positions must be mapped back manually.

**Relationships:** Depends on **Foreign Code** (Ch. 27) and **Alternative Tokenization** (Ch. 28). It is the composition-level answer to the same pressure that Foreign Code answers at the expression level. It's also the structural counterweight to the "DSL creeps toward general-purpose" failure mode.

**SDK relevance:**
- **"Limited expressiveness is a feature" is the core API design lesson of the whole book**, stated here most compactly. Resist the pull toward generality: every capability you add makes the surface harder to learn and harder to process. Prefer several small, focused APIs/languages over one that grows to cover everything.
- **Composition over expansion.** When a DSL/API needs to cover a new area, ask whether it should be a *separate* composable language/module rather than new syntax in the existing one. This is the argument for plugin ecosystems and for formats that embed other formats by reference.
- **Layer boundaries block composition.** The lexer/parser split is exactly the kind of global, cross-cutting layer that prevents modules from composing. Watch for the same shape in libraries: a global registry, a single shared config schema, a singleton serializer — anything that must be globally consistent will block plugin composition. Scannerless parsing is the "remove the global layer" answer.
- **Opaque embedding is the pragmatic composition mechanism.** Take the sub-language as an opaque blob and delegate to its own parser/handler. This is how most real systems compose formats, and it works because the interface is a string plus a well-defined boundary.

---

## Cross-cutting synthesis

**1. The output-production decision, condensed.**

| | Tree Construction (24) | Embedded Translation (25) | Embedded Interpretation (26) |
|---|---|---|---|
| Produces | AST → then Semantic Model | Semantic Model directly | The answer directly |
| Passes over input | Many (walk the tree freely) | Exactly one | Exactly one |
| Forward references | Easy (later passes resolve) | Hard (find-or-create + Context Variable) | N/A / hard |
| Grammar file cleanliness | Enforced by the mechanism | Depends on your discipline | Depends on your discipline |
| Side-effect risk | None (actions return subtrees) | Real (actions may fire unexpectedly) | Real |
| Reuse of parse | High (many walks, many models) | None | None |
| Cost | Two stages to write | One stage | One stage |
| Best when | Complex transformation, multiple passes, good AST tooling | Simple language, simple parser, single pass suffices | Small expressions; the syntax tree *is* the model |

Fowler's default position: **build a Semantic Model** (so 24 or 25, not 26); choose between 24 and 25 on complexity, pass count, and tool support; and switch from 25 to 24 the moment side effects or forward references get tangled.

**2. The recurring "keep the grammar clean" discipline.** Across Ch. 24, 25 and 27 the same advice recurs: the grammar file should read as a description of the language, not as a program. Mechanisms: **Embedment Helper** (one call per action), tree-construction DSLs instead of hand-rolled node building, returning values upward instead of mutating shared context, and keeping all Semantic Model construction in one place. The strongest form of the argument is that Tree Construction *enforces* what Embedded Translation merely *permits*.

**3. Context is the enemy.** Context Variables are treated as a smell throughout. The preferred alternatives, in order: let a later pass resolve it (Tree Construction); pass it down as a rule parameter; return values upward and let the parent assemble. Only when none of those work does Fowler accept "what is effectively a context variable" — and he says so apologetically.

**4. The lexer/parser boundary is where most of the pain lives.** Ch. 27, 28, 30 and 31 are all, at bottom, about that boundary: the lexer has no context but must make context-dependent decisions (Alternative Tokenization); the lexer discards whitespace the parser needs (hidden channels, INDENT/DEDENT, newline separators); the lexer is global and blocks grammar composition (modular grammars). Scannerless parsing is named as the direction that dissolves the problem.

**5. Escape hatches: the meta-pattern.** Foreign Code and modular grammars are two answers to the same question — what to do when the limited language isn't enough. The answers Fowler endorses: keep the DSL limited, embed rather than expand, keep the embedded portion minimal via a helper API, and let the audience's skill level decide how visible the escape hatch may be.
