# Implementation Reference

How to build the internals behind the API surface, and the Python code-style
rules the whole library follows. Rules marked **Azure:** are the
Azure-specific binding — mandatory for `azure-*` libraries, a model to
imitate elsewhere.

## Contents

- [The HTTP pipeline](#the-http-pipeline)
- [Custom policies](#custom-policies)
- [Parameter validation mechanics](#parameter-validation-mechanics)
- [Model implementation](#model-implementation)
- [Configuration](#configuration)
- [Logging](#logging)
- [Distributed tracing](#distributed-tracing)
- [Telemetry](#telemetry)
- [Testing](#testing)
- [Tooling](#tooling)
- [Code style](#code-style)
  - [Error handling](#error-handling)
  - [Naming conventions](#naming-conventions)
  - [Method signatures](#method-signatures)
  - [Public vs private](#public-vs-private)
  - [Typing](#typing)
  - [Threading](#threading)

## The HTTP pipeline

Route every request through an **HTTP pipeline**: a transport wrapped in an
ordered list of *policies*, each a control point that can inspect or modify
the request on the way out and the response on the way in. This is what makes
service-agnostic behavior (retries, logging, tracing, auth) uniform across an
SDK family instead of re-implemented per client.

The standard policy stack, outermost first:

- Unique request ID
- Headers (static/default headers)
- User-agent / telemetry
- Proxy
- Content decoding
- **Retry** (sync and async variants)
- Credentials / authentication (e.g. bearer-token policy)
- Distributed tracing
- HTTP logging / network trace logging

**Azure:** these are `azure.core.pipeline.policies.RequestIdPolicy`,
`HeadersPolicy`, `UserAgentPolicy`, `ProxyPolicy`, `ContentDecodePolicy`,
`RetryPolicy`/`AsyncRetryPolicy`, `BearerTokenCredentialPolicy` (or
`AzureKeyCredentialPolicy`), `DistributedTracingPolicy`,
`HttpLoggingPolicy`/`NetworkTraceLoggingPolicy`, composed with
`azure.core.pipeline.Pipeline`. Typical construction inside a client:

```python
def _create_pipeline(self, credential, base_url=None, **kwargs):
    transport = kwargs.get('transport') or RequestsTransport(**kwargs)
    try:
        policies = kwargs['policies']
    except KeyError:
        scope = base_url.strip("/") + "/.default"
        if hasattr(credential, "get_token"):
            credential_policy = BearerTokenCredentialPolicy(credential, scope)
        else:
            raise ValueError(
                "Please provide an instance from azure-identity or a class "
                "that implements the 'get_token' protocol"
            )
        policies = [
            HeadersPolicy(**kwargs),
            UserAgentPolicy(**kwargs),
            ContentDecodePolicy(**kwargs),
            RetryPolicy(**kwargs),
            credential_policy,
            HttpLoggingPolicy(**kwargs),
            DistributedTracingPolicy(**kwargs),
            NetworkTraceLoggingPolicy(**kwargs),
        ]
    return Pipeline(transport, policies)
```

Note how `**kwargs` flows from the client constructor into every policy —
that is the mechanism behind "constructor keyword arguments configure the
pipeline" and "per-call keyword arguments override them".

### Protocol shapes to implement

If you are not on `azure-core`, these are the shapes your own core must
provide (Azure's implementations: `azure.core.polling.LROPoller`,
`azure.core.paging.ItemPaged`):

```python
class LROPoller(Protocol):
    def result(self, timeout=None) -> T: ...     # final result; raises on timeout
    def wait(self, timeout=None) -> None: ...
    def done(self) -> bool: ...
    def add_done_callback(self, func) -> None: ...  # func receives the eventual T

class ItemPaged(Protocol, Iterable[T]):
    continuation_token: str
    def by_page(self) -> Iterable[Iterable[T]]: ...  # pages also expose continuation_token

class ResponseHook(Protocol):
    def __call__(self, headers, deserialized_response) -> None: ...
```

## Custom policies

Some services need policies beyond the standard set (secondary-endpoint
failover during retry, request signing, exotic auth).

- Reuse or parameterize an existing core policy before writing a new one.
  **Azure:** proposed custom policies go past the Architecture Board — one
  usually already exists.
- Derive from the policy base classes: the network-capable base if the
  policy makes its own calls, the sans-IO base if it only transforms
  request/response. **Azure:** `HTTPPolicy`/`AsyncHTTPPolicy` vs
  `SansIOHTTPPolicy`.
- Policies are shared by every request on the client: they must be
  **thread-safe**. The practical rule: keep per-request state in the
  request *context*, never on the policy instance.
- Document every custom policy — how users opt in and what it does — and
  namespace policies under `<package>.pipeline.policies`.

## Parameter validation mechanics

- Never use `isinstance` checks against types you don't own — accept
  anything that has the right shape (**structural typing**: check for the
  method/attribute, or just use it). `isinstance` is acceptable only for
  built-ins (`str`, `bytes`, `int`, …).
- Remember the design-level rule (api-design.md): validate client
  parameters, never service parameters.

## Model implementation

- Every model implements **`__repr__`**, including the type name and the key
  identifying properties, **truncated at 1024 characters** — reprs feed
  logs, and logs must not explode when a model contains a 10 MB payload.

  ```python
  def __repr__(self) -> str:
      return f"ConfigurationSetting(name={self.name!r})"[:1024]
  ```

- Extensible enums, the mechanism: interchangeable with case-insensitive
  strings. **Azure:**

  ```python
  from enum import Enum
  from azure.core import CaseInsensitiveEnumMeta

  class MyCustomEnum(str, Enum, metaclass=CaseInsensitiveEnumMeta):
      FOO = 'foo'
      BAR = 'bar'
  ```

  Off Azure, replicate the behavior: subclass `(str, Enum)` and add a
  `_missing_` hook that resolves values case-insensitively.

## Configuration

Honor the platform's ambient configuration rather than inventing private
knobs: respect the environment variables users already set globally (proxy
settings such as `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY`, and your SDK
family's shared variables). **Azure:** the guidelines maintain the exact
table of environment variables every library must honor — consult it rather
than picking a subset.

## Logging

Use the **standard `logging` module** — never a bespoke logging framework —
so users control SDK logging with the tooling they already know.

- The library's logger is **named after its module** (package
  `azure-someservice` → logger `azure.someservice`). Child loggers are
  allowed but must be documented. This naming lets users dial logging for
  the whole SDK family, one library, or one sub-component with standard
  logger-hierarchy configuration.
- Level semantics:
  - `ERROR` — failures the application is unlikely to recover from (out of
    memory).
  - `WARNING` — a function failed its intended task (which normally also
    means an exception is being raised). Self-healed events — an
    automatically retried request — are *not* warnings.
  - `INFO` — normal operation: request lines, response lines, and headers of
    outgoing requests; cancellation of a service call.
  - `DEBUG` — troubleshooting detail; the only level where sensitive
    information (account keys in headers, …) may appear. Everywhere else,
    **redact**.
- Log raised exceptions at `WARNING`, appending the stack trace only when
  the effective level is `DEBUG` (`logger.isEnabledFor(logging.DEBUG)`).

## Distributed tracing

- Open a **span per public method** invocation, named
  `<package name>/<method name>`. **Azure:** the decorator in
  `azure.core.tracing` does this.
- Open a **span per outgoing network call** (the pipeline's tracing policy
  handles this when requests go through the pipeline).
- **Propagate trace context** on every outgoing request, so service-side
  telemetry correlates with the client's.

## Telemetry

Service teams identify SDK usage via the **User-Agent** header:

```
[<application_id> ]azsdk-python-<package_name>/<package_version> <platform_info>
# e.g. AzCopy/10.0.4-Preview azsdk-python-storage/4.0.0 Python/3.7.3 (Ubuntu; Linux x86_64; rv:34.0)
```

- `application_id` is the user's own app identifier, supplied via the client
  constructor; enforce **≤ 24 characters**, no spaces (slashes allowed).
  It lets *users* correlate their app's traffic across services.
- `package_name` drops the org indicator and uses dashes
  (`azure-keyvault-secrets` → `azsdk-python-keyvault-secrets`);
  `package_version` is the library's version, not the service's.
- **Azure:** `UserAgentPolicy` implements this; optional dynamic telemetry
  (class/method of the triggering call) goes in the `X-MS-AZSDK-Telemetry`
  header as `key=value;key=value` — never with personally identifiable
  information.

## Testing

- **pytest** as the framework; **pytest-asyncio** for async code.
- Scenario tests must be runnable **against the live service** — mocks
  can't catch a service that changed under you.
- Ship **recordings** so the suite also runs offline, without credentials or
  a subscription.
- Tests must tolerate **parallel runs in one subscription/account** (unique
  resource names per run) and each test must be **independent** of every
  other — order-dependence and shared fixtures across tests are how suites
  rot.

## Tooling

- **pylint** (**Azure:** with the repo-root `pylintrc`).
- **flake8-docstrings** to enforce docstring presence/format.
- **Black** for formatting — no bespoke style debates.
- **mypy** (or equivalent) on the public surface; non-shipping code (tests)
  may be skipped.

## Code style

Baseline: **PEP 8** unless a rule here overrides it. Two meta-rules:

- Don't "borrow" paradigms from other languages, however popular there
  (Reactive chains, builder hierarchies, options bags…).
- Favor consistency **with other Python libraries** over consistency with
  the same service's SDK in other languages — developers live in one
  language and many services, not the reverse.

### Error handling

Use **exception chaining** so the original cause survives — either raise
directly inside the `except` block (implicit `__context__`) or use
`raise NewError() from err`. The anti-pattern is recording a failure flag in
`except` and raising *after* the block — that silently severs the chain:

```python
# Yes — __context__ preserved
try:
    something()
except SomethingError:
    raise MyOwnError()

# No — __context__ lost
success = True
try:
    something()
except SomethingError:
    success = False
if not success:
    raise MyOwnError()
```

### Naming conventions

| Element | Convention |
|---|---|
| variables, functions, methods | `snake_case` |
| types/classes | `PascalCase` |
| constants | `ALL_CAPS` |
| modules | `snake_case` |

### Method signatures

- **No `@staticmethod`** — use module-level functions instead.
- **No `get_x()`/`set_x()` methods** — use properties. (But remember client
  *immutability*: properties on clients are read-only in spirit.)
- At most **five positional parameters**; everything optional or flag-like
  is **keyword-only** (after `*`). Parameters with no obvious ordering —
  `recurse`, `overwrite` — are keyword-only even when they have defaults:

  ```python
  def copy(source, dest, *, recurse=False, overwrite=False): ...
  ```

- **Never consume `**kwargs` for the method's own parameters** — spell them
  out as keyword-only arguments so they're discoverable, typed, and
  documented:

  ```python
  # Yes
  def create_thing(name: str, *, size: int = 0, color: str = "blue") -> None: ...

  # No
  def create_thing(name: str, **kwargs) -> None:
      size = kwargs.pop("size", 0)
  ```

  `**kwargs` is legitimate only as **documented pass-through** to another
  layer (the pipeline, an underlying API) — and then the docstring must say
  which API receives them.
- At call sites (inside the SDK and in samples): name the parameters when
  calling with more than two required positional arguments, and always name
  optional arguments (`foo(1, b=2, c=3)`, never `foo(1, 2, 3)`).

### Public vs private

- Single leading underscore marks non-public API (no stability guarantee);
  reserve double-underscore name mangling for the rare genuine inheritance
  clash.
- Everything public goes in the module's **`__all__`**.
- Internal *modules* get a leading underscore (`azure.example._internal_module`)
  — or live under an underscored parent (`azure.example._internal.utils`),
  which keeps them internal too.

### Typing

- **Type-hint the public surface** (PEP 484), checked with mypy.
- Prefer **structural subtyping / protocols** over explicit type checks;
  derive custom containers from `collections.abc`.
- Use **built-in generics** — `list[str]`, `dict[str, int]` — never
  `typing.List`/`typing.Dict` (PEP 585).
- Unions: the guidelines' examples use `typing.Union`/`typing.Optional` for
  3.9 compatibility, with an explicit note that once the minimum is
  Python 3.10+ (which it now is), the `X | Y` / `X | None` syntax
  (PEP 604) is the preferred form. Match your library's actual minimum.

### Threading

- Invoke user-supplied callbacks on the thread the user gave them to you
  from (**thread affinity**) unless explicitly documented otherwise.
- If something is thread-safe, **say so in its docs** — silence means
  unsafe.
- For parallelism, *accept an `Executor`* from the caller instead of
  spawning your own threads — unless the thread is completely invisible to
  the caller (the poller's background polling thread is the canonical
  legitimate example).
