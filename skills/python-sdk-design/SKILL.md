---
name: python-sdk-design
description: >-
  Design and implement production-quality Python SDKs and client libraries,
  using the Azure SDK for Python guidelines as the canonical model of good SDK
  craftsmanship. Covers service client design (naming, constructors,
  immutability, sync/async split), method conventions (verb vocabulary, paging,
  long-running operations, error behavior), model types, exceptions, packaging
  and versioning, logging/tracing/telemetry, testing, and Pythonic code style.
  Use this skill whenever the user wants to design, build, review, refactor,
  wrap, or publish a Python SDK, client library, or API client for any REST,
  gRPC, or remote service — including phrasings like "write a Python wrapper
  for this API", "make this client library more pythonic", "review my SDK's
  public API", or "add async support to my library" — even if they never say
  the word "SDK". Always use it when authoring or reviewing an actual Azure
  SDK (azure-*) library.
---

# Python SDK Design and Implementation (Azure SDK model)

This skill teaches you to design and implement Python SDKs to the standard of
the Azure SDK for Python guidelines — one of the most battle-tested public SDK
rulebooks in existence. The rules are presented generally so they apply to
*any* Python library that wraps a remote service. Where a rule has an
Azure-specific binding (the `azure-core` package, `azure.*` namespaces, the
Architecture Board), it is marked **Azure:** — apply those verbatim when
building an actual Azure library, and treat them as a pattern to imitate
otherwise.

## The prime directive: developer productivity

An SDK exists to make developers using the service productive. Every other
quality — completeness, extensibility, performance — is secondary. Five
principles follow from this, and when rules below seem arbitrary, one of these
is the reason:

1. **Idiomatic** — the library must feel natural to a Python developer.
   Follow Python conventions and embrace the ecosystem; never import
   paradigms from other languages (no matter how common Reactive streams or
   builders are elsewhere, they are foreign in Python).
2. **Consistent** — when consistency pressures conflict, the priority order
   is: consistency **within Python** (highest), consistency **with the
   service's terminology**, consistency **across other languages' SDKs**
   (lowest). A developer uses many Python libraries and one service; they
   rarely use the same service from five languages. Every deliberate
   difference between service and library terminology needs an articulated
   reason rooted in Python idiom, not whim.
3. **Approachable** — predictable defaults that implement best practices;
   progressive disclosure of concepts; core use cases discoverable without
   reading the whole manual. Getting off the ground must be easy.
4. **Diagnosable** — it must be discoverable when a network call happens.
   Logging, tracing, and actionable error messages are features, not
   afterthoughts.
5. **Dependable** — breaking changes hurt users more than new features help
   them. Never take a dependency that can force a breaking change on you.

Two blanket requirements: support **100% of the service's features** (gaps
cause more confusion than they save effort), and support **Python 3.10+**.

## Workflow: design the surface before writing the implementation

The public API surface is the primary thing users interact with; it deserves
more thought than the implementation behind it. Work in this order:

1. **Identify the champion scenarios.** List the handful of tasks 99% of
   users will perform. The API must make these trivial; everything else may
   take more steps.
2. **Sketch the entire public surface as stub code first** — client classes,
   method signatures with full type hints and docstrings, model classes —
   before implementing anything. Read `references/api-design.md` before this
   step. Present the sketch for review when working with a user; the cost of
   changing a signature is near-zero now and near-infinite after release.
3. **Walk the sketch against `references/review-checklist.md`.** Fix
   violations before they calcify.
4. **Implement.** Read `references/implementation.md` for pipeline/middleware
   structure, logging, tracing, validation, and code-style rules.
5. **Write samples and docstrings** for every champion scenario — runnable,
   atomic (one operation per sample), and copy-pasteable in isolation.

When *reviewing* an existing SDK rather than building one, go straight to
`references/review-checklist.md` and audit the surface against it, pulling
detail from the other two references as needed.

## The rules that shape everything

The digest below contains the load-bearing rules. The reference files hold
the full detail, rationale, and examples.

### Clients

- One or more **service clients** are the entry points; name them with a
  `Client` suffix (`CosmosClient`, not `CosmosProxy`) and expose the main
  ones from the package root.
- Constructor takes **positional** parameters only for the binding
  information (endpoint/URL) and the credential; **everything else is
  keyword-only**. Never use an "options bag" object — Python has keyword
  arguments.
- Clients are **immutable**: no scenario should require mutating a client
  after construction.
- Alternative construction goes through factory classmethods:
  `from_connection_string(...)` (the constructor itself must *never* accept a
  connection string), and optionally `from_<resource>_url(...)`.
- Accept an `api_version` keyword argument defaulting to the latest stable
  service API version, even if only one version exists today — users need to
  pin what they tested against.
