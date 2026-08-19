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
