# Traveller Intelligence Profile (TIP) — Specification

## Overview

The Traveller Intelligence Profile (TIP) is the primary domain object in TravelOS. It is the single source of truth for everything the system knows about a traveller — identity, travel style, comfort preferences, accessibility needs, loyalty memberships, and trip history.

Every agent decision, recommendation, and booking derives from or writes back to the TIP.

## Design Goals

1. **Complete** — captures the full picture of a traveller's identity and preferences.
2. **Agent-readable** — structured so any agent can extract exactly the fields it needs.
3. **Evolvable** — fields are additive; existing profiles remain valid when new fields are added.
4. **Privacy-safe** — sensitive fields (documents, payment) are never logged or included in default API responses.

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

---

### TravellerIdentity

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Full name |
| `email` | string | Primary contact email |
| `locale` | string | BCP 47 locale tag (e.g. `en-NG`) |
| `timezone` | string | IANA timezone (e.g. `Africa/Lagos`) |

---

### TravellerPreferences

#### Travel Basics

| Field | Type | Values | Default |
|-------|------|--------|---------|
| `home_airport` | string | IATA airport code (e.g. `LOS`) | `""` |
| `preferred_currency` | string | ISO 4217 code (e.g. `USD`, `NGN`) | `"USD"` |
| `preferred_language` | string | BCP 47 language code (e.g. `en`, `fr`) | `"en"` |
| `budget_style` | string | `backpacker`, `budget`, `balanced`, `comfort`, `luxury` | `"balanced"` |
| `travel_interests` | string[] | See **Travel Interests** below | `[]` |

**Travel Interests values:**
`beach`, `city`, `adventure`, `culture`, `food_drink`, `wellness`, `sport`, `nature`, `luxury`, `business`

#### Flight Preferences

| Field | Type | Values | Default |
|-------|------|--------|---------|
| `seat` | string | `window`, `aisle`, `no_preference` | `"no_preference"` |
| `cabin_class` | string | `economy`, `business`, `first` | `"economy"` |
| `meal` | string | `standard`, `vegetarian`, `vegan`, `halal`, `kosher` | `"standard"` |

#### Accommodation Preferences

| Field | Type | Values | Default |
|-------|------|--------|---------|
| `accommodation_type` | string | `hotel`, `apartment`, `hostel`, `resort` | `"hotel"` |
| `hotel_preferences` | string[] | See **Hotel Preferences** below | `[]` |

**Hotel Preferences values:**
`pool`, `gym`, `wifi`, `breakfast`, `spa`, `parking`, `pet_friendly`

#### Accessibility

| Field | Type | Values | Default |
|-------|------|--------|---------|
| `accessibility_needs` | string[] | See **Accessibility** below | `[]` |

**Accessibility values:**
`wheelchair_access`, `visual_assistance`, `hearing_assistance`, `extra_legroom`, `dietary_options`

---

### TravellerLoyalty

| Field | Type | Description |
|-------|------|-------------|
| `airline_programs` | AirlineLoyalty[] | Airline loyalty memberships |
| `hotel_programs` | HotelLoyalty[] | Hotel loyalty memberships |

**AirlineLoyalty:** `{ carrier: string, number: string }` — e.g. `{ carrier: "LH", number: "LH-123456" }`

**HotelLoyalty:** `{ brand: string, number: string }` — e.g. `{ brand: "Marriott", number: "MR-789" }`

---

### TripRecord (travel_history entries)

| Field | Type | Description |
|-------|------|-------------|
| `trip_id` | UUID | Unique trip identifier |
| `destination` | string | City name or IATA code |
| `dates.depart` | YYYY-MM-DD | Departure date |
| `dates.return` | YYYY-MM-DD | Return date |
| `status` | string | `planned`, `completed`, `cancelled` |

---

## Lifecycle

```
POST /traveller/profile
    │
    ▼
TravellerService.create_profile()
    │
    ▼
TravellerRepository._store[id] = profile
    │
    ▼
TravellerIntelligenceService.store_profile()  ← syncs to MemoryService
    │
    ▼
Orchestrator.run(agent_name, ..., traveller_id)
    │
    ▼
TravellerIntelligenceService.build_context_data()
    │  Enriches with: travel_style, preference_summary
    ▼
AgentContext.traveller_profile = enriched profile
    │
    ▼
Agent.run(input_data)  ← has full TIP + intelligence
```

---

## Enriched Intelligence Fields

`TravellerIntelligenceService` appends an `intelligence` block to every profile before injection into `AgentContext`:

```json
{
  "intelligence": {
    "travel_style": "comfort traveller",
    "preference_summary": {
      "name": "Peter Adeyemi",
      "home_airport": "LOS",
      "currency": "NGN",
      "language": "en",
      "budget_style": "comfort",
      "cabin_class": "business",
      "seat": "window",
      "meal": "halal",
      "accommodation": "hotel",
      "interests": ["city", "food_drink"],
      "hotel_preferences": ["wifi", "breakfast"],
      "accessibility": []
    }
  }
}
```

**Travel style inference:**

| Condition | Inferred style |
|-----------|---------------|
| `first` cabin OR `luxury` budget | `luxury traveller` |
| `business` cabin OR `comfort` budget + `business` interest | `business traveller` |
| `business` cabin OR `comfort` budget | `comfort traveller` |
| `backpacker` or `budget` budget | `budget traveller` |
| `adventure` or `nature` interest | `adventure traveller` |
| Default | `leisure traveller` |

---

## Sprint 1 Constraints

- **No persistence** — stored in process memory. Lost on server restart.
- **No documents** — passport fields deferred to Sprint 2.
- **No authentication** — profile ID is the only access control mechanism.
- **No PATCH** — full replacement only via POST + new ID.

## Planned Extensions (Sprint 2+)

| Field | Sprint | Notes |
|-------|--------|-------|
| `documents.passport_country` | 2 | ISO 3166-1 alpha-2 |
| `documents.passport_expiry` | 2 | YYYY-MM-DD |
| `travel_history` writes | 2 | Written by booking agents |
| `payment_methods` | 6 | Tokenised — never stored raw |
| `notification_preferences` | 3 | Push, email, SMS |
| PostgreSQL persistence | 2 | Swap `TravellerRepository` with a DB adapter |
