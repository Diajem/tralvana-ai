# ADR-011: Discovery Layer Pattern

**Date**: 2026-07-09
**Status**: Accepted
**Sprint**: 2 (T-016)

## Context

T-015 built Flight Intelligence — the first Discovery Layer module — without a written pattern to follow, since it was the first of its kind. T-016 adds Accommodation Intelligence as the second module and explicitly asks for the pattern to be documented first, so Accommodation (and every Discovery module after it — Destination, Visa, Weather per `ROADMAP.md` T-017–T-019) is built *against* a standard rather than by copying Flight Intelligence file-by-file and hoping the shape stays consistent.

Reviewing Flight Intelligence's actual structure before writing the pattern surfaced one real gap: `MockFlightProvider.search()` emits already-normalized dicts directly. There is no separate normalizer file. This worked because Sprint 1 had exactly one provider and the raw/normalized distinction had no payoff yet — but it means Flight Intelligence doesn't literally have all seven pipeline stages as separate files, even though the task's required architecture is `Provider → Normalizer → Scorer → Reasoner → Risk Assessor → Recommendation → Explanation`.

## Decision

**Document the seven-stage pipeline** in `docs/DISCOVERY_LAYER_PATTERN.md`, with Provider and Normalizer as genuinely separate concerns:
- **Provider**: raw, provider-shaped data (deterministic, mock in Sprint 1)
- **Normalizer**: raw → canonical internal schema, and the place where **objective** (preference-independent) scores are computed
- **Scorer**: the **subjective** `match_score`, computed against one traveller's preferences/DNA/goal — everything downstream of the Normalizer

**Treat Flight Intelligence's missing Normalizer as a documented precedent, not a violation.** Retroactively splitting `flight_intelligence.py` into a separate normalizer file is out of scope for T-016 ("do not over-complicate the architecture" and T-016's own scope is Accommodation Intelligence, not a Flight Intelligence refactor) and would touch code that's already shipped, tested, and stable. Instead, `DISCOVERY_LAYER_PATTERN.md` explicitly calls this out: Flight Intelligence is grandfathered, every module from Accommodation onward must have an explicit Normalizer file.

**Generalise the recommendation-labelling algorithm** from Flight Intelligence's priority-ordered, exhaustive assignment (AVOID → BEST_OVERALL → objective-winner categories → persona categories → best-fit fallback) as the standard every Discovery module must implement, since it's what guarantees every option gets exactly one label with no gaps regardless of how many candidates the Provider returns.

**Codify the domain/AI/API/conversation/frontend/test/docs checklist** that was implicit in how Flight Intelligence was actually built, so a future contributor building, say, Destination Intelligence (T-017) has an explicit list rather than needing to reverse-engineer it from reading `ai/discovery/flights/`.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Retrofit `ai/discovery/flights/` with a separate normalizer file before writing the pattern doc | Out of scope for T-016; touches shipped, tested code for a Sprint-1 mock provider that doesn't yet need the raw/normalized distinction — no functional payoff today |
| Write the pattern as an abstract base class (`DiscoveryProvider(ABC)`, `DiscoveryScorer(ABC)`, ...) | Premature — two modules (Flights, Accommodation) don't yet reveal what's genuinely shared vs. domain-specific; an ABC now would be guessing. Revisit once a third module exists |
| Skip documenting the Provider/Normalizer split and let each module decide independently | Defeats the purpose of a "pattern" — the whole point is that a real provider integration later only ever touches the Normalizer, never the Scorer/Reasoner/Risk Assessor; that guarantee only holds if it's enforced consistently |
| One shared `recommendation_type` enum across all Discovery modules | Each module's recommendation types are domain-specific (Flight has `LOWEST_PRICE`/`SHORTEST_DURATION`; Accommodation has `BEST_LOCATION`/`BEST_COMFORT`) — forcing a shared enum would mean meaningless values for modules that don't use them |

## Consequences

- `docs/DISCOVERY_LAYER_PATTERN.md` is the reference every future Discovery module (T-016 Accommodation, and T-017–T-019 Destination/Visa/Weather) is reviewed against.
- Accommodation Intelligence (T-016) is the first module with a genuine Provider/Normalizer split — `mock_accommodation_provider.py` returns deliberately raw, provider-shaped data; `accommodation_normalizer.py` converts it and computes `comfort_score`/`location_score`/`safety_score` before the Scorer ever runs.
- Flight Intelligence is unchanged. The gap between it and the now-formal pattern is documented, not hidden — a future engineer reading `ai/discovery/flights/` after reading this ADR won't be confused about why there's no `flight_normalizer.py`.
- No abstract base classes were introduced. If a third Discovery module reveals genuinely identical scaffolding (not just a similar shape), extracting a shared base is a future ADR, not a bet made now on two data points.

## Sprint 3+ Evolution

| Item | Next step |
|------|-----------|
| Flight Intelligence Normalizer gap | Optional cleanup once Flight Intelligence gets a real provider (Sprint 4+) — the real provider integration is exactly when the raw/normalized split starts paying for itself |
| Shared Discovery base classes | Revisit once T-017–T-019 exist and genuine duplication (not just similar shape) is visible |
| Recommendation labelling algorithm | Currently duplicated logic per orchestrator (`flight_intelligence.py`, `accommodation_intelligence.py`); extract to a shared `ai/discovery/shared/` helper if a fourth module repeats it identically |
