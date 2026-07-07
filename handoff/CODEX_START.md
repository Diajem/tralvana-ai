# Codex — Handoff Document

## Project: Tralvana AI

AI-native travel OS. You are operating on the Sprint 0 scaffold.

## Codebase Map

```
tralvana-ai/
├── apps/web/          Next.js 15 frontend (TypeScript, Tailwind, App Router)
├── services/api/      FastAPI backend (Python 3.12)
├── ai/
│   ├── agents/        BaseAgent + TravelManagerAgent
│   ├── orchestration/ Orchestrator (routes requests to agents)
│   └── memory/        Traveller profile schema (no DB yet)
└── docs/              Architecture and product docs
```

## Constraints

- Python 3.12+ syntax (use `str | None` not `Optional[str]`)
- No synchronous blocking calls in async functions
- No LLM API calls in Sprint 0 — agents return stub data
- No database writes — memory layer is schema-only until Sprint 1
- All secrets via environment variables (`.env.example` has the keys)

## Running Locally

Frontend:
```bash
cd apps/web && npm install && npm run dev
```

Backend:
```bash
cd services/api
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Adding a New Agent

1. Create `ai/agents/<name>_agent.py`
2. Inherit `BaseAgent`, implement `async def run(self, input_data)`
3. Register it in `ai/orchestration/orchestrator.py` → `AGENT_REGISTRY`
4. Add a unit test in `ai/tests/`

## Key Interfaces

```python
# Input to any agent
input_data: dict[str, Any]

# Output from any agent
AgentResult(success=True, output={...})
AgentResult(success=False, output=None, error="reason")
```
