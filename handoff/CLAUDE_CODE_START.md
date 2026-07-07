# Claude Code — Handoff Document

## Project: Tralvana AI

AI-native travel operating system. Sprint 0 scaffold is complete.

## What Has Been Built

| Area | Status |
|------|--------|
| `apps/web` (Next.js 15 + Tailwind) | Scaffold complete |
| `services/api` (FastAPI) | Scaffold complete |
| `ai/agents/base_agent.py` | BaseAgent ABC |
| `ai/agents/travel_manager_agent.py` | First concrete agent |
| `ai/orchestration/orchestrator.py` | Agent routing layer |
| `ai/memory/traveller_profile_schema.md` | Data contract (no DB yet) |
| `docs/` | Product constitution + architecture docs |

## Rules

- No paid APIs without explicit instruction.
- No database implementation until Sprint 1.
- No commits unless explicitly asked.
- Keep files under 500 lines.
- Read a file before editing it.

## Where to Start for Sprint 1

1. Wire the orchestrator into FastAPI — add a `POST /agents/run` endpoint in `services/api/app/routers/`.
2. Add a traveller profile endpoint — `GET /profile/{traveller_id}`.
3. Add unit tests for `TravelManagerAgent` in `ai/tests/`.

## Key Files

| File | Purpose |
|------|---------|
| `ai/orchestration/orchestrator.py` | Entry point for all agent calls |
| `ai/agents/base_agent.py` | Base class — extend this for new agents |
| `services/api/app/main.py` | FastAPI app — add new routers here |
| `docs/01-platform-architecture.md` | System diagram |
| `docs/02-ai-architecture.md` | Agent design details |

## Environment

```bash
cp .env.example .env
# Fill in ANTHROPIC_API_KEY when LLM calls are added (Sprint 1+)
```
