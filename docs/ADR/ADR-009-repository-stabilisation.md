# ADR-009: Repository Stabilisation & Engineering Refactor

**Date**: 2026-07-08
**Status**: Accepted
**Sprint**: 2 (T-014)

## Context

The T-010 audit (Sprint 2) logged seven engineering debt items — TD-001 through TD-005, plus TD-016 and TD-017 added during T-013 CI setup — all describing dead code, duplicate types, and tooling gaps accumulated since Sprint 0. Before starting live travel intelligence integrations (T-015+), the repository needed to be stabilised: dead code removed, duplication resolved, and the two CI jobs left advisory in ADR-008 (Ruff, frontend lint/build) made to actually pass.

This was scoped as a pure engineering task — no new features, no API changes, no behaviour changes, no new dependencies, no database changes.

## A correction, found before deleting anything

Investigating TD-002 and TD-004 before touching any file revealed the original T-010 audit had the two `AgentRegistry` implementations **backwards**:

| | T-010 audit claimed | Actually found |
|---|---|---|
| `ai/registry/agent_registry.py` | Registers `TravelConcierge` + `TravelManager`, active | Registers `budget_agent`/`experience_agent`/`flight_agent`/`hotel_agent`/`visa_agent`, and **is** active |
| `ai/orchestration/agent_registry.py` | Registers Budget/Flight/Hotel/Visa/Experience, dead | Registers `TravelConciergeAgent`/`TravelManagerAgent`, and **is** dead |

Tracing the live request path confirms it: `POST /conversation/message` → `ai.concierge.travel_concierge` → `ai/concierge/conversation_engine.py` → `ai/manager/travel_manager.py` (`TravelManager.execute`) → `ai/registry/agent_registry.py` (`default_registry`) → the five specialist agents. Those five agents were never dead — TD-004 was a false positive. The code that was actually unreachable was `ai/orchestration/` in its entirety, plus `ai/agents/travel_concierge_agent.py` and `ai/agents/travel_manager_agent.py` (registered only inside the dead `ai/orchestration/agent_registry.py`), plus `ai/agents/base_agent.py` (used only by those last two).

This was verified by full-repository grep for every symbol before deleting anything, not by re-reading the old audit's conclusions. Full detail is in `TECHNICAL_DEBT_REGISTER.md` under each item's "Correction (T-014)" note.

## Decision

**TD-001 — Legacy conversation layer.** The live `POST /conversation/message` endpoint and the three legacy stub endpoints (`/conversation/start`, `/conversation/{id}/message`, `/conversation/{id}`) were defined in the same file, `services/api/app/conversation/conversation_router.py`. Moved the live endpoint to `services/api/app/routers/conversation.py` (matching the existing one-file-per-resource-group pattern in `routers/health.py` and `routers/traveller.py`), updated `main.py`'s import, then deleted the rest of `services/api/app/conversation/` (`conversation_engine.py`, `intent_classifier.py`, `response_composer.py`, `conversation_session.py`) — all superseded by `ai/concierge/`, confirmed via grep to have no other callers.

**TD-002/TD-003 — Duplicate registry + dead Orchestrator.** Deleted `ai/orchestration/` (`orchestrator.py`, `agent_registry.py`, `__init__.py`) in full. Its only external referrer was the legacy `conversation_engine.py` removed under TD-001. `ai/registry/agent_registry.py` — the genuinely active registry — was left untouched.

**TD-004 — "Dead" specialist agents.** No deletion. `budget_agent.py`, `experience_agent.py`, `flight_agent.py`, `hotel_agent.py`, `visa_agent.py` are live and were preserved exactly as they were. Instead, `ai/agents/travel_concierge_agent.py` and `ai/agents/travel_manager_agent.py` — the two agents actually reachable only through the dead orchestration registry — were deleted.

**TD-005 — Duplicate `AgentContext`/`AgentResult`.** `ai/agents/base_agent.py` was used only by the two agents deleted under TD-004's correction. Deleting all three in the same pass leaves `ai/shared/agent_context.py` and `ai/shared/agent_result.py` as the single definition — already what every live agent uses. No code migration needed; the duplicate simply lost its only callers.