- Sync and async are **separate classes with the same name in sibling
  namespaces**: `mylib.ThingClient` and `mylib.aio.ThingClient`. Never mix
  sync and async methods in one class, never use an `Async` prefix/suffix on
  the class name, and never suffix method names with `_async`.

### Service methods

- Use the standard verb vocabulary — `create_`, `upsert_`, `set_`,
  `update_`, `replace_`, `get_`, `list_`, `delete_`, `<noun>_exists`, etc. —
  with their prescribed semantics (see the verb table in
  `references/api-design.md`). Deviations need an articulated reason.
- Methods that enumerate resources are prefixed `list_` and return a **paged
  iterable** (never a plain list, never `None`): iterating yields items
  across page boundaries transparently, and a `.by_page()` escape hatch
  exposes pages and continuation tokens. Return this shape even if the
  service doesn't page *yet*, so adding paging later isn't a breaking change.
- Long-running operations are prefixed `begin_` and return a **poller**
  object (`result()`, `wait()`, `done()`, `add_done_callback()`).
- **Failures raise exceptions** — never return `None` or `False` to signal
  an error. But never raise for *normal* outcomes: `thing_exists()` returns
  `False` on not-found and raises only when it couldn't determine the answer.
- Every method takes an optional keyword-only `timeout` (seconds). Optional
  arguments are always keyword-only. Per-call keyword arguments (e.g.
  `timeout`, `max_retries`) override the same-named client-constructor
  defaults.
- Validate **client-side** parameters (anything used to build a URL or
  fulfill the request locally); do **not** pre-validate parameters the
  service will validate — let the service be the authority.
- Accept a plain `dict` shaped like a model anywhere a model instance is
  accepted; `update_` methods take flattened named arguments that override
  fields of an optionally-passed model instance.

### Errors

- Reuse existing exception types — the ecosystem's (built-ins like
  `ValueError`) or your core library's shared hierarchy — before inventing
  new ones. Only create a new exception type when a caller could plausibly
  handle it *programmatically*.
- Distinguish "request never made it" from "service said no" as separate
  exception types, and carry the service's rich error details on the
  exception.
- Chain exceptions (`raise X from err` or raise inside the `except` block) so
  `__context__` is preserved.

### Models and enums

- Model types are PascalCase nouns matching service terminology
  (`ConfigurationSetting`, `VirtualMachine`). Use the same type for input and
  output so responses round-trip into update calls; server-generated
  read-only fields simply get ignored on input. Follow the naming taxonomy:
  `<Model>Item` for partial enumeration entries, `<Model>Details` for
  secondary data hung off `.details`, `<Operation>Result` for
  operation-specific outputs (and prefer a plain `dict` if that result is
  never used as an input elsewhere).
- User-instantiable models take minimal required data positionally and
  everything else keyword-only; every model implements `__repr__` (type name
  + key properties, truncated at 1024 chars).
- Enums subclass `(str, Enum)`, use UPPERCASE member names, and compare
  case-insensitively so they're interchangeable with strings — services add
  enum values without warning, and clients must not break when they do.

### Code style essentials

- Keyword-only arguments for anything optional or without an obvious
  ordering. Never consume `**kwargs` for the method's own parameters —
  spell them out; `**kwargs` is only for documented pass-through.
- Properties, not `get_x()`/`set_x()` methods; module-level functions, not
  `@staticmethod`; single leading underscore for private API and internal
  modules; public names go in `__all__`.
- Full type hints on public API using built-in generics (`list[str]`, not
  `typing.List[str]`).

## When to read each reference

- **`references/api-design.md`** — read *before* sketching or changing any
  public surface: clients, constructors, the full verb table, paging and
  poller protocols, conditional requests, hierarchical clients, models,
  enums, exceptions, auth, namespaces, async, packaging, versioning,
  dependencies, docstrings and samples.
- **`references/implementation.md`** — read *before* implementing: HTTP
  pipeline and policy architecture, parameter validation mechanics, logging
  levels, distributed tracing, telemetry/User-Agent, testing requirements,
  lint/format tooling, naming, method signatures, typing, threading.
- **`references/review-checklist.md`** — load when auditing an existing SDK
  or as the final pass over new work: the full rulebook condensed into
  checkable MUST/SHOULD items by category.

## Building an actual Azure library?

Everything above applies verbatim, plus: build on `azure-core` (its
pipeline, policies, `ItemPaged`, `LROPoller`, `MatchConditions`, credential
types, and exception hierarchy), place the library in the `azure.*` namespace
(never `microsoft.*`) as `azure-<service>` on PyPI, register the namespace
with the Architecture Board, and seek Board approval for new dependencies,
common libraries, custom policies, and binary extensions. The **Azure:**
callouts in the reference files mark every such binding in context.
