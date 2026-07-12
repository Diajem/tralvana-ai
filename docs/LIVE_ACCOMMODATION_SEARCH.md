# Live Accommodation Search (T-039)

Connects the existing Accommodation Intelligence Engine to real Duffel
Stays sandbox data through the Intelligence Gateway and Live Provider
Framework — the same pattern T-038 established for flights, adapted
for accommodation's real differences (destination resolution, a
Normalizer stage, richer field mapping). **Search and recommendation
only.** No booking, payment, reservation creation, cancellation, or
modification exists anywhere in this feature.

See `docs/DUFFEL_STAYS_INTEGRATION.md` for the adapter's technical
design and `docs/ADR/ADR-025-duffel-stays-integration.md` for the
decisions behind it.

## Status: Access Not Yet Enabled

**The existing `DUFFEL_API_TOKEN` (used for Flights sandbox testing
since T-027) does not have Duffel Stays access.** Confirmed against the
real API during this task: `POST /stays/search` returns HTTP 403,
`"This feature is not enabled for your account. Please contact sales
to get access: https://duffel.com/contact-us"`. The adapter is fully
built, fully unit-tested against documented Duffel-shaped fixtures, and
the manual verification script runs successfully — it just correctly
reports this access blocker instead of live results. See
`docs/DUFFEL_STAYS_INTEGRATION.md`'s Access Requirement section.

## Architecture

```
Accommodation Search UI (apps/web/src/app/accommodation/recommend)
  -> POST /accommodation/recommend (services/api/app/domains/accommodation/router.py)
    -> AccommodationIntelligenceService (services/api/app/domains/accommodation/service.py)
      -> [LIVE_SANDBOX only] validate_live_accommodation_search() — before any provider call
      -> AccommodationIntelligence.recommend() (ai/discovery/accommodation/accommodation_intelligence.py)
        -> GatewayAccommodationProvider.search() (travelos/intelligence_gateway/discovery_adapters.py)
          -> IntelligenceGateway.execute(ACCOMMODATION, ...) — per-capability environment resolution
            -> DuffelStaysProvider (SANDBOX) or mock_accommodation_provider (MOCK)
              -> HttpxTransport -> Duffel Places API (destination resolution) -> Duffel Stays Search API (live mode only)
        -> raw, Duffel-vocabulary dicts -> AccommodationNormalizer (extended, T-039)
        -> AccommodationScorer -> AccommodationReasoner -> AccommodationRiskAssessor -> ranked, labelled results
      -> data_source / provider_status / retrieved_at / request_id / *_results_count attached
    -> AccommodationRecommendationResponse (existing shape, additively extended)
```

No new endpoint. `POST /accommodation/recommend` and `GET /accommodation/{id}`
are unchanged in shape and continue to work exactly as before in `MOCK`
mode (the default) — every existing test and caller is unaffected.

## Switching Between MOCK and LIVE_SANDBOX

One environment variable, read by `ConfigurationManager.accommodation_provider_mode`:

```bash
TRALVANA_ACCOMMODATION_PROVIDER_MODE=MOCK          # default — no change from before T-039
TRALVANA_ACCOMMODATION_PROVIDER_MODE=LIVE_SANDBOX  # requires DUFFEL_API_TOKEN AND Stays account access
```

- **Never inferred from `DUFFEL_API_TOKEN`'s presence.** Independent of
  `TRALVANA_FLIGHT_PROVIDER_MODE` (T-038) — enabling one never enables
  the other.
- **Restart required** — `configure_accommodation_provider()`
  (`travelos/live_providers/accommodation_provider_bootstrap.py`) runs
  once at application startup.
- **Scoped to ACCOMMODATION only.** `IntelligenceGateway._environment_for(capability)`
  now resolves both FLIGHTS (T-038) and ACCOMMODATION (T-039) from
  their own dedicated switches via a small capability→config-attribute
  map (`travelos/intelligence_gateway/gateway.py`'s
  `_CAPABILITY_MODE_CONFIG_ATTR`) — Weather still resolves from the
  general `PROVIDER_ENVIRONMENT`, untouched.
- **Even with the mode set and the token present, a live search can
  still fail with a clear 503** if Duffel Stays itself isn't enabled on
  the account — see "Status: Access Not Yet Enabled" above. That is a
  per-request provider failure, not a startup misconfiguration, since a
  valid Flights token doesn't imply Stays access.

## Request Validation (LIVE_SANDBOX only)

`ai/discovery/accommodation/live_search_validator.py`'s
`validate_live_accommodation_search()`, called before any Duffel call:

