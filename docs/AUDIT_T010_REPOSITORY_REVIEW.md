# T-010 Repository Audit — Architecture Review

**Date**: 2026-07-08
**Sprint**: 1 (post-T-009)
**Scope**: Full codebase — `ai/`, `services/api/`, `apps/web/`, `docs/`

---

## 1. Folder Structure

```
tralvana-ai/
├── ai/                         ← All AI logic (intelligence, planning, concierge)
│   ├── agents/                 ← Specialist agents (Budget, Flight, Hotel, Visa, Experience)
│   ├── concierge/              ← Active conversation pipeline
│   ├── goals/                  ← Goal classifier and reasoner
│   ├── intelligence/           ← DNA, ontology, knowledge graph, reasoning
│   │   ├── knowledge/
│   │   ├── ontology/
│   │   ├── reasoning/
│   │   └── traveller_dna/
│   ├── manager/                ← TravelManager (active agent dispatcher)
│   ├── memory/                 ← Traveller profile memory
│   ├── orchestration/          ← DEAD — Orchestrator + duplicate AgentRegistry
│   ├── planning/               ← Trip planner, itinerary, budget, risk
│   ├── registry/               ← AgentRegistry used by TravelManager
│   └── shared/                 ← AgentContext, AgentResult, AgentStatus
├── apps/web/src/               ← Next.js 15 frontend
│   ├── app/                    ← Pages (demo, goals, onboarding, profile, trips)
│   ├── components/onboarding/  ← 4-step onboarding form
│   ├── lib/api.ts              ← Fetch wrappers for all API endpoints
│   └── types/                  ← TypeScript interfaces
├── services/api/app/           ← FastAPI backend
│   ├── conversation/           ← LEGACY — old conversation stack (3 stale endpoints)
│   ├── demo/                   ← Demo endpoint
│   ├── domains/goals/          ← Goals domain (model, schema, repo, service, router)
│   ├── domains/trips/          ← Trips domain (model, schema, repo, service, router)
│   ├── models/                 ← Traveller model
│   ├── routers/                ← Health + Traveller routers
│   └── services/               ← TravellerService
├── docs/                       ← Product + engineering documentation
│   └── ADR/                    ← 5 architectural decision records
├── handoff/                    ← Agent handoff context files
├── infrastructure/             ← EMPTY — placeholder for IaC
└── scripts/                    ← local-start.md (not a script, a guide)
```

### Issues

| # | Location | Issue |
|---|----------|-------|
| F-1 | `ai/orchestration/` | Entire module is dead code — Orchestrator never wired into main.py |
| F-2 | `services/api/app/conversation/` | Legacy module — 3 endpoints that bypass the active AI pipeline |
| F-3 | `infrastructure/` | Empty directory — remove or populate |
| F-4 | `scripts/local-start.md` | A markdown guide inside `scripts/` — should be `docs/LOCAL_SETUP.md` |
| F-5 | `ai/shared/` | Re-defines `AgentContext` and `AgentResult` already defined in `ai/agents/base_agent.py` |

---

## 2. Naming Consistency

### Duplicate class names across modules

| Class | Location 1 (active) | Location 2 (legacy) |
|-------|---------------------|---------------------|
| `ConversationEngine` | `ai/concierge/conversation_engine.py` | `services/api/app/conversation/conversation_engine.py` |
| `ConversationSession` | `ai/concierge/conversation_engine.py` | `services/api/app/conversation/conversation_session.py` |
| `ConversationMessage` | `ai/concierge/conversation_engine.py` | `services/api/app/conversation/conversation_session.py` |
| `IntentClassifier` | `ai/concierge/intent_classifier.py` | `services/api/app/conversation/intent_classifier.py` |
| `ResponseComposer` | `ai/concierge/response_composer.py` | `services/api/app/conversation/response_composer.py` |
| `AgentRegistry` | `ai/registry/agent_registry.py` | `ai/orchestration/agent_registry.py` |
| `AgentContext` | `ai/shared/agent_context.py` | `ai/agents/base_agent.py` |
| `AgentResult` | `ai/shared/agent_result.py` | `ai/agents/base_agent.py` |

### Naming inconsistencies

| # | Issue |
|---|-------|
| N-1 | Backend uses `traveller` (British spelling) everywhere; one Pydantic field uses `traveler` — verify |
| N-2 | `plan_from_conversation()` in `TripPlanningService` but `_create_trip()` in conversation engine — different verbs for the same concept |
| N-3 | Some AI modules use `_service` suffix (e.g. `knowledge_service`), others don't (e.g. `trip_planner`) |

---

