# TravelOS — System Architecture

## Vision

TravelOS is an AI-native travel operating system. It replaces fragmented, human-driven booking workflows with an intelligent agent hierarchy that plans, books, and manages the complete travel lifecycle on behalf of the traveller — autonomously.

The system is built for orchestration, not integration. Every capability is expressed as an agent or service that can be composed, replaced, or scaled independently.

---

## TravelOS Philosophy

| Principle | Meaning |
|-----------|---------|
| **Orchestration over integration** | Agents coordinate work; humans approve outcomes, not steps |
| **Profile as truth** | All decisions derive from the traveller's persistent profile |
| **Model agnostic** | No agent is hardwired to a single LLM provider |
| **Commerce as a layer** | Booking and payment are services agents call, not core logic |
| **Memory compounds** | Every trip makes the next recommendation smarter |

---

## AI Agent Hierarchy

```
┌──────────────────────────────────────────────────────────┐
│                   TRAVEL CONCIERGE                       │
│   Natural language interface. Understands intent,        │
│   delegates to Travel Manager. The user's single point   │
│   of contact.                                            │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                   TRAVEL MANAGER                         │
│   Orchestrates the full trip. Decomposes requests into   │
│   department tasks. Assembles the final itinerary.       │
└──────┬──────────────┬──────────────┬──────────────┬──────┘
       │              │              │              │
┌──────▼──────┐ ┌─────▼──────┐ ┌────▼──────┐ ┌────▼──────┐
│  FLIGHTS    │ │    STAY    │ │ TRANSPORT │ │EXPERIENCES│
│  Dept.      │ │    Dept.   │ │   Dept.   │ │   Dept.   │
└──────┬──────┘ └─────┬──────┘ └────┬──────┘ └────┬──────┘
       │              │              │              │
┌──────▼──────────────▼──────────────▼──────────────▼──────┐
│                  SPECIALIST AGENTS                        │
│  FlightSearch · HotelSearch · CarRental · ActivitySearch  │
│  PriceMonitor · VisaChecker · WeatherAdvisor · etc.      │
└──────────────────────────┬────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
┌─────────▼──────┐ ┌───────▼──────┐ ┌──────▼────────┐
│    MEMORY      │ │  KNOWLEDGE   │ │   COMMERCE    │
│  Traveller     │ │  Destination │ │  Booking APIs │
│  profiles,     │ │  data, rules,│ │  Payment,     │
│  trip history, │ │  regulations,│ │  confirmations│
│  preferences   │ │  embeddings  │ │  receipts     │
└────────────────┘ └──────────────┘ └───────────────┘
```

### Layer Responsibilities

| Layer | Role | Sprint |
|-------|------|--------|
| **Travel Concierge** | NL interface, intent parsing, user communication | Sprint 3 |
| **Travel Manager** | Trip decomposition, department routing, assembly | Sprint 0 ✓ |
| **Departments** | Domain-scoped orchestration (flights, stays, etc.) | Sprint 2 |
| **Specialist Agents** | Single-task executors (search, compare, book) | Sprint 2–4 |
| **Memory** | Traveller profiles, history, preferences | Sprint 1 |
| **Knowledge** | Destination data, rules, embeddings, RAG | Sprint 4 |
| **Commerce** | Booking, payment, confirmation, receipts | Sprint 6 |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                        │
│           apps/web  —  Next.js 15 (App Router)           │
│     Browser UI · SSR pages · API routes · Auth           │
└──────────────────────────┬───────────────────────────────┘
                           │ HTTPS / WebSocket
┌──────────────────────────▼───────────────────────────────┐
│                       API LAYER                          │
│            services/api  —  FastAPI (Python)             │
│    REST endpoints · Request validation · Auth middleware  │
│    Agent dispatch · Response serialisation               │
└──────────────────────────┬───────────────────────────────┘
                           │ Python imports (Sprint 0–1)
                           │ Message queue (Sprint 3+)
┌──────────────────────────▼───────────────────────────────┐
│               CONCIERGE / MANAGER LAYER                  │
│   ai/concierge/  intent, decision, conversation engine    │
│   ai/trip_brain/ Trip Brain — PLAN_TRIP orchestration,    │
│                   calls six core Discovery modules and    │
│                   optional Event Intelligence;            │
│                   trip_assembly.py (T-040) is a second,   │
│                   separate caller of Trip Brain's own     │
│                   output — never a change to Trip Brain   │
│   ai/explainability/ Explainability Engine — turns Trip   │
│                   Brain's merged results into traveller-  │
│                   facing drivers/trade-offs/confidence     │
│   ai/manager/    TravelManager — dispatches via registry, │
│                   still active for MODIFY_TRIP,           │
│                   DESTINATION_QUESTION, TRAVEL_ADVICE,    │
│                   BUDGET_ADVICE (not PLAN_TRIP)           │
│   ai/registry/   AgentRegistry — agent name → class       │
│    Session management · Agent routing · Error handling   │
└──────┬─────────────┬─────────────┬───────────────────────┘
       │              │             │