- `destination`: required, non-empty
- `check_in_date`: `YYYY-MM-DD`, required, not in the past
- `nights`: 1–99 (Duffel's own documented maximum stay length)
- `adults`: 1–9
- `rooms`: 1–8

Every problem found is collected and returned together as a `422` with
`{"detail": {"errors": [...]}}`. **Deliberately MOCK-mode-exempt** —
`MockAccommodationProvider` has never validated its inputs this
strictly, and `MOCK` mode's public API behaviour must stay
byte-identical to before T-039.

## Destination Resolution

Duffel Stays' location-based search requires geographic coordinates +
a radius, not a place name — but `AccommodationIntelligence` only ever
has a destination *string* ("Tokyo"). `DuffelStaysProvider` resolves
this internally via Duffel's own Places API
(`GET /places/suggestions`), entirely self-contained: no Duffel place
ID or coordinate ever reaches `ai/discovery/accommodation/` or any
Tralvana domain model.

**A real finding from this task's live verification**: querying
"Tokyo" returns a `city`-type place with `latitude`/`longitude` both
`null`, alongside `airport`-type places that do carry coordinates.
`_resolve_destination()` originally assumed the first city match would
have coordinates — fixed to prefer the first *geocoded* place (city
type first, any type otherwise), confirmed against the real API. See
`docs/DUFFEL_STAYS_INTEGRATION.md`'s Destination Resolution section.

## Response Mapping — What Duffel Provides vs. What's Approximated

`AccommodationNormalizer` gained a second raw-record vocabulary it
absorbs (`_normalize_duffel_stays()`), alongside its original
mock-provider branch, unchanged. Full field-by-field detail is in
`docs/DUFFEL_STAYS_INTEGRATION.md`; the short version — **nothing is
fabricated, every default is documented**:

| Canonical field | Source |
|---|---|
| `property_name`, `nightly_price`, `total_price`, `currency` | Direct from Duffel |
| `star_rating`, `review_score` | Direct from Duffel (`rating`, `review_score`), defaulted (0, 5.0) only when Duffel itself returns null |
| `distance_to_centre` | **Computed** via the haversine formula between the search's resolved coordinates and the property's — real geometry, not a Duffel-provided figure |
| `distance_to_transport` | **Approximated as equal to `distance_to_centre`** — Duffel has no transit-distance data anywhere in its documented schema |
| `breakfast_included` | Derived from the cheapest rate's `board_type` |
| `cancellation_policy` | Derived from `cancellation_timeline`'s refund amounts vs. total price (Duffel's own documented semantics) |
| `accessibility_features` | Keyword-matched against Duffel's own `amenities` list (best-effort — Duffel's amenity vocabulary isn't publicly documented with concrete values) |
| `safety_score` | **Always neutral (0.5)** — no safety signal exists anywhere in Duffel's schema |
| `accommodation_type` | **Always defaults to `HOTEL`** — Duffel's schema has no property-type classification field |
| `comfort_score` | Recomputed using `review_score` in place of the mock's `cleanliness_rating` (which Duffel doesn't provide) |

## Public API Additions

`POST /accommodation/recommend`'s response gains additive fields (all
have defaults — not a breaking change):

| Field | Meaning |
|---|---|
| `data_source` | `MOCK` \| `DUFFEL_STAYS_SANDBOX` \| `MOCK_FALLBACK` |
| `provider_status` | The `ProviderStatus` the Intelligence Gateway reported |
| `retrieved_at` | ISO timestamp the result was retrieved |
| `request_id` | The Intelligence Gateway's request id for this call |
| `raw_results_count` | Properties Duffel itself returned, before any mapping |
| `normalised_results_count` | Properties that survived `DuffelStaysProvider`'s own per-result mapping (partial mapping failure, see below) |
| `ranked_results_count` | `len(accommodation_options)` |

Each `AccommodationOptionResponse` also gains `data_source` (same
values) so a single option fetched later via `GET /accommodation/{id}`
still carries its own sandbox/mock label.

**Never exposed, anywhere:** the Duffel bearer token, any outbound
request header, the raw Duffel JSON payload, or Duffel's own internal
property/rate IDs. Those are preserved *internally only*
(`AccommodationOption.provider_property_id`/`provider_rate_id`,
excluded from `to_dict()`'s public shape) for future booking-readiness
work — no booking flow reads them yet.

## Failure and Fallback Behaviour

Same policy as T-038's flights implementation: `MOCK` mode never
contacts Duffel; a `LIVE_SANDBOX` failure (auth, timeout, rate limit,
malformed response, unresolvable destination, or — as confirmed in this
task — account-not-enabled) returns a `503` by default; setting
`TRALVANA_ACCOMMODATION_MOCK_FALLBACK_ENABLED=true` falls back to
clearly-labelled mock data instead; mock and live properties are never
blended in one ranked result set. A batch of malformed Duffel search
results has the same partial-mapping-failure tolerance flights'
adapter has — one bad result is skipped and counted, not treated as a
whole-response failure.

## Manual Live Verification

```bash
python scripts/verify_duffel_stays_live_sandbox.py
```

Reads `DUFFEL_API_TOKEN` from `.env`, runs one real search through the
full architecture above, prints only safe diagnostics (HTTP status,
provider status, `data_source`, raw/normalised/ranked counts, request
id) — never the token or the full payload. Currently reports the
403 access-not-enabled blocker (see "Status" above), which is itself
the correct, expected, documented outcome until Stays access is
requested. Never run in CI or as part of `pytest`.

## What Remains Before Production and Booking

1. **Duffel Stays account access.** Someone with authority over the
   Duffel account must request Stays access
   (`https://duffel.com/contact-us`, per the 403's own message) before
   any real sandbox data can be returned.
2. **The rest of `docs/PRODUCTION_READINESS.md`'s checklist** — even
   once access is granted, monitoring, rate-limit tuning, secret
   rotation, second-engineer review, and a rollback plan all remain
   open, same as flights.
3. **No booking, payment, reservation creation, cancellation, or
   modification exists anywhere** — explicitly out of scope.
   `provider_property_id`/`provider_rate_id` are preserved internally
   specifically so a future booking task doesn't have to re-derive
   them.
4. **Amenity-vocabulary precision.** Accessibility/comfort/business
   signals derived from Duffel's `amenities` list use keyword matching
   against terms this task could not confirm from public documentation
   — real data may use different vocabulary than assumed, silently
   defaulting to the neutral/unset branch rather than erroring
   (documented in `docs/DUFFEL_STAYS_INTEGRATION.md`).
5. **Application-startup wiring remains opt-in only** — no deployment
   automatically enables `LIVE_SANDBOX`.
