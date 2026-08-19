# External DSLs, Computational Models, and Code Generation

Condensed from Fowler, *Domain-Specific Languages* (2010), Part 3 — Pattern Catalog II (Chs. 17–31, 47–51, 52–57). Citations point at the book; "SDK lens" notes are the transfer to library/API design.

## Contents

**Parsing an external DSL** — [1 Delimiter-Directed Translation](#1-delimiter-directed-translation-ch-17) · [2 Syntax-Directed Translation](#2-syntax-directed-translation-ch-18) · [3 BNF](#3-bnf-ch-19) · [4 Regex Table Lexer](#4-regex-table-lexer-ch-20) · [5 Recursive Descent Parser](#5-recursive-descent-parser-ch-21) · [6 Parser Combinator](#6-parser-combinator-ch-22) · [7 Parser Generator](#7-parser-generator-ch-23) · [8 Choosing a parsing strategy](#8-choosing-a-parsing-strategy)

**Producing output from a parse** — [9 Tree Construction](#9-tree-construction-ch-24) · [10 Embedded Translation](#10-embedded-translation-ch-25) · [11 Embedded Interpretation](#11-embedded-interpretation-ch-26) · [12 Choosing an output strategy](#12-choosing-an-output-strategy) · [13 Foreign Code](#13-foreign-code-ch-27) · [14 Alternative Tokenization](#14-alternative-tokenization-ch-28) · [15 Nested Operator Expression](#15-nested-operator-expression-ch-29) · [16 Newline Separators](#16-newline-separators-ch-30) · [17 Syntactic indentation & modular grammars](#17-syntactic-indentation--modular-grammars-ch-31)

**Alternative computational models** — [18 Adaptive Model](#18-adaptive-model-ch-47) · [19 Decision Table](#19-decision-table-ch-48) · [20 Dependency Network](#20-dependency-network-ch-49) · [21 Production Rule System](#21-production-rule-system-ch-50) · [22 State Machine](#22-state-machine-ch-51)

**Code generation** — [23 Transformer Generation](#23-transformer-generation-ch-52) · [24 Templated Generation](#24-templated-generation-ch-53) · [25 Embedment Helper](#25-embedment-helper-ch-54) · [26 Model-Aware Generation](#26-model-aware-generation-ch-55) · [27 Model Ignorant Generation](#27-model-ignorant-generation-ch-56) · [28 Generation Gap](#28-generation-gap-ch-57)

---

# Parsing an external DSL

The seven parsing patterns sit on one spectrum: **how explicitly is the structure of the language stated?** No grammar (Delimiter-Directed) → implicit in functions (Recursive Descent) → explicit as composed objects (Parser Combinator) → explicit as a BNF DSL (Parser Generator). Moving right buys documentation value, easier evolution, and power on complex languages; it costs a grammar learning curve and, at the far right, build complexity. Fowler repeatedly frames this as a decision about *your team and your build*, not only about your language.

## 1. Delimiter-Directed Translation *(Ch. 17)*

**Intent:** "Translate source text by breaking it up into chunks (usually lines) and then parsing each chunk."

**Concept.** Split the input on a delimiter (almost always the line ending) and run each chunk through code that recognizes and processes it. No grammar, no lexer/parser split, no parse tree — string splitting, regexes, conditionals. Output goes to a Semantic Model (Embedded Translation) or is interpreted on the spot.

**Mechanics.** *Line continuation:* quoting the line ending (backslash) "looks ugly … and is vulnerable to whitespace between the quote and the end of line." Prefer a dedicated continuation character; the join must loop, since continuations chain.
- *The line taxonomy — a complexity ladder.* **Autonomous + isomorphic** (no line affects any other; all lines same form) → one line-processing function. **Autonomous + polymorphic** → dispatching conditional, with each regex wrapped in a well-named predicate method, and a mandatory final `else throw RecognitionException`. **Isomorphic lines with polymorphic clauses** → top-level routine splits clauses, each clause routine dispatches internally. **Nonautonomous statements** (same form means different things in different blocks) → force parse state; use a family of line parsers, one per parse state, swapped by the top-level parser. "This, of course, is just an application of the *State [gof]* design pattern."
- *Extracting data*, in order of preference: string splitter → regex with named capture groups (doubles as a validity check) → **composed regex** (break a big regex into named subexpression constants and concatenate). *Whitespace is a recurring pain* — optional whitespace around `=` complicates processing; forbidding it makes the DSL harder to use. *It is doing grammar work anyway:* polymorphic lines are **alternatives**, isomorphic lines are **production rules without alternatives**, clause methods are **subrules**.

**When to use.**
- **Strength: approachability.** "Very simple for people to use" — relies purely on techniques most programmers already have.
- **Weakness: the same approachability.** Works well for simple languages, "particularly those which don't require much nested context"; as complexity increases it "can get messy quickly."
- **The recommendation:** favor it only with simple autonomous statements, "or maybe just a single nested context. Even then I'd prefer to use Syntax-Directed Translation unless I'm working with a team that I didn't think was prepared to deal with learning that technique." A team-capability decision, stated as such.
- **The slippery-slope tripwire:** when your dispatch table starts wanting configuration, ordering, and state, "once you've got far enough into this to want to use a framework, then the jump to Syntax-Directed Translation is not much further."
- *Behavior placement with a context object:* decentralized (behavior in line parsers) forces repeated pulls from a shared symbol table — "Pulling data out of an object repeatedly is usually a bad smell"; centralized concentrates logic and "may make it overcomplicated." Fowler: "I'll confess I don't have a strong preference either way."

**Relationships.** Alternative to Syntax-Directed Translation. Feeds Embedded Translation / Embedded Interpretation. Natural fit for Newline Separators (§16); poor host for syntactic indentation (§17). The technique of choice for a minimal interpreter in a constrained target (§26).

> **SDK lens:** Steal the line taxonomy as a complexity ladder for any config or input format. Keep statements autonomous and isomorphic and the implementation stays trivial while the format stays reorderable and diffable — **design formats where each statement carries its own context**, because context-sensitivity is what forces stateful parsing machinery on you. "Once you want a framework for this, you should have used the real tool" is a general smell test. And fail loudly: a parser that silently ignores what it does not understand is a bug factory.

## 2. Syntax-Directed Translation *(Ch. 18)*

**Intent:** "Translate source text by defining a grammar and using that grammar to structure translation."

**Concept.** The umbrella pattern. A grammar defines how elements decompose into subelements, and drives creation of a parser producing a **parse tree mirroring the grammar rules**. Two routes: grammar as spec/implementation guide for a handwritten parser (Recursive Descent, Parser Combinator), or grammar as a DSL fed to a Parser Generator. "The grammar only handles part of the problem" — it gets you to a parse tree and no further. Fowler's best one-line argument for DSLs generally: "although the Parser Generator does a lot of work for you, you still have to do a fair bit of programming… It doesn't solve the whole problem, but does make a significant chunk of it much easier."

**The three-layer architecture.**
- **Layer 1 — lexer.** Splits characters into **tokens**, each with a **type** and a **payload** (plus line/column for diagnostics). Separate from the parser for *simplicity* (parser works in tokens) and *efficiency* ("the lexer is usually a state machine while the parser is usually a push-down stack machine"); scannerless parsers merge the two. Rules are *ordered, first match wins*, so a keyword can never also be an identifier, "avoiding such things as PL/1's notorious `if if = then then then = if;`." Whitespace is usually stripped (the lexer must emit tokens when it is significant); comments are usually discarded, though "it's always useful to have comments in even the smallest DSL." Three kinds of token: **punctuation** (type matters, payload doesn't), **domain text** (names, literals), **ignorables**. Handwritten lexers give "more flexibility for more complex interactions between the parser and the lexer" — notably multiple modes the parser can switch between (Alternative Tokenization).
  - **Keep lexing simple.** Don't define a dedicated `code` token type for four-character codes: `FAIL FZ17` would tokenize `FAIL` as a code "because the lexer only looks at the characters, not the overall context." Leave it to the parser. "It's best to keep lexing as simple as possible."
- **Layer 2 — syntactic analyzer.** *Syntactic analysis* (arranging tokens into a tree) "can be derived entirely from the grammar itself"; *actions* cannot and run while the tree is built. Analysis alone yields only success/failure — **recognizing** the input. **The parse tree usually is not real** — the parser builds pieces, runs actions mid-parse, discards them. Terminology: **parse tree** reflects the parse with all tokens; **AST** is simplified and reorganized for later processing; **syntax tree** is the supertype.
  - **Many grammars match the same language** — two grammars accepting identical inputs can produce different parse trees. **The grammar is a design artifact with choices in it, not a transcription of the language.**
- **Layer 3 — output production.** Embedded Translation, Tree Construction, Embedded Interpretation (§§9–11). Woven into handwritten code, passed as action objects, or embedded as Foreign Code in the grammar.

**Semantic predicates.** "A hunk of general-purpose code that provides a Boolean response to indicate whether a grammar production should be accepted or not — effectively overriding what's expressed by the rule." Fowler's directive: **"You shouldn't come across the need to use semantic predicates for a DSL, since you should be able to define the language in such a way as to avoid this need."** Needing one means your DSL syntax is wrong.

**When to use.**
- **Principal disadvantage:** getting used to driving parsing via a grammar. "But it doesn't take long … and once you do, they provide a technique that is much easier to use as your DSLs get more complex."
- **The key upside:** "the grammar file — itself a DSL — provides a clear documentation of the syntactic structure of the DSL it's processing. This makes it easier to evolve the syntax of the DSL over time."

**Relationships.** Umbrella for BNF, Regex Table Lexer, Recursive Descent, Parser Combinator, Parser Generator. Counterpart of Delimiter-Directed Translation. Its lexer/parser boundary is where Alternative Tokenization, Newline Separators, and modular grammars get hard.

> **SDK lens:** The layering is the lesson — lexer → analyzer → actions → semantic model, each raising abstraction, each with one responsibility. **Never push a decision into a layer that lacks the context to make it correctly**; `FAIL FZ17` is a leaky abstraction producing subtly wrong answers rather than loud errors. A self-documenting declarative spec is the whole argument for OpenAPI/protobuf/type-stub artifacts. "Many grammars, one language" is "many resource models express the same capability," and the model you pick shapes every client. **Recognition versus output is validation versus deserialization** — a yes/no answer is cheap and worth exposing independently. Treat semantic predicates as a design smell: if users of your schema constantly reach for the escape hatch, the schema is wrong.

## 3. BNF *(Ch. 19)*

**Intent:** "Formally define the syntax of a programming language."

**Concept.** "In a wonderful display of irony, BNF, a language for defining syntax, does not itself have a standard syntax." Treat it as "a family of languages… with a pattern, you see it differently every time."

**Core vocabulary.** **Production rules** (name + body) decompose into **elements**, which are other rules or **terminals** — "your terminals will usually be the token types that come out of the lexer." **Alternatives** (`|`) "actually unleash an enormous amount of expressive power": everything else reduces to alternatives plus recursion. **Extract subrules for intent** even when a subrule resolves to a single terminal — "similarly to extracting a simple method in imperative code." **Grouping** can inline subrules but usually shouldn't: "the subrules capture intent and make the grammar much more readable." Put each logical piece of a complicated rule on its own line.

**Operators:** `|` alternative · `*` none-or-more · `+` one-or-more · `?` optional · `~` up-to (`~'}'` ≡ regex `[^}]*`) · `..` range (lexical rules only; ASCII-centric, which hurts non-English identifiers) · `/` ordered alternative. "Adding multiplicity symbols is usually what makes the difference between EBNF and basic BNF." Lexical rules are kept separate from syntactic ones and stay close to regular expressions.

**Ordered alternatives / PEGs.** "The biggest difference between a PEG and a CFG is that PEGs have ordered alternatives." Use them when two rules can both match the same input (structured US phone number vs raw number) and you want first-match-wins. Some mainstream tools use unordered syntax but warn on ambiguity and take the first match — a decent compromise to copy.

**Converting EBNF to basic BNF.** Multiplicity symbols add readability, not power; **the key to every transformation is alternatives.** `foo?` → `foo | `. Folding `a : b? c` → `a : c | b c` — with several optionals "you get into a combinatorial explosion, which, like most explosions, isn't something that's fun to be in the middle of." Repetition uses recursion: `x : y*` → `x : y x | `. **Left vs right recursion matters: "a top-down parser cannot do left recursion at all," while Yacc prefers right recursion.** Cost of conversion: extra subrules, lost multiplicity markers, "much harder to follow. As a result, I always prefer to use EBNF if all else is equal."

**Code actions.** BNF alone gets you a parse tree, so tools let you embed **code actions**. Refer to elements by **named labels**, not positional variables — "positional references are brittle to changes in the grammar." **Rules can return values**, and that facility matters most:
> "Often, the rule that gives you the best information about a value isn't the best rule to decide what to do with that data. Passing data up the rule stack allows you to capture information at a low level in a parse, and deal with it at a higher level. Without this, you would have to use a lot of *Context Variables* — which would soon get very messy."

Placement determines timing; "most of the time it's easiest to put code actions at the end of a rule." Beware: "Recursive-descent parsers are usually pretty easy to follow, but bottom-up parsers often cause confusion." **The big danger:** too much code in actions destroys the grammar's readability — "I thus strongly recommend that you use *Embedment Helper* when using code actions."

**When to use.** Required with a Parser Generator. And: "**It's also very useful as an informal thinking tool to help visualize the structure of your DSL, or to communicate the syntactic rules of your language to other humans.**" Sketch the grammar even if you implement with Delimiter-Directed Translation.

**Relationships.** Notation for Parser Generator; informally for everything else. Its left-recursion constraint shapes Recursive Descent and Parser Combinator and drives Nested Operator Expression. Code actions are Foreign Code, disciplined by Embedment Helper.

> **SDK lens:** Sketching a grammar first is the same discipline as writing type signatures or an IDL before implementing. **Named references beat positional references** — Yacc's `$1`/`$2` versus labels is the argument for keyword arguments over positional and named fields over tuples, with a concrete historical failure to point at. **Returning values up the stack removes shared mutable state.** And **expressive sugar with a defined desugaring is legitimate**: EBNF adds zero power over basic BNF and enormous readability — the argument for convenience layers, provided the desugaring is well defined.

## 4. Regex Table Lexer *(Ch. 20, by Rebecca Parsons)*

**Intent:** "Implement a lexical analyzer using a list of regular expressions."

**Concept.** "By using a separate pass to recognize these terminal symbols, we simplify the construction of the parser." Lexers "stay firmly in the space of regular languages, which means we can use standard regular expression APIs." A Regex Table Lexer is literally a two-column table: pattern → token type.

**Mechanics.** *Scanning:* anchor regexes to the start of the remaining string; walk the recognizer list in order; on match, emit, advance, and **return to the beginning of the list**; if nothing matches, lexical analysis fails. *Ordering is a design decision* — keywords are checked before identifiers, because keywords also match the identifier rule. *Token-set selection is a design decision* — Parsons deliberately uses one identifier token for both names and four-character codes: "the lexer doesn't have the context to know that a four-letter name should match the identifier token, if it isn't in the position where a code is legal" (Fowler's `FAIL FZ17` conclusion, reached independently). *Each recognizer holds three things:* token type, regex, and a **Boolean saying whether to emit** — that flag is how whitespace and comments are dropped before the parser sees them. Add line and column to each token for diagnostics.

**The structural point:** "The implementation is split into the specification of the tokens to recognize and the lexical analysis algorithm itself." Adding a token type is a data change, not a code change.

**When to use.** Nearly unconditional. "While lexical analysis generators, such as Lex, do exist, there is little need to use them given the prevalence of regular expression APIs" — the exception being a Parser Generator that integrates lexing tightly. "**The only time I would suggest not using Regex Table Lexer would be if there is no acceptable regular expression API available.**" And a shortcut: "As long as the language is regular, this approach applies for the parser as well" — **if your DSL is a regular language, the lexer may be the entire implementation.**

**Relationships.** Shared front end for Recursive Descent and Parser Combinator; alternative to a generated lexer. Its first-match-wins ordering is the mechanism behind the keyword/identifier conflicts Alternative Tokenization resolves.

> **SDK lens:** The archetype of **table-driven design — varying data plus one generic engine**; adding a case is a data change. That is the shape you want for extensible registries, dispatch tables, rule catalogs, plugin manifests. **Ordered matching with first-match-wins** is a simple, explainable resolution rule: when registry entries can overlap, define and document ordering (more specific first) rather than leaving it emergent. **Filter at the earliest layer that can do it correctly** — but only where that layer has enough context to be right. And **carry provenance through every intermediate representation**: line/column exist purely so errors can point at the source.

## 5. Recursive Descent Parser *(Ch. 21, by Rebecca Parsons)*

**Intent:** "Create a top-down parser using control flow for grammar operators and recursive functions for nonterminal recognizers."

**Concept.** "A Recursive Descent Parser supports the flexibility of an external DSL without requiring a Parser Generator" — no new tools, no complicated build. One function per nonterminal; control-flow operators implement grammar operators.

**Mechanics.** Consumes a token stream from a lexer. "There is a method for each nonterminal symbol… **The method returns a Boolean value which represents the result of the match.**" Failure propagates up the call stack; each method advances the token pointer as it matches.

| Grammar rule | Implementation shape |
|---|---|
| `C : A \| B` | try `A`; if matched, succeed; else try `B`; else fail |
| `C : A B` | if `A` matched, then if `B` matched, succeed; else fail |
| `C : A?` | try `A`; succeed either way |
| `C : A*` | loop `A` until it fails; always succeed |
| `C : A+` | require one `A`, then loop; fail if the first did not match |

The alternative implementation "clearly checks one alternative and then the other, acting more like an ordered alternative. If you truly need to allow for the ambiguity introduced by unordered alternatives, it might be time for a *Parser Generator*."

**Two invariants make it work — a transactional discipline.**
1. **Token buffer management.** On match, advance past the match; on failure, restore the buffer to its entry position. "Managing the buffer thus allows alternatives to be properly handled."
2. **Model/tree population.** Each method manages its own model pieces, and "**actions must be deferred until the entire sequence completes**."

No side effects until the match is confirmed; exact state restoration on failure. This is why disciplined backtracking parsers don't corrupt their output and ad-hoc ones do.

**The grammar is still there.** "A grammar clearly exists in the methods. Changing the methods changes the grammar. The difference is not in the presence or absence of the grammar but in how the grammar is expressed."

Single-pass translation means helpers "must allow for a reference to a state that has not yet been defined. **This property holds true for all the implementations that don't use *Tree Construction*.**"

**When to use.**
- **Strengths:** "The greatest strength of Recursive Descent Parser is its simplicity." A parser in an ordinary class — no build step, no foreign toolchain. "Testing approaches work in the same way they always do; in particular, a unit test makes more sense when the unit is a method." Ordinary debuggers work. **Weaknesses:** "The most serious shortcoming … is that there is no explicit representation of the grammar." No left recursion, so Nested Operator Expressions get messy. Performance inferior to a generator, though "in practice, these disadvantages aren't such a factor for DSLs."
- **The practical tripwire — look-ahead:** "Generally, I wouldn't use Recursive Descent Parser for a grammar that requires more than one symbol of look ahead; such grammars are better suited to Parser Generators."

**Relationships.** Consumes a lexer (§4). Handwritten sibling of Parser Combinator (§6). Constrained by BNF's left-recursion limit (§3), which makes §15 painful. Some generators emit recursive descent parsers because they're easy to follow while debugging a grammar.

> **SDK lens:** **"The grammar exists whether or not you write it down."** Your library has a protocol, schema, or state machine regardless; the only choice is explicit and reviewable versus implicit and scattered. **Transactional semantics on failure:** any operation that can partially succeed should fully commit or fully restore. **Ordinary code has ordinary tooling** — normal tests, debuggers, stack traces, refactoring: the standing argument against introducing codegen for problems small enough to solve directly. And **define your complexity tripwire before you start**: "more than one symbol of look-ahead → use a generator" is checkable in advance, and every hand-rolled component deserves an equivalent.

## 6. Parser Combinator *(Ch. 22, by Rebecca Parsons)*

**Intent:** "Create a top-down parser by a composition of parser objects."

**Concept.** "The most obvious issue [with generators] is the additional steps in the build process." A Parser Combinator implements a grammar as a structure of parser objects composed with *Composite*. "**Effectively, parser combinators represent a *Semantic Model* of a grammar.**" "Combinators are designed to be composed to create more complex operations of the same type as their input."

**Mechanics.** Base cases are terminal recognizers; operator combinators (sequence, alternative, optional, list) build up production rules — one combinator per nonterminal, mirroring recursive descent's one function per nonterminal. A combinator accepts the match status so far, the token buffer, and accumulated action results, and returns the same three. Same invariant as recursive descent: on success the tokens are consumed; on failure "the combinator returns an unaltered token buffer." *Actions:* terminals populate a match value and invoke the action; sequence/list combinators call their action on the *list* of component match values; alternatives run only the selected branch's. "**The challenge is getting the proper action methods associated with the combinator.**" With closures, pass the function to the constructor; without, subclass the operator class and override the action method.
- **The central insight:** "While a *Recursive Descent Parser* combines those fragments with function calls in inline code, a Parser Combinator combines these by linking together objects in an *Adaptive Model*." Same algorithm; composition moves from code into a runtime object graph.
- **Where the power comes from:** `C : A B` becomes a *declaration* — `C = Sequence(A, B)` — "where the logic implementing the sequencing is shared across all such rules."
- *Functional style:* thread the result value (buffer state, match status, action results) through pure functions — "in this style, the saves are unnecessary since the input parameter's value remains valid." Nothing to restore because nothing was mutated.
- *Two structural details worth stealing:* every recognizer opens with a **guard clause** returning immediately if the inbound status is false, so failure short-circuits a whole composite; and the base combinator carries an **action hook with an empty default body**, so domain behavior lives only in a few rule-specific overrides. A judgement call from the same example: separate classes for optional and required sequences "rather than introducing an optional operator and adding another level of production rules" — **the implementation structure may differ from the canonical grammar structure when that makes the grammar simpler.**

**When to use.**
- "This approach occupies a nice middle ground between *Recursive Descent Parser* and using a *Parser Generator*." **Explicit grammar without the build cost** — "the combinators can be defined declaratively."
- **Language fit:** "Functional languages are an obvious choice… However, implementations in other languages are quite possible too." **Same top-down restrictions** as recursive descent (no left recursion, look-ahead limits, weaker performance); **same debugging advantages.**
- **The layering payoff:** "the Parser Combinator approach coupled with an operator library or tested operator implementations allows the language implementer to focus on the actions rather than the parsing."
- **Downsides:** "you still have to build it yourself," and you get none of a mature generator's sophisticated parsing and error handling.

**Relationships.** Middle ground between §5 and §7. Structurally an Adaptive Model (§18) configured by a grammar. The natural implementation for a generator that interprets a grammar at runtime.

> **SDK lens:** The most directly transferable chapter in the parsing section — a combinator library is a template for composable API design: (a) a small set of primitive values, (b) operators taking values of the type and returning the same type, (c) closure under composition, (d) a uniform result type threaded throughout. **Same-type-in / same-type-out is the constraint to protect above all others**; the moment an operator returns a different type, composition stops. Implement logic once per operator instead of duplicating control flow at every case (query builders, validators, middleware chains, retry policies, stream pipelines). Prefer **threaded explicit state over ambient mutable state**; use **hook methods with no-op defaults**; let **guard clauses propagate failure through a composite for free**. And note that **language capability determines the ergonomic surface** — closures mean "pass the behavior in," no closures means "subclass and override"; when porting an SDK across languages the model transfers but the idiom must be adapted.

## 7. Parser Generator *(Ch. 23)*

**Intent:** "Build a parser driven by a grammar file as a DSL."

**Concept.** "Once you have a grammar, it's tedious work to turn it into a handwritten parser, and tedious work should be done by a computer." Update the grammar, regenerate. The generated parser can use efficient techniques that are hard to maintain by hand. Note the reflexive structure: the grammar file is a DSL and the generator is its code generator — the book's favourite worked example of a DSL that has paid for itself over decades.

**Mechanics.** Write a grammar in your generator's BNF dialect, generate parser source, compile it with the rest of your code. "Don't expect any standardization here; if you change your Parser Generator, you will have to write a new grammar." Treat generated code as a black box, except when debugging a grammar — then there's an advantage in a generator that emits a recursive descent parser. **Codegen vs interpretation:** "There's no reason, of course, why a Parser Generator shouldn't be able to read a grammar file at runtime and interpret it, perhaps by building a *Parser Combinator*. Parser Generators use code generation due to a mix of tradition and performance considerations."

**Embedding actions.** Code goes in the grammar as Foreign Code; "where we place it in the grammar indicates when the code is executed." Refer to elements by name, not position. Embedded code is usually in the same language as the generated parser. "**A common and useful facility is thus to allow a subrule to return data to its parent** … it can remove a lot of *Context Variables*"; some generators also push arguments down into subrules.

**The dominant failure mode, and its fix.** "A common problem I've seen is to put too much host code in the grammar. When this happens, it's hard to see the structure of the grammar and the host code is difficult to edit — and requires a regeneration to test and debug. **The key pattern here is *Embedment Helper* — shift as much code as you can to a helper object. The only code in the grammar should be single method calls.**"

**Semantic predicates**, restated: "like an action, a block of Foreign Code, but it returns a Boolean that indicates whether the parse for the rule succeeds or fails. **Actions don't affect the parsing, but semantic predicates do.**" For a DSL you control, needing one means redesigning the DSL.

**The documented silent-failure traps.** "It's good to get a really simple thing going just to ensure you know what the moving parts are and how they fit together." Two places where a mature tool's default is to **silently succeed on bad input**:
1. **Define a catch-all illegal-character lexer rule, last.** Without it "the lexer … quietly ignore[s]" tokens that fit no rule instead of reporting an error.
2. **Put end-of-file at the end of the top rule.** "If you don't put the EOF at the end of the top rule, ANTLR won't report errors. **It effectively stops parsing at the first point of trouble and doesn't think anything went wrong.**" Particularly awkward because the tool's own interactive interpreter *will* show the error.

And the third, about testing, which is the important one: a test that runs the parser over *valid* input and passes "isn't very helpful. All it indicates is that the ANTLR parser didn't blow up when it read the file… **So it's useful to feed the parser some invalid input.**" That test will initially fail to fail, because "ANTLR is determined to keep on parsing and recover from errors as much as possible." The fix: override the error-reporting hook to record errors, then throw if any were recorded.

*Build notes:* keep generated sources in their own directory, out of source control; keep a handwritten wrapper class to orchestrate the generated lexer and parser.

**Delegation vs Generation Gap for attaching your helper.** Either declare the helper as a field on the generated parser and delegate, or hand-write an abstract superclass the generated parser extends (which also lets the superclass own error reporting). "**Both … have their strengths for the Embedment Helper. I don't have a strong opinion on the best one to use.**"

**When to use.**
- "**The greatest advantage of using a Parser Generator is that it provides an explicit grammar to define the syntactic structure of the language you're processing. This is, of course, the key advantage of using a DSL.**"
  More features and power than a handwritten parser (start with a simple subset and work up), plus good error handling and diagnostics out of the box.
- **Downsides:** there may be no generator for your language, and it's not something you should write; you may balk at a new tool; and codegen complicates the build, "which can be a significant irritant."

**Relationships.** Far-right end of the explicitness spectrum. Consumes BNF (§3) and Foreign Code (§13); disciplined by Embedment Helper (§25); can be structured with Generation Gap (§28). Runtime-interpretation alternative is Parser Combinator (§6).

> **SDK lens:** "Tedious work should be done by a computer" — with the price named: a declarative source of truth and regeneration-on-change, paid for with a new tool, a more complicated build, and black-box generated code. **The runtime-interpretation alternative is always available**: when tempted by codegen, ask whether an interpreted or combinator implementation yields the same declarative artifact without the build step. **Keep the escape hatch in any declarative artifact thin** — logic embedded in a spec cannot be unit tested without regenerating. And **design for loud failure**: a library whose default is tolerant recovery must make strict mode easy and obvious. **Test with invalid input, not just valid input** — "all it indicates is that the parser didn't blow up" applies to every parser, deserializer, validator, and config loader an SDK ships.

## 8. Choosing a parsing strategy

| | Delimiter-Directed | Recursive Descent | Parser Combinator | Parser Generator |
|---|---|---|---|---|
| Grammar explicit? | No grammar at all | Implicit in functions | Explicit as composed objects | Explicit as a BNF DSL |
| Learning curve | Lowest — familiar techniques | Grammar concepts, simple algorithm | Grammar + combinator library | Grammar + a new tool |
| Build complexity | None | None | None (maybe a library) | Codegen step; "a significant irritant" |
| Debuggability | Ordinary code | Ordinary code, easy to trace | Ordinary code + object graph | Black-box generated code |
| Handles complexity | Poorly; messy fast | Simple grammars; ≤1 symbol look-ahead; no left recursion | Same top-down limits as recursive descent | Best: ambiguity, performance, error recovery |
| Error handling | Roll your own | Roll your own | Roll your own | Mature, out of the box |
| Verdict | Only for simple autonomous statements, or a team not ready for grammars | The simplest thing that is a real parser | "A nice middle ground" | Right for complex or ambiguous grammars, or when you want the explicit grammar most |

**The decision tripwires**, each checkable before you have written much code:

- Your ad-hoc line processing **starts wanting a framework** → you are most of the way to Syntax-Directed Translation anyway; go there *(Ch. 17)*.
- Your grammar needs **more than one symbol of look-ahead** → Parser Generator *(Ch. 21)*.
- Your grammar is genuinely **ambiguous** and you need unordered alternatives → Parser Generator *(Chs. 21, 22)*.
- **Left recursion or nested operator expressions** matter → not a top-down parser *(Chs. 19, 21)*.
- Your DSL is actually a **regular language** → a Regex Table Lexer may be the entire implementation *(Ch. 20)*.
- You find yourself needing a **semantic predicate** for a DSL you control → redesign the DSL instead *(Ch. 18)*.

Principles recurring across all seven: layer with honest capability boundaries and never push a decision into a layer lacking the context to make it correctly; make the structure explicit, or accept it is implicit and still there; keep the declarative artifact thin; prefer composition to duplication; use transactional semantics on failure, or thread state so there is nothing to restore; prefer named references to positional; prefer explicit data flow to ambient context; fail loudly by default; apply the same naming and extraction discipline to specs that you apply to code.

---

# Producing output from a parse

A parser only *recognizes*. Three strategies produce a result, plus four supporting tactics. **The Semantic Model is the centre of gravity**, and each tactic is judged by whether it keeps the grammar clean and the model-population code understandable.

## 9. Tree Construction *(Ch. 24)*

**Intent:** "The parser creates and returns a syntax tree representation of the source text that is manipulated later by tree-walking code."

**Concept.** Don't throw away the structure the parse implicitly builds — assemble an explicit tree, then walk it as many times as you like, most commonly to populate a Semantic Model. Critically, build an **AST, not a parse tree**: a deliberate simplification tuned to how you intend to use it. Block keywords earned their keep during lexing but are clutter once structure exists as a tree. And the AST is *purpose-relative* — "obviously, different ASTs might be needed for different reasons."

**Mechanics.** Two ways to build the tree: *code actions in the grammar*, where each rule's action constructs its node and attaches the nodes returned by subrules — the code is "very regular—indeed rather boring," and **boring code usually means you need another abstraction**; or *a tree-construction DSL supplied by the generator*, a rewrite notation declaring the node shape each rule produces, which is exactly that missing abstraction (such tools hand you the raw parse tree if you supply no rewrite rules — "but you almost never want the parse tree"). Build **generic** nodes, not domain objects: "I prefer to have a generic AST and then use second-stage processing to transform that into a Semantic Model. **I'd rather have two simple transformations than one complicated one.**" Second stage in phases: build AST → walk to build **symbol tables** (name → element) → walk again to assemble the Semantic Model, resolving names.

*Design points from the example:* **push ambiguity to the layer that has context** (one token type for names and codes; the parser no longer catches a malformed code, so that check moves into semantic processing — a deliberate, acknowledged trade); keywords as literals in parser rules read better than named lexer rules; **don't add statement separators until you need them**; skipping whitespace loses line/column, so use a **hidden channel** — **discarded input is still needed for diagnostics; route it somewhere rather than dropping it**; keep tree rules simple, "collecting together appropriate clumps of the DSL and putting them under a node that describes what that clump represents."

**When to use.** Decision factors:
- **Complexity of the transformation** — "the more complex the transformation is, the more useful an intermediate model can be." **Multiple passes.** The big one. If you need several passes — most commonly for **forward references** — Tree Construction wins easily; Embedded Translation is stuck with one pass and find-or-create tricks.
- **Parser Generator support** — some tools remove the choice; easy AST building tips the balance. **Memory** — stores the AST, but "in most cases … this won't make any appreciable difference." **Reuse** — process the same AST several ways for different Semantic Models. **Side-effect safety** — a tree action only returns a subtree, so it cannot fire at an unexpected moment.

**Relationships.** Alternative to §10 and §11. Uses Foreign Code (§13) when built with code actions. Embedment Helper (§25) normally keeps the grammar thin, though Fowler skips it when tree-building actions are trivial. Reduces the code-action mangling of §15.

> **SDK lens:** **Two simple transformations beat one complicated one** — wire format → normalized IR → domain object, rather than deserializing straight into rich domain types. Each stage is independently testable, and the IR is where validation, diagnostics, and multiple back ends can stand. A generic IR buys **re-targeting**: one parse, many outputs (validator, formatter, doc generator, executor). **Multi-pass resolution is the answer to forward references** — if your builder or config API lets users reference things declared later, you need collect-then-link, not a streaming pass, and retrofitting it is painful. **Boring, highly regular glue code is a missing abstraction.** And preserve source positions even for tokens you discard.

## 10. Embedded Translation *(Ch. 25)*

**Intent:** "Embed output production code into the parser, so that the output is produced gradually as the parse runs."

**Concept.** Model-population code lives *inside* the parser: as each clause is recognized, an action creates or updates Semantic Model objects. One pass, no intermediate tree. With a generator this population code is Foreign Code woven into the grammar file.

**Mechanics and hazards.**
- **The side-effect hazard.** Actions with side effects "can often be executed in unexpected places, depending on exactly how rules are recognized by the parsing algorithm." Rule of thumb worth memorizing verbatim: **"If you find yourself getting into a tangle with Embedded Translation side effects, that's a sign that you should switch to Tree Construction."**
- **Hierarchic context.** Don't think of it as SAX processing of XML — that's "misleading, because Parser Generators can give you much more context during the execution of the code so you don't need to keep it around yourself." Where the tool lets you pass parameters into rules, **prefer parameter passing to a context variable.**
- **Forward references.** No multi-pass option, so use an **"obtain" (find-or-create) operation** applied to *both* references and declarations. Cost: a misspelled name silently produces a blank object. "It's common, however, to check declarations against usage," tracking states created by use and ensuring all are declared. Some context defeats the tool regardless (e.g. "the start state is the first state mentioned" needed "what is effectively a context variable"). Constructs appearing before there is anything to attach them to get accumulated in a field and applied after the parse — post-parse cleanup is normal and is where **semantic analysis** naturally lives.

**When to use.**
- **For:** "The biggest appeal … is that it provides a simple way to handle both syntactic analysis and model population in one pass." With Tree Construction you write tree-building *and* tree-walking code; "particularly for simple cases, which many DSLs are, this two-stage process can be more trouble than it's worth."
- **Against:** it **encourages complex grammar files**, "usually due to a poor use of Foreign Code." An Embedment Helper mitigates this, "but a strength of Tree Construction is that it helps to enforce the discipline." **Tree Construction makes the good structure the default; Embedded Translation makes it a matter of willpower.** Single-pass only. "The better the tree-building features of your Parser Generator the more appealing Tree Construction becomes."
- **Summary rule:** "the simpler the language and parser, the more appealing is Embedded Translation."

**One observation to carry beyond this chapter.** "Most of the time, the BNF rules don't vary if you use different parsing patterns; what changes is the supporting code around the BNF." **The grammar is the stable asset; the output-production strategy is a swappable layer** — which makes choosing among these three a reversible decision.

**Relationships.** Direct alternative to §9. Depends on Foreign Code (§13) and on Embedment Helper (§25) to keep actions to a single call.

> **SDK lens:** **Streaming, one-pass APIs trade simplicity for expressiveness.** A SAX-style or event-callback API is cheap and fast, but every cross-cutting relationship becomes hidden mutable state in the consumer; if your format has forward references or hierarchic context, a document/tree API serves users better. **Find-or-create is the standard trick for forward references in one-pass builders** — and carries the standard cost that typos become silently created empty objects, so add a "declared versus merely referenced" audit at the end (config loaders, identity maps, DI containers, resource-graph tools). **Push context down as explicit parameters rather than parking it in shared mutable state.** And: **callbacks with side effects can fire at surprising times** — if your API invokes user callbacks from inside a speculative process, document it or restructure so callbacks return values.

## 11. Embedded Interpretation *(Ch. 26)*

**Intent:** "Embed interpreter actions into the grammar, so that executing the parser causes the text to be directly interpreted to produce the response."

**Concept.** No model — an *answer*. "Embedded Interpretation works by evaluating DSL expressions as soon as possible, collating results together, and returning the overall result." Each rule's action combines the values returned by its subrules; `1 + 2 * 3` collapses to `6` then `7` as the parse proceeds.

**When to use.** The pattern Fowler least recommends.
- "I'm a big proponent of a *Semantic Model*, so I don't usually favor Embedded Interpretation—it is useful when you have relatively small expressions that you just want to evaluate and run."
- "Sometimes, building a Semantic Model just isn't worth the overhead. But I find this is a rare case."
- The clinching argument: **"a Semantic Model provides a stronger foundation if the language grows."** The cost is paid the first time the language needs a feature requiring more than one fragment at a time.
- The one good fit is the calculator, where "the syntax tree for arithmetic is a perfectly good Semantic Model." **The test: use it when the syntax tree already *is* the domain model.**

**The methodological warning** — the most important paragraph in the chapter, and not about the pattern at all:
> "The big problem with using arithmetic expressions as examples is that they force you to deal with a rare problem (Nested Operator Expression) but avoid the common DSL-related problems that encourage the use of Semantic Model and Embedment Helper."

**The canonical tutorial example teaches the rare problem and hides the common ones.** Carry that warning beyond DSLs.

**Relationships.** Third alternative to §9 and §10. Entangled with Nested Operator Expression (§15) in the calculator case. Deliberately skips the Semantic Model, which is the whole argument against it.

> **SDK lens:** Eager evaluation with no intermediate representation is the **"just give me the answer" API** — right for a one-shot evaluator (template expression, filter predicate, unit conversion), wrong for anything you will later inspect, cache, optimize, serialize, explain, or partially evaluate. Ask Fowler's question: **does your syntax tree already serve as your domain model?** Note that "a stronger foundation if the language grows" is the argument for keeping a representation layer even when today's use case doesn't need it — but only because the cost of that layer is small, not as a blanket "always add a layer."

## 12. Choosing an output strategy

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

1. **Complexity of the transformation.** The more complex, the more an intermediate model earns its keep — "two simple transformations rather than one complicated one" *(Ch. 24)*.
2. **Number of passes and forward references.** Decisive. Multiple passes are trivial with a tree and impossible without one. If your language permits forward references, Tree Construction is the honest answer and everything else is a workaround.
3. **Tooling.** "The better the tree-building features of your Parser Generator the more appealing Tree Construction becomes" *(Ch. 25)*; some tools remove the choice.
4. **Side-effect tangles.** Embedded actions fire at moments the parsing algorithm chooses. Getting tangled in that is itself the signal to switch *(Ch. 25)*.

Fowler's default: **build a Semantic Model** — so Tree Construction or Embedded Translation, not Embedded Interpretation. Choose between the first two on complexity, pass count, and tool support. Switch from Embedded Translation to Tree Construction the moment side effects or forward references get tangled.

## 13. Foreign Code *(Ch. 27)*

**Intent:** "Embed some foreign code into an external DSL to provide more elaborate behavior than can be specified in the DSL."

**Concept.** Two responses when a script needs something the DSL cannot express: extend the DSL, or open an escape hatch. "Taking this path [extending] may significantly complicate the DSL, removing much of the simplicity that makes it appealing."

**Mechanics — two questions.**
1. *How do we recognize and weave in the foreign pieces?* The grammar marks the spots; because your grammar cannot see inside the foreign code you usually need Alternative Tokenization (§14) to read the whole fragment as one string. Then either embed the raw string in the Semantic Model, or hand it to a separate parser — the latter "is more involved—it's something you'd only consider if your Foreign Code is another DSL." Fowler declines to parse it in his example: parsing catches only *syntactic* errors, not the semantic ones that matter.
2. *How do we execute it?* "The biggest issue lies in whether the Foreign Code can be interpreted or needs to be compiled." Interpreted is easiest if the interpreter interoperates with the host, though "it's usually a bit fiddly, especially when it comes to moving data around." Embedding the compiled host language adds a compilation step — free if you already generate code; "the complexity matters if you're compiling code while interpreting the Semantic Model."

**The discipline rule.**
> "Whenever you use general-purpose Foreign Code, you should seriously consider using an *Embedment Helper*. That way, the only Foreign Code in your DSL script should be the minimum required for the context within the DSL… One of the big problems with Foreign Code is that a lot of foreign code can overwhelm the DSL, thus losing most of the advantages of readability that the DSL offers. Embedment Helper is an easy technique and is worth it in all but the smallest cases."

**Craft points from the example.** The foreign language was chosen by **deployment cycle**, not preference — an interpreted language so rules could be evaluated at runtime without recompiling. The fragment is stored as an **opaque string** in the Semantic Model, evaluated at match time with the candidate injected into scope. **Self-reference:** "the code actions in a grammar are an excellent example of Foreign Code." **Delimiter selection** matters — braces break if the embedded code contains braces; fixes are an unlikely delimiter pair or a push-down lexer allowing balanced nesting, still defeated by a brace inside a string literal ("it should do for most cases"). **Naming:** full labels for tokens, abbreviations for subrule labels — **a name should add information; a name that restates the type is noise.** **Where to populate the model:** a child rule *returns a list of objects* rather than populating the model, so the parent does it — "I prefer to do all the Semantic Model in the one place." **Error handling:** a Notification collects per-token errors and the driver throws after the whole parse, so users see all errors.

**When to use.** Always framed as **Foreign Code versus extending the DSL.** Costs: "you are breaking the abstraction that the DSL gives you"; readers must understand two languages; it complicates parsing and probably the model. Cost of the alternative: "the more powerful the DSL, the harder it is to understand and use." Three cases lean toward Foreign Code:
1. **You genuinely need a general-purpose language.** "You certainly don't want to turn your DSL into a general-purpose language."
2. **The capability is needed very rarely.** "A rarely used capability may not be worth extending the DSL for."
3. **Audience.** "If the DSL is only used by programmers, then adding Foreign Code is not a problem… If nonprogrammers will read the DSL, that argues against Foreign Code as they may not be able to understand, and thus engage with, the foreign code."

**Relationships.** Requires Alternative Tokenization (§14); should almost always be paired with Embedment Helper (§25). The mechanism underneath §10 and §11 with a generator; recommended in §17 as the practical substitute for modular grammars.

> **SDK lens:** This is **escape hatches in declarative APIs**, and the analysis transfers unchanged. Every declarative config format eventually faces "we need a general-purpose language here," with the same three choices: extend the config language until it becomes a bad programming language, embed a real language, or provide a plugin interface in the host language. **The audience test is the sharpest tool**; **the rarely-needed-capability test** is the other — don't grow the core surface for a long-tail need, give it an extension point. **Runtime-eval versus compile-in maps directly to plugin architectures.** Keep the escape hatch narrow via a helper API; **store the foreign fragment opaquely** rather than half-parsing a language you don't own; and **collect errors into a notification and report them all**.

## 14. Alternative Tokenization *(Ch. 28)*

**Intent:** "Alter the lexing behavior from within the parser."

**Concept.** "There are times when the way the lexer does the tokenizing should change depending on where we are in the parse tree—meaning that the parser has to manipulate the way the lexer does the tokenizing." The motivating case: `item small white item;` — users want spaces in names, but the lexer sees the word `item` and returns a keyword. What you want is: **everything between the `item` keyword and the terminator is name text, whatever it looks like.** The other pervasive case is Foreign Code.

**The four techniques**, each with a distinct failure mode.

1. **Quoting.** The quoting rule "gobbles up all the text between the delimiters, so it is never touched by the other lexer rules." Key limitation: "**Quoting doesn't involve the parser at all, so a quoting scheme has to be used everywhere in the language. You can't have specific rules for quoting particular elements.**" A global decision, not a contextual one. Handling embedded delimiters: **escaping** (works well, "but it may be confusing, particularly to nonprogrammers"); **unusual delimiters** ("only as good as the unlikeliness of its use"); **multiple delimiter kinds**; **balanced nesting via a push-down lexer** (still defeated by a brace inside a string literal; "you can only do it if the lexer is a push-down machine, which is relatively rare").
2. **Lexical State.** "Perhaps the most logical way of thinking about this problem": switch lexer modes at the keyword, switch back at the terminator; the parser drives the switch through actions. **The catch — parser lookahead versus lexer state.** "Even one token of look ahead breaks this": the first word is lexed before the state change takes effect. Ordering matters too — reset the state *before* the separator is recognized. "Combining parsing and lexical states can easily get pretty messy." Tools that pre-tokenize the whole input cannot do it at all.
3. **Token Type Mutation.** "The parser's rules react not to the full contents of the token, but to the token's type." Change the type before it reaches the parser. **The mirror image of lexical state:** needs the ability to look ahead in the token stream, so it suits pre-tokenizing tools and not one-token-lookahead ones. Downside: "**This technique doesn't capture exactly what was in the original text, as anything that the lexer skips won't be offered up to the parser. For example, whitespace isn't preserved… If that's an issue, then this technique isn't the right one to use.**"
4. **Ignoring Token Types.** "If the tokens don't make sense and you want the full text, you can ignore the token types completely and grab every token until you reach a sentinel token." Trivial with a negation operator; without one you must enumerate all keywords. With Tree Construction, collect them into a single list node.

**When to use.** Relevant with Syntax-Directed Translation and a separate lexer — "which is the common case." Consider it "when you have a section of special text that shouldn't be tokenized using your usual scheme." Three triggers: **keywords that shouldn't be keywords in a particular context**; **allowing any form of text** (prose descriptions); and **Foreign Code**.

**Relationships.** Prerequisite for Foreign Code (§13). Interacts badly with Newline Separators (§16) — Fowler uses visible separators here "to deal with one tricky issue at a time." Offered in §17 as the constrained workaround for modular grammars. Exists entirely because of the lexer/parser boundary (§2).

> **SDK lens:** The **context-sensitive input problem** in any format library — a field whose contents must not be interpreted by the enclosing parser (raw markup blocks, template literals, embedded SQL/JSON, free-prose fields). The four techniques map onto four API choices: require quoting/escaping (simple, global, pushes burden onto users); switch modes by position (contextual and pleasant, but bad with lookahead and streaming); post-process the token stream (loses skipped input); or take everything up to a sentinel (simplest and most robust when a clean terminator exists). **Round-trip fidelity is a first-class requirement** — if your library must reproduce input (formatters, autofixing linters, config rewriters), choose the technique that keeps every character. And **design for the non-programmer's input habits**: accommodating natural text costs real parser complexity; decide deliberately rather than defaulting to identifier rules.

## 15. Nested Operator Expression *(Ch. 29)*

**Intent:** "An operator expression that can recursively contain the same form of expression (for example, arithmetic and Boolean expressions)."

**Framing.** "Calling Nested Operator Expression a pattern is a bit of a stretch, since it isn't so much a solution as it is a common problem in parsing." *(Correction to note: the chapter's opening suggests left recursion is a problem "particularly with bottom-up parsers," but the body demonstrates the opposite — bottom-up parsers handle left recursion fine; **top-down** parsers must eliminate it. Read the body, not the intro.)*

**The two difficulties:** **recursion** (the rule appears inside its own body) and **precedence** (`1 + 2 * 3` must mean `1 + (2 * 3)`), plus **associativity**, which must be declared even where it seems not to matter.

**Bottom-up parsers.** "The easiest to describe." One production rule with one alternative per operator plus a base case; recursion is direct and the grammar reads like the language. Precedence is declared *separately* as an ordered list of levels with associativity; a **ghost token** that never appears in the input gives unary minus a different precedence from binary minus. Why declarations are needed at all is **ambiguity**: "Without the precedence rules, a parser with this grammar could parse `1 + 2 * 3` as `(1 + 2) * 3` or as `1 + (2 * 3)`… The same is true for `1 + 2 + 3` even though we (humans) know it doesn't matter." **The parser needs a total order even where the semantics is indifferent.**

**Top-down parsers.** "More complicated" — you cannot write the left-recursive rule, so you build a **cascade of rules, one per precedence level**, which eliminates the left recursion and encodes precedence at once. "The resulting grammar, however, is much less clear. Indeed, this lack of clarity is why many people prefer a bottom-up parser."
- **Left-associative binary:** body starts with a reference to the *next-lower* precedence rule, then a repeating group of (operator, next-lower rule). Never refer to yourself.
- **Right-associative binary:** the right-hand side is a **recursive reference to the rule itself**, and the group is **optional** rather than repeating.
- **Unary prefix:** recurse into yourself when the sign is present; fall through to the next-lower rule when it isn't.
- **Atoms** (literals, parenthesized expressions) sit at the bottom; parentheses reintroduce deep recursion.

**Three consequences of the mangling.** (1) "You're spending your time massaging the Parser Generator rather than expressing intent." (2) The parse tree fills with clutter — each operand carries a chain of one node per precedence level. (3) Output production makes it worse: you need an accumulator, and because different operators at one level do different things you must **widen the alternative**, duplicating the right-hand-side reference in each branch. "Tree Construction often reduces this problem."

**Relationships.** Forced on you by §11's calculator — which §11 warns is unrepresentative *because* it drags in this rare problem. Mitigated by §9. Same left-recursion constraint as §3, §5, §6; the strongest argument in the book about which generator to choose.

> **SDK lens:** **Precedence and associativity are ambiguity resolution, not semantics.** Any API accepting user-authored expressions — query filters, rule engines, formula fields, search syntax — must define and document a total precedence order even where order is mathematically irrelevant, because *the parser* needs it. **Your grammar's shape is constrained by your tool**: if the expression grammar must be mangled, budget for a normalization step that collapses the clutter, because tree consumers shouldn't have to know your precedence-cascade node types. And take the meta-lesson: expression parsing is the most over-taught and least representative parsing problem there is — don't design a general library around it.

## 16. Newline Separators *(Ch. 30)*

**Intent:** "Use newlines as statement separators."

**The core difficulty.** Trivial with Delimiter-Directed Translation; with Syntax-Directed Translation it is "rather more tricky, introducing a number of subtle traps."
> "The reason that newline separators and Syntax-Directed Translation don't go together too well is that newlines play two roles when you use them as separators. Apart from their syntactic role, they also play a formatting role in providing vertical space. As a result, they can appear in spaces where you wouldn't expect a statement separator to pop up."

**The four cases that break the naive grammar:** blank lines *between* statements; blank lines *before* the first; blank lines *after* the last; and the last statement having **no end-of-line at all**. The first three are all blank lines but "may need different ways of handling them in the grammar, so should all be tested." The headline advice: "**Making sure you have tests for these cases is probably the most important thing to do.** I've got some solutions for these problems below, but the good tests are the key."

**Three grammar shapes.**
1. **An end-of-statement rule matching multiple newlines.** Logically belongs in the lexer, but the missing-final-newline case forces matching EOF, which the lexer may not be able to do — so a "vertical space" rule (zero-or-more line endings) plus an "end of statement" rule (one-or-more line endings *or* EOF) lands in the parser. Escape hatch: "forcing an end-of-line at the end—either through the lexer (if you can) or perhaps by prelexing… can help avoid a few awkward corner cases." **Normalizing input before parsing is a legitimate and often cheapest fix.**
2. **Treat them as separators rather than terminators** — `statement (separator statement)*` bracketed by optional vertical space. "I've come to prefer this style." Fowler's stated preference.
3. **Statement body as an optional element of each line** — requires explicit EOF matching; an EOF-free variant exists but "doesn't read as clearly."

**Comments — the other trap.** With newlines ignored you can let a comment rule consume the newline. **With newline separators, consuming the newline destroys the statement terminator** — and comments very often sit at the end of a statement. Fix: match everything up to *but not including* the newline. Line continuation: a lexer rule matching the continuation character plus optional whitespace plus the line ending, skipped entirely.

**When to use — two separate decisions.**
- **Should you have statement separators at all?** "The limited structure of a DSL often means that you can live without statement separators. The parser can usually figure out the context of the parse from the various keywords." The argument *for* is **error localization**: "In order for the parser to localize errors it needs some kind of checkpointing marker… Without checkpointing, an error in one line of the script may not be apparent to the parser until several lines later." (Keywords can serve this role too.)
- **If yes, newline or a visible character?** "The nice thing about using newlines is that most of the time, you have one statement per line anyway, so using a newline separator doesn't add any syntactic noise… This is particularly valuable when working with nonprogrammers." The downside is the finickiness above plus mandatory tests. "On the whole, however, I still prefer to use newlines rather than a visible statement separator."

**Relationships.** Trivial with §1; fiddly with §2. §14 deliberately avoids newline separators to isolate one difficulty at a time. §17's syntactic indentation is the next step and much harder.

> **SDK lens:** **Syntax that is invisible to the eye is expensive to implement.** Whitespace-significant formats are pleasant for authors and painful for parser maintainers; price the implementation cost honestly. Fowler's four failure cases are a **ready-made test checklist for any line-oriented format**: leading blank lines, trailing blank lines, interior blank lines, missing final newline — plus a comment at the end of the last line with no trailing newline. **Normalize input at the boundary** so core logic only sees well-formed input. **Checkpointing improves error messages** — design synchronization points into the format or accept vague diagnostics. And note the general smell: **an element carrying two responsibilities invites ambiguity**, and newlines carrying both structure and visual formatting is the archetype.

## 17. Syntactic indentation & modular grammars *(Ch. 31)*

Fowler labels this chapter a hodgepodge of unfinished topics: "the thoughts here are more preliminary than much of the other material in this book" — a model of intellectual honesty worth imitating.

**Syntactic indentation.**
- *The argument:* "The primary form of structure that we read comes from the indentation, not from the delimiters." Since we read structure through indentation anyway, let it *be* the structure. Usability advantage: "The definition and the eye are always in sync—you can't mislead yourself by altering the formatting without changing the real structure." Qualified: auto-formatting editors remove much of that advantage for mainstream languages — "but DSLs are less likely to have that kind of support." **The value is highest exactly where tooling is weakest, which is where DSLs live.**
- *Tabs:* "follow the approach of YAML and forbid tabs from any language that uses syntactic indentation. Any inconvenience you'll suffer from not allowing tabs will be much less than the confusion you avoid." **Eliminate a class of user error by removing the ambiguous input rather than handling it.**
- *Cost lands in the lexer.* Delimiter-Directed Translation is a poor companion, "since syntactic indentation is all about counting the kind of block structure that Delimiter-Directed Translation has problems with."
- *Effective tactic:* **imaginary indent/dedent tokens** — "you just use 'indent' and 'dedent' instead of `{` and `}`," and the parser never knows about indentation. But "doing this in a conventional lexer is somewhere between hard and impossible… you'll probably end up having to write a custom lexer."
- *The alternative Fowler would try first:* **preprocess the input text before it hits the lexer**, inserting textual markers at indentation changes. Two costs: markers must not clash with anything in the language, and you have altered the text the user wrote, which breaks **line/column diagnostics**. "But this approach will greatly simplify the lexing of syntactic indentation."

**Modular grammars.**
- *The motivating principle*, one of the most quotable statements of the book's philosophy: "**DSLs are the better the more limited they are. Limited expressiveness keeps them easy to understand, use, and process. One of the biggest dangers with a DSL is the desire to add expressiveness—leading to the trap of the language inadvertently becoming general-purpose.**"
- *The escape:* stop growing one language; combine several independent DSLs. "Modular grammars would allow you to use reusable grammars in the same way that we currently use reusable libraries." State of the art: "not a well-understood area in the language world… nothing that's really mature as I write this."
- *The obstacle is the separate lexer* — a child grammar usually needs a different lexer than its parent. Alternative Tokenization is a workaround "but that places constraints on how the child grammar can fit in with the parent." **Scannerless parsers** are the promising direction: no separate lexer means no lexer to conflict.
- *Practical advice for today:* "the simplest way of dealing with separate languages is to treat them as *Foreign Code*, pulling the text of the child language into a buffer and then parsing that buffer separately." **Don't compose grammars — compose parsers.** Cost: the outer grammar cannot validate or interleave with the inner one, and error positions must be mapped back manually.

> **SDK lens:** From syntactic indentation: **translate an implicit property into explicit tokens at the earliest boundary** so every downstream layer works with ordinary nesting. **A preprocessing stage is a legitimate architecture but breaks source-position mapping** — you need a source map, the same problem transpilers and template engines face. **Forbid the ambiguous input** (reject ambiguous date formats rather than guessing). From modular grammars: **"limited expressiveness is a feature" is the core API design lesson of the whole book** — prefer several small focused APIs over one that grows to cover everything, and when a surface must cover a new area, ask whether it should be a *separate composable module* rather than new syntax. Watch the structural trap: **anything global and cross-cutting blocks composition** — a global registry, a single shared config schema, or a singleton serializer blocks plugin composition exactly as the lexer/parser split blocks grammar composition. And **opaque embedding is the pragmatic composition mechanism**: take the sub-language as a blob and delegate to its own parser.

---

# Alternative computational models

"Often the desire to use a DSL comes with a desire to use a different computational model" *(Ch. 47)*. One umbrella pattern (Adaptive Model) plus four concrete models typically implemented *as* Adaptive Models. The list is not exhaustive. **The recurring bill: they demo beautifully and scale badly without tooling. Every pattern here needs tracing.**

## 18. Adaptive Model *(Ch. 47)*

**Intent:** Arrange blocks of code in a data structure to implement an alternative computational model.

**Concept.** Ordinarily the flow of processing is dictated by the code; different data changes details but not flow. An Adaptive Model inverts this — "the instantiation of the state model *is* the program." A general Semantic Model of "a state machine" remains as a constant factor and a constraint, but the program that executes is the *configuration*. Fowler's boundary definition: **"the essence of using an Adaptive Model is the sense that you are changing the program by altering the instances and their relationships."** This dissolves the code/data boundary — "for many developers it's a world that's both entrancing and scary."

**Mechanics.** Links between elements represent the computational model's behavioral relationships — states to transitions to target states, rules to conditions and actions, tasks to prerequisites. Run it by **executing code over the model** (procedural — an interpreter walks it) or **executing code within the model** (object-oriented — the model's objects carry run behavior). Adaptive Models often take well-known graph shapes, so algorithms textbooks are genuinely useful reference material. *Forms:* in-memory object model; a data structure interpreted by procedural code; or stored in a database and interpreted by other applications (common in workflow systems, usually with a crude forms-based projectional editor) — a textual DSL instead lets you put the Adaptive Model under version control, and "I find it deeply troubling when core system behavior isn't kept under a proper source code control system."

**Adaptive Model and DSL are independent.** You can have one with no DSL and get most of the benefits. **The DSL's role is to make it easier to program the Adaptive Model.** "One of the hardest parts in using an Adaptive Model is to figure out what it's supposed to do — a DSL can be a big help in overcoming that."

**Incorporating imperative code**, in Fowler's order of preference: **closures** (most direct statement of intent; his cited drawback — many languages lacked them — has largely evaporated, strengthening the recommendation); **command objects** (one small object per condition/action, with the subclass count cut down by **parametrizing** them — `JourneyStartCondition("BOS")` rather than a bespoke class); **method name plus reflection** (disliked: "it circumvents the mechanisms of the underlying environment just a bit too much"). Nuance: commands look like a workaround, but **if you populate the model with a DSL, commands become more attractive**, since the DSL wraps common cases in parameters anyway. Full closure expressiveness means closures in an internal DSL, or Foreign Code in an external one — "the latter, in particular, is something you should use only rarely."

**Tools you must build alongside it.** A DSL is "not really enough to work with an Adaptive Model when it gets more complicated."
- **Tracing.** Capture how the model processed its inputs, leaving a clear log of why it did what it did. This "greatly helps answering the question, 'Why did the program do that?'"
- **Alternative visualizations.** Have the model produce descriptive output of an instance — auto-laid-out state diagrams, reports from different perspectives. "A simple equivalent of the multiple projections of a language workbench," minus editability. **Build them automatically as part of your build process** and use them to check your understanding of the configuration.

**When to use.**
- It is **the key to using an alternative computational model** — any of the models below should be implemented with one.
- He calls that "somewhat of a glib answer," since it begs when you'd want an alternative model at all. That is a **qualitative decision with no rigorous approach**. Best suggestion: try expressing the behavior in a different computational model and see if it makes the problem easier to think about — which often means **prototyping a DSL to drive the model**.
- **The realization can also grow out of the way a framework changes over time** — it begins by storing data, behavior worms in, an Adaptive Model forms.
- **The large disadvantage:** they "can be very hard to understand." The root cause is **implicit behavior** — you can no longer reason about what the program does by reading the code; you must look at a particular configuration. Debugging can be a nightmare, and building tools to help means time not spent on the software's true purpose.

**The sociological failure mode** — the part skipped in most retellings, and the most important paragraph in the chapter:
> "Usually, there are a couple of people around who understand the Adaptive Model. They are big fans of it, and can be incredibly productive by using it. Everyone else, however, steers well clear."

**Sometimes you have to forgo the gains**, because "it's not good to have a magic section in a system that people are fearful of touching. If the few people who understand the Adaptive Model would move on, nobody will be able to maintain that part of the system." His hope is that DSLs alleviate this by making implicit behavior explicit. Note the structure of that hope: **the mitigation for the sociological risk is exactly the tracing and visualization tooling above, plus a readable DSL. If you build the model without the tooling, you have built the scary magic.**

**Relationships.** Umbrella for §§19–22. Uses commands and closures for embedded behavior, Foreign Code (§13) in external DSLs. Parser Combinator (§6) is structurally an Adaptive Model configured by a grammar. Its generated-code counterpart is Model-Aware Generation (§26).

> **SDK lens:** The pattern behind **configuration-driven frameworks, plugin registries, middleware pipelines, and workflow engines** — anything whose behavior is determined by a structure the user assembles rather than control flow the user writes. The two tooling recommendations become **library observability requirements**: a config-driven library must ship a tracing or explain facility ("why did this rule fire? why was this request routed here?") and ideally a dump/visualize facility for the assembled configuration. Build a config-driven API without these and you have built the scary magic. The version-control argument is an API-design argument for **text-based configuration over database-stored or GUI-edited configuration** for anything constituting core system behavior. And take the sociological warning as the honest cost-benefit for "magic" APIs generally — heavy annotation frameworks, DI containers, metaprogramming ORMs — weighing maintainer bus-factor, not just expressiveness.

## 19. Decision Table *(Ch. 48)*

**Intent:** Represent a combination of conditional statements in a tabular form.

**Concept.** **Each column is one combination of conditions and the outcome for that combination.** Condition rows on top, consequence rows below; reading one column gives you a whole rule.

**Mechanics.** With *n* two-valued Booleans you need 2ⁿ columns for full coverage; a table needs only one consequence but can have several. **Three-valued Boolean logic** with a "don't care" third value removes a lot of repetition — implement it **polymorphically with a `matches` method rather than `equals`, because the relation is not symmetric** (don't-care matches true, but true does not match don't-care). **Beyond Booleans:** encoding ranges as Booleans forces the table to know about mutual exclusion; a **single condition row for the value of `x` with ranges typed into the cells** "is usually easier to work with," and with complex condition values it's better to treat unmatched cases as errors than to compute all permutations.
- **Completeness checking is a valuable property.** Columns are enumerable, so you can determine whether all permutations are captured and report the missing ones. Impossible combinations become an *error column*, or define missing columns as errors.
- **How generic to make model and parser is an explicit decision.** A single-case model fixes condition rows in code (though column values stay configurable); a generic one configures condition and consequence types, needs a way to indicate the code evaluating each condition (method name or closure), and in a strongly typed language needs input/consequence types configured at compile time. A flexible parser needs "something akin to a simple grammar for the table structure."
- The parser should operate against a **tiny table abstraction** (cell, row count, column count) rather than a particular spreadsheet mechanism, and should **verify condition row names** so a reordered or renamed table fails loudly instead of silently mis-parsing. A general lesson attached to the completeness-checking code: *"I'm quite happy to use the data structure that makes it easiest to write some code and then transform the result into the data structure I actually want to consume."*

**The spreadsheet angle.** Tables "are very simple to follow, and indeed edit, and so are particularly suited to capturing information from domain experts." Let experts edit in a spreadsheet and import: CSV (crude but often effective — it works because the table is pure values, no formulae), interoperate with a running spreadsheet, or use the spreadsheet's own language to transmit data.

**When to use.**
Very effective for a **set of interacting conditions**; communicates well to programmers and domain experts alike. **Biggest disadvantage:** setup effort for editing and display — "this effort is usually quite small compared to the communicative benefit they provide." **Complexity ceiling:** "Decision Tables can only handle a certain degree of complexity — no more than what you can capture in a single (if complex) conditional expression. If you need to combine multiple kinds of conditionals, consider a *Production Rule System*."

**Relationships.** An instance of §18. Escalates to §21. Its parser is written "in the spirit of Delimiter-Directed Translation but using rows and columns."

> **SDK lens:** The natural shape for **pricing matrices, permission/authorization matrices, feature-flag combinations, and rate or discount schedules**. If your API takes five booleans and returns a policy, a decision table is very likely a better public surface than five nested conditionals or an options object. **Completeness checking is a genuine API feature**: a table-based API can tell the caller "you have not specified what happens when A and B are both true" at configuration time — a guarantee an imperative conditional cannot offer. The **spreadsheet round-trip** is a real integration design, and it works precisely because the table contains only values. The generic-versus-specific decision is the classic tension between a narrow, statically typed, easy API and a general, dynamically configured, harder one; Fowler declines to declare a winner but insists you choose consciously.

## 20. Dependency Network *(Ch. 49)*

**Intent:** A list of tasks linked by dependency relationships. To run a task, you invoke its dependencies, running those tasks as prerequisites.

**Concept.** A **directed acyclic graph of tasks and dependencies**. Requesting a task ensures prerequisites execute first, and — critically — **even if a task is reached more than once via different dependency paths, it executes only once.**

**Task-oriented versus product-oriented — the central design axis.**
- **Task-oriented:** the network is a set of *tasks* with dependencies between tasks (compilation depends on code generation).
- **Product-oriented:** focus on the *products* and dependencies between them (generated source files are a prerequisite to building the executable).

**How it runs.** The requested thing is the **target**; the system collects prerequisites transitively and invokes each in dependency order. **Two failure modes:** a **missed prerequisite** — the most serious, because "everything looks like it works correctly but the data is all wrong because we didn't get a prerequisite" — and an **unnecessary build**, usually just slower "as the tasks are often idempotent. It can cause more serious errors if they aren't."

**Last-modified dates, and invoke versus execute.** Each product tracks when it was last updated; the process runs only if the output is older than a prerequisite — which means prerequisites must be invoked first so they can rebuild.
> **Every transitive prerequisite is *invoked*, but a prerequisite is only *executed* if it's necessary.**

In a **task-oriented** network, last-modified dates are often unused; each task tracks whether it has already executed during the current request.

**The argument for product-orientation:** persistent last-modified dates are easier to work with, which "is a strong reason to prefer the product-oriented style." Task-oriented systems can use last-modified info, but each task must own that responsibility; product-orientation lets the *network* decide on execution.

**The price, stated plainly:** "This capability doesn't come for free; it only works if the output will always be the same if none of the prerequisites change. **Thus everything that could make a change to the output needs to be declared in prerequisites.**"

*In real tools:* Make is product-oriented (products are files); Ant is task-oriented. A real problem with product-orientation is that **there is not always a natural product** — running tests is the classic case; the canonical pseudo-output is a **touch file**, an empty file existing solely for its last-modified date. Implementation note from the example: the behavior lives in the getter — the invocation passes back along the inputs, then each node checks whether it is out of date (no result, result predates its own definition, or an input updated after the result) and recalculates only if necessary.

**When to use.**
Problems you can **divide into tasks with well-defined inputs and outputs**. Suitable for **resource-intensive tasks, or tasks that take an effort to get going — such as remote operations.** **Tricky to debug**, so **log invocations and executions**; that, plus executing only when needed, produces a concrete recommendation: **prefer relatively coarse-grained tasks.**

**Relationships.** An instance of §18, subject to its tracing requirement, specialized to "log invocations and executions."

> **SDK lens:** The model behind **build tools, task runners, and incremental pipeline libraries**. The task-versus-product decision determines whether your library or your users own staleness logic — Fowler's verdict is that product-orientation lets the framework own it. **"Everything that could make a change to the output needs to be declared in prerequisites" is the fundamental correctness contract of any incremental or caching API** — it is why modern build systems demand full input declarations down to tool versions and env vars, and why hidden inputs produce the missed-prerequisite silent-wrong-answer failure. Three corollaries: the **touch-file / pseudo-output trick** is the standard workaround when your API is product-keyed but a task has no natural artifact; **idempotence is what makes the unnecessary-build error benign**, so document idempotence expectations; and **coarse-grained tasks** is good default guidance for public task APIs.

## 21. Production Rule System *(Ch. 50)*

**Intent:** Organize logic through a set of production rules, each having a condition and an action.

**Concept.** Naturally suits **validation** (raise an error if a condition is false), **qualification/eligibility** (a chain of conditions), and **diagnosis** (questions leading to more questions and a root fault). The system runs rules **through a series of cycles**; each cycle identifies matching rules and executes their actions. "A Production Rule System is usually at the heart of an expert system."

**Mechanics.** A rule is a Boolean condition plus an action; the action "may be constrained by context" (a validation-only system's actions just specify which error and what data). The complex part is **deciding how to execute the rules** — and "the fact that a general Production Rule System is very complicated doesn't mean that you can't build a simple Production Rule System for limited cases."

**The rule engine** puts all execution control in one component. A simple engine runs **inference cycles**: run all conditions → each true rule is **activated** → activated rules go on the **agenda** → the engine **fires** the agenda's actions.

**Firing sequence:**
- **Arbitrary sequence** — simplest; write-order does not determine fire-order. "This can help keep the computation simple." **Definition order** — always fire in definition order (email filters: the first matching filter wins).
- **Priority** (*salience*) — highest-priority rule first. **"Using priorities is often considered a smell; if you find yourself using priorities a lot, you should reconsider whether a Production Rule System is the appropriate computational model for your problem."**

Another variation: re-check activation **after each rule fires**, or fire the whole agenda before rechecking — this can change system behavior. **Rule sets** divide the rule base into logical groups evaluated in order (validate basic data first; only if clean, run qualification).

**Chaining.** **No chaining** — validation rules; one cycle suffices because actions don't change the data. **Forward chaining** — actions change state, so conditions must be re-evaluated: "You start with some facts, use rules to infer more facts, these facts activate more rules… The engine stops only when there are no more rules on the agenda." **Backward chaining** — start from a goal, find rules whose actions would make it true, make their conditions subgoals; "less common in simple Production Rule Systems as it's much more involved."

**Contradictory inferences — the hard problem.** "One of the great advantages of rules is that you can state each rule independently and let the Production Rule System figure out the consequences. But this strength comes with a problem." **The biggest danger is that you may not notice at all** — if the consequence sets a Boolean, whichever rule runs last wins, giving "different inferences depending on hidden qualities in the rule execution sequence." Two approaches:
1. **Design the rule structure to avoid contradictions.** Fowler's concrete convention: **start with all eligibility conditions set to false and only allow them to be changed to true.** That monotone discipline forces anyone wanting to *exclude* a group to write the rule differently, "surfacing the potential contradiction while writing the rules." Caveat: "a mistake can sneak in a rule that will potentially subvert the design."
2. **Record all inferences in a way that tolerates contradiction.** Instead of a Boolean, create a **fact object** keyed by conclusion; afterwards look for facts with the same key and different values. The *Observation* pattern is one way.

Also **beware circles** — contradictory rules that keep arguing, and positive feedback loops.

**Three recurring rule structures.** **Validation** — simple consequence, little chaining; "it seemed an overkill to me to use a specialized rules tool for something like this. However, this kind of simple structure is a nice one for you to write yourself." **Eligibility** — "a progression of steps where lower-level rules lead to higher-level inferences"; avoid contradictions by keeping inferences positive. **Diagnostic** — "you're much more likely to get contradictions, so having something like *Observation* is more important."

**Put the smarts in the Semantic Model, not the builder.** The most transferable design principle in the chapter:
> "I want to stress here that I didn't need to change the *Semantic Model* to support this. Instead, I could easily put this code in the builder… **It's often an easy reflex to put this kind of logic in the builder, but I urge you not to fall for it. If I put the logic in the Semantic Model, it will be able to make a much better use of the information, since it knows what it's doing.**"

His example of "better use": a Semantic Model that *knows* a rule is a not-null check can generate client-side validation code to embed in a form; a builder that has flattened the rule into an anonymous predicate cannot — the information is gone. "My preference is to put smarts in the Semantic Model as much as possible. It isn't any more work than putting it in the builder, but it keeps the knowledge of the rules where it's most useful." **General form: don't collapse declared intent into an opaque closure at the API boundary.** A closure is a one-way door — you can call it, and that is all. A first-class model object representing *the kind of thing the user declared* can be called, serialized, rendered in another language, documented, introspected, and optimized.

*Four more design points from the eligibility example:* **rules are open-ended** ("I can easily add new rules… without altering the rules that are already in place"), with the plainly stated downside that "there's no single spot in the rule base text where I can be sure of finding *all* the conditions" — mitigated by tooling that finds all rules with a given consequence; the **data class is deliberately monotone**; the engine keeps a **fired log** (activated rules are removed so they can't fire twice; fired rules move to a log used "to provide a trace for diagnostic purposes") — §18's tracing requirement made concrete; and **null-safety is moved into the engine**, trapping null-reference exceptions as failure-to-activate so rule authors need no null checks.

**When to use.**
- Natural **when behavior feels like a set of if-then statements.** "Just writing control flow like that is often a good starting point for evolving into a Production Rule System."
- **The big danger: they are seductive.** A small example demos well to nonprogrammers. "What isn't clear from simple demos is that it may become very hard to reason about what a Production Rule System is doing as it gets bigger, particularly if you are using chaining."
- **Rule engine tools exacerbate this.** "It's very easy to stretch a tool — to use it in lots of places without realizing how difficult it is to modify until you've already built something too large." Hence: **build something simple yourself**, tune it, learn the domain, and only then evaluate replacing it with a tool.
- The blunt summary: **"I'm not saying that rule engines are always a bad idea, although I've yet to see one that's worked well. What is important is that you should treat them with caution and understand what you are getting into when you use them."**

**Relationships.** An instance of §18; the escalation target from §19. Uses Notification and Observation for error and fact collection.

> **SDK lens:** **Validation libraries, policy and authorization engines, eligibility and pricing-rule services, alerting rules, and lint frameworks** are all this pattern, and "validation is the simple, chain-free case that you should just write yourself" applies directly — most validation DSLs do not need a rule engine. **"Put the smarts in the Semantic Model, not the builder" is arguably the single most reusable API-design rule in this section:** for fluent and builder APIs, resist collapsing user intent into an opaque closure at the builder boundary; keep the *kind* of thing the user declared as a first-class model object and you retain the ability to serialize, render, document, introspect, or optimize it. Four more: **the agenda and fired log are API surface, not implementation detail** — anything rule-driven needs an explain facility; **open-endedness versus discoverability** is the core tradeoff of any plugin or rule-registration API, answered with introspection APIs and registry-dumping commands; **monotone state design** (fields start false and only ever get set true) makes order-independence safe wherever independent extensions write shared state; and the tool-creep warning applies to adopting *any* heavyweight rules or workflow engine as a dependency.

## 22. State Machine *(Ch. 51)*

**Intent:** Model a system as a set of explicit states with transitions between them.

**Machine state versus object state — the chapter's most useful idea.** In general use "the state of an object" means the combination of its property values, so removing an item changes an order's state. But the state diagram shows only a few states: **"These are the states that are interesting in terms of the model, in that they affect the behavior of the system. I'll refer to this smaller set of states as *machine states*."**

**And the judgement call that follows is the "when NOT to build one" advice:**
> "This state model is a useful way of thinking about the behavior of the order, but this doesn't mean that we want a state machine model in our software."
- The model says `cancel` needs a state check — but that can simply be a **guard clause** in `cancel`.
- The current machine state could be a status field, "but it could also be completely derived" — *paid* means the payment authorization is at least the total cost.
- **"The diagram may still be a useful way to visualize how the order works, but you don't need the model to be manifest in the software."**

**Common elements and variations.** The essence: multiple **states**, and multiple **transitions** on each state, each triggered by an **event** and moving to a **target state**; multiple transitions may share a target and still be separate transitions.
- **Unhandled events:** "A general question with state machines is how they react to an event that isn't defined on the state that the machine is currently in. Depending on the application, such an event may be an error, or it may be safely ignored." A design decision the model must make explicit.
- **Guarded transitions:** "**The Boolean conditions on the transitions should not overlap, otherwise the state machine won't know where to go.**"
- **Binding actions is what makes it an Adaptive Model.** A state diagram alone is a **passive model**. Bind actions **on transitions** (executed when taken) or **on states** (usually on *entry*, sometimes *exit*); some machines allow **internal actions** invoked on an event in that state — "like a transition back to itself, but perhaps without triggering any entry actions again." On choosing: "Different action-binding approaches suit different problems and different personalities. I don't have any strong guidelines to offer, other than to keep it as simple as it can reasonably be to model your behavior. Many implementations… have gone for the maximum expressiveness of the machine — such as the very expressive state machine models used by the UML. But small state machines suitable for DSLs can often work well with much simpler models."

**When to use.** Refreshingly honest:
> "I have that horrible feeling when I know that almost the only thing I can say is that you should use a State Machine when the behavior you're specifying feels like a State Machine — that is, when you have a sense of movement, triggered by events, from state to state. In many ways, the best way to see if a State Machine is appropriate is to try sketching one on paper, and if it fits well, to try it in action."

One concrete danger: **State Machines are limited to parsing regular grammars.** They cannot match arbitrarily nested delimiters. "If your behavior has anything like that, you may run into the same problem."

**Relationships.** An instance of §18 — but only once actions are bound; a pure state diagram is passive. Target model for most code-generation examples in §§23–28. Its regular-grammar limit is why a lexer is a state machine and a parser a push-down machine.

> **SDK lens:** **Machine state versus object state is a public-API distinction.** Exposing a status or lifecycle enum is choosing which states are behaviorally interesting: too many leaks internals, and exposing a *derived* state avoids a redundant, drift-prone field. Stored versus derived status is a real API-design choice. **"You don't need the model to be manifest in the software"** cautions against over-modeling — a guard clause in `cancel()` is often the whole of what the state machine buys. Reach for an explicit state machine model when you need behavior to be *configurable*, *inspectable*, or *generated*, not merely because the domain has states. Enforce two invariants at configuration time rather than discovering them at runtime: **non-overlapping guards**, and an explicit, documented **unhandled-event policy** (error versus ignore). The action-binding decision (entry / transition / internal) is exactly the callback-surface design question for workflow engines, connection and session lifecycles, retry and circuit-breaker state, and protocol implementations — pick the simplest binding that models your behavior rather than copying UML's maximal expressiveness.

---

# Code generation patterns

Six patterns on **three independent axes**: (1) how you write the generator — Transformer vs Templated Generation (code that emits text vs text with holes); (2) what the generated code looks like — Model-Aware vs Model Ignorant Generation (generated code configuring a runtime model vs logic inlined into control flow); (3) hygiene patterns cutting across both — Embedment Helper (keep foreign code out of templates and grammars) and Generation Gap (keep generated code out of handwritten files). The axes are genuinely orthogonal. **Axis 1 is chosen by the static/dynamic ratio and structural complexity of the output; axis 2 by what the target environment can host and afford.**

## 23. Transformer Generation *(Ch. 52)*

**Intent:** Generate code by writing a transformer that navigates the input model and produces output.

**Concept.** A program taking the Semantic Model as input and producing target source as output. Ordinary code: loops over model elements, string formatting, writes to a stream.

**Input-driven versus output-driven — the key conceptual tool.**
- **Output-driven** "starts from the required output and dives into the input to gather the data it needs as it goes" — `renderHeader(); renderBody(); renderFooter();`.
- **Input-driven** "walks the input data structure and produces output" — for each product, render its name, then for each photo, render the photo.
> "Often, transformers use a combination of the two… The outer logic describes the broad structure of the output document… while the inner section produces output driven by a particular kind of input data. **In any case, I find it useful to think of each routine in the transformation as either input-driven or output-driven and to be conscious of which I'm using.**"

The outer level must be output-driven when the output has ordering constraints — **all states have to be declared before any transitions**, because forward-referencing a state is an error in the target language. The outer structure follows the *output's* requirements, not the model's shape.

**Multistage transforms.** A **two-step transform** walks the input model to produce an **output model** — a model, not text, oriented towards the generated output — and a second step renders it. Useful "when the transform is complicated, **or when you have multiple output texts to produce from the same input that share some characteristics**": the first stage produces one output model with the common elements, and the differences go in varying second stages. **You can mix techniques across stages.**

**When to use.**
- **Single-stage** when the output has a **simple relationship with the input model and most of the output text is generated** — "very easy to write and doesn't require introducing a templating tool." **Multi-stage** when the relationship is more complex, "as each stage can handle a different aspect of the problem."
- **Pairs naturally with Model-Aware Generation:** "If you use *Model-Aware Generation*, you can usually populate the model with a simple sequence of calls, which is easy to generate with Transformer Generation." The implicit contrast: mostly *static* text with occasional simple dynamic bits → Templated Generation. One craft note: the generator emits **comments containing dynamic data** — orientation for humans who will later read the output in a debugger.

**Relationships.** Alternative and complement to §24; the two mix within a multistage transform, and printf-style formatting mixes them at fine grain. Pairs with §26. Consumes the Semantic Model.

> **SDK lens:** This is how most **client-SDK generators** work — spec model in, source out — and the input-driven/output-driven distinction organizes one: the file skeleton (imports, class shell, footer) is output-driven; per-operation and per-model-type sections are input-driven. **The multistage transform with an intermediate output model is the standard answer to multi-language SDK generation:** one first stage normalizes the spec into a language-agnostic output model (resolved types, naming conventions, pagination shape), and per-language second stages render it — exactly "multiple output texts from the same input that share some characteristics," and why mature generators have an IR rather than templates reading the spec directly. The transformer-versus-template choice reduces to one question: **is the generated file mostly boilerplate scaffolding, or mostly synthesized structure?**

## 24. Templated Generation *(Ch. 53)*

**Intent:** Generate output by handwriting an output file and placing template callouts to generate variable portions.

**Concept.** Write the output file you want, then insert callouts for the bits that vary; a template processor combines template and *context*. "Templated Generation is a very old technique, familiar to anyone who has used mail-merge facilities in a word processor." It also works at small scale: "**The old faithful `printf` function in C is an example of using Templated Generation to print out a single string at a time**" — a reminder that Templated and Transformer Generation "can be very intermixed."

**The three components.** **Template** — output source text with callouts referencing the context. **Context** — the source for dynamic data, "essentially, the data model for the template generation." **Templating engine** — brings them together; a controlling program "may run the same template with multiple contexts to produce multiple outputs."

**Callout languages: host code versus a templating language.**
- Arbitrary host code in callouts is most general, but "like any form of *Foreign Code*, it needs to be used with care, otherwise the structure of the host code can overwhelm the template." Strong recommendation: "**if you have a template processor that embeds arbitrary host code, you confine yourself to simple function calls within the callouts, preferably using an *Embedment Helper*.**"
- Because template files so commonly get "thoroughly messed up due to too much host code," many processors provide a restricted **templating language** "to encourage simpler callouts and preserve the clarity of the template structure." The simplest such language treats the context as a map with lookup expressions; three needs push further — **iteration** ("a common driver for more complex templating"), **conditionals**, and **subroutines**.
- **The governing advice:** "be as minimalist as possible, **since the strength of Templated Generation is directly proportional to how easy it is to visualize the output file by looking at the template.**"

**When to use.**
- **Great strength:** "you can look at the template file and easily understand what the generated output will look like." Best when there is **quite a lot of static content** and the dynamic content is **occasional and simple**. **First indicator:** proportion of static content. "The greater the proportion of static content, the more likely that it will be easier to use Templated Generation."
- **Second consideration:** complexity of dynamic content. "The more you use iterations, conditionals, and advanced templating language features, the harder it is to comprehend what the output will look like… When this happens, you should consider *Transformer Generation* instead."
- So: **static-heavy plus simple dynamics → template; generated-heavy plus complex structure → transformer.**

**Practical points from the example.** **The context is a single Embedment Helper** initialized with the model, rather than pushing model objects and loose values in. **Where the line falls:** simple properties come straight off Semantic Model objects; derived names, identifiers, and assembled lists are helper methods. **A generator and its target can compete for the same syntax** — the C preprocessor and the template engine both used `#`, and it worked by luck. **Choose a template delimiter that does not collide with your target language's syntax.** Two asides revealing his values: he generates named constants rather than raw codes "because I prefer even my generated code to be readable," and recomputes a sorted list each time, noting he would cache it only if performance demanded.

**Relationships.** Opposite end of a spectrum from §23, combinable in a multistage transform. Strongly associated with §25. A form of Foreign Code (§13). The book's example generates Model Ignorant output (§27).

> **SDK lens:** Templates are right for the **boilerplate-heavy files in a generated SDK** — package manifests, README scaffolds, client class shells, per-endpoint methods with a fixed shape. Transformers are better for structural variation: type mapping, union and discriminator handling, nested schema flattening. **"The strength of Templated Generation is directly proportional to how easy it is to visualize the output by looking at the template"** is a usable acceptance criterion for a generator's maintainability: a template that has become unreadable to someone who knows the target language has stopped paying for itself — move logic into a helper or switch to a transformer. Treat delimiter collision as a real hazard, not a curiosity.

## 25. Embedment Helper *(Ch. 54)*

**Intent:** An object that minimizes code in a templating system by providing all needed functions to that templating mechanism.

**The separation principle.** Embedding general-purpose code into a simple representation "adds a lot of power… without complicating the basic representation itself. **However, a common problem when you do this is that the Foreign Code can end up being quite involved and obscure the representation that it's embedded into.**" The pattern: **move all the complex code into a helper class, leaving only simple method calls in the host representation. "This allows the host representation to be dominant and retain its clarity."** In one line: *the foreign representation — grammar, template, config — should read as itself, not as host-language code with a bit of grammar sprinkled in.* Fowler's three examples span the whole book: web page templates, code actions in grammar files, and code generation templates.

**Mechanics.** "Similar to a refactoring": create the helper, make it visible, move the code out, leave a call behind. **The one tricky technical aspect is getting an object into visible scope** — in a templating engine, place the helper in the context; in a parser generator, declare it as a field on the generated parser or make it the parser's superclass. The damage prevented, concretely: a grammar with inline code stuffing elements into maps, looking up or creating model objects, and wiring relationships — "**With such inlined code, grammar files can have more lines of [host language] than the grammar DSL.**" The "after" is one call per rule. A related trick: **pass the raw tokens to the helper rather than extracting text in the grammar.**
- **The rule: "any code that's more than a simple method call should move into the Embedment Helper, so the only code left in the host representation is simple calls."**
- **The remaining complication is not technical:** "The key to this, as with any abstraction, is careful naming of the methods, so they clearly state the intention of the called code without revealing its implementation. This is the same basic skill as method and function naming in any context — a central skill of a good programmer."

**A naming judgement.** Command-oriented (`addEvent`) or event-oriented (`eventRecognized`)?
> "The argument for event-oriented names is that it doesn't imply any action on the helper, leaving it up to the helper to decide what to do. This is particularly handy if you use different helpers with the same parser… The problem with event-oriented names is that you can't tell what's going on by just reading the grammar. In a case where I'm only using the grammar for one activity, I'd rather be able to read the grammar and see from the naming what's happening at each step."

Tiebreaker: *how many differently-behaving consumers will there be, and does the call-site reader need to know what happens?*

**Should the helper generate output? — a genuine debate.** "I often hear this as an absolute point: **Helpers must never generate output.** I don't agree with this absoluteness."
- **The real cost:** "any such output isn't visible from the template. Since the whole point of Templated Generation is that you see the output with holes, such hiding of generated material is, without doubt, a problem." **The counterweight:** it "has to be weighed against the complexity of retaining the output in the template and the more complicated constructs of *Foreign Code* you may need if you want to avoid generating output in it."
- **The middle ground:** the helper takes the *logic* without taking the *output* — expose predicates and derived values ("does this item have a link? what is its target?") so the template keeps its markup but loses the precedence rules.
- **Conclusion:** "**The more complicated the logic and the more complicated the overall template, the more I gain by moving output generation to the Embedment Helper where I can factor it better.**"
- **The strongest objection, and its scope:** separate people working on the template (an HTML designer) and the code create a coordination cost. "**Of course, this is only a problem if you have different people working on the different files; when generating code for a DSL, this is usually not the case.**" The deciding variable is organizational, not technical.

**When to use.** A near-universal recommendation, unusually for Fowler.
- "I'm very suspicious of patterns that someone claims should always be used, but Embedment Helper is one of those things I would always suggest doing, except in really trivial cases." Empirical justification: "I see a huge difference if Embedment Helper is present. Without it, it's hard to see the host representation, so much so that it rather defeats the purpose of using an alternative representation at all… **a grammar file with lots of Foreign Code in actions makes it very hard to see the basic flow of the grammar.**"
- **A second benefit: tooling.** Embedded code cannot be edited with the IDE's tooling; moved to a helper, "you're back in your full editing environment." Even code coloring usually fails for embedded code.
- **The one exemption:** "where you are using classes that act as a natural home for providing this kind of information" — e.g. Templated Generation with a Semantic Model, where much of the helper's behavior can live in the model itself, "**provided this doesn't make the Semantic Model too complex.**"

**Relationships.** Applies to Foreign Code (§13) wherever it appears. Explicitly required by Parser Generator (§7) — "the only code in the grammar should be single method calls" — and by BNF's code actions (§3). Omittable when a Semantic Model naturally provides the behavior, as in §28.

> **SDK lens:** The general principle — **keep foreign code out of the foreign representation** — is a config and DSL surface design rule. Anywhere a library lets users embed host code in a declarative artifact (build config, CI YAML with inline scripts, query DSLs with raw-SQL escape hatches, schema files with hooks), offer a way to *name and call out to* real code rather than inline it; forcing inlining stops the declarative files being readable as declarations. **Command-oriented versus event-oriented naming is a general callback and hook API question**: event names keep the emitter decoupled and support multiple differently-behaving listeners; command names make the call site self-documenting. **The tooling argument is a real DX argument for extension APIs** — code in a normal source file gets refactoring, autocomplete, type checking, and highlighting; code inside a string or config file gets none, which alone often justifies "reference a function by name" over "inline a snippet." And the should-the-helper-generate-output debate generalizes to **how much a helper or formatter layer should own** — pulling logic out is nearly always good; pulling *the visible artifact* out trades reviewability for factoring, with ownership of the two files as the tiebreaker.

## 26. Model-Aware Generation *(Ch. 55)*

**Intent:** Generate code with an explicit simulacrum of the semantic model of the DSL, so that the generated code has generic-specific separation.

**Concept.** **Model-Aware Generation replicates some form of the Semantic Model in the generated code in order to preserve the separation of generic and specific code within the generated code.** The target environment gets **a hand-written generic runtime model** plus **a small generated configuration script that populates it** — calls like `declare_state("idle")` and `declare_transition("idle", "doorClosed", "active")`.

**Mechanics.**
- "**The most important aspect of Model-Aware Generation is that it preserves the principle of generic-specific separation. The actual form that the model takes in the generated code is much less important, which is why I like to say that the generated code contains a *simulacrum* of the Semantic Model.**"
- It is a simulacrum for good reasons: target-environment limitations force compromises that make the model a weaker statement of intent — "**it's important to realize that this isn't such a big deal as long as you keep the generic-specific separation.**"
- **The testability property is the most practically valuable part:**
  > "Since the simulacrum model is a self-standing version of the Semantic Model, you can, and should, build and test the model without using any code generation. **Ensure the model has a simple API to populate it.** The code generation will then generate configuration code that calls this API. You can then test the simulacrum model using testing scripts that use this same API."

  The generator and the runtime become **independently testable, joined only by a small, stable API.**

**What the worked example makes concrete** (generating C for a constrained controller). *Implementation shape:* a data structure plus navigation routines, all memory allocated up front, integer references standing in for object references.
- **Encapsulation:** all data definitions in one file, "encapsulate[d]… behind a bunch of externally declared functions. **The specific code only knows about these functions and is, rightly, ignorant about the data structure itself. In this case, ignorance is truly bliss.**" Those declaration functions *are* the population API.
- **The consequence of that encapsulation is a versioning payoff:** the internals are primitive (linear name scans), and "in running the machine we might be better off replacing the linear search with a hash function. **Since the state machine is well encapsulated, this is easy to do… Changing such implementation details of the model doesn't affect the interface of the configuration functions that define new state machines. This is an important encapsulation.**"
- **Readability of generated code, as a principle:** "I believe that generated code should be readable even if it isn't edited, because it will often be used for debugging. **To make it readable, you have to understand your target audience, such as who is doing the debugging.**" Hence array indices over pointer arithmetic, even though many C programmers prefer the latter. He also keeps state names (used only at configuration time) because they enable "more useful diagnostics when things go wrong" — sacrificed only if space were really tight.
- **A deliberate loss of intent:** reset events are translated into ordinary transitions — "an example of a typical tradeoff where I prefer simplicity of operation to clearly stating intent. **For the true Semantic Model, I prefer to keep as much intent as I can, but for a model in a generated target environment I value capturing intent a little less.**"

**The second example is the payoff case.** Instead of recompiling to install a new machine, generate a plain line-oriented **data file** that a small interpreter in the target reads with Delimiter-Directed Translation, dispatching each line to the *same* declaration functions.
- On the format: "I don't consider this textual format a DSL, as I designed it to make it easy to interpret, not for readability by humans… human readability was a distant second to ease of interpretation." A clean statement of the difference between **a DSL and a wire/config format.**
- The general lesson: "**code generation for a static target language does not mean you cannot use runtime interpretation.** … By generating a file that's designed for ease of interpretation in the environment I have available, I can minimize the cost of the interpreter." The boundary: putting the full DSL processor in the target would raise processing demands and leave this pattern.

**When to use.**
- **Advantages over Model Ignorant Generation:** the simulacrum "is easier to build and test, because you don't have to rerun and comprehend code generation while working on [it]"; and "since the generated code is now made up of API calls on the simulacrum model, that code is much easier to generate, which makes the generator simpler to build and maintain."
- **The two reasons not to use it — both about the target environment:** "Either it's too hard to express even a simulacrum model" there, **or** "there are performance problems with having a simulacrum model at runtime."
- **Framing sentence:** "In many cases, you are using DSLs as a front end to an existing model. **If you are generating code to work with the model, then you are using Model-Aware Generation.**"

**Relationships.** Counterpart to §27 and Fowler's default preference. Pairs naturally with §23. The target-side simulacrum is an Adaptive Model (§18) living in the target. The dynamic-loading variant uses Delimiter-Directed Translation (§1).

> **SDK lens:** The most directly SDK-relevant pattern in Part VI. **"A thin generated layer over a fat hand-written runtime" is the dominant architecture of good generated client SDKs.** Generated code should be a declarative configuration or registration surface — endpoint descriptors, type registrations, method stubs calling a shared request pipeline — while retry, auth, serialization, pagination, and error mapping live in a hand-written, versioned runtime library the generated code calls. Fowler's argument for the split is exactly the argument for that architecture: the runtime is testable without running the generator, and the generator becomes trivial because it only emits API calls. **"Ensure the model has a simple API to populate it"** is a concrete requirement on that runtime's stable surface: the population API is the contract between generator and runtime, and keeping it small and stable is what lets each side evolve. **The encapsulation payoff is a versioning payoff** — because generated code only knows the declaration functions, the runtime can change internals without regenerating anything; conversely, if generated code reaches into runtime internals, every runtime change forces full regeneration across all consumers. **Generated code is read constantly** (stack traces, "what does this method actually send?"), so calibrate readability to whoever debugs it. **The dynamic-loading example is the "ship a spec file, not a recompile" pattern** — and note the attached guidance: *that generated file is optimized for ease of interpretation, not human readability.* It is a serialization format, not a DSL, and conflating the two makes both worse. Lastly, **the fidelity you demand of your true Semantic Model need not be demanded of a derived artifact.**

## 27. Model Ignorant Generation *(Ch. 56)*

**Intent:** Hardcode all logic into the generated code so that there's no explicit representation of the Semantic Model.

**Concept.** The opposite pole: an event-handling function with a switch on current state and nested conditionals on the event. **There is no model data structure in the target at all** — the model's content has been dissolved into control flow.

**Mechanics.** The enabling insight: "One of the advantages of code generation is that it allows you to produce code that would be too repetitive to write by hand in a controlled way. **This opens up implementation options that, usually, you would wisely shy away from because of duplicating code. In particular, this allows you to take behavior usually represented through data structures and encode them in control flow.**"

The method: "start by writing an implementation of a particular DSL script in the target environment. **I prefer to start with a very simple and minimal script.** The implementation code should be clear, but can freely intermingle generic and specific code, and I don't have to worry about repetition… **This means I don't have to think about clever data structures, usually preferring procedural code and simple structures.**" Because a machine writes it, you can relax DRY and prefer flat, obvious, repetitive code: "**While this code would be too repetitive to write by hand for different machines, when generated it is quite easy to follow.**"

**When to use — two reasons.**
1. **Target-environment limitations.** "Target environments often involve languages with limited facilities for structuring programs and building a good model. In these situations, it's not possible to use *Model-Aware Generation*, so Model Ignorant Generation is pretty much the only option."
2. **Runtime resource pressure.** "When using Model-Aware Generation results in an implementation that demands too much runtime resources. Encoding logic in control flow may reduce memory needs or increase performance."

**Preference and honest counterweight:** "On the whole, however, I prefer to see Model-Aware Generation if it's possible… Having said that, **using Model Ignorant Generation often makes the generated code easier to follow. This has the converse effect that it can be easier to figure out what to generate, although harder to write the code to generate it.**" The crisp tradeoff: **Model Ignorant Generation moves complexity from the generated artifact into the generator; Model-Aware Generation moves it from the generator into a hand-written runtime.**

**Relationships.** Counterpart to §26. Generated in the book's example by Templated Generation (§24) — static-heavy output with simple dynamic parts — mirroring the Transformer + Model-Aware pairing.

> **SDK lens:** Right when **the target cannot host a runtime library**: embedded or constrained environments, dependency-free generated code, single-file drop-in artifacts, or environments where a runtime dependency is politically or technically impossible. "Zero-dependency generated client" is a real product requirement that forces this pattern. Also right when **inlining wins on performance or size** (generated serializers and parsers where a table-driven runtime is slower or bigger than unrolled control flow). But state the costs: **every behavior fix requires regenerating and redistributing to all consumers**, since there is no shared runtime to patch — with Model-Aware you ship a runtime patch, here the bug is baked into every user's checked-in files, which is usually the decisive argument for Model-Aware in library ecosystems. The one genuine counterweight is trust: fully inlined generated code is auditable without learning your runtime.

## 28. Generation Gap *(Ch. 57)*

**Intent:** Separate generated code from non-generated code by inheritance.

**Concept.** "One of the difficulties of code generation is that generated code and handwritten code need to be treated differently. **Generated code should never be edited by hand, otherwise you can't safely regenerate it.**" Generation Gap keeps them in different classes linked by inheritance. (Attributed to the late John Vlissides, whose formulation had the handwritten class as a *subclass*; "my description is a little different, based on the use I've seen.")

**Mechanics.** Basic form: generate a superclass, hand-code a subclass.
- "This way you can always override any aspect of the generated code that you like in the subclass." The generated code calls hand-coded features via **abstract methods** (compiler-checked) or **hook methods** (overridden only when needed).
- "**When you refer to these classes from outside, you always refer to the handwritten concrete class. The generated class is effectively ignored by the rest of the code.**"

**The three-class structure.**

| Class | Kind | Contains |
|---|---|---|
| Handwritten base class | handwritten | logic that doesn't vary based on the parameters to code generation |
| Generated class | generated | logic that can be generated automatically from the generation parameters |
| Handwritten concrete class | handwritten | logic that can't be generated and relies on generated features — **"the only one that should be mentioned by other code"** |

Rationale for the base class: "Instead of generating the nonvarying code, having it in a superclass allows it to be better tracked by tools, particularly IDEs." Behind that sits the general principle:
> "**In general, my suggestion with code generation is to generate as little code as possible.** This is because any generated code is more awkward to edit than handwritten code. Whenever you change generated code, you need to rerun the code generation system. Refactoring capabilities of modern IDEs won't work properly with generated code."

You don't always need all three: skip the base class if there is no unvarying logic; skip the concrete class if you never need to override — "another reasonable variation of Generation Gap is a handwritten superclass and a generated subclass." A candid admission: "**The interplay of code generation and handwriting does lead to a more complicated class structure — this is the price you pay for the convenience of code generation.**"

**The empty-concrete-class rule.** When only *some* classes need handwritten overrides, you must decide what happens for the rest. Making the generated class the named class "causes a lot of confusion over naming and usage. **As a result, I prefer to always create a concrete class, leaving it empty if it has nothing to override.**" Who writes the empty ones is a volume question: fine to leave to a programmer if there are few and they change rarely; "if you have a lot of them and they change frequently, then it's good to tweak the code generation system to check if there's an existing concrete class and generate an empty one if not."

**The extension-point recipe from the example** (schema → data classes), worth lifting whole:
- The **handwritten base class** defines the validation entry point: create a Notification, call an **abstract** per-field check method and an **empty hook** class-level check method, return the notification.
- The **generated class** implements the abstract method by calling one check per field, generated from the same information as the fields, so **it can never drift out of sync with the field list.**
- Those per-field checks are themselves **generated as empty hook methods**, so the **handwritten concrete class** can override any to add real validation.
- The class-level hook covers validations spanning several fields. **Net effect: the abstract method gives compiler-enforced completeness; the hooks give opt-in extensibility; and the handwritten code never has to enumerate the fields.**

Two further notes: the **Semantic Model plays the Embedment Helper role** here (§25's carved-out exemption); and on builds — "**An alternative approach is to use a scripting language for code generation; then I only have to run a script to generate code. This simplifies the build process at the cost of introducing another language.**"

**When to use.**
- "A very effective technique that allows you to create one logical class split into separate files." **Language requirement:** "You do need a language with inheritance… any members that can be overridden need to have sufficiently relaxed access controls to make them visible to subclasses — that is, not private."
- **Alternative — partial or open classes.** Partial classes separate generated and handwritten code without inheritance, and are "good for adding features to generated classes" but give "no mechanism to override features"; open classes "do handle this by evaluating the handwritten code after the generated code."
- **The anti-pattern it replaced.** Generating into a marked region between `code gen start` / `code gen end` comments "was confusing, leading to people modifying the generated code and awkward source control diffs. **Keeping generated code in separate files is almost always a better idea if you can find a way to do it.**"
- **Prefer collaboration to inheritance when you can.** "**Collaborating classes are a simpler mechanism to use and understand, so in general I prefer them. I am only pushed to Generation Gap when the call interaction becomes more complicated — for example, when there is a default behavior in the generated class that I want to override for special cases.**" That is the actual decision rule: **inheritance only when you need to override defaults; otherwise plain collaboration.**

**Relationships.** Orthogonal to §§23–24 and §§26–27. Its "handwritten base class" layer is, in a generated-SDK architecture, the same thing as Model-Aware Generation's hand-written runtime. One of the two ways to attach an Embedment Helper (§25) to a generated parser, per §7.

> **SDK lens:** The canonical answer to "how do users customize a generated client SDK?" **The invariant to enforce is that generated files are never hand-edited** — every ecosystem that violates it ends up with users' local edits silently lost on regeneration, or users pinned to an old generator version. Generation Gap makes the boundary a *file and class* boundary rather than a comment marker. **The three-layer structure maps cleanly onto generated SDKs:** hand-written runtime and base (transport, auth, retry, serialization — the non-varying logic, which is also §26's runtime); generated layer (per-endpoint methods, per-schema models); hand-written concrete layer (convenience methods, an override for one weird endpoint) — and **only the last is what user code names.** **"Generate as little code as possible"** is the load-bearing guidance: every generated line is one your users' IDEs cannot refactor, that bloats their diffs, and that you must regenerate to fix — push everything invariant down into the runtime. **Always emit the concrete class, even empty** — otherwise user code sometimes names the generated class and sometimes the handwritten one, and adding a customization later becomes a breaking rename at every call site; that rule is precisely the stability guarantee a public SDK needs. Two more: **visibility constraints are a real API consequence** — decide up front which members are extension points and which are sealed; and **the abstract-method plus hook-method pairing is a reusable extension-point recipe** — abstract where the compiler should enforce that generated code supplied something over an enumerable set, empty hooks where extension is optional. For multi-language generators the separation mechanism must be idiomatic per target (partial classes, open classes, declaration merging, embedding) rather than forcing inheritance everywhere — and **prefer collaboration over inheritance unless you genuinely need per-case default overrides.**
