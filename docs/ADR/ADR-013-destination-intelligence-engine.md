# ADR-013: Destination Intelligence Engine

**Date**: 2026-07-10
**Status**: Accepted
**Sprint**: 2 (T-017)

## Context

T-017 adds Destination Intelligence as the third Discovery Layer module, built against `docs/DISCOVERY_LAYER_PATTERN.md` (ADR-011) the same way Accommodation Intelligence (ADR-012) was. It must reason about which destinations, neighbourhoods, attractions, food areas, transport zones, and experience clusters fit the traveller — not just return a flat list of cities.

Unlike Flight and Accommodation Intelligence, a destination search is inherently two-shaped: "where should I go?" (comparing cities) and "what should I do in Tokyo?" (exploring within a known city). Both are common, real questions, and the spec's field list (`city`, `neighbourhood`, `destination_type` including both `CITY` and place-level types like `NEIGHBOURHOOD`/`FOOD_DISTRICT`) implies both need to be representable in the same model.

## Decision

**Dual-mode Provider**, matching how travellers actually ask. `MockDestinationProvider.search(city)`: a specific city returns the curated places *within* it (excluding the city-level entry itself); no city returns the top-level city overviews across the whole catalogue. This mirrors `ai/planning/trip_planner.py`'s existing precedent of returning `recommended_destinations` only when no destination is specified — same idea, now built as a first-class Discovery module instead of a static fallback list.

**10-city mock catalogue, 60 entries.** Tokyo, Osaka, Barcelona, Paris, London, New York, Lagos, Accra, Kingston, Dubai — each with a city-level overview plus five curated sub-options spanning all 12 `DestinationType` values. City-level attributes (safety, transport, food scene, culture, football reputation, budget tier, peak months) are shared across every entry within a city; per-entry data (name, type, tags, distance, popularity) is what varies. This keeps authoring effort proportional — 10 city attribute blocks, not 60 independently-tuned rating sets — while still producing genuinely differentiated candidates.

**Objective scores are formula-derived, not hand-authored per entry.** With 9 required objective score fields (`transport_access_score`, `food_score`, `culture_score`, `football_score`, `nightlife_score`, `family_score`, `safety_score`, `budget_score`, `season_score`), hand-authoring 9 numbers × 60 entries (540 values) would violate "do not over-complicate the architecture" and be unmaintainable. Instead, `DestinationNormalizer` derives each from the entry's `destination_type` + tags + the shared city-level attributes — e.g. `food_score` is boosted if `destination_type == FOOD_DISTRICT` or `"food"` is tagged, scaled by the city's own food-scene reputation. Same technique as Accommodation Intelligence's `comfort_score`/`location_score` derivation (ADR-012), applied to a larger field set.

**No dedicated `photography_score` field**, even though `BEST_FOR_PHOTOGRAPHY` is a required recommendation type and "photography suitability" is a required scoring input. The required model field list doesn't include one. Photography suitability is computed internally (from tags + a culture/popularity proxy) and reinforced via the DNA `photography_tendency` trait in the adjustment layer — the same pattern Flight and Accommodation Intelligence already use for traits that don't have a dedicated per-option field (e.g. flights never got a `luxury_score` field even though `luxury_orientation` DNA affects scoring).

**`interest_fit` absorbs food/culture/football relevance rather than triple-counting them.** The spec asks scoring to consider interests *and* food/football/culture relevance separately. Making these three fully independent weighted dimensions *in addition to* `interest_fit` would double-count the same signal whenever a traveller's interests include "food" or "football" — the objective `food_score`/`football_score` already feed into `interest_fit` when those interests are requested, and separately feed the `food`/`football` persona sub-scores used for labelling. One signal, two honest uses (fit vs. label), not three.

