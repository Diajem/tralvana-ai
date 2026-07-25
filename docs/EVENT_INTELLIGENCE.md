# Event Intelligence Foundation — T-053

Event Intelligence adds a provider-neutral `EVENTS` discovery path for
event-shaped trip interests such as fashion, football, soccer, matches,
concerts, festivals, and theatre.

## Current evidence level

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

## Architecture

```text
Trip Brain
  -> Event Intelligence
    -> GatewayEventProvider
      -> Intelligence Gateway (Capability.EVENTS)
        -> mock_event_provider
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

The response contains ranked `event_options` plus provider-neutral provenance.
`GET /events/{event_option_id}` and `GET /trips/{trip_id}/events` expose the
same safe option contract.

## Planner integration

`POST /planner/plan` adds `itinerary.event_recommendations`. The planner UI
renders them in a dedicated section. Grounding remains fail-closed:

- structured mock event results are `CURATED`, never `LIVE`;
- event interests with no successful Event Intelligence result remain `IDEA`;
- every result requires official date and availability confirmation.

## Future live provider

A live adapter must register for `Capability.EVENTS` and implement the same
search parameters: destination, start date, end date, and interests. It must
populate current timestamps, exact dates, source identity, and availability
only from the provider response. Activating a live vendor, credential,
commercial ticket link, or booking flow is outside T-053.
