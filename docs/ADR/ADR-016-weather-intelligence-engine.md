# ADR-016: Weather & Safety Intelligence Engine

**Date**: 2026-07-10
**Status**: Accepted
**Sprint**: 2 (T-020)

## Context

T-020 adds Weather & Safety Intelligence as the sixth and final Discovery Layer module, built against `docs/DISCOVERY_LAYER_PATTERN.md` (ADR-011) the same way Budget (ADR-014) and Visa (ADR-015) Intelligence were. It must determine how weather, climate, seasonality, and safety affect the traveller's overall trip experience for a destination and month — explicitly **not** a forecast engine, using deterministic mock data only, with representative monthly climate patterns for ten destinations.

The task set an explicit integration constraint not present in T-015–T-019: Weather Intelligence must remain independent and must not tightly couple with Destination or Budget Intelligence, exposing only interfaces a future Trip Brain can consume.

## Decision

**Single assessment, dual-mode request — combining Visa's and Destination's precedents rather than inventing a third pattern.** Like Visa Intelligence (ADR-015), a destination/month pair has exactly one true weather assessment, so `WeatherIntelligence.analyse()` returns one `WeatherAssessment`, not a ranked list. Like Destination Intelligence (ADR-013), the request itself is dual-mode: a specific month assesses that month directly; an omitted month scores all 12 months internally and assesses whichever one is best, recording an assumption explaining the substitution. This directly serves one of the task's own conversation examples — *"When should I visit Spain?"* has no month at all, and forcing a required-month field would make that question unanswerable.

**`weather_status` and `alternative_months` were added beyond the literal field list**, for the same reasons `visa_status` was added in ADR-015: the separately-specified 5-value `WeatherStatus` enum needs a field to live in (it's the module's `recommendation_type` equivalent), and the task's own requirement — Reasoner must explain "alternative travel month if appropriate," frontend must display "Alternative months" — needs structured data, not just prose the frontend would have to parse back out of `explanation`.

**Unknown destinations get a neutral status, not `NOT_RECOMMENDED`.** With no climate data, `WeatherNormalizer` defaults every comfort input to a neutral 0.5, which typically resolves to `ACCEPTABLE`. This was a deliberate choice over forcing the lowest status: a low score would incorrectly imply *confirmed* bad weather, when the true state is "we don't know." `VisaStatus` had a dedicated `CHECK_MANUALLY` bucket for exactly this situation; `WeatherStatus`'s fixed 5 values (all given by the task) have no equivalent, so the uncertainty is instead communicated honestly through low `confidence` (0.3, vs. 0.9 for a matched destination) and an explicit "no climate data available" risk flag — the same information, routed through a different field.

**Climate profiles authored as 2-4 season blocks per destination, then expanded to 12 months** — the same "formula, not hundreds of hand-tuned values" technique Destination Intelligence used for its objective scores (ADR-013) and Visa Intelligence used for its tier × destination policy table (ADR-015), applied here to month expansion instead of per-entry or per-nationality-pair authoring. Near-equatorial destinations (Nigeria, Ghana) use a two-block wet/dry pattern instead of four temperate seasons, and Jamaica's wet-season block is explicitly labelled `HURRICANE_SEASON` — genuine climate variety rather than a uniform template stamped onto every destination, the same principle behind Destination Intelligence differentiating region-appropriate attributes per city.

**Risk Assessor returns a structured object, not a flat list — the module's one legitimate deviation from every other Discovery module's Risk Assessor shape.** Flight/Accommodation/Destination/Budget/Visa's Risk Assessors all return `list[str]`. `WeatherRiskAssessor.assess()` returns `{risks, transport_disruption_risk, natural_hazard_risk, health_risk, safety_summary}` because the WeatherAssessment model requires those three categorical risk-level fields and a safety summary as distinct fields, not just itemized messages — the task's model spec asks for both structured risk levels and free-text risk messages, and a flat list can't carry both. Still property-intrinsic only; no preferences parameter, preserving the one invariant every Risk Assessor does share.

**No coupling to Destination or Budget Intelligence, per the task's explicit constraint.** `ai/discovery/weather/` has no import from `ai/discovery/destinations/` or `ai/discovery/budget/`, and `services/api/app/domains/weather/service.py` has no import from `app.domains.destinations` or `app.domains.budget`. The only cross-domain read is Trip context (`destination`, linked `goal_type`) as a convenience default — the same pattern every other Discovery module's service layer already uses for Trip integration, and explicitly not what the constraint was guarding against (it names Destination and Budget specifically, not Trips).

