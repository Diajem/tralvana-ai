# Traveller Profile Schema

Defines the structure of a traveller's persistent profile stored in memory.

## Schema

```json
{
  "traveller_id": "string (UUID)",
  "created_at": "ISO 8601 datetime",
  "updated_at": "ISO 8601 datetime",

  "identity": {
    "name": "string",
    "email": "string",
    "locale": "string (e.g. en-NG)",
    "timezone": "string (e.g. Africa/Lagos)"
  },

  "preferences": {
    "seat": "window | aisle | no_preference",
    "cabin_class": "economy | business | first",
    "meal": "standard | vegetarian | vegan | halal | kosher",
    "accommodation_type": "hotel | hostel | apartment | resort",
    "budget_tier": "budget | mid | luxury"
  },

  "travel_history": [
    {
      "trip_id": "string (UUID)",
      "destination": "string",
      "dates": {
        "depart": "YYYY-MM-DD",
        "return": "YYYY-MM-DD"
      },
      "status": "planned | completed | cancelled"
    }
  ],

  "loyalty": {
    "airline_programs": [
      { "carrier": "string", "number": "string" }
    ],
    "hotel_programs": [
      { "brand": "string", "number": "string" }
    ]
  },

  "documents": {
    "passport_country": "ISO 3166-1 alpha-2",
    "passport_expiry": "YYYY-MM-DD"
  }
}
```

## Notes

- `traveller_id` is the primary key — all session data links back to it.
- `travel_history` is append-only; do not mutate past entries.
- `documents` fields are sensitive — do not log or expose in API responses.
- Schema evolves with sprints; bump `updated_at` on every write.
