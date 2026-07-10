# Knowledge Source Strategy

T-021 — architecture only. This repository already has six different-looking things that all "hold data": Providers, repositories, a knowledge graph, traveller memory, and (via FastAPI) APIs. Before Trip Brain reads from several of them at once, this document draws the boundary between them precisely, so the Coordinator never reaches for the wrong one.

## The Six Terms

### Knowledge Source

**Definition**: Any component that answers a factual or inferred question about the *world*, the *travel domain*, or the *traveller* — as opposed to answering "what candidate options exist for this specific request," which is a Provider's job (below).

**Test**: If the answer would be the same regardless of which Discovery module is asking, it's a Knowledge Source. Traveller DNA traits, the knowledge graph's country/continent data, the travel ontology's controlled vocabulary — none of these are specific to flights, or hotels, or visas. Every Discovery module's Scorer reaches into Knowledge Sources for its DNA/goal adjustment layer; none of them owns the data it reads.

**Existing instances**: `ai/intelligence/` (knowledge graph, ontology, reasoning engines, DNA) and `ai/memory/` (traveller profile). "Knowledge Source" is the umbrella term this document uses for both — see `docs/EPIC3_ARCHITECTURE.md`'s table for the full breakdown.

### Provider

**Definition**: The one component *inside* a single Discovery module that returns raw, domain-specific candidate data — deterministic mock data today, a live third-party API tomorrow. Defined precisely and exhaustively in `docs/DISCOVERY_LAYER_PATTERN.md`: "returns raw candidate data in whatever shape a real external provider would use."

**Test**: A Provider only ever answers "what raw candidates exist for *this* domain, given *these* domain-specific parameters" — `MockFlightProvider.search(origin, destination, departure_date, ...)`, `MockVisaProvider.lookup(passport_country, destination_country, ...)`, `MockWeatherProvider.month(destination, month_of_travel)`. It never answers a question another module would also need answered — that's what makes it a Provider and not a Knowledge Source.

**Ownership boundary — the single most important rule in this document**: **a Provider is owned by exactly one Discovery module and is never called by anything else.** Not by another Discovery module, not by the Coordinator, not by Trip Brain. `docs/EPIC3_ARCHITECTURE.md` states this explicitly: "Trip Brain never calls a Provider directly." The only way anything outside a Discovery module gets data that originated in a Provider is through that module's Normalizer → Scorer → Reasoner → Orchestrator pipeline and out through its public `service.recommend()`/`check()`/`analyse()` method.

**Existing instances**: `mock_flight_provider.py`, `mock_accommodation_provider.py`, `mock_destination_provider.py`, `mock_budget_provider.py`, `mock_visa_provider.py`, `mock_weather_provider.py` — one per Discovery module, six total.

### API

**Definition**: The REST boundary — `services/api/app/domains/<domain>/router.py` — through which an HTTP client (the frontend, or in principle any external caller) reaches a Discovery module or the conversation endpoint. Not a data source at all; a transport and validation layer (Pydantic request/response schemas) in front of a `service.py`.

**Test**: If removing it wouldn't change what data is available, only how it's reached over HTTP, it's an API, not a Knowledge Source or a Provider. `POST /weather/analyse` is an API; `MockWeatherProvider` is a Provider; they are different layers of the same module, not the same thing described twice.

**Existing instances**: every `router.py` under `services/api/app/domains/`, plus `services/api/app/routers/conversation.py`. Trip Brain introduces **zero** new APIs, per the task's explicit constraint — it is invoked from inside `ConversationEngine`, behind the existing `POST /conversation/message` endpoint, never as a new HTTP surface.

### Repository

**Definition**: The persistence boundary for one domain's *results* — `services/api/app/domains/<domain>/repository.py`. Stores what a Discovery module already decided (a `FlightOption`, a `VisaAssessment`, ...) so it can be retrieved later by ID or by `trip_id`. In-memory today (`dict[str, T]`), a PostgreSQL adapter in Sprint 3 per every Discovery module's own migration table.

**Test**: A Repository never *decides* anything — it only stores and retrieves what the Orchestrator already produced. This is the opposite direction of data flow from a Provider (Provider → in; Repository → out, after the fact).

**Existing instances**: `FlightRepository`, `AccommodationRepository`, `DestinationRepository`, `BudgetRepository`, `VisaRepository`, `WeatherRepository` — one per Discovery module, same six-way split as Providers, for a different reason (candidate generation vs. result persistence).

### Knowledge Graph

