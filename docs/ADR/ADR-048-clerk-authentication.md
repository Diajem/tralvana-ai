# ADR-048: Delegate Authentication to Clerk

**Status:** Accepted

**Date:** 2026-07-26

**Task:** T-031

## Context

Tralvana had persistent personal Goals and Trips but no account boundary. The
remaining product decision was Clerk versus application-owned Auth.js sessions.
The owner selected Clerk after reviewing the launch trade-off.

## Decision

- Use Clerk for user lifecycle and session management.
- Use Clerk's stable user ID as Tralvana's canonical `traveller_id`.
- Verify session JWTs independently in FastAPI using the official Python SDK
  and configured PEM public key; do not call Clerk on every API request.
- Protect resources at the FastAPI router and ownership boundaries.
- Keep only liveness/readiness, the isolated demo, root metadata, and public
  commercial redirects anonymous.
- Preserve an explicitly disabled zero-setup mode for development/tests, but
  reject that mode in production.

## Consequences

- Tralvana stores no password or password-reset credential.
- Client-provided traveller IDs are no longer an authority.
- Production deployment requires one Clerk application and three securely
  configured values.
- Local regression tests remain deterministic and make no network calls.

## Rejected alternatives

### Auth.js/NextAuth

Rejected for the current launch because Tralvana would own more session,
provider, recovery, and operational configuration without a product advantage.

### Frontend-only route protection

Rejected because direct FastAPI calls would remain open and resource IDs could
cross account boundaries.

### Fetch Clerk JWKS on each request

Rejected in favour of the configured public key, eliminating a request-time
network dependency from the authentication path.
