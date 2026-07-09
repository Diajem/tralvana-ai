# Destination Intelligence Engine

T-017 — the third Discovery Layer module. Reasons about which destinations, neighbourhoods, attractions, food areas, transport zones, and experience clusters best fit the traveller — not just a flat list of cities.

## Architecture

```
Provider → Normalizer → Scorer → Reasoner → Risk Assessor → Recommendation → Explanation
```

| Stage | Module | Responsibility |
|-------|--------|-----------------|
| Domain | `services/api/app/domains/destinations/` | DestinationOption model, REST API, in-memory repo |
| Provider | `ai/discovery/destinations/mock_destination_provider.py` | Deterministic 10-city mock catalogue |
| Normalizer | `ai/discovery/destinations/destination_normalizer.py` | Raw → canonical schema; computes 9 objective `*_score` fields |
| Scorer | `ai/discovery/destinations/destination_scorer.py` | Subjective `match_score` against interests, DNA, goal type, season |
| Reasoner | `ai/discovery/destinations/destination_reasoner.py` | Human-readable explanation from the score breakdown |
| Risk Assessor | `ai/discovery/destinations/destination_risk_assessor.py` | Per-option risk flags |
| Orchestrator | `ai/discovery/destinations/destination_intelligence.py` | Wires the above together, ranks, labels |
| Conversation | `ai/concierge/conversation_engine.py` | Routes `DESTINATION_DISCOVERY` intent directly to this engine |

See `docs/DISCOVERY_LAYER_PATTERN.md` for the general pipeline; this module follows it exactly, same as Accommodation Intelligence (ADR-012).

## Two Modes

`MockDestinationProvider.search(city)` matches how travellers actually ask:

- **City given** — "what should I do in Tokyo?" — returns the specific places *within* that city: neighbourhoods, food districts, football venues, museums, transport hubs, hidden gems.
- **City omitted** — "where should I go?" — returns the top-level city overviews across the whole catalogue, so the traveller can compare destinations before picking one.

## Mock Catalogue

10 cities, each with a city-level overview plus ~5 curated sub-options: **Tokyo, Osaka, Barcelona, Paris, London, New York, Lagos, Accra, Kingston, Dubai** — 60 entries total, spanning all 12 `DestinationType` values.

City-level attributes (safety, transport, food scene, culture, football reputation, budget tier, peak travel months) are shared across every entry within that city and drive the objective scoring. **These ratings are illustrative mock data for deterministic scoring demonstrations — not real safety assessments or travel advisories.** Sprint 4+ replaces the catalogue with a live provider; see Constraints below.

## DestinationOption Fields

| Field | Type | Description |
|-------|------|-------------|
| `destination_option_id` | str | UUID |
| `traveller_id` / `trip_id` | str \| None | Linked traveller / trip |
| `city` / `country` / `region` | str | Location context |
| `neighbourhood` | str | Empty for CITY-type entries |
| `destination_type` | str | One of 12 `DestinationType` values |
| `name` / `description` | str | Mock place name and blurb |
| `best_for` | list[str] | Curated descriptive tags, e.g. `["fresh seafood", "street food"]` |
| `interests_matched` | list[str] | Which requested interests this option actually satisfies |
| `distance_from_centre` | float | Kilometres |
| `transport_access_score` / `food_score` / `culture_score` / `football_score` / `nightlife_score` / `family_score` / `safety_score` / `budget_score` / `season_score` | float | 0.0–1.0, objective (Normalizer) |
| `match_score` | float | 0.0–1.0, subjective (Scorer) |
| `reasoning` | str | Explanation of the score |
| `risks` | list[str] | Per-option risk flags |
| `assumptions` | list[str] | Per-option assumptions |
| `recommendation_type` | str | One of the 9 types below |

`budget_score` is affordability, not cost — 1.0 is very affordable, 0.0 is very expensive.

## Destination Types

`CITY`, `NEIGHBOURHOOD`, `ATTRACTION`, `MUSEUM`, `FOOD_DISTRICT`, `FOOTBALL_VENUE`, `SHOPPING_DISTRICT`, `BEACH`, `NATURE_AREA`, `HISTORIC_SITE`, `TRANSPORT_HUB`, `NIGHTLIFE_AREA`.

## Recommendation Types

