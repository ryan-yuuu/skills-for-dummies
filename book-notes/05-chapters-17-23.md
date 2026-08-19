# Study Notes — Fowler, *Domain-Specific Languages* (2010), Part III "External DSL Topics", Chapters 17–23

Source: Martin Fowler with Rebecca Parsons, *Domain-Specific Languages*, Addison-Wesley 2010.
PDF read: `Domain-Specific Languages.pdf`, PDF pages 146–201 (print page numbers differ).

Actual chapter boundaries found in the PDF:

| Chapter | Title | PDF pages |
|---|---|---|
| — | Part III opener (chapter list) | 146 |
| 17 | Delimiter-Directed Translation | 146–159 |
| 18 | Syntax-Directed Translation | 159–166 |
| 19 | BNF | 166–173 |
| 20 | Regex Table Lexer (Rebecca Parsons) | 173–177 |
| 21 | Recursive Descent Parser (Rebecca Parsons) | 177–183 |
| 22 | Parser Combinator (Rebecca Parsons) | 183–194 |
| 23 | Parser Generator | 194–201 |
| 24 | Tree Construction (next assignment; starts here) | 202 |

Part III's full chapter list, in book order (Fowler, DSL book, Part III opener): Delimiter-Directed
Translation, Syntax-Directed Translation, BNF, Regex Table Lexer, Recursive Descent Parser, Parser
Combinator, Parser Generator, Tree Construction, Embedded Translation, Embedded Interpretation,
Foreign Code, Alternative Tokenization, Nested Operator Expression, Newline Separators, External DSL
Miscellany.

Reading note: code examples are deliberately **not** transcribed. Where an example matters, only what
it demonstrates conceptually is recorded.

---

## The shape of Part III (orienting frame)

Chapters 17–23 are a graded set of answers to one question: *how do you get from a chunk of external
DSL text to something your program can act on?* They fall on a spectrum of **how explicitly the
structure of the language is stated**:

1. **Delimiter-Directed Translation** — no explicit grammar at all; chop by delimiters and dispatch.
2. **Recursive Descent Parser** — grammar exists but is *implicit* in the shape of the functions.
3. **Parser Combinator** — grammar is *explicit as composed objects*, but not in BNF syntax.
4. **Parser Generator** — grammar is *explicit as a declarative DSL* (a BNF file) and the parser is
   generated from it.

Moving right buys documentation value, easier evolution, and more power on complex languages; it
costs a learning curve (grammars) and, at the far right, build complexity. Chapters 18 (Syntax-
Directed Translation) and 19 (BNF) are the shared conceptual substrate for 3 and 4; chapter 20 (Regex
Table Lexer) is the shared front end for 2, 3, and (optionally) 4.

---

## Chapter 17: Delimiter-Directed Translation
*(PDF pp. 146–159)*

**Intent (verbatim, one line):** "Translate source text by breaking it up into chunks (usually lines)
and then parsing each chunk." (Fowler, DSL book, Ch. 17 "Delimiter-Directed Translation", intent)

### The concept

The most naive-but-honest way to parse an external DSL. You take the input, split it on some
delimiter — almost always the line ending — and then run each chunk through code that recognizes and
processes it. There is no grammar, no lexer/parser separation, no parse tree. Everything is done with
string splitting, regular expressions, and conditionals: tools every working programmer already has.
Output goes straight into a Semantic Model (Embedded Translation) or is interpreted on the spot
(Embedded Interpretation); Tree Construction is possible in principle but Fowler says he rarely sees
it combined with this pattern.

The sketch in the book shows a state-machine block being split into its four lines, each line handed
to a `parse(line)` call, each call feeding the semantic model directly.

### How it works

**Chunking.** Line-at-a-time reading is trivial in every environment. The one complication is *line
continuation*: long logical lines you want to break physically in the editor. Quoting the line ending
(Unix backslash) works but "looks ugly … and is vulnerable to whitespace between the quote and the
end of line." A dedicated continuation character — if it's the last non-whitespace character on a
line, the next line is part of this one — is usually better. Remember you can get more than one
continuation line, so the join must be recursive/looping.
(Ch. 17, section "How It Works")

**Classifying lines.** How you process the lines depends on the language, and Fowler gives a
taxonomy that is the real content of this chapter:

- **Autonomous + isomorphic lines.** None affects the others (you could safely reorder or delete
  lines without changing the interpretation of any other line), and every line encodes the same kind
  of information in the same form. Processing is trivial: one line-processing function run against
  each line, pulling out the fields you need.
- **Autonomous + polymorphic lines.** Each line still stands alone, but different lines have
  different forms and need different processing. Handle with a dispatching conditional:
  `if (isBorder()) parseBorder(); else if (isHeadline()) parseHeadline(); … else throw
  RecognitionException(input)`. The conditions can be regexes or other string operations; Fowler
  "usually prefer[s] using methods" — wrapping each regex in a well-named predicate — over inlining
  the regex in the conditional. Note the mandatory `else throw`: unrecognized input must fail loudly.
- **Hybrid: isomorphic lines with polymorphic clauses.** Every line has the same broad structure
  (e.g. always `<reward> for <activity> at <location>`), but each clause can take several forms. A
  single top-level routine identifies the clauses and calls one processing routine per clause; each
  clause routine then uses the polymorphic conditional pattern internally.
- **Nonautonomous statements.** The hard case. The same syntactic form means different things
  depending on where in the file it appears — e.g. `unlockPanel PNUL` is legal and means one thing in
  an `events` block, means another in a `commands` block, and is an error inside a `state` block.
  This forces you to track parse state. Fowler's recommended structure: **a family of line parsers,
  one per parse state** — a top-level line parser plus a command-block line parser, event-block line
  parser, reset-event line parser, and state-block line parser. When the top-level parser sees the
  `events` keyword it switches the current line parser to the event line parser. "This, of course, is
  just an application of the *State [gof]* design pattern." (Ch. 17, "How It Works")

**Extracting data from a chunk.** In order of preference:
1. A string splitter function (split on whitespace, take element *n*). Easiest when the string splits
   cleanly.
2. A regular expression with named capture groups. More expressive power than a split, and it doubles
   as a syntactic validity check. Downside: regexes are complicated and many people find them awkward
   to follow.
3. A **composed regex** — Fowler's own term for breaking a large regex into named subexpression
   constants, defining each separately, and concatenating them. He uses this whenever a regex gets
   complicated: "I find this makes it much easier to understand what's going on."

**Whitespace is a recurring pain.** For a line of the form `property = value` you must decide whether
whitespace around the `=` is optional. Optional whitespace complicates line processing; making it
mandatory (or forbidding it) makes the DSL harder to use. It gets worse when there's a distinction
between one and many whitespace characters, or between tabs and spaces. (Contrast with
Syntax-Directed Translation, where the lexer usually just throws whitespace away.)

**The slippery slope to a framework.** There's a recurring shape here: check whether a string matches
a pattern, then invoke a processing rule for that pattern. That regularity "naturally raises the
thought that this would be amenable to a framework" — a series of objects each holding a regex and
processing code, run in turn, plus some indication of overall parser state, and (to configure it) a
DSL on top. Fowler's punchline: that is exactly what Lex-inspired lexer generators do, and — this is
the key judgement — "once you've got far enough into this to want to use a framework, then the jump
to Syntax-Directed Translation is not much further, and you have a wider range of more powerful tools
to work with." (Ch. 17, "How It Works")

### Relationship to grammars

Fowler explicitly maps his line taxonomy onto grammar concepts (Ch. 17, "How It Works"):

- polymorphic lines and clauses ≈ **alternatives** in a grammar
- isomorphic lines ≈ **production rules without alternatives**
- using methods to break a line down into clauses ≈ **subrules**

This is worth noticing: even the "no grammar" technique is doing grammar work, just without saying
so. The same observation recurs in Ch. 21 about recursive descent.

### When to use it

(Ch. 17, section "When to Use It")

- **Strength: approachability.** "The great strength of Delimiter-Directed Translation is that it is a
  technique that is very simple for people to use." The main alternative, Syntax-Directed Translation,
  requires you to mount a learning curve on grammars. Delimiter-Directed Translation relies purely on
  techniques most programmers are already familiar with.
- **Weakness: the same approachability.** It doesn't scale to complex languages. It works very well
  for simple languages, "particularly those which don't require much nested context." As complexity
  increases it "can get messy quickly, particularly since it takes thought to keep the design of the
  parser clean."
- **Fowler's actual recommendation:** favor it only when you have simple autonomous statements, "or
  maybe just a single nested context. Even then I'd prefer to use Syntax-Directed Translation unless
  I'm working with a team that I didn't think was prepared to deal with learning that technique."

So: this is a *team-capability* decision as much as a technical one.

### The examples (conceptually)

- **Frequent customer points (C#).** A hotel-loyalty DSL where each line is an "offer." The semantic
  model is an `Offer` composed of a location Specification, an activity Specification, and a Reward
  (with per-day and per-dollar subclasses) — i.e. the *Specification* pattern from Evans DDD used as
  the model's spine. The parser reads lines, joins continuations, strips comments, skips blanks, and
  delegates each line to a fresh **Method Object** because the per-line parsing behavior is
  complicated enough to want its own class. Inside, one composed regex splits the line into reward /
  activity / location groups, then a separate small parse method handles each clause. Notable
  judgement calls Fowler flags: he kept the group-defining method long rather than decomposing it,
  because there is "a strong semantic linkage between the definition and the use of these groups";
  and he deliberately built the regex out of named subexpressions rather than one monolith.
- **Miss Grant's controller (Java).** The nonautonomous case. Blocks (`events`, `resetEvents`,
  `commands`, individual `state`s) each have their own statement syntax, so the parser is in
  different states as it reads. Implemented with State/Strategy: a `StateMachineParser` context plus a
  `LineParser` hierarchy. The abstract `LineParser` does the common work (strip comment, trim, skip
  blank) then calls an abstract `doParse` hook — Template Method. Each concrete line parser's
  `doParse` is a conditional over line-shape predicates. The `StateMachineParser` also acts as a
  **Symbol Table** (name → Command/State/Event), with an `obtain`-prefixed method meaning "get one if
  it exists or create if it doesn't" — needed because a transition can reference a state that hasn't
  been declared yet (forward references).

  Fowler also flags **the classic State-pattern design question**: how much behavior lives in the
  context object versus the state objects? He shows both. *Decentralized* (behavior in the line
  parsers) means the line parsers constantly pull data out of the shared Symbol Table — "Pulling data
  out of an object repeatedly is usually a bad smell" — and forces the context to expose its state.
  *Centralized* (behavior in the state machine parser) keeps the Symbol Table private and hidden, but
  concentrates a lot of logic in the context, "which may make it overcomplicated. This would be more
  of an issue for a larger language." His verdict: "Both alternatives have their problems, and I'll
  confess I don't have a strong preference either way."