┌──────▼──────┐ ┌─────▼──────┐ ┌────▼──────┐
│   AGENTS    │ │ DISCOVERY  │ │  MEMORY   │
│  ai/agents/ │ │ai/discovery/│ │ ai/memory/│
└─────────────┘ └─────┬──────┘ └───────────┘
                       │ provider access (Flight/Accommodation/Weather/Events)
                ┌──────▼───────────────────┐
                │   INTELLIGENCE GATEWAY   │
                │ travelos/intelligence_gateway/ │
                │ contract · registry ·    │
                │ selection · cache ·      │
                │ retry · failover ·       │
                │ rate limit               │
                └──────┬────────────────────┘
                       │
                ┌──────▼──────┐         ┌──────────────────┐
                │Mock Provider│         │ BaseLiveProvider │
                │  (T-025)    │         │ travelos/live_providers/
                └─────────────┘         │ (T-026)          │
                                         │ DuffelFlightProvider
                                         │ + DuffelStaysProvider
                                         │ + HttpxTransport │
                                         │ (T-027/T-037,    │
                                         │  T-039; FLIGHTS  │
                                         │  + ACCOMMODATION)│
                                         └──────────────────┘
```

`PLAN_TRIP` is the only intent Trip Brain handles; `TravelManager`/`AgentRegistry` remain the active dispatcher for the four intents above. See `docs/TRIP_BRAIN_ARCHITECTURE.md` and `docs/ADR/ADR-018-legacy-orchestration-retirement.md` for why full retirement of `ai/manager/`/`ai/registry/` is not yet possible.

Trip Brain's `plan()` also calls the Explainability Engine once per request, right after merging module results — see `docs/EXPLAINABILITY_ENGINE.md` and `docs/ADR/ADR-019-explainability-engine.md`. It is presentation-only: it explains `ai/discovery/` and Trip Brain's existing output, never scores or recommends anything itself.

Flight, Accommodation, Weather, and Event Intelligence obtain their provider through the Intelligence Gateway (`travelos/intelligence_gateway/`) rather than constructing a provider directly — see `docs/INTELLIGENCE_GATEWAY.md`, `docs/EVENT_INTELLIGENCE.md`, ADR-020, and ADR-033. Only Discovery modules call the gateway; the Trip Brain is never wired to a provider directly, preserving the same layering ADR-017 established.

`travelos/live_providers/` (T-026) is the reusable base a real vendor integration would extend — `BaseLiveProvider` implements the same `Provider` contract a mock provider does, so the gateway above needed zero changes to support it. See `docs/LIVE_PROVIDER_FRAMEWORK.md` and `docs/ADR/ADR-021-live-provider-framework.md`.

**FLIGHTS and ACCOMMODATION each have a real, independently switchable live vendor (T-038, T-039)** — `DuffelFlightProvider` (T-027) and `DuffelStaysProvider` (T-039), both over `HttpxTransport` (T-037), selected by `TRALVANA_FLIGHT_PROVIDER_MODE`/`TRALVANA_ACCOMMODATION_PROVIDER_MODE` respectively (`MOCK` by default for both), via `IntelligenceGateway._environment_for(capability)`'s generalized per-capability lookup (`docs/INTELLIGENCE_GATEWAY.md`'s "Live Providers and Per-Capability Environment Resolution" section) — Weather still resolves its provider environment from the general `PROVIDER_ENVIRONMENT` var, untouched by either switch. See `docs/LIVE_FLIGHT_SEARCH.md`/`docs/ADR/ADR-024-live-flight-product-integration.md` and `docs/LIVE_ACCOMMODATION_SEARCH.md`/`docs/ADR/ADR-025-duffel-stays-integration.md`. **Accommodation's live path is fully built and tested but not yet verified against real Duffel Stays data** — the account's token lacks Stays access (`docs/DUFFEL_STAYS_INTEGRATION.md`'s Access Requirement section).

Accommodation's live path also differs structurally from Flights': `DuffelStaysProvider` resolves a destination string to coordinates via Duffel's Places API internally, and its `parse_response()` output is absorbed by `AccommodationNormalizer` (a second raw-vocabulary branch alongside the mock's own), rather than mapping directly to canonical fields the way `DuffelFlightProvider` does — Accommodation's pipeline has an explicit Normaliser stage Flights' pipeline doesn't.

**The AI Travel Planner (T-040) is now the primary user experience** — a traveller describes a trip in natural language via `POST /planner/plan` (`services/api/app/routers/planner.py`, backed by `apps/web/src/app/planner/page.tsx`) and receives one coherent, consultant-style itinerary. This reuses `travel_concierge.handle()`/`ConversationEngine.process()`/`TripBrain.plan()` entirely unchanged — the only new component is `ai/trip_brain/trip_assembly.py`'s `TripAssemblyEngine`, a second, separate caller of Trip Brain's own output (the same relationship `ConversationEngine` and `POST /explain` already have with it) that assembles an executive summary, per-module recommendations, a daily outline (reusing `ai/planning/itinerary_builder.py`, T-008 — not duplicated), risks, assumptions, confidence, and alternatives into one `TripItinerary`. See `docs/AI_TRAVEL_PLANNER.md` and `docs/ADR/ADR-026-trip-assembly-engine.md`. No module's score is ever recalculated by this layer.

---

## Folder Responsibilities

```
tralvana-ai/
├── apps/
│   └── web/              UI layer — Next.js, React, Tailwind
│       └── src/app/      App Router pages and layouts
│
├── services/
│   └── api/              API layer — FastAPI app
│       └── app/
│           ├── routers/  One file per resource group
│           └── models/   Pydantic request/response schemas
│
├── ai/
│   ├── agents/           One file per specialist agent class (flight/hotel/budget/
│   │                     experience/visa — still live, dispatched by TravelManager
│   │                     for MODIFY_TRIP/DESTINATION_QUESTION/TRAVEL_ADVICE/BUDGET_ADVICE)
│   ├── concierge/        Intent classification, decision engine, conversation engine
│   ├── discovery/        Six core modules plus optional events (flights,
│   │                     accommodation, destinations, budget, visa, weather,
│   │                     events) — provider-neutral and explainable
│   ├── trip_brain/       Trip Brain — orchestrates core modules plus relevant events
│   ├── explainability/   Explainability Engine — turns Trip Brain/Discovery reasoning
│   │                     into traveller-facing drivers, trade-offs, and confidence
│   ├── manager/          TravelManager — dispatches to agents via the registry;
│   │                     active for MODIFY_TRIP/DESTINATION_QUESTION/TRAVEL_ADVICE/
│   │                     BUDGET_ADVICE only, not PLAN_TRIP (see ADR-018)
│   ├── registry/         AgentRegistry — agent name → class lookup
│   ├── shared/           Canonical AgentContext / AgentResult / AgentStatus types
│   └── memory/           Profile schema, memory adapters
│
├── travelos/              Platform layer — SDK, DI container, service registry,
│   │                      configuration, structured logging, event bus (docs/PLATFORM_LAYER.md)
│   ├── intelligence_gateway/  Provider-access infrastructure — mock/future-live
│   │                      knowledge sources behind one contract, with caching,
│   │                      retry, failover, and rate limiting (docs/INTELLIGENCE_GATEWAY.md)
│   └── live_providers/    Reusable base for a real vendor integration — auth,
│                          transport, request/response mapping, error model,
│                          health/tracing/metrics (docs/LIVE_PROVIDER_FRAMEWORK.md)
│
├── docs/                 Architecture authority (this folder)
├── handoff/              Agent-to-agent start documents
├── scripts/              Developer runbooks
└── infrastructure/       Docker, cloud config (future)
```

---

## Service Boundaries

| Service | Owns | Does NOT own |
|---------|------|-------------|
| `apps/web` | UI state, routing, auth session | Business logic, agent calls |
| `services/api` | HTTP contract, validation, auth | Agent implementation |
| `ai/` | Agent logic, orchestration, memory | HTTP transport, UI |
| `ai/memory/` | Traveller data schema | Persistence engine |
| `infrastructure/` | Deployment, scaling | Application code |

---

## Communication Flow

### Sprint 0–1 (current)
```
Browser → Next.js → FastAPI → TravelConcierge → TravelManager → Agent → return
```
Direct Python calls within one process. No network hops after FastAPI.

### Sprint 3+ (target)
```
Browser → Next.js → FastAPI → Message Queue → TravelManager → Agents
                                                           ↕
                                                    Memory / Knowledge