## 3. Service Boundaries

### Active service graph (what actually runs)

```
POST /conversation/message
  └── ai.concierge.TravelConcierge
        └── ai.concierge.ConversationEngine
              ├── ai.concierge.IntentClassifier
              ├── ai.concierge.DecisionEngine
              ├── ai.manager.TravelManager → ai.registry.AgentRegistry
              ├── ai.goals.GoalReasoner ← lazy import
              ├── ai.goals.GoalClassifier ← lazy import
              ├── ai.domains.goals.GoalService ← lazy import
              └── ai.domains.trips.TripPlanningService ← lazy import

POST /trips/plan
  └── app.domains.trips.TripPlanningService
        └── ai.planning.TripPlanner
              ├── ai.planning.ItineraryBuilder
              ├── ai.planning.BudgetEstimator → ai.intelligence.reasoning.BudgetReasoner
              └── ai.planning.RiskAssessor → ai.intelligence.reasoning.SafetyReasoner

POST /demo/japan-football-food
  └── app.demo.DemoService  (calls all of the above)
```

### Legacy / parallel services (not integrated)

```
POST /conversation/start          → app.conversation.ConversationEngine (legacy)
POST /conversation/{id}/message   → app.conversation.ConversationEngine (legacy)
GET  /conversation/{id}           → app.conversation.ConversationEngine (legacy)

Orchestrator.run()                → ai.orchestration.AgentRegistry → Budget/Flight/Hotel/Visa/Experience
(Never called from any active path)
```

### Boundary violations

| # | Issue |
|---|-------|
| B-1 | `conversation_router.py` imports both `app.conversation.conversation_engine` AND `ai.concierge.travel_concierge` — two different conversation stacks in one router file |
| B-2 | `demo_service.py` calls `goal_service.create()` on every demo run, writing to the shared in-memory goal store — no isolation between demo and live data |
| B-3 | `TripPlanningService.plan_from_conversation()` uses lazy imports to avoid circular deps — symptom of a boundary issue between `ai/` and `services/api/app/` |
| B-4 | `DemoService._run_conversation()` triggers `_create_trip()` inside the conversation engine, creating a second trip plan alongside the explicit `_run_trip()` call — potential for duplicate trip plans |

---

## 4. AI Layer Boundaries

The AI layer is `ai/` — it should not depend on `services/api/app/`. Currently:

- `ai/concierge/conversation_engine.py` imports from `app.domains.goals.service` and `app.domains.trips.service` (lazy, inside methods) — this crosses the AI ↔ API boundary
- `ai/planning/budget_estimator.py` imports `ai.intelligence.reasoning.budget_reasoner` — correct
- `ai/planning/risk_assessor.py` imports `ai.intelligence.reasoning.safety_reasoner` — correct

**Issue A-1**: The concierge (AI layer) directly calls domain services (API layer). The correct direction is API → AI, never AI → API. This works in Sprint 1 because everything is a singleton, but it will cause test isolation and deployment issues in Sprint 3.

---

## 5. Backend Domain Structure

Both `goals/` and `trips/` follow the same clean layering pattern:

```
domains/{domain}/
├── models.py     ← dataclass/enum definitions
├── schemas.py    ← Pydantic request/response models
├── repository.py ← in-memory store (swap for DB in Sprint 3)
├── service.py    ← business logic + orchestrator calls
└── router.py     ← FastAPI router with HTTP handlers
```

This is the correct pattern. No issues within the domain structure itself.

However, `services/api/app/routers/traveller.py` and `services/api/app/services/traveller_service.py` do NOT follow this pattern — they exist outside `domains/` without a `models/`, `schemas/`, `repository/` split. The traveller profile should be promoted to `domains/traveller/`.

---

## 6. Frontend Page Structure

| Route | File | Type | Notes |
|-------|------|------|-------|
| `/` | `app/page.tsx` | Server | Landing/home |
| `/onboarding` | `app/onboarding/page.tsx` | Client | 4-step profile form |
| `/profile/[id]` | `app/profile/[id]/page.tsx` | Server | Profile view |
| `/goals/new` | `app/goals/new/page.tsx` | Client | Goal creation form |
| `/goals/[id]` | `app/goals/[id]/page.tsx` | Server | Goal view |
| `/trips/new` | `app/trips/new/page.tsx` | Client | Trip planning form |
| `/trips/[id]` | `app/trips/[id]/page.tsx` | Server | Trip view |
| `/demo` | `app/demo/page.tsx` | Client | Demo pipeline |