### SDK relevance

- The line taxonomy (autonomous/isomorphic → polymorphic → hybrid → nonautonomous) is a **complexity
  ladder** worth stealing for any input-format or config-format design. If you can keep your format's
  statements autonomous and isomorphic, the implementation stays trivial and the format stays
  reorderable and diffable. Nonautonomous, context-sensitive statements are what force you into
  stateful parsing machinery. That's an argument for designing formats where each statement carries
  its own context.
- "Once you want a framework for this, you should have used the real tool" is a general library-design
  smell test. When your ad-hoc dispatch table starts wanting configuration, ordering, and state, you
  have re-derived a worse version of an existing abstraction.
- The composed-regex technique (name subexpressions, compose them) is the regex-level version of
  extracting well-named functions — applicable to any place a library exposes pattern-like strings.
- Both examples fail loudly on unrecognized input (`RecognitionException`). A parser that silently
  ignores what it doesn't understand is a bug factory.

---

## Chapter 18: Syntax-Directed Translation
*(PDF pp. 159–166)*

**Intent (verbatim):** "Translate source text by defining a grammar and using that grammar to
structure translation." (Fowler, DSL book, Ch. 18 "Syntax-Directed Translation", intent)

### The concept

"Computer languages naturally tend to follow a hierarchical structure with multiple levels of
context. We can define the legal syntax of such a language by writing a grammar that describes how
elements of a language get broken down into subelements." Syntax-Directed Translation uses that
grammar to define the creation of a parser that turns input text into a **parse tree mirroring the
structure of the grammar rules**. (Ch. 18, intro + "How It Works")

The sketch: input text + grammar → parser → syntax tree.

This is the umbrella pattern for chapters 19–23. It doesn't tell you *how* to build the parser; it
tells you that a grammar is what structures the translation. Two routes from grammar to parser:

1. **Grammar as specification and implementation guide for a handwritten parser** — Recursive Descent
   Parser (Ch. 21) and Parser Combinator (Ch. 22).
2. **Grammar as a DSL** fed to a **Parser Generator** (Ch. 23) that builds the parser automatically.
   Here you write none of the core parser code; it's all generated.

Crucially, "the grammar only handles part of the problem." It can tell you how to turn input text
into a parse-tree data structure, and nothing more. You almost always need to do more than that,
which is why Parser Generators provide ways to embed further behavior (e.g. populating a Semantic
Model). Fowler's summary: "although the Parser Generator does a lot of work for you, you still have
to do a fair bit of programming to create something truly useful. In this way, as in many others, a
Parser Generator is an excellent example of a practical use of DSLs. It doesn't solve the whole
problem, but does make a significant chunk of it much easier." (Ch. 18, "How It Works")

### How it works — the three-layer architecture

Syntax-Directed Translation decomposes translation into layers. This separation of concerns is the
chapter's main design content.

#### Layer 1: The Lexer (a.k.a. tokenizer, scanner)

The first stage. It splits the *characters* of the input into **tokens** — "more reasonable chunks of
the input." Tokens are generally defined with regular expressions.

A token has essentially two properties:
- **type** — the kind of token (`Event-keyword`, `Identifier`)
- **payload** — the text that was matched (`events`, `doorClosed`)

For keywords the payload is basically irrelevant; only the type matters. For identifiers the payload
is the data that matters later in the parse. In practice tokens often carry more — notably line number
and character position, which is essential for error diagnostics.

**Why separate lexing from parsing** (Ch. 18, "The Lexer"):
- *Simplicity*: the parser can be written in terms of tokens rather than raw characters.
- *Efficiency*: the machinery for chunking characters into tokens differs from the machinery for
  parsing. In automata terms, **the lexer is usually a state machine while the parser is usually a
  push-down stack machine.**
- Fowler notes this traditional split is "being challenged by some more modern developments": ANTLR
  uses a push-down machine for its lexer, and some modern **scannerless parsers** combine lexing and
  parsing.

**Ordered rules, first match wins.** Lexer rules are tested in order and the first match succeeds. So
you can't use `events` as an identifier — the lexer will always recognize it as a keyword. Fowler:
"This is generally considered a Good Thing to reduce confusion, avoiding such things as PL/1's
notorious `if if = then then then = if;`." When you genuinely need to get round it, that's what
*Alternative Tokenization* is for.

**Whitespace.** For many languages the lexer strips whitespace so the parser never sees it. "This is a
big difference to *Delimiter-Directed Translation* where the whitespace usually plays a key
structuring role." If whitespace *is* syntactically significant — newlines as statement separators,
indentation signifying block structure — the lexer can't just ignore it and must generate tokens
indicating what's happening (see *Newline Separators*). But languages intended for Syntax-Directed
Translation usually try to make whitespace ignorable; many DSLs can do without any statement
separator at all.

**Comments.** Usually discarded by the lexer, and "it's always useful to have comments in even the
smallest DSL." But you may want to keep them — they can be useful for debugging, particularly in
generated code — in which case you must think about how to attach them to Semantic Model elements.

**Keep lexing simple — the context argument.** Fowler warns against fine-tuning token matching. In the
state controller example, event codes are four-character sequences of capitals and digits, so it's
tempting to define a dedicated `code` token type. Don't: an input like `FAIL FZ17` would tokenize
`FAIL` as a code rather than an identifier, "because the lexer only looks at the characters, not the
overall context of the expression. This kind of distinction is best left to the parser to deal with,
as it has the information to tell the difference between the name and the code." The four-character
check belongs later in the parse. General rule: **"it's best to keep lexing as simple as possible."**

**Three kinds of tokens** (Ch. 18, "The Lexer"):
- **Punctuation** — keywords, operators, other organizing constructs (parens, statement separators).
  Type matters, payload doesn't. Fixed elements of the language.
- **Domain text** — names of things, literal values. Token type is very generic ("number",
  "identifier"). Variable: every DSL script has different domain text.
- **Ignorables** — whitespace, comments; usually discarded by the tokenizer.

**Generated vs handwritten lexers.** Most Parser Generators provide lexer generation using regex
rules. But many people prefer to write their own — they're fairly straightforward using a *Regex
Table Lexer* (Ch. 20). Handwritten lexers give "more flexibility for more complex interactions
between the parser and the lexer, which can often be useful." The specific useful interaction Fowler
names: **supporting multiple modes in the lexer and allowing the parser to switch between modes**,
letting the parser alter how tokenizing occurs at certain points of the language — which is how you
implement Alternative Tokenization.

#### Layer 2: The Syntactic Analyzer

Given a stream of tokens, the parser's behavior divides into two sections:

- **Syntactic analysis** — takes the token stream and arranges the tokens into a parse tree. This work
  "can be derived entirely from the grammar itself," and in a Parser Generator it is automatically
  generated.
- **Actions** — take that syntax tree and do something more with it, such as populating a Semantic
  Model. "The actions cannot be generated from a grammar, and are usually executed while the parse
  tree is being built up." A Parser Generator's grammar file typically combines the grammar definition
  with additional code specifying the actions, usually in a general-purpose language (though some
  actions can be expressed in additional DSLs).

A parser built from the grammar alone, doing only syntactic analysis, produces just success or
failure — it tells you whether the input matches the grammar. This is called **recognizing** the
input.

**Many grammars match the same language.** Fowler shows two grammars for the same event-block input
that accept exactly the same set of inputs but produce *different parse trees* (one flattens the event
declarations directly under `eventBlock`, the other introduces an intermediate `eventList` node). "It's
important to realize that any given language can be matched by many grammars." Which grammar you pick
depends on how you want to control the parse — and different grammars also arise from differences
between Parser Generator tools. **The grammar is a design artifact with choices in it, not a
transcription of the language.**

**The parse tree usually isn't real.** Fowler is careful here: "So far I've talked about the parse tree
as if it's something that is explicitly produced by the parser as an output of the parse. However,
this is usually not the case." Typically you never access the parse tree directly; the parser builds
up pieces, runs actions in the middle of parsing, and discards each piece once done with it
(historically important to reduce memory consumption). Only with **Tree Construction** do you actually
produce a tree — and then usually a simplified AST rather than the full parse tree.

**Terminology** (Ch. 18, "Syntactic Analyzer") — the book's definitions, worth pinning down:
- Academic books often use "parse" as a synonym for *syntactic analysis only*, calling the whole
  process translation/interpretation/compilation. Fowler uses "parse" much more broadly, matching
  common field usage. Parser Generators call the token-consuming stage "the parser," so lexer and
  parser are spoken of as separate tools; Fowler follows that here even though, to be consistent with
  the rest of the book, parsing arguably should include lexing.
- **parse tree** — a tree that accurately reflects the parse with the grammar you have, with all
  tokens present: the raw tree.
- **abstract syntax tree (AST)** — a simplified tree, discarding unnecessary tokens and reorganized to
  suit later processing.
- **syntax tree** — the supertype of AST and parse tree; used when either would do.
- "As ever, the terminology in software varies rather more than we would like."

#### Layer 3: Output Production

