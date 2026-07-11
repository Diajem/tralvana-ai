"""
Explainability Engine — explanation generation, assumption/risk
preservation, source attribution, partial-failure visibility, and
deterministic output (docs/EXPLAINABILITY_ENGINE.md).
"""

from __future__ import annotations

from ai.explainability.explainability_engine import ExplainabilityEngine
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus

_EXPECTED_KEYS = {
    "summary", "recommendation_drivers", "tradeoffs", "assumptions", "risks",
    "missing_information", "confidence", "confidence_explanation",
    "alternatives_considered", "what_would_change_the_result", "source_modules",
}


def _flight_result(status=AgentStatus.SUCCESS, confidence=0.8) -> AgentResult:
    return AgentResult(
        agent_name="flight_intelligence",
        status=status,
        confidence=confidence,
        data={
            "count": 3,
            "destination": "Tokyo",
            "top_option": {
                "reasoning": "Best overall match for your preferences.",
                "match_score": 0.82,
                "estimated_price": 825,
                "currency": "USD",
                "stops": 0,
                "total_duration": "6h 0m",
            },
            "alternative_option": {
                "match_score": 0.6,
                "estimated_price": 415,
                "currency": "USD",
                "stops": 2,
                "total_duration": "10h 18m",
            },
        },
        assumptions=["No traveller profile linked — scoring uses default preferences only."],
        risks=["Fare may change before booking."],
    )


class TestExplanationGeneration:
    def test_explain_returns_every_required_key(self):
        engine = ExplainabilityEngine()
        out = engine.explain([_flight_result()], overall_confidence=0.8)
        assert set(out.keys()) == _EXPECTED_KEYS

    def test_explain_with_no_results_still_returns_full_shape(self):
        engine = ExplainabilityEngine()
        out = engine.explain([])
        assert set(out.keys()) == _EXPECTED_KEYS
        assert out["confidence"] == 0.0
        assert out["source_modules"] == []

    def test_confidence_defaults_to_mean_of_succeeded_when_not_supplied(self):
        engine = ExplainabilityEngine()
        r1 = _flight_result(confidence=0.6)
        r2 = AgentResult(agent_name="weather_intelligence", status=AgentStatus.SUCCESS, confidence=0.4)
        out = engine.explain([r1, r2])
        assert out["confidence"] == 0.5


class TestAssumptionPreservation:
    def test_assumptions_preserved_verbatim(self):
        engine = ExplainabilityEngine()
        text = "No traveller profile linked — scoring uses default preferences only."
        out = engine.explain([_flight_result()])
        assert text in out["assumptions"]

    def test_assumptions_deduplicated_across_modules(self):
        engine = ExplainabilityEngine()
        shared = "Prices and schedules are deterministic mock data — no live inventory was queried."
        r1 = AgentResult(agent_name="a", status=AgentStatus.SUCCESS, confidence=0.5, assumptions=[shared])
        r2 = AgentResult(agent_name="b", status=AgentStatus.SUCCESS, confidence=0.5, assumptions=[shared])
        out = engine.explain([r1, r2])
        assert out["assumptions"].count(shared) == 1

    def test_assumption_wording_is_never_altered(self):
        engine = ExplainabilityEngine()
        exact = "Budget estimates based on your 'balanced' style."
        r = AgentResult(agent_name="budget_intelligence", status=AgentStatus.SUCCESS, confidence=0.7, assumptions=[exact])
        out = engine.explain([r])
        assert out["assumptions"] == [exact]


class TestRiskPreservation:
    def test_risks_preserved_verbatim_for_succeeded_modules(self):
        engine = ExplainabilityEngine()
        out = engine.explain([_flight_result()])
        assert "Fare may change before booking." in out["risks"]

    def test_risks_deduplicated(self):
        engine = ExplainabilityEngine()
        shared = "Live availability has not been checked — fares are indicative only."
        r1 = AgentResult(agent_name="a", status=AgentStatus.SUCCESS, confidence=0.5, risks=[shared])
        r2 = AgentResult(agent_name="b", status=AgentStatus.SUCCESS, confidence=0.5, risks=[shared])
        out = engine.explain([r1, r2])
        assert out["risks"].count(shared) == 1


