# Engineering Principles

These principles govern every technical decision on TravelOS. When in doubt, return to this document.

---

## 1. Architecture First

Design before building. Every non-trivial feature requires a documented design before a line of code is written.

**In practice:**
- Update `ARCHITECTURE.md` when adding new services or agents
- Define the data contract (schema) before implementing the storage
- New agent types require a written spec in `docs/` before code in `ai/agents/`
- PRs that skip design for complex features are returned, not merged

**Why:** Architectural mistakes are exponentially more expensive to fix than implementation mistakes.

---

## 2. Small Iterations

Ship the smallest thing that proves the idea. Never build more than the current sprint requires.

**In practice:**
- Each task produces a working, demonstrable increment — not a partial foundation
- Stubs and placeholder data are acceptable; half-built abstractions are not
- Refactor when the third use case appears, not when the first is written
- Sprint scope is fixed; add to the backlog, not the current sprint

**Why:** Unreleased code is a liability. Working software in the next sprint beats a perfect architecture in six months.

---

## 3. Modular Services

Every component has a single owner and a defined interface. No component reaches into another's internals.

**In practice:**
- Agents communicate through `AgentResult` — never by sharing state
- API routes own HTTP; they do not contain business logic
- Memory layer is accessed only through its defined schema and adapters
- Folder boundaries are enforced: `ai/` is not imported by `apps/web/`

**Why:** Modularity is what allows agents to be upgraded, replaced, or scaled without cascading rewrites.

---

## 4. Model Agnostic

No agent is hardwired to a specific LLM provider, embedding model, or API.

**In practice:**
- LLM provider is configured via environment variable (`LLM_PROVIDER=anthropic`)
- Agent prompts are stored as strings or templates — not embedded in SDK calls
- Provider-specific SDK calls are wrapped in an adapter (`ai/llm/`)
- Switching from Claude to GPT-4 should require a config change, not a code rewrite

**Why:** The LLM landscape is moving fast. Vendor lock-in today is technical debt tomorrow.

---

## 5. Security First

Security is a requirement, not a sprint task. Every feature is built with security by default.

**In practice:**
- Secrets live in `.env` only — never in source code, logs, or API responses
- Sensitive traveller data (passport, payment) is never logged
- API endpoints validate all inputs with Pydantic before processing
- Authentication is enforced at the API layer — agents assume the caller is authenticated
- Dependencies are pinned in `requirements.txt` and reviewed on update

**Why:** A travel platform handles personal documents, payment details, and itinerary data. A breach is existential.

---

## 6. No Hardcoded Providers

No third-party service, API, or vendor is hardcoded into business logic.

**In practice:**
- Flight search uses a `FlightProvider` interface — not a direct Amadeus or Skyscanner call
- Email uses a `NotificationProvider` — not a direct SendGrid call
- Payment uses a `PaymentProvider` — not a direct Stripe call
- Provider implementations live in `services/providers/` and are injected at runtime

**Why:** Provider contracts change, pricing changes, and better options appear. Swap the adapter, not the agent.

---

## 7. Documentation Driven

If it isn't documented, it doesn't exist. Code without documentation is a trap for the next engineer.

**In practice:**
- Every new agent has a docstring describing what it does and what it returns
- Architecture changes update `ARCHITECTURE.md` in the same PR
- New APIs are documented in FastAPI docstrings (Swagger generates from these)
- `TASK_TRACKER.md` is updated when tasks change status
- Handoff documents are kept current for AI coding assistants

**Why:** TravelOS will be built across sessions, tools, and contributors. Documentation is the shared memory.

---

## 8. Testable Components

Every agent and service is independently testable without requiring the full stack.

**In practice:**
- Agents accept `input_data: dict` and return `AgentResult` — no hidden dependencies
- FastAPI endpoints are tested with `TestClient` — no live network calls in unit tests
- External provider calls are behind interfaces that can be stubbed
- Tests live in `ai/tests/` and `services/api/tests/` — not alongside implementation files
- CI runs tests before any merge

**Why:** Confidence to change is confidence to move fast. Without tests, every refactor is a risk.
