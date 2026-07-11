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
│                   calls the six Discovery modules         │
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
                       │ provider access (Flight/Accommodation/Weather)
                ┌──────▼───────────────────┐
                │   INTELLIGENCE GATEWAY   │
                │ travelos/intelligence_gateway/ │
                │ contract · registry ·    │
                │ selection · cache ·      │
                │ retry · failover ·       │
                │ rate limit               │
                └──────┬────────────────────┘
                       │
                ┌──────▼──────┐
                │Mock Provider│  (future: live provider, same contract)
                └─────────────┘
```

`PLAN_TRIP` is the only intent Trip Brain handles; `TravelManager`/`AgentRegistry` remain the active dispatcher for the four intents above. See `docs/TRIP_BRAIN_ARCHITECTURE.md` and `docs/ADR/ADR-018-legacy-orchestration-retirement.md` for why full retirement of `ai/manager/`/`ai/registry/` is not yet possible.

Trip Brain's `plan()` also calls the Explainability Engine once per request, right after merging module results — see `docs/EXPLAINABILITY_ENGINE.md` and `docs/ADR/ADR-019-explainability-engine.md`. It is presentation-only: it explains `ai/discovery/` and Trip Brain's existing output, never scores or recommends anything itself.

Three of the six Discovery modules (Flight, Accommodation, Weather) obtain their provider through the Intelligence Gateway (`travelos/intelligence_gateway/`) rather than constructing a mock provider directly — see `docs/INTELLIGENCE_GATEWAY.md` and `docs/ADR/ADR-020-intelligence-gateway.md`. Only Discovery modules call the gateway; the Trip Brain is never wired to a provider directly, preserving the same layering ADR-017 established.

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
│   ├── discovery/        Six Discovery Layer modules (flights, accommodation,
│   │                     destinations, budget, visa, weather) — real, explainable
│   ├── trip_brain/       Trip Brain — orchestrates the six Discovery modules for PLAN_TRIP
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
│   └── intelligence_gateway/  Provider-access infrastructure — mock/future-live
│                          knowledge sources behind one contract, with caching,
│                          retry, failover, and rate limiting (docs/INTELLIGENCE_GATEWAY.md)
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
