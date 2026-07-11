# Technical Debt Register

Tracked from T-010 audit. Updated each sprint. Items are closed when resolved and the commit is noted.

**Severity**: `critical` · `high` · `medium` · `low`
**Status**: `open` · `in-progress` · `resolved`

---

## Open Items

### TD-001 — Legacy conversation layer
**Severity**: High
**Status**: Resolved (T-014)
**Introduced**: T-006 (Sprint 1)

Three endpoints (`POST /conversation/start`, `POST /conversation/{id}/message`, `GET /conversation/{id}`) use `services/api/app/conversation/ConversationEngine` — a legacy stub that predates the full AI concierge. This engine has no trip/goal integration, no DNA inference, no session trip_id field.

The active endpoint is `POST /conversation/message` → `ai.concierge.TravelConcierge`.

**Files affected**:
- `services/api/app/conversation/conversation_engine.py`
- `services/api/app/conversation/intent_classifier.py`
- `services/api/app/conversation/response_composer.py`
- `services/api/app/conversation/conversation_session.py`
- `services/api/app/conversation/conversation_router.py` (old 3 endpoints)

**Resolution**: The active `POST /conversation/message` endpoint was moved to `services/api/app/routers/conversation.py` (matching the one-file-per-resource-group pattern used by `health.py`/`traveller.py`), still delegating to `ai.concierge.travel_concierge` exactly as before. `main.py` updated accordingly. The entire `services/api/app/conversation/` directory (the 3 legacy endpoints + `conversation_engine.py`, `intent_classifier.py`, `response_composer.py`, `conversation_session.py`) was deleted — confirmed via full-repo grep that nothing else imported from it. All 92 tests pass unchanged; `POST /conversation/message` behavior is byte-for-byte identical.

---

### TD-002 — Duplicate AgentRegistry
**Severity**: Medium
**Status**: Resolved (T-014)
**Introduced**: T-001B (Sprint 0)

`AgentRegistry` class is defined twice:
- `ai/registry/agent_registry.py`
- `ai/orchestration/agent_registry.py`

Both classes have identical APIs. The orchestration registry is only used by the dead Orchestrator.

**Correction (T-014)**: The original description above had the two registries' roles reversed. Investigation before deleting anything found: `ai/registry/agent_registry.py` registers `budget_agent`/`experience_agent`/`flight_agent`/`hotel_agent`/`visa_agent` and is imported by `ai/manager/travel_manager.py` — which **is** the active dispatcher, called from the live request path (`POST /conversation/message` → `travel_concierge` → `ai/concierge/conversation_engine.py` → `travel_manager.execute()`). `ai/orchestration/agent_registry.py` registers `TravelConciergeAgent`/`TravelManagerAgent` and is used only by `ai/orchestration/orchestrator.py`, which nothing else imports. So `ai/registry/` was active and `ai/orchestration/` was dead — the opposite of what was recorded in T-010. This matters for TD-004 below.

**Resolution**: Deleted `ai/orchestration/agent_registry.py` along with the rest of `ai/orchestration/` (see TD-003). `ai/registry/agent_registry.py` — the genuinely active registry — was left untouched.

---

### TD-003 — Dead Orchestrator module
**Severity**: Medium
**Status**: Resolved (T-014)
**Introduced**: T-001B (Sprint 0)

`ai/orchestration/orchestrator.py` contains `Orchestrator` and `default_orchestrator`. Neither is imported from `main.py` or any active route. The active agent dispatcher is `ai/manager/TravelManager`.

**Files affected**:
- `ai/orchestration/orchestrator.py`
- `ai/orchestration/agent_registry.py`
- `ai/orchestration/__init__.py`

**Resolution**: Confirmed via full-repo grep that `ai/orchestration/` had exactly one external referrer — the legacy `services/api/app/conversation/conversation_engine.py` (removed under TD-001). Once that was gone, the entire `ai/orchestration/` directory was deleted. All 92 tests pass unchanged.

---

### TD-004 — Dead specialist agents
**Severity**: Low
**Status**: Resolved (T-014) — found to be a false positive; no deletion needed
**Introduced**: T-001B (Sprint 0)

Five specialist agents were believed to be registered only in the dead orchestration registry (TD-003) and unreachable from the active pipeline:
- `ai/agents/budget_agent.py`
- `ai/agents/experience_agent.py`
- `ai/agents/flight_agent.py`
- `ai/agents/hotel_agent.py`
- `ai/agents/visa_agent.py`