**TD-016 — Frontend ESLint config.** `apps/web/src/lib/api.ts` had `// eslint-disable-next-line @typescript-eslint/no-explicit-any` guarding `export type DemoResponse = Record<string, any>`, but `.eslintrc.json` only extends `next/core-web-vitals`, which doesn't register that rule. Confirmed by removing the comment and re-running lint: zero warnings, meaning the rule was never actually enforced — the comment was dead weight. Removed it; left `Record<string, any>` completely unchanged. No dependency added, per the "no external dependencies" constraint.

**TD-017 — Ruff violations, 72 → 0.** `ruff check --fix` resolved 10 (unused imports, f-strings without placeholders). `ruff format`, run only against the 6 files that still had violations (not a repo-wide reformat) mechanically split 59 `E701` compound one-line `if x: y` statements into standard multi-line form — verified against the diff as pure whitespace restructuring with identical conditions and right-hand sides. The final 3 (2 ambiguous single-letter loop variables `l` → `lang`, 1 assigned-but-unused variable with no side effects) were fixed by hand after individually confirming each was safe.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Trust the T-010 audit's TD-002/TD-004 description and delete the 5 specialist agents | Would have deleted live, tested, reachable code and broken `POST /conversation/message` for any request needing agent dispatch — caught only by tracing actual imports before deleting anything |
| Repo-wide `ruff format` | Touches every file in the repo, including ones with zero violations — far larger diff than necessary for a task scoped to "reduce Ruff violations." Scoped formatting to only the 6 violating files instead |
| Add `@typescript-eslint/eslint-plugin` to fix TD-016 | Violates the explicit "no external dependencies" constraint; unnecessary once testing showed the rule was never enforced in the first place |
| Leave TD-004's specialist agents "reassessed" per the original resolution note | The agents were never in question once traced — no reimplementation decision was needed |
| Rewrite `ARCHITECTURE.md`'s folder diagram (still shows `ai/orchestration/orchestrator.py`) | Out of scope — "preserve all documentation" was an explicit constraint; flagged as a known limitation below instead of edited |

## Consequences

- 13 files deleted (`services/api/app/conversation/` × 6, `ai/orchestration/` × 3, `ai/agents/base_agent.py`, `ai/agents/travel_concierge_agent.py`, `ai/agents/travel_manager_agent.py`, minus the new `services/api/app/routers/conversation.py`), net negative line count.
- Zero API changes: `POST /conversation/message` has the identical request/response schema and behaviour, just served from a new file.
- Zero behaviour changes anywhere else: every specialist agent, the active registry, and the active manager are byte-for-byte what they were before, confirmed by 92/92 tests passing before and after every deletion step.
- `ruff check .` is clean (0 violations, down from 72). The `backend-lint` CI job (ADR-008) can now be flipped from advisory to a required check.
- `npm run lint` and `npm run build` both succeed cleanly. The `frontend` CI job (ADR-008) can now be flipped from advisory to a required check.
- `TECHNICAL_DEBT_REGISTER.md` retains the original (incorrect) TD-002/TD-004 descriptions with an added "Correction (T-014)" note explaining what was actually found, rather than silently rewriting history — the record of the mistake is itself useful context for future audits.

## Known Limitations

- `docs/ARCHITECTURE.md`'s system diagram and folder-responsibilities table still show `ai/orchestration/orchestrator.py` as part of the current structure. Per the "preserve all documentation" constraint on this task, it was not edited. It should be updated in a documentation-only follow-up.
- `docs/CODING_STANDARDS.md`'s `ai/` folder layout example still lists `orchestration/` as a subfolder. Same limitation — flagged, not edited.
- TD-006 (AI↔API dependency inversion), TD-009 through TD-014 remain open — out of scope for this task, tracked for Sprint 3+.

## Sprint 3+ Evolution

| Item | Next step |
|------|-----------|
| `ARCHITECTURE.md` / `CODING_STANDARDS.md` drift | Documentation-only follow-up to remove references to deleted `ai/orchestration/` |
| `backend-lint` / `frontend` CI jobs | Flip from advisory (`continue-on-error: true`) to required in `.github/workflows/ci.yml`, now that both pass cleanly |
| T-012A (Platform Layer Test Coverage) | Now unblocked — was deliberately scheduled to start after T-014 |
