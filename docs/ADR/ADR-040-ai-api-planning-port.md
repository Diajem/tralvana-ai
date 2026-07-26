# ADR-040: Invert the AI-to-API Planning Dependency

**Status:** Accepted

**Date:** 2026-07-26

**Task:** T-036

## Context

REC-008 and TD-006 identified lazy imports from `ai/` into
`services/api/app/domains`. Since that audit, the same dependency had expanded
from Goal/Trip creation into Trip Brain context and all seven Discovery
adapters. Moving AI orchestration into another process would therefore fail
even if only the two original imports were removed.

## Decision

- Define `PlanningPort` in `ai/ports/`.
- Put Goal/Trip creation and lookup plus the seven public Discovery operations
  on that AI-owned contract.
- Implement it in `services/api/app/adapters/PlanningAdapter`.
- Bind the adapter once in the FastAPI composition root.
- Make Conversation Engine accept an explicitly injected port for isolated
  use/tests, falling back to the configured application binding.
- Make Trip Brain context and Discovery adapters resolve the same port.
- Add a repository-boundary test that rejects every `app.*` import in
  production `ai/` code.

## Consequences

- The dependency direction is now `services/api/app` → `ai`, never the reverse.
- Existing domain services remain the application implementation; business
  logic and public API responses do not move or change.
- AI tests can provide small deterministic port doubles.
- A future AI service can supply an HTTP/RPC adapter without changing the
  Conversation Engine or Trip Brain.
- The binding is process-wide because the current FastAPI application has one
  composition root; individual `ConversationEngine` instances may override it.

## Rejected alternatives

### Fix only Goal and Trip imports

Rejected because seven newer Discovery imports would leave the same
multi-service failure in place while misleadingly closing TD-006.

### Move domain services into `ai/`

Rejected because HTTP application/domain ownership would become less clear and
the dependency would merely be reversed elsewhere.

### Duplicate Discovery logic behind new AI services

Rejected because it would create competing scoring and provider paths. The
adapter delegates to the existing public domain-service operations.
