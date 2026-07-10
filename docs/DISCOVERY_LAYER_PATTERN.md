# Discovery Layer Pattern

The standard structure every Discovery module follows. Formalised in T-016 from the precedent set by Flight Intelligence (T-015); Accommodation Intelligence (T-016) is the first module built directly against this document rather than by example.

## Why a Discovery Layer

Tralvana Travel does not "search and list" — it reasons about which option best fits the traveller, goal, budget, trip plan, and preferences, and explains why. Every Discovery module (Flight, Accommodation, Destination, Budget, Visa, and future Weather modules per `docs/TASK_TRACKER.md`) exists to turn a category of raw options into ranked, explainable recommendations. A consistent internal pipeline means a new engineer who has read one Discovery module already understands the shape of every other one.

## The Pipeline

```
Provider → Normalizer → Scorer → Reasoner → Risk Assessor → Recommendation → Explanation
```

| Stage | File | Responsibility | Knows about traveller preferences? |
|-------|------|-----------------|:---:|
| **Provider** | `mock_<domain>_provider.py` | Returns raw candidate data in whatever shape a real external provider would use | No |
| **Normalizer** | `<domain>_normalizer.py` | Converts raw provider data into the module's canonical internal schema; computes **objective**, preference-independent scores intrinsic to the option itself | No |
| **Scorer** | `<domain>_scorer.py` | Computes the **subjective** `match_score` (0.0–1.0) by weighting normalized fields against a specific traveller's preferences, DNA, and goal type | Yes |
| **Reasoner** | `<domain>_reasoner.py` | Turns the scorer's breakdown into a human-readable explanation — every sentence traceable to a specific field or weighted dimension | Yes (via the score breakdown) |
| **Risk Assessor** | `<domain>_risk_assessor.py` | Flags property-intrinsic risks from the normalized data alone (not preference-dependent) | No |
| **Recommendation** | Orchestrator (`<domain>_intelligence.py`) | Ranks by `match_score`, assigns exactly one `recommendation_type` per option via the priority-ordered labelling algorithm (see below) | — |
| **Explanation** | Orchestrator output | The full response: ranked options, `assumptions`, `next_actions`, `recommended_agents`, `summary` | — |

### Why Provider and Normalizer are separate

The Provider returns data shaped however a real external API would return it — inconsistent field names, nested structures, provider-specific vocabulary. The Normalizer is the only place that translates that raw shape into the module's canonical schema. Every other stage (Scorer, Reasoner, Risk Assessor) only ever sees normalized data and never needs to change when a provider is swapped.

**Flight Intelligence (T-015) is a documented exception, not a counter-example.** Its `MockFlightProvider.search()` was written to already emit normalized dicts directly, because Sprint 1 had exactly one provider and the raw/normalized distinction added no value yet. This is acceptable for a first implementation but is **not** the pattern going forward — every Discovery module from Accommodation Intelligence (T-016) onward must have an explicit Normalizer file, because:

