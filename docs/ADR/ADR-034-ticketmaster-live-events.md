# ADR-034: Ticketmaster Live Event Provider

**Status:** Accepted
**Date:** 2026-07-26
**Task:** T-054

## Context

T-053 established a provider-neutral event contract but intentionally returned
curated, undated ideas. The planner therefore could not verify whether a
football match, fashion event, concert, festival, or performance existed
during the traveller's dates.

## Decision

Use Ticketmaster Discovery API v2 as Tralvana's first live event source.

- Register it only when `TRALVANA_EVENT_PROVIDER_MODE=LIVE`.
- Require `TICKETMASTER_API_KEY` at startup in live mode.
- Authenticate with Ticketmaster's documented `apikey` query parameter while
  preventing the key from entering logs, diagnostics, public results, or tests.
- Select it as `ProviderEnvironment.PRODUCTION`; Ticketmaster Discovery has no
  sandbox catalogue.
- Map destination, dates, name, classification, venue, public URL, and event
  status into T-053's canonical event shape.
- Treat the link as discovery, not a booking or guaranteed-inventory surface.
- Return a clear unavailable error after a failed live search unless an
  operator explicitly enables labelled curated fallback.
- Never blend live and mock results.

## Consequences

- Event Intelligence and Trip Brain remain vendor-neutral.
- The planner can label current provider listings `LIVE`, with retrieval time.
- The New York acceptance scenario can show dated football/fashion listings
  when Ticketmaster has relevant coverage.
- A broad search is used when several different interests are supplied;
  Tralvana's existing scorer ranks the results. A single interest is sent as
  Ticketmaster's documented keyword filter.
- Ticket prices and actual ticket inventory remain outside this task.

## Rejected alternatives

| Alternative | Reason |
|---|---|
| Enable live calls whenever a key exists | Credential presence is not operator consent |
| Keep using curated ideas after obtaining the key | Does not solve dated event discovery |
| Mix mock ideas into every live result set | Makes provenance ambiguous |
| Add ticket checkout now | Requires commercial, legal, inventory, and payment decisions outside event discovery |