The grammar suffices for recognition, but you want output. Three broad ways (Ch. 18, "Output
Production"): **Embedded Translation**, **Tree Construction**, and **Embedded Interpretation**. All
require something beyond the grammar, so you write additional code.

How you weave that code in depends on how you're writing the parser:
- **Recursive Descent Parser** — you add actions into the handwritten code.
- **Parser Combinator** — you pass action objects into the combinators using the facilities of your
  language.
- **Parser Generator** — you use *Foreign Code* to add code actions into the text of the grammar file.

#### Semantic Predicates

Syntactic analyzers, hand-written or generated, follow a core algorithm that recognizes input based on
a grammar. Sometimes the rules for recognition can't quite be expressed in the grammar — "most notable
in a Parser Generator."

A **semantic predicate** is "a hunk of general-purpose code that provides a Boolean response to
indicate whether a grammar production should be accepted or not — effectively overriding what's
expressed by the rule." It lets the parser do things beyond what the grammar can express.

Classic example: parsing C++ and hitting `T(6)`. Depending on context this is either a function call
or a constructor-style typecast; to tell them apart you need to know how `T` was defined, which cannot
be specified in a context-free grammar. Hence a semantic predicate resolves the ambiguity.

**Fowler's design position:** "You shouldn't come across the need to use semantic predicates for a
DSL, since you should be able to define the language in such a way as to avoid this need." That is a
language-design directive: if you need a semantic predicate, your DSL syntax is probably wrong.

### When to use it

(Ch. 18, "When to Use It")

- It's the alternative to Delimiter-Directed Translation.
- **Principal disadvantage:** "the need to get used to driving parsing via a grammar, while chopping
  up via delimiters is usually a more familiar approach." But "it doesn't take long … to get used to
  grammars, and once you do, they provide a technique that is much easier to use as your DSLs get more
  complex."
- **The key upside, stated as a design principle:** "the grammar file — itself a DSL — provides a clear
  documentation of the syntactic structure of the DSL it's processing. This makes it easier to evolve
  the syntax of the DSL over time."

Further reading Fowler cites: the Dragon Book [aho-dragon] as the usual starting point; [parr-LIP]
(Parr, *Language Implementation Patterns*) as an alternative, non-traditional route.

### SDK relevance

- **The layering is the lesson.** lexer → syntactic analyzer → actions → semantic model. Each layer
  raises the level of abstraction and each has a single responsibility. The lexer knows characters and
  nothing about context; the syntactic analyzer knows structure and nothing about meaning; the actions
  know meaning. When a decision needs context that a layer doesn't have (the `FAIL FZ17` case), it
  belongs in a higher layer — pushing it down produces a leaky abstraction that gets subtly wrong
  answers.
- **A declarative spec that documents itself.** "The grammar file — itself a DSL — provides a clear
  documentation of the syntactic structure." This is the argument for any schema/IDL/spec artifact in
  an SDK (OpenAPI, protobuf, type stubs): the value is not only that the machine reads it, but that
  a human can read the shape of the interface in one place and evolve it deliberately.
- **Many grammars, one language.** The same accepted inputs can be described by different structures,
  and the structure you choose determines what the downstream code looks like. Same in API design:
  many resource models can express the same capability, and the model you pick determines the shape of
  every client.
- **Recognition vs. output** is the same split as validation vs. deserialization. Recognition alone
  gives you a yes/no; useful, cheap, and worth having as an independent capability.
- **Semantic predicates as a design smell.** An escape hatch that lets your declarative spec be
  overridden by imperative code. Necessary for general-purpose languages; a sign of bad design in a
  DSL you control. Applies directly to schema/config systems: if users constantly need the escape
  hatch, the schema is wrong.

---

## Chapter 19: BNF
*(PDF pp. 166–173)*

**Intent (verbatim):** "Formally define the syntax of a programming language." (Fowler, DSL book,
Ch. 19 "BNF", intent)

The sketch is itself a BNF grammar *for BNF* — a nice self-describing touch.

### The concept

BNF — Backus-Naur Form — is a way of writing grammars that define the syntax of a language. Invented
to describe Algol in the 60s; since then BNF grammars have been widely used both for explanation and
to drive Syntax-Directed Translation.

Fowler's opening irony: "In a wonderful display of irony, BNF, a language for defining syntax, does
not itself have a standard syntax." Any BNF grammar will have obvious and subtle differences from any
other you've seen. "As a result, it's not really fair to call BNF a language; rather, I think of it as
a family of languages. When people talk about patterns, they say that with a pattern, you see it
differently every time — BNF is very much like that." (Ch. 19, "How It Works")

### How it works — the core vocabulary

**Production rules.** The primary commonality across all BNF variants: describing a language through a
sequence of production rules. Each rule has a **name** and a **body**. The body describes how to
decompose the rule into a sequence of **elements**. Elements may be other rules or **terminals**. A
terminal is something that isn't another rule — e.g. a literal. When you use a BNF grammar with
Syntax-Directed Translation, "your terminals will usually be the token types that come out of the
lexer." (Ch. 19, "How It Works")

**Syntactic variants.** Fowler shows the same tiny contact grammar in ANTLR style
(`rule : body ;`) and in something close to original Algol BNF (`<rule> ::= body`, rules quoted in
angle brackets, literal text unquoted, newline-terminated, `::=` as separator). "You'll see all of
these elements varied in different BNFs, so don't get hung up on the syntax." He uses ANTLR's syntax
throughout the book; Parser Generators typically use this style rather than the Algol style.

**Alternatives** (`|`). `line : email | tel ;` — decompose `line` into either `email` or `tel`. Used
alone, alternatives are limited (one email *or* one telephone), but Fowler notes "alternatives
actually unleash an enormous amount of expressive power" — the EBNF→basic-BNF conversion later in the
chapter shows why: everything else reduces to alternatives plus recursion.

**Extracting subrules for intent.** Fowler pulls `Identifier` out into a `username` rule even though
"the `username` rule only resolves to a single identifier, but it's worth doing to more clearly show
the intent of the grammar — **similarly to extracting a simple method in imperative code**." This is
an explicit statement that grammar writing is subject to the same readability discipline as code.

**Multiplicity symbols (Kleene operators).** `*` none-or-more, `+` one-or-more, `?` optional — the same
symbols you know from regexes. "Using multiplicity symbols like this makes it much easier to
understand grammars."

**Grouping.** A grouping construct lets you apply a multiplicity rule to several elements at once, so
you can inline subrules. Fowler's advice: **don't**, usually. "I wouldn't suggest doing this, because
the subrules capture intent and make the grammar much more readable. But there are occasions where a
subrule adds clutter and grouping operators work out better."

**Formatting.** Most BNFs ignore line endings, so put each logical piece of a rule on its own line for
complicated rules, and put the semicolon on its own line to mark the end. Fowler prefers this style
"once the rule becomes too complicated to fit easily on a single line."

**basic BNF vs EBNF.** "Adding multiplicity symbols is usually what makes the difference between EBNF
(extended BNF) and basic BNF." Terminology is muddled in the wild. In this book: **"basic BNF"** means
without multiplicity symbols; **"BNF"** unqualified includes any BNF-like language, EBNF included.

**Bracket style.** An alternative notation replaces `?` with `[..]` and `*` with `{..}`; there's no
replacement for `+`, so `foo+` becomes `foo {foo}`. This bracketing style is common in grammars
intended for human consumption and is the style used by the ISO standard for EBNF (ISO/IEC 14977).
Most Parser Generators prefer the regex form, which is what Fowler uses.

**Other useful operators.**
- **up-to** (`~` in ANTLR): matches everything up to the element following it. `~'}'` matches all
  characters up to but not including a close brace. Equivalent regex: `[^}]*`.
- **range** (`..`): identifies a range of characters, e.g. `'a'..'z'`. Fowler notes ranges "only make
  sense in lexical rules, not syntactic rules. They are traditionally also rather ASCII-centric, which
  makes it difficult to support identifiers in languages other than English." (A real
  internationalization caveat.)

**Lexical vs syntactic rules.** Most approaches to Syntax-Directed Translation separate lexical from
syntactic analysis. You *can* define lexical analysis in production-rule style, "but there are usually
subtle but important differences as to what kinds of operators and combinations are allowed. Lexical
rules are more likely to be close to regular expressions, if only because regular expressions are
often used for lexical analysis since they use a finite-state machine rather than a parser's push-down
machine."

**Operator summary table** (Ch. 19):

| symbol | meaning | example |
|---|---|---|
| `\|` | alternative | `email \| tel` |
| `*` | none or more (Kleene star) | `tel*` |
| `+` | one or more (Kleene plus) | `email+` |
| `?` | optional | `fullname?` |
| `~` | up-to | `~'}'` |
| `..` | range | `'0'..'9'` |
| `/` | ordered alternative | `us_tel / raw_tel` |

### Parsing Expression Grammars (PEGs)

Most BNF grammars you'll run into are **context-free grammars (CFG)**. A recent style is the **parsing
expression grammar (PEG)**. "The biggest difference between a PEG and a CFG is that PEGs have
**ordered alternatives**." (Ch. 19, "Parsing Expression Grammars")

In a CFG, `contact : email | tel;` — the order you write the alternatives doesn't affect the
interpretation. Usually fine, but "occasionally having unordered alternatives leads to ambiguities."

Fowler's worked case: you want to recognize a well-formed ten-digit sequence as a US telephone number,
but capture anything else as an unstructured raw number. A CFG with `tel : us_number | raw_number ;`
is ambiguous for input like `312-373 1000` because both rules match it. An **ordered alternative**
forces the rules to be tried in order, and whichever matches first is the one used. Common syntax is
`/`: `tel : us_number / raw_number ;`.

Practical note: "although ANTLR uses unordered alternatives, they act more like ordered ones. For this
kind of ambiguity, ANTLR will report a warning and go with the first alternative that matches."

### Converting EBNF to basic BNF

