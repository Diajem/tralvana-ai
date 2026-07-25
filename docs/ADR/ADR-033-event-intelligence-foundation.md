# ADR-033: Event Intelligence Foundation

**Status:** Accepted  
**Date:** 2026-07-25  
**Task:** T-053

## Context

T-051 carried fashion and soccer interests into the New York itinerary.
T-052 correctly labelled those activities as unverified ideas because no
event provider had been queried. The Intelligence Gateway already reserved
`Capability.EVENTS`, but no Event Discovery module, provider, API, Trip Brain
adapter, or planner output existed.

Connecting a live vendor immediately would mix two decisions: the stable
Tralvana event contract and a vendor-specific credential/commercial choice.
It would also block progress on obtaining and approving an external API key.

## Decision

Add Event Intelligence as an optional seventh Discovery module.

- Events is selected only when the trip has a destination and an explicit
  event-shaped interest.
- A complete trip still selects the original six core modules; Events is not
  silently forced into every plan.
- The first provider is a deterministic curated mock behind the existing
  Intelligence Gateway.
- The public contract supports exact dates, availability, and ticket URLs,
  but the mock provider sets all of them to unknown/null.
- Trip Assembly exposes ranked `event_recommendations` and a `CURATED`
  grounding notice. It never promotes mock retrieval time to current event
  evidence.
- A live event vendor and credential are a separate task.

## Consequences

- `POST /events/recommend`, `GET /events/{id}`, and
  `GET /trips/{trip_id}/events` are additive APIs.
- `POST /planner/plan` gains additive structured event recommendations.
- The Intelligence Gateway diagnostic output includes
  `mock_event_provider` under `EVENTS`.
- Fashion/football plans become more structured without claiming that a
  fixture, show, ticket, price, or availability was confirmed.
- A future live provider can replace the mock at the provider boundary
  without changing Trip Brain or the planner response shape.

## Rejected alternatives

| Alternative | Reason |
|---|---|
| Hard-code New York fixtures or fashion dates | Would fabricate time-sensitive facts |
| Add a live vendor before defining the domain contract | Couples Tralvana's public API to one vendor and blocks on credentials |
| Keep only free-text daily-outline ideas | Cannot rank, attribute, store, diagnose, or later replace them cleanly |
| Run Events for every complete trip | Adds irrelevant work and lowers confidence for travellers who did not request events |
