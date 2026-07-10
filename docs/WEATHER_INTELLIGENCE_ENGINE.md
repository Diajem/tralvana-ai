# Weather & Safety Intelligence Engine

T-020 — the sixth and final Discovery Layer module. Determines how weather, climate, seasonality, and safety affect the traveller's overall trip experience for a destination and month.

**This is a travel decision engine, not a weather forecast.** Every assessment is built from a deterministic mock climate profile — no OpenWeather, WeatherAPI, AccuWeather, or any other live forecast/advisory service is queried. Always check an official forecast closer to your travel date.

## Architecture

```
Provider → Normalizer → Scorer → Reasoner → Risk Assessor → Recommendation → Explanation
```

| Stage | Module | Responsibility |
|-------|--------|-----------------|
| Domain | `services/api/app/domains/weather/` | WeatherAssessment model, REST API, in-memory repo |
| Provider | `ai/discovery/weather/mock_weather_provider.py` | Deterministic monthly climate profiles for 10 destinations |
| Normalizer | `ai/discovery/weather/weather_normalizer.py` | Raw → canonical schema; computes objective `outdoor_activity_score`/`photography_score`/`family_score` |
| Scorer | `ai/discovery/weather/weather_scorer.py` | `weather_suitability_score` (subjective composite) and `confidence` |
| Reasoner | `ai/discovery/weather/weather_reasoner.py` | Human-readable explanation and packing advice |
| Risk Assessor | `ai/discovery/weather/weather_risk_assessor.py` | 9 required risk categories plus 3 categorical risk levels |
| Orchestrator | `ai/discovery/weather/weather_intelligence.py` | Wires the above together, finds the best month, resolves alternatives |
| Conversation | `ai/concierge/conversation_engine.py` | Routes `WEATHER_ANALYSIS` intent directly to this engine |

See `docs/DISCOVERY_LAYER_PATTERN.md` for the general pipeline. Weather Intelligence follows Visa Intelligence's precedent (ADR-015) of producing **one** assessment rather than a ranked list — there's no "best weather option" to rank, a specific destination/month pair has one assessment. It combines this with Destination Intelligence's dual-mode precedent (ADR-013): a specific month assesses that month; an omitted month finds the best month across the year and assesses that one instead. See ADR-016.

## Independence from Other Discovery Modules

Per the task's explicit integration constraint, Weather Intelligence has **no import from `ai/discovery/destinations/` or `ai/discovery/budget/`**, and `services/api/app/domains/weather/service.py` has no import from `app.domains.destinations` or `app.domains.budget`. It only reads Trip context (`destination`, linked `goal_type`) as a convenience default, the same pattern every other Discovery module's service layer already uses. This keeps the module consumable standalone by a future Trip Brain without a dependency edge into another Discovery module's internals.

## Mock Climate Profiles

**Ten destinations**: Japan, Spain, France, United Kingdom, Ireland, USA, Nigeria, Ghana, Jamaica, UAE. Each destination is authored as 2-4 season blocks (not 12 individually hand-tuned months), then expanded to all 12 months — the same "formula, not hundreds of hand-tuned values" technique Destination Intelligence used for its objective scores (ADR-013) and Visa Intelligence used for its tier × destination policy table (ADR-015).

**Genuine climate variety, not a uniform template**: temperate destinations (Japan, Spain, France, UK, Ireland, USA) use four seasons (`WINTER`/`SPRING`/`SUMMER`/`AUTUMN`); near-equatorial destinations (Nigeria, Ghana) use a two-block wet/dry pattern (`DRY_SEASON`/`WET_SEASON`); Jamaica's wet season is explicitly labelled `HURRICANE_SEASON`; UAE uses `MILD_SEASON`/`HOT_SEASON`. Each block carries an average temperature, rainfall level, humidity level, daylight hours, and a list of hazard tags (`typhoon`, `hurricane`, `flood`, `wildfire`, `extreme_heat`, `extreme_cold`) — covering every category the Risk Assessor is required to detect. All figures are illustrative mock climate archetypes, not a real forecast.

