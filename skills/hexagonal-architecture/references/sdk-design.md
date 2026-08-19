# Ports and Adapters for SDK and library design

The primary sources describe deployable applications, but the pattern maps
cleanly onto SDKs — Cockburn himself wished for exactly this use: "a
packaging concept that allows arbitrary sub-sections of code to be protected
by a test wall and configured to their environments" (*Component-plus-
Strategy*, 2022). An SDK is a component in his sense: a replaceable modular
unit with a formal contract of provided and required interfaces. Read this
file whenever the deliverable is a library, SDK, or framework; apply it *on
top of* the invariants in SKILL.md, which all still hold.

## The role mapping

| Application concept | SDK equivalent |
|---|---|
| Hexagon | The SDK core package: domain logic, zero technology imports |
| Driving ports | The SDK's public API, grouped by purpose |
| Driver adapters | The **host application's** code (plus any framework integrations you ship) |
| Driven ports | The SDK's extension points / SPI: storage, transport, credentials, clock, telemetry |
| Driven adapters | Backend integrations — yours, third-party, and the host's own |
| Configurator | The **host application**, via your client constructor / builder |

Two role shifts matter most: the driver adapter is code you don't write (the
host's), and the configurator is a party you don't control (also the host).
Both shifts turn pattern rules into API-design obligations.

## Design obligations

**The SDK owns its SPI interfaces — shape them around the core's needs.**
Declare every driven port in the core package, in the core's domain terms.
The rule from Cockburn's slides — the required interface belongs to the
caller, not the repository — is doubly binding for an SDK: an SPI shaped
around one vendor's client library is a leaked adapter that every other
implementer (including your users) will fight. If a port's methods mirror
one particular backend's API, redesign the port before shipping it; after
shipping, it's a compatibility contract.

**Make the wiring explicit at construction.** The host is the configurator,
so the client constructor or builder *is* the configurator interface:
accept port implementations as parameters. A default backend is not a
special case — it is the SDK choosing one of its bundled adapters when the
caller passes none. Reach for dependency lookup (a broker the host
registers factories with) only when the adapter genuinely varies per call,
e.g. per-tenant storage.

```python
# The constructor is the configurator seam. Defaults are just bundled adapters.
client = SdkClient(
    storage=PostgresStorage(dsn),      # or omit → bundled InMemoryStorage
    transport=HttpxTransport(),
    clock=None,                        # None → bundled SystemClock
)
```

**Ship the test doubles as product, not test junk.** In the pattern a mock
is a first-class adapter and a supported configuration. For an SDK, the
in-memory backend and the recording spy belong in the *published* package:
they are what let consumers run the tests-and-mocks-first build sequence
against their own applications without standing up your dependencies. An
SDK whose users must hand-write fakes for its SPI has shipped half the
pattern. (Garrido de Paz's BlueZone models this: stub, spy, and fake
adapters are named, versioned modules beside the production ones.)

**Package along the adapter seams.** Core package = hexagon + all port
declarations + bundled in-memory adapters. Each technology adapter is a
separately installable module (`sdk-adapter-postgres`, `sdk-adapter-kafka`)
carrying its own third-party dependencies. This is the pattern's folder
rule turned into dependency hygiene: installing the core must not drag in
every backend driver ever supported; installing an adapter opts into
exactly one. Optional-extras syntax (`pip install sdk[postgres]`) is an
acceptable front door to the same structure.

**Ports are the semver surface.** Technology immunity — upgrades happen in
adapters while the core is untouched — becomes versioning policy: port
interfaces (API and SPI) are the stable contract that semantic versioning
protects; adapters may churn with their technologies on their own cadence.
This also factors the test matrix: verify core logic once against doubles;
verify each adapter separately against its real technology. Remember that
*adding* a required method to a shipped SPI port is a breaking change for
every implementer — design SPI ports narrow and grow them additively
(new port, or defaulted methods where the language allows).

**Resist port inflation hardest here.** Every published port is a promise:
an owned interface, at least two plausible implementations, a shipped test
double, and boundary tests maintained forever. Internal seams that don't
meet that bar stay internal — Cockburn's warnings against one-port-per-use-
case and untested decorative boundaries apply with interest once outsiders
depend on the surface. His "small number, two, three or four" purposeful
conversations is as good a default for an SDK's SPI as for an application.

## A worked shape

A telemetry SDK, by way of example:

- **Driving ports (API):** `ForRecordingEvents` (record, flush),
  `ForConfiguringSampling`.
- **Driven ports (SPI):** `ForExportingBatches` (recipient),
  `ForPersistingQueue` (repository), `ForTellingTime`.
- **Bundled adapters:** in-memory queue, recording exporter spy, system
  clock — shipped, documented, versioned.
- **Separate adapter packages:** `-adapter-otlp`, `-adapter-sqlite`.
- **Host wiring:** constructor injection; exporter choice per environment
  is the host's configurator decision, not an env-var the core reads.
- **Tests:** core suite runs entirely on bundled doubles; each adapter
  package carries its own integration suite; consumers test *their* apps
  against the bundled doubles.

The test of success mirrors the application case: the consumer can run
their full application suite — SDK included — with no network, no broker,
and no database, purely by choosing adapters at construction time.
