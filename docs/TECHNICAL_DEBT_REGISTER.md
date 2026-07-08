# Technical Debt Register

Tracked from T-010 audit. Updated each sprint. Items are closed when resolved and the commit is noted.

**Severity**: `critical` · `high` · `medium` · `low`
**Status**: `open` · `in-progress` · `resolved`

---

## Open Items

### TD-001 — Legacy conversation layer
**Severity**: High
**Status**: Open
**Introduced**: T-006 (Sprint 1)

Three endpoints (`POST /conversation/start`, `POST /conversation/{id}/message`, `GET /conversation/{id}`) use `services/api/app/conversation/ConversationEngine` — a legacy stub that predates the full AI concierge. This engine has no trip/goal integration, no DNA inference, no session trip_id field.

The active endpoint is `POST /conversation/message` → `ai.concierge.TravelConcierge`.

**Files affected**:
- `services/api/app/conversation/conversation_engine.py`
- `services/api/app/conversation/intent_classifier.py`
- `services/api/app/conversation/response_composer.py`
- `services/api/app/conversation/conversation_session.py`
- `services/api/app/conversation/conversation_router.py` (old 3 endpoints)

**Resolution**: Deprecate and remove old endpoints in Sprint 2. Move session store to `ai/concierge/`. Remove the `services/api/app/conversation/` module (all classes superseded by `ai/concierge/`).

---

### TD-002 — Duplicate AgentRegistry
**Severity**: Medium
**Status**: Open
**Introduced**: T-001B (Sprint 0)

`AgentRegistry` class is defined twice:
- `ai/registry/agent_registry.py` — registers TravelConcierge + TravelManager (active)
- `ai/orchestration/agent_registry.py` — registers Budget/Flight/Hotel/Visa/Experience (dead)

Both classes have identical APIs. The orchestration registry is only used by the dead Orchestrator.

**Resolution**: Delete `ai/orchestration/agent_registry.py` and `ai/orchestration/orchestrator.py` when the orchestration module is removed (see TD-003).

---

### TD-003 — Dead Orchestrator module
**Severity**: Medium
**Status**: Open
**Introduced**: T-001B (Sprint 0)

`ai/orchestration/orchestrator.py` contains `Orchestrator` and `default_orchestrator`. Neither is imported from `main.py` or any active route. The active agent dispatcher is `ai/manager/TravelManager`.

**Files affected**:
- `ai/orchestration/orchestrator.py`
- `ai/orchestration/agent_registry.py`
- `ai/orchestration/__init__.py`

**Resolution**: Remove entire `ai/orchestration/` directory in Sprint 2.

---

### TD-004 — Dead specialist agents
**Severity**: Low
**Status**: Open
**Introduced**: T-001B (Sprint 0)

Five specialist agents are registered in the dead orchestration registry (TD-003) and are never reachable from the active pipeline:
- `ai/agents/budget_agent.py`
- `ai/agents/experience_agent.py`
- `ai/agents/flight_agent.py`
- `ai/agents/hotel_agent.py`
- `ai/agents/visa_agent.py`

**Resolution**: When the orchestration module is removed, assess whether any of these agents should be reimplemented and registered in the active `ai/registry/` path. Delete those that aren't needed.

---

### TD-005 — Duplicate AgentContext / AgentResult
**Severity**: Medium
**Status**: Open
**Introduced**: T-001B (Sprint 0)

`AgentContext` and `AgentResult` are defined twice:
- `ai/agents/base_agent.py` — simple version (`success`, `output`, `error`)
- `ai/shared/agent_context.py` and `ai/shared/agent_result.py` — richer version with `agent_name`, `status`, `confidence`, `risks`

The active stack uses `ai/shared/`. `ai/agents/base_agent.py` versions are used only by the dead agents (TD-004).

**Resolution**: Consolidate to `ai/shared/`. Update `BaseAgent` to import from there. Remove duplicates from `base_agent.py`.

---

### TD-006 — AI ↔ API dependency inversion
**Severity**: Medium
**Status**: Open
**Introduced**: T-006/T-007/T-008 (Sprint 1)

`ai/concierge/conversation_engine.py` imports from `app.domains.goals.service` and `app.domains.trips.service` (via lazy imports inside methods). This crosses the intended AI → API dependency direction.

In Sprint 1 this works because all code runs in one process. In Sprint 3 (separate AI service), these imports will fail.

**Resolution**: Define a `PlanningPort` interface that the concierge calls, with the domain service providing the implementation. The port lives in `ai/`, the adapter in `services/api/app/`.

---

