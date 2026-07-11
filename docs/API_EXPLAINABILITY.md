# Explainability API

`POST /explain` — the Explainability Engine's HTTP surface
(`services/api/app/routers/explain.py`). See `docs/EXPLAINABILITY_ENGINE.md`
for the underlying engine.

## `POST /explain`

Returns a structured explanation for a recommendation. Never re-runs a
Discovery module or Trip Brain — it only reads and explains a result that
already exists.

### Request

```json
{
  "conversation_id": "string, optional",
  "trip_id": "string, optional",
  "module_results": "list, optional",
  "question": "string, optional"
}
```

Three ways to supply the recommendation to explain, tried in this order:

1. **`module_results`** — an explicit list of module results, shaped like
   `AgentResult.to_dict()` (`ai/shared/agent_result.py`). Use this to
   explain a result you already have, without a prior conversation. Each
   entry:

   ```json
   {
     "agent_name": "flight_intelligence",
     "status": "success",
     "confidence": 0.75,
     "data": { "top_option": { "...": "..." } },
     "assumptions": ["..."],
     "missing_information": [],
     "risks": ["..."],
     "recommendations": [],
     "next_actions": []
   }
   ```

   `status` must be one of `success`, `needs_information`, `failed`,
   `partial`, `skipped` (`AgentStatus`) — an invalid value returns `400`.

2. **`conversation_id`** — looks up the conversation's cached Trip Brain
   result (`ConversationSession.last_recommendation`, set the last time
   `PLAN_TRIP` ran in that conversation).

3. **`trip_id`** — same lookup, keyed by trip instead of conversation, for
   callers that only have the trip.

If none of the three resolves to a recommendation, the response is `404`.

`question` (optional, any input mode): a natural-language follow-up (e.g.
*"why not the cheaper option?"*) that tailors the `summary` field's
closing sentence toward the relevant part of the explanation — every
other field is returned in full regardless, per the fixed response shape
below.

### Response — `200`

```json
{
  "summary": "This recommendation for Tokyo draws on 6 module(s), at 0.62 confidence. Here's the main trade-off behind that choice.",
  "recommendation_drivers": [
    { "module": "flight_intelligence", "driver": "AeroLondon AL453 (0 stops, 6h 0m) scores 0.82 for a economy traveller." }
  ],
  "tradeoffs": [
    "Flights: a cheaper option is available (USD 415 vs USD 825) — it has 2 stop(s) and takes 10h 18m, versus 0 stop(s) and 6h 0m for the recommended flight."
  ],
  "assumptions": [
    "No traveller profile linked — scoring uses default preferences only."
  ],
  "risks": [
    "Fare may change before booking."
  ],
  "missing_information": [],
  "confidence": 0.62,
  "confidence_explanation": "Moderate confidence (0.62) — missing traveller information; mock or incomplete provider data.",
  "alternatives_considered": [
    { "module": "flight_intelligence", "alternative": "Continental Express", "why_not_chosen": "Scored lower overall (match score 0.68) than the recommended option (match score 0.82)." }
  ],
  "what_would_change_the_result": [
    "Providing the missing detail behind “No traveller profile linked...” would refine this recommendation."
  ],
  "source_modules": [
    { "module": "flight_intelligence", "status": "success" },
    { "module": "weather_intelligence", "status": "failed" }
  ]
}
```

Field meanings are documented in full in
`docs/EXPLAINABILITY_ENGINE.md`'s Explanation Output section.

### Errors

| Status | When |
|---|---|
| `400` | `module_results[].status` is not a valid `AgentStatus` value |
| `404` | No `module_results` supplied, and neither `conversation_id` nor `trip_id` resolves to a session with a cached recommendation |

### Examples

**Explain the most recent trip-planning conversation:**

```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "c1a2b3..."}'
```

**Ask a focused follow-up:**

```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"trip_id": "t9f8e7...", "question": "why not the cheaper option?"}'
```

**Explain a result you already have, with no prior conversation:**

```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{
    "module_results": [{
      "agent_name": "budget_intelligence",
      "status": "success",
      "confidence": 0.7,
      "data": {"top_option": {"reasoning": "Closely matches your balanced style.", "match_score": 0.7}},
      "assumptions": ["Budget estimates based on your balanced style."]
    }]
  }'
```

## Conversational Equivalent

The same explanations are available inside an ongoing conversation via
`POST /conversation/message` — ask a follow-up like *"why did you
recommend this?"* after a `PLAN_TRIP` request and it classifies to
`Intent.EXPLAIN_RECOMMENDATION`, reusing the same
`ConversationSession.last_recommendation` this endpoint's `conversation_id`
path reads. See `docs/EXPLAINABILITY_ENGINE.md`'s Conversation Integration
section.
