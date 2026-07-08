# Trips API

Base URL: `http://localhost:8000`

## Endpoints

### POST /trips/plan

Generate a draft trip plan.

**Request body**

```json
{
  "traveller_id": "traveller_001",
  "goal_id": "uuid",
  "origin": "London",
  "destination": "Tokyo",
  "duration_days": 7,
  "budget_style": "balanced",
  "cabin_class": "economy",
  "interests": ["food", "culture", "photography"],
  "travellers": { "adults": 2, "children": 0, "infants": 0 }
}
```

All fields are optional except `origin` (default: `"London"`). If `goal_id` is provided, fields from the Goal are merged in.

**Response: 201 Created**

```json
{
  "trip_id": "uuid",
  "title": "Food Tour — Tokyo (7 days)",
  "destination": "Tokyo",
  "duration_days": 7,
  "confidence": 0.80,
  "status": "READY",
  "trip_summary": "...",
  "draft_itinerary": [...],
  "estimated_budget_breakdown": { "total_estimate_usd": 4850 },
  "risks": [...],
  "assumptions": [...],
  "missing_information": [],
  "next_actions": [...],
  "recommended_agents": ["food_agent", "experience_agent", "hotel_agent"]
}
```

---

### GET /trips/{trip_id}

Retrieve a trip plan by ID.

**Response: 200 OK** — full `TripPlan` object, or **404** if not found.

---

### GET /traveller/{traveller_id}/trips

List all trips for a traveller.

**Response: 200 OK** — array of `TripPlan` objects.

---

### PATCH /trips/{trip_id}

Update a trip plan.

**Request body** (all optional)

```json
{
  "title": "Updated title",
  "destination": "Osaka",
  "duration_days": 10,
  "status": "ARCHIVED",
  "interests": ["food", "history"]
}
```

**Response: 200 OK** — updated `TripPlan`, or **404** if not found.

---

## Budget Styles

| Value | Daily Rate (USD) | Description |
|-------|-----------------|-------------|
| `backpacker` | ~$40/day | Hostels, street food |
| `budget` | ~$65/day | Budget hotels, local dining |
| `balanced` | ~$150/day | Mid-range hotels, mix of dining |
| `comfort` | ~$300/day | 4-star hotels, restaurants |
| `luxury` | ~$650/day | 5-star hotels, fine dining |

## Trip Statuses

| Status | Description |
|--------|-------------|
| `DRAFT` | Created, some context missing |
| `NEEDS_INFORMATION` | Key fields absent |
| `READY` | Confidence ≥ 65% |
| `ARCHIVED` | No longer active |
