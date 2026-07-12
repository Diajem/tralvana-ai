# ADR-025: Duffel Stays Integration

**Date**: 2026-07-13
**Status**: Accepted
**Sprint**: 2/3 boundary (T-039)

## Context

T-038 connected live Duffel flight data to the product behind a
FLIGHTS-specific switch. T-039 asks for the accommodation equivalent —
Duffel Stays — with an explicit instruction not to assume the flight
adapter's structure applies. It doesn't, in two significant ways: Stays
requires resolving a destination string into geographic coordinates
(Flights takes IATA codes directly), and Accommodation Intelligence has
an explicit Normalizer stage absorbing per-provider raw vocabularies
(Flights maps a vendor offer almost directly into scoring-ready
fields). This ADR also records a genuine access finding: Duffel Stays
requires separately-requested account access, confirmed unavailable on
the token this repository already uses for Flights.

## Decision

**Accommodation gets its own environment switch, generalized into the
same per-capability mechanism T-038 built for FLIGHTS.**
`TRALVANA_ACCOMMODATION_PROVIDER_MODE` is read by a new
`ConfigurationManager.accommodation_provider_mode` property.
`IntelligenceGateway._environment_for(capability)` (T-038) was
refactored from a single FLIGHTS-only `if` branch into a small
`Capability -> config attribute name` map
(`_CAPABILITY_MODE_CONFIG_ATTR`), so adding ACCOMMODATION required
one new dict entry and one new config property, not a second gateway
instance or a second per-capability special case hardcoded in
`execute()`. Weather is untouched, still resolving from the general
`provider_environment`.

**Destination resolution happens inside `DuffelStaysProvider`, as a
second, self-contained transport call from within `build_request()`.**
Duffel's location-based search needs `geographic_coordinates` + a
radius; `AccommodationIntelligence` only ever has a destination string.
`_resolve_destination()` calls Duffel's own Places API
(`GET /places/suggestions`) before building the search request — no
Duffel-specific location data (place IDs, coordinates) ever reaches
`ai/discovery/accommodation/` or any Tralvana domain model, satisfying
the task's explicit "keep Duffel-specific location data inside the
provider adapter" requirement.