Sometimes necessary because some Parser Generators only accept basic BNF. Multiplicity symbols make
BNF easier to follow but "they don't increase the expressive power of BNF" — any EBNF grammar has an
equivalent basic BNF grammar. **The key to every transformation is alternatives.** (Ch. 19, "Converting
EBNF to Basic BNF")

- **Optional**: replace `foo?` with `foo | ` (foo or nothing). Fowler annotates the empty branch with a
  comment (`/* optional */`) to make it readable — and notes that when a tool doesn't support the
  comment syntax of the language he's writing in, he uses C-style comments "without hesitation."
- **Folding**: if the parent clause is simple you can fold the alternative into the parent —
  `a : b? c` becomes `a : c | b c`. But with several optional elements "you get into a combinatorial
  explosion, which, like most explosions, isn't something that's fun to be in the middle of."
- **Repetition**: use **recursion**. Replace `x : y*` with `x : y x | ` . "It's quite common for rules
  to be recursive — that is, to use the rule itself in its body."
- **Left vs right recursion**: `x : y*` can become `x : y x` (right) or `x : x y` (left). "Usually your
  parser will tell you to prefer one over the other due to the algorithm it's using. For example, a
  **top-down parser cannot do left recursion at all**, while Yacc can do either but prefers right
  recursion." This is the same constraint that shows up in Ch. 21 as recursive descent's inability to
  handle left recursion.
- **One-or-more**: `x : y+` becomes `x : y | x y` (or `x : y | y x` to avoid left recursion).
- **Intermediate rules**: transforming to basic BNF often requires introducing extra intermediate
  subrules (e.g. extracting `singleEmail` because the single-email expression is now used twice); you
  also have to do this if you have groups.
- **Cost**: the resulting grammar "works just fine, but … is much harder to follow. Not only do I lose
  the multiplicity markers, I also have to introduce extra subrules just to make the recursion work
  properly. As a result, I always prefer to use EBNF if all else is equal."

### Code Actions

BNF defines syntactic structure and Parser Generators use it to drive the parser. "BNF, however, isn't
enough. It provides enough information to generate a parse tree, but not enough to come up with a more
useful abstract syntax tree, nor to do further tasks like Embedded Translation or Embedded
Interpretation. So the common approach is to place **code actions** into the BNF in order for the code
to react." (Ch. 19, "Code Actions")

Not all Parser Generators use code actions — another approach is a separate DSL for something like Tree
Construction.

**Basic idea:** place snippets of *Foreign Code* at certain places in the grammar; they execute when
that part of the grammar is recognized by the parser.

**Referring to parsed elements.** Code actions usually need the data that was recognized, not just the
fact of recognition. Approaches differ by tool:
- Classic Yacc: **positional variables** (`$1`, `$2`) indexing the element position. "Positional
  references are brittle to changes in the grammar."
- Modern generators (ANTLR): **label the elements** (`e=EmailAddress`, then `$e.text`). Better.
- Mechanism: "In order to resolve these references, Parser Generators run code actions through a
  templating system, which replaces expressions like `$e` with the suitable values." ANTLR goes
  further — attributes like `text` don't refer to fields or methods directly; ANTLR performs further
  substitution to get the right information.

**Rules returning values.** You can also refer to a *rule* rather than a token, but "returning some
rule object like this isn't too helpful, particularly when we are matching larger rules." So Parser
Generators usually let you **define what a rule returns when it's matched** (ANTLR: a return type and
variable per rule; ANTLR allows multiple return values). "You can return anything you like from a rule
and then refer to that in the parent. … **This facility, combined with code actions, is extremely
important. Often, the rule that gives you the best information about a value isn't the best rule to
decide what to do with that data. Passing data up the rule stack allows you to capture information at
a low level in a parse, and deal with it at a higher level. Without this, you would have to use a lot
of *Context Variables* — which would soon get very messy.**" (Ch. 19, "Code Actions")

**Placement determines timing.** "The position of a code action in a grammar determines when it's
executed." `parent : first {log("hello");} second` calls `log` after the first subrule is recognized
but before the second. "Most of the time it's easiest to put code actions at the end of a rule, but
occasionally you need to put them in the middle." Caveat: "the sequence of execution of code actions
can be hard to understand, because it depends on the algorithm of the parser. **Recursive-descent
parsers are usually pretty easy to follow, but bottom-up parsers often cause confusion.** You may need
to look at the details of your parser system to understand exactly when code actions get executed."

**The big danger.** "One of the dangers of code actions is that you can end up putting a lot of code in
them. If you do this, the grammar becomes hard to see, and you lose most of the documentation advantage
it brings. I thus strongly recommend that you use *Embedment Helper* when using code actions."

### When to use it

(Ch. 19, "When to Use It") — short and pointed:

- "You'll need to use BNF whenever you are working with a *Parser Generator*, as these tools use BNF
  grammars to define how to parse."
- "**It's also very useful as an informal thinking tool to help visualize the structure of your DSL, or
  to communicate the syntactic rules of your language to other humans.**"

That second sentence is the whole "grammar-first thinking" argument in one line: BNF's value is not
only as machine input. Even if you'll implement with Delimiter-Directed Translation or hand-rolled
code, sketching the grammar is how you *design and communicate* the language.

### SDK relevance

- **Grammar-first as a design discipline.** Sketching BNF before implementing forces you to decide what
  the units of your language are and how they nest — the same discipline as writing the type signatures
  or the IDL before writing the implementation. Fowler explicitly endorses BNF as an *informal* thinking
  and communication tool independent of any tooling.
- **Extract subrules to express intent**, even when a subrule resolves to a single element — the direct
  analogue of extracting a well-named function. Naming the parts of a spec is the same work as naming
  the parts of a program.
- **Named references beat positional references.** Yacc's `$1`/`$2` vs ANTLR's labels is the same
  argument as keyword arguments vs positional arguments, or named struct fields vs tuples: positional
  is brittle under change. This is a general API-design rule with a concrete historical example
  attached.
- **Returning values up the rule stack removes Context Variables.** Capture data at the level that knows
  it best, hand it upward to the level that decides what to do with it, rather than stashing it in
  shared mutable state. This is a direct argument for return values / explicit data flow over
  ambient/global context in library design.
- **Keep the declarative artifact thin** (Embedment Helper): the spec should contain single method
  calls, not logic. Once logic leaks into the spec, the spec stops being documentation. Same reason
  build files, config files, and schema files should not accumulate procedural code.
- **Ordered vs unordered alternatives** is a resolution-strategy decision that shows up everywhere in
  API design (route matching, overload resolution, dispatch tables). Ordered = deterministic and
  explainable; unordered = declarative but ambiguity-prone. ANTLR's compromise — accept unordered
  syntax, warn on ambiguity, resolve in order — is a decent pattern to copy.
- **Expressive sugar vs. minimal core.** EBNF's multiplicity operators add no expressive power over
  basic BNF but massively improve readability; the mechanical desugaring exists and is ugly. That is
  exactly the argument for convenience layers in an SDK: no new capability, large usability gain,
  provided the desugaring is well-defined.

---

## Chapter 20: Regex Table Lexer
*by Rebecca Parsons — (PDF pp. 173–177)*

**Intent (verbatim):** "Implement a lexical analyzer using a list of regular expressions."
(Fowler/Parsons, DSL book, Ch. 20 "Regex Table Lexer", intent)

The sketch is literally a two-column table: pattern → token type (`^events` → `K_EVENT`, `^end` →
`K_END`, `^(\w)+` → `IDENTIFIER`, `^(\s)+` → `WHITESPACE`).

### The concept

"Parsers primarily deal with the structure of a language, specifically the way components of the
language can be combined. The most basic language components — such as keywords, numbers, and names —
can clearly be recognized by the parser. However, we generally separate this stage out into a lexical
analyzer. **By using a separate pass to recognize these terminal symbols, we simplify the construction
of the parser.**" (Ch. 20, intro)

Why this is easy: "Lexical analyzers stay firmly in the space of regular languages, which means we can
use standard regular expression APIs to implement them." A Regex Table Lexer is a list of regexes, each
associated with a particular terminal symbol. You scan the input, relate individual pieces of it to the
proper regexes, and generate a stream of tokens naming individual terminal symbols. That token stream
is the parser's input.

### How it works

**The scanning algorithm.** Scan the input string from the beginning, matching tokens and consuming
characters as you go. Regexes are anchored to the start of the remaining string (the `^` operator).
Walk the list of recognizers in order until one matches; on a match, emit the token, advance the input
pointer past the match, and **return to the beginning of the regex list** — because ordering matters.
Repeat until the input is consumed. Parsons illustrates with a deliberately silly `Hello`/`Goodbye`
example on the input `HelloGoodbyeHelloHelloGoodbye` producing
`HOWDY, BYEBYE, HOWDY, HOWDY, BYEBYE`.

**Ordering is a design decision.** "The order of checking the patterns is important so that we can
properly handle things like keywords. In the state machine grammar, for example, our keywords also
match the rules for identifiers. We order the checks for keywords first, so that the proper token will
appear for our keywords."

**Token-set selection is a design decision.** "Selection of appropriate tokens is a design decision for
the lexical analyzer." In the state machine grammar they deliberately **do not** distinguish between
four-character codes and names, using a single identifier token for both. "This choice is necessary,
since the lexer doesn't have the context to know that a four-letter name should match the identifier
token, if it isn't in the position where a code is legal." (Same point Fowler makes in Ch. 18 with
`FAIL FZ17`.) Typically the token set includes keywords, names, numbers, punctuation, and operators.

**The table.** You instantiate a particular lexical analyzer by specifying the recognizers, held in a
table or list to fix their order. Each **recognizer** contains three things:
1. the **token type** (used to identify the token class to the parser),
2. the **regular expression** to recognize that token,
3. a **Boolean** saying whether this token should be emitted into the output stream.

The Boolean is how you handle "semantically meaningless whitespace and comments. While these strings
are in the input stream and must be handled by the lexer, we don't pass the corresponding tokens on to
the parser." The repeated sequential scan of the table enforces match ordering, and the table "makes it
simple to introduce additional token types."

