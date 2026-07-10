# Epic 3: Knowledge Integration

T-021 — architecture only. Defines Epic 3 as the umbrella initiative that connects the six independent Discovery Layer modules (Epic 2, T-015–T-020) into one coherent traveller-facing intelligence, and positions it against the longer-range knowledge work already sketched in `docs/ROADMAP.md` Phase 5.

## Epic Framing

| Epic | Scope | Status |
|---|---|---|
| Epic 1 | Foundation — traveller profile, conversation engine, goals, trip planning (T-001–T-014) | Complete |
| Epic 2 | Discovery Layer — six independent, explainable intelligence modules (T-015–T-020) | Complete |
| **Epic 3** | **Knowledge Integration — unify Epic 2's modules behind one orchestrator; formalize the shared knowledge substrate they all read from** | **This document; architecture defined in T-021, not yet built** |
| Epic 4+ | Commerce, multi-tenant TravelOS (`docs/ROADMAP.md` Phases 6-7) | Future |

Epic 2 deliberately built six **independent** modules — the Discovery Layer pattern's whole point was that "a new engineer who has read one Discovery module already understands the shape of every other one" (`docs/DISCOVERY_LAYER_PATTERN.md`). That independence was correct for Epic 2: it let six modules ship in sequence without any of them blocking on the others. Epic 3 is the deliberate next step — now that all six exist, connect them, without undoing the independence that made them buildable in the first place. Trip Brain (`docs/TRIP_BRAIN_ARCHITECTURE.md`) is an orchestration layer *above* the six modules, not a rewrite of any of them.

## Knowledge Integration — What It Actually Means Here

"Knowledge Integration" is doing two distinct jobs in Epic 3, and conflating them is the main risk this document exists to head off:

1. **Orchestration integration** — six modules, invoked separately today, need to be callable together for one broad request and merged into one answer. This is Trip Brain's job, and it requires no new knowledge sources — it's pure coordination over data every module already produces.
2. **Shared knowledge substrate** — several modules already independently read from the same underlying sources (`ai/intelligence/` for the knowledge graph and traveller DNA; `ai/memory/` for the traveller profile). Epic 3 formalizes this as a named layer — "Knowledge Sources," defined precisely in `docs/KNOWLEDGE_SOURCE_STRATEGY.md` — so that as Phase 5's larger knowledge-layer work (vector store, RAG, embeddings) eventually arrives, it has one place to plug in rather than six.

Epic 3 delivers (1) as architecture now and stops. It defines the shape (2) needs to fit into later, but does not build (2) — no vector store, no embeddings, no RAG in this epic. That is explicitly Phase 5 work per `docs/ROADMAP.md`, and pulling it forward here would be exactly the "unnecessary abstraction" this task was told to avoid.

## Trip Brain

Full detail in `docs/TRIP_BRAIN_ARCHITECTURE.md`. In Epic 3's terms: Trip Brain is the **orchestration integration** half — a Coordinator that sits between `ConversationEngine` and the six Discovery module services, selecting, running, merging, and explaining across them for broad requests, while narrow single-domain requests continue to bypass it entirely (no regression to Epic 2's existing behaviour).

## Knowledge Sources

Full taxonomy in `docs/KNOWLEDGE_SOURCE_STRATEGY.md`. Summary for Epic 3 purposes — these are the sources that already exist and that Trip Brain (and every Discovery module) reads from, none of them new:

| Source | Location | What it holds |
|---|---|---|
| Knowledge Graph | `ai/intelligence/knowledge/` | Destinations, countries, relationships (199 nodes, 205 edges per `docs/TRAVEL_INTELLIGENCE_LAYER.md`) |
| Ontology | `ai/intelligence/ontology/` | The travel domain's controlled vocabulary — goal types, interests, destination types |
| Traveller DNA | `ai/intelligence/traveller_dna/` | Inferred persona traits (`adventure_seeking`, `budget_consciousness`, ...) every Discovery module's Scorer already reads for its DNA/goal adjustment layer |
| Reasoning engines | `ai/intelligence/reasoning/` | `BudgetReasoner`, `DestinationReasoner`, `SafetyReasoner`, `SeasonReasoner`, `TimelineReasoner`, `ExperienceReasoner` — pre-Discovery-Layer reasoning components, some (`BudgetReasoner`) explicitly reused by Discovery modules for data consistency (`docs/BUDGET_INTELLIGENCE_ENGINE.md`) |
| Traveller Memory | `ai/memory/` | The traveller's profile, preferences, loyalty data |

## Provider Layer

Every Discovery module's Provider (`mock_flight_provider.py`, `mock_visa_provider.py`, etc.) is a **deterministic mock data source scoped to exactly one Discovery module.** This is distinct from Knowledge Sources above: a Provider answers "what raw candidates exist for this domain" (flight inventory, visa rules, climate profiles); a Knowledge Source answers "what do we know about the traveller, the world, or the travel domain generally" that's shared *across* domains. `docs/KNOWLEDGE_SOURCE_STRATEGY.md` defines this boundary precisely — Epic 3 does not blur it. Trip Brain never calls a Provider directly; it only ever calls a Discovery module's public `service.recommend()`/`check()`/`analyse()` entrypoint, exactly as `ConversationEngine` does today.

## Future Live Integrations

Every Discovery module's documentation already states its Sprint 4+ migration path (see each module's own doc, e.g. `docs/VISA_INTELLIGENCE_ENGINE.md`'s "Sprint 4+ Migration Path" table). Epic 3 does not change any of these plans — it changes nothing about *how* a Provider is swapped for a live feed, only ensures that when that happens, Trip Brain's orchestration and the Knowledge Source layer above it don't need to change at all, because they never depended on any Provider's internal shape to begin with. The migration boundary for every module remains exactly what the Discovery Layer pattern already established: swap the Provider, keep everything downstream (Normalizer through Orchestrator) untouched.

| Module | Current | Future (unchanged plan, restated for completeness) |
|---|---|---|
| Flight | `MockFlightProvider` | Amadeus, Skyscanner, or similar |
| Accommodation | `MockAccommodationProvider` | A hotel inventory API |
| Destination | `MockDestinationProvider` | Google Places or similar |
| Budget | `MockBudgetProvider` | A live pricing feed |
| Visa | `MockVisaProvider` | A Timatic-style immigration data feed |
| Weather | `MockWeatherProvider` | A live climate/forecast feed |

Trip Brain's confidence aggregation (`docs/TRIP_BRAIN_ARCHITECTURE.md`) is specifically designed so that a live-data module reporting *higher* confidence than a mock one requires no orchestration change — confidence is read from each module's existing output field, not computed with knowledge of whether that module is mock or live.

## What Epic 3 Deliberately Does Not Include

- No new REST endpoints (`POST /conversation/message` remains the sole entry point).
- No new Discovery module (six is complete, per `docs/TASK_TRACKER.md`).
- No vector store, embeddings, or RAG (Phase 5).
- No changes to any existing Discovery module's Provider, Normalizer, Scorer, Reasoner, or Risk Assessor.
- No commerce/booking (Phase 6).
