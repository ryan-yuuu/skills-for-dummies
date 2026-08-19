---
name: hexagonal-architecture
description: >-
  Design and implement software using Hexagonal Architecture, aka the Ports and
  Adapters pattern (Alistair Cockburn): isolate business logic in a
  technology-free core that talks to the world only through purpose-named ports
  with swappable adapters, so the same application runs unchanged under tests,
  UIs, and production infrastructure. Use this skill whenever the user mentions
  hexagonal architecture, ports and adapters, decoupling business logic from a
  database/framework/broker, swappable or pluggable backends, in-memory fakes,
  testing the core without infrastructure, SPI or extension-point design, or
  asks to design, implement, review, or refactor an application or SDK toward
  any of these — even if they never name the pattern.
---

# Hexagonal Architecture (Ports and Adapters)

This skill teaches you to produce designs and implementations that follow
Alistair Cockburn's Ports and Adapters pattern *as its author defines it* —
not the layered folklore that circulates under its name. The pattern's intent,
in Cockburn's words: "Allow an application to equally be driven by users,
programs, automated test or batch scripts, and to be developed and tested in
isolation from its eventual run-time devices and databases."

The core move: treat the application as one self-contained component with no
knowledge of any technology. Everything external — humans, tests, other
programs, databases, brokers, mail servers — connects only through **ports**
(purpose-defined interfaces the application owns) via **adapters** (one per
technology, swappable). A test double is just another adapter, which is why a
correctly built hexagon runs its full regression suite with no UI and no
database.

**When to apply it:** applications and SDKs with real external dependencies
and a lifespan — anything that must be testable without its infrastructure or
survive a technology swap. **When not to:** small scripts and throwaway tools;
the constructor parameters, interface declarations, and configurator are
overhead that short-lived code never repays. Say so instead of applying the
pattern ritually.

## First, decide the mode

