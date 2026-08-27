# ADR-049: HBX and Provider-Neutral Accommodation Transactions

**Status:** Accepted

**Date:** 2026-08-27

**Task:** T-076

## Context

Tralvana must not depend on one supplier or redirect customers away from its
website or application. Duffel Stays access remains pending, while Diajem
Global Ltd has obtained HBX API access. HBX evaluation access is quota-limited,
and its Content API is intended for offline static catalogue synchronisation.

## Decision

- Add HBX Hotels as a second accommodation search provider behind the existing
  Intelligence Gateway.
- Support explicit HBX-only and multi-supplier sandbox modes; never infer
  activation from credential presence.
- Resolve destination codes from a migration-backed offline catalogue, not
  Content API calls in customer request paths.
- Keep search failover in the gateway, while rate confirmation, booking and
  cancellation use a provider-neutral contract outside discovery caching and
  automatic retry behaviour.
- Require explicit customer approval and a verified price/currency boundary
  before booking; default cancellation to simulation.
- Keep sandbox inventory non-purchasable until checkout, payment, persistence,
  servicing and HBX certification are complete.
- Remove redirect-based Expedia affiliate checkout from flight and
  accommodation details.

## Consequences

Tralvana can develop and certify HBX without coupling the product to HBX field
names. Another supplier can implement the same booking contract. Content API
cannot silently consume quota during customer traffic, and transactional calls
cannot be replayed by the discovery retry layer. A migration and catalogue sync
are required before HBX searches succeed.

## Rejected alternatives

### Content API during every search

Rejected because the data is static, it wastes quota and creates an unnecessary
runtime dependency.

### Booking inside the Intelligence Gateway

Rejected because discovery retries and caching are unsafe for reservation
mutations and could create duplicate bookings.

### Enable sandbox booking buttons immediately

Rejected because sandbox confirmations are not real reservations and the
customer-facing safeguards are incomplete.

### Retain redirect affiliate checkout

Rejected because it conflicts with Tralvana's non-redirect product principle.
