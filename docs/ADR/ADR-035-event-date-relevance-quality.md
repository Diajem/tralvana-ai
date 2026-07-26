# ADR-035: Event Date and Relevance Quality

**Status:** Accepted
**Date:** 2026-07-26
**Task:** T-055

## Context

The first real Ticketmaster verification succeeded, but the provider returned
listings outside the requested 7–22 August 2026 New York window. T-054 also
kept a multi-interest search broad, so its first page was dominated by events
that did not match the traveller's fashion or soccer interests.

External search parameters cannot be treated as proof that every returned
record satisfies Tralvana's itinerary contract.

## Decision

- Fan out two or more distinct interests into separate keyword searches,
  capped at four gateway calls per logical request.
- Deduplicate live records by provider event ID, with name/date/venue as a
  provider-neutral fallback key.
- Preserve Ticketmaster's destination-local date alongside its UTC timestamp.
- Enforce the inclusive requested date window after normalisation; when no
  start date exists, exclude events before today.
- Exclude undated live records because they cannot prove itinerary fit.
- Score a strong match to any stated interest without diluting it by unrelated
  trip preferences.
- Exclude unrelated live listings when interests were supplied.
- Do not infer soccer from Ticketmaster's generic Sports segment alone.
- Return safe filter counts so zero results remain explainable.

Curated mock ideas retain their T-053 contract: they are undated suggestions,
not live listings, and are not discarded by live-only date filtering.

## Consequences

- A provider bug or broad first page cannot silently place an event outside
  the traveller's trip.
- Fashion and soccer searches can each contribute results to one itinerary.
- Multiple interests consume multiple cached/rate-limited provider calls,
  bounded at four.
- A relevant zero-result response is preferable to displaying an unrelated or
  out-of-window event.
- Ticket booking, ticket inventory, and pricing remain outside the system.

## Rejected alternatives

| Alternative | Reason |
|---|---|
| Trust Ticketmaster date parameters | The live verification proved returned records can violate them |
| Send no keyword for multiple interests | Generic events dominated the first page |
| Treat every Sports event as soccer | Misclassifies basketball, baseball, wrestling, and American football |
| Keep unrelated events as low-ranked alternatives | Still exposes recommendations that do not satisfy the request |
| Remove undated curated ideas too | Their explicit purpose is safe fallback guidance, not a live claim |