- **Design mode** — the user wants an architecture proposal. Follow
  [Design workflow](#design-workflow); deliver the design document, no code
  beyond port signatures.
- **Implementation mode** — the user wants working code. Do the design
  workflow first (compressed if the design is obvious), then follow
  [Implementation workflow](#implementation-workflow).
- **Review mode** — the user has existing code to audit or refactor. Follow
  [Review checklist](#review-checklist), report violations with locations,
  and propose the smallest refactor sequence that restores each invariant.

If the subject is a **library or SDK** rather than a deployable application,
also read [references/sdk-design.md](references/sdk-design.md) — the pattern
maps cleanly but the roles shift (the host application becomes the
configurator, and test doubles become shipped product).

## Vocabulary — use it precisely

Correct terminology is half the pattern; most published mistakes begin as
vocabulary drift. These are Cockburn's terms:

| Term | Meaning |
|---|---|
| **Hexagon / application** | The business logic, free of all technology references. The shape is arbitrary — six sides mean nothing; the hexagon just gives room to draw many ports and breaks the top/bottom layered picture. |
| **Driving (primary) actor** | External party that initiates: a human at a UI, a test suite, a cron job, another program. |
| **Driven (secondary) actor** | External party the application calls: a database (*repository* — two-way) or a mail server (*recipient* — one-way). |
| **Driving port** | An interface the application *implements and offers* — its API, one purposeful conversation of use cases. |
| **Driven port** | An interface the application *declares and calls* — what it requires from the world (its SPI). |
| **Driver adapter** | Translates a driving technology into port calls: REST controller, CLI, GUI, test fixture, queue consumer. |
| **Driven adapter** | Implements a driven port with a technology: SQL repository, SMTP notifier, in-memory fake, recording spy. |
| **Configurator** | The one place that knows concrete adapters and wires everything at startup (aka composition root). |

## The invariants

These nine rules are what make an implementation *be* the pattern. Each
exists for a reason; when you must trade one off, say so explicitly rather
than silently drifting.

1. **No technology inside the hexagon.** No SQL, no HTTP types, no framework
   imports, no vendor SDKs. One leaked import couples the core to a
   technology and quietly kills the ability to test and swap — the two
   benefits the whole pattern exists to buy.

2. **The application owns every port definition — on both sides.** Driven
   ports especially: the interface belongs to the caller, not the
   implementation. The persistence port looks the way the *application's
   logic* needs it to look, never the way some database driver happens to
   look. An interface shaped around one technology is a leaked adapter, and
   every other implementation will fight it.

3. **Name ports for their purpose: "for doing something".**
   `ForParkingCars`, `ForObtainingRates`, `ForNotifyingSubscribers`. Purpose
   naming keeps ports organized around conversations rather than nouns, and
   makes it obvious when a proposed port is really a technology in disguise
   (`ForAccessingPostgres` fails the test on sight).

4. **Every port must plausibly support at least two adapters** — and one of
   them is usually the test double. This is Cockburn's own acid test for
   whether something deserves to be a port. A "port" with exactly one
   conceivable implementation is just indirection. The inverse error is
   worse: one-technology-per-port inverts the pattern's entire point, which
   is that technologies substitute *behind* a stable port.

5. **All source dependencies point at the hexagon.** Driver adapters depend
   on driving ports; driven adapters depend on (implement) driven ports; the
   hexagon depends on nothing outside itself. If the build system can
   enforce this (import rules, module boundaries), have it do so — leaks
   recur when nothing structural prevents them.

6. **Only the configurator knows concrete adapters.** The hexagon receives
   driven adapters as constructor parameters (dependency injection) or asks
   a broker for them (dependency lookup — use when the choice varies per
   call, e.g. per-tenant storage). Test cases are their own configurators;
   production gets one startup module. Concrete adapter names appearing
   anywhere else are wiring leaks.

7. **Tests attach at the ports, on both sides.** A test driver pushes the
   driving ports while test doubles answer the driven ports — full system
   behavior with zero infrastructure. Cockburn: a claimed Ports and Adapters
   implementation with no tests at the boundary hasn't implemented the
   pattern, it has drawn the diagram. Treat test doubles as first-class
   adapters that ship and version like the production ones.

8. **One hexagon per application — do not nest.** The boundary sits exactly
   at the technology edge. Nested hexagons multiply boundary tests until the
   team stops maintaining them, at which point the inner boundaries stop
   being real. Internal structure can still use components with
   provided/required interfaces; just don't call them hexagons or give them
   the full ceremony.

9. **The pattern prescribes nothing inside the hexagon.** No layers, no
   domain/application-service split, no CQRS, no DDD — those are separate,
   optional decisions. Don't present them as part of this pattern, and
   don't reject them either; the hexagon's interior is the user's to
   organize.

## Design workflow

Work through these steps in order; each feeds the next.

1. **Identify the purposeful conversations.** List everything the system
   talks to, then group by *purpose*, not technology. "Weather data arrives
   by RSS, HTTP, and telemetry" is one conversation (collecting weather
   data) with three adapters — not three ports. Expect a small number:
   two to four ports is Cockburn's stated norm; one port per use case and
   a single left/right pair are both named anti-patterns.

2. **Classify each conversation** as driving (who initiates: them) or driven
   (who initiates: the application), and driven ones as repository or
   recipient. When one external system appears on both sides, that's two
   ports — the split follows the conversation, not the box.

3. **Name every port** in "for doing something" form and give each 2–6
   function signatures in domain terms only (domain types in, domain types
   out — no rows, requests, or wire formats).

4. **Enumerate adapters per port**, minimum two, always including the test
   instrument: test drivers on driving ports, doubles (fake / stub / spy) on
   driven ports. If a port cannot name a second adapter, merge it back —
   see invariant 4.

5. **Plan the configurator:** which wiring configurations exist (tests+fakes,
   demo, staging, production), injection vs lookup per port, where the
   startup module lives.

6. **Deliver the design** in this shape:

   ```markdown
   ## <System> — Ports and Adapters design
   ### Actors
   <driving / driven, one line each>
   ### Ports
   | Port | Side | Operations | Adapters (planned) |
   ### The hexagon
   <what lives inside; explicitly technology-free>
   ### Configurator
   <configurations and wiring mechanism>
   ### Test strategy
   <what runs with zero infrastructure; what each real adapter's own tests cover>
   ```

## Implementation workflow

### The code shape

Five kinds of artifact, whatever the language (sketch in Python; in dynamic
languages the port interfaces may stay implicit — the discipline is
identical):

```python
# hexagon/ports/driving/for_calculating_taxes.py   — the app's API
class ForCalculatingTaxes(Protocol):
    def tax_on(self, amount: Decimal) -> Decimal: ...

# hexagon/ports/driven/for_getting_tax_rates.py    — what the app requires
class ForGettingTaxRates(Protocol):
    def tax_rate(self, amount: Decimal) -> Decimal: ...

# hexagon/tax_calculator.py                        — the hexagon
class TaxCalculator:                     # implements ForCalculatingTaxes
    def __init__(self, rates: ForGettingTaxRates) -> None:
        self._rates = rates              # injected; concrete type unknown here
    def tax_on(self, amount: Decimal) -> Decimal:
        return amount * self._rates.tax_rate(amount)

# adapters/driven/fake_rates.py                    — first-class deliverable
class FixedRates:                        # implements ForGettingTaxRates
    def tax_rate(self, amount): return Decimal("0.15")

# adapters/driven/sql_rates.py — SQL exists here and only here
# adapters/driver/cli.py       — argv in, app.tax_on() out
# main.py                      — the configurator:
#   app = TaxCalculator(SqlRates(connect(dsn))); cli.run(app)
```

### Build order — tests and mocks first

This sequence is the pattern's native workflow; it front-loads the payoff
(finished, regression-tested logic before any infrastructure exists):

1. **Test drivers + fake driven adapters.** Implement the whole hexagon
   driven by tests, every driven port answered by a double.
2. **Real drivers + fakes.** Add the UI/REST/CLI adapters against the still-
   fake back end (also the demo configuration).
3. **Test drivers + real driven adapters.** Implement and verify the SQL,
   SMTP, etc. adapters by driving the app from tests.
4. **Real + real.** End-to-end; every other combination is now a deployment
   choice, not a code change.

### Folder layout

Port declarations live *inside* the application package; each adapter is its
own module *outside* it, named for the port it serves plus its technology
(`adapter-forgettingrates-sql`, `adapter-forparkingcars-webui`,
`adapter-forpaying-spy`). This makes the dependency rule (invariant 5)
enforceable mechanically and keeps each technology's dependencies isolated to
its adapter.

## Review checklist

Audit in this order — the cheapest checks catch the most common rot:

1. **Grep the hexagon for technology:** SQL strings, HTTP/framework imports,
   vendor SDK names, serialization annotations inside core logic → invariant 1
   violations, each with file:line.
2. **Locate every port definition.** Any interface defined in an adapter's
   package, or shaped like a specific driver's API → invariant 2.
3. **Check constructor signatures** in the core: concrete adapter types
   instead of port types → invariants 5/6.
4. **Find the configurator.** Wiring scattered across modules, or adapters
   instantiating each other → invariant 6.
5. **Run the no-infrastructure test:** can the suite exercise the driving
   ports with doubles on the driven ports, with nothing external running?
   If not → invariant 7, and this is the finding to fix first.
6. **Count adapters per port.** Ports with one conceivable implementation
   (merge them) and technologies bypassing ports entirely (wrap them).

For refactors, sequence fixes to restore invariant 7 earliest — once the
no-infrastructure test configuration exists, every later step is protected
by it.

## Going deeper

- [references/pattern-deep-dive.md](references/pattern-deep-dive.md) — read
  when correctness of interpretation matters: the pattern's history and
  names, the driving/driven asymmetry, the configurator variants, common
  published misconceptions and their rebuttals, costs and benefits, relation
  to Clean/Onion/DDD, and the Component + Strategy generalization. All
  claims cited to primary sources (Cockburn; Garrido de Paz).
- [references/sdk-design.md](references/sdk-design.md) — read whenever the
  deliverable is a library, SDK, or framework rather than an application.