**A real, live-verification-discovered bug in that resolution logic was
found and fixed.** Querying "Tokyo" against the real Places API
returns a `city`-type place with `latitude`/`longitude` both `null`,
alongside `airport`-type places that do carry coordinates. The original
design (take the first `city` match unconditionally) would have failed
to resolve a perfectly valid, common destination. Fixed to select the
first *geocoded* place — city type preferred among geocoded candidates,
any type otherwise — confirmed against the real response and covered by
a regression test built from that exact shape
(`docs/DUFFEL_STAYS_INTEGRATION.md`'s Destination Resolution section).
This is the direct analogue of T-037's day-component ISO 8601 duration
finding: fixture-only testing, however careful, cannot substitute for
one real call against the actual API when a vendor's real-world data
shape diverges from its own documentation's implied assumptions.

**Response mapping goes through `AccommodationNormalizer`, not a
direct raw-to-canonical translation the way `DuffelFlightProvider`
does.** `parse_response()` produces raw, Duffel-vocabulary dicts
(tagged `_provider_source: "duffel_stays"`) — mirroring
`MockAccommodationProvider`'s own documented contract ("the
Normalizer's job is to absorb exactly this kind of inconsistency").
`AccommodationNormalizer.normalize()` gained a
`_normalize_duffel_stays()` branch, dispatched on that tag, leaving the
original mock-provider path byte-identical. This was the architecturally
honest choice: Accommodation's pipeline explicitly names a "Normaliser"
stage (per this task's own architecture diagram) that Flights' pipeline
doesn't have — bypassing it by having the provider adapter emit
already-canonical fields directly would have hidden a real pipeline
stage rather than extending it.

**Fields Duffel doesn't provide get documented, neutral defaults —
never a fabricated specific value.** `safety_score` is always exactly
`0.5` (no Duffel signal exists at all); `distance_to_transport` is set
equal to the *computed* `distance_to_centre` (Duffel has no transit
data, but approximating to a real geometric value is less fabricated
than inventing an independent number); `accommodation_type` always
defaults to `HOTEL` (Duffel's schema has no property-type field at
all); `comfort_score` substitutes `review_score` for the mock's
`cleanliness_rating` (the closest available *real* signal, not an
invented one). Every one of these is documented field-by-field in
`docs/DUFFEL_STAYS_INTEGRATION.md`'s Response Mapping table, per this
task's explicit "no fabricated accommodation data" constraint.

**`adults`/`children`/`rooms` were added to `MockAccommodationProvider.search()`
and `GatewayAccommodationProvider.search()`, accepted and ignored by
the mock.** Unlike T-038's flights work (which explicitly deferred
passenger count as out of scope), this task's own request section
requires adults/rooms/children to reach Duffel — Duffel's `guests`/
`rooms` fields are required, not optional. Extending the shared
`search()` interface with new, defaulted, backward-compatible keyword
parameters was the smallest change that let Duffel receive real
occupancy data without touching `MockAccommodationProvider`'s actual
candidate-generation logic (mock inventory still doesn't vary by
occupancy — nothing asked for that to change).

**Confirmed the existing token lacks Stays access, and treated that as
data, not a blocker to work around.** A direct, minimal live check
(`POST /stays/search` with the real token) returned a clean, informative
403 — `"This feature is not enabled for your account."` Per Duffel's own
"Getting Started with Stays" guide, this is expected: Stays access is
requested separately from Flights access, even though both share the
same account and token. Rather than treat this as blocking the task,
per the task's own explicit instruction ("If the token or account does
not have Stays access, build and test the adapter with documented
Duffel-shaped fixtures, then stop before a live request and report the
exact access requirement") — the adapter was built and fully tested
against real-schema fixtures, and the manual verification script was
still run to completion, producing this exact 403 as its documented,
correct outcome.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| A second `IntelligenceGateway` instance for ACCOMMODATION, separate from the one T-038 already extended for FLIGHTS | The generalized `_CAPABILITY_MODE_CONFIG_ATTR` map inside the one existing gateway class is smaller and scales to a third capability with one more dict entry, not a third gateway instance |
| Have `DuffelStaysProvider.parse_response()` emit already-canonical fields directly (matching `DuffelFlightProvider`'s pattern) | Bypasses `AccommodationNormalizer` entirely, hiding a real, task-diagrammed pipeline stage rather than extending it as designed |
| Skip the live access check and assume Stays would work, deferring discovery of the 403 to the final verification step | The task's own section 1 explicitly requires confirming access *before* coding the response-mapping assumptions — doing it early let the adapter be designed and tested against the real, confirmed error shape (the plain-text 403 body) rather than a guessed one |
| Fabricate a plausible `distance_to_transport` (e.g. a fixed average) instead of approximating it to `distance_to_centre` | Approximating to a real, already-computed geometric value is more honest than inventing an unrelated number with no basis in any real data point |
| Leave `accommodation_type` unset/null when Duffel doesn't classify it | The canonical schema's `accommodation_type` field is non-nullable (used directly in scoring, e.g. `_type_preference_fit`); a documented, neutral default (`HOTEL`) is safer than introducing a new null-handling path through the entire scoring pipeline for one provider |
| Register `duffel_stays_provider` through `travelos/registry/service_registry.py` | Same reasoning as ADR-024 — that registry resolves domain *services* by name; the correct registry for a `Provider` is `travelos.intelligence_gateway.provider_registry`, already used |

## Consequences

- New: `travelos/live_providers/adapters/duffel_stays_provider.py`,
  `travelos/live_providers/accommodation_provider_bootstrap.py`,
  `ai/discovery/accommodation/live_search_validator.py`,
  `scripts/verify_duffel_stays_live_sandbox.py`.
- Modified: `travelos/config/configuration_manager.py` (+2 properties),
  `travelos/intelligence_gateway/gateway.py` (generalized
  `_environment_for()`), `travelos/intelligence_gateway/discovery_adapters.py`
  (`GatewayAccommodationProvider` +last_result/used_mock_fallback/adults/children/rooms,
  new `LiveAccommodationSearchUnavailableError`),
  `ai/discovery/accommodation/accommodation_normalizer.py`
  (`_normalize_duffel_stays()` branch, additive), `ai/discovery/accommodation/accommodation_intelligence.py`
  (`_source_metadata()`, `rooms` param, provider-id/data_source
  handling), `ai/discovery/accommodation/mock_accommodation_provider.py`
  (accepts and ignores adults/children/rooms),
  `services/api/app/domains/accommodation/{models,schemas,service,router}.py`
  (additive fields, validation call, exception-to-HTTP mapping),
  `services/api/app/main.py` (one composition-root call),
  `apps/web/src/{types/accommodation.ts,lib/api.ts,app/accommodation/recommend/page.tsx,app/accommodation/[id]/page.tsx}`.
- Zero changes to Trip Brain, the Explainability Engine, `AccommodationScorer`'s
  weights, `AccommodationReasoner`, `AccommodationRiskAssessor`, or any
  other Discovery module (Flights, Destination, Budget, Visa, Weather).
- `MOCK` mode (the default) is behaviourally identical to pre-T-039 —
  every pre-existing test passes unchanged.
- 129 new tests (1161 total, all passing), Ruff clean, frontend
  typecheck and production build both clean.
- One real HTTP round trip was made to Duffel's real API
  (`GET /places/suggestions`, succeeded; `POST /stays/search`,
  returned the documented 403) via `scripts/verify_duffel_stays_live_sandbox.py`,
  using the existing, already-configured token — never printed, logged,
  or committed anywhere.

## Deferred Items

- **Duffel Stays account access** — requires action outside this
  repository (`https://duffel.com/contact-us`); nothing further can be
  verified live until it's granted.
- The remainder of `docs/PRODUCTION_READINESS.md`'s checklist.
- Any booking, payment, reservation-creation, cancellation, or
  modification work — explicitly out of scope;
  `provider_property_id`/`provider_rate_id` are preserved internally
  specifically so this doesn't have to be re-derived later.
- Precise `board_type`/amenity vocabulary confirmation against a real
  populated response — this task's mapping is a defensible best effort
  against public documentation alone, not confirmed against live data
  (blocked on the same access requirement above).
- Application-startup wiring remains opt-in only.
