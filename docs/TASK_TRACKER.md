# Task Tracker

Live register of all engineering tasks. Update status in the same PR that completes the work.

**Statuses:** `planned` · `in-progress` · `complete` · `blocked` · `cancelled`

**Priorities:** `critical` · `high` · `medium` · `low`

---

## Active Tasks

| Task ID | Title | Status | Priority | Owner | Date | Files | Notes |
|---------|-------|--------|----------|-------|------|-------|-------|
| T-001 | Bootstrap project foundation | `complete` | critical | Claude Code | 2026-07-07 | `apps/web/`, `services/api/`, `ai/`, `docker-compose.yml`, `README.md`, `.gitignore`, `.env.example` | Sprint 0 scaffold. Next.js 15 + FastAPI + AI directory structure |
| T-001B | Complete Sprint 0 scaffold | `complete` | critical | Claude Code | 2026-07-07 | `ai/agents/base_agent.py`, `ai/agents/travel_manager_agent.py`, `ai/orchestration/orchestrator.py`, `ai/memory/traveller_profile_schema.md`, `docs/00-product-constitution.md`, `docs/01-platform-architecture.md`, `docs/02-ai-architecture.md`, `handoff/CLAUDE_CODE_START.md`, `handoff/CODEX_START.md`, `scripts/local-start.md` | AI agent layer, orchestrator, memory schema, architecture docs, handoff docs |
| T-002 | Initial commit and remote push | `complete` | high | Peter | 2026-07-07 | — | `git init` → `git add .` → `git commit` → `git push origin main`. Repo live at github.com/Diajem/tralvana-ai |
| T-003 | Create Architecture Authority | `complete` | high | Claude Code | 2026-07-07 | `docs/ARCHITECTURE.md`, `docs/ENGINEERING_PRINCIPLES.md`, `docs/CODING_STANDARDS.md`, `docs/TASK_TRACKER.md`, `docs/ROADMAP.md`, `docs/PRODUCT_VISION.md` | Governing documentation for TravelOS. AI hierarchy, principles, standards, roadmap, vision |

---

## Backlog

| Task ID | Title | Status | Priority | Owner | Date | Notes |
|---------|-------|--------|----------|-------|------|-------|
| T-004 | Wire orchestrator into FastAPI | `planned` | high | — | — | `POST /agents/run` endpoint. Calls `Orchestrator.run()` from a FastAPI router |
| T-005 | Traveller profile API | `planned` | high | — | — | `GET /profile/{traveller_id}`. In-memory store for Sprint 1 |
| T-006 | Unit tests — AI agents | `planned` | high | — | — | `ai/tests/test_base_agent.py`, `ai/tests/test_travel_manager_agent.py` |
| T-007 | LLM provider adapter | `planned` | medium | — | — | `ai/llm/` — wraps Anthropic SDK. Model-agnostic interface |
| T-008 | Traveller profile persistence | `planned` | medium | — | — | SQLite store. Implements `traveller_profile_schema.md` |
| T-009 | Auth layer | `planned` | medium | — | — | Clerk or NextAuth.js. Protect API routes |
| T-010 | CI pipeline | `planned` | medium | — | — | GitHub Actions: lint, type-check, tests on every PR |

---

## Completed

See rows with `complete` status in Active Tasks above.

---

## Notes

- Task IDs are sequential and never reused.
- All task IDs referenced in PR titles: `[T-004] Add /agents/run endpoint`.
- Blocked tasks include the blocker in Notes.
