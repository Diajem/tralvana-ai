# API Reference — Traveller Profile

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## POST /traveller/profile

Create a new Traveller Intelligence Profile.

### Request

```http
POST /traveller/profile
Content-Type: application/json
```

**Body**

```json
{
  "identity": {
    "name": "Peter Adeyemi",
    "email": "peter@example.com",
    "locale": "en-NG",
    "timezone": "Africa/Lagos"
  },
  "preferences": {
    "seat": "window",
    "cabin_class": "business",
    "meal": "halal",
    "accommodation_type": "hotel",
    "budget_tier": "mid"
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

**Field defaults** — `preferences` and `loyalty` are optional and default to sensible values if omitted.

### Response `201 Created`

```json
{
  "id": "a3f1c7d2-...",
  "created_at": "2026-07-07T10:30:00.000000+00:00",
  "updated_at": "2026-07-07T10:30:00.000000+00:00",
  "identity": {
    "name": "Peter Adeyemi",
    "email": "peter@example.com",
    "locale": "en-NG",
    "timezone": "Africa/Lagos"
  },
  "preferences": {
    "seat": "window",
    "cabin_class": "business",
    "meal": "halal",
    "accommodation_type": "hotel",
    "budget_tier": "mid"
  },
  "loyalty": {
    "airline_programs": [
      { "carrier": "LH", "number": "LH-123456" }
    ],
    "hotel_programs": [
      { "brand": "Marriott", "number": "MR-789012" }
    ]
  },
  "travel_history": []
}
```

### Error Responses

| Status | Meaning |
|--------|---------|
| `422 Unprocessable Entity` | Request body failed validation |

---

## GET /traveller/profile/{traveller_id}

Retrieve a profile by ID.

### Request

```http
GET /traveller/profile/a3f1c7d2-...
```

| Parameter | In | Type | Required |
|-----------|-----|------|----------|
| `traveller_id` | path | UUID string | Yes |

### Response `200 OK`

Same schema as the `POST` response above.

### Error Responses

| Status | Meaning |
|--------|---------|
| `404 Not Found` | No profile with that ID |

---

## Preference Field Reference

### `seat`
| Value | Meaning |
|-------|---------|
| `window` | Window seat |
| `aisle` | Aisle seat |
| `no_preference` | No preference (default) |

### `cabin_class`
| Value | Meaning |
|-------|---------|
| `economy` | Economy class (default) |
| `business` | Business class |
| `first` | First class |

### `meal`
| Value | Meaning |
|-------|---------|
| `standard` | Standard meal (default) |
| `vegetarian` | Vegetarian |
| `vegan` | Vegan |
| `halal` | Halal |
| `kosher` | Kosher |

### `accommodation_type`
| Value | Meaning |
|-------|---------|
| `hotel` | Hotel (default) |
| `apartment` | Serviced apartment |
| `hostel` | Hostel |
| `resort` | Resort |

### `budget_tier`
| Value | Meaning |
|-------|---------|
| `budget` | Budget tier |
| `mid` | Mid-range (default) |
| `luxury` | Luxury |

---

## Example — curl

```bash
# Create profile
curl -X POST http://localhost:8000/traveller/profile \
  -H "Content-Type: application/json" \
  -d '{
    "identity": {
      "name": "Peter Adeyemi",
      "email": "peter@example.com",
      "locale": "en-NG",
      "timezone": "Africa/Lagos"
    }
  }'

# Retrieve profile (replace ID)
curl http://localhost:8000/traveller/profile/a3f1c7d2-...
```

---

## Notes

- Profile IDs are UUIDs generated server-side on creation.
- Profiles are held in memory in Sprint 1; they are lost on server restart.
- No authentication is required in Sprint 1. Auth is added in Sprint 2.
- The `travel_history` array is append-only. Agents write to it; clients do not.