```
Async task queue decouples API response time from agent execution time.

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Next.js 15, React 19 | App Router, SSR, streaming |
| Styling | Tailwind CSS 3 | Utility-first, consistent |
| API | FastAPI, Python 3.12 | Async, typed, fast iteration |
| Validation | Pydantic v2 | Schema-first, fast |
| Agent runtime | Python async | Native async agent execution |
| LLM (Sprint 1+) | Anthropic Claude (default) | Best reasoning, model-agnostic design |
| Memory (Sprint 1) | SQLite → PostgreSQL | Progressive persistence |
| Vector store (Sprint 4) | pgvector or Chroma | RAG for knowledge layer |
| Auth (Sprint 2) | Clerk or NextAuth.js | Delegated, not custom |
| Infra (Sprint 5+) | Docker, Railway / Fly.io | Incremental cloud migration |

---

## Future Microservices (Sprint 5+)

When the monolith needs to split, these are the natural boundaries:

| Service | Responsibility |
|---------|---------------|
| `concierge-service` | NL interface, session management |
| `planning-service` | Trip planning, itinerary assembly |
| `search-service` | Flight/hotel/activity search aggregation |
| `memory-service` | Traveller profile CRUD and retrieval |
| `knowledge-service` | Destination data, RAG, embeddings |
| `commerce-service` | Booking, payment, confirmation |
| `notification-service` | Alerts, itinerary updates, check-in reminders |
