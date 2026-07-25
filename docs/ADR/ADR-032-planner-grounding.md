# ADR-032: Planner Grounding and Source Transparency

**Status:** Accepted  
**Date:** 2026-07-25  
**Task:** T-052

## Context

T-051 made the complete New York holiday request plan correctly, but the
assembled itinerary still placed deterministic mock prices, static budgets,
general visa rules, seasonal climate profiles, and generic event ideas beside
each other without a first-class source contract. Assumption text existed deep
in the recommendation, but the executive summary and planner UI could still
sound more current or certain than the underlying evidence.

Tralvana's product constitution requires trust before automation and forbids
pretending to know live price, availability, visa, weather, or event facts
without current data.

## Decision

Add `GroundingNotice` at the Trip Assembly boundary and expose it as
`itinerary.grounding_notices`.

Trip Assembly is the correct boundary because it is where already-computed
module results become one traveller-facing itinerary. The new contract
describes provenance only; it does not score, rank, select, or mutate a module
result.

Source classification fails closed:

- explicit production-shaped labels may be `LIVE`;
- labels containing `SANDBOX` are `SANDBOX`;
- mock, fallback, missing, and unknown provider labels are `ESTIMATE`;
- non-provider domains use explicit `CURATED`, `GUIDANCE`,
  `CLIMATE_PROFILE`, and `IDEA` levels.

Every current notice requires confirmation before the traveller acts. Even a
future live search can change before booking.

## Consequences

- The planner API gains one additive itinerary field.
- The frontend renders a visible "What Has Been Checked" section.
- Executive summaries can no longer say "You'll fly" or "You'll stay" for
  mock/sandbox results.
- ESTA/visa wording remains useful but is explicitly planning guidance that
  must be verified officially.
- Fashion and football interests remain useful itinerary ideas without
  fabricating a date-specific event.
- Later live price and event integrations have a stable public contract to
  populate without redesigning Trip Brain or the planner.

## Rejected alternatives

| Alternative | Reason |
|---|---|
| Parse free-text assumptions in the frontend | Brittle, presentation-specific, and not a stable API contract |
| Treat any vendor-branded response as live | Duffel sandbox data is vendor-shaped but explicitly non-purchasable |
| Wait until every live provider exists | Leaves current acceptance output capable of overstating certainty |
| Add event fixtures manually for New York | Would fabricate date-specific facts without a live provider |