**Two entity-extraction bugs were found and fixed while verifying the task's own conversation examples**, both pre-existing in shared code (`IntentClassifier._extract_entities()`), not new to this module:

1. *"Is July a good time to **visit** Japan?"* was extracting the destination as `"Visit"` — the `"to "` marker (checked before `"visit "`) matched `"time **to** visit Japan"` first and took the word immediately following, which was `"visit"` itself. Fixed by adding `"visit"` to the marker's own exclusion list, so the search correctly falls through to the `"visit "` marker on the next iteration.
2. *"Will it **rain** in Jamaica"* was extracting no destination at all — `"in "` matched *inside* the word `"rain"` (`r` + `ain` + `" "`) before ever reaching the real `"in Jamaica"`. Fixed by requiring a leading space before every destination marker, so `"in "` only matches a standalone word, not a substring of an unrelated word.

Both were verified against every existing conversation/intent test (467 tests passing before this module, 574 after) before being folded into this change, and both are now individually regression-tested.

**`"weather in"` and `"best time to visit"`/`"best time to go"` reclaimed from `DESTINATION_QUESTION`/`TRAVEL_ADVICE`**, the same reclaiming pattern Visa Intelligence used for `"visa requirements for"` (ADR-015) — both were generic catch-all phrases before a dedicated weather engine existed.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Require `month_of_travel` on every request | Fails the task's own "When should I visit Spain?" example, which supplies no month at all — the question is only answerable if "find the best month" is a legitimate mode |
| Force unknown destinations to `NOT_RECOMMENDED` | Misrepresents genuine uncertainty as a confirmed negative assessment; low confidence plus an explicit risk flag is the honest signal |
| Hand-author all 120 destination/month climate entries | Same rejection as Destination Intelligence's per-entry objective scores (ADR-013) and Visa Intelligence's 80 nationality/destination pairs (ADR-015) — unmaintainable, and the season-block expansion produces the same illustrative variety with a fraction of the authored data |
| Keep `WeatherRiskAssessor.assess()` returning `list[str]` and compute the three risk-level fields elsewhere (e.g. in the Normalizer) | The risk levels are inherently risk-domain judgements (how severe is this hazard combination), not objective climate facts — they belong with the Risk Assessor's other reasoning, not folded into the Normalizer's property-intrinsic climate description |
| Read Destination Intelligence's catalogue for shared city/region data instead of maintaining a separate climate table | Directly contradicts the task's explicit independence constraint; a shared-data import would be exactly the tight coupling the constraint rules out |

## Consequences

- Weather & Safety Intelligence is the sixth and final reference implementation in `docs/DISCOVERY_LAYER_PATTERN.md`, alongside Flight (ADR-010), Accommodation (ADR-012), Destination (ADR-013), Budget (ADR-014), and Visa (ADR-015) — completing the Discovery Layer as scoped in `docs/TASK_TRACKER.md`.
- 107 new tests (mock provider determinism, normalizer, scorer, reasoner, risk assessor, orchestrator, API endpoints, conversation routing, intent/decision coverage) — 574 total, all passing. Zero regressions to Flight, Accommodation, Destination, Budget, or Visa Intelligence.
- `IntentClassifier._extract_entities()`'s destination-marker fix is available to every intent, not just `WEATHER_ANALYSIS` — any existing or future intent that relies on the `"to "`/`"in "`/`"visit "`/etc. markers now gets correct word-boundary matching.
- `ai/discovery/weather/` and `services/api/app/domains/weather/` have zero import edges into Destination or Budget Intelligence, verified by inspection — the module is consumable standalone by a future Trip Brain.

## Sprint 4+ Migration Path

| Component | Upgrade |
|-----------|---------|
| `MockWeatherProvider` | Real climate/forecast data feed behind the same `month()`/`year()` interface; only the Normalizer changes |
| `WeatherScorer` | Incorporate live seasonal-event and crowd data into `weather_suitability_score` |
| `WeatherRiskAssessor` | Live advisory and disaster-alert data instead of static hazard tags |
| `WeatherRepository` | Swap for PostgreSQL adapter (same Sprint 3 migration as every other Discovery module) |
| `Intent.WEATHER_ANALYSIS` | LLM-backed classification, replacing keyword patterns and the month-name scanner |
| Climate coverage | Expand beyond the ten destinations and the season-block simplification once a real data feed replaces static authoring |
