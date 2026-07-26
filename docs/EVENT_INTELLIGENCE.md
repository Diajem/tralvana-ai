# Event Intelligence — T-053–T-056

Event Intelligence adds a provider-neutral `EVENTS` discovery path for
event-shaped trip interests such as fashion, football, soccer, matches,
concerts, festivals, and theatre.

## Evidence levels

The first provider is `mock_event_provider`. It returns curated search ideas,
not date-specific event listings. Every option therefore has:

- `date_status = UNVERIFIED`
- `availability_status = UNKNOWN`
- `starts_at = null`
- `ends_at = null`
- `ticket_url = null`
- `data_source = TRALVANA_CURATED_EVENT_IDEAS`

The module never invents a fixture, fashion calendar, organiser, ticket,
price, or availability. Its purpose is to match the traveller's interests to
useful searches while preserving a stable contract for a later live provider.

T-054 adds `ticketmaster_event_provider` as the first opt-in live source.
It returns current public listings, exact dates, and event links only when
present in Ticketmaster's response. It does not guarantee ticket inventory or
price and does not implement booking.

T-055 treats provider date and category filters as hints rather than proof.
Tralvana independently:

- fans out a multi-interest request into at most four interest-specific live
  searches and deduplicates provider event IDs;
- enforces the inclusive destination-local travel-date window after retrieval;
- excludes past or undated live listings when their timing cannot be proven;
- rejects live listings that do not match any stated interest; and
- prevents a generic Sports classification from being treated as evidence of
  a soccer/football match.

T-056 adds a conservative team-level signal for soccer listings:

- explicit reserve, academy, youth, age-group, B-team, or roman-numeral-II
  labels map to `RESERVE_OR_YOUTH`;
- a soccer listing without one of those provider-text markers maps to
  `SENIOR_OR_OPEN`, which does not claim that Ticketmaster guaranteed a
  senior first-team fixture;
- comparable `SENIOR_OR_OPEN` listings rank above reserve/youth listings;
  and
- a reserve/youth match remains visible when it is the only relevant match in
  the traveller's date window.

## Architecture

```text
Trip Brain
  -> Event Intelligence
    -> GatewayEventProvider
      -> Intelligence Gateway (Capability.EVENTS)
        -> mock_event_provider (MOCK mode)
        -> ticketmaster_event_provider (LIVE mode)
```

The Trip Brain selects Events only when a destination exists and either the
current entities or linked Goal contains an event-shaped interest. A complete
trip without such an interest still runs the original six core modules only.

## Public API

`POST /events/recommend`

```json
{
  "destination": "New York",
  "start_date": "2026-08-07",
  "end_date": "2026-08-22",
  "interests": ["fashion", "soccer"]
}
```

The response contains ranked `event_options`, provider-neutral provenance, and
a `filter_summary` stating how many provider results were excluded by travel
dates or relevance.
`GET /events/{event_option_id}` and `GET /trips/{trip_id}/events` expose the
same safe option contract.

## Planner integration

`POST /planner/plan` adds `itinerary.event_recommendations`. The planner UI
renders them in a dedicated section. Grounding remains fail-closed:

- structured mock event results are `CURATED`, never `LIVE`;
- Ticketmaster results are `LIVE`, timestamped, and require confirmation;
- an explicitly enabled curated fallback is `MOCK_FALLBACK`, never blended;
- event interests with no successful Event Intelligence result remain `IDEA`;
- every result requires official date and availability confirmation.

## Live provider contract

The Ticketmaster adapter registers for `Capability.EVENTS` and implements the
same search parameters: destination, start date, end date, and interests.
It populates exact dates, source identity, event status, venue, and public URL
only from the provider response. Multiple distinct interests are searched
separately (maximum four vendor calls), then deduplicated before provider-neutral
date and relevance filtering. See `docs/LIVE_EVENT_SEARCH.md`.