Same priority-ordered, exhaustive labelling algorithm as Flight and Accommodation Intelligence:

1. **AVOID** — `match_score < 0.35`
2. **BEST_OVERALL** — highest score among the rest
3. **BEST_FOR_FOOD / BEST_FOR_FOOTBALL / BEST_FOR_CULTURE / BEST_FOR_FAMILY / BEST_FOR_BUDGET / BEST_FOR_PHOTOGRAPHY / BEST_HIDDEN_GEM** — seven persona-weighted sub-scores each claim their best-fit remaining option
4. Same "weakest of the set → AVOID" refinement from Accommodation Intelligence (ADR-012) applies when candidates exactly match the category count.

**A relevance floor, new in this module**: a persona only claims a candidate if that candidate is genuinely relevant to it (`persona_score >= 0.45`). Without this, a small city with no football content at all (e.g. Tokyo's 5 curated options, none football-related) could still end up with a `BEST_FOR_FOOTBALL` label just because one option scored marginally higher than the others on an irrelevant dimension. Skipped personas simply go unclaimed; any candidate left over still gets a label via the guaranteed-coverage fallback, so every option always receives one of the 9 types — just not a nonsensical one. City-mode results (≤6 candidates) are always fully unique; catalogue mode (10 candidates vs. 9 categories) can have one expected duplicate, same documented trade-off as Accommodation Intelligence.

## Scoring

`DestinationScorer` computes seven weighted, independently explainable dimensions (weights sum to 1.0): `interest_fit` (0.30), `safety_fit` (0.15), `budget_fit` (0.15), `transport_fit` (0.10), `season_fit` (0.10), `family_fit` (0.10), `photography_fit` (0.10).

**`interest_fit`** is the traveller-preference dimension: each requested interest (e.g. `"food"`, `"football"`, `"culture"`) maps to the corresponding objective score field; unmapped interests (e.g. `"romance"`) contribute a neutral 0.6 rather than being ignored. Food/culture/football relevance are not separate weighted dimensions — they flow through `interest_fit` and the persona sub-scores, avoiding double-counting the same signal twice.

**Photography suitability** has no dedicated model field (not in the required field list) — it's computed from tags plus a culture/popularity proxy, and reinforced through the DNA `photography_tendency` trait in the adjustment layer, the same way Flight and Accommodation Intelligence fold DNA-only signals into the adjustment layer rather than adding new model fields for every trait.

A DNA/goal-type adjustment layer (±0.05–0.08) follows: `sport_focus`/`FOOTBALL_TRAVEL` boosts football relevance, `food_focus`/`FOOD_TOUR` boosts food relevance, `cultural_curiosity` boosts culture relevance, `family_orientation`/`FAMILY_TRIP` boosts family suitability, `budget_consciousness` boosts affordability, `photography_tendency` boosts photogenic spots, and `DIASPORA_TRAVEL`/`PILGRIMAGE` goals boost heritage-tagged destinations (Cape Coast Castle, Bob Marley Museum). Every adjustment is logged in `dna_notes` and surfaces in `reasoning`.

## Conversation Integration

A new `Intent.DESTINATION_DISCOVERY` was added, checked before `PLAN_TRIP` and `TRAVEL_ADVICE` (patterns: `"where should i go"`, `"recommend a destination"`, `"things to do in"`, etc. — verified not to collide with `DESTINATION_QUESTION`'s `"tell me about"` or `TRAVEL_ADVICE`'s bare `"recommend"`/`"suggest"`, the same collision class already solved for `FLIGHT_SEARCH`/`ACCOMMODATION_SEARCH`).

Unlike every other Discovery intent, `DESTINATION_DISCOVERY` is **always ready** — no destination is required, since the "no city" catalogue mode is itself a complete, useful response ("where should I go?" is a valid question with no city yet). `DecisionEngine` maps it to zero specialist agents; `ConversationEngine._get_destination_recommendations()` calls the service directly, matching Flight and Accommodation Intelligence.

## Constraints

- No live maps or places APIs (no Google Places, no TripAdvisor)
- No booking, no payment
- Deterministic mock data only — same city always produces the same candidates
- Sprint 4+: swap `MockDestinationProvider` for a real `DestinationProvider`; only the Normalizer changes