## WeatherAssessment Fields

| Field | Type | Description |
|-------|------|-------------|
| `weather_assessment_id` | str | UUID |
| `traveller_id` / `trip_id` | str \| None | Linked traveller / trip |
| `destination` | str | Display name (e.g. `"United Kingdom"`, not `"UK"`) |
| `month_of_travel` | int | 1-12; the assessed month (requested, or the best month if omitted) |
| `season` | str | e.g. `"SPRING"`, `"WET_SEASON"`, `"HURRICANE_SEASON"` — destination-appropriate, not a fixed 4-value enum |
| `average_temperature` | float \| None | °C |
| `rainfall_level` / `humidity_level` | str | `LOW` \| `MODERATE` \| `HIGH` \| `VERY_HIGH` |
| `daylight_hours` | float \| None | Average hours/day |
| `weather_summary` | str | One-line climate description |
| `weather_suitability_score` | float | 0.0–1.0, subjective (Scorer) — this module's equivalent of `match_score` |
| `outdoor_activity_score` / `photography_score` / `family_score` | float | 0.0–1.0, objective (Normalizer) |
| `transport_disruption_risk` / `natural_hazard_risk` / `health_risk` | str | `LOW` \| `MODERATE` \| `HIGH` \| `SEVERE`, from the Risk Assessor |
| `personal_suitability` | str | Short sentence bridging the score to this specific traveller, incorporating one DNA note when available |
| `packing_recommendations` | list[str] | Derived from temperature, rainfall, humidity, and active hazards |
| `safety_summary` | str | One-line safety narrative, distinct from the itemized `risks` list |
| `risks` | list[str] | Itemized risk flags |
| `assumptions` | list[str] | Per-assessment assumptions |
| `confidence` | float | 0.0–1.0, from the Scorer |
| `weather_status` | str | One of the 5 `WeatherStatus` values below — this module's equivalent of `recommendation_type` |
| `alternative_months` | list[dict] | Up to 2 months that score meaningfully better, each with `month`, `month_name`, `weather_status`, `weather_suitability_score` |
| `recommendation` | str | Short, direct next-step call-to-action |
| `explanation` | str | Full reasoning paragraph, from the Reasoner |
| `created_at` | str | — |

`weather_status` and `alternative_months` are not in the task's literal field list but were added for the same reason Visa Intelligence added `visa_status` (ADR-015): the separately-specified `WeatherStatus` enum needs somewhere to live, and the required "alternative travel month" narrative needs structured data for the frontend to render, not just prose.

## Weather Status

`EXCELLENT` (≥0.85), `GOOD` (≥0.65), `ACCEPTABLE` (≥0.45), `CHALLENGING` (≥0.25), `NOT_RECOMMENDED` (<0.25) — thresholds on `weather_suitability_score`.

**Unknown destinations get a neutral status, not a punitive one.** With no climate data, the Normalizer's comfort inputs default to neutral (0.5), which typically resolves to `ACCEPTABLE` — not `NOT_RECOMMENDED`, which would incorrectly imply confirmed bad conditions we don't actually know about. The uncertainty is instead communicated honestly through low `confidence` (0.3) and an explicit "no climate data available" risk flag. `VisaStatus` has a dedicated `CHECK_MANUALLY` bucket for this case; `WeatherStatus`'s fixed 5-value enum has no equivalent, so confidence carries that signal instead.

## Scoring

`WeatherScorer` computes `weather_suitability_score` across five weighted dimensions summing to 1.0: `temp_fit` (0.30 — how close to an ideal ~21°C), `rainfall_fit` (0.25), `humidity_fit` (0.15), `hazard_fit` (0.20 — inverse of active hazard count), `daylight_fit` (0.10). A DNA/goal-type adjustment layer (±0.04–0.06) follows: `adventure_seeking` reduces the deterrent effect of hazards, `photography_tendency`/`PHOTOGRAPHY` goal boosts months with strong `photography_score`, `family_orientation`/`FAMILY_TRIP` goal boosts months with strong `family_score`, `ADVENTURE` goal reduces hazard sensitivity further. Every adjustment is logged and surfaces in `personal_suitability` and `explanation`.

