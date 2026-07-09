# Task Tracker

Live register of all engineering tasks. Update status in the same PR that completes the work.

**Statuses:** `planned` · `in-progress` · `complete` · `blocked` · `cancelled`
**Priorities:** `critical` · `high` · `medium` · `low`

---

## Completed Tasks

| Task ID | Title | Status | Priority | Commit | Notes |
|---------|-------|--------|----------|--------|-------|
| T-001 | Bootstrap project foundation | `complete` | critical | Sprint 0 | Next.js 15 + FastAPI + AI directory structure |
| T-001B | Complete Sprint 0 scaffold | `complete` | critical | Sprint 0 | AI agent layer, orchestrator, memory schema, architecture docs |
| T-002 | Initial commit and remote push | `complete` | high | Sprint 0 | Repo live at github.com/Diajem/tralvana-ai |
| T-003 | Create Architecture Authority | `complete` | high | Sprint 0 | ARCHITECTURE.md, ENGINEERING_PRINCIPLES.md, CODING_STANDARDS.md, ROADMAP.md |
| T-004 | Traveller DNA + Travel Intelligence Layer | `complete` | critical | Sprint 1 | `ai/intelligence/` — KG (199 nodes, 205 edges), ontology, reasoning, DNA inference (12 types), memory service |
| T-005 | Traveller Profile API | `complete` | high | Sprint 1 | `POST /traveller/profile`, `GET /traveller/profile/{id}` — in-memory store; onboarding frontend |
| T-006 | Conversation Engine | `complete` | high | Sprint 1 | `ai/concierge/` — intent classifier, decision engine, session store, TravelConcierge facade; `POST /conversation/message` |
| T-007 | Goal Planning Engine | `complete` | high | Sprint 1 | `ai/goals/` + `services/api/app/domains/goals/` — GoalReasoner, CRUD, readiness scoring; `/goals/new` + `/goals/[id]` |
| T-008 | Trip Planning Engine | `complete` | high | `889ab4c` | `ai/planning/` + `services/api/app/domains/trips/` — itinerary/budget/risk; trip auto-trigger from conversation; `/trips/new` + `/trips/[id]` |
| T-009 | End-to-End TravelOS Integration Demo | `complete` | high | `8a8ab1e` | `services/api/app/demo/` — 7-stage pipeline; `POST /demo/japan-football-food`; frontend `/demo` |
| T-010 | Repository Audit and Architecture Review | `complete` | medium | `1d10953` | Audit doc, tech debt register, architecture recommendations, stray file cleanup |
| T-011 | Platform Layer | `complete` | high | `aa5934a` | `travelos/` — SDK, DI container, service registry, config, structured logging, event bus, shared types (`Result`, `Identifier`, `Timestamp`, `Pagination`); ADR-006 |
| T-012 | Testing Framework | `complete` | critical | `aa5934a` | pytest suite — 30 backend API tests + 62 AI layer tests (92 total, all passing); ADR-007; resolves TD-007 |
| T-013 | GitHub Actions CI/CD | `complete` | high | `2a17d6c` | `.github/workflows/ci.yml` — `pytest` (required), Ruff + frontend lint/build (advisory, see TD-016/TD-017); ADR-008 |
| T-014 | Repository Stabilisation & Engineering Refactor | `complete` | high | `07f63eb` | Closed TD-001 (legacy conversation layer removed), TD-002/TD-003 (dead `ai/orchestration/` removed), TD-004 (found to be a false positive — the 5 specialist agents are live, not dead), TD-005 (duplicate `AgentContext`/`AgentResult` resolved), TD-016 (ESLint config fixed), TD-017 (Ruff violations 72 → 0). No API or behaviour changes; 92/92 tests pass throughout. ADR-009 |
| T-015 | Flight Intelligence Engine | `complete` | high | `85664fe` | First Discovery Layer module — `services/api/app/domains/flights/` + `ai/discovery/flights/` (scorer/reasoner/risk assessor/orchestrator); `POST /flights/recommend`, `GET /flights/{id}`, `GET /trips/{id}/flights`; new `Intent.FLIGHT_SEARCH` conversation routing; `/flights/recommend` + `/flights/[id]` frontend; 49 new tests (141 total, all passing); ADR-010 |
| T-016 | Discovery Layer Pattern and Accommodation Intelligence | `complete` | high | `2a7112d` | `docs/DISCOVERY_LAYER_PATTERN.md` (ADR-011) formalises the 7-stage pipeline. Second Discovery module — `services/api/app/domains/accommodation/` + `ai/discovery/accommodation/` (provider/normalizer/scorer/reasoner/risk assessor/orchestrator, first module with a genuine Provider/Normalizer split); `POST /accommodation/recommend`, `GET /accommodation/{id}`, `GET /trips/{id}/accommodation`; new `Intent.ACCOMMODATION_SEARCH` conversation routing; `/accommodation/recommend` + `/accommodation/[id]` frontend; found and fixed a labelling-algorithm pigeonhole bug and a shared entity-extractor bug ("to stay" misread as a destination); 70 new tests (211 total, all passing); ADR-012 |
| T-017 | Destination Intelligence Engine | `complete` | medium | (this task) | Third Discovery module — `services/api/app/domains/destinations/` + `ai/discovery/destinations/` (provider/normalizer/scorer/reasoner/risk assessor/orchestrator); 10-city mock catalogue (60 entries, all 12 `DestinationType` values); dual-mode search (city given → places within it, omitted → compare cities); `POST /destinations/recommend`, `GET /destinations/{id}`, `GET /trips/{id}/destinations`; new `Intent.DESTINATION_DISCOVERY` conversation routing (always-ready, no destination required); `/destinations/recommend` + `/destinations/[id]` frontend; found and fixed a persona-relevance bug (irrelevant categories like BEST_FOR_FOOTBALL forced onto football-irrelevant cities) and an off-season boundary bug in the risk assessor; 78 new tests (289 total, all passing); ADR-013 |

