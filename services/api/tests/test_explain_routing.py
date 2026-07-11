"""
POST /explain and EXPLAIN_RECOMMENDATION follow-up routing —
docs/API_EXPLAINABILITY.md, docs/EXPLAINABILITY_ENGINE.md's Conversation
Integration section.
"""


class TestExplainRecommendationIntentRouting:
    def test_why_did_you_recommend_classifies_as_explain_recommendation(self, client):
        client.post("/conversation/message", json={
            "message": "I want to plan a trip to Tokyo in October",
        })
        res = client.post("/conversation/message", json={"message": "why did you recommend this?"})
        assert res.json()["intent"] == "EXPLAIN_RECOMMENDATION"

    def test_why_not_cheaper_classifies_as_explain_recommendation(self, client):
        res = client.post("/conversation/message", json={"message": "why not the cheaper option?"})
        assert res.json()["intent"] == "EXPLAIN_RECOMMENDATION"

    def test_how_confident_are_you_classifies_as_explain_recommendation(self, client):
        res = client.post("/conversation/message", json={"message": "how confident are you?"})
        assert res.json()["intent"] == "EXPLAIN_RECOMMENDATION"

    def test_what_assumptions_classifies_as_explain_recommendation(self, client):
        res = client.post("/conversation/message", json={"message": "what assumptions did you make?"})
        assert res.json()["intent"] == "EXPLAIN_RECOMMENDATION"

    def test_what_would_change_classifies_as_explain_recommendation(self, client):
        res = client.post("/conversation/message", json={"message": "what would change your answer?"})
        assert res.json()["intent"] == "EXPLAIN_RECOMMENDATION"

    def test_does_not_misclassify_a_narrow_flight_search(self, client):
        res = client.post("/conversation/message", json={"message": "recommend flights to Tokyo"})
        assert res.json()["intent"] == "FLIGHT_SEARCH"

    def test_does_not_misclassify_travel_advice(self, client):
        res = client.post("/conversation/message", json={"message": "travel tips for Spain"})
        assert res.json()["intent"] == "TRAVEL_ADVICE"


class TestExplainRecommendationFollowUp:
    def test_follow_up_explains_the_prior_plan_trip_result(self, client):
        r1 = client.post("/conversation/message", json={
            "message": "I want to plan a trip to Tokyo in October",
        })
        cid = r1.json()["conversation_id"]

        r2 = client.post("/conversation/message", json={
            "conversation_id": cid,
            "message": "why did you recommend that?",
        })
        body = r2.json()
        assert body["intent"] == "EXPLAIN_RECOMMENDATION"
        assert "This recommendation" in body["response"]
        # The full module section dump is not repeated on a follow-up —
        # only the explanation-derived answer.
        assert "**Flights:**" not in body["response"]

    def test_follow_up_with_no_prior_recommendation_gives_a_clear_fallback(self, client):
        res = client.post("/conversation/message", json={"message": "why did you recommend that?"})
        body = res.json()
        assert body["intent"] == "EXPLAIN_RECOMMENDATION"
        assert "don't have a recent recommendation" in body["response"]

    def test_narrow_intent_result_does_not_populate_last_recommendation(self, client):
        r1 = client.post("/conversation/message", json={"message": "recommend flights to Tokyo"})
        cid = r1.json()["conversation_id"]
        r2 = client.post("/conversation/message", json={
            "conversation_id": cid,
            "message": "why did you recommend that?",
        })
        # FLIGHT_SEARCH never populates session.last_recommendation (only
        # PLAN_TRIP/Trip Brain does) — the fallback fires even though a
        # narrow result was just shown.
        assert "don't have a recent recommendation" in r2.json()["response"]


class TestExplainEndpointViaConversationId:
    def test_explain_by_conversation_id_returns_full_structured_object(self, client):
        r1 = client.post("/conversation/message", json={
            "message": "I want to plan a trip to Tokyo in October",
        })
        cid = r1.json()["conversation_id"]

        res = client.post("/explain", json={"conversation_id": cid})
        assert res.status_code == 200
        body = res.json()
        for key in (
            "summary", "recommendation_drivers", "tradeoffs", "assumptions", "risks",
            "missing_information", "confidence", "confidence_explanation",
            "alternatives_considered", "what_would_change_the_result", "source_modules",
        ):
            assert key in body

    def test_explain_by_conversation_id_with_question_tailors_summary(self, client):
        r1 = client.post("/conversation/message", json={
            "message": "I want to plan a trip to Tokyo in October",
        })
        cid = r1.json()["conversation_id"]

        res = client.post("/explain", json={"conversation_id": cid, "question": "how confident are you?"})
        assert "confidence" in res.json()["summary"].lower()

    def test_unknown_conversation_id_returns_404(self, client):
        res = client.post("/explain", json={"conversation_id": "does-not-exist"})
        assert res.status_code == 404


class TestExplainEndpointViaTripId:
    def test_explain_by_trip_id_returns_the_same_recommendation(self, client):
        r1 = client.post("/conversation/message", json={
            "message": "I want to plan a trip to Tokyo in October",
        })
        trip_id = r1.json()["trip_id"]
        assert trip_id is not None

        res = client.post("/explain", json={"trip_id": trip_id})
        assert res.status_code == 200

    def test_unknown_trip_id_returns_404(self, client):
        res = client.post("/explain", json={"trip_id": "does-not-exist"})
        assert res.status_code == 404


class TestExplainEndpointViaModuleResults:
    def test_explicit_module_results_bypass_session_lookup_entirely(self, client):
        res = client.post("/explain", json={
            "module_results": [{
                "agent_name": "flight_intelligence",
                "status": "success",
                "confidence": 0.75,
                "data": {"top_option": {"reasoning": "Great overall fit.", "match_score": 0.75}},
                "assumptions": ["No traveller profile linked — scoring uses default preferences only."],
            }],
        })
        assert res.status_code == 200
        body = res.json()
        assert body["confidence"] == 0.75
        assert body["source_modules"] == [{"module": "flight_intelligence", "status": "success"}]
        assert body["recommendation_drivers"] == [
            {"module": "flight_intelligence", "driver": "Great overall fit."}
        ]

    def test_module_results_takes_priority_over_conversation_id(self, client):
        r1 = client.post("/conversation/message", json={
            "message": "I want to plan a trip to Paris in June",
        })
        cid = r1.json()["conversation_id"]

        res = client.post("/explain", json={
            "conversation_id": cid,
            "module_results": [{"agent_name": "weather_intelligence", "status": "success", "confidence": 0.9}],
        })
        assert res.json()["source_modules"] == [{"module": "weather_intelligence", "status": "success"}]

    def test_invalid_status_value_returns_400(self, client):
        res = client.post("/explain", json={
            "module_results": [{"agent_name": "x", "status": "not_a_real_status", "confidence": 0.5}],
        })
        assert res.status_code == 400

    def test_no_input_at_all_returns_404(self, client):
        res = client.post("/explain", json={})
        assert res.status_code == 404


class TestDeterminism:
    def test_explaining_the_same_module_results_twice_gives_identical_output(self, client):
        payload = {
            "module_results": [{
                "agent_name": "flight_intelligence",
                "status": "success",
                "confidence": 0.6,
                "data": {"top_option": {"reasoning": "Solid choice.", "match_score": 0.6}},
            }],
        }
        first = client.post("/explain", json=payload).json()
        second = client.post("/explain", json=payload).json()
        assert first == second