**A relevance floor on persona labelling — a real bug found during testing.** Testing revealed that a small city with no genuinely relevant option for a persona (e.g. Tokyo's 5 curated places, none football-related) would still get a `BEST_FOR_FOOTBALL` label, because the labelling algorithm from ADR-011/ADR-012 always claims the *best available* candidate for each category regardless of how weak that candidate's actual relevance is. Fixed by requiring `persona_score >= 0.45` before a persona claims a candidate in the main labelling pass; personas with no qualifying candidate go unclaimed, and any option left over still receives a label via the existing guaranteed-coverage fallback — so coverage is preserved, but the label is honest. This is a refinement of the ADR-011 algorithm specific to Destination Intelligence's larger persona count (7, vs. Accommodation's 6) and its smaller typical candidate pool (city-mode: ≤6).

**A second real bug found during testing**: the risk assessor's off-season threshold (`season_score < 0.5`) never actually caught the Normalizer's own off-peak value, because the Normalizer sets off-peak `season_score` to exactly `0.5` and the comparison was strict `<`. Fixed to `<=`. Caught by a test asserting the risk assessor flags a `season_score` of exactly `0.5` — a boundary condition that's easy to introduce and easy to miss without an explicit test at the boundary.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Single search mode (always require a city) | Loses "where should I go?" — a genuinely common, valid question this module should answer, and the spec's `CITY` destination type implies city-level comparison is a first-class case |
| Hand-author all 9 objective scores per entry | 540 numbers across 60 entries, unmaintainable, and inconsistent with how Accommodation Intelligence already solved the identical problem (formula-derived from type + tags + shared city attributes) |
| Add a `photography_score` model field | Not in the required field list; the DNA-trait/tag-derived approach already used elsewhere in the codebase for non-modelled traits covers it without expanding the schema beyond spec |
| Separate `food_relevance`/`football_relevance`/`culture_relevance` weighted dimensions on top of `interest_fit` | Double-counts the same signal for any traveller whose interests already include food/football/culture; `interest_fit` plus persona sub-scores already cover both "how well does this fit this traveller's stated interests" and "which option is best for this activity type" without redundancy |
| Leave the football-persona-on-irrelevant-city behaviour as "expected" (per ADR-011's fallback note) | ADR-011's note covers duplicate labels when candidates outnumber categories — it does not license assigning a category to an option with no genuine relevance to it at all. That's a distinct, fixable problem, and leaving it would make `BEST_FOR_FOOTBALL` badges actively misleading on some of the ten launch cities |

## Consequences

- Destination Intelligence is the third reference implementation in `docs/DISCOVERY_LAYER_PATTERN.md`, alongside Flight (ADR-010) and Accommodation (ADR-012).
- The persona relevance floor (`_PERSONA_MIN_SCORE = 0.45`) is specific to this module for now. If Accommodation or Flight Intelligence ever show the same "irrelevant category forced onto a small pool" symptom, port the same fix — not urgent today since neither currently exhibits it (both operate on larger, more uniformly-relevant candidate pools).
- City-mode results (≤6 candidates against 9 categories) are always fully unique. Catalogue mode (10 candidates against 9 categories) can have exactly one expected duplicate — same documented, acceptable trade-off as Accommodation Intelligence.
- 76 new tests (mock provider determinism, normalizer, scorer, risk assessor, orchestrator, API endpoints, conversation routing, intent/decision coverage) — 289 total, all passing. Zero regressions to Flight or Accommodation Intelligence.
- Mock safety/culture/football ratings per city are explicitly documented as illustrative, not real travel advisories — same caveat already applied to `ai/planning/risk_assessor.py`'s heuristic safety data.

## Sprint 4+ Migration Path

| Component | Upgrade |
|-----------|---------|
| `MockDestinationProvider` | Real `DestinationProvider` (Google Places or similar) behind the same `search()` signature; only the Normalizer changes |
| `DestinationScorer` | Incorporate live crowd-density and seasonal-event data |
| `DestinationRiskAssessor` | Live travel advisory data instead of static heuristics |
| `DestinationRepository` | Swap for PostgreSQL adapter (same Sprint 3 migration as Goals/Trips/Flights/Accommodation) |
| `Intent.DESTINATION_DISCOVERY` | LLM-backed classification, replacing keyword patterns |
| Mock catalogue | Expand beyond 10 cities once a real provider replaces static authoring |
