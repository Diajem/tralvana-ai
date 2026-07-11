from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain.conflicts import detect_conflicts


def _result(agent_name: str, data: dict, status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(agent_name=agent_name, status=status, confidence=0.7, data=data)


class TestDetectConflicts:
    def test_backpacker_budget_vs_four_star_pick_flags_mismatch(self):
        budget = _result("budget_intelligence", {"top_option": {"budget_style": "backpacker"}})
        accommodation = _result("accommodation_intelligence", {"top_option": {"star_rating": 4}})
        conflicts = detect_conflicts({"budget": budget, "accommodation": accommodation})
        assert len(conflicts) == 1
        assert "budget guidance" in conflicts[0]
        assert conflicts[0] in accommodation.assumptions

    def test_matching_tier_and_rating_no_conflict(self):
        budget = _result("budget_intelligence", {"top_option": {"budget_style": "luxury"}})
        accommodation = _result("accommodation_intelligence", {"top_option": {"star_rating": 5}})
        conflicts = detect_conflicts({"budget": budget, "accommodation": accommodation})
        assert conflicts == []
        assert accommodation.assumptions == []

    def test_low_star_rating_with_low_tier_no_conflict(self):
        budget = _result("budget_intelligence", {"top_option": {"budget_style": "backpacker"}})
        accommodation = _result("accommodation_intelligence", {"top_option": {"star_rating": 2}})
        conflicts = detect_conflicts({"budget": budget, "accommodation": accommodation})
        assert conflicts == []

    def test_missing_budget_module_no_conflict(self):
        accommodation = _result("accommodation_intelligence", {"top_option": {"star_rating": 4}})
        conflicts = detect_conflicts({"accommodation": accommodation})
        assert conflicts == []

    def test_failed_module_does_not_produce_conflict(self):
        budget = _result(
            "budget_intelligence", {"top_option": {"budget_style": "backpacker"}}, status=AgentStatus.FAILED
        )
        accommodation = _result("accommodation_intelligence", {"top_option": {"star_rating": 4}})
        conflicts = detect_conflicts({"budget": budget, "accommodation": accommodation})
        assert conflicts == []

    def test_never_mutates_budget_result(self):
        budget = _result("budget_intelligence", {"top_option": {"budget_style": "backpacker"}})
        accommodation = _result("accommodation_intelligence", {"top_option": {"star_rating": 4}})
        detect_conflicts({"budget": budget, "accommodation": accommodation})
        assert budget.assumptions == []
        assert budget.data["top_option"]["budget_style"] == "backpacker"