**Matching detail.** The single-token matcher steps through the recognizers; on a match it consumes the
matched input and sends the token to the output stream if the output flag is set. The token value
(payload) is populated whether needed or not — "generally, token values are only needed for
identifiers, numbers, and sometimes operators, but this approach saves us another Boolean flag and
simplifies the code." The main scanner loop repeatedly invokes the single-match method, checking that
recognition succeeded. If a scan of the remaining string fails to match anything, the overall lexical
analysis fails. Once the input is fully consumed and matching succeeded throughout, the token buffer
goes to the parser.

**Diagnostics.** "To help with error diagnostics, you can add information to the token about where that
token was in the character stream — for example, a line number and column position."

### When to use it

(Ch. 20, "When to Use It")

- "While lexical analysis generators, such as Lex, do exist, **there is little need to use them given
  the prevalence of regular expression APIs.** One exception is using ANTLR as the *Parser Generator*,
  since the lexical analysis and parsing are more tightly integrated in that tool."
- "The implementation described here is an obvious one. Its performance clearly depends on the specifics
  of the regular expression API used. **The only time I would suggest not using Regex Table Lexer would
  be if there is no acceptable regular expression API available.**"
- "Given the simple syntax of many DSLs, it is possible for this approach to be used to recognize the
  full language. As long as the language is regular, this approach applies for the parser as well."
  (i.e. if your DSL is actually a regular language, you may not need a parser at all.)

This is close to an unconditional recommendation: the pattern is cheap, it's obvious, and the tooling
alternative buys little.

### The example (conceptually)

Lexing Miss Grant's controller in Java. "The lexical analyzer for the state machine grammar is quite
typical. We call out tokens for our keywords, punctuation, and a token type for identifiers. We also
have a token type for comments and whitespace, which are just consumed by the lexer." Uses
`java.util.regex`.

The design point worth keeping: **"The implementation is split into the specification of the tokens to
recognize and the lexical analysis algorithm itself. This approach makes it easy to add additional
token types to the lexer."** The token types live in a Java enum where each constant carries its regex
and its output Boolean — a data table — while the scanning engine is separate and generic. Parsons
notes the enum "is a clean one in Java, but you could just as easily use a more traditional object.
However, the token types do need to be readily available for use in the parser itself."

### SDK relevance

- **Table-driven design: data + generic engine.** The whole pattern is "put the varying part in a table
  and write one engine that walks it." Adding a token type is a data change, not a code change. This is
  the archetype for extensible registries, dispatch tables, rule engines, and plugin catalogs in an
  SDK.
- **Ordered matching with first-match-wins** is a simple, explainable resolution rule. When you build a
  registry that can have overlapping entries, defining order semantics explicitly (and documenting that
  more-specific entries go first) avoids a whole class of surprising behavior.
- **Filter at the earliest layer that can do it correctly.** The output Boolean is a filter in the lexer
  for things the parser must never see. But note the constraint from the token-set discussion: filter
  or classify only when the layer has enough context to be right.
- **Uniform payload population** ("populate tokenValue whether it's needed or not") is a small but real
  API simplification: fewer flags, fewer conditional shapes, one uniform record type. Cost is a little
  wasted work; benefit is a simpler contract.
- **Carry provenance in your data structures.** Line/column on each token exists purely so errors can
  point at the source. Any library that transforms user input should propagate source location through
  every intermediate representation.

---

## Chapter 21: Recursive Descent Parser
*by Rebecca Parsons — (PDF pp. 177–183)*

**Intent (verbatim):** "Create a top-down parser using control flow for grammar operators and recursive
functions for nonterminal recognizers." (Fowler/Parsons, DSL book, Ch. 21 "Recursive Descent Parser",
intent)

### The concept

The motivating tradeoff, stated up front: "Many DSLs are quite simple as languages. While the
flexibility of external languages is appealing, using a *Parser Generator* to create a parser
introduces new tools and languages into a project, complicating the build process. A Recursive Descent
Parser supports the flexibility of an external DSL without requiring a Parser Generator." (Ch. 21,
intro)

You can implement it in whatever general-purpose language you choose. It uses **control flow operators
to implement the grammar operators**, and **individual methods/functions to implement the parsing rules
for the different nonterminal symbols**.

### How it works

**Still layered.** "As in the other implementations, we again separate lexical analysis and parsing. A
Recursive Descent Parser receives a token stream from a lexical analyzer, such as a *Regex Table
Lexer*."

**Basic structure.** "There is a method for each nonterminal symbol in the grammar. This method
implements the various production rules associated with the nonterminal. **The method returns a Boolean
value which represents the result of the match.** Failure at any level gets propagated back up the call
stack. Each method operates on the token buffer, advancing the pointer through the tokens as it matches
some portion of the sentence."

**The grammar-operator → control-flow mapping** (Ch. 21, "How It Works"). Because there are only a few
grammar operators (sequencing, alternatives, repetition), the implementation methods take on a small
number of patterns:

| Grammar rule | Implementation shape |
|---|---|
| `C : A \| B` | `if (A()) then true else if (B()) then true else false` |
| `C : A B` | `if (A()) then { if (B()) then true else false } else false` |
| `C : A?` | `A(); true` (can't fail — optional) |
| `C : A*` | `while A(); true` |
| `C : A+` | `if (A()) then { while (A()); true } else false` |

Notes on these:
- The alternative implementation "clearly checks one alternative and then the other, **acting more like
  an ordered alternative**. If you truly need to allow for the ambiguity introduced by unordered
  alternatives, it might be time for a *Parser Generator*." (Direct callback to the PEG discussion in
  Ch. 19.)
- Sequencing is nested `if`s because you don't continue processing if one method fails.
- `A?` is different in that there's no way to fail: match or not, you return true.
- `A+` returns true as soon as one `A` matched, then greedily consumes more; `A*` is `A+` with the outer
  `if` removed.

**Two invariants that make the whole thing work** (Ch. 21, "How It Works"). Parsons is explicit that the
approach is only as clean as it is because the methods behave consistently:

1. **Token buffer management.** "If the method matches what it is looking for, the current position in
   the input token string is advanced to the point just past the matched input. … If the match fails,
   the position of the buffer should be the same as it was when the method was called. This is of most
   importance for sequences. At the beginning of the function, we need to save the incoming buffer
   position, in case the first part of the sequence matches … but the match for B fails. **Managing the
   buffer thus allows alternatives to be properly handled.**"
2. **Model/tree population.** "As much as possible, each method should manage its own pieces of the
   model or create its own elements in the syntax tree. Naturally, any actions should only be taken when
   the full match has been confirmed. As with the token buffer management for sequences, **actions must
   be deferred until the entire sequence completes**."

Together these are a transactional discipline: *no side effects until the match is confirmed; restore
state exactly on failure*. Same shape as speculative execution with rollback.

**Actions.** "We use the same style of helper functions as in the other sections to keep the actions
distinct from the parsing. *Tree Construction* and *Embedded Translation* are both possible in recursive
descent."

**The grammar is still there.** Parsons closes "How It Works" with a point that reframes the whole
chapter: "One complaint about Parser Generators is that they require developers to become familiar with
language grammars. While it is quite true that the syntax of the grammar operators does not appear in
the recursive descent implementation, **a grammar clearly exists in the methods. Changing the methods
changes the grammar. The difference is not in the presence or absence of the grammar but in how the
grammar is expressed.**"

### When to use it

(Ch. 21, "When to Use It")

**Strengths:**
- "**The greatest strength of Recursive Descent Parser is its simplicity.** Once you understand the
  basic algorithm and how to handle various grammar operators, writing a Recursive Descent Parser is a
  simple programming task."
- "You then have a parser in an ordinary class in your system." No special build step, no generated
  code, no foreign toolchain.
- "**Testing approaches work in the same way they always do; in particular, a unit test makes more
  sense when the unit is a method, just like any other.**"
- "Since the parser is simply a program, it is easy to reason about its behavior and debug the parser.
  The Recursive Descent Parser is a direct implementation of a parsing algorithm, making the tracing
  through the parse much easier to discern." Ordinary debuggers work.

**Weaknesses:**
- "**The most serious shortcoming of Recursive Descent Parser is that there is no explicit
  representation of the grammar.** By encoding the grammar into the recursive descent algorithm, you
  lose the clear picture of the grammar, which can only live in documentation or comments. Both *Parser
  Combinator* and *Parser Generator* have an explicit statement of the grammar, making it easier to
  understand and evolve."
- "Another problem … is that you have a top-down algorithm that can't handle left-recursion, which makes
  it more messy to deal with *Nested Operator Expressions*." (Ties directly to the left-vs-right
  recursion discussion in Ch. 19.)
- "Performance will also be usually inferior to a Parser Generator. In practice, these disadvantages
  aren't such a factor for DSLs."
- **Look-ahead is the practical limit:** "A Recursive Descent Parser is straightforward to implement as
  long as the grammar is reasonably simple. One of the factors that can make it easy to deal with is
  limited look ahead — that is, how many tokens the parser needs to peek forward to determine what to do
  next. **Generally, I wouldn't use Recursive Descent Parser for a grammar that requires more than one
  symbol of look ahead; such grammars are better suited to Parser Generators.**"

Further reading: [parr-LIP] for a less-traditional programming-language context; the Dragon Book
[aho-dragon] as the standard reference.

### The example (conceptually)

Miss Grant's controller in Java. Structure: a parser class holding the token buffer, the resulting state
machine, and various collections (events, commands, reset events, states, a partial state). The
implementation is written **grammar-first**: for each production rule shown (`stateMachine : eventBlock
optionalResetBlock optionalCommandBlock stateList`, `eventBlock : eventKeyword eventDecList
endKeyword`, `eventDecList : eventDec+`, `eventDec : identifier identifier`, etc.), the corresponding
method is a mechanical application of the operator table. That mechanical correspondence *is* the
pattern.

Design points worth keeping:
- The top-level entry method is also responsible for final construction of the state machine on success
  (loading reset events) — one place where whole-parse completion work happens.
