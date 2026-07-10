# Weather API

Base URL: `http://localhost:8000`

**This is a travel decision engine, not a weather forecast.** Always check an official forecast closer to your travel date.

## Endpoints

### POST /weather/analyse

Generate a single weather/safety assessment for a destination, optionally for a specific month.

**Request body**

```json
{
  "traveller_id": "traveller_001",
  "trip_id": "uuid",
  "destination": "Japan",
  "month_of_travel": 4,
  "goal_type": "PHOTOGRAPHY"
}
```

Only `destination` is required. `month_of_travel` (1-12) is optional — when omitted, the engine scores all 12 months internally and returns an assessment for the best one, recording an assumption explaining the substitution.

**Response: 201 Created**

```json
{
  "weather_assessment_id": "uuid",
  "traveller_id": null,
  "trip_id": null,
  "destination": "Japan",
  "month_of_travel": 4,
  "season": "SPRING",
  "average_temperature": 15,
  "rainfall_level": "MODERATE",
  "humidity_level": "MODERATE",
  "daylight_hours": 12.5,
  "weather_summary": "Spring, around 15°C, moderate rainfall, moderate humidity.",
  "weather_suitability_score": 0.79,
  "outdoor_activity_score": 0.76,
  "photography_score": 0.73,
  "family_score": 0.81,
  "transport_disruption_risk": "LOW",
  "natural_hazard_risk": "LOW",
  "health_risk": "LOW",
  "personal_suitability": "This is a good match for your travel style.",
  "packing_recommendations": [
    "Standard travel clothing — no significant weather extremes this month"
  ],
  "safety_summary": "No significant weather-related safety concerns this month.",
  "risks": [],
  "assumptions": [
    "No traveller profile linked — scoring uses default preferences only.",
    "Weather and safety data are deterministic mock climate profiles — no live forecast or advisory service was queried. This is a travel decision aid, not a forecast."
  ],
  "confidence": 0.9,
  "weather_status": "GOOD",
  "alternative_months": [],
  "recommendation": "A good time to visit — minor trade-offs, nothing that should change your plans.",
  "explanation": "Japan in April (Spring) scores 0.79 for this trip. Average temperature is around 15°C. Good light and clarity for photography this month. Well suited to travelling with children. This is a good match for your travel style.",
  "created_at": "2026-07-10T12:00:00+00:00"
}
```

---

### GET /weather/{weather_assessment_id}

Retrieve a single weather assessment by ID.

**Response: 200 OK** — full `WeatherAssessment` object, or **404** if not found.

---

### GET /trips/{trip_id}/weather

List all weather assessments previously analysed and linked to a trip.

**Response: 200 OK** — array of `WeatherAssessment` objects (empty array if the trip has no saved assessments).

---

## Mock Climate Coverage

Japan, Spain, France, United Kingdom, Ireland, USA, Nigeria, Ghana, Jamaica, UAE — accepted by full name, common abbreviation (`UK`, `USA`, `UAE`), or a handful of long-form aliases (`"United Kingdom"`, `"United States"`, `"United Arab Emirates"`). Any other destination returns a neutral, low-confidence assessment with an `assumptions` entry explaining the fallback — see `docs/WEATHER_INTELLIGENCE_ENGINE.md`.

## Weather Status

| Status | Score threshold | Meaning |
|--------|------------------|---------|
| `EXCELLENT` | ≥ 0.85 | Ideal conditions for this trip |
| `GOOD` | ≥ 0.65 | Minor trade-offs only |
| `ACCEPTABLE` | ≥ 0.45 | Workable, with real trade-offs |
| `CHALLENGING` | ≥ 0.25 | Significant trade-offs — consider alternatives |
| `NOT_RECOMMENDED` | < 0.25 | Significant weather or safety concerns |

## Rainfall / Humidity Levels

`LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`.

## Risk Levels

`transport_disruption_risk`, `natural_hazard_risk`, `health_risk` are each one of `LOW`, `MODERATE`, `HIGH`, `SEVERE`.

## Conversation Shortcut

`POST /conversation/message` with a weather-related message (e.g. `"Is July a good time to visit Japan?"`, `"When should I visit Spain?"`, `"Will it rain in Jamaica in September?"`, `"Should I avoid hurricane season?"`) routes to the same Weather Intelligence engine and returns a composed natural-language summary — see `docs/CONVERSATION_ENGINE.md`. Only a destination is required; if missing, the response asks for it instead of guessing. A month is never required — the response defaults to the best month to visit.
