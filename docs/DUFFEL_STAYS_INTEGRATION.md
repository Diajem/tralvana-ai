# Duffel Stays Integration

Technical design of `DuffelStaysProvider`
(`travelos/live_providers/adapters/duffel_stays_provider.py`, T-039).
Written as a companion to `docs/LIVE_PROVIDER_ADAPTER_GUIDE.md` (the
general pattern) and `docs/FLIGHT_PROVIDER_INTEGRATION.md` (the
flights equivalent) — read both first. **Do not assume the flight
adapter's structure applies here**: the two adapters share only
`BaseLiveProvider`; everything else differs, for real reasons detailed
below.

## API Reference (confirmed against Duffel's public docs during this task)

| | |
|---|---|
| Endpoint | `POST https://api.duffel.com/stays/search` |
| Auth | `Authorization: Bearer <token>`, `Duffel-Version: v2` — same scheme and same token as `DuffelFlightProvider` |
| Processing | **Synchronous** — no polling, matching Flights |
| Required fields | `check_in_date`, `check_out_date`, `rooms`, `guests`, and either `accommodation` or `location` |
| Location search | `location.geographic_coordinates.{latitude,longitude}` + `location.radius` (1–100km, Duffel's documented range; this adapter defaults to 15km) |
| Stay limits | Check-in no more than 330 days out; stay up to 99 nights |
| Response | `data.results[]`, each with `accommodation{...}`, `cheapest_rate_*` fields, and (when included) `accommodation.rooms[].rates[]` |

Places API (for destination resolution): `GET https://api.duffel.com/places/suggestions?query=...`
— same auth, returns `{data: [{id, type: "airport"|"city", name, latitude, longitude, ...}]}`.

Sources: [Search](https://duffel.com/docs/api/v2/search), [Accommodation object](https://duffel.com/docs/api/v2/accommodation), [Stays key concepts](https://duffel.com/docs/api/overview/stays-key-concepts), [Place suggestions](https://duffel.com/docs/api/places/get-place-suggestions), [Test Hotels](https://duffel.com/docs/guides/test-hotels), [Cancellation timeline](https://duffel.com/docs/guides/displaying-the-cancellation-timeline).

## Access Requirement

**Confirmed against the real API during this task**: the existing
`DUFFEL_API_TOKEN` does not have Stays access.

```
$ POST /stays/search  (real sandbox token, valid for Flights)
HTTP 403
This feature is not enabled for your account. Please contact sales to get access: https://duffel.com/contact-us
```

Per Duffel's own "Getting Started with Stays" guide: Stays uses the
same account and the same API token as Flights, but **access must be
separately requested** through Duffel's contact form — a token that
works for Flights sandbox search does not automatically work for
Stays. This is not a bug in this adapter or in this repository's
configuration; it is confirmed, documented Duffel account behaviour.
`DuffelStaysProvider.map_error()` recognises this exact plain-text 403
body and translates it into a clear `ProviderValidationError` rather
than a generic failure — see Error Handling below.

## Test Hotels

Once Stays access is granted, Duffel's sandbox exposes deterministic
test properties at **latitude -24.38, longitude -128.32** ("Test Mode"
— per `docs/guides/test-hotels`). `DuffelStaysProvider`'s own
destination-resolution step (Places API) is bypassed if a caller
constructs a `ProviderRequest` with these coordinates directly, or
simply search a destination Duffel's Places API resolves near there.

## Destination Resolution

`_resolve_destination()` (private, never leaves this class) calls the
Places API before building the search request. **A real finding from
this task's own live verification**: searching "Tokyo" returns a
`city`-type place with `latitude`/`longitude` both `null`, alongside
several `airport`-type places that do carry coordinates:

```
0 type=city    name=Tokyo                       lat_present=False lng_present=False
1 type=airport name=Narita International Airport lat_present=True  lng_present=True
2 type=airport name=Haneda Airport               lat_present=True  lng_present=True
```

The adapter's original assumption — take the first `city`-type match
unconditionally — failed against this exact real response (it would
have raised "could not resolve destination" for a perfectly valid
city). Fixed to select the first **geocoded** place (one with both
coordinates present), preferring `city` type among geocoded candidates,
falling back to any other type (an airport) otherwise. Verified by
`travelos/tests/test_duffel_stays_provider.py::TestDestinationResolution::test_city_place_missing_coordinates_falls_back_to_a_geocoded_airport`,
built from this exact real response shape.

## Request Mapping

| Internal param (`GatewayAccommodationProvider.search()`) | Duffel field |
|---|---|
| `destination` | Resolved to `location.geographic_coordinates` via the Places lookup above |
| `check_in_date` | `check_in_date` (unchanged) |
| `nights` | `check_out_date` is **computed** as `check_in_date + nights` days — Duffel has no "nights" concept, this is the one exact, non-fabricated conversion between the two representations |
| `adults`, `children` | `guests: [{"type": "adult"}, ...] + [{"type": "child"}, ...]` |
| `rooms` | `rooms` (unchanged) |

`adults`/`children`/`rooms` are new parameters on
`GatewayAccommodationProvider.search()` and
`MockAccommodationProvider.search()` (T-039) — the mock accepts and
ignores them (mock inventory has never varied by occupancy); Duffel
needs them to build a valid request. `AccommodationIntelligence.recommend()`
gained a `rooms` parameter to thread through; `RecommendAccommodationRequest`
gained a `rooms` field (default 1).

## Response Mapping — Field by Field

`parse_response()` produces **raw, Duffel-vocabulary dicts** (not the
canonical internal schema) — tagged `_provider_source: "duffel_stays"`.
This mirrors `MockAccommodationProvider`'s own contract exactly (see
that module's docstring: "raw, provider-shaped records... the
Normalizer's job is to absorb exactly this kind of inconsistency").
`AccommodationNormalizer._normalize_duffel_stays()`
(`ai/discovery/accommodation/accommodation_normalizer.py`) is where the
conversion to canonical form happens — a second raw vocabulary this
Normalizer now absorbs, alongside its original mock-provider branch,
unchanged.

| Canonical field | Duffel source | Notes |
|---|---|---|
| `property_name` | `accommodation.name` | Direct |
| `star_rating` | `accommodation.rating` | Nullable (1–5) in Duffel; defaults to `0` when absent — a value distinguishable from a real rating, never a guessed number |
| `review_score` | `accommodation.review_score` | Nullable (1.0–10.0); defaults to `5.0` (exactly neutral) when absent |
| `neighbourhood` | `accommodation.location.address.city_name`, falling back to `.region` | |
| `distance_to_centre` | **Computed** via the haversine great-circle formula between the search's resolved coordinates and `accommodation.location.geographic_coordinates` | Real geometry from two real data points — not a Duffel-provided figure, and not fabricated |
| `distance_to_transport` | **Set equal to `distance_to_centre`** | Duffel has no transit-distance data anywhere in its documented schema; approximating it to a real computed value, rather than inventing an independent number, is the least-fabricated reasonable choice |
| `nightly_price`, `total_price`, `currency` | The cheapest rate's `total_amount`/`total_currency` if room/rate detail is present, else the search result's own `cheapest_rate_total_amount`/`cheapest_rate_currency` — per Duffel's own docs: "a search result's accommodation may not include rooms and rates information... but you will always know the price of the cheapest rate" | |
| `breakfast_included` | The cheapest rate's `board_type`, checked against `{"breakfast", "half_board", "full_board", "all_inclusive"}` | Duffel's exact `board_type` enum values aren't published with concrete strings in the documentation this task could access — this is a best-effort, defensible mapping, documented as such |
| `cancellation_policy` | `cancellation_timeline` — `refund_amount == total_price` → `free_cancellation`; every entry `<= 0` → `non_refundable`; otherwise `partial_refund`; absent → `"unknown"` (a safe fourth bucket `AccommodationScorer` already treats as neutral, 0.5) | Grounded in Duffel's own documented semantics (`docs/guides/displaying-the-cancellation-timeline`) |
| `accessibility_features` | Keyword-matched against `accommodation.amenities` (`wheelchair`, `accessible`, `step_free`, `elevator`, `lift`) | Duffel's amenity vocabulary has no publicly documented enum list — matches only when a real Duffel amenity string contains one of these substrings; never invents a feature |
| `accommodation_type` | **Always `HOTEL`** | Duffel's Accommodation schema has no property-type classification field at all; a deliberately neutral placeholder, not a guess at the "most likely" type |
| `safety_score` | **Always `0.5`** (exactly neutral) | No safety signal exists anywhere in Duffel's documented schema; kept just below `AccommodationRiskAssessor`'s `< 0.5` threshold so it never triggers a false "below-average safety" flag |
| `comfort_score` | Recomputed: `0.5×star_component + 0.3×review_component + 0.2×amenity_bonus` | Same weighting as the mock's own formula, substituting `review_score` for `cleanliness_rating` (which Duffel doesn't provide) — guest review score is the closest available real signal for perceived quality |
| `family_friendly`, `business_friendly` | Reused directly from `AccommodationNormalizer`'s existing `_family_friendly()`/`_business_friendly()` methods | Generic enough to operate on any `(accommodation_type, amenities, distance)` triple — genuine code reuse, not a new formula |
| `provider_property_id`, `provider_rate_id` | `accommodation.id`, the cheapest rate's `id` (or the search result's own `id` when no rate detail is present) | Internal only — never in `AccommodationOption.to_dict()`'s public shape |