Issues:
- No `/conversation` page — the conversation engine has an API but no UI
- No navigation component — pages are only reachable by direct URL
- No error boundary or loading state pattern established
- `apps/web/src/components/` only has `onboarding/` — shared components like buttons, cards, badges are defined inline in each page

---

## 7. Duplicated Logic

| ID | Description | Files |
|----|-------------|-------|
| D-1 | `AgentRegistry` class defined twice (identical API) | `ai/registry/agent_registry.py`, `ai/orchestration/agent_registry.py` |
| D-2 | `AgentContext` dataclass defined twice | `ai/agents/base_agent.py`, `ai/shared/agent_context.py` |
| D-3 | `AgentResult` dataclass defined twice (slightly different fields) | `ai/agents/base_agent.py`, `ai/shared/agent_result.py` |
| D-4 | `ConversationSession` dataclass defined twice (different field sets) | `ai/concierge/conversation_engine.py`, `services/api/app/conversation/conversation_session.py` |
| D-5 | `ConversationMessage` defined twice | Same as D-4 |
| D-6 | `IntentClassifier` (different implementations) | `ai/concierge/intent_classifier.py`, `services/api/app/conversation/intent_classifier.py` |
| D-7 | `ResponseComposer` (different implementations) | `ai/concierge/response_composer.py`, `services/api/app/conversation/response_composer.py` |
| D-8 | Fetch error handling pattern repeated 8× in `api.ts` | `apps/web/src/lib/api.ts` |

---

## 8. Dead Code

| ID | File / Symbol | Why Dead |
|----|---------------|----------|
| DC-1 | `ai/orchestration/orchestrator.py` — `default_orchestrator` | Never imported from main.py or any active route |
| DC-2 | `ai/orchestration/agent_registry.py` — `default_registry` (Budget/Flight/Hotel/Visa/Experience) | Only used by DC-1 |
| DC-3 | `ai/agents/budget_agent.py`, `experience_agent.py`, `flight_agent.py`, `hotel_agent.py`, `visa_agent.py` | Only reachable via DC-2 |
| DC-4 | `services/api/app/conversation/conversation_engine.py` | Used only by old endpoints; superseded by `ai/concierge/` |
| DC-5 | `services/api/app/conversation/intent_classifier.py` | Same |
| DC-6 | `services/api/app/conversation/response_composer.py` | Same |
| DC-7 | `services/api/app/conversation/conversation_session.py` | Same |
| DC-8 | Old conversation endpoints: `POST /conversation/start`, `POST /conversation/{id}/message`, `GET /conversation/{id}` | Miss trip/goal integration; `POST /conversation/message` supersedes them |
| DC-9 | `ai/intelligence/reasoning/timeline_reasoner.py` | Not imported by any active path (verify) |
| DC-10 | `ai/intelligence/reasoning/season_reasoner.py` | Not imported by any active path (verify) |
| DC-11 | `ai/intelligence/reasoning/destination_reasoner.py` | Not imported by any active path (verify) |
| DC-12 | `ai/intelligence/reasoning/experience_reasoner.py` | Not imported by any active path (verify) |
| DC-13 | `ai/agents/travel_concierge_agent.py`, `travel_manager_agent.py` | Registered in `ai/registry/`, but TravelManager's active path calls them only if `decision.requires_agents` is non-empty — verify if ever populated |
| DC-14 | `infrastructure/` directory | Empty |

---

## 9. Missing Tests

**Zero test files exist anywhere in the repository.**

| Area | Test priority | What to cover |
|------|---------------|---------------|
| `ai/intelligence/traveller_dna/dna_classifier.py` | Critical | 12 trait inference rules, primary/secondary DNA selection |
| `ai/concierge/intent_classifier.py` | Critical | Intent patterns, entity extraction |
| `ai/planning/budget_estimator.py` | High | KG-backed vs fallback estimates |
| `ai/planning/risk_assessor.py` | High | Risk aggregation, tropical heuristic |
| `ai/planning/itinerary_builder.py` | High | Day count, arrival/departure templates, KG enrichment |
| `services/api/app/domains/goals/service.py` | High | Goal creation, readiness scoring |
| `services/api/app/domains/trips/service.py` | High | Status logic (READY/NEEDS_INFO/DRAFT), confidence score |
| `ai/concierge/decision_engine.py` | Medium | Decision rules for has_enough_information |
| `services/api/app/demo/demo_service.py` | Medium | Pipeline stage ordering, response shape |
| FastAPI endpoints | Medium | Integration tests: POST /trips/plan, POST /goals |

---

## 10. Documentation Drift

