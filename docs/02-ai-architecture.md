# AI Architecture

## Design Philosophy

Agents are stateless units of work. All state lives in the memory layer or is passed via `AgentContext`. This makes agents independently testable and replaceable.

## Agent Anatomy

```
BaseAgent (abstract)
│
├── run(input_data) → AgentResult   ← all agents implement this
├── context: AgentContext           ← session + traveller identity
├── _ok(output)                     ← success helper
└── _err(message)                   ← failure helper
```

Every agent returns an `AgentResult`:

```python
@dataclass
class AgentResult:
    success: bool
    output: Any
    error: str | None
```

## Orchestrator Flow

```
API request
    │
    ▼
Orchestrator.run(agent_name, input_data, traveller_id)
    │
    ├── Creates AgentContext (new session_id)
    ├── Looks up agent in AGENT_REGISTRY
    ├── Instantiates agent with context
    └── Calls agent.run(input_data)
            │
            └── Returns AgentResult → API response
```

## Agent Registry

Agents are registered in `orchestrator.py`:

```python
AGENT_REGISTRY = {
    "travel_manager": TravelManagerAgent,
    # add new agents here
}
```

Adding a new agent: create the class in `ai/agents/`, inherit `BaseAgent`, add to the registry.

## Memory Layer

Sprint 0: schema-only (no persistence). The `traveller_profile_schema.md` defines the data contract. Persistence (SQLite → Postgres → vector store) will be added in Sprint 1.

## LLM Integration (Sprint 1+)

No LLM calls in Sprint 0. When added:
- Use `anthropic` SDK with `claude-sonnet-4-6` as default model
- Prompts live in `ai/agents/<agent_name>/prompts/`
- Never hardcode API keys — read from environment variables

## Testing Agents

```bash
cd tralvana-ai
python -m pytest ai/tests/
```

Each agent should have a unit test that calls `agent.run(input_data)` directly without going through the orchestrator.
