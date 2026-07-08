# Flights API

Base URL: `http://localhost:8000`

## Endpoints

### POST /flights/recommend

Generate ranked flight recommendations.

**Request body**

```json
{
  "traveller_id": "traveller_001",
  "trip_id": "uuid",
  "origin": "London",
  "destination": "Tokyo",
  "departure_date": "2026-09-15",
  "return_date": "2026-09-25",
  "cabin_class": "economy",
  "budget_style": "balanced",
  "airline_preference": "AeroLondon",
  "adults": 1,
  "trip_duration_days": 10
}
```

All fields are optional except `destination`. `origin` defaults to `"London"`. If `trip_id` is provided, `origin`/`destination`/`trip_duration_days` are taken from the linked Trip Plan when present. If `departure_date` is omitted, it defaults to 30 days from today and the response's `assumptions` records this.

**Response: 201 Created**

```json
{
  "traveller_id": "traveller_001",
  "trip_id": null,
  "origin": "London",
  "destination": "Tokyo",
  "flight_options": [
    {
      "flight_option_id": "uuid",
      "airline": "AeroLondon",
      "flight_number": "AL453",
      "cabin_class": "economy",
      "stops": 0,
      "layover_duration": "",
      "departure_time": "14:30",
      "arrival_time": "20:30",
      "total_duration": "6h 0m",
      "estimated_price": 825,
      "currency": "USD",
      "baggage_included": true,
      "refundability": "partially_refundable",
      "flexibility": "flexible",
      "match_score": 0.82,
      "reasoning": "AeroLondon AL453 (0 stops, 6h 0m) scores 0.82 for a economy traveller. ...",
      "risks": [],
      "assumptions": ["No traveller profile — default cabin and budget assumptions applied."],
      "recommendation_type": "BEST_OVERALL"
    }
  ],
  "assumptions": [
    "Prices and schedules are deterministic mock data — no live airline inventory was queried.",
    "Scoring assumes a economy cabin preference and 'balanced' budget style."
  ],
  "next_actions": [
    "Confirm exact travel dates for accurate pricing.",
    "Compare baggage policies before booking.",
    "Check visa and passport requirements for the destination."
  ],
  "recommended_agents": ["flight_agent"],
  "summary": "6 flight option(s) ranked for London to Tokyo. Best overall: AeroLondon AL453 at USD 825 (match 0.82). No live bookings have been made."
}
```

---

### GET /flights/{flight_option_id}

Retrieve a single flight option by ID.

**Response: 200 OK** — full `FlightOption` object, or **404** if not found.

---

### GET /trips/{trip_id}/flights

List all flight options previously recommended and linked to a trip.

**Response: 200 OK** — array of `FlightOption` objects (empty array if the trip has no saved flight options).

---

## Recommendation Types

| Type | Meaning |
|------|---------|
| `BEST_OVERALL` | Highest match score |
| `LOWEST_PRICE` | Cheapest fare |
| `SHORTEST_DURATION` | Fastest total travel time |
| `BEST_FOR_FAMILY` | Best baggage + low stop count fit |
| `BEST_FOR_BUSINESS` | Best flexible + direct + fast fit |
| `BEST_FOR_COMFORT` | Best cabin class + low stop count fit |
| `BEST_FOR_BUDGET` | Best price-weighted fit |
| `AVOID` | Match score below 0.35 |

Every option in a response gets exactly one of these — see `docs/FLIGHT_INTELLIGENCE_ENGINE.md` for the assignment algorithm.

## Conversation Shortcut

`POST /conversation/message` with a flight-related message (e.g. `"recommend flights to Tokyo"`) routes to the same Flight Intelligence engine and returns a composed natural-language summary referencing the top match — see `docs/CONVERSATION_ENGINE.md`.