| Document | Status | Issue |
|----------|--------|-------|
| `docs/TASK_TRACKER.md` | **Stale** | Shows T-001–T-003 complete. Backlog (T-004–T-010) is completely wrong — these were planned before Sprint 1 tasks were re-scoped. Actual T-004–T-010 have all been completed. |
| `docs/ROADMAP.md` | Likely stale | References Sprint 0/1/2 tasks predating T-005–T-009 |
| `docs/ARCHITECTURE.md` | Partial | Describes architecture before KG, Goals, Trips, Demo were built |
| `docs/02-ai-architecture.md` | Partial | Pre-dates conversation engine, planning layer, demo |
| `docs/AGENT_REGISTRY.md` | Unknown | May describe the dead orchestration agents |
| `handoff/CLAUDE_CODE_START.md` | Stale | Written at Sprint 0 |
| `handoff/CODEX_START.md` | Stale | Written at Sprint 0 |

---

## 11. ADR Coverage

| ADR | Decision | Status |
|-----|----------|--------|
| ADR-001 | Conversation Engine architecture | Accepted |
| ADR-002 | Travel Intelligence Layer | Accepted |
| ADR-003 | Goal Planning Engine | Accepted |
| ADR-004 | Trip Planning Engine | Accepted |
| ADR-005 | End-to-End Demo Layer | Accepted |

**Gaps:**
- No ADR for: Traveller DNA inference model
- No ADR for: In-memory storage strategy and swap plan (just Sprint 1 comments in code)
- No ADR for: Frontend tech stack (Next.js 15 App Router, Tailwind)
- No ADR for: API layer domain structure (`domains/{name}/models-schema-repo-service-router`)
- No ADR for: Lazy-import pattern for AI ↔ API boundary crossing

---

## 12. Risk Areas

| ID | Risk | Severity | Likelihood |
|----|------|----------|------------|
| R-1 | No auth — API is open to any caller | High | Certain (accepted for Sprint 1) |
| R-2 | In-memory stores — all data lost on restart | High | Certain (accepted for Sprint 1) |
| R-3 | Demo creates live Goal/Trip objects — pollutes shared state | Medium | Certain |
| R-4 | Two conversation session stores — sessions from old endpoints can't continue via new endpoint | Medium | High |
| R-5 | `travel_ontology.py` is 34KB (far over 500-line limit) | Medium | Present |
| R-6 | CORS allows all methods/headers from localhost:3000 — sufficient for dev, not for prod | Medium | Present |
| R-7 | AI ↔ API dependency inversion — concierge calls domain services | Medium | Sprint 3 risk |
| R-8 | `DemoService._run_conversation()` may generate a second trip inside the engine (when `has_enough_information=True`) alongside the explicit `_run_trip()` call | Low | Present |
| R-9 | `ai/planning/itinerary_builder.py` has hardcoded `_KG_ENRICHMENTS` — will diverge from KG data as ontology evolves | Medium | Sprint 3 risk |

---

## 13. Technical Debt

See `TECHNICAL_DEBT_REGISTER.md` for the full register.

**Summary by category:**

| Category | Item count |
|----------|-----------|
| Dead code / legacy layer | 14 items |
| Duplication | 8 items |
| Missing tests | 10 areas |
| Documentation | 5 stale docs |
| Architecture | 4 structural issues |

---

## 14. Future Scalability Concerns

| ID | Concern | Trigger |
|----|---------|---------|
| S-1 | In-memory singletons won't survive multiple API instances | Adding a second API pod |
| S-2 | `knowledge_graph.py` nodes/edges are dict literals — schema drift risk | KG data expands |
| S-3 | `TripRepository` and `GoalRepository` are per-process — no cross-instance reads | Horizontal scaling |
| S-4 | `ConversationEngine` session store is per-process — same issue | Horizontal scaling |
| S-5 | `DemoService` creates real domain objects each run — in prod, every demo click fills the store | Leaving demo endpoint in place |
| S-6 | No pagination on list endpoints (`/traveller/{id}/trips`, `/traveller/{id}/goals`) | Traveller with 100+ trips |
| S-7 | `ItineraryBuilder._KG_ENRICHMENTS` static dict is a snapshot — won't reflect KG updates | Any KG change |
| S-8 | `BudgetEstimator` static fallback tables (`_DAILY_USD`, `_FLIGHT_USD`) need manual maintenance | Currency/cost changes |

---

## Cleanup Completed in This Task

- Removed stray files: `0.85`, `Any`, `dict[str` (smoke test output artefacts from T-008/T-009)

---

## Recommended Sprint 2 Priorities

See `ARCHITECTURE_RECOMMENDATIONS.md` for the full prioritised list.
