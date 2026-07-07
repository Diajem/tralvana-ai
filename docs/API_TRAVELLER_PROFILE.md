# API Reference — Traveller Profile

Base URL: `http://localhost:8000`

Interactive docs (Swagger UI): `http://localhost:8000/docs`

---

## POST /traveller/profile

Create a new Traveller Intelligence Profile.

### Request

```http
POST /traveller/profile
Content-Type: application/json
```

**Full body (all fields)**

```json
{
  "identity": {
    "name": "Peter Adeyemi",
    "email": "peter@example.com",
    "locale": "en-NG",
    "timezone": "Africa/Lagos"
  },
  "preferences": {
    "home_airport": "LOS",
    "preferred_currency": "NGN",
    "preferred_language": "en",
    "budget_style": "comfort",
    "travel_interests": ["city", "food_drink", "business"],
    "seat": "window",
    "cabin_class": "business",
    "meal": "halal",
    "accommodation_type": "hotel",
    "hotel_preferences": ["wifi", "breakfast", "gym"],
    "accessibility_needs": []
  },
  "loyalty": {
    "airline_programs": [
      { "carrier": "LH", "number": "LH-123456" }
    ],
    "hotel_programs": [
      { "brand": "Marriott", "number": "MR-789012" }
    ]
  }
}
```

**Minimal body (required fields only)**

```json
{
  "identity": {
    "name": "Peter Adeyemi",
    "email": "peter@example.com"
  }
}
```

All `preferences` fields have defaults; `loyalty` programs default to empty lists.

### Response `201 Created`

```json
{
  "id": "a3f1c7d2-9e4b-4f1a-8c3d-2b5e6f7a8d9c",
  "created_at": "2026-07-07T10:30:00.000000+00:00",
  "updated_at": "2026-07-07T10:30:00.000000+00:00",
  "identity": {
    "name": "Peter Adeyemi",
    "email": "peter@example.com",
    "locale": "en-NG",
    "timezone": "Africa/Lagos"
  },
  "preferences": {
    "home_airport": "LOS",
    "preferred_currency": "NGN",
    "preferred_language": "en",
    "budget_style": "comfort",
    "travel_interests": ["city", "food_drink", "business"],
    "seat": "window",
    "cabin_class": "business",
    "meal": "halal",
    "accommodation_type": "hotel",
    "hotel_preferences": ["wifi", "breakfast", "gym"],
    "accessibility_needs": []
  },
  "loyalty": {
    "airline_programs": [{ "carrier": "LH", "number": "LH-123456" }],
    "hotel_programs": [{ "brand": "Marriott", "number": "MR-789012" }]
  },
  "travel_history": []
}
```

### Errors

| Status | Cause |
|--------|-------|
| `422 Unprocessable Entity` | Request body failed validation |

---

## GET /traveller/profile/{traveller_id}

Retrieve a saved profile by ID.

### Request

```http
GET /traveller/profile/a3f1c7d2-9e4b-4f1a-8c3d-2b5e6f7a8d9c
```

| Parameter | In | Type | Required |
|-----------|-----|------|----------|
| `traveller_id` | path | UUID string | Yes |

### Response `200 OK`

Same schema as the `POST` response.

### Errors

| Status | Cause |
|--------|-------|
| `404 Not Found` | No profile exists with that ID |

---

## Field Reference

### `budget_style`

| Value | Meaning |
|-------|---------|
| `backpacker` | Hostel, ground transport, self-catering |
| `budget` | Budget hotels, economy flights |
| `balanced` | Mid-range across all categories (default) |
| `comfort` | Business travel, 4-star hotels |
| `luxury` | First class, 5-star hotels, premium experiences |

### `travel_interests`

Multi-value string array. Accepted values:

`beach`, `city`, `adventure`, `culture`, `food_drink`, `wellness`, `sport`, `nature`, `luxury`, `business`

### `seat`

| Value | Meaning |
|-------|---------|
| `window` | Window seat |
| `aisle` | Aisle seat |
| `no_preference` | No preference (default) |

### `cabin_class`

| Value | Meaning |
|-------|---------|
| `economy` | Economy (default) |
| `business` | Business class |
| `first` | First class |

### `meal`

`standard` · `vegetarian` · `vegan` · `halal` · `kosher`

### `accommodation_type`

`hotel` · `apartment` · `hostel` · `resort`

### `hotel_preferences`

Multi-value string array: `pool`, `gym`, `wifi`, `breakfast`, `spa`, `parking`, `pet_friendly`

### `accessibility_needs`

Multi-value string array: `wheelchair_access`, `visual_assistance`, `hearing_assistance`, `extra_legroom`, `dietary_options`

---

## Example — curl

```bash
# Create profile (minimal)
curl -X POST http://localhost:8000/traveller/profile \
  -H "Content-Type: application/json" \
  -d '{"identity": {"name": "Peter Adeyemi", "email": "peter@example.com"}}'

# Create profile (full)
curl -X POST http://localhost:8000/traveller/profile \
  -H "Content-Type: application/json" \
  -d '{
    "identity": {"name": "Peter", "email": "peter@example.com", "locale": "en-NG", "timezone": "Africa/Lagos"},
    "preferences": {
      "home_airport": "LOS",
      "preferred_currency": "NGN",
      "budget_style": "comfort",
      "travel_interests": ["city", "business"],
      "cabin_class": "business",
      "meal": "halal",
      "hotel_preferences": ["wifi", "breakfast"]
    }
  }'

# Retrieve profile (replace ID)
curl http://localhost:8000/traveller/profile/a3f1c7d2-9e4b-4f1a-8c3d-2b5e6f7a8d9c
```

---

## Notes

- Profile IDs are UUIDs generated server-side. Store the `id` from the POST response.
- Profiles are held in process memory in Sprint 1 and are lost on server restart.
- No authentication is required in Sprint 1. Sprint 2 adds JWT-based auth.
- `travel_history` is append-only. Agents write to it; the create endpoint does not.
- Preference arrays (`travel_interests`, `hotel_preferences`, `accessibility_needs`) accept any subset of the listed values.
