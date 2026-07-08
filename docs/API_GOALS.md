# Goals API

The Goals API manages travel goal lifecycle — from creation to trip planning readiness.

**Base URL:** `http://localhost:8000`

---

## POST /goals

Create a new travel goal.

**Request body:**

```json
{
  "traveller_id": "string (required)",
  "title": "Summer holiday in Barcelona",
  "goal_type": "RELAXATION",
  "priority": 3,
  "budget": {
    "min_usd": 2000,
    "max_usd": 5000,
    "currency": "USD"
  },
  "timeframe": {
    "earliest": "2026-08-01",
    "latest": "2026-08-31",
    "duration_days": 10,
    "flexible": true
  },
  "travellers": {
    "adults": 2,
    "children": 0,
    "infants": 0
  },
  "interests": ["beach", "food_drink", "culture"],
  "constraints": ["Must be halal-friendly"],
  "success_criteria": ["See Sagrada Família", "Eat at a Michelin restaurant"],
  "flexibility": {
    "dates": true,
    "duration": true,
    "budget": false
  }
}
```

**Response:** `201 Created`

```json
{
  "goal_id": "3f4a1b2c-...",
  "traveller_id": "...",
  "title": "Summer holiday in Barcelona",
  "goal_type": "RELAXATION",
  "priority": 3,
  "budget": { "min_usd": 2000, "max_usd": 5000, "currency": "USD" },
  "timeframe": { "earliest": "2026-08-01", "latest": "2026-08-31", "duration_days": 10, "flexible": true },
  "travellers": { "adults": 2, "children": 0, "infants": 0 },
  "interests": ["beach", "food_drink", "culture"],
  "constraints": ["Must be halal-friendly"],
  "success_criteria": ["See Sagrada Família", "Eat at a Michelin restaurant"],
  "flexibility": { "dates": true, "duration": true, "budget": false },
  "status": "DRAFT",
  "created_at": "2026-07-08T10:00:00Z",
  "updated_at": "2026-07-08T10:00:00Z"
}
```

---

## GET /goals/{goal_id}

Retrieve a goal by ID.

**Response:** `200 OK` — same shape as POST response.

**Error:** `404 Not Found` if the goal does not exist.

---

## GET /traveller/{traveller_id}/goals

List all goals for a traveller.

**Response:** `200 OK`

```json
[
  { ...goal object... },
  { ...goal object... }
]
```

Returns an empty list `[]` if the traveller has no goals.

---

## PATCH /goals/{goal_id}

Update one or more fields of an existing goal. All fields are optional.

**Request body (partial update):**

```json
{
  "budget": { "min_usd": 3000, "max_usd": 6000, "currency": "USD" },
  "status": "ACTIVE"
}
```

**Response:** `200 OK` — full updated goal object.

Status is also automatically promoted based on readiness score:
- Score ≥ 75% → `ACTIVE`
- Score ≥ 90% → `READY_FOR_PLANNING`

**Error:** `404 Not Found` if the goal does not exist.

---

## Goal Type Values

`RELAXATION` | `ADVENTURE` | `FOOTBALL_TRAVEL` | `FAMILY_TRIP` | `BUSINESS_TRAVEL` | `FOOD_TOUR` | `PHOTOGRAPHY` | `PILGRIMAGE` | `DIASPORA_TRAVEL` | `ROMANTIC_TRIP` | `GENERAL_TRAVEL`

## Goal Status Values

`DRAFT` | `ACTIVE` | `READY_FOR_PLANNING` | `PLANNED` | `ARCHIVED`

---

## Conversation Integration

When a `PLAN_TRIP` intent is detected via `POST /conversation/message`, the response includes a `goal_id` field if a Goal was automatically created:

```json
{
  "conversation_id": "...",
  "intent": "PLAN_TRIP",
  "response": "I'd love to help you plan a trip...",
  "goal_id": "3f4a1b2c-..."
}
```

The client can then redirect to `/goals/{goal_id}` to view or enrich the goal.
