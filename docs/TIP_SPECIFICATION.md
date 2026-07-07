# Traveller Intelligence Profile (TIP) — Specification

## Overview

The Traveller Intelligence Profile (TIP) is the primary domain object in TravelOS. It is the single source of truth for everything the system knows about a traveller. Every agent decision, recommendation, and booking is derived from or written back to the TIP.

## Design Goals

1. **Complete** — captures identity, preferences, loyalty, history, and documents in one place.
2. **Agent-readable** — structured so any agent can extract the fields it needs without parsing prose.
3. **Evolvable** — fields can be added without breaking existing profiles.
4. **Privacy-safe** — sensitive fields (documents, payment) are never logged or returned in default API responses.

---

## Data Model

### Top-Level Structure

```
TravellerProfile
├── id               UUID — primary key
├── created_at       ISO 8601 UTC
├── updated_at       ISO 8601 UTC
├── identity         TravellerIdentity
├── preferences      TravellerPreferences
├── loyalty          TravellerLoyalty
└── travel_history   TripRecord[]
```

### TravellerIdentity

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Full name |
| `email` | string | Primary contact email |
| `locale` | string | BCP 47 locale tag (e.g. `en-NG`) |
| `timezone` | string | IANA timezone (e.g. `Africa/Lagos`) |

### TravellerPreferences

| Field | Type | Values | Default |
|-------|------|--------|---------|
| `seat` | string | `window`, `aisle`, `no_preference` | `no_preference` |
| `cabin_class` | string | `economy`, `business`, `first` | `economy` |
| `meal` | string | `standard`, `vegetarian`, `vegan`, `halal`, `kosher` | `standard` |
| `accommodation_type` | string | `hotel`, `apartment`, `hostel`, `resort` | `hotel` |
| `budget_tier` | string | `budget`, `mid`, `luxury` | `mid` |

### TravellerLoyalty

| Field | Type | Description |
|-------|------|-------------|
| `airline_programs` | AirlineLoyalty[] | List of airline loyalty memberships |
| `hotel_programs` | HotelLoyalty[] | List of hotel loyalty memberships |

**AirlineLoyalty:** `{ carrier: string, number: string }`
**HotelLoyalty:** `{ brand: string, number: string }`

### TripRecord (travel_history entries)

| Field | Type | Description |
|-------|------|-------------|
| `trip_id` | UUID | Unique trip identifier |
| `destination` | string | City or IATA code |
| `dates.depart` | YYYY-MM-DD | Departure date |
| `dates.return` | YYYY-MM-DD | Return date |
| `status` | string | `planned`, `completed`, `cancelled` |

---

## Lifecycle

```
Create (POST /traveller/profile)
    │
    ▼
Profile stored in TravellerRepository
    │
    ▼
Profile synced to MemoryService (agent layer)
    │
    ▼
AgentContext.traveller_profile populated on every agent run
    │
    ▼
(Sprint 2) Agents write trip results back to travel_history
```

---

## Sprint 1 Constraints

- **No persistence** — stored in-memory. Lost on server restart.
- **No documents** — passport fields deferred to Sprint 2.
- **No authentication** — profile ID is the only access control.
- **No partial updates** — no PATCH endpoint; full replacement only.

## Planned Extensions (Sprint 2+)

| Field | Sprint | Notes |
|-------|--------|-------|
| `documents.passport_country` | 2 | ISO 3166-1 alpha-2 |
| `documents.passport_expiry` | 2 | YYYY-MM-DD |
| `travel_history` writes | 2 | Written by agents after booking |
| `payment_methods` | 6 | Tokenised, never stored raw |
| `notification_preferences` | 3 | Push, email, SMS |

---

## Agent Integration

The TIP is injected into `AgentContext.traveller_profile` before every agent run:

```python
context = AgentContext(
    session_id="...",
    traveller_id="...",
    traveller_profile={
        "identity": {"name": "Peter", "cabin_class": "business", ...},
        "preferences": {...},
        "loyalty": {...},
    }
)
```

Agents access it via `self.context.traveller_profile`. If no `traveller_id` is supplied, `traveller_profile` is `None` and agents fall back to defaults.
