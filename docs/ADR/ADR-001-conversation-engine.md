# ADR-001: Conversation Engine Architecture

**Status:** Accepted
**Date:** 2026-07-07
**Deciders:** Product, Engineering
**Sprint:** Sprint 1

---

## Context

TravelOS needs a central AI conversation layer. Every traveller interaction must pass through
a single entry point. The system must handle multi-turn conversations, classify intent,
decide which specialist agents are required, dispatch them concurrently, and compose a
coherent natural-language response.

The business goal is for the traveller to feel they are speaking to an experienced travel
consultant, not a chatbot reading back a list of fields.

Sprint 1 constraints: no database, no authentication, no external APIs, no LLM provider.

---

## Decision

### Architecture: Layered pipeline with a single entry point

```
TravelConcierge          ← public API, stable interface for the HTTP layer
ConversationEngine       ← state machine, session management, turn orchestration
IntentClassifier         ← classify message into one of 8 intents
DecisionEngine           ← decide agents needed, info gaps, safety flags
TravelManager            ← dispatch to specialist agents via AgentRegistry
AgentRegistry            ← name → class map, zero coupling to TravelManager
Specialist Agents        ← run concurrently, each returns AgentResult
ResponseComposer         ← assemble one coherent traveller-facing reply
```

### Key decisions

**1. TravelConcierge as a single stable entry point**

The HTTP layer calls only `TravelConcierge.handle()`. This means internal refactors
(swapping the classifier, adding agents, changing session storage) never require
changes in the API layer.

**2. DecisionEngine before agents**

A dedicated `DecisionEngine` decides *before* any agent runs:
- Is there enough information to proceed?
- Which agents are required?
- Is the destination safety-sensitive?
- Will live data be needed?

This prevents partial execution and enables clean clarification loops.

**3. Registry pattern for agent dispatch**

`TravelManager` never imports agent classes directly. It queries `AgentRegistry`.
Adding a new specialist agent requires only:
1. Creating the class.
2. Registering it.
3. Adding it to `_AGENT_MAP` if needed.

No changes to TravelManager, ConversationEngine, or the HTTP layer.

**4. Concurrent agent execution via asyncio.gather**

Specialist agents run concurrently. One agent's failure does not block others.
Exceptions are caught and returned as `AgentStatus.FAILED` results.

**5. Rich AgentResult**

Every agent returns a structured `AgentResult` with 9 fields: `agent_name`, `status`,
`confidence`, `data`, `assumptions`, `missing_information`, `risks`, `recommendations`,
`next_actions`. This makes the API response transparent and actionable for the traveller.

**6. Rule-based placeholder logic in Sprint 1**

Intent classification and decision logic are deterministic keyword matching and
rule sets. This keeps Sprint 1 dependency-free and testable. The `IntentClassifier`
interface (`classify(message) → ClassifiedIntent`) is stable — the LLM classifier
in Sprint 3 implements the same interface with zero call-site changes.

---

## Alternatives Considered

### A. Single monolithic function

**Pros:** Simple to implement.
**Cons:** Not testable in isolation; impossible to add agents without touching the core;
violates single-responsibility.

### B. Microservice per agent

**Pros:** Independent deployability.
**Cons:** Massive complexity for Sprint 1 with no infrastructure; overkill before
product-market fit; premature optimisation.
**Verdict:** Architecture is designed so each agent *can* be extracted to a microservice
in Sprint 4+; the registry pattern makes this refactor low-risk.

### C. LLM-first (no rules)

**Pros:** More natural intent classification.
**Cons:** Requires an LLM provider (paid API), makes the system non-deterministic,
prevents offline development, introduces latency and cost from day one.
**Verdict:** LLM classification is the target state in Sprint 3. Sprint 1 uses rules
to validate the architecture without committing to a provider.

---

## Consequences

**Positive:**
- API layer is decoupled from AI implementation details.
- Adding a new specialist agent is a 3-step operation with no core changes.
- Rule-based logic is fully deterministic and unit-testable without mocks.
- Architecture is provider-agnostic — any LLM provider slots in at Sprint 3.
- Concurrent agent execution is built in from the start.

**Negative / Trade-offs:**
- More files and layers than a monolithic approach (accepted for long-term maintainability).
- Two separate conversation stacks exist in Sprint 1 (legacy service-layer stack from
  T-005 v1 and new AI concierge stack). The legacy endpoints remain for backward
  compatibility; the new `/conversation/message` is the primary interface going forward.

---

## Future Work

| Sprint | Change |
|--------|--------|
| 2 | JWT authentication; profile persistence in PostgreSQL |
| 3 | LLM-powered IntentClassifier and ResponseComposer |
| 3 | Redis session persistence; rolling context_summary |
| 4 | Live flight and hotel search via APIs |
| 5 | Live visa data; safety advisory API integration |
| 4+ | Extract heavy agents into microservices behind AgentRegistry |
