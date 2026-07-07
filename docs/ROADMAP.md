# TravelOS — Implementation Roadmap

A phased delivery plan from scaffold to full operating system. Each phase produces a deployable, demonstrable increment.

---

## Phase 1 — Foundation
**Goal:** Runnable development environment with working API and agent scaffold.

**Deliverables:**
- Next.js 15 frontend scaffold (App Router, Tailwind, TypeScript)
- FastAPI backend with `/health` endpoint
- `BaseAgent` + `TravelManagerAgent` stub
- `Orchestrator` routing layer
- Traveller profile schema (no persistence)
- Architecture, principles, standards, and roadmap documentation
- Docker Compose local development
- Initial commit on GitHub

**Definition of done:** `npm run dev` and `uvicorn` both start without errors. `GET /health` returns `{"status": "ok"}`.

**Status:** ✅ Complete

---

## Phase 2 — Traveller Intelligence
**Goal:** A persistent traveller profile that personalises every agent decision.

**Deliverables:**
- `POST /agents/run` endpoint (orchestrator wired into API)
- Traveller profile CRUD API (`/profile/{traveller_id}`)
- SQLite persistence (profile + trip history)
- `ProfileMemory` adapter in `ai/memory/`
- Unit tests for all agents
- CI pipeline (GitHub Actions: lint, type-check, tests)
- Auth layer (Clerk) — frontend login + protected API routes

**Definition of done:** A registered traveller's preferences persist across sessions and are passed to agent context on every run.

**Status:** 🔲 Planned

---

## Phase 3 — AI Concierge
**Goal:** A conversational interface that understands travel intent in natural language.

**Deliverables:**
- LLM provider adapter (`ai/llm/`) — Anthropic Claude default
- `TravelConciergeAgent` — intent parsing, NL → structured request
- Streaming responses from API to frontend (Server-Sent Events)
- Conversational UI in `apps/web` — chat interface with trip context
- Session memory (conversation history per traveller)
- Message queue between API and orchestrator (Redis or Celery)

**Definition of done:** A user can say "I need to be in Lagos next Friday for 3 nights" and the Concierge produces a structured trip plan with the correct destination, dates, and preferences applied.

**Status:** 🔲 Planned

---

## Phase 4 — Travel Planning
**Goal:** End-to-end trip planning with real search results.

**Deliverables:**
- `FlightSearchAgent` — aggregates flight options (provider-agnostic interface)
- `HotelSearchAgent` — accommodation options
- `VisaCheckerAgent` — entry requirements by nationality
- `WeatherAdvisorAgent` — destination weather for travel dates
- Department layer (Flights Dept, Stay Dept, Transport Dept)
- Itinerary assembly — Travel Manager combines department results
- Itinerary UI — structured trip view in frontend

**Definition of done:** Given a destination, dates, and traveller profile, TravelOS returns a complete itinerary plan with flight options, hotel options, visa requirements, and weather summary.

**Status:** 🔲 Planned

---

## Phase 5 — Travel Intelligence
**Goal:** Recommendations that improve with every trip, powered by a knowledge layer.

**Deliverables:**
- Knowledge layer (`ai/knowledge/`) — destination data, rules, embeddings
- Vector store (pgvector or Chroma) for semantic search
- RAG pipeline — agent queries knowledge base before recommending
- `PriceMonitorAgent` — tracks price changes on saved trips
- Preference learning — profile updates based on booking patterns
- `TravelInsightsAgent` — proactive suggestions ("Your Lagos trip: hotel prices are rising")
- PostgreSQL migration (from SQLite)

**Definition of done:** The system proactively surfaces a relevant insight for a returning traveller based on their history and current market data.

**Status:** 🔲 Planned

---

## Phase 6 — Commerce
**Goal:** TravelOS books and manages travel end-to-end, handling payment and confirmation.

**Deliverables:**
- Commerce layer (`services/commerce/`) — provider-agnostic booking interface
- `BookingAgent` — executes confirmed bookings via provider APIs
- `PaymentProvider` adapter — Stripe (default)
- Confirmation and receipt storage
- Itinerary management — changes, cancellations, refunds
- Push notifications — check-in reminders, flight status, itinerary updates
- `notification-service` (microservice extraction)

**Definition of done:** A traveller can confirm a trip plan in the UI and receive email confirmation of flights and hotel within 60 seconds. Itinerary is stored and retrievable.

**Status:** 🔲 Planned

---

## Phase 7 — TravelOS
**Goal:** A production-grade, multi-traveller platform operating as a travel OS.

**Deliverables:**
- Multi-tenant architecture — organisation accounts with team travel management
- `TravelManagerRole` — corporate travel manager dashboard
- Policy engine — travel policies enforced at booking (budget caps, airline preferences)
- Analytics dashboard — spend, patterns, carbon footprint
- Mobile app (`apps/mobile/` — React Native)
- Microservices extraction (concierge, planning, search, memory, commerce, notifications)
- SLA monitoring and alerting
- GDPR compliance tooling (data export, deletion)
- Production infrastructure (cloud deployment, CDN, managed DB)

**Definition of done:** TravelOS handles 100+ concurrent traveller sessions, enforces company travel policies, and a corporate travel manager can view team spend and approve trips in real time.

**Status:** 🔲 Planned

---

## Timeline Orientation

| Phase | Name | Scope |
|-------|------|-------|
| 1 | Foundation | ✅ Complete |
| 2 | Traveller Intelligence | Sprint 1–2 |
| 3 | AI Concierge | Sprint 3–4 |
| 4 | Travel Planning | Sprint 5–7 |
| 5 | Travel Intelligence | Sprint 8–10 |
| 6 | Commerce | Sprint 11–13 |
| 7 | TravelOS | Sprint 14+ |

Sprints are two-week cycles. Timeline depends on resource allocation and scope decisions per sprint.