1. It is where **objective, provider-independent scores** are computed (e.g. Accommodation's `comfort_score`, `location_score`, `safety_score` — properties of the option itself, not of any one traveller).
2. It is the seam a real provider integration slots into without touching scoring/reasoning/risk logic at all.

### Objective vs. subjective scores

A Discovery module typically produces two kinds of scores, computed at different stages:

- **Objective scores** (Normalizer): intrinsic to the option, the same for every traveller. E.g. a hotel's `comfort_score` derived from its star rating and amenities doesn't change based on who's asking.
- **Subjective score** (Scorer): `match_score`, computed by weighting normalized fields (including the objective scores) against one traveller's specific preferences, DNA, and goal type. Two travellers see the same options with different `match_score`s.

## Recommendation Labelling Algorithm

Every option in a response must receive **exactly one** `recommendation_type` — no duplicates, no gaps. Applied in priority order so no option is labelled twice:

1. **AVOID** — any option with `match_score` below the module's avoid threshold (0.35 in both Flight and Accommodation Intelligence) is filtered out first.
2. **BEST_OVERALL** — highest `match_score` among what's left.
3. Module-specific "objective winner" categories (e.g. Flight's `LOWEST_PRICE`, `SHORTEST_DURATION`) each claim one option from what's left, in a fixed order.
4. **Persona categories** (e.g. `BEST_FOR_FAMILY`, `BEST_FOR_BUSINESS`, `BEST_FOR_COMFORT`/`BEST_COMFORT`, `BEST_FOR_BUDGET`/`BEST_BUDGET`) each claim their best-fit remaining option via independently computed persona sub-scores.
5. Any option still unlabelled (more candidates than categories) falls back to its own single best-fit persona, computed from its own persona sub-scores — guaranteeing full coverage regardless of how many candidates the Provider returns.

## Required Structure Checklist

Every Discovery module must have:

- [ ] **Provider** — `ai/discovery/<domain>/mock_<domain>_provider.py`, deterministic (no unseeded randomness — same inputs always produce the same candidates), returns raw provider-shaped dicts
- [ ] **Normalizer** — `ai/discovery/<domain>/<domain>_normalizer.py`, raw → canonical schema, computes objective scores
- [ ] **Scorer** — `ai/discovery/<domain>/<domain>_scorer.py`, weighted dimensions summing to 1.0, plus a DNA/goal-type adjustment layer, returns `match_score` + a `breakdown` dict for explainability
- [ ] **Reasoner** — `ai/discovery/<domain>/<domain>_reasoner.py`, one `explain()` method producing a traceable sentence-by-sentence explanation from the breakdown
- [ ] **Risk Assessor** — `ai/discovery/<domain>/<domain>_risk_assessor.py`, one `assess()` method, property-intrinsic only, no preferences parameter
- [ ] **Orchestrator** — `ai/discovery/<domain>/<domain>_intelligence.py`, wires the above into one `recommend()` call, applies the labelling algorithm
- [ ] **Domain layer** — `services/api/app/domains/<domain>/` with `models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py` (same five files as `goals/`, `trips/`, `flights/`)
- [ ] **API contract** — `POST /<domain>/recommend`, `GET /<domain>/{<domain>_option_id}`, `GET /trips/{trip_id}/<domain>` — same three-endpoint shape as Flights
- [ ] **Conversation integration** — a dedicated `Intent`, routed as a direct `ConversationEngine` call (not through `TravelManager`/`AgentRegistry`), matching how `FLIGHT_SEARCH` and Goal/Trip creation already work
- [ ] **Frontend** — `apps/web/src/app/<domain>/recommend/page.tsx` (form + ranked results) and `apps/web/src/app/<domain>/[id]/page.tsx` (detail view)
- [ ] **Tests** — unit tests for the Scorer, Risk Assessor, and orchestrator (ranking, uniqueness of `recommendation_type`, determinism), API endpoint tests, conversation routing tests
- [ ] **Docs** — `docs/<DOMAIN>_INTELLIGENCE_ENGINE.md`, `docs/API_<DOMAIN>.md`, and an ADR

## Constraints (apply to every Discovery module)

- No live external provider APIs, no booking, no payment
- Deterministic mock data only — same inputs always produce the same candidates and prices
- Provider interface must be real-integration-ready: a future adapter only implements the Provider's `search()` signature; nothing downstream changes
- Keep it simple — a Discovery module is Provider → Normalizer → Scorer → Reasoner → Risk Assessor → Recommendation, not more layers than that

## Reference Implementations

| Module | Domain | AI Package | ADR |
|--------|--------|-------------|-----|
| Flight Intelligence | `services/api/app/domains/flights/` | `ai/discovery/flights/` | ADR-010 |
| Accommodation Intelligence | `services/api/app/domains/accommodation/` | `ai/discovery/accommodation/` | ADR-012 |
| Destination Intelligence | `services/api/app/domains/destinations/` | `ai/discovery/destinations/` | ADR-013 |
| Budget Intelligence | `services/api/app/domains/budget/` | `ai/discovery/budget/` | ADR-014 |
| Visa Intelligence | `services/api/app/domains/visa/` | `ai/discovery/visa/` | ADR-015 |
