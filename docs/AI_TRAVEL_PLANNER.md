# AI Travel Planner (Trip Assembly Engine) — T-040

The primary user experience of Tralvana: a traveller describes a trip
in natural language and receives one coherent, consultant-style
itinerary — not six independent module responses stitched together
visibly. See `docs/ADR/ADR-026-trip-assembly-engine.md` for the design
decisions behind it.

**Search and recommendation only.** No booking, payment, or
reservation logic exists anywhere in this feature.

## Architecture

```
Traveller (natural language)
  -> POST /planner/plan (services/api/app/routers/planner.py)
    -> travel_concierge.handle() (ai/concierge/travel_concierge.py, UNCHANGED)
      -> ConversationEngine.process() (UNCHANGED — intent classification,
         goal/trip creation, session management)
        -> Intent.PLAN_TRIP -> TripBrain.plan() (ai/trip_brain/coordinator.py, UNCHANGED)
          -> six Discovery modules, run in parallel, each scoring/ranking
             its own domain (UNCHANGED — zero new scoring anywhere)
          -> Explainability Engine (ai/explainability/, UNCHANGED)
    -> session.last_recommendation (the UnifiedRecommendation Trip Brain produced)
  -> TripAssemblyEngine.assemble() (ai/trip_brain/trip_assembly.py, NEW)
    -> reads UnifiedRecommendation.results/explanation (never recomputes them)
    -> calls itinerary_builder.build() (ai/planning/itinerary_builder.py,
       T-008, Sprint 1 — UNCHANGED, the one genuinely new *capability*
       this task adds is calling it, not building it)
    -> produces one TripItinerary
  -> PlanTripResponse (conversational reply + the assembled itinerary)
```

**Trip Brain remains the sole orchestrator of the six Discovery
modules** — `ai/trip_brain/coordinator.py` is byte-for-byte unchanged,
its own 75+ existing tests untouched. The Trip Assembly Engine is a
second, separate *caller* of Trip Brain's output, the same relationship
`ai/concierge/conversation_engine.py` and `POST /explain`
(`services/api/app/routers/explain.py`) already have with it — not a
seventh Discovery module, not a change to Trip Brain itself.

## What's Genuinely New vs. What's Reused

| Piece | Status |
|---|---|
| Destination, flight, accommodation, budget, visa, weather scoring | **Unchanged** — read from `AgentResult.data`, never recomputed |
| Confidence, conflicts, module selection | **Unchanged** — Trip Brain's own aggregation, read as-is |
| Recommendation drivers, trade-offs, risks, assumptions, alternatives | **Unchanged** — the Explainability Engine's own output, read as-is |
| Daily outline (morning/afternoon/evening per day) | **Reused, not duplicated** — `ai/planning/itinerary_builder.py` (T-008), called for the first time from this new orchestration path |
| Executive summary | **New** — a natural-language paragraph template over facts each module already decided (destination, airline+price, property name, budget tier, visa outcome, weather fit); every clause is conditional on the fact it quotes actually being present |
| `TripItinerary` assembly (`ai/trip_brain/trip_assembly.py`) | **New** — pure composition/formatting, zero scoring |
| `POST /planner/plan` (`services/api/app/routers/planner.py`) | **New** — a thin wrapper around `travel_concierge.handle()`, adding only the assembly step |

## The Itinerary's 13 Sections

Every section maps to a field a Discovery module or the Explainability
Engine already produced — see the table in
`docs/ADR/ADR-026-trip-assembly-engine.md` for the exact source of each
one. Summary:

| Section | Source |
|---|---|
| Executive summary | New template over already-decided facts |
| Destination / Flight / Accommodation / Budget recommendation | Each module's own `top_option` (already labelled `BEST_OVERALL`) |
| Visa summary / Weather expectations | Visa/Weather Intelligence's own single-assessment output, unchanged |
| Risks / Assumptions | `UnifiedRecommendation.explanation["risks"/"assumptions"]` |
| Daily outline | `ai/planning/itinerary_builder.py`, called with the trip's own `goal_type`/`budget_style`/`duration_days` |
| Why this itinerary was selected | `explanation["recommendation_drivers"]` |
| Confidence | `UnifiedRecommendation.overall_confidence` + `explanation["confidence_explanation"]` |
| Alternative options | `explanation["alternatives_considered"]` |

