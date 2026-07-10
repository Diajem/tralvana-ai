# Visa API

Base URL: `http://localhost:8000`

**This is explainable travel-planning intelligence, not legal advice.** Always verify with an official government source before travelling.

## Endpoints

### POST /visa/check

Generate a single visa/entry-requirement assessment for a passport/destination/purpose combination.

**Request body**

```json
{
  "traveller_id": "traveller_001",
  "trip_id": "uuid",
  "nationality": "British",
  "passport_country": "UK",
  "destination_country": "Japan",
  "transit_countries": [],
  "travel_purpose": "TOURISM",
  "intended_length_of_stay": 14,
  "passport_expiry_date": "2027-06-01"
}
```

Only `passport_country` and `destination_country` are required. `nationality` defaults to `passport_country` if omitted. `passport_country`/`destination_country`/`nationality` accept country names, ISO 3166-1 alpha-2 codes, or common nationality adjectives (`"Nigeria"`, `"NG"`, and `"Nigerian"` all resolve the same way). If `passport_expiry_date` is omitted, `passport_validity_months` cannot be computed and an assumption/risk explains why.

**Response: 201 Created**

```json
{
  "visa_assessment_id": "uuid",
  "traveller_id": null,
  "trip_id": null,
  "nationality": "United Kingdom",
  "passport_country": "United Kingdom",
  "destination_country": "Japan",
  "transit_countries": [],
  "travel_purpose": "TOURISM",
  "intended_length_of_stay": 14,
  "passport_expiry_date": "2027-06-01",
  "passport_validity_months": 10.7,
  "visa_status": "VISA_NOT_REQUIRED",
  "visa_required": false,
  "visa_type": "None",
  "entry_requirements": [
    "Valid passport",
    "Proof of onward or return travel",
    "Proof of sufficient funds for the trip"
  ],
  "supporting_documents": ["Passport", "Travel insurance"],
  "vaccination_requirements": [],
  "travel_authorisation_required": false,
  "processing_time": "Not applicable",
  "confidence": 0.9,
  "risks": [],
  "assumptions": [
    "Visa data is a deterministic mock rule set — no live government, embassy, or Timatic-style data was queried. This is not legal advice."
  ],
  "recommendation": "No visa action needed for this trip.",
  "explanation": "As a United Kingdom passport holder travelling to Japan for tourism, no visa is required. This covers stays of up to 90 days. 10.7 month(s) of passport validity remain — meets the common 6-month rule. No transit countries specified — this assumes direct routing. No visa application is needed for this trip.",
  "created_at": "2026-07-10T12:00:00+00:00"
}
```

---

### GET /visa/{visa_assessment_id}

Retrieve a single visa assessment by ID.

**Response: 200 OK** — full `VisaAssessment` object, or **404** if not found.

---

### GET /trips/{trip_id}/visa

List all visa assessments previously checked and linked to a trip (e.g. one per traveller, or one per leg of a multi-country itinerary).

**Response: 200 OK** — array of `VisaAssessment` objects (empty array if the trip has no saved assessments).

---

## Mock Rule Coverage

| | |
|---|---|
| Nationalities | UK, Ireland, USA, Canada, Nigeria, Ghana, South Africa, Jamaica, EU (generic), Japan |
| Destinations | Japan, USA, UK, Ireland, France, Spain, Nigeria, UAE |

Any nationality or destination outside these lists returns `CHECK_MANUALLY` with a lower `confidence` and an `assumptions` entry explaining the fallback — see `docs/VISA_INTELLIGENCE_ENGINE.md`.

## Visa Status

| Status | Meaning |
|--------|---------|
| `VISA_NOT_REQUIRED` | No visa or authorisation needed for this stay |
| `VISA_REQUIRED` | A traditional visa must be obtained before travel |
| `ETA_REQUIRED` | An Electronic Travel Authorisation is required (e.g. ESTA, UK ETA) |
| `EVISA_AVAILABLE` | An e-Visa can be obtained online before travel |
| `CHECK_MANUALLY` | No reliable rule available — contact the destination's embassy or consulate |
| `ENTRY_RESTRICTED` | Entry may be restricted — supported by the schema, not emitted by the current mock data set |

## Travel Purpose

`TOURISM`, `BUSINESS`, `TRANSIT`, `STUDY`, `WORK`, `FAMILY_VISIT`, `OTHER`. `STUDY` and `WORK` always require a proper visa regardless of passport tier — tourism-oriented waivers never cover them.

## Conversation Shortcut

`POST /conversation/message` with a visa-related message (e.g. `"Do I need a visa?"`, `"Can I enter Japan?"`, `"Will my Irish passport work?"`, `"I am Nigerian travelling to Spain."`) routes to the same Visa Intelligence engine and returns a composed natural-language summary — see `docs/CONVERSATION_ENGINE.md`. Both nationality and destination are required; if either is missing, the response asks for it instead of guessing.
