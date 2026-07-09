# Accommodation Intelligence Engine

T-016 — the second Discovery Layer module, and the first built directly against `docs/DISCOVERY_LAYER_PATTERN.md` rather than by precedent. Turns an accommodation search into a ranked, explainable set of recommendations.

## Architecture

```
Provider → Normalizer → Scorer → Reasoner → Risk Assessor → Recommendation → Explanation
```

| Stage | Module | Responsibility |
|-------|--------|-----------------|
| Domain | `services/api/app/domains/accommodation/` | AccommodationOption model, REST API, in-memory repo |
| Provider | `ai/discovery/accommodation/mock_accommodation_provider.py` | Raw, provider-shaped mock inventory |
| Normalizer | `ai/discovery/accommodation/accommodation_normalizer.py` | Raw → canonical schema; computes objective `comfort_score`/`location_score`/`safety_score` |
| Scorer | `ai/discovery/accommodation/accommodation_scorer.py` | Subjective `match_score` against traveller preferences, DNA, goal type |
| Reasoner | `ai/discovery/accommodation/accommodation_reasoner.py` | Human-readable explanation from the score breakdown |
| Risk Assessor | `ai/discovery/accommodation/accommodation_risk_assessor.py` | Per-option risk flags |
| Orchestrator | `ai/discovery/accommodation/accommodation_intelligence.py` | Wires the above together, ranks, labels |
| Conversation | `ai/concierge/conversation_engine.py` | Routes `ACCOMMODATION_SEARCH` intent directly to this engine |

See `docs/DISCOVERY_LAYER_PATTERN.md` for why Provider and Normalizer are separate stages — this module is the reference example of a genuine raw/canonical split (Flight Intelligence's mock provider skipped it; this one doesn't).

## A genuine Provider/Normalizer split

`MockAccommodationProvider.search()` returns records shaped like a real hotel API would — `hotel_name`, `property_type: "boutique_hotel"`, `km_to_center`, `guest_rating` (0–10), `cleanliness_rating`, raw `amenities` lists. None of that vocabulary matches the domain's canonical `AccommodationOption` fields directly.

`AccommodationNormalizer.normalize()` is the only place that translates it: `property_type` → the `AccommodationType` enum, `km_to_center`/`km_to_transit` → `distance_to_centre`/`distance_to_transport`, and — critically — computes three **objective** scores intrinsic to the property itself, the same for every traveller:

- `comfort_score` — from star rating, cleanliness rating, and comfort amenities (pool, spa, private beach)
- `location_score` — from distance to centre and distance to transport
- `safety_score` — normalized `safety_rating` (0–10 → 0.0–1.0)

The Scorer never touches raw provider fields — only normalized ones. A future `BookingComProvider` or `ExpediaProvider` only needs to implement `search()` returning its own raw shape; the Normalizer absorbs the difference and nothing else changes.

## AccommodationOption Fields

| Field | Type | Description |
|-------|------|-------------|
| `accommodation_option_id` | str | UUID |
| `traveller_id` / `trip_id` | str \| None | Linked traveller / trip |
| `destination` | str | Search destination |
| `property_name` | str | Mock property name |
| `accommodation_type` | str | One of the 8 `AccommodationType` values |
| `star_rating` | int | 1–5 |
| `neighbourhood` | str | Mock area name |
| `distance_to_centre` / `distance_to_transport` | float | Kilometres |
| `nightly_price` / `total_price` | float | `total_price = nightly_price × nights` |
| `currency` | str | Always `"USD"` in Sprint 1 |
| `breakfast_included` | bool | |
| `cancellation_policy` | str | free_cancellation / partial_refund / non_refundable |
| `accessibility_features` | list[str] | e.g. `["elevator", "step_free_access"]` |
| `family_friendly` / `business_friendly` | bool | Objective, computed in the Normalizer from type + amenities |
| `review_score` | float | 0–10 scale (guest rating) |
| `safety_score` / `comfort_score` / `location_score` | float | 0.0–1.0, objective (Normalizer) |
| `match_score` | float | 0.0–1.0, subjective (Scorer) |
| `reasoning` | str | Explanation of the score |
| `risks` | list[str] | Per-option risk flags |
| `assumptions` | list[str] | Per-option assumptions |
| `recommendation_type` | str | One of the 8 types below |

