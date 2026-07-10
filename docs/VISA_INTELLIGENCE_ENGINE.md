# Visa Intelligence Engine

T-019 — the fifth Discovery Layer module. Assesses entry requirements for a traveller based on nationality, destination, trip purpose, and travel plans.

**This is explainable travel-planning intelligence, not legal advice.** Every assessment is built from a deterministic mock rule set — no live government service, embassy data, or Timatic-style database is queried. Always verify with an official government source before travelling.

## Architecture

```
Provider → Normalizer → Scorer → Reasoner → Risk Assessor → Recommendation → Explanation
```

| Stage | Module | Responsibility |
|-------|--------|-----------------|
| Domain | `services/api/app/domains/visa/` | VisaAssessment model, REST API, in-memory repo |
| Provider | `ai/discovery/visa/mock_visa_provider.py` | Deterministic rule lookup: tier + destination policy, overrides, same-country, unknown fallback |
| Normalizer | `ai/discovery/visa/visa_normalizer.py` | Raw → canonical schema; computes passport validity, requirement lists, `visa_required`/`travel_authorisation_required` |
| Scorer | `ai/discovery/visa/visa_scorer.py` | Confidence in the assessment (not a subjective preference match — see below) |
| Reasoner | `ai/discovery/visa/visa_reasoner.py` | Human-readable explanation from the score breakdown |
| Risk Assessor | `ai/discovery/visa/visa_risk_assessor.py` | Six required risk categories (see below) |
| Orchestrator | `ai/discovery/visa/visa_intelligence.py` | Wires the above together, resolves transit implications, produces the recommendation |
| Conversation | `ai/concierge/conversation_engine.py` | Routes `VISA_CHECK` intent directly to this engine |

See `docs/DISCOVERY_LAYER_PATTERN.md` for the general pipeline. Visa Intelligence follows it with one deliberate structural difference from Flight/Accommodation/Destination/Budget Intelligence, documented in ADR-015: it assesses **one** specific passport/destination/purpose combination rather than ranking several candidates. There is nothing to rank, so there is no labelling algorithm — the single `recommendation` field takes its place.

## Relationship to the Existing `visa_agent`

A placeholder `VisaAgent` (`ai/agents/visa_agent.py`) already existed, dispatched during `PLAN_TRIP` conversations. It returns a static "live visa data activates in Sprint 5" message and is unchanged — `PLAN_TRIP` still dispatches it exactly as before. `Intent.VISA_CHECK` is a new, separate, directly-routed intent (same relationship Flight Intelligence has to the older `flight_agent`): a traveller asking a direct visa question gets a real deterministic assessment from this module, not the placeholder.

## Mock Rule Set

**Ten representative passport nationalities**, split into two illustrative "strength tiers" (a deliberate simplification — mock data, not real government policy):

- **Strong tier**: UK, Ireland, USA, Canada, Japan, EU (generic)
- **Developing tier**: Nigeria, Ghana, South Africa, Jamaica

**Eight destinations**: Japan, USA, UK, Ireland, France, Spain, Nigeria, UAE — each with a base policy per tier (formula-derived, not hand-authored per nationality pair — the same "formula, not hundreds of hand-tuned values" approach Destination Intelligence used for its objective scores, ADR-013).

**Specific overrides** checked before the tier lookup, for real regional agreements a two-tier default can't express: Common Travel Area (UK ↔ Ireland) and ECOWAS free movement (Ghana → Nigeria). A traveller returning to their own passport country always resolves to `VISA_NOT_REQUIRED` regardless of tier.

**Aliases**: both ISO 3166-1 alpha-2 codes (`NG`, `GB`, `IE`, ...) and natural-language nationality adjectives (`Nigerian`, `Irish`, `British`, ...) resolve to the same canonical key, so profile data (which stores ISO-2 codes) and free-text conversation input (which uses adjectives) both work.

**Purpose escalation**: a tourism/business/transit/family-visit waiver never covers `STUDY` or `WORK` — those always escalate to `VISA_REQUIRED` regardless of passport tier, a deliberately simple and realistic rule.

**Unmapped pairs** (a nationality or destination outside the above lists) resolve to `CHECK_MANUALLY` with an `"unknown"` match type, which downstream stages use to lower confidence and flag the "unknown rule" risk.

## VisaAssessment Fields

