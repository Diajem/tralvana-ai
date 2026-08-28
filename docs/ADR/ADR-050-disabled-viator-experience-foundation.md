# ADR-050: Disabled Viator experience foundation

## Status

Accepted for T-080.

## Context

Tralvana requires transactional tours and activities without redirecting the
customer to a supplier website. Viator qualification and the exact commercial
model are not yet confirmed. Implementing endpoints, credentials or booking
behaviour before that decision would risk coupling Tralvana to the wrong API
access level and accidentally exposing an unapproved transaction path.

## Decision

- Add `EXPERIENCES` as a capability distinct from ticketed `EVENTS`.
- Define provider-neutral discovery, availability, hold, booking, voucher,
  cancel-quote and cancellation records.
- Add a Viator adapter shell that is permanently fail-closed in this task.
- Do not register it in the application composition root.
- Do not add a mode switch, endpoint URL, secret reference or HTTP transport.
- Keep transactions outside discovery caching and automatic retries.

## Consequences

The supplier boundary and required lifecycle are testable before credentials
arrive, while all external and transactional activity remains impossible. A
later ADR must select the approved Viator partner model and document endpoint,
payment, certification, persistence, idempotency and servicing decisions before
the adapter can be activated.
