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
**Status**: Resolved (T-012)

No test files exist anywhere in the repository. Untested areas with highest risk:
1. DNA trait inference (complex scoring logic)
2. Intent classification patterns
3. Trip status determination logic (READY/NEEDS_INFO/DRAFT)
4. BudgetEstimator fallback paths
5. KG entity/relationship queries

**Resolution**: `services/api/tests/` (30 tests) and `ai/tests/` (62 tests) established with pytest — 92 tests, all passing. See ADR-007.

---

### TD-008 — TASK_TRACKER.md stale
**Severity**: Medium
**Status**: Resolved (2026-07-08)
**Introduced**: T-003

TASK_TRACKER.md was written in Sprint 0. The backlog it showed (old T-011–T-023 numbering: remove legacy conversation, remove dead orchestration, etc.) had drifted from the actual roadmap in use (T-011 Platform Layer, T-012 Testing Framework, T-013 CI/CD, T-014 Repository Refactoring, T-015–T-020 intelligence engines).

**Resolution**: Rewrote TASK_TRACKER.md to match the roadmap actually in use; old T-011–T-023 items preserved as TD-001–TD-006 (now scoped under T-014).

---

### TD-015 — `travelos/` platform layer has no test coverage
**Severity**: High
**Status**: Open
**Introduced**: T-011/T-012 (Sprint 2)

T-012 established `services/api/tests/` and `ai/tests/`, but the platform layer (`travelos/` — SDK, DI container, `ServiceRegistry`, `ConfigurationManager`, `EventBus`, `TravelLogger`, and shared types `Result`/`Identifier`/`Timestamp`/`Pagination`/`BaseRepository`/`BaseService`) shipped in the same commit with zero tests. This is the foundation every future service (T-015–T-020 intelligence engines) will build on — untested infrastructure at the base of the stack is higher-risk than untested application code.

**Resolution**: Tracked as backlog item **T-012A — Platform Layer Test Coverage** (`TASK_TRACKER.md`). Deliberately scheduled after T-014 (repository refactoring) so it doesn't delay current progress. Add `travelos/tests/` mirroring the module structure (`test_event_bus.py`, `test_service_registry.py`, `test_configuration_manager.py`, `test_result.py`, `test_container.py`, etc.).

---

### TD-016 — Frontend ESLint config references unregistered rule, blocks lint/build
**Severity**: Medium
**Status**: Open
**Introduced**: Unknown (pre-existing, found during T-013 CI setup)

`apps/web/src/lib/api.ts:2` has `// eslint-disable-next-line @typescript-eslint/no-explicit-any`, but `apps/web/.eslintrc.json` only extends `next/core-web-vitals` — the `@typescript-eslint` rule namespace isn't registered under the active config, so ESLint errors immediately: `Definition for rule '@typescript-eslint/no-explicit-any' was not found`. This fails both `npm run lint` and `npm run build` (Next.js runs lint during build) on the current `main` branch, independent of any new changes.

**Files affected**:
- `apps/web/src/lib/api.ts`
- `apps/web/.eslintrc.json`

**Resolution**: Either remove the stale disable comment (the `any` it was suppressing may need a proper type instead) or add `@typescript-eslint/eslint-plugin` + parser to `apps/web/package.json` and extend the config to register the rule. One-line-scale fix; blocks CI frontend job from being a required check until resolved — see ADR-008.

---

### TD-017 — Backend Ruff violations (pre-existing)
**Severity**: Low
**Status**: Open
**Introduced**: Sprint 0–2 (accumulated, first measured T-013)

Running `ruff check .` against the current backend/AI codebase surfaces 72 violations (mostly `E701` multiple-statements-on-one-line in `services/api/app/domains/goals/service.py`, and unused imports like `TravellersSchema` in `services/api/app/domains/trips/service.py`). `CODING_STANDARDS.md` specifies PEP 8 "enforced by Ruff in CI," but Ruff was never added to `requirements.txt` or run before now.

**Resolution**: Clean up violations as part of T-014 (repository refactoring), then flip the Ruff CI job from advisory to a required check — see ADR-008.

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
| TD-007 | Zero test coverage | T-012 | `aa5934a` |
| TD-008 | TASK_TRACKER.md stale | — | 2026-07-08 doc update |

---

## Sprint Targets

| Sprint | Items to close |
|--------|---------------|
| Sprint 2 | TD-001 (legacy conversation), TD-002/TD-003/TD-004 (dead orchestration), TD-005 (shared types), TD-017 (Ruff violations) — all under T-014; TD-015 (platform layer tests, T-012A); TD-016 (frontend ESLint config) |
| Sprint 3 | TD-006 (AI↔API boundary), TD-010 (static KG enrichment), TD-011 (traveller domain), TD-013 (pagination) |
| Sprint 4+ | TD-009 (demo isolation), TD-012 (ontology split), TD-014 (infra) |
