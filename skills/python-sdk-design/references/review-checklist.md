# SDK Review Checklist

The full rulebook condensed into checkable items. Use this to audit an
existing Python SDK or as the final pass over a new surface. **MUST** items
are violations when absent; **SHOULD** items need a reason when absent.
Items marked *(Azure)* apply only to actual `azure-*` libraries; for other
SDKs read them as "the equivalent in your SDK's shared core".

For rationale or detail on any item, follow the section names into
`api-design.md` and `implementation.md`.

## Clients

- [ ] MUST: client types end in `Client`
- [ ] MUST: primary clients exported from the package root
- [ ] MUST: separate sync and async client classes, same class name, async
      under the `.aio` namespace — no `Async*` names, no `*_async` methods,
      no mixed sync/async classes
- [ ] MUST: client design is immutable (no scenario requires mutating one)
- [ ] MUST: constructor = positional endpoint/binding params + positional
      `credential`; all other params keyword-only
- [ ] MUST NOT: options-bag parameter objects
- [ ] MUST: `transport` keyword argument accepted
- [ ] MUST: pipeline/policy defaults configurable via constructor kwargs
- [ ] MUST: connection strings only via `from_connection_string` classmethod;
      constructor never accepts one
- [ ] MUST: `api_version` keyword argument, defaulting to latest stable;
      default documented; version-gated features documented
- [ ] MUST: `application_id` accepted for telemetry, ≤ 24 chars enforced

## Methods

- [ ] SHOULD: names use the standard verb table (`create_`/`upsert_`/`set_`/
      `update_`/`replace_`/`get_`/`list_`/`delete_`/`<noun>_exists`/…) with
      the prescribed semantics (`create_` fails on exists; `delete_`
      succeeds on missing; `get_` raises on missing)
- [ ] MUST: verbs consistent across the SDK family (no `download` here,
      `fetch` there)
- [ ] MUST: `list_` prefix for enumerations; returns a paged iterable with
      `.by_page()` — even for services that don't page yet; empty iterable,
      not `None`, when there are no items
- [ ] MUST NOT: `continuation_token` parameter on the `list_` method itself
      (it belongs to `.by_page()`)
- [ ] MUST: `begin_` prefix for long-running operations; returns a poller
      (`result`/`wait`/`done`/`add_done_callback`)
