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
| T-010 | Repository Audit and Architecture Review | `complete` | medium | (this task) | Audit doc, tech debt register, architecture recommendations, stray file cleanup |

---

## Backlog — Sprint 2

| Task ID | Title | Status | Priority | Notes |
|---------|-------|--------|----------|-------|
| T-011 | Remove legacy conversation layer | `planned` | high | Delete 3 old endpoints + `services/api/app/conversation/` module; see REC-001, TD-001 |
| T-012 | Remove dead orchestration module | `planned` | medium | Delete `ai/orchestration/`, assess dead specialist agents; see REC-002, TD-002–TD-004 |
| T-013 | Test infrastructure — Sprint 1 coverage | `planned` | critical | pytest in `services/api/tests/` and `ai/tests/`; DNA classifier, intent classifier, budget estimator, trip status logic; see REC-003, TD-007 |
| T-014 | Promote Traveller to domain | `planned` | medium | Move to `services/api/app/domains/traveller/`; see REC-006, TD-011 |
| T-015 | Frontend navigation component | `planned` | low | `apps/web/src/components/Navigation.tsx` in `layout.tsx`; see REC-007 |
| T-016 | Auth layer | `planned` | high | Clerk or NextAuth.js — protect API routes |
| T-017 | CI pipeline | `planned` | high | GitHub Actions: lint, type-check, tests on every PR |

---

## Backlog — Sprint 3

| Task ID | Title | Status | Priority | Notes |
|---------|-------|--------|----------|-------|
| T-018 | PostgreSQL persistence — Goals + Trips | `planned` | critical | Replace in-memory repositories; Alembic migrations |
| T-019 | Redis session store | `planned` | high | Replace in-memory conversation store; enables horizontal scaling |
| T-020 | Fix AI↔API dependency direction | `planned` | medium | Introduce PlanningPort interface; see REC-008, TD-006 |
| T-021 | Replace static KG enrichments with live queries | `planned` | medium | ItineraryBuilder reads from KnowledgeService at runtime; see REC-009, TD-010 |
| T-022 | Kuzu graph database | `planned` | medium | Replace in-memory KG with persistent Kuzu DB |
| T-023 | Consolidate AgentContext/AgentResult | `planned` | low | Single canonical definition in `ai/shared/`; see REC-005, TD-005 |

---

## Notes

- Task IDs are sequential and never reused.
- PR title format: `[T-011] Remove legacy conversation layer`
- Blocked tasks include the blocker in Notes.
- Technical debt items tracked in `docs/TECHNICAL_DEBT_REGISTER.md`.
- Architecture recommendations in `docs/ARCHITECTURE_RECOMMENDATIONS.md`.
