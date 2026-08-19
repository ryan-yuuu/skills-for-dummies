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







