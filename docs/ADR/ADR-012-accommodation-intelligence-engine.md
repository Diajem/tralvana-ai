# ADR-012: Accommodation Intelligence Engine

**Date**: 2026-07-09
**Status**: Accepted
**Sprint**: 2 (T-016)

## Context

T-016 adds Accommodation Intelligence as the second Discovery Layer module, the first built directly against `docs/DISCOVERY_LAYER_PATTERN.md` (ADR-011) rather than by copying Flight Intelligence. It must reason about which accommodation fits the traveller — budget, comfort, location, family/business needs, accessibility — not just list hotels, following the same explainable-scoring philosophy as Flight Intelligence.

## Decision

**Full six-file AI module** matching the pattern exactly: `mock_accommodation_provider.py`, `accommodation_normalizer.py`, `accommodation_scorer.py`, `accommodation_reasoner.py`, `accommodation_risk_assessor.py`, `accommodation_intelligence.py` (orchestrator).

**A genuine Provider/Normalizer split**, unlike Flight Intelligence. `MockAccommodationProvider` returns raw, provider-shaped records (`hotel_name`, `property_type: "boutique_hotel"`, `km_to_center`, `guest_rating` on a 0–10 scale, raw `amenities` lists) — deliberately different vocabulary from the domain's canonical schema. `AccommodationNormalizer` is the only place that translates it, and it's also where the three **objective** scores live: `comfort_score`, `location_score`, `safety_score` — properties of the accommodation itself, independent of who's asking. This directly follows `DISCOVERY_LAYER_PATTERN.md`'s requirement that every module from Accommodation onward have an explicit Normalizer.

**Eight mock templates, one per `AccommodationType`.** Unlike Flight Intelligence's six carrier archetypes (which don't map 1:1 to its eight recommendation types), Accommodation's eight templates map exactly to its eight `AccommodationType` values — a boutique hotel, budget hostel, family apartment, luxury resort, business serviced apartment, standard hotel, private villa, and guesthouse, each with realistic price/location/amenity profiles.

**A labelling algorithm refinement, found and fixed during implementation.** The recommendation-labelling algorithm generalised from Flight Intelligence (AVOID → BEST_OVERALL → persona categories → best-fit fallback) was tested against Accommodation's exact numbers — 8 candidates, 8 possible `recommendation_type` values — and immediately produced a duplicate label (two options both labelled `BEST_FOR_BUSINESS`) whenever `AVOID`'s 0.35 threshold didn't naturally trigger, leaving only 7 usable positive categories for 8 candidates. Flight Intelligence never surfaces this (6 candidates, 8 categories, always slack), so it was invisible until Accommodation's tighter numbers exposed it. Fixed by having the single candidate that wins no category become `AVOID` — the relative weakest of the set — instead of duplicating another option's label. This guarantees exactly 8 unique labels for exactly 8 candidates every time, verified in tests.

**A conversation entity-extraction bug, also found and fixed.** Adding `Intent.ACCOMMODATION_SEARCH` patterns including `"where to stay"` and `"a place to stay"` exposed a pre-existing flaw in the shared `IntentClassifier._extract_entities()`: its generic `"to "` destination marker matched `"to stay"`, misreading messages like `"find me a place to stay"` as `destination: "Stay"`. Fixed by adding `"stay"` to the extractor's existing stopword exclusion list (alongside `"the"`, `"my"`, `"a"`, etc.) — a general fix to shared code, not a workaround scoped to this module's own patterns.

**Conversation integration** follows Flight Intelligence's precedent exactly: `Intent.ACCOMMODATION_SEARCH` maps to zero specialist agents in `DecisionEngine._AGENT_MAP`; `ConversationEngine._get_accommodation_recommendations()` calls the service directly, not through `TravelManager`/`AgentRegistry`. Only requires a destination — check-in date is defaulted with a recorded assumption, avoiding an unnecessary clarification round-trip.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Skip the Normalizer, emit normalized dicts directly from the mock provider (Flight Intelligence's approach) | `DISCOVERY_LAYER_PATTERN.md`, written earlier in this same task, explicitly requires every module from Accommodation onward to have one — this module exists partly to prove the pattern out |
| Duplicate-label collisions accepted as "expected" per the pattern doc's fallback note | The pattern doc's fallback note anticipates duplicates only when candidates *structurally* outnumber every category; 8 candidates vs. 8 categories should never collide, and didn't need to once the weakest-of-set-to-AVOID rule was added — accepting an avoidable bug because a general note technically covered it would be settling for less correctness than achievable |
| Fewer than 8 mock templates, to sidestep the pigeonhole collision without changing the algorithm | Loses the clean 1:1 mapping to all 8 `AccommodationType` values, and is a much less honest fix than correcting the actual algorithm |
| Scope the entity-extraction fix narrowly (e.g. skip destination extraction only for `ACCOMMODATION_SEARCH` patterns containing "stay") | The bug is in shared code (`IntentClassifier._extract_entities`) used by every intent; a module-specific workaround would leave the same bug reachable via any other future phrase containing "to stay" |
| `review_score` on a 0.0–1.0 scale, matching `safety_score`/`comfort_score`/`location_score`/`match_score` | 0–10 is the familiar guest-review convention (matches the raw provider's `guest_rating`) and avoids a confusing precision loss (8.3/10 is more legible than 0.83) — documented explicitly as the one field on a different scale |

## Consequences

- Accommodation Intelligence is the reference implementation for a fully compliant Discovery module — `docs/DISCOVERY_LAYER_PATTERN.md` links to it alongside Flight Intelligence.
- The labelling algorithm fix (weakest-of-set → AVOID) is Accommodation-specific for now; Flight Intelligence's simpler version is untouched since it's mathematically safe for its own candidate/category ratio. If a future Discovery module needs the same guarantee, extract the improved algorithm to a shared helper (already flagged as a Sprint 3+ item in ADR-011).
- The `"stay"` stopword fix improves `IntentClassifier._extract_entities()` for every intent, not just `ACCOMMODATION_SEARCH` — a small net positive to shared conversation code.
- 70 new tests (accommodation normalizer, scorer, risk assessor, orchestrator, API endpoints, conversation routing, intent/decision coverage) — 211 total, all passing. Zero regressions to Flight Intelligence or any earlier module.

## Sprint 4+ Migration Path

| Component | Upgrade |
|-----------|---------|
| `MockAccommodationProvider` | Real `AccommodationProvider` (Booking.com, Expedia) behind the same `search()` signature; only the Normalizer changes |
| `AccommodationScorer` | Incorporate live review-fraud detection and dynamic pricing signals |
| `AccommodationRiskAssessor` | Live safety-incident and neighbourhood-advisory data instead of static heuristics |
| `AccommodationRepository` | Swap for PostgreSQL adapter (same Sprint 3 migration as Goals/Trips/Flights) |
| `Intent.ACCOMMODATION_SEARCH` | LLM-backed classification, replacing keyword patterns |