---

## Backlog — Sprint 2 (current)

| Task ID | Title | Status | Priority | Notes |
|---------|-------|--------|----------|-------|
| T-012A | Platform Layer Test Coverage | `planned` | medium | Unit tests for `travelos/`: SDK, Service Registry, Event Bus, Configuration Manager, Service Container, shared base classes; see TD-015. Now unblocked — T-014 is complete |
| T-018 | Visa Intelligence Engine | `planned` | medium | Entry requirements by nationality/destination |
| T-019 | Weather & Safety Intelligence | `planned` | medium | Destination weather + safety advisories |
| T-020 | Budget Optimisation Engine | `planned` | medium | Cross-trip budget optimisation, replaces static budget estimator paths |

---

## Backlog — Sprint 3

| Task ID | Title | Status | Priority | Notes |
|---------|-------|--------|----------|-------|
| T-021 | PostgreSQL persistence — Goals + Trips | `planned` | critical | Replace in-memory repositories; Alembic migrations |
| T-022 | Redis session store | `planned` | high | Replace in-memory conversation store; enables horizontal scaling |
| T-023 | Fix AI↔API dependency direction | `planned` | medium | Introduce PlanningPort interface; see REC-008, TD-006 |
| T-024 | Replace static KG enrichments with live queries | `planned` | medium | ItineraryBuilder reads from KnowledgeService at runtime; see REC-009, TD-010 |
| T-025 | Kuzu graph database | `planned` | medium | Replace in-memory KG with persistent Kuzu DB |
| T-026 | Promote Traveller to domain | `planned` | medium | Move to `services/api/app/domains/traveller/`; see REC-006, TD-011 |
| T-027 | Auth layer | `planned` | high | Clerk or NextAuth.js — protect API routes |

---

## Notes

- Task IDs are sequential and never reused.
- PR title format: `[T-013] GitHub Actions CI/CD`
- Blocked tasks include the blocker in Notes.
- Technical debt items tracked in `docs/TECHNICAL_DEBT_REGISTER.md`.
- Architecture recommendations in `docs/ARCHITECTURE_RECOMMENDATIONS.md`.
- 2026-07-08: Renumbered Sprint 2/3 backlog to match the actual roadmap in use (T-013 CI/CD → T-020 Budget Optimisation Engine). Previous T-011–T-023 numbering (legacy conversation removal, dead orchestration removal, etc.) is superseded — see `TECHNICAL_DEBT_REGISTER.md` for those items, now tracked as TD-001–TD-005 under T-014.
- 2026-07-08: T-014 closed TD-001, TD-002, TD-003, TD-004, TD-005, TD-016, TD-017. Investigation found TD-002/TD-004's original T-010 description had the two `AgentRegistry` implementations backwards — `ai/registry/agent_registry.py` (budget/experience/flight/hotel/visa agents) was the active one, not `ai/orchestration/agent_registry.py`. See TD-002/TD-004 correction notes in `TECHNICAL_DEBT_REGISTER.md` and ADR-009.