| Field | Type | Description |
|-------|------|-------------|
| `visa_assessment_id` | str | UUID |
| `traveller_id` / `trip_id` | str \| None | Linked traveller / trip |
| `nationality` | str | Display nationality; defaults to `passport_country` if not supplied separately |
| `passport_country` | str | The passport actually used for the rule lookup |
| `destination_country` | str | — |
| `transit_countries` | list[str] | Countries the traveller passes through en route |
| `travel_purpose` | str | One of the 7 `TravelPurpose` values below |
| `intended_length_of_stay` | int | Days |
| `passport_expiry_date` | str \| None | ISO date; when supplied, drives `passport_validity_months` |
| `passport_validity_months` | float \| None | Computed from `passport_expiry_date` to today |
| `visa_status` | str | One of the 6 `VisaStatus` values below — this module's equivalent of `recommendation_type` |
| `visa_required` | bool | True for `VISA_REQUIRED`/`ENTRY_RESTRICTED` |
| `visa_type` | str | e.g. `"ESTA"`, `"Schengen Short-Stay Visa"`, `"None"` |
| `entry_requirements` | list[str] | What's needed to enter |
| `supporting_documents` | list[str] | What to carry/present |
| `vaccination_requirements` | list[str] | Currently populated only for Nigeria (Yellow Fever) |
| `travel_authorisation_required` | bool | True for `ETA_REQUIRED`/`EVISA_AVAILABLE` |
| `processing_time` | str | e.g. `"3-5 business days"` |
| `confidence` | float | 0.0–1.0, from the Scorer |
| `risks` | list[str] | Per-assessment risk flags |
| `assumptions` | list[str] | Per-assessment assumptions |
| `recommendation` | str | Short, direct next-step call-to-action |
| `explanation` | str | Full reasoning paragraph, from the Reasoner |
| `created_at` | str | — |

## Visa Status

`VISA_NOT_REQUIRED`, `VISA_REQUIRED`, `ETA_REQUIRED`, `EVISA_AVAILABLE`, `CHECK_MANUALLY`, `ENTRY_RESTRICTED`. Note: `ENTRY_RESTRICTED` is fully supported by every downstream stage but not emitted by any of the eight mock destination policies — none of the eight specified destinations realistically warrant it, and inventing a "restricted" pairing among real countries risks reading as editorial commentary rather than illustrative mock data. It's covered by direct unit tests and reserved for future rule additions.

## Travel Purpose

`TOURISM`, `BUSINESS`, `TRANSIT`, `STUDY`, `WORK`, `FAMILY_VISIT`, `OTHER`.

## Scoring — Confidence, Not Preference Match

Unlike Flight/Accommodation/Destination/Budget Intelligence, there is no traveller "preference" to score against — a visa determination is an objective compliance fact about one passport/destination/purpose combination, not a matter of taste. `VisaScorer` therefore computes **confidence** in the assessment rather than a subjective `match_score`, across four weighted dimensions summing to 1.0: `rule_specificity` (0.40 — override/same-country match scores highest, tier match next, unknown lowest), `data_completeness` (0.25 — was a passport expiry date supplied? was purpose specified?), `purpose_clarity` (0.15 — tourism/business is well-supported, study/work needs consulate-level assessment so scores lower), `transit_simplicity` (0.20 — each transit country reduces confidence, floored at 0.3).

**No DNA/goal-type adjustment layer** — a deliberate deviation from the other four Discovery modules. Injecting persona-based adjustment into a compliance-adjacent confidence score would be actively misleading: a football-focused traveller shouldn't get a different visa confidence than an identical trip for a food-focused traveller. See ADR-015.

## Risk Assessment

Six required categories, all property-intrinsic (no preferences parameter, same convention as every other Discovery module's Risk Assessor):

1. **Passport expiry risk** — expiry date not supplied, or less than 6 months' validity remains (the common international rule)
2. **Insufficient validity** — passport validity shorter than the intended stay, or the intended stay exceeds the entry category's `max_stay_days`
3. **Transit visa risk** — any transit country that itself requires a visa/authorisation for this passport
4. **Missing documentation** — travel purpose was `OTHER` (documentation requirements can't be pinned down)
5. **Unknown rule** — the passport/destination pair fell back to `CHECK_MANUALLY`
6. **Low confidence** — `confidence < 0.5`

## Conversation Integration

A new `Intent.VISA_CHECK` was added, checked before `PLAN_TRIP` (patterns: `"do i need a visa"`, `"can i enter"`, `"passport work"`, `"visa requirements for"`, etc.). `"visa requirements for"` was reclaimed from `DESTINATION_QUESTION`, which previously had no dedicated engine to route it to.

A new fallback rule in `IntentClassifier.classify()` handles messages with no explicit visa keyword but that state both a nationality and a destination — e.g. *"I am Nigerian travelling to Spain."* Nationality is not otherwise relevant to any intent in this conversation layer, so stating it alongside a destination is treated as an implicit visa-check signal. This only fires after every explicit pattern has failed to match, so it cannot hijack an existing intent (e.g. *"I'm Nigerian and want to plan a trip to Spain"* still matches `PLAN_TRIP` first).

Entity extraction was extended with a `nationality` entity (from `"I am X"` / `"I'm X"` / `"my X passport"` phrasing) and a new `"enter "` destination marker (for `"Can I enter Japan?"`).

Unlike `DESTINATION_DISCOVERY`/`BUDGET_ANALYSIS`, `VISA_CHECK` is **not** always-ready — both nationality and destination are required, since there is no useful "generic" visa answer without them. `DecisionEngine` asks for whichever is missing and maps the intent to zero specialist agents; `ConversationEngine._get_visa_assessment()` calls the service directly once both are present, matching the other Discovery intents' direct-routing pattern.

## Constraints

- No live government services, no Timatic, no external APIs
- No legal advice — every response and the frontend both carry this disclaimer
- Deterministic mock data only — same inputs always produce the same assessment
- Sprint 4+: swap `MockVisaProvider` for a real immigration data feed; only the Normalizer changes