**Never mapped, never invented**: images (Duffel's `photos` field
exists but this task's scope didn't require displaying them), phone/email
(populated only for completed bookings per Duffel's own docs — never
relevant pre-booking), loyalty programme fields, chain/brand detail.

## Error Handling

Same standard-error-type mapping as `DuffelFlightProvider`
(`docs/PROVIDER_ERROR_MODEL.md`) — 401/403→auth, 408→timeout,
429→rate-limit, 5xx→unavailable — plus two Stays-specific refinements
in `map_error()`:

1. **The account-not-enabled 403** (plain text, not JSON) is
   recognised by substring match and reclassified as a non-retryable
   `ProviderValidationError` naming this doc's Access Requirement
   section — confirmed against the real response body during this
   task's live verification.
2. **Duffel's structured `{"errors": [...]}` body** (validation_error,
   authentication_error, rate_limit_error) is reclassified the same way
   `DuffelFlightProvider` does, for statuses (like 422) the generic
   status-code mapping can't distinguish on its own.

**Partial mapping failure** (T-039 requirement): one malformed search
result in a batch is skipped and counted
(`ProviderResult.warnings`/`source_metadata.raw_result_count` vs.
`mapped_result_count`), not treated as a whole-response failure — same
pattern `DuffelFlightProvider.parse_response()` established in T-038.

## Testing

`travelos/tests/test_duffel_stays_provider.py` — 33 tests, all against
`FakeTransport` with a responder distinguishing the Places call from
the Search call by URL. Covers destination resolution (including the
city-without-coordinates regression above), request mapping,
full-response and search-only-response mapping, partial mapping
failure, every standard error type, the account-not-enabled 403
specifically, health checks, and no-secret-leakage.

## Registration

`register_duffel_stays_provider(transport, registry=None, ...)` —
explicit, opt-in, never auto-registered at import, matching
`register_duffel_flight_provider()`'s (T-027) pattern exactly. Wired
into application startup via
`travelos/live_providers/accommodation_provider_bootstrap.py`'s
`configure_accommodation_provider()`, called once from
`services/api/app/main.py` — a no-op in `MOCK` mode (the default).
