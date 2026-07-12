"""
TripAssemblyEngine (T-040) — assembles Trip Brain's already-computed
UnifiedRecommendation into one TripItinerary. Every assertion here
checks that a value was *read*, not recomputed — no test constructs a
scoring scenario, only pre-scored AgentResults the engine must not touch.
"""

from __future__ import annotations

from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain.models import UnifiedRecommendation
from ai.trip_brain.trip_assembly import TripAssemblyEngine

engine = TripAssemblyEngine()


def _flight_result(top=None, status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(
        agent_name="flight_intelligence", status=status, confidence=0.82,
        data={"top_option": top or {"airline": "AeroLondon", "estimated_price": 825, "currency": "USD", "match_score": 0.82}},
    )


def _accommodation_result(top=None, status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(
        agent_name="accommodation_intelligence", status=status, confidence=0.75,
        data={"top_option": top or {"property_name": "Tokyo Guesthouse", "accommodation_type": "GUESTHOUSE", "match_score": 0.75}},
    )


def _destination_result(status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(
        agent_name="destination_intelligence", status=status, confidence=0.73,
        data={"top_option": {"name": "Shibuya", "match_score": 0.73}},
    )


def _budget_result(style="balanced", status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(
        agent_name="budget_intelligence", status=status, confidence=0.70,
        data={"top_option": {"budget_style": style, "match_score": 0.70}},
    )


def _visa_result(required=False, status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(
        agent_name="visa_intelligence", status=status, confidence=0.9,
        data={"visa_status": "NOT_REQUIRED" if not required else "VISA_REQUIRED", "visa_required": required, "visa_type": "Tourist Visa"},
    )


def _weather_result(status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(
        agent_name="weather_intelligence", status=status, confidence=0.6,
        data={"season": "Summer", "recommendation": "A great time to visit."},
    )


def _unified(results, explanation=None, confidence=0.7) -> UnifiedRecommendation:
    succeeded = [r.agent_name.replace("_intelligence", "") for r in results if r.status != AgentStatus.FAILED]
    failed = [r.agent_name.replace("_intelligence", "") for r in results if r.status == AgentStatus.FAILED]
    return UnifiedRecommendation(
        results=results,
        modules_selected=succeeded + failed,
        modules_succeeded=succeeded,
        modules_failed=failed,
        overall_confidence=confidence,
        destination="Tokyo",
        explanation=explanation or {},
    )


class TestTopOptionExtraction:
    def test_flight_recommendation_is_the_modules_own_top_option(self):
        unified = _unified([_flight_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.flight_recommendation == {"airline": "AeroLondon", "estimated_price": 825, "currency": "USD", "match_score": 0.82}

    def test_accommodation_recommendation_is_the_modules_own_top_option(self):
        unified = _unified([_accommodation_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.accommodation_recommendation["property_name"] == "Tokyo Guesthouse"

    def test_failed_module_yields_none_not_a_crash(self):
        unified = _unified([_flight_result(status=AgentStatus.FAILED)])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.flight_recommendation is None

    def test_missing_module_yields_none(self):
        unified = _unified([])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.flight_recommendation is None
        assert itinerary.accommodation_recommendation is None
        assert itinerary.destination_recommendation is None
        assert itinerary.budget_summary is None


class TestSingleAssessmentExtraction:
    def test_visa_summary_is_the_whole_assessment_dict(self):
        unified = _unified([_visa_result(required=True)])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.visa_summary["visa_required"] is True
        assert itinerary.visa_summary["visa_type"] == "Tourist Visa"

    def test_weather_expectations_is_the_whole_assessment_dict(self):
        unified = _unified([_weather_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.weather_expectations["season"] == "Summer"

    def test_failed_visa_module_yields_none(self):
        unified = _unified([_visa_result(status=AgentStatus.FAILED)])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.visa_summary is None


class TestExplainabilityPassthrough:
    """Risks/assumptions/why/confidence_explanation/alternatives must
    come from Trip Brain's own `explanation` dict (produced by the
    Explainability Engine) — never recomputed here."""

    def test_risks_read_directly_from_explanation(self):
        explanation = {"risks": ["Non-refundable fare.", "Tight connection."]}
        unified = _unified([_flight_result()], explanation=explanation)
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.risks == ["Non-refundable fare.", "Tight connection."]

    def test_assumptions_read_directly_from_explanation(self):
        explanation = {"assumptions": ["No traveller profile linked."]}
        unified = _unified([_flight_result()], explanation=explanation)
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.assumptions == ["No traveller profile linked."]

    def test_why_this_itinerary_reads_recommendation_drivers(self):
        explanation = {"recommendation_drivers": [{"module": "flight_intelligence", "driver": "Direct flight, no layover risk."}]}
        unified = _unified([_flight_result()], explanation=explanation)
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.why_this_itinerary == [{"module": "flight_intelligence", "driver": "Direct flight, no layover risk."}]

    def test_confidence_explanation_read_directly(self):
        explanation = {"confidence_explanation": "High confidence — every module succeeded."}
        unified = _unified([_flight_result()], explanation=explanation)
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.confidence_explanation == "High confidence — every module succeeded."

    def test_alternative_options_read_directly(self):
        explanation = {"alternatives_considered": [{"module": "flight_intelligence", "alternative": "Continental Express"}]}
        unified = _unified([_flight_result()], explanation=explanation)
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.alternative_options == [{"module": "flight_intelligence", "alternative": "Continental Express"}]

    def test_confidence_is_unified_overall_confidence_not_recomputed(self):
        unified = _unified([_flight_result()], confidence=0.91)
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.confidence == 0.91


class TestDailyOutline:
    def test_daily_outline_has_one_entry_per_day(self):
        unified = _unified([_flight_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5, goal_type="GENERAL_TRAVEL")
        assert len(itinerary.daily_outline) == 5
        assert [d["day"] for d in itinerary.daily_outline] == [1, 2, 3, 4, 5]

    def test_daily_outline_reflects_goal_type_theme(self):
        unified = _unified([_flight_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=4, goal_type="FOOD_TOUR")
        # Day 2 (first non-arrival day) should carry a FOOD_TOUR theme, not GENERAL_TRAVEL's.
        assert "Market" in itinerary.daily_outline[1]["theme"] or "Culinary" in itinerary.daily_outline[1]["theme"] or "Wine" in itinerary.daily_outline[1]["theme"] or "Neighbourhood" in itinerary.daily_outline[1]["theme"]

    def test_zero_or_negative_duration_still_produces_at_least_one_day(self):
        unified = _unified([_flight_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=0)
        assert len(itinerary.daily_outline) >= 1


class TestExecutiveSummary:
    def test_no_succeeded_modules_produces_a_clear_not_ready_message(self):
        unified = _unified([_flight_result(status=AgentStatus.FAILED)])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert "more detail" in itinerary.executive_summary.lower()

    def test_summary_quotes_real_flight_and_accommodation_facts(self):
        unified = _unified([_flight_result(), _accommodation_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert "AeroLondon" in itinerary.executive_summary
        assert "Tokyo Guesthouse" in itinerary.executive_summary
        assert "Tokyo" in itinerary.executive_summary

    def test_summary_never_fabricates_a_module_that_did_not_run(self):
        unified = _unified([_flight_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert "visa" not in itinerary.executive_summary.lower()
        assert "stay at" not in itinerary.executive_summary.lower()

    def test_summary_reflects_visa_required_vs_not_required(self):
        unified_required = _unified([_visa_result(required=True)])
        itinerary_required = engine.assemble(unified_required, destination="Tokyo", duration_days=5)
        assert "required" in itinerary_required.executive_summary.lower()

        unified_not_required = _unified([_visa_result(required=False)])
        itinerary_not_required = engine.assemble(unified_not_required, destination="Tokyo", duration_days=5)
        assert "no visa is required" in itinerary_not_required.executive_summary.lower()

    def test_summary_includes_confidence_percentage(self):
        unified = _unified([_flight_result()], confidence=0.82)
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert "82%" in itinerary.executive_summary


class TestModulesUsedAndUnavailable:
    def test_modules_used_and_unavailable_pass_through(self):
        unified = _unified([_flight_result(), _accommodation_result(status=AgentStatus.FAILED)])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert "flight" in itinerary.modules_used
        assert "accommodation" in itinerary.modules_unavailable


class TestToDict:
    def test_to_dict_contains_every_required_section(self):
        unified = _unified([_flight_result(), _accommodation_result(), _destination_result(), _budget_result(), _visa_result(), _weather_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        d = itinerary.to_dict()
        required_keys = {
            "executive_summary", "destination_recommendation", "flight_recommendation",
            "accommodation_recommendation", "budget_summary", "visa_summary",
            "weather_expectations", "risks", "assumptions", "daily_outline",
            "why_this_itinerary", "confidence", "confidence_explanation",
            "alternative_options",
        }
        assert required_keys.issubset(d.keys())