- Helper functions keep actions separate: `consumeIdentifier` advances the buffer and returns the token
  value; `makeEventDec` does the model population. Recognition and action stay in different methods.
- **Forward references:** "Since transitions can refer to states that don't yet exist, our helper
  functions must allow for a reference to a state that has not yet been defined. **This property holds
  true for all the implementations that don't use *Tree Construction*.**" (i.e. single-pass translation
  forces you to design for forward references; Tree Construction lets you make multiple passes instead
  — this is the setup for Ch. 24's "when to use it".)
- For a simple optional block, the operator patterns can be inlined rather than each getting its own
  method — judgement, not dogma.

### SDK relevance

- **"The grammar exists whether or not you write it down."** This generalizes hard: your library has a
  protocol/schema/state machine whether or not there's an artifact stating it. The choice is only
  whether it's explicit and reviewable or implicit and scattered through the code. Fowler/Parsons make
  the identical argument about implicit vs. explicit grammars that applies to implicit vs. explicit API
  contracts.
- **Transactional semantics on failure.** "On failure, restore the position exactly as it was; take no
  actions until the match is confirmed." Any library operation that can partially succeed should either
  fully commit or fully restore. Partial mutation on failure is the defect this discipline prevents.
- **Ordinary code has ordinary tooling.** Being "a parser in an ordinary class in your system" means
  normal unit tests, normal debuggers, normal stack traces, normal refactoring. That's the standing
  argument against introducing codegen/DSL machinery for problems small enough to solve directly — and
  it's the same argument for keeping SDK internals in plain code rather than clever metaprogramming.
- **Know your complexity threshold in advance.** "More than one symbol of look ahead → use a Parser
  Generator" is a concrete, checkable rule for when to abandon the hand-rolled approach. Useful
  practice: define the tripwire that says "stop hand-rolling" *before* you start.

---

## Chapter 22: Parser Combinator
*by Rebecca Parsons — (PDF pp. 183–194)*

**Intent (verbatim):** "Create a top-down parser by a composition of parser objects."
(Fowler/Parsons, DSL book, Ch. 22 "Parser Combinator", intent)

The sketch is an object tree: a Sequence Combinator whose children are a Terminal Parser (`TT_EVENT`),
a List Combinator (whose child is another Sequence Combinator of two `TT_IDENTIFIER` Terminal Parsers),
and a Terminal Parser (`TT_END`). i.e. the grammar rendered as a composite object graph.

### The concept

Positioning: "Even though our premise is that Parser Generators are not nearly as difficult to work
with as they are perceived to be, there are legitimate reasons to avoid them if possible. **The most
obvious issue is the additional steps in the build process required to first generate the parser and
then build it.** While Parser Generators are still the right choice for more complex context-free
grammars, particularly if the grammar is ambiguous or performance is crucial, directly implementing a
parser in a general-purpose language is a viable option." (Ch. 22, intro)

The pattern: "A Parser Combinator implements a grammar using a structure of parser objects. Recognizers
for the symbols in the production rules are combined using *Composites [gof]*, which are referred to as
combinators. **Effectively, parser combinators represent a *Semantic Model* of a grammar.**"

That last sentence is the crux. A parser combinator structure *is* the grammar, as live objects.

### How it works

**Still layered.** "As with *Recursive Descent Parser*, we use a lexer, for example a *Regex Table
Lexer*, to perform the lexical analysis of the input string. Our Parser Combinator then operates on the
resulting token string."

**Where the name comes from.** "The term 'combinator' comes from functional languages. **Combinators are
designed to be composed to create more complex operations of the same type as their input.** So, parser
combinators are combined to make more complex parser combinators. In functional languages, these
combinators are first-class functions, but we can do the same with objects in an object-oriented
environment."

**The build-up.** Start with the base cases — recognizers for the terminal symbols. Then use combinators
implementing the various grammar operators (sequence, list, etc.) to implement the production rules.
"Effectively, for each nonterminal in our grammar, we have a combinator for it, just like in Recursive
Descent Parser we have a recursive function for each nonterminal."

**What each combinator is responsible for:** "recognizing some portion of the language, determining if
there is a match, consuming the relevant tokens from the input buffer for the match, and performing the
required actions. **These operations are the same as those required by the recursive functions in
Recursive Descent Parser.**"

**The central design insight** (Ch. 22, "How It Works"): "What's really happening here is that **we
abstract out the fragments of logic associated with processing the grammar operators for top-down
parsing and create the combinators to hold that logic. While a *Recursive Descent Parser* combines those
fragments with function calls in inline code, a Parser Combinator combines these by linking together
objects in an *Adaptive Model*.**"

So: same algorithm, same operator semantics as recursive descent — but the *composition* moves out of
code and into a runtime object graph. That's a refactoring from "logic duplicated per rule" to "logic
implemented once per operator, composed as data."

**Combinator signature.** "Individual parser combinators accept as input the status of the match so far,
the current token buffer, and possibly a set of accumulated action results. Parser combinators return a
match status, a possibly altered token buffer, and a set of action results." (Initially the chapter
assumes buffer and results are kept in background state, then relaxes that assumption later.)

**Terminal recognizer (base case).** "The actual recognition of a terminal symbol is easy; we simply
compare the token at the current position in the input token buffer to whatever terminal symbol,
represented by a token, the recognizer is for. If the token matches, we advance the current position in
the token buffer."

**Operator combinators.** Each mirrors the recursive descent pattern exactly:
- *alternative* (`C : A | B`): try one combinator; if its match status is true, `C`'s return value is
  that combinator's return value. Cycle through the alternatives; if all fail, return a failed match
  status with the input token buffer unchanged. "As you can see, this logic looks just like the
  recursive descent algorithm."
- *sequence* (`C : A B`): step through the components; if any match fails, reset the token buffer to its
  input state.
- *optional* (`C : A?`): try `A`, return true either way.
- *one-or-more list* (`C : A+`): require one `A`, then loop until failure; if the initial match fails,
  return false with the input tokens.
- *zero-or-more list*: always return true, handling the token buffer appropriately.

**The invariant everything relies on:** "If the match succeeds, the tokens relating to that match are
consumed in the token buffer. If the match fails, the combinator returns an unaltered token buffer."
(Identical discipline to recursive descent.)

**Where the power comes from.** "The combinator implementations shown here are direct implementations of
specific rules. **The power of parser combinators comes from the fact that we can construct the
composite combinators from the component combinators.**" So `C : A B` becomes a *declaration*:
`C = new SequenceCombinator(A, B)` — "**where the logic implementing the sequencing is shared across all
such rules.**"

That is the payoff sentence for composability: write each operator's logic once, then express any
grammar as a declarative assembly of operator instances.

### Dealing with the actions

(Ch. 22, "Dealing with the Actions")

Actions vary by output style: in *Tree Construction* they build the AST as the parse proceeds; in
*Embedded Translation* they populate the semantic model. "The type of the match value will obviously
vary based on what the actions are."

- **Terminal combinator:** on success, populate the match value with the result of the match and invoke
  the actions on that match value. For an identifier recognizer you might record it in a *Symbol Table*;
  for terminals like identifiers and numbers the action often simply records the token value for later
  use.
- **Sequence:** "once we have recognized all the components of the sequence, we need to call the action
  on the list of match values from the individual components." The match values from `A` and `B` must be
  saved so they can be used in the action.
- **Alternative:** performs only the actions for the selected alternative.
- **List:** like sequence, must operate on all the match values.
- **Optional:** only performs the actions on match.

**Associating actions with combinators — the language-dependent API problem.** "The invocations for the
actions are relatively straightforward. **The challenge is getting the proper action methods associated
with the combinator.** In languages with closures or other ways of passing functions as parameters, we
could simply have the details of the action method passed into the constructor as a function. In
languages without closures, such as Java, we need to be a bit more clever. One approach is to extend the
operator classes with classes specific to a particular production rule and override the action method to
introduce the specific behavior."

(The Java example does exactly that: inner classes extending `SequenceCombinator` etc., overriding the
`action` hook.)

**Building an AST with actions:** "the match values passed to the action function would be the trees
constructed for the different components, and the action would combine those parse trees as implied by
the grammar rule in question. For example, a list operator will commonly have some node type in the
syntax tree representing the list. The list operator action would then create a new subtree with that
list node as the root, and make the subtrees from the component matches the children of this root."

### Functional style of combinators

(Ch. 22, "Functional Style of Combinators")

Relax the assumption that action results and the token buffer live in background state. "**Thought of in
the functional style, a combinator is a function that maps an input combinator result value to an output
combinator result value.**" The components of a combinator result value are:
1. the current state of the token buffer,
2. the current status of the match,
3. the current state of the cumulative actions performed so far.

In this style, "the saves are unnecessary since the input parameter's value remains valid. This version
also makes more explicit how the token buffer is handled and where the action values come from."

This is a compact statement of *threaded immutable state*: instead of mutating shared background state
and saving/restoring on failure, each combinator is a pure function `Result -> Result`, and "restore on
failure" becomes "return the input result value unchanged."

### When to use it

(Ch. 22, "When to Use It")

- **The positioning line:** "This approach occupies a nice middle ground between *Recursive Descent
  Parser* and using a *Parser Generator*."
- **Explicit grammar without the build cost.** "A significant benefit of using a Parser Generator is an
  explicit grammar specification for the language. The grammar in a Recursive Descent Parser is implied
  in the functions but is difficult to read as a grammar. With the Parser Combinator approach, **the
  combinators can be defined declaratively** … While it does not use *BNF* syntax, the grammar is clearly
  specified in terms of the component combinators and the operators. So with Parser Combinator, you get
  a reasonably explicit grammar without the build complications that tend to come with Parser
  Generator."
- **Language fit.** "Libraries exist that implement the various grammar operators in different languages.
  **Functional languages are an obvious choice** to implement a Parser Combinator, given their support
  for functions as first-class objects which allows for passing an action function as a parameter to the
  combinator constructor. However, implementations in other languages are quite possible too."