### TD-007 — Zero test coverage
**Severity**: Critical
**Status**: Open
**Introduced**: Sprint 1 (deferred)

No test files exist anywhere in the repository. Untested areas with highest risk:
1. DNA trait inference (complex scoring logic)
2. Intent classification patterns
3. Trip status determination logic (READY/NEEDS_INFO/DRAFT)
4. BudgetEstimator fallback paths
5. KG entity/relationship queries

**Resolution**: Sprint 2 — establish `services/api/tests/` and `ai/tests/` with pytest. Minimum: unit tests for DNA classifier, intent classifier, budget estimator, and trip status logic.

---

### TD-008 — TASK_TRACKER.md stale
**Severity**: Medium
**Status**: Open (resolved partially in this task)
**Introduced**: T-003

TASK_TRACKER.md was written in Sprint 0. The backlog it shows (old T-004 through T-010) does not reflect actual Sprint 1 work. T-004–T-009 have all been completed; the tracker was never updated.

**Resolution**: Rewrite TASK_TRACKER.md with correct completed/backlog items (done in this task).

---

### TD-009 — DemoService writes to shared data stores
**Severity**: Low
**Status**: Open
**Introduced**: T-009

`DemoService.run()` calls `goal_service.create()` and `trip_planning_service.plan()`, writing real objects to the shared in-memory stores. Each demo button click adds a Goal + Trip Plan to the live application state.

**Resolution**: Add a `demo=True` flag to Goal/Trip creation to mark demo objects, or use isolated in-memory stores for the demo pipeline. Alternatively, clear demo objects at the end of each run.

---

### TD-010 — Static `_KG_ENRICHMENTS` in ItineraryBuilder
**Severity**: Medium
**Status**: Open
**Introduced**: T-008

`ai/planning/itinerary_builder.py` has a hardcoded `_KG_ENRICHMENTS` dict with static venue lists for 10 cities. This is a snapshot of the KG at build time. When the KG is updated (new restaurants, attractions) the itinerary builder won't reflect changes.

**Resolution**: Sprint 3 — replace `_KG_ENRICHMENTS` with a live query to `KnowledgeService.get_connected_entities()` at itinerary build time.

---

### TD-011 — Traveller domain not in `domains/`
**Severity**: Low
**Status**: Open
**Introduced**: T-001B

The traveller profile routes live in `services/api/app/routers/traveller.py` and `services/api/app/services/traveller_service.py`, outside the `domains/` structure used by Goals and Trips. No `models/`, `schemas/`, `repository/`, `service/`, `router/` split.

**Resolution**: Promote to `services/api/app/domains/traveller/` in Sprint 2 to match the domain pattern.

---

### TD-012 — `travel_ontology.py` exceeds 500-line limit
**Severity**: Low
**Status**: Open
**Introduced**: T-005 (TIL sprint)

`ai/intelligence/ontology/travel_ontology.py` is 34KB — the largest file in the repo, well over the 500-line CLAUDE.md limit. It is a large static data file (ontology definitions).

**Resolution**: Split into smaller domain-specific ontology modules (e.g. `transport_ontology.py`, `accommodation_ontology.py`, `destination_ontology.py`).

---

### TD-013 — No pagination on list endpoints
**Severity**: Low
**Status**: Open
**Introduced**: T-007/T-008

`GET /traveller/{id}/goals` and `GET /traveller/{id}/trips` return all results with no limit or cursor. In-memory stores make this safe now but it becomes a risk when stores are replaced by databases.

**Resolution**: Add `limit` + `offset` query parameters when domains move to PostgreSQL in Sprint 3.

---

### TD-014 — Empty `infrastructure/` directory
**Severity**: Low
**Status**: Open
**Introduced**: T-001

`infrastructure/` was created as a placeholder for Terraform/Docker Compose IaC. Currently empty.

**Resolution**: Either populate with IaC files or remove and add back when infra work begins.

---

## Resolved Items

| ID | Description | Resolved in | Commit |
|----|-------------|-------------|--------|
| — | Stray files `0.85`, `Any`, `dict[str` at repo root | T-010 | (this task) |

---

## Sprint Targets

| Sprint | Items to close |
|--------|---------------|
| Sprint 2 | TD-001 (legacy conversation), TD-002/TD-003/TD-004 (dead orchestration), TD-007 (tests), TD-008 (tracker) |
| Sprint 3 | TD-005 (shared types), TD-006 (AI↔API boundary), TD-010 (static KG enrichment), TD-011 (traveller domain), TD-013 (pagination) |
| Sprint 4+ | TD-009 (demo isolation), TD-012 (ontology split), TD-014 (infra) |
