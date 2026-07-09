# Accommodation API

Base URL: `http://localhost:8000`

## Endpoints

### POST /accommodation/recommend

Generate ranked accommodation recommendations.

**Request body**

```json
{
  "traveller_id": "traveller_001",
  "trip_id": "uuid",
  "destination": "Tokyo",
  "check_in_date": "2026-09-15",
  "nights": 5,
  "accommodation_type": "HOTEL",
  "budget_style": "balanced",
  "adults": 1,
  "children": 0,
  "business_trip": false,
  "accessibility_required": false
}
```

All fields are optional except `destination`. If `trip_id` is provided, `destination`/`nights` are taken from the linked Trip Plan when present. If `check_in_date` is omitted, it defaults to 30 days from today and the response's `assumptions` records this.

**Response: 201 Created**

```json
{
  "traveller_id": null,
  "trip_id": null,
  "destination": "Tokyo",
  "accommodation_options": [
    {
      "accommodation_option_id": "uuid",
      "property_name": "Tokyo Guesthouse",
      "accommodation_type": "GUESTHOUSE",
      "star_rating": 3,
      "neighbourhood": "Local Quarter",
      "distance_to_centre": 1.2,
      "distance_to_transport": 0.6,
      "nightly_price": 45,
      "total_price": 225,
      "currency": "USD",
      "breakfast_included": true,
      "cancellation_policy": "free_cancellation",
      "accessibility_features": [],
      "family_friendly": true,
      "business_friendly": false,
      "review_score": 8.3,
      "safety_score": 0.76,
      "comfort_score": 0.62,
      "location_score": 0.71,
      "match_score": 0.82,
      "reasoning": "Tokyo Guesthouse (Guesthouse, 3-star, Local Quarter) scores 0.82. ...",
      "risks": [],
      "assumptions": ["No traveller profile — default budget and location assumptions applied."],
      "recommendation_type": "BEST_OVERALL"
    }
  ],
  "assumptions": [
    "Prices and availability are deterministic mock data — no live provider inventory was queried.",
    "Scoring assumes a 'balanced' budget style for a 5-night stay."
  ],
  "next_actions": [
    "Confirm exact check-in and check-out dates for accurate pricing.",
    "Compare cancellation policies before booking.",
    "Check neighbourhood safety advisories for the destination."
  ],
  "recommended_agents": ["hotel_agent"],
  "summary": "8 accommodation option(s) ranked for Tokyo. Best overall: Tokyo Guesthouse at USD 45/night (match 0.82). No live bookings have been made."
}
```

---

### GET /accommodation/{accommodation_option_id}

Retrieve a single accommodation option by ID.

**Response: 200 OK** — full `AccommodationOption` object, or **404** if not found.

---

### GET /trips/{trip_id}/accommodation

List all accommodation options previously recommended and linked to a trip.

**Response: 200 OK** — array of `AccommodationOption` objects (empty array if the trip has no saved options).

---

## Accommodation Types

| Type | Description |
|------|-------------|
| `HOTEL` | Standard hotel |
| `APARTMENT` | Self-catering apartment |
| `HOSTEL` | Budget shared/dorm accommodation |
| `VILLA` | Private standalone property |
| `RESORT` | Full-service leisure resort |
| `SERVICED_APARTMENT` | Business-oriented serviced apartment |
| `BOUTIQUE_HOTEL` | Small, design-led hotel |
| `GUESTHOUSE` | Local, homely accommodation |

## Recommendation Types

| Type | Meaning |
|------|---------|
| `BEST_OVERALL` | Highest match score |
| `BEST_VALUE` | Best price-to-quality ratio |
| `BEST_LOCATION` | Closest to centre and transport |
| `BEST_COMFORT` | Highest comfort score |
| `BEST_FOR_FAMILY` | Best family-friendly fit |
| `BEST_FOR_BUSINESS` | Best business-friendly fit |
| `BEST_BUDGET` | Best price-weighted fit |
| `AVOID` | Below the match threshold, or the relative weakest of the set |

Every option in a response gets exactly one of these — see `docs/DISCOVERY_LAYER_PATTERN.md` and `docs/ACCOMMODATION_INTELLIGENCE_ENGINE.md` for the assignment algorithm.

## Conversation Shortcut

`POST /conversation/message` with an accommodation-related message (e.g. `"find hotels in Tokyo"`, `"where to stay in Lisbon"`) routes to the same Accommodation Intelligence engine and returns a composed natural-language summary referencing the top match — see `docs/CONVERSATION_ENGINE.md`.