- [ ] MUST: failures raise; no `None`/`False` error returns
- [ ] MUST NOT: exceptions for normal outcomes (`exists` returns `False`,
      doesn't raise, on not-found)
- [ ] MUST: optional arguments keyword-only
- [ ] MUST: `timeout` keyword argument on every service method (seconds);
      async cancellation via standard `asyncio`
- [ ] MUST: common kwargs supported: `headers`, `client_request_id` (where
      applicable), `response_hook`
- [ ] MUST: per-call kwargs override same-named constructor defaults
- [ ] MUST: client parameters validated (especially anything embedded in a
      URL); service parameters NOT validated client-side
- [ ] MUST: `dict` accepted wherever a model is accepted
- [ ] MUST: `update_` methods use flattened named args; explicit args
      override a passed model's fields
- [ ] MUST: conditional-request methods take `match_condition` and `etag`
      kwargs; explicit `etag` overrides the model's

## Hierarchy

- [ ] MUST: a client per hierarchy level (leaves optional); each directly
      constructible
- [ ] MUST: `get_<child>_client()` on parents makes no network call
- [ ] MUST: `create_<child>()` exists (SHOULD return the child's client);
      SHOULD: `delete_<child>()`

## Models and enums

- [ ] MUST: PascalCase, service-aligned names; get/set round-trip through
      the same type (read-only fields ignored on input)
- [ ] SHOULD: naming taxonomy respected — `<Model>Item` / `<Model>Details` /
      `<Operation>Result`; plain `dict` when a Result type is never an input
- [ ] MUST: user-instantiable models: required data positional, rest
      keyword-only
- [ ] MUST: `__repr__` on every model — type + key properties, ≤ 1024 chars
- [ ] MUST NOT: models duplicated into the async namespace
- [ ] MUST: enums subclass `(str, Enum)`, case-insensitive, UPPERCASE
      members *(Azure: `CaseInsensitiveEnumMeta`)*

## Errors

- [ ] MUST NOT: new exception types where a built-in or shared-core type
      suffices; new types only when programmatically handleable
- [ ] MUST: transport failures vs service failures distinguishable by type
- [ ] MUST: service error details exposed as attributes on the exception
- [ ] MUST: exception chaining preserved (`raise ... from`, or raise inside
      `except`)
- [ ] MUST: raised exceptions documented (except ubiquitous built-ins)

## Auth

- [ ] MUST: every service-supported auth method supported
- [ ] MUST: credentials as protocol objects, not loose strings *(Azure:
      `azure-core` credential classes and policies)*

## Packaging, namespaces, versioning, dependencies

- [ ] MUST: namespace maps to the service; stable across rebrands *(Azure:
      under `azure.*`, `azure.mgmt.*` for management planes, registered
      with the Board; never `microsoft.*` root)*
- [ ] MUST: package name = namespace, lowercase, dash-separated; no
      underscores or periods
- [ ] MUST: async package/namespace = sync + `-aio`/`.aio`
- [ ] MUST: sdist + wheel published; `__init__.py` present in sdists
- [ ] MUST: semver; patch=fixes, minor=features or default-API-version
      change, major=breaking only; PEP 440 pre-release segments only
      (`bN` for betas)
- [ ] MUST: dependencies from the approved allowlist only; no vendoring;
      no exact pins — compatible-release (`~=`) ranges
- [ ] SHOULD NOT: shared "common" library unless its objects are consumed
      directly from multiple libraries

## Implementation

- [ ] MUST: all requests via the HTTP pipeline; standard policy stack
      (request-id, headers, user-agent, proxy, decode, retry, credential,
      tracing, logging)
- [ ] MUST: custom policies derive from the policy base classes, keep
      per-request state in the context (thread-safe), documented, under
      `<package>.pipeline.policies`
- [ ] MUST NOT: `isinstance` validation against non-built-in types — use
      structural typing
- [ ] MUST: std `logging`; logger named after the module; levels per
      semantics (WARNING on failed function + raise; INFO for request/
      response lines; sensitive data only at DEBUG, redacted elsewhere)
- [ ] MUST: span per public method (`<package>/<method>`), span per network
      call, trace context propagated
- [ ] MUST: User-Agent telemetry in the standard format
- [ ] MUST: pytest (+ pytest-asyncio); tests runnable live AND from
      recordings; parallel-safe; independent
- [ ] MUST: pylint, flake8-docstrings, Black; SHOULD: mypy on the public
      surface

## Code style

- [ ] MUST: PEP 8; snake_case functions/variables/modules, PascalCase
      types, ALL_CAPS constants
- [ ] MUST NOT: paradigms imported from other languages
- [ ] MUST NOT: `@staticmethod` (module functions instead); no getter/setter
      methods (properties instead)
- [ ] SHOULD NOT: more than five positional parameters
- [ ] MUST NOT: `**kwargs` consumed for the method's own params; pass-through
      `**kwargs` documented with the receiving API
- [ ] MUST: single-underscore private API; underscored internal modules;
      public names in `__all__`
- [ ] MUST: type hints on public API; built-in generics (`list[str]`);
      protocols/`collections.abc` over type checks
- [ ] MUST: thread affinity for user callbacks; thread-safety documented;
      caller-supplied `Executor` over own thread management (hidden threads
      excepted)

## Docs and samples

- [ ] MUST: docstrings on all public modules/types/constants/functions;
      consumed and forwarded `**kwargs` documented
- [ ] MUST: snippets atomic (one operation each), CI-tested, ingested into
      docstrings
- [ ] MUST: samples in `/samples`, runnable, one scenario each, graftable,
      cross-platform, baseline-Python only
- [ ] MUST: README with install + champion scenarios
