# Planner Grounding and Source Transparency — T-052

The assembled planner response now states what kind of evidence supports
each recommendation. This closes a trust gap exposed by the New York
acceptance scenario: a useful mock or static planning result must not read
like a live, bookable, or legally authoritative fact.

## Public contract

`POST /planner/plan` adds `itinerary.grounding_notices`. Each notice contains:

| Field | Meaning |
|---|---|
| `domain` | Destination, flight, accommodation, budget, visa, weather, or events |
| `level` | `LIVE`, `SANDBOX`, `ESTIMATE`, `CURATED`, `GUIDANCE`, `CLIMATE_PROFILE`, or `IDEA` |
| `title` / `message` | Traveller-facing disclosure |
| `data_source` | Provider-neutral source label |
| `is_current` | Whether the result came from an explicit live production source |
| `requires_confirmation` | Whether the traveller must recheck before acting |
| `retrieved_at` | Provider retrieval time when one is available |

Unknown provider labels fail closed to `ESTIMATE`. A vendor name or a
successful mock/sandbox request never makes a result `LIVE`. Only an explicit
production-shaped source label can do so.

## Planner behaviour

- Mock flight and accommodation options are labelled `ESTIMATE`.
- Duffel sandbox options are labelled `SANDBOX` and non-purchasable.
- Static regional budgets are labelled `ESTIMATE`, not quotes.
- Destination catalogue results are labelled `CURATED`.
- Visa results are labelled `GUIDANCE` and require an official check.
- Weather results are labelled `CLIMATE_PROFILE`, not forecasts.
- Fashion, football, soccer, match, and event interests add an `IDEA` notice
  when Event Intelligence is unavailable. T-053's curated event results use
  `CURATED` instead: they are structured interest matches, but still confirm
  no live calendar, fixture, ticket, price, or availability was queried.
- Executive-summary wording follows the same source distinction.

This task does not add or activate a provider, alter scoring, change a selected
recommendation, or add booking/payment behaviour. It establishes the public
contract that later live price and event providers must satisfy.
