# API Design Reference

The public surface of an SDK. Read this before sketching or changing any
public API. Rules marked **Azure:** are the Azure-specific binding of the
preceding general rule — mandatory for `azure-*` libraries, a model to
imitate elsewhere.

## Contents

- [Service clients](#service-clients)
  - [Naming and placement](#naming-and-placement)
  - [Constructors and factory methods](#constructors-and-factory-methods)
  - [Service API versioning](#service-api-versioning)
  - [Immutability](#immutability)
- [Service methods](#service-methods)
  - [The verb vocabulary](#the-verb-vocabulary)
  - [Return values: the logical entity](#return-values-the-logical-entity)
  - [Errors are exceptions; normal outcomes are not](#errors-are-exceptions-normal-outcomes-are-not)
  - [Parameters](#parameters)
  - [Cancellation and timeouts](#cancellation-and-timeouts)
- [Paging](#paging)
- [Long-running operations](#long-running-operations)
- [Conditional requests](#conditional-requests)
- [Hierarchical clients](#hierarchical-clients)
- [Model types](#model-types)
- [Enumerations](#enumerations)
- [Exceptions](#exceptions)
- [Authentication](#authentication)
- [Namespaces and packages](#namespaces-and-packages)
- [Async support](#async-support)
- [Versioning](#versioning)
- [Dependencies](#dependencies)
- [Docstrings, snippets, and samples](#docstrings-snippets-and-samples)

## Service clients

The service client is the user's entry point: a class exposing methods that
interact with the service.

### Naming and placement

- Name client types with a **`Client` suffix**: `CosmosClient`, yes;
  `CosmosProxy` or `CosmosUrl`, no. The suffix tells users "this is the thing
  you instantiate to talk to the service."
- Expose the clients users are most likely to need from the **root
  namespace** of the package. Specialized clients may live in sub-namespaces.
- Provide **separate sync and async clients** (see [Async support](#async-support)).

### Constructors and factory methods

Only the minimal information needed to connect should be *required*;
everything else is optional and **keyword-only**.

- The constructor signature is: positional binding parameter(s) (the service
  endpoint URL or instance name), a positional `credential`, then
  keyword-only settings.

  ```python
  client = ExampleClient('https://contoso.com/xmpl',
                         DefaultAzureCredential(),
                         max_retries=18,
                         timeout=2)
  ```

- **Never use an "options bag"** object to group optional settings. Python
  has keyword arguments; a `ClientOptions` class is a C#/Java idiom that adds
  a layer of indirection for nothing.
- Accept a keyword-only **`transport`** argument so callers can substitute
  the HTTP transport (for testing, proxying, or alternative stacks).
  **Azure:** default is `RequestsTransport` (sync) / `AioHttpTransport`
  (async) from `azure.core.pipeline.transport`.
- Accept default request options (retries, timeout, headers…) as keyword
  arguments and pass them through to the pipeline policies, so client-wide
  defaults are set at construction and overridable per call.
- Well-known constructor parameters, consistent across all clients:

  | Name | Purpose |
  |---|---|
  | `credential` | Credential object used to authenticate requests |
  | `application_id` | Caller's application name, prepended to telemetry (≤ 24 chars) |
  | `api_version` | Service API version to use (see below) |
  | `transport` | Override the default HTTP transport |

- If (and only if) the service hands out **connection strings**, provide a
  `from_connection_string(connection_string, **kwargs)` **classmethod**. The
  constructor itself must *never* accept a connection string — even if that
  makes the factory the only way to build the client. The factory parses the
  string and delegates to the constructor:

  ```python
  @classmethod
  def from_connection_string(cls, connection_string, **kwargs):
      endpoint, credential = cls._parse_connection_string(connection_string)
      return cls(endpoint, credential, **kwargs)
  ```

- If the service passes around **URLs to resources** (as Azure Blob Storage
  does), you may add a `from_<resource_type>_url(url, ...)` classmethod
  taking the same keyword arguments as the constructor.

### Service API versioning

For services that version their API independently of the library:

- Accept an optional keyword-only **`api_version: str`**. Default to the
  latest stable (non-preview) version the library understands — or the
  latest preview version if no stable version exists. Provide the parameter
  even when only one version exists, so users can lock the version they
  tested against before the library updates underneath them.
- Document the default version, and document which API version introduced
  each method or parameter that isn't universally supported.
- You *may* validate `api_version` against the known list, and *may* expose
  the known versions as an enum (e.g. `ServiceVersion`).

### Immutability

Design clients so no scenario requires changing their attributes after
construction. This isn't about slapping read-only properties everywhere —
plain attributes are fine — it's about the *design*: reconfiguration means
constructing a new client. Immutable clients are trivially safe to share
across threads and to reason about.

## Service methods

### The verb vocabulary

Use these verbs with exactly these semantics. A different verb for one of
these operations needs an articulated reason — and whatever verb a given
operation uses, keep it consistent across your SDK family (if it's
`download` in one library, don't call it `fetch` in another).

| Verb | Parameters | Returns | Semantics |
|---|---|---|---|
| `create_<noun>` | key, item, `[allow_overwrite=False]` | created item | Create new; **fails if it already exists** |
| `upsert_<noun>` | key, item | item | Create or update (database-flavored services) |
| `set_<noun>` | key, item | item | Create or update (dictionary-flavored properties) |
| `update_<noun>` | key, partial item | item | Update; **fails if it doesn't exist** |
| `replace_<noun>` | key, item | item | Replace entirely; fails if it doesn't exist |
| `append_<noun>` | item | item | Add to end of a collection |
| `add_<noun>` | index, item | item | Add to a collection at a position |
| `get_<noun>` | key | item | **Raises** if it doesn't exist |
| `list_<noun>` | — | paged iterable of items | Empty iterable when none exist (never `None`, never raises for "no items") |
| `<noun>_exists` | key | `bool` | `True`/`False`; raises only if existence couldn't be determined |
| `delete_<noun>` | key | `None` | **Succeeds even if the item didn't exist** (idempotent) |
| `remove_<noun>` | key | removed item or `None` | Remove a *reference* from a collection without deleting the item |

Two mandatory prefixes on top of the verbs:

- **`begin_`** for [long-running operations](#long-running-operations).
- **`list_`** for enumerations.

### Return values: the logical entity

Model each call's return as the **logical entity** — a protocol-neutral
representation of the response optimized for the 99% case. For HTTP that may
mean merging data from the body, headers, and status line (e.g. expose the
`ETag` header as an `etag` attribute on the returned model). Users should not
need the raw response for normal work; a `response_hook` callback (see
[Parameters](#parameters)) covers the 1% who do.

### Errors are exceptions; normal outcomes are not

- If the method failed to accomplish the user's task — whether the service
  answered with an error or no answer came at all — **raise**. Never signal
  failure by returning `None` or `False`:

  ```python
  # Yes
  try:
      resource = client.create_resource(name)
  except ResourceExistsError:
      ...

  # No
  resource = client.create_resource(name)
  if not resource: ...
  ```

- Conversely, **never raise for a normal response**. The canonical case is
  `exists`: not-found is a *normal answer* to an existence question, not an
  exceptional condition:

  ```python
  # Yes
  exists = client.resource_exists(name)   # False on 404
  # ...raises only if it couldn't determine the answer (e.g. a 503)
  ```

  A method's contract determines what is "normal": `get_thing` raising on
  not-found is correct because the caller asked for the thing and didn't get
  it; `thing_exists` raising on not-found is wrong because the caller asked a
  yes/no question and got an answer.

### Parameters

- **Optional operation-specific arguments are keyword-only.** Positional
  parameters are reserved for required, obviously-ordered data.
- Support the **common per-operation keyword arguments** on every method:

  | Name | Purpose |
  |---|---|
  | `timeout` | Seconds the caller is willing to wait |
  | `headers` | Extra headers merged into every request the call makes |
  | `client_request_id` | Caller-supplied correlation ID (where the service supports one); generate a unique value per request when absent |
  | `response_hook` | Callable invoked with the raw response for each operation |

- Per-call keyword arguments **override same-named client-constructor
  defaults** for that call only:

  ```python
  client = ExampleClient(url, cred, max_retries=18, timeout=2)
  client.do_stuff(timeout=32)   # this call: timeout 32, retries still 18
  ```

  If a *service* parameter's name collides with one of these pipeline
  options, qualify the service parameter's name — the pipeline names win.
- **Validate client parameters; don't validate service parameters.** Client
  parameters are consumed locally — above all, anything interpolated into a
  URL, where an empty string silently produces a *different, valid* URL:

  ```python
  def get_thing(name: str) -> Thing:
      if not name:
          raise ValueError('name must be a non-empty string')
      # '' would have turned /things/{name} into /things/ — the *list* endpoint
  ```

  Service parameters go over the wire untouched: no null checks, no empty
  checks — the service owns those rules, and duplicating them client-side
  means the SDK breaks when the service relaxes them. Do, however, *try out*
  the failure modes: if the service's error message for bad input is
  unusable, raise that with the service team rather than papering over it.
- **Accept a `dict` wherever a model is accepted**, shaped like the
  serialized model — this keeps quick scripts friction-free:

  ```python
  do_something(Thing(name='a', size=17))
  do_something({'name': 'a', 'size': 17})   # equivalent
  ```

- **`update_` methods take flattened named arguments.** They may *also*
  accept the whole model via a keyword parameter; explicit named arguments
  override the model's fields:

  ```python
  client.update_thing(thing=thing, size=4712)  # size 4712 wins over thing.size
  ```

### Cancellation and timeouts

- Sync methods: the optional keyword-only `timeout` (seconds), honored as
  best as possible.
- Async methods: rely on standard `asyncio` cancellation
  (`asyncio.Task.cancel()` / `asyncio.timeout`), not a bespoke mechanism.

## Paging

Collections may take multiple requests to enumerate; the service returns
partial results plus a continuation token. Hide this behind a **paged
iterable** so the full-enumeration case is effortless and page-level access
remains available:

```python
# Transparent iteration across page boundaries:
for thing in client.list_things():
    print(thing)

# Page-level access when needed:
for page in client.list_things().by_page():
    ...

# Resuming from a saved continuation token happens at the page level:
for page in client.list_things().by_page(continuation_token='...'):
    ...
```

Rules:

- `list_` methods return an object implementing this protocol — iterable of
  items, `.by_page()` returning an iterable of pages, `continuation_token`
  exposed on the pager. **Azure:** `azure.core.paging.ItemPaged`.
- Do **not** accept `continuation_token` on the `list_` method itself —
  continuation is a paging concern and lives on `by_page()`.
- You *may* accept a `results_per_page` keyword argument where the service
  supports a page-size hint (e.g. OData `$top`).
- Return the paged shape **even if the service doesn't page today**. If you
  return a plain `list` now, the day the service adds paging you must either
  break your users or silently buffer unbounded results.

## Long-running operations

Operations the service models as asynchronous jobs (rule of thumb: can't
finish in 0.5 s at P99) get a **poller**, not a blocking call — and so should
operations where the documented usage pattern is "call, then poll a status
yourself", even if the service doesn't formally flag them as long-running.

- Method name is prefixed **`begin_`** and returns immediately with a poller:

  ```python
  poller = client.begin_copy_model(source)
  model = poller.result(timeout=300)   # block until done (or timeout)
  ```

- The poller protocol: `result(timeout=None) -> T` (final result, raises on
  timeout), `wait(timeout=None)`, `done() -> bool`,
  `add_done_callback(func)`. **Azure:** `azure.core.polling.LROPoller`
  implements it.

## Conditional requests

For methods supporting optimistic-concurrency / conditional semantics:

- Accept a keyword-only **`match_condition`** parameter expressing the
  condition (if-modified, if-not-modified, …). **Azure:** type it as
  `azure.core.MatchConditions`.
- Accept a keyword-only **`etag`** parameter. When the method also takes a
  model that carries an `etag` attribute, an explicitly passed `etag`
  overrides the model's:

  ```python
  thing = client.get_thing('name')
  # condition evaluated against thing.etag:
  client.update_thing(thing, match_condition=MatchConditions.IfNotModified)
  # condition evaluated against the explicit etag:
  client.update_thing(thing, match_condition=MatchConditions.IfNotModified,
                      etag='"other"')
  ```

## Hierarchical clients

Services with nested resources (account → container → blob) get a client per
level of the hierarchy, except leaves (leaf clients are optional):

- Every level's client must be **directly constructible** (from a URL and
  credential) — users holding a deep resource's URL must not be forced to
  construct the whole ancestry.
- Parents vend children via **`get_<child>_client(name, **kwargs)`** —
  which must **not** make a network call. Getting a handle is free;
  existence is checked when you *use* it.
- Parents create children via **`create_<child>(...)`**, which should return
  the new child's client; and *should* offer **`delete_<child>(...)`**.

## Model types

Models are the entities exchanged with the service.

- Name them PascalCase after the service's terminology
  (`ConfigurationSetting`, `VirtualMachine`) — shared vocabulary between
  library and service docs aids diagnosability.
- **Round-trip with one type**: the type returned by `get_` is the type
  accepted by `set_`/`update_`. Include server-generated read-only fields on
  it; they're simply ignored on input. This makes
  get → modify → set workflows natural.
- The naming taxonomy for everything that isn't the full resource:

  | Type | Example | Use |
  |---|---|---|
  | `<Model>` | `Secret` | The full resource |
  | `<Model>Details` | `SecretDetails` | Secondary data, hung off `<model>.details` |
  | `<Model>Item` | `SecretItem` | Partial schema returned by enumerations |
  | `<Operation>Result` | `AddSecretResult` | Output specific to one operation |
  | `<Model><Verb>Result` | `SecretChangeResult` | Shared output of several operations on a model |

  If an `<Operation>Result` is never *input* to another API, don't define a
  class — return a plain `dict`/Mapping. Classes earn their keep by being
  passed back in.
- Constructors for user-instantiable models: minimal required data
  positionally, everything else keyword-only. Result-only types users never
  construct don't need friendly constructors.
- Accept `dict`s as alternative input anywhere models are accepted (see
  [Parameters](#parameters)).
- Implement `__repr__` on every model: type name + the key identifying
  properties, truncated at 1024 characters (see implementation reference).
- Sync and async namespaces **share model types** — never duplicate models
  into the async (`aio`) namespace. **Azure:** generated-layer models may be
  re-exported from the root `__init__.py`/`__all__` if they meet these
  guidelines.

## Enumerations

- Enums are **extensible**: subclass `(str, Enum)` and compare
  case-insensitively, so enum members and plain strings are interchangeable
  and unknown values coming back from a newer service version don't crash
  the client. **Azure:** use `CaseInsensitiveEnumMeta` from `azure.core`
  (see implementation reference for the snippet).
- Member names are **UPPERCASE** (`ONE = 'one'`; not `One`, not `one`).

## Exceptions

- **Prefer existing exception types.** Order of preference: a Python
  built-in if it fits (`ValueError`, `TypeError`); your SDK family's shared
  exception hierarchy for service failures. **Azure:** the `azure-core`
  exceptions (`ServiceRequestError`, `ServiceResponseError`,
  `ResourceNotFoundError`, `ResourceExistsError`, `HttpResponseError`, …).
- Only introduce a new exception type when a caller could **handle it
  programmatically** — a new type whose only purpose is a different message
  is noise. Derive service-failure exceptions from the shared hierarchy so
  broad `except` clauses keep working.
- Keep the transport/service distinction: "the request never made it"
  (retriable connectivity failure) and "the service rejected it" are
  different exception types, because callers treat them differently.
- Put **service-specific error information** (error codes, reasons,
  correlation IDs) in dedicated attributes on the exception — actionable
  errors are a design principle, not a nicety.
- For composite operations spanning multiple requests, raise either the last
  failure or an aggregate of all failures.
- Document the exceptions each method raises — except the ubiquitous ones
  Python never documents (`ValueError`, `TypeError`, `RuntimeError`).

## Authentication

- Support **every** authentication method the service supports.
- Take credentials as objects with a defined protocol (e.g. a `get_token`
  method), not as raw strings scattered across parameters — this decouples
  the client from credential acquisition and rotation. **Azure:** use the
  credential classes and authentication policies from `azure-core` /
  `azure-identity`; new credential types need Architecture Board guidance.

## Namespaces and packages

Terminology: "namespace" = what users `import`; "distribution package" =
what they `pip install`.

- Pick a namespace users can tie to the service: a compressed service name
  ("Media Analytics" → `mediaanalytics`), stable across marketing renames.
  A group segment may organize families (`azure.storage.blob`,
  `azure.mgmt.servicebus`) — but never introduce a new distribution package
  *only* to rename it into a group.
- **Azure:** the root namespace is `azure.*` (registered with the
  Architecture Board); management-plane libraries live under `azure.mgmt.*`;
  `microsoft` is never the root (when policy requires it, concatenate:
  `microsoft_myservice`).
- The distribution package is named after the namespace, lowercase with
  dashes: namespace `azure.data.tables` → package `azure-data-tables`.
  No underscores or periods in package names (namespace underscores become
  dashes).
- Async namespace: sync namespace + **`.aio`** (see below).
- Ship both **sdist and wheel**; include `__init__.py` for the namespace
  packages in sdists; follow the language's namespace-package rules
  (PEP 420); test wheels on CPython and PyPy.
- **Shared "common" libraries** (code shared by sibling client libraries)
  are justified only when users consume its objects *directly* from more
  than one library — shared *shape* alone (look-alike models with no logic)
  is not a reason; duplicate those instead. Keep common libraries minimal.
  **Azure:** requires Architecture Board approval.

## Async support

Most Python developers still reach for sync code first; an SDK serves both
audiences.

- Provide **both sync and async** versions of the API, using
  `async`/`await` (never the legacy generator-based coroutine styles).
- Sync and async are **separate classes with the same name**, distinguished
  only by namespace:

  ```python
  from azure.sampleservice import SampleServiceClient       # sync
  from azure.sampleservice.aio import SampleServiceClient   # async
  ```

  Never mix sync and async methods on one class; never name a class
  `AsyncExampleClient`; never name methods `do_thing_async`.
- If async support needs extra dependencies, ship it as a separate package
  named `<package>-aio`.
- **Azure:** the default async transport is `aiohttp`
  (`AioHttpTransport`); async clients live in the `.aio` sub-namespace.

## Versioning

- **Semantic versioning**, strictly. Any change at all → new version number.
  Bug fixes → patch. New functionality → minor. Breaking changes → major
  (and treat the bar for breaking a stable library as extremely high —
  sometimes a renamed package is kinder than a diamond-dependency mess).
- Changing the **default service API version is at least a minor bump**,
  even with zero Python-surface changes — behavior changes. A new service
  API version alone is *not* a major bump unless it forces breaking Python
  changes.
- Pre-releases use PEP 440 segments only (`aN`, `bN`, `rcN`; beta releases
  use `bN`) — tools mis-sort anything else.
- **Azure:** breaking changes need Architecture Board approval, and a new
  package's version must exceed any previously released version of the same
  service's older-generation packages.

## Dependencies

Every dependency is a tax on users (version conflicts, install size,
security surface) and a compatibility hostage (see "Dependable").

- Depend only on a deliberately short, well-known allowlist of packages.
  **Azure:** the approved-dependencies list; additions need Architecture
  Board sign-off.
- Do **not vendor** dependencies (copying their source into your package)
  without explicit approval.
- Do **not pin exact versions** — libraries declare [compatible
  ranges](https://peps.python.org/pep-0440/#compatible-release) (`~=`);
  only *applications* pin. A library that pins makes itself uninstallable
  next to any neighbor that needs a different patch release.
- Binary extensions (native code) need explicit justification and must
  support Windows, Linux (manylinux), and macOS across x86 and x64.
  **Azure:** Architecture Board approval required.

## Docstrings, snippets, and samples

- Docstring **every public module, type, constant, and function**.
- If a method consumes `**kwargs`, document each consumed key. If it
  forwards `**kwargs`, document *which API receives them*.
- Document raised exceptions — except ubiquitous built-ins.
- **Snippets**: short, atomic examples — one operation per snippet (account
  creation and container creation are two snippets, not one). Keep them in
  the repo, exercised by CI, and ingested into docstrings/API reference
  (Sphinx `literalinclude`) so they can't rot.
- **Samples**: runnable end-to-end files under `/samples`, shipped in the
  package. One scenario per sample, graftable (no dependence on variables
  defined in *other* samples), readable over clever, baseline-Python only
  (no features newer than the minimum supported version), runnable on
  Windows/macOS/Linux.
- README with install + champion-scenario usage; aim to "document into
  silence" — preempt the questions (service limits, common errors and
  recovery) so they never become issues.
