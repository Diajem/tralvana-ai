# ADR-015: Visa Intelligence Engine

**Date**: 2026-07-10
**Status**: Accepted
**Sprint**: 2 (T-019)

## Context

T-019 adds Visa Intelligence as the fifth Discovery Layer module, built against `docs/DISCOVERY_LAYER_PATTERN.md` (ADR-011) the same way Accommodation (ADR-012), Destination (ADR-013), and Budget (ADR-014) Intelligence were. It must assess entry requirements for a traveller based on nationality, destination, trip purpose, and travel plans — explicitly **not** legal advice, using deterministic mock data only, with representative rules for ten passport nationalities and eight destinations.

A placeholder `VisaAgent` (`ai/agents/visa_agent.py`) already existed, dispatched during `PLAN_TRIP` conversations, returning a static "live visa data activates in Sprint 5" message. It is unchanged by this task — `Intent.VISA_CHECK` is new and separate, the same relationship Flight Intelligence (T-015) has to the older `flight_agent`.

## Decision

**Single assessment, not a ranked list — the module's central structural departure from the other four.** Flight/Accommodation/Destination/Budget Intelligence each rank several candidates and label them via the priority-ordered algorithm in `DISCOVERY_LAYER_PATTERN.md`. A visa check has exactly one true answer for a given passport/destination/purpose combination — there is nothing to rank. `VisaIntelligence.check()` (named to match the `POST /visa/check` verb, not `recommend()`) returns one `VisaAssessment`. The Discovery Layer's "Recommendation" pipeline stage still exists, just simplified to a direct `visa_status → recommendation` mapping instead of a labelling algorithm over multiple options.

**`visa_status` was added to the model despite not being in the literal field list**, to give the separately-specified 6-value `VisaStatus` enum somewhere to live. This is the module's equivalent of `recommendation_type` in the other four modules — every other Discovery module's primary categorical result lives in a same-shaped field, and `VisaStatus` has no other sensible home given `visa_required`/`travel_authorisation_required` are derived booleans, not the full 6-way categorization.

**Two-tier passport "strength" + eight destination policies, not 80 hand-authored nationality/destination pairs.** Same technique Destination Intelligence used for its objective scores (ADR-013): a formula (tier × destination policy) rather than hand-tuned figures for every combination. Real visa policy has far more nuance than a two-tier split — this is explicitly documented as illustrative mock data, not real government policy, the same caveat Destination Intelligence applied to its mock safety/culture ratings. Specific overrides (Common Travel Area, ECOWAS free movement, same-country return) sit above the tier lookup for the handful of cases a two-tier default can't express.

**Scorer computes confidence, not a subjective preference match.** Unlike the other four modules, there is no traveller "preference" to score a visa determination against — it's an objective compliance fact about one passport/destination/purpose combination. `VisaScorer` scores **confidence** in the assessment across four weighted dimensions (`rule_specificity` 0.40, `data_completeness` 0.25, `purpose_clarity` 0.15, `transit_simplicity` 0.20) — the same "weighted, explainable dimensions summing to 1.0" shape as every other Discovery module's scorer, reinterpreted for a domain where "how sure are we" is the meaningful question rather than "how well does this match your taste." Consequently, **no DNA/goal-type adjustment layer** was added — injecting persona-based adjustment into a compliance-adjacent confidence score would be actively misleading (a football-focused and a food-focused traveller on an identical trip must get the identical visa confidence).

**Nationality-adjective aliasing was a mid-build fix, not an initial design choice.** The rule tables are naturally keyed by country name (`NIGERIA`, `IRELAND`); free-text conversation input naturally uses the adjective form (`"I am Nigerian"`, `"my Irish passport"`). The first implementation missed this and silently fell back to `CHECK_MANUALLY` for the spec's own worked example ("I am Nigerian travelling to Spain."). Fixed by extending `_ALIASES` with the adjective forms for all ten nationalities, verified by a dedicated test (`test_nationality_adjective_resolves_same_as_country_name`) and by re-running the conversation example end-to-end.

