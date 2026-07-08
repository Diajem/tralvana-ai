# Architecture Recommendations

From T-010 audit. Prioritised actions for Sprint 2 and beyond.

---

## Priority 1 — Immediate (Sprint 2)

### REC-001: Remove the legacy conversation layer

**What**: Delete `services/api/app/conversation/` and the 3 old conversation endpoints.

**Why**: Two conversation stacks in one router create two separate session stores. Sessions started via old endpoints can't continue via the new endpoint. The legacy engine has no trip/goal integration and will mislead anyone testing the API.

**How**:
1. Remove `POST /conversation/start`, `POST /conversation/{id}/message`, `GET /conversation/{id}` from `conversation_router.py`
2. Delete `services/api/app/conversation/conversation_engine.py`, `intent_classifier.py`, `response_composer.py`, `conversation_session.py`
3. The `ConversationSession`, `ConversationStore`, and session management should live in `ai/concierge/` (already there) or be promoted to `services/api/app/domains/conversation/`

**Risk**: Low — the new endpoint already covers all functionality.

---

### REC-002: Remove the dead orchestration module

**What**: Delete `ai/orchestration/` entirely.

**Why**: `Orchestrator` and its `AgentRegistry` (Budget/Flight/Hotel/Visa/Experience) are never imported from any active path. They duplicate the `AgentRegistry` in `ai/registry/` and the `TravelManager` in `ai/manager/`.

**How**:
1. Delete `ai/orchestration/orchestrator.py`, `ai/orchestration/agent_registry.py`, `ai/orchestration/__init__.py`
2. Assess the 5 dead specialist agents (`budget_agent`, `experience_agent`, `flight_agent`, `hotel_agent`, `visa_agent`) — either re-register them in `ai/registry/` with a plan to wire them, or delete them

**Risk**: None — nothing in the active path depends on these.

---

### REC-003: Establish test infrastructure

**What**: Create `services/api/tests/` and `ai/tests/` with pytest. Write minimum viable test suite.

**Why**: Zero test coverage on a codebase with complex scoring logic (DNA inference, trip confidence, budget estimation) is the highest risk in the repo.

**Minimum test targets** (in priority order):
1. `ai/intelligence/traveller_dna/dna_classifier.py` — 12 trait rules, primary/secondary DNA selection
2. `ai/concierge/intent_classifier.py` — intent patterns, entity extraction edge cases
3. `ai/planning/budget_estimator.py` — KG path vs static fallback
4. `services/api/app/domains/trips/service.py` — READY/NEEDS_INFORMATION/DRAFT status logic
5. `ai/planning/risk_assessor.py` — risk aggregation, tropical heuristic

**Add to `requirements.txt`**: `pytest`, `pytest-asyncio`, `httpx` (for FastAPI test client).

---

### REC-004: Fix TASK_TRACKER.md

**What**: Rewrite with accurate task history and current backlog.

**Why**: The existing tracker still shows Sprint 0's planned tasks in the backlog — T-004 through T-009 from the original plan that were never done and were replaced by the actual Sprint 1 tasks (which are also named T-004 through T-009 but do entirely different things). Anyone reading the tracker will be confused.

**Done in this task** — see updated TASK_TRACKER.md.

---

## Priority 2 — Sprint 2 (alongside feature work)

### REC-005: Consolidate AgentContext and AgentResult

**What**: Move canonical definitions to `ai/shared/`. Remove duplicates from `ai/agents/base_agent.py`.

**Why**: `AgentContext` and `AgentResult` exist in two places with slightly different schemas. The active stack uses `ai/shared/`. The `base_agent.py` versions are only used by the dead agents.

**How**: Update `BaseAgent.__init__()` and `_ok()`/`_err()` to use `ai.shared.agent_context.AgentContext` and `ai.shared.agent_result.AgentResult`. Remove the dataclasses from `base_agent.py`.

---

### REC-006: Promote Traveller to a domain

**What**: Move traveller to `services/api/app/domains/traveller/` with the standard `models/schemas/repository/service/router` split.

**Why**: Goals and Trips both use the clean domain pattern. Traveller is the odd one out — it has `routers/traveller.py` and `services/traveller_service.py` at the top level without a proper models/schemas/repository split. This also means Traveller has no in-memory repository (it's a singleton dict in the service).

---

### REC-007: Add a navigation component to the frontend

**What**: Create `apps/web/src/components/Navigation.tsx` and add it to `layout.tsx`.

**Why**: All pages are reachable only by direct URL. There is no nav bar, sidebar, or link structure. The home page (`/`) doesn't link to any feature page.

---

## Priority 3 — Sprint 3 (database/infra phase)

### REC-008: Fix AI ↔ API dependency direction

**What**: Introduce a `PlanningPort` interface in `ai/` so the conversation engine doesn't import from `app.domains`.

**Why**: Currently `ai/concierge/conversation_engine.py` imports from `app.domains.goals.service` and `app.domains.trips.service`. The correct dependency direction is API → AI. In a multi-service deployment this creates a circular import.

**Pattern**:
```python
# ai/ports/planning_port.py  (interface, no deps)
class PlanningPort(Protocol):
    def create_trip(self, ...): ...

# services/api/app/adapters/planning_adapter.py  (implements the port)
class PlanningAdapter:
    def create_trip(self, ...):
        from app.domains.trips.service import trip_planning_service
        return trip_planning_service.plan_from_conversation(...)

# Inject PlanningAdapter into ConversationEngine at startup
```

---

### REC-009: Replace static `_KG_ENRICHMENTS` with live KG queries

**What**: Refactor `ItineraryBuilder.build()` to call `KnowledgeService.get_connected_entities()` rather than reading from the hardcoded `_KG_ENRICHMENTS` dict.

**Why**: The static dict is a frozen snapshot. When the KG grows (new venues, updated data), itineraries don't reflect the change. This is already how `BudgetEstimator` works — it queries the `BudgetReasoner` which queries the KG.

**Risk**: Slight performance impact (in-memory graph traversal vs dict lookup) — acceptable given the KG is fully in-memory.

---

### REC-010: Isolate demo data from live stores

**What**: Give `DemoService` isolated in-memory stores so demo runs don't pollute live Goal/Trip data.

**Options**:
1. Mark demo objects with a `is_demo: bool` field and filter them from list endpoints
2. Pass a `DemoGoalRepository` and `DemoTripRepository` to the demo service
3. Accept and acknowledge as a known limitation while the store is in-memory (remove in Sprint 3 when DB adds proper isolation)

**Recommendation**: Option 1 is cheapest; add `is_demo` field to both models now so Sprint 3 migrations can filter correctly.

---

## Summary Table

| ID | Recommendation | Sprint | Effort |
|----|---------------|--------|--------|
| REC-001 | Remove legacy conversation layer | 2 | 1 day |
| REC-002 | Remove dead orchestration module | 2 | 0.5 day |
| REC-003 | Establish test infrastructure | 2 | 3 days |
| REC-004 | Fix TASK_TRACKER.md | 2 | Done |
| REC-005 | Consolidate AgentContext/AgentResult | 2 | 0.5 day |
| REC-006 | Promote Traveller to domain | 2 | 1 day |
| REC-007 | Add frontend navigation | 2 | 0.5 day |
| REC-008 | Fix AI↔API dependency direction | 3 | 2 days |
| REC-009 | Replace static KG enrichments | 3 | 1 day |
| REC-010 | Isolate demo data | 3 | 0.5 day |