class TestSourceAttribution:
    def test_source_modules_lists_every_module_with_status(self):
        engine = ExplainabilityEngine()
        r1 = _flight_result()
        r2 = AgentResult(agent_name="weather_intelligence", status=AgentStatus.FAILED, confidence=0.0)
        out = engine.explain([r1, r2])
        assert {"module": "flight_intelligence", "status": "success"} in out["source_modules"]
        assert {"module": "weather_intelligence", "status": "failed"} in out["source_modules"]

    def test_recommendation_drivers_attributed_to_their_module(self):
        engine = ExplainabilityEngine()
        out = engine.explain([_flight_result()])
        assert out["recommendation_drivers"] == [
            {"module": "flight_intelligence", "driver": "Best overall match for your preferences."}
        ]

    def test_failed_module_produces_no_driver(self):
        engine = ExplainabilityEngine()
        r = AgentResult(agent_name="weather_intelligence", status=AgentStatus.FAILED, confidence=0.0)
        out = engine.explain([r])
        assert out["recommendation_drivers"] == []


class TestPartialModuleFailure:
    def test_failed_module_visible_in_risks(self):
        engine = ExplainabilityEngine()
        r1 = _flight_result()
        r2 = AgentResult(agent_name="weather_intelligence", status=AgentStatus.FAILED, confidence=0.0,
                          risks=["weather_intelligence raised an exception: timeout"])
        out = engine.explain([r1, r2], modules_failed=["weather"])
        assert any("weather could not be completed" in r for r in out["risks"])
        # The raw internal exception text is not leaked to the traveller.
        assert "raised an exception" not in " ".join(out["risks"])

    def test_failed_module_suggests_a_what_would_change_entry(self):
        engine = ExplainabilityEngine()
        out = engine.explain([_flight_result()], modules_failed=["weather"])
        assert any("weather" in c for c in out["what_would_change_the_result"])

    def test_modules_failed_derived_from_results_when_not_supplied(self):
        engine = ExplainabilityEngine()
        r = AgentResult(agent_name="weather_intelligence", status=AgentStatus.FAILED, confidence=0.0)
        out = engine.explain([r])
        assert any("weather_intelligence could not be completed" in risk for risk in out["risks"])


class TestConflictingResults:
    def test_conflicts_surface_as_tradeoffs(self):
        engine = ExplainabilityEngine()
        conflict = (
            "Your best-value accommodation pick is above your backpacker-tier budget "
            "guidance — consider the BEST_FOR_BUDGET-labelled accommodation option instead."
        )
        out = engine.explain([_flight_result()], conflicts=[conflict])
        assert conflict in out["tradeoffs"]

    def test_conflicts_reduce_confidence_explanation(self):
        engine = ExplainabilityEngine()
        out = engine.explain([_flight_result()], overall_confidence=0.7, conflicts=["some conflict"])
        assert "disagreed" in out["confidence_explanation"]


class TestDeterministicOutput:
    def test_same_input_produces_identical_output(self):
        engine = ExplainabilityEngine()
        results = [_flight_result()]
        out1 = engine.explain(results, overall_confidence=0.75)
        out2 = engine.explain(results, overall_confidence=0.75)
        assert out1 == out2

    def test_no_randomness_across_repeated_calls(self):
        engine = ExplainabilityEngine()
        outputs = [engine.explain([_flight_result()]) for _ in range(5)]
        assert all(o == outputs[0] for o in outputs)


class TestAnswerQuestion:
    def test_answer_question_focuses_on_tradeoffs(self):
        engine = ExplainabilityEngine()
        out = engine.explain([_flight_result()])
        answer = engine.answer_question(out, "why not the cheaper option?")
        assert "Flights: a cheaper option is available" in answer

    def test_answer_question_focuses_on_confidence(self):
        engine = ExplainabilityEngine()
        out = engine.explain([_flight_result()], overall_confidence=0.5)
        answer = engine.answer_question(out, "how confident are you?")
        assert out["confidence_explanation"] in answer

    def test_answer_question_defaults_to_drivers(self):
        engine = ExplainabilityEngine()
        out = engine.explain([_flight_result()])
        answer = engine.answer_question(out, "tell me more")
        assert "flight_intelligence" in answer
