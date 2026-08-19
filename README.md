# skills for dummies
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)](LICENSE)

A collection of skills I use everyday for systems design, planning, code review, open-source best practices, etc.

<br>

## Skills

### [diataxis-docs-writer](skills/diataxis-docs-writer)

Write and structure docs following the Diátaxis framework, governing documentation _content_ (what to write), _style_ (how to write it) and _architecture_ (how to organise it).

#### Install

```bash
npx skills add https://github.com/ryan-yuuu/skills-for-dummies --skill diataxis-docs-writer
```

### [codex](skills/codex)

Delegate work to the OpenAI Codex CLI headlessly — second opinions, code review,
scoped implementation, design critique and brainstorming — with a safe invocation
contract, deliberate sandboxing, dynamic selection of the strongest model, and an
acceptance bar set before the call and verified after it.

#### Install

```bash
npx skills add https://github.com/ryan-yuuu/skills-for-dummies --skill codex
```

### [open-source-vendoring-best-practices](skills/open-source-vendoring-best-practices)

Vendor external open-source code safely — license check first, attribution and
provenance recorded, risky licenses flagging, and other oss best practices.

#### Install

```bash
npx skills add https://github.com/ryan-yuuu/skills-for-dummies --skill open-source-vendoring-best-practices
```

### [google-adk-architecture](skills/google-adk-architecture)

Understand Google ADK's internals — graph orchestration, execution flow, resumption and checkpointing, node contracts, and observability.
_Vendored from [google/adk-python](https://github.com/google/adk-python) (Apache-2.0)._

#### Install

```bash
npx skills add https://github.com/ryan-yuuu/skills-for-dummies --skill google-adk-architecture
```

### [google-adk-agent-builder](skills/google-adk-agent-builder)

Build, test, and iterate on Google ADK agents — agent modes, tool binding, graph-based workflows, and multi-agent patterns.
_Vendored from [google/adk-python](https://github.com/google/adk-python) (Apache-2.0)._

#### Install

```bash
npx skills add https://github.com/ryan-yuuu/skills-for-dummies --skill google-adk-agent-builder
```

### [hexagonal-architecture](skills/hexagonal-architecture)

Design, implement, and review code following Hexagonal Architecture (Ports and
Adapters) as Cockburn defines it — technology-free core, purpose-named ports
owned by the application, swappable adapters with first-class test doubles, and
a tests-and-mocks-first build order. Includes a reference for applying the
pattern to SDK/library design, grounded in primary sources.

#### Install

```bash
npx skills add https://github.com/ryan-yuuu/skills-for-dummies --skill hexagonal-architecture
```

### [python-sdk-design](skills/python-sdk-design)

Design and implement production-quality Python SDKs and client libraries, using
the Azure SDK for Python guidelines as the canonical model of good SDK
craftsmanship — service client design, method conventions (paging, long-running
operations, error behavior), model types, packaging and versioning,
logging/tracing/telemetry, and Pythonic style.

#### Install

```bash
npx skills add https://github.com/ryan-yuuu/skills-for-dummies --skill python-sdk-design
```

### [sdk-api-design](skills/sdk-api-design)

Design, implement, and review language-agnostic SDK and client-library public
APIs using the durable principles from Joshua Bloch's talk "How to Design a
Good API and Why It Matters" — use-case-first design, small hard-to-misuse
surfaces, and evidence-backed reviews, with every rule cited back to the source.

#### Install

```bash
npx skills add https://github.com/ryan-yuuu/skills-for-dummies --skill sdk-api-design
```

### [dsl-design](skills/dsl-design)

Design, implement, and review fluent APIs, SDKs, config formats, and
domain-specific languages using the principles from Fowler's
_Domain-Specific Languages_ — a semantic model separated from every surface,
call shapes chosen from the grammar of what callers supply, collected
structured errors, and the generated-SDK architecture (thin generated layer
over a handwritten runtime, Generation Gap). Backed by a complete cited
distillation of the book in [docs/dsl-design-principles.md](docs/dsl-design-principles.md).

#### Install

```bash
npx skills add https://github.com/ryan-yuuu/skills-for-dummies --skill dsl-design
```

<br>

## License

Licensed under the [MIT License](LICENSE).
