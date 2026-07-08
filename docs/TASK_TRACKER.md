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
| T-013 | GitHub Actions CI/CD | `complete` | high | (this task) | `.github/workflows/ci.yml` — `pytest` (required), Ruff + frontend lint/build (advisory, see TD-016/TD-017); ADR-008 |

---

## Backlog — Sprint 2 (current)

| Task ID | Title | Status | Priority | Notes |
|---------|-------|--------|----------|-------|
| T-014 | Repository refactoring | `planned` | high | Close remaining Sprint 2 tech debt: TD-001 (legacy conversation layer), TD-002–TD-004 (dead orchestration module + duplicate registry + unreachable agents), TD-005 (duplicate AgentContext/AgentResult), TD-017 (Ruff violations) |
| T-012A | Platform Layer Test Coverage | `planned` | medium | Unit tests for `travelos/`: SDK, Service Registry, Event Bus, Configuration Manager, Service Container, shared base classes. Scheduled after T-014 (repository refactor) so it doesn't delay current progress; see TD-015 |
| T-015 | Flight Intelligence Engine | `planned` | high | Provider-agnostic flight search/compare agent |
| T-016 | Hotel Intelligence Engine | `planned` | high | Provider-agnostic accommodation search/compare agent |
| T-017 | Destination Intelligence Engine | `planned` | medium | Destination data, activities, local knowledge |
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