**Correction (T-014)**: This was incorrect (see TD-002's correction note). These five agents are registered in `ai/registry/agent_registry.py` — the **active** registry — and are dispatched live by `ai/manager/travel_manager.py` on every `POST /conversation/message` call that needs agent work. They use `ai/shared/agent_context.py` and `ai/shared/agent_result.py` (the canonical shared types, see TD-005), not `ai/agents/base_agent.py`. They are also covered by `ai/tests/test_agent_registry.py`. The actually-dead agents were `ai/agents/travel_concierge_agent.py` (`TravelConciergeAgent`) and `ai/agents/travel_manager_agent.py` (`TravelManagerAgent`) — registered only in the dead `ai/orchestration/agent_registry.py`, referenced nowhere else in the repository.

**Resolution**: `budget_agent.py`, `experience_agent.py`, `flight_agent.py`, `hotel_agent.py`, `visa_agent.py` were **preserved unchanged** — they are live code. `travel_concierge_agent.py` and `travel_manager_agent.py` were deleted along with `ai/orchestration/`. All 92 tests pass unchanged.

---

### TD-005 — Duplicate AgentContext / AgentResult
**Severity**: Medium
**Status**: Resolved (T-014)
**Introduced**: T-001B (Sprint 0)

`AgentContext` and `AgentResult` are defined twice:
- `ai/agents/base_agent.py` — simple version (`success`, `output`, `error`)
- `ai/shared/agent_context.py` and `ai/shared/agent_result.py` — richer version with `agent_name`, `status`, `confidence`, `risks`

The active stack uses `ai/shared/`.

**Resolution**: `ai/agents/base_agent.py` (`BaseAgent`, and its simple `AgentContext`/`AgentResult`) was used only by the two dead agents removed under TD-004 (`travel_concierge_agent.py`, `travel_manager_agent.py`) — confirmed via full-repo grep before deleting. Removing all three files in the same pass leaves `ai/shared/agent_context.py` and `ai/shared/agent_result.py` as the single canonical definition, already used by every live agent. No consolidation code change was needed — the duplicate simply had no other callers once the dead agents were gone.

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

**Partial progress (T-025, 2026-07-11)**: `travelos/tests/` now exists, created for the new `travelos/intelligence_gateway/` package (110 tests — registration, selection, cache, retry, failover, rate limiting, secrets, discovery-adapter determinism) and registered in `pytest.ini`. SDK, `ServiceRegistry`, `ConfigurationManager` (beyond the five new intelligence-gateway properties, exercised only indirectly), `EventBus`, and the `shared/` types still have zero direct tests — T-012A remains open for those.

---

### TD-016 — Frontend ESLint config references unregistered rule, blocks lint/build
**Severity**: Medium
**Status**: Resolved (T-014)
**Introduced**: Unknown (pre-existing, found during T-013 CI setup)

`apps/web/src/lib/api.ts:2` has `// eslint-disable-next-line @typescript-eslint/no-explicit-any`, but `apps/web/.eslintrc.json` only extends `next/core-web-vitals` — the `@typescript-eslint` rule namespace isn't registered under the active config, so ESLint errors immediately: `Definition for rule '@typescript-eslint/no-explicit-any' was not found`. This fails both `npm run lint` and `npm run build` (Next.js runs lint during build) on the current `main` branch, independent of any new changes.

**Files affected**:
- `apps/web/src/lib/api.ts`
- `apps/web/.eslintrc.json`

**Resolution**: Confirmed `next/core-web-vitals` never enforced `@typescript-eslint/no-explicit-any` in this project (no warning appears without the disable comment) — the comment was suppressing a rule that was never active, pure dead weight. Removed the comment; left the underlying type (`Record<string, any>`) completely unchanged, so the public `DemoResponse` type is unaffected. `npm run lint` now reports zero warnings and `npm run build` succeeds. No new dependency added — resolved without touching `package.json`, honoring the "no external dependencies" constraint on T-014.

---

### TD-017 — Backend Ruff violations (pre-existing)
**Severity**: Low
**Status**: Resolved (T-014)
**Introduced**: Sprint 0–2 (accumulated, first measured T-013)

Running `ruff check .` against the current backend/AI codebase surfaces 72 violations (mostly `E701` multiple-statements-on-one-line in `services/api/app/domains/goals/service.py`, and unused imports like `TravellersSchema` in `services/api/app/domains/trips/service.py`). `CODING_STANDARDS.md` specifies PEP 8 "enforced by Ruff in CI," but Ruff was never added to `requirements.txt` or run before now.

**Resolution**: 72 → 0. `ruff check --fix` resolved 10 (unused imports, f-strings without placeholders). `ruff format`, scoped only to the 6 files with remaining `E701` violations (not a repo-wide reformat), mechanically split 59 compound one-line `if x: y` statements into standard multi-line form — verified as pure whitespace/structural changes (same conditions, same right-hand sides). The last 3 (2 ambiguous single-letter loop variables, 1 unused variable assignment with no side effects) were fixed by hand after confirming each was safe. All 92 tests pass unchanged throughout. The `backend-lint` CI job (ADR-008) can now be flipped from advisory to required.

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

### TD-018 — Legacy specialist-agent orchestration still live for four intents
**Severity**: Medium
**Status**: Open
**Introduced**: T-001B (Sprint 0); misdiagnosed as retirable in ADR-017 (T-021)

`ai/manager/TravelManager`, `ai/registry/AgentRegistry`, and the five
placeholder agents (`ai/agents/{flight,hotel,budget,experience,visa}_agent.py`)
were expected, per ADR-017 and the original `docs/TASK_TRACKER.md` T-023
entry, to be dormant rollback code once Trip Brain (T-022) shipped, ready
for wholesale deletion. T-023's investigation found this was wrong:
`ConversationEngine.process()` still dispatches `MODIFY_TRIP`,
`DESTINATION_QUESTION`, `TRAVEL_ADVICE`, and `BUDGET_ADVICE` through
`travel_manager.execute()` — Trip Brain only ever superseded `PLAN_TRIP`.
These four intents return static "pending_live_data" stub output from
Sprint-1 placeholder agents, the same limitation `PLAN_TRIP` had before
T-022.

**Files affected**:
- `ai/manager/travel_manager.py`
- `ai/registry/agent_registry.py`
- `ai/agents/{flight,hotel,budget,experience,visa}_agent.py`
- `ai/concierge/decision_engine.py` (`_AGENT_MAP` entries for these four intents)

**Resolution**: Tracked as backlog item **T-032 — Migrate remaining
intents off legacy TravelManager** (`docs/TASK_TRACKER.md`). Once
`MODIFY_TRIP`/`DESTINATION_QUESTION`/`TRAVEL_ADVICE`/`BUDGET_ADVICE` have a
real Discovery-module or Trip Brain equivalent, `ai/manager/`,
`ai/registry/`, and the five placeholder agents become genuinely unused and
can be deleted — the deletion T-023 was originally asked to perform. See
`docs/ADR/ADR-018-legacy-orchestration-retirement.md` for the full
investigation.

---

### TD-019 — Destinations, Budget, Visa not yet wired to the Intelligence Gateway
**Severity**: Low
**Status**: Open
**Introduced**: T-025

T-025 built the Intelligence Gateway and wired the three minimum-required
providers (Flight, Accommodation, Weather). Destination, Budget, and Visa
Intelligence still construct their `Mock*Provider` directly, bypassing
the gateway's caching/retry/failover/observability entirely — not a
technical blocker, just deferred to keep T-025's diff reviewable (see
`docs/INTELLIGENCE_GATEWAY.md`'s Deferred Integrations section and
ADR-020).

