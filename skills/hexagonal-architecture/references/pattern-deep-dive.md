# Ports and Adapters — deep dive from primary sources

This file grounds the skill's rules in the pattern's primary literature:
Alistair Cockburn's own publications and those of his co-author Juan Manuel
Garrido de Paz. Consult it when a design discussion turns on *what the pattern
actually says* — misconceptions about this pattern are widespread enough that
Cockburn spent much of 2017–2024 correcting them. Numbered citations refer to
the [sources](#sources) at the end.

## Contents

1. [Intent and the problem](#1-intent-and-the-problem)
2. [History and the names](#2-history-and-the-names)
3. [The anatomy, precisely](#3-the-anatomy-precisely)
4. [The asymmetry](#4-the-asymmetry)
5. [The configurator](#5-the-configurator)
6. [Misconceptions and rebuttals](#6-misconceptions-and-rebuttals)
7. [Costs and benefits](#7-costs-and-benefits)
8. [Relation to other architectures](#8-relation-to-other-architectures)
9. [The generalization: Component + Strategy](#9-the-generalization-component--strategy)
10. [Sources](#sources)

## 1. Intent and the problem

The 2005 article states the intent: "Allow an application to equally be driven
by users, programs, automated test or batch scripts, and to be developed and
tested in isolation from its eventual run-time devices and databases" [1].
The 2023 restatement is more operational: "Create your application to work
without either a UI or a database so you can run automated regression-tests
against the application, work when the database becomes unavailable, upgrade
to new technology, and link applications together" [3].

Two motivating failures [1]: business logic leaking into UI code (killing
automated testing, batch use, and program-to-program integration — and
layering rules don't stop it because nothing structural detects violations),
and application logic entangled with databases/services (development stalls
when the dependency changes or disappears). Cockburn's insight is that these
are one problem: the real boundary is inside/outside, not top/bottom, and
"code pertaining to the inside part should not leak into the outside part"
[1]. The user and the database are the same kind of thing — external actors —
and deserve identical treatment.

## 2. History and the names

- **Mid-1990s** — Cockburn draws "a symmetric architecture in which the
  database is considered not at the bottom of the stack, but fully outside
  the application, just as we recommend doing with the user," names it
  Hexagonal Architecture — "the rather stupid name … because I could not
  think of what the 'hexagon' meant" [2]. He dates the first drawing to 1994
  OO-design course notes [7].
- **June 2005** — the "aha!": the facets of the hexagon are *ports*, the
  objects between the hexagons are *adapters* — credited to Rebecca
  Wirfs-Brock's *Object Design* and a Kevin Rutherford blog post [2].
- **September 4, 2005** — the definitive article, HaT TR 2005.02 [1].
- **~2012** — the DDD community adopts it to protect domain models from
  technology — "an act of self-defense" — and popularity surges, along with
  a wave of wrong tutorials [7].
- **2022–2023** — *Component-plus-Strategy generalizes Ports-and-Adapters*
  [4] and the refreshed 2023 explanation [3].
- **2024** — the book *Hexagonal Architecture Explained* (Cockburn &
  Garrido de Paz) [9].

Cockburn prefers "Ports and Adapters" as the accurate name but concedes
"hexagonal architecture is catchier, the hexagon shape is memorable" [7] —
that is the name that prevailed. They are the same pattern. The hexagon
itself is meaningless geometry: "not a hexagon because the number six is
important, but rather to allow the people doing the drawing to have room to
insert ports and adapters as they need" [1]; he picked it because "pentagons
and heptagons are impossible to draw" [7].

## 3. The anatomy, precisely

**The application** is a component — Cockburn draws it as a chip with pins
[3]. Its boundary is the use-case boundary: use cases written here (functions
and events, no screens or tables) come out shorter and more stable [1].

**Actors** divide by who initiates. Driving (primary) actors start the
conversation; driven (secondary) actors are called by the application, and
subdivide into *repositories* (two-way, e.g. databases) and *recipients*
(one-way, e.g. an SMTP server) [1][5]. The same external system can be a
driving actor at one port and a driven actor at another.

**Ports** are the application's "purposeful conversations" with the world —
the OS/electronics metaphor: anything honoring the protocol can plug in [1].
A port is an interface; Cockburn names them "for doing something" and notes
each carries multiple function calls [3]. Driving ports are the API (UML
*provided interface*: the app implements, drivers call). Driven ports are
the SPI (UML *required interface*: the app declares and calls, outsiders
implement) [3][4][5]. Ownership is the load-bearing rule, bolded on
Cockburn's slide: "Make sure the required interface's definition belongs to
the calculator, not to the repository!" [3].

Port count is intuitive and small: the known uses run two to four (weather
alerting: collecting weather data, administration, notifying subscribers,
subscriber data; coffee machine: four; hospital medication: three), and both
extremes — a port per use case, or a single left/right pair — are called out
as suboptimal [1].

**Adapters** convert between one technology and one port, in both
directions [1]. Plurality is the point: on the C2 wiki Cockburn stress-tests
each candidate port by finding its second adapter (test harness for the
admin, loopback for the database, web/email beside the answering machine)
[2], and in the interview he is blunt that "the whole point of a port is to
allow technology substitutions" [7]. Deployment configurations are adapter
selections: tests+fakes in development, GUI+fakes for demos, scripts+test
database for integration, GUI+production database live [1].

## 4. The asymmetry

The pattern began as a quest for symmetry (stop treating the database as
special), and the finished pattern keeps the symmetric *dependency* picture:
both adapter kinds depend on the hexagon; the hexagon depends on nothing.
But implementation is asymmetric — Garrido de Paz's "symmetrical asymmetry"
[5]. The application never knows which driver is calling it; it must *hold*
some driven adapter to call, without knowing which one it received. So
configurable dependency applies on the driven side only, and the natural
test instruments differ: script-reading drivers on the driving side, mocks
and spies on the driven side [1]. Cockburn credits Gerard Meszaros's
observation — the shared property worth naming is that *the dependency is
configurable* — with both clarifying the model and "ruin[ing] my quest for
total symmetry" [6][7].

## 5. The configurator

"Sooner or later there has to be some module or code that knows all the
players and introduces them to each other. That's where source-code
dependencies lie. This is the Configurator object" [4] — the "hidden fourth
object" omitted from most diagrams, aka the composition root [5]. Two
designs [3]:

- **Setter/constructor injection** (Dependency Injection) — configurator
  creates adapters and hands them in. Default choice.
- **Repository broker** (Dependency Lookup) — the app asks a broker at call
  time. Use when the adapter varies per request (Cockburn's example:
  tax-rate repositories per country).

In early development each test case is its own configurator; in production a
startup module (possibly a DI framework) plays the role [4].

## 6. Misconceptions and rebuttals

- **"Hexagonal architecture has layers: domain, ports, adapters."** No — the
  pattern prescribes nothing inside the hexagon; no layers anywhere [5].
  Inside, use DDD, transaction scripts, whatever: the pattern governs the
  external boundary; internal organization is a separate decision [7].
- **"One port per technology."** Backwards; substitutability of technologies
  behind a port is the pattern's purpose [7].
- **"Actor → Port → Adapter → Hexagon."** The port sits *on* the hexagon:
  Actor → Adapter → (Port) Hexagon [5].
- **"Hexagons all the way down."** The boundary belongs at the technology
  edge only; nested hexagons multiply boundary tests until teams abandon
  them and the boundaries stop being real [4]. Use nested *components* for
  internal structure (§9).
- **"We implemented Ports and Adapters" (with no boundary tests).** "One of
  the things that makes my blood freeze … is the absence of tests on both
  sides" [4]. The tests-at-ports configuration is the implementation's
  proof.
- **Test doubles as throwaway scaffolding.** They are first-class adapters
  and supported deployment configurations [1]; the BlueZone reference app
  versions its stub/spy/fake adapters as named modules beside production
  ones [8].

## 7. Costs and benefits

Benefits [3]: choose driven actors at initialization, over years, or in real
time; swap production connections for test harnesses and back without source
changes; no rebuild per configuration; structural prevention of logic leaks
in both directions.

Costs [3]: an instance variable per driven actor; a constructor
parameter/setter/configurator call per driven actor; you must design and
build a configurator; (type-checked languages) declared required interfaces
and the folder structure to hold port declarations.

Garrido de Paz adds [5]: more modules, mappings, and indirection; slower
builds at scale; tiny projects may not repay the overhead; long-lived
systems with anticipated technology change are the sweet spot — and even
fixed-technology projects profit from the fakes and per-environment
configurations.

## 8. Relation to other architectures

From the 2005 related-patterns section [1]: GoF *Adapter* supplies the
adapter concept (applied systematically at an application boundary); *MVC*
is ports-and-adapters on the driving side only; *Mock Objects* supply the
driven-side test instruments; the *Dependency Inversion Principle* and DI
frameworks supply the wiring mechanics.

Clean Architecture and Onion Architecture are later, separate proposals that
*also* prescribe internal structure (layers, dependency rules inside the
core). Ports and Adapters is compatible with them but does not include
them — presenting their layer diagrams as "hexagonal architecture" is the
single most common conflation (§6, first bullet).

## 9. The generalization: Component + Strategy

Cockburn's 2022 report reframes the pattern from above [4]. A UML Component
is "a modular unit with well-defined interfaces that is replaceable within
its environment," carrying a formal contract of provided and required
interfaces. Strategy is the mechanism of handing a component a collaborator
satisfying its required interface; Adapter "is a special case of the
Strategy pattern in which the concrete strategy will make some adjustments
for interface compatibility and then call another service." Then:

> "Ports & Adapters, also known as Hexagonal architecture, is a specific use
> of Component + Strategy where the component boundary is placed just in
> front of external technologies." [4]

Consequences: Component + Strategy nests (components inside components, each
a real, tested boundary) while Ports and Adapters deliberately does not; and
where two components' interfaces already match, no adapter object is needed
— the adapter is a translation device, not a ritual [4]. When a user wants
hexagon-like seams *inside* an application, or wants "arbitrary sub-sections
of code to be protected by a test wall and configured to their environments"
[4], Component + Strategy is the honest name for what they're building.

## Sources

1. Alistair Cockburn, *Hexagonal Architecture (Ports & Adapters)*, Humans
   and Technology TR 2005.02, September 4, 2005.
   <https://alistair.cockburn.us/hexagonal-architecture/>
2. Alistair Cockburn et al., *Ports And Adapters Architecture*, C2 wiki.
   <http://wiki.c2.com/?PortsAndAdaptersArchitecture>
3. Alistair Cockburn, *Hexagonal Architecture (Ports & Adapters) — The 2023
   version*, slide deck, May 18, 2023.
   <https://alistaircockburn.com/Hexagonal%20Budapest%2023-05-18.pdf>
4. Alistair Cockburn, *Component-plus-Strategy generalizes
   Ports-and-Adapters*, HaT TR 2022.01 (v3a, 2023).
   <https://alistaircockburn.com/Component%20plus%20strategy.pdf>
5. Juan Manuel Garrido de Paz, *Ports and Adapters Pattern (Hexagonal
   Architecture)*.
   <https://jmgarridopaz.github.io/content/hexagonalarchitecture.html>
6. Juan Manuel Garrido de Paz, *Configurable Dependency*.
   <https://jmgarridopaz.github.io/content/confdep.html>
7. Juan Manuel Garrido de Paz, *Interview with Alistair Cockburn*.
   <https://jmgarridopaz.github.io/content/interviewalistair.html>
8. Juan Manuel Garrido de Paz, *BlueZone* sample application.
   <https://github.com/jmgarridopaz/bluezone>
9. Alistair Cockburn & Juan Manuel Garrido de Paz, *Hexagonal Architecture
   Explained*, 2024. ISBN 978-1-7375197-8-2.