**A new nationality-and-destination fallback rule in `IntentClassifier`.** Three of the four spec examples ("Do I need a visa?", "Can I enter Japan?", "Will my Irish passport work?") match explicit keyword patterns; the fourth ("I am Nigerian travelling to Spain.") contains no visa-specific keyword at all. Rather than hardcoding every nationality into the pattern list, `classify()` gained a last-resort rule: if no explicit pattern matches but the extracted entities contain both `nationality` and `destination`, classify as `VISA_CHECK` — nationality has no other meaning in this conversation layer. It only fires after every explicit pattern has failed, so it cannot hijack an existing intent (e.g. "I'm Nigerian and want to plan a trip to Spain" still matches `PLAN_TRIP` first via `"trip to"`).

**`"visa requirements for"` reclaimed from `DESTINATION_QUESTION`.** It was a generic catch-all pattern before any visa engine existed. Moved to `VISA_CHECK`, which is checked earlier in `_PATTERNS` — verified via a regression test that the phrase now routes correctly and no existing test depended on the old routing.

**`ENTRY_RESTRICTED` is supported end-to-end but not emitted by the mock data.** None of the eight specified destinations realistically warrant it, and fabricating a "restricted" pairing among real countries risks reading as editorial commentary on real geopolitics rather than illustrative mock data — a real concern for a travel product's mock dataset in a way it wasn't for, say, Destination Intelligence's safety ratings. It's exercised via direct unit tests constructing that status explicitly, and reserved for future rule additions.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Force a ranked-candidates shape (e.g. rank visa "options" like visa-on-arrival vs. e-visa vs. embassy visa) | A real traveller doesn't choose between visa types the way they choose between flights — there is one correct entry-requirement answer per passport/destination/purpose. Forcing a ranking would fabricate false choice |
| Hand-author all 80 nationality/destination pairs | Same rejection as Destination Intelligence's per-entry objective scores (ADR-013) — unmaintainable, and the tier+policy formula produces the same illustrative variety with 8 destination policies × 2 tiers instead of 80 |
| Reuse `DestinationScorer`'s DNA/goal-adjustment pattern for confidence | Would make visa confidence vary by travel persona for an identical trip — actively misleading for a compliance-adjacent number, not just unnecessary |
| Keep `"visa requirements for"` under `DESTINATION_QUESTION` and duplicate it under `VISA_CHECK` too | `VISA_CHECK` is checked earlier in priority order regardless, so a duplicate entry would be dead weight — moving it is the same net behaviour with less redundant data |
| Skip the nationality-and-destination fallback and require the user to say "visa" explicitly | Fails the spec's own fourth example; travellers naturally state nationality + destination without the word "visa" when the intent is contextually obvious |

## Consequences

- Visa Intelligence is the fifth reference implementation in `docs/DISCOVERY_LAYER_PATTERN.md`, alongside Flight (ADR-010), Accommodation (ADR-012), Destination (ADR-013), and Budget (ADR-014) — and the first to document a legitimate structural deviation (single assessment, not ranked candidates) from the pattern's ranking/labelling stage.
- 100 new tests (mock provider determinism, normalizer, scorer, reasoner, risk assessor, orchestrator, API endpoints, conversation routing, intent/decision coverage) — 467 total, all passing. Zero regressions to Flight, Accommodation, Destination, or Budget Intelligence, and zero changes to the existing `visa_agent` placeholder's `PLAN_TRIP` behaviour.
- `IntentClassifier._extract_entities()` gained a `nationality` entity and an `"enter "` destination marker — additive changes available to every intent, not just `VISA_CHECK`.
- Every assessment carries an explicit "not legal advice" disclaimer in `assumptions` and on both frontend pages, consistent with the constraint that this is travel-planning intelligence, not a compliance guarantee.

## Sprint 4+ Migration Path

| Component | Upgrade |
|-----------|---------|
| `MockVisaProvider` | Real immigration/Timatic-style data feed behind the same `lookup()` signature; only the Normalizer changes |
| `VisaScorer` | Incorporate live rule-change-frequency data into `rule_specificity` |
| `VisaRiskAssessor` | Live travel-advisory and entry-ban data instead of static heuristics |
| `VisaRepository` | Swap for PostgreSQL adapter (same Sprint 3 migration as Goals/Trips/Flights/Accommodation/Destinations/Budget) |
| `Intent.VISA_CHECK` | LLM-backed classification, replacing keyword patterns and the nationality-fallback heuristic |
| Rule coverage | Expand beyond the ten nationalities / eight destinations and the two-tier simplification once a real data feed replaces static authoring |