- **Same top-down restrictions apply** as Recursive Descent Parser (so: no left recursion, look-ahead
  limits, performance).
- **Same debugging advantages apply**, "in particular the ease of reasoning about when actions are
  performed. Even though a Parser Combinator is a very different implementation of a parser, the control
  algorithm of the parsing can be tracked using the same tools we use for debugging other programs."
- **The layering payoff:** "**Indeed, the Parser Combinator approach coupled with an operator library or
  tested operator implementations allows the language implementer to focus on the actions rather than
  the parsing.**"
- **Downsides:** "The biggest downside to a Parser Combinator is that **you still have to build it
  yourself**. In addition, you won't get the more sophisticated parsing and error handling features that
  a mature Parser Generator gives you out of the box."

### The example (conceptually)

Java implementation of the Miss Grant state machine using combinator objects + Embedded Translation.
Design observations worth keeping (no code):

- **Grammar productions are listed in reverse order** relative to the usual top-down presentation, "to
  match the implementation strategy we're using" — because in an object-composition approach you must
  construct the components before you can construct the composites. *The construction order of the object
  graph dictates the declaration order.*
- A base `Combinator` class with two members: an abstract `recognizer(CombinatorResult) : CombinatorResult`
  and an `action(MatchValue...)` **hook method** with an empty default body. "All combinators have two
  functions" — recognition and action — and the default no-op action means most combinators need no
  action code at all.
- `CombinatorResult` holds exactly the three things from the functional-style discussion: token buffer,
  match status, match value.
- Every recognizer begins with a **guard clause**: if the inbound match status is false, return the
  inbound result immediately. Failure short-circuits the entire composite without special-casing.
- `SequenceCombinator` and `OptionalSequenceCombinator` both extend a shared
  `AbstractSequenceCombinator` carrying the list of component combinators plus an `isOptional` Boolean.
  Deliberate design choice, explained: "we've chosen to make separate classes for optional and required
  sequences, sharing the implementation, rather than introducing an optional operator and adding another
  level of production rules to the grammar." — i.e. **the implementation structure is allowed to differ
  from the canonical grammar structure when it makes the grammar simpler.**
- `ListCombinator` collects an unknown number of match values in a list and converts to an array to fit
  the varargs signature of the action method — a small note that the action-invocation signature is part
  of the framework's public contract.
- **All the operator classes' default actions are no-ops.** The domain behavior (populating the state
  machine) lives only in per-rule subclasses overriding `action`. So: a small, reusable, fully generic
  operator library + a thin layer of rule-specific behavior. That's the whole architecture.

### SDK relevance

This chapter is the most directly transferable one in the range for API/library design.

- **Combinators as an API design template.** A combinator library is: (a) a small set of primitive
  values, (b) a small set of operators that take values of the type and return values of the same type,
  (c) closure under composition, (d) a uniform result type threaded through the whole structure. Any API
  with that shape composes without limit and can be learned in an afternoon. Contrast with an API of
  fifty unrelated methods.
- **"Logic implemented once per operator, shared across all rules."** The entire argument for combinator
  APIs over hand-written per-case code: you stop duplicating control-flow logic and start declaring
  structure. Directly applicable to query builders, validators, middleware chains, retry/backoff
  policies, stream processing, and test fixtures.
- **Same-type-in / same-type-out is what makes composition possible.** If an operator returns a
  different type from its inputs, composition stops. This is the design constraint to protect above all
  others.
- **Threaded state vs. ambient state.** The functional-style section is a clean statement of why pure
  `Result -> Result` functions are easier: no save/restore, explicit data flow, obvious provenance of
  every value. When designing a pipeline API, prefer passing an explicit context/result value over
  mutating shared state.
- **Hook methods with no-op defaults** are how you make a framework extensible without forcing every
  user to implement everything. Most combinators never override `action`.
- **Guard clauses that short-circuit propagate failure through a composite for free** — no special
  handling at each node.
- **Language capability determines the ergonomic API.** Closures → pass the action as a constructor
  parameter. No closures → subclass and override. Same design, two surface syntaxes. Worth remembering
  when porting an SDK across languages: the *model* transfers; the *idiom for supplying behavior* must
  be adapted.
- **"Focus on the actions rather than the parsing"** is the layering goal for any framework: the reusable
  layer should be tested once and then invisible, so users think only about their domain logic.

---

## Chapter 23: Parser Generator
*(PDF pp. 194–201)*

**Intent (verbatim):** "Build a parser driven by a grammar file as a DSL." (Fowler, DSL book, Ch. 23
"Parser Generator", intent)

Sketch: a grammar file → *generates* → a parser.

### The concept

"A grammar file is a natural way of describing the syntactic structure of a DSL. Once you have a
grammar, **it's tedious work to turn it into a handwritten parser, and tedious work should be done by a
computer.**" A Parser Generator uses the grammar file to generate a parser. Two consequences:

1. "The parser can be updated merely by updating the grammar and regenerating."
2. "The generated parser can use efficient techniques that would be hard to build and maintain by hand."

Note the reflexive structure: the Parser Generator is *itself* a DSL tool — the grammar file is a DSL,
and the generator is a code generator for it. This is Fowler's favorite worked example of a DSL that has
demonstrably paid for itself over decades.

### How it works

Fowler explicitly limits scope: "Building your own Parser Generator is no simple task, and anyone who is
capable of doing such a thing is unlikely to learn anything from this book. So, here I'll only talk
about *using* a Parser Generator. Fortunately, Parser Generators are common tools, with some useful forms
available in most programming platforms, often as open source." (Ch. 23, "How It Works")

**The workflow.** Write a grammar file in the particular form of BNF that generator uses. "Don't expect
any standardization here; if you change your Parser Generator, you will have to write a new grammar."
For output production, most generators let you use *Foreign Code* to embed code actions.

**Codegen vs. interpretation.** "Most Parser Generators use code generation, which may allow you to
generate a parser in different host languages. **There's no reason, of course, why a Parser Generator
shouldn't be able to read a grammar file at runtime and interpret it, perhaps by building a *Parser
Combinator*.** Parser Generators use code generation due to a mix of tradition and performance
considerations — particularly since they are usually aimed at general-purpose languages." (An explicit
link between Ch. 22 and Ch. 23: combinators are the runtime-interpretation answer to the same problem.)

**Treating generated code.** "Mostly, you treat the generated code as a black box and don't delve into
it. It is, however, occasionally useful to follow what the parser is doing — particularly if you are
trying to debug your grammar. In this case, there is an advantage in the Parser Generator using an
algorithm that's easier to follow, such as generating a *Recursive Descent Parser*."

**Tool recommendation.** ANTLR: "my usual recommendation for people getting into Parser Generators since
it is an easily available, mature tool with good documentation. There's also a nice IDE-style tool
(ANTLRWorks) that provides some very handy UI affordances for developing grammars."

### Embedding actions

(Ch. 23, "Embedding Actions")

"Syntactic analysis produces a parse tree; to do something with that tree, we need to embed further
code. We place the code in the grammar using *Foreign Code*. **Where we place it in the grammar
indicates when the code is executed.** Embedded code is placed in rule expressions to be executed as a
consequence of the recognition of that rule."

Key facilities and cautions:

- **Referring to tokens:** positional (`$1`, `$2` — Yacc style) vs. by name (ANTLR labels). "With ANTLR,
  the actions refer to grammar elements by name, which is usually better than by position."
- **Host language coupling:** "The actions are usually woven into the generated parser while it is being
  generated. As a result, the embedded code is usually in the same language as the generated parser."
- **Returning values from subrules to parents:** "Since the nature of a parser is to create a parse tree,
  it's often useful to move data around this tree. **A common and useful facility is thus to allow a
  subrule to return data to its parent.** … The ability to return values from rules can make it much
  easier to write parsers — in particular, **it can remove a lot of *Context Variables***." Some
  generators (ANTLR included) can also **push data down as arguments to subrules**, "which allows a lot
  of flexibility in providing context to subrules."
- **Action placement defines call timing:** an action in the middle of a rule's right-hand side is called
  after each preceding subrule is recognized. "Placing actions like this is a common feature in Parser
  Generator."
- **The dominant failure mode, and its fix:** "When using *Syntax-Directed Translation*, a common problem
  I've seen is to put too much host code in the grammar. When this happens, it's hard to see the
  structure of the grammar and the host code is difficult to edit — and requires a regeneration to test
  and debug. **The key pattern here is *Embedment Helper* — shift as much code as you can to a helper
  object. The only code in the grammar should be single method calls.**"
- **Actions depend on the output style:** Tree Construction, Embedded Interpretation, or Embedded
  Translation. "As Parser Generator isn't really too interesting without one of these, you won't find any
  examples in this pattern; instead, take a look at those other patterns for examples."
- **Semantic predicates** (repeat from Ch. 18, restated here): "like an action, a block of Foreign Code,
  but it returns a Boolean that indicates whether the parse for the rule succeeds or fails. **Actions
  don't affect the parsing, but semantic predicates do.** You usually use a semantic predicate when you're
  dealing with areas of a grammar that can't be captured properly in the grammar language itself. They
  usually appear in more complicated languages, so they tend to crop up more often in general-purpose
  languages. But if you're having difficulty getting a grammar to work with the grammar DSL itself, then
  a semantic predicate opens the door to more complicated processing."

### When to use it

(Ch. 23, "When to Use It")

**Advantages:**
- "**For me, the greatest advantage of using a Parser Generator is that it provides an explicit grammar
  to define the syntactic structure of the language you're processing. This is, of course, the key
  advantage of using a DSL.**" (i.e. the argument for a Parser Generator is a special case of the
  argument for DSLs generally — a declarative artifact stating the structure.)
- "Since Parser Generators are primarily designed to handle complicated languages, they also give you
  much more features and power than you would get by writing your own parser. While these features may
  require some effort to learn, you can usually start with a simple set and work your way up from there."
