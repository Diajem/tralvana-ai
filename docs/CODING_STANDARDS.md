# Coding Standards

Standards applied across all TravelOS code. Consistency enables safe, fast iteration.

---

## Naming

### General
- Names describe **what**, not **how**
- Prefer clarity over brevity (`traveller_profile` not `tp`)
- Avoid abbreviations unless universally known (`id`, `url`, `api`)

### Python
| Construct | Convention | Example |
|-----------|-----------|---------|
| Variables / functions | `snake_case` | `traveller_id`, `run_agent()` |
| Classes | `PascalCase` | `TravelManagerAgent`, `AgentResult` |
| Constants | `SCREAMING_SNAKE_CASE` | `AGENT_REGISTRY`, `DEFAULT_TIMEOUT` |
| Private methods | `_leading_underscore` | `_build_plan()`, `_ok()` |
| Modules / files | `snake_case` | `flight_agent.py`, `travel_manager.py` |

### TypeScript
| Construct | Convention | Example |
|-----------|-----------|---------|
| Variables / functions | `camelCase` | `travellerId`, `fetchTrip()` |
| Components | `PascalCase` | `TripCard`, `SearchForm` |
| Types / interfaces | `PascalCase` | `TravellerProfile`, `TripPlan` |
| Constants | `SCREAMING_SNAKE_CASE` | `API_BASE_URL` |
| Files (components) | `PascalCase.tsx` | `TripCard.tsx` |
| Files (utilities) | `camelCase.ts` | `formatDate.ts` |

---

## Folder Layout

### Python (`services/api/app/`)
```
routers/        one file per resource group (health.py, trips.py, agents.py)
models/         Pydantic schemas only — no logic
services/       business logic called by routers
tests/          mirrors the app/ structure
```

### Python (`ai/`)
```
agents/         one file per specialist agent class
concierge/      intent classification, decision engine, conversation engine
manager/        TravelManager — dispatches to agents via the registry
registry/       AgentRegistry — agent name → class lookup
shared/         canonical AgentContext / AgentResult / AgentStatus types
memory/         schema definitions and adapters
llm/            provider adapters (Sprint 1+)
tests/          unit tests for agents
```

### TypeScript (`apps/web/src/`)
```
app/            Next.js App Router pages and layouts
components/     shared React components
lib/            utility functions, API client
types/          TypeScript type definitions
hooks/          custom React hooks
```

---

## Typing

**Python**
- All functions have type annotations — no bare `Any` unless unavoidable
- Use `str | None` (Python 3.10+ union syntax), not `Optional[str]`
- Pydantic models for all API request/response schemas
- `TypedDict` or `dataclass` for internal structured data

```python
# Correct
async def run(self, input_data: dict[str, Any]) -> AgentResult: ...

# Wrong
async def run(self, input_data): ...
```

**TypeScript**
- Strict mode is enabled (`"strict": true` in `tsconfig.json`)
- No `any` — use `unknown` and narrow, or define a proper type
- API response shapes are typed via interfaces in `src/types/`
- Props interfaces are defined alongside their component

---

## Comments

Write comments to explain **why**, never **what**.

```python
# Correct — explains a non-obvious constraint
# Passport expiry must not be logged; it is PII under GDPR Article 9
logger.info("Document check complete", extra={"traveller_id": traveller_id})

# Wrong — restates the code
# Loop through agents
for agent in agents:
```

- Docstrings: one line per public class and public method
- No block comments narrating what the code does step by step
- No `# TODO` in committed code — use `TASK_TRACKER.md` instead

---

## Error Handling

**Python**
- Agents return `AgentResult(success=False, error=...)` — never raise inside an agent's `run()`
- FastAPI routes raise `HTTPException` for client errors (`4xx`)
- Unexpected exceptions are caught at the route layer and return `500`
- Never swallow exceptions silently (`except Exception: pass` is forbidden)

```python
# Correct
try:
    result = await agent.run(input_data)
except Exception as exc:
    logger.exception("Agent run failed", extra={"agent": agent.name})
    raise HTTPException(status_code=500, detail="Internal error") from exc
```

**TypeScript**
- Use `Result`-style returns for async data fetching where errors are expected
- `try/catch` in Server Components for data fetching
- Never expose internal error messages to the browser

---

## Logging

**Python**
- Use the stdlib `logging` module — not `print()`
- Log at the correct level: `DEBUG` (dev detail), `INFO` (normal operations), `WARNING` (recoverable issues), `ERROR` (failures), `CRITICAL` (system integrity)
- Include structured context: `logger.info("msg", extra={"traveller_id": ..., "agent": ...})`
- Never log: passwords, API keys, passport numbers, payment details

**TypeScript**
- `console.log` only in development
- Server-side: use a structured logger (e.g. Pino) in Sprint 2+
- Never log auth tokens or PII

---

## Testing

| Layer | Framework | Location |
|-------|-----------|---------|
| Python agents | `pytest` + `pytest-asyncio` | `ai/tests/` |
| FastAPI routes | `pytest` + `httpx.AsyncClient` | `services/api/tests/` |
| React components | `vitest` + React Testing Library | `apps/web/src/__tests__/` |
| E2E | Playwright (Sprint 3+) | `tests/e2e/` |

**Rules:**
- Every new agent has at least one unit test in `ai/tests/`
- Tests do not call live external APIs — use stubs or fixtures
- Test file names mirror source: `agent_registry.py` → `test_agent_registry.py`
- Tests must pass before a PR is merged

---

## Python Style

- Follow **PEP 8** (enforced by Ruff in CI)
- Line length: 88 characters (Black default)
- Imports: stdlib → third-party → local, separated by blank lines
- No wildcard imports (`from module import *`)
- Use `dataclass` or `Pydantic` for data structures — not bare dicts for typed data

---

## TypeScript Style

- Follow **Prettier** defaults (enforced in CI)
- Use `const` by default; `let` only when reassignment is required
- No `var`
- Prefer `async/await` over `.then()` chains
- Server Components are the default in App Router — opt into `"use client"` deliberately

---

## Git Conventions

### Branch Names
```
feat/short-description        New feature
fix/short-description         Bug fix
docs/short-description        Documentation only
refactor/short-description    Code change without behaviour change
test/short-description        Tests only
```

### Commit Messages
```
<type>: <short imperative summary>

Optional body explaining WHY, not what.
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Examples:
```
feat: add TravelManagerAgent orchestration
fix: return 400 on missing destination field
docs: update ARCHITECTURE.md with Commerce layer
```

### Pull Requests
- One concern per PR
- PRs reference the Task ID in the title: `[T-004] Add /agents/run endpoint`
- Must pass CI before merge
- Squash merge to keep `main` history clean