## API

`POST /planner/plan`

```json
{"message": "I want to plan a football trip to London in September for 2 adults, balanced budget, from Nigeria"}
```

Response (`itinerary` is `null` whenever Trip Brain hasn't produced a
full recommendation yet — e.g. the message was too vague; `response`/
`missing_information` carry the follow-up in that case, exactly as
`POST /conversation/message` already does):

```json
{
  "conversation_id": "...",
  "intent": "PLAN_TRIP",
  "response": "Here's what I found for your London trip: ...",
  "confidence": 0.62,
  "itinerary": {
    "executive_summary": "Here's the plan I've put together for London. You'll fly with AeroLondon for USD 580. ...",
    "destination_recommendation": {...},
    "flight_recommendation": {...},
    "accommodation_recommendation": {...},
    "budget_summary": {...},
    "visa_summary": {...},
    "weather_expectations": {...},
    "risks": [...],
    "assumptions": [...],
    "daily_outline": [{"day": 1, "title": "Day 1: Arrival & Orientation", ...}, ...],
    "why_this_itinerary": [{"module": "flight_intelligence", "driver": "..."}],
    "confidence": 0.62,
    "confidence_explanation": "Moderate confidence (0.62) — missing traveller information; mock or incomplete provider data.",
    "alternative_options": [...],
    "modules_used": ["destination", "flight", "accommodation", "budget", "visa", "weather"],
    "modules_unavailable": []
  }
}
```

Multi-turn: pass the returned `conversation_id` back on the next call
to continue the same conversation (e.g. answering a follow-up
question) — reuses `ConversationSession` exactly as
`POST /conversation/message` does.

## Frontend

`apps/web/src/app/planner/page.tsx` — a single natural-language text
box, no forms-within-forms. Renders every section above, including a
day-by-day outline grid. The homepage (`apps/web/src/app/page.tsx`)
now leads with "Plan My Trip" as the primary call to action.

**Verified live in a real browser during this task**: a natural
message ("I want to plan a football trip to London in September for 2
adults, balanced budget, travelling from Nigeria") produced a complete
itinerary — all six Discovery modules ran, the executive summary
correctly quoted the real flight/accommodation/visa/weather facts, and
the daily outline correctly used football-themed days with real London
landmark enrichment (Buckingham Palace, Tower of London, Borough
Market — from `ai/planning/itinerary_builder.py`'s existing KG
enrichment table).

## Testing

- `ai/tests/test_trip_assembly.py` (23 tests) — every test asserts a
  value was *read* from a pre-constructed `AgentResult`/`explanation`
  dict, never that a value was computed; explicit tests for failed/
  missing modules (graceful `None`, no crash) and for the executive
  summary never fabricating a fact from a module that didn't run.
- `services/api/tests/test_planner.py` (6 tests) — full natural-language
  message end-to-end, vague message with no itinerary, no
  internal-field leakage (`_provider_offer_id`, `_persona_scores`,
  `_price_anchor`), multi-turn conversation continuity.

## What Remains Out of Scope

- No booking, payment, reservation, cancellation, or modification —
  explicitly excluded by this task.
- No changes to Trip Brain, the Explainability Engine, or any Discovery
  module's scoring, weights, or labelling.
- The legacy `POST /trips/plan` endpoint (`ai/planning/trip_planner.py`,
  Sprint 1) is untouched and still exists in parallel — it never called
  Trip Brain or the real Discovery modules to begin with (a pre-existing
  fact, not something this task changed); `POST /planner/plan` is the
  new, Trip-Brain-backed path.