- "Parser Generators may provide good error handling and diagnostics, which, despite my not talking about
  them, can make a big difference when trying to figure out why your grammar isn't doing what you think
  it should."

**Downsides:**
- "You may be in a language environment where there isn't a Parser Generator — and it's not the kind of
  thing you should be writing yourself."
- "Even if there is one, you may balk at introducing a new tool to your mix."
- "Since Parser Generators tend to use code generation, they complicate the build process, **which can be
  a significant irritant.**"

### The Hello World example (conceptually) — Java + ANTLR

The example is a trivial `hello <Name>` greetings file. Fowler's stated reason for including something
this small is itself the lesson: "Whenever you start with a new programming language, it's traditional
to write a 'Hello World' program. It's a good habit because, when you're not familiar with a new
programming environment, there's usually a certain amount of hassle to sort out before you can run even
the simplest program. A Parser Generator like ANTLR is much the same. **It's good to get a really simple
thing going just to ensure you know what the moving parts are and how they fit together.**"

**Basic operating model of a Parser Generator:** write a grammar file → run the tool on it to produce
parser source code → compile the parser together with the other code it works with → parse some files.

Conceptual takeaways from the walkthrough (Ch. 23, sections "Writing the Basic Grammar" through "Using
Generation Gap"):

- **The grammar file needs more than rules.** ANTLR needs `@header` blocks to weave a package statement
  (and imports) into the generated parser, plus a separate `@lexer::header` for the generated lexer.
  Generated code has to fit into your project's structure, and the grammar file is where you say how.
- **One file, two artifacts.** ANTLR, like most Parser Generators, uses a separate lexer and parser, but
  you generate both from a single grammar file. Convention: **token rules start with an uppercase
  letter.**
- **Grammar hygiene rules that prevent silent failure** — two traps Fowler calls out explicitly:
  1. Define a catch-all `ILLEGAL : . ;` rule *last*, which "causes the lexer to report an error if it
     runs into a token that doesn't fit any of its rules (**otherwise such tokens are quietly
     ignored**)."
  2. Put `EOF` at the end of the top rule. "If you don't put the EOF at the end of the top rule, ANTLR
     won't report errors. **It effectively stops parsing at the first point of trouble and doesn't think
     anything went wrong.**" Fowler describes this as having "bitten me a couple of times" and being
     "particularly awkward" because the IDE will show an error in its interpreter, "so it's easy to get
     confused, frustrated, and ready to do violent acts against your monitor."
- **Whitespace and comments** are handled with lexer rules calling `skip()`. "I usually find it helpful to
  get rid of whitespace here and declare comments. When things are desperate, comments are a crude but
  reliable debugging aid."
- **Build integration:** generated sources go into a separate `gen` directory, kept apart from core
  sources and excluded from source control.
- **A hand-written loader/wrapper class** orchestrates the generated lexer and parser (create lexer over
  the input, create parser over the lexer's token stream, call the method named after the top grammar
  rule). ANTLR "has already used the word 'parser'," so Fowler names his wrapper a *loader*. Even with
  Generation Gap (below), "it's still valuable to have a wrapper class to coordinate the running of the
  parser."
- **Testing a parser — the crucial point:** a test that just runs the parser over valid input and passes
  "isn't very helpful. All it indicates is that the ANTLR parser didn't blow up when it read the file.
  That, however, may not even tell you that it read the file without problems. **So it's useful to feed
  the parser some invalid input.**" And the invalid-input test will initially *fail to fail*: "ANTLR will
  print a warning telling you it had trouble, but ANTLR is determined to keep on parsing and recover from
  errors as much as possible. In general, this is a good thing, but particularly early on it can be
  frustrating to find ANTLR so tolerant and determined." Fix: override the error-reporting method so
  errors are recorded, then throw if any were recorded.
- **Two ways to attach your code to generated code (both are *Embedment Helper*):**
  1. **Delegation** — declare a helper object field in the grammar's `@members` block and have the
     grammar's actions and overridden error methods delegate to it.
  2. **Generation Gap** — hand-write an abstract superclass of the generated parser and declare it in the
     grammar with `options { superClass = BaseGreetingsParser; }`. The generated parser then calls the
     helper's methods as bare method calls, and you no longer need to override error reporting inside the
     grammar because the handwritten superclass does it.

  Verdict: "**Both the inheritance and delegation relationships have their strengths for the Embedment
  Helper. I don't have a strong opinion on the best one to use, and use both of them in this book's
  examples.**"

### SDK relevance

- **"Tedious work should be done by a computer" — with a stated price.** The whole codegen tradeoff in
  one chapter: you gain a declarative source of truth, efficient generated implementations, and
  regeneration-on-change; you pay with a new tool, a more complicated build, and generated code you must
  treat as a black box. Fowler names build complication as "a significant irritant" — worth taking
  seriously before adopting codegen in an SDK toolchain.
- **The runtime-interpretation alternative is always available.** "There's no reason a Parser Generator
  shouldn't read a grammar at runtime and interpret it, perhaps by building a Parser Combinator." When
  you're tempted to reach for codegen, ask whether an interpreted/reflective/combinator implementation
  gets you the same declarative artifact without the build step. Codegen is often chosen for tradition
  and performance, not necessity.
- **Keep generated-code escape hatches thin (Embedment Helper).** Whatever your declarative artifact is —
  grammar, schema, config, template — the code embedded in it should be single method calls into a real,
  testable, debuggable object. Logic embedded in a spec can't be unit tested without regenerating, and it
  destroys the spec's readability. This is the single most transferable rule in the chapter.
- **Delegation vs. inheritance for framework extension points**, with Fowler declining to pick a winner.
  Generation Gap (generated class extends your hand-written class) is worth knowing as a technique for
  any codegen-based SDK: it gives generated code access to your helpers as plain method calls, and keeps
  your code in ordinary editable files.
- **Design for loud failure.** Both ANTLR traps Fowler documents (missing `ILLEGAL` rule, missing `EOF`)
  are cases where the *default behavior of a mature tool is to silently succeed on bad input*. A library
  whose default is tolerant recovery must make strict mode easy and obvious, and its docs must say
  loudly that a passing run is not evidence of a correct parse.
- **Test with invalid input, not just valid input.** "All it indicates is that the parser didn't blow up."
  Applies to every parser, deserializer, validator, and config loader an SDK ships.
- **Do a Hello World with any unfamiliar toolchain first** — establish the moving parts and their
  connections before adding domain complexity. That is also an argument for shipping a genuinely minimal
  quickstart in SDK docs: its job is to prove the plumbing, not to demonstrate features.

---

## Cross-cutting synthesis

### Choosing a parsing strategy — the decision the range is really about

Assembled from the "When to Use It" sections of Chs. 17, 18, 21, 22, 23:

| | Delimiter-Directed | Recursive Descent | Parser Combinator | Parser Generator |
|---|---|---|---|---|
| Grammar explicit? | No grammar at all | Implicit in functions | Explicit as composed objects | Explicit as a BNF DSL |
| Learning curve | Lowest — familiar techniques | Grammar concepts, simple algorithm | Grammar + combinator library | Grammar + a new tool |
| Build complexity | None | None | None (maybe a library) | Codegen step; "significant irritant" |
| Debuggability | Ordinary code | Ordinary code, easy to trace | Ordinary code + object graph | Black-box generated code |
| Handles complexity | Poorly; messy fast | Simple grammars; ≤1 symbol look-ahead; no left recursion | Same top-down limits as recursive descent | Best; ambiguity, performance, error recovery |
| Error handling | Roll your own | Roll your own | Roll your own | Mature, out of the box |
| Fowler/Parsons verdict | Only for simple autonomous statements, or a team not ready for grammars | Simplest thing that has a real parser | "A nice middle ground" | Right choice for complex/ambiguous grammars, or when you want the explicit grammar most |

Decision tripwires stated in the text:
- Ad-hoc line processing starts wanting a *framework* → you're most of the way to Syntax-Directed
  Translation anyway; go there (Ch. 17).
- Your grammar needs **more than one symbol of look-ahead** → Parser Generator (Ch. 21).
- Your grammar is genuinely **ambiguous** and you need unordered alternatives → Parser Generator
  (Chs. 21, 22).
- **Left recursion / nested operator expressions** matter → not a top-down parser (Chs. 19, 21).
- Your DSL is actually a **regular** language → a Regex Table Lexer may be the entire implementation
  (Ch. 20).
- You need a **semantic predicate** for your own DSL → redesign the DSL instead (Ch. 18).

### Recurring design principles across the range

1. **Layering with honest capability boundaries.** lexer → syntactic analysis → actions → semantic model.
   Never push a decision into a layer that lacks the context to make it correctly (`FAIL FZ17`; "keep
   lexing as simple as possible").
2. **Make the structure explicit, or accept that it's implicit but still there.** "The difference is not
   in the presence or absence of the grammar but in how the grammar is expressed" (Ch. 21). Explicitness
   buys documentation and evolvability.
3. **The declarative artifact must stay thin.** Embedment Helper; "the only code in the grammar should be
   single method calls." Otherwise the spec stops being a spec.
4. **Composition beats duplication.** Combinators implement each operator once and compose; recursive
   descent re-implements each operator inline at every rule.
5. **Transactional semantics on failure.** Consume on success; restore exactly on failure; defer actions
   until the match is confirmed. Or, better, go functional and thread the state so there's nothing to
   restore.
6. **Named references over positional ones.** ANTLR labels vs. Yacc `$1`.
7. **Explicit data flow over ambient context.** Returning values up the rule stack "removes a lot of
   Context Variables."
8. **Fail loudly by default.** `else throw RecognitionException`; the `ILLEGAL` token rule; `EOF` on the
   top rule; overriding tolerant error recovery. Test with invalid input.
9. **Naming and extraction discipline applies to specs as much as to code.** Extract subrules to show
   intent, "similarly to extracting a simple method in imperative code."
10. **Sugar with a defined desugaring is legitimate.** EBNF adds no power over basic BNF and enormous
    readability; the mechanical conversion exists for tools that need it.
