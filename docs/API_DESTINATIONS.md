# Destinations API

Base URL: `http://localhost:8000`

## Endpoints

### POST /destinations/recommend

Generate ranked destination recommendations. Omit `city` to compare cities across the whole catalogue; provide it to explore neighbourhoods, food areas, and attractions within that city.

**Request body**

```json
{
  "traveller_id": "traveller_001",
  "trip_id": "uuid",
  "city": "Tokyo",
  "interests": ["food", "culture"],
  "goal_type": "FOOD_TOUR",
  "budget_style": "balanced",
  "travel_month": 10,
  "trip_duration_days": 7,
  "children": 0
}
```

All fields are optional. If `trip_id` is provided, `city`/`interests`/`trip_duration_days` are taken from the linked Trip Plan when present. If `city` is omitted entirely, the response contains one option per city in the catalogue. If `city` is not in the mock catalogue (`Tokyo`, `Osaka`, `Barcelona`, `Paris`, `London`, `New York`, `Lagos`, `Accra`, `Kingston`, `Dubai`), `destination_options` is empty and `assumptions` explains why.

**Response: 201 Created**

```json
{
  "traveller_id": null,
  "trip_id": null,
  "city": "Tokyo",
  "destination_options": [
    {
      "destination_option_id": "uuid",
      "city": "Tokyo",
      "country": "Japan",
      "region": "Asia",
      "neighbourhood": "Tokyo National Museum",
      "destination_type": "MUSEUM",
      "name": "Tokyo National Museum",
      "description": "Japan's oldest and largest museum of art and antiquities.",
      "best_for": ["art", "Japanese history"],
      "interests_matched": ["culture"],
      "distance_from_centre": 4.0,
      "transport_access_score": 0.75,
      "food_score": 0.48,
      "culture_score": 1.0,
      "football_score": 0.12,
      "nightlife_score": 0.3,
      "family_score": 0.5,
      "safety_score": 0.92,
      "budget_score": 0.4,
      "season_score": 0.6,
      "match_score": 0.77,
      "reasoning": "Tokyo National Museum (Museum, Tokyo, Japan) scores 0.77. ...",
      "risks": [],
      "assumptions": ["No traveller profile — default interest and budget assumptions applied."],
      "recommendation_type": "BEST_OVERALL"
    }
  ],
  "assumptions": [
    "No travel month supplied — season fit uses a neutral baseline.",
    "Destination data is a deterministic mock catalogue — no live maps or places provider was queried."
  ],
  "next_actions": [
    "Confirm opening hours and any booking requirements before visiting.",
    "Check current safety advisories for the destination.",
    "Destination data has not been checked live — details are indicative only."
  ],
  "recommended_agents": ["experience_agent"],
  "summary": "5 destination option(s) ranked within Tokyo. Best overall: Tokyo National Museum (match 0.77). No live bookings have been made."
}
```

---

### GET /destinations/{destination_option_id}

Retrieve a single destination option by ID.

**Response: 200 OK** — full `DestinationOption` object, or **404** if not found.

---

### GET /trips/{trip_id}/destinations

List all destination options previously recommended and linked to a trip.

**Response: 200 OK** — array of `DestinationOption` objects (empty array if the trip has no saved options).

---

## Destination Types

| Type | Description |
|------|-------------|
| `CITY` | Top-level city overview |
| `NEIGHBOURHOOD` | A specific area within a city |
| `ATTRACTION` | A standout sight or landmark |
| `MUSEUM` | Museums and galleries |
| `FOOD_DISTRICT` | Markets, street food strips, food halls |
| `FOOTBALL_VENUE` | Stadiums and football culture sites |
| `SHOPPING_DISTRICT` | Malls, markets, shopping streets |
| `BEACH` | Beaches and waterfront areas |
| `NATURE_AREA` | Parks and green spaces |
| `HISTORIC_SITE` | Heritage and historical sites |
| `TRANSPORT_HUB` | Major stations and transit gateways |
| `NIGHTLIFE_AREA` | Bars, clubs, and evening entertainment |

## Recommendation Types

| Type | Meaning |
|------|---------|
| `BEST_OVERALL` | Highest match score |
| `BEST_FOR_FOOD` | Best food relevance |
| `BEST_FOR_FOOTBALL` | Best football relevance |
| `BEST_FOR_CULTURE` | Best culture relevance |
| `BEST_FOR_FAMILY` | Best family suitability |
| `BEST_FOR_BUDGET` | Best affordability |
| `BEST_FOR_PHOTOGRAPHY` | Best photography suitability |
| `BEST_HIDDEN_GEM` | Least mainstream, most under-the-radar |
| `AVOID` | Below the match threshold, or the relative weakest of the set |

A persona only claims one of these labels if genuinely relevant (`persona_score >= 0.45`) — see `docs/DESTINATION_INTELLIGENCE_ENGINE.md` for why, and `docs/DISCOVERY_LAYER_PATTERN.md` for the general assignment algorithm.

## Conversation Shortcut

`POST /conversation/message` with a destination-discovery message (e.g. `"where should i go"`, `"things to do in Tokyo"`) routes to the same Destination Intelligence engine and returns a composed natural-language summary referencing the top match — see `docs/CONVERSATION_ENGINE.md`.
