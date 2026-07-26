# ADR-036: Senior-Team Event Preference

**Status:** Accepted
**Date:** 2026-07-26
**Task:** T-056

## Context

The first T-055 Windows verification returned three relevant, in-window New
York soccer listings, but every result involved NYCFC II. The date and sport
filters were correct; the remaining issue was that a reserve-team match could
score exactly like a comparable senior-team listing.

Ticketmaster does not expose one reliable, universal senior-first-team field.
Treating every soccer result without a reserve marker as guaranteed senior
would overstate the provider evidence.

## Decision

- Inspect only the provider's event and attraction names for explicit
  reserve/youth signals.
- Classify reserve, academy, youth, supported age-group, B-team,
  development-squad, and standalone roman-numeral-II markers as
  `RESERVE_OR_YOUTH`.
- Classify other soccer listings as `SENIOR_OR_OPEN`: available provider text
  does not mark them as reserve/youth, but Tralvana does not claim independent
  first-team verification.
- Use a bounded score penalty so a comparable `SENIOR_OR_OPEN` listing ranks
  above `RESERVE_OR_YOUTH`.
- Keep reserve/youth results when no stronger relevant listing exists.
- Preserve `NOT_APPLICABLE` for non-soccer live events and `UNSPECIFIED` for
  curated event ideas.
- Expose the label, reasoning, and risk through Event Intelligence, the public
  API, Trip Brain, planner, verification script, and planner UI.
- Add a deterministic full-planner test for the existing 7–22 August 2026 New
  York scenario, including live grounding and a zero-result fashion search.

## Consequences

- A senior/open soccer listing becomes the preferred recommendation when it
  competes with a healthy reserve/youth listing.
- Reserve-team matches are not hidden when they are the traveller's only
  relevant option.
- Women's senior-team names are not treated as youth solely because they
  contain `Women`.
- The public label remains honest about the limit of Ticketmaster's metadata.
- Booking, ticket inventory, price, and competition-tier guarantees remain
  outside Tralvana.

## Rejected alternatives

| Alternative | Reason |
|---|---|
| Remove every reserve/youth result | A reserve match can still be useful when no senior listing exists |
| Treat all unmarked soccer listings as guaranteed senior | Ticketmaster does not provide a universal field proving that claim |
| Maintain a hard-coded global club hierarchy | It would become stale, provider-specific, and incomplete |
| Prefer by event name alone in the planner | Ranking belongs in provider-neutral Event Intelligence, not assembly or UI |