`confidence` reflects whether the destination was recognised (0.9 when matched, 0.3 when not) — simpler than Budget/Visa Intelligence's multi-dimensional confidence, since Weather Intelligence has only one real source of uncertainty: does the mock catalogue cover this destination at all.

## Dual-Mode Requests

`month_of_travel` is optional. **Month given** — assess that specific month (e.g. `"Is July a good time to visit Japan?"`). **Month omitted** — score all 12 months internally and assess the best one (e.g. `"When should I visit Spain?"`), recording an assumption explaining the substitution. This mirrors Destination Intelligence's city vs. no-city dual mode (ADR-013): both are genuinely common, useful questions.

**Alternative months**: whenever the year has been scored (i.e. the destination is known), any other month scoring at least 0.05 higher than the assessed month is surfaced as an alternative, capped at 2, sorted best-first. In best-month mode, this list is always empty — by construction, nothing scores higher than the month already selected.

## Risk Assessment

Nine required categories. Unlike the other five Discovery modules' Risk Assessors (which return a flat `list[str]`), `WeatherRiskAssessor.assess()` returns a richer structure — the itemized `risks` list plus the three categorical risk-level fields and `safety_summary` — because the WeatherAssessment model requires those as distinct fields, not just itemized messages. Still property-intrinsic only, no preferences parameter, same convention as every other Discovery module's Risk Assessor.

| Category | Trigger |
|----------|---------|
| Heavy rain | `rainfall_level` is `HIGH` or `VERY_HIGH` |
| Extreme heat | `extreme_heat` hazard tag, or average temperature ≥ 32°C |
| Extreme cold | `extreme_cold` hazard tag, or average temperature ≤ 0°C |
| Typhoon season | `typhoon` hazard tag (Japan, Jun-Nov) |
| Hurricane season | `hurricane` hazard tag (USA Jun-Nov, Jamaica May-Nov) |
| Flood risk | `flood` hazard tag |
| Wildfire season | `wildfire` hazard tag (Spain, Jun-Aug) |
| Transport disruption | Any of flood/typhoon/hurricane present, or very high rainfall |
| Health considerations | High heat + very high humidity (heat stress), or flood + heavy rainfall (mosquito-borne illness) |

## Conversation Integration

A new `Intent.WEATHER_ANALYSIS` was added, checked before `PLAN_TRIP`. `"weather in"` was reclaimed from `DESTINATION_QUESTION` and `"best time to visit"`/`"best time to go"` from `TRAVEL_ADVICE` — both had no dedicated engine to route to before this module existed, the same reclaiming pattern Visa Intelligence used for `"visa requirements for"` (ADR-015).

Two entity-extraction fixes were needed to make the task's own conversation examples work, both regression-tested:

1. **`"visit"` added to the destination-marker exclusion list** — `"Is July a good time to visit Japan?"` contains `"...time **to** visit Japan"`, and the `"to "` marker (checked before `"visit "`) was extracting the word `"visit"` itself as the destination.
2. **Word-boundary padding on all destination markers** — `"Will it rain in Jamaica"` was extracting no destination at all, because `"in "` matched *inside* the word `"rain"` (`ra` + `in ` ) before ever reaching the real `"in Jamaica"`. Every marker search now requires a leading space, so `"in "` only matches a standalone word.

Like `DESTINATION_DISCOVERY` and `BUDGET_ANALYSIS`, `WEATHER_ANALYSIS` requires only a destination — a month is never required, since the "no month" best-month mode is itself a complete, useful answer. `DecisionEngine` maps it to zero specialist agents; `ConversationEngine._get_weather_assessment()` calls the service directly.

## Constraints

- No OpenWeather, WeatherAPI, AccuWeather, or any other external weather/climate API
- No booking, no payment
- Deterministic mock data only — same destination and month always produce the same assessment
- Sprint 4+: swap `MockWeatherProvider` for a real climate data feed; only the Normalizer changes