**Files affected**: `ai/discovery/destinations/destination_intelligence.py`,
`ai/discovery/budget/budget_intelligence.py`, `ai/discovery/visa/visa_intelligence.py`.

**Resolution**: Extend `travelos/intelligence_gateway/discovery_adapters.py`
with three more gateway-contract wrappers and drop-in `Gateway*Provider`
adapters, following the exact pattern already proven for Flight/
Accommodation/Weather. No new gateway capability is needed — `Capability.DESTINATIONS`/
`BUDGET`/`VISA` already exist.

---

### TD-020 — Maps, Currency, Events capabilities have no provider
**Severity**: Low
**Status**: Open
**Introduced**: T-025

`Capability.MAPS`/`CURRENCY`/`EVENTS` exist in
`travelos/intelligence_gateway/provider_status.py` (per T-025's explicit
capability list) but no Discovery module or mock provider exists yet for
any of them — there is nothing to register. Not a bug; the registry and
selector are simply ready the moment a real module for one of these
domains is built.

**Resolution**: No action needed until a Maps/Currency/Events Discovery
module is scoped as its own task.

---

## Resolved Items

| ID | Description | Resolved in | Commit |
|----|-------------|-------------|--------|
| — | Stray files `0.85`, `Any`, `dict[str` at repo root | T-010 | (this task) |
| TD-007 | Zero test coverage | T-012 | `aa5934a` |
| TD-008 | TASK_TRACKER.md stale | — | 2026-07-08 doc update |
| TD-001 | Legacy conversation layer | T-014 | (this task) |
| TD-002 | Duplicate AgentRegistry | T-014 | (this task) |
| TD-003 | Dead Orchestrator module | T-014 | (this task) |
| TD-004 | Dead specialist agents (false positive — see correction note) | T-014 | (this task) |
| TD-005 | Duplicate AgentContext/AgentResult | T-014 | (this task) |
| TD-016 | Frontend ESLint config | T-014 | (this task) |
| TD-017 | Backend Ruff violations (72 → 0) | T-014 | (this task) |

---

## Sprint Targets

| Sprint | Items to close |
|--------|---------------|
| Sprint 2 | ~~TD-001, TD-002, TD-003, TD-004, TD-005, TD-016, TD-017~~ — all closed in T-014; TD-015 (platform layer tests) partially addressed in T-025, remains open for SDK/EventBus/shared types, tracked as T-012A; TD-018 (legacy orchestration retirement blocked on T-032) opened in T-023; TD-019/TD-020 (deferred Intelligence Gateway integrations) opened in T-025 |
| Sprint 3 | TD-006 (AI↔API boundary), TD-010 (static KG enrichment), TD-011 (traveller domain), TD-013 (pagination), TD-019 (wire remaining Discovery providers to the gateway) |
| Sprint 4+ | TD-009 (demo isolation), TD-012 (ontology split), TD-014 (infra), TD-018 (legacy orchestration, pending T-032), TD-020 (Maps/Currency/Events providers, pending new Discovery modules) |