## Accommodation Types

`HOTEL`, `APARTMENT`, `HOSTEL`, `VILLA`, `RESORT`, `SERVICED_APARTMENT`, `BOUTIQUE_HOTEL`, `GUESTHOUSE` — the mock provider generates exactly one candidate per type (8 templates), so every search returns one property of each archetype.

## Recommendation Types

Same priority-ordered, exhaustive labelling algorithm as Flight Intelligence (see `docs/DISCOVERY_LAYER_PATTERN.md`):

1. **AVOID** — `match_score < 0.35`
2. **BEST_OVERALL** — highest score among the rest
3. **BEST_VALUE / BEST_LOCATION / BEST_COMFORT / BEST_FOR_FAMILY / BEST_FOR_BUSINESS / BEST_BUDGET** — six persona-weighted sub-scores each claim their best-fit remaining option

**A refinement not needed in Flight Intelligence**: with exactly 8 mock templates and exactly 8 possible `recommendation_type` values, if `AVOID`'s threshold never triggers (common — 0.35 is a low bar), only 7 "positive" categories remain for 8 candidates, forcing a collision by the pigeonhole principle. Flight Intelligence never hits this (6 candidates, 8 categories, always slack). Accommodation resolves it deterministically: if every positive category has been claimed and one candidate still has no label, the one that won *no* category — the relative weakest of the set — becomes `AVOID`, rather than duplicating another option's label. This guarantees exactly 8 unique labels for exactly 8 candidates every time (verified in `ai/tests/test_accommodation_intelligence.py::test_every_option_has_unique_recommendation_type`).

## Scoring

`AccommodationScorer` computes ten weighted, independently explainable dimensions (weights sum to 1.0): `price_fit` (0.20), `type_preference_fit` (0.10), `location_fit` (0.15), `breakfast_fit` (0.08), `cancellation_flexibility_fit` (0.10), `accessibility_fit` (0.10), `family_fit` (0.07), `business_fit` (0.05), `review_score_fit` (0.10), `safety_score_fit` (0.05).

`location_fit` is a direct example of the objective/subjective split: when the traveller prefers a central location, it simply returns the Normalizer's own `location_score` — the objective measurement feeds straight into the subjective weighting.

A DNA/goal-type adjustment layer (±0.05–0.08) follows, same pattern as Flight Intelligence: `luxury_orientation` boosts high star ratings, `budget_consciousness` boosts below-average prices, `family_orientation`/`FAMILY_TRIP` boosts `family_friendly` properties, `business_orientation`/`BUSINESS_TRAVEL` boosts `business_friendly` properties. Every adjustment is logged in `dna_notes` and surfaces in `reasoning` — explainable, not a black box.

## Conversation Integration

A new `Intent.ACCOMMODATION_SEARCH` was added, with patterns checked before the generic `PLAN_TRIP` bucket (`"find hotels"`, `"recommend accommodation"`, `"where to stay"`, etc.), verified not to collide with `MODIFY_TRIP`'s `"different hotel"` or `BUDGET_ADVICE`'s `"affordable hotels"`.

**A real bug found and fixed during this task**: the shared entity extractor's generic `"to "` marker misread `"a place to stay"` as `destination: "Stay"`, because `"to stay"` matches the same pattern used for `"trip to Tokyo"`. Fixed by adding `"stay"` to the extractor's stopword exclusion list — a general fix, not a narrow one, since it corrects the extractor for any future message containing "to stay," not just this module's own trigger phrases.

Like `FLIGHT_SEARCH`, `ACCOMMODATION_SEARCH` only requires a destination — no date is required; the check-in date is defaulted and recorded as an assumption. `DecisionEngine` maps it to zero specialist agents; `ConversationEngine._get_accommodation_recommendations()` calls the service directly, matching the established direct-call pattern (Goal/Trip creation, Flight Intelligence).

## Constraints

- No external accommodation APIs (no Booking.com, no Expedia, no Airbnb)
- No booking, no payment
- Deterministic mock data only — same destination always produces the same candidates and prices
- Sprint 4+: swap `MockAccommodationProvider` for a real `AccommodationProvider`; only the Normalizer changes