**Definition**: One specific Knowledge Source — `ai/intelligence/knowledge/` (`KnowledgeGraph`, `KnowledgeService`) — the structured, queryable graph of destinations, countries, and their relationships (199 nodes, 205 edges, per `docs/TRAVEL_INTELLIGENCE_LAYER.md`). Not a synonym for "Knowledge Source" in general; it's the largest and most structured *instance* of one.

**Test**: If the question is "what entities and relationships exist in the travel domain" (is Osaka in Japan; is Japan in Asia; what's Japan's continent for a `BudgetReasoner` lookup), it's the Knowledge Graph specifically, not the DNA classifier or the traveller profile.

### Internal Memory

**Definition**: Everything about *this specific traveller* or *this specific conversation* — as opposed to the Knowledge Graph's general-purpose facts about the world. Two distinct scopes, already established and unchanged by Trip Brain:

- **Long-term**: `ai/memory/` — the traveller's profile, preferences, loyalty data, persisting across every future conversation.
- **Short-term**: `ConversationSession` (`ai/concierge/conversation_engine.py`) — the current conversation's history, active goal, linked trip, pending questions. Discarded (or archived) at the end of the session, not carried forward automatically.

**Test**: If the answer changes depending on *who's asking*, it's Internal Memory. If it changes depending on *what they're asking about*, it's the Knowledge Graph or a Provider.

### Future Integrations

Not a category of what exists today — a placeholder for what Phase 5 (`docs/ROADMAP.md`) adds later, named here so Trip Brain's boundaries don't have to be redrawn when it arrives:

- **Vector store / embeddings / RAG** — would become a new kind of Knowledge Source, sitting alongside the Knowledge Graph, not replacing it. A Discovery module's Scorer would query it the same way it queries `ai/intelligence/` today — through the module's own code, not through Trip Brain reaching in on its behalf.
- **Live Provider feeds** (Amadeus, a hotel inventory API, Timatic, a climate feed, ...) — replace a Provider's internals, per each Discovery module's own already-documented migration path (`docs/EPIC3_ARCHITECTURE.md`'s table). No change to the Provider/Knowledge Source boundary — a live Provider is still owned by exactly one module and still never called directly by Trip Brain.
- **`PriceMonitorAgent` / `TravelInsightsAgent`** (`docs/ROADMAP.md` Phase 5) — proactive, not request-driven, so they sit outside the request/response lifecycle this document and `docs/TRIP_BRAIN_ARCHITECTURE.md` describe entirely. Out of scope here.

## Decision Table

When something new needs to read data, use this table to decide where it belongs:

| Question being asked | Answer lives in |
|---|---|
| "What flight/hotel/destination/budget-tier/visa-rule/climate options exist for this specific request?" | A Provider, inside its one owning Discovery module |
| "What does this traveller generally prefer / what's their inferred persona?" | Traveller DNA (`ai/intelligence/traveller_dna/`) |
| "What do we know about this traveller specifically — name, passport, loyalty?" | Internal Memory, long-term (`ai/memory/`) |
| "What did we already discuss this conversation / what trip or goal is linked?" | Internal Memory, short-term (`ConversationSession`) |
| "How does destination X relate to country Y / continent Z?" | Knowledge Graph (`ai/intelligence/knowledge/`) |
| "What did a Discovery module already decide, that we now need to look up by ID?" | That module's Repository |
| "How does an HTTP client reach this?" | An API (`router.py`) |

## Why This Matters for Trip Brain Specifically

Every architectural risk in `docs/TRIP_BRAIN_ARCHITECTURE.md` traces back to violating one of these boundaries:

- If the Coordinator called a Provider directly (e.g. `MockFlightProvider.search()` instead of `flight_intelligence_service.recommend()`), it would bypass that module's Normalizer/Scorer/Reasoner/RiskAssessor entirely — silently discarding scoring, explainability, and risk assessment for that domain. This is the single most important failure mode this document exists to prevent.
- If a Discovery module started reading another module's Repository (e.g. Accommodation Intelligence reading `BudgetRepository` to "helpfully" filter by a prior budget result), the six modules would stop being independent, breaking the property that made them shippable one at a time in Epic 2, and the exact "tight coupling" the Weather Intelligence task explicitly warned against (`docs/WEATHER_INTELLIGENCE_ENGINE.md`).
- If Trip Brain invented a new memory store instead of reading `ConversationSession` and `ai/memory/`, the traveller's context would fragment across three places instead of two, and nothing downstream (profile updates, goal/trip linkage) would stay consistent.

The rule that falls out of all three: **Trip Brain (and any future orchestration) only ever calls a Discovery module's public service method, or reads directly from a Knowledge Source. It never reaches past a Discovery module's public boundary into its Provider or Repository, and Discovery modules never reach into each other's.**
