from ai.discovery.budget.budget_risk_assessor import BudgetRiskAssessor


def _option(**overrides) -> dict:
    base = {
        "budget_style": "balanced",
        "total_cost_usd": 2000,
        "duration_days": 7,
        "children": 0,
        "cost_certainty_score": 0.85,
    }
    base.update(overrides)
    return base


class TestBudgetRiskAssessor:
    def test_low_cost_certainty_flagged(self):
        assessor = BudgetRiskAssessor()
        risks = assessor.assess(_option(cost_certainty_score=0.5))
        assert any("variability" in r.lower() for r in risks)

    def test_high_cost_certainty_not_flagged(self):
        assessor = BudgetRiskAssessor()
        risks = assessor.assess(_option(cost_certainty_score=0.9))
        assert not any("variability" in r.lower() for r in risks)

    def test_high_absolute_cost_flagged(self):
        assessor = BudgetRiskAssessor()
        risks = assessor.assess(_option(total_cost_usd=8000))
        assert any("high absolute" in r.lower() for r in risks)

    def test_low_absolute_cost_not_flagged(self):
        assessor = BudgetRiskAssessor()
        risks = assessor.assess(_option(total_cost_usd=1500))
        assert not any("high absolute" in r.lower() for r in risks)

    def test_backpacker_tier_always_flagged(self):
        assessor = BudgetRiskAssessor()
        risks = assessor.assess(_option(budget_style="backpacker"))
        assert any("hostel" in r.lower() for r in risks)

    def test_non_backpacker_tier_not_flagged_for_hostel(self):
        assessor = BudgetRiskAssessor()
        risks = assessor.assess(_option(budget_style="luxury"))
        assert not any("hostel" in r.lower() for r in risks)

    def test_long_duration_flagged(self):
        assessor = BudgetRiskAssessor()
        risks = assessor.assess(_option(duration_days=30))
        assert any("currency" in r.lower() for r in risks)

    def test_short_duration_not_flagged_for_currency(self):
        assessor = BudgetRiskAssessor()
        risks = assessor.assess(_option(duration_days=7))
        assert not any("currency" in r.lower() for r in risks)

    def test_children_with_backpacker_tier_flagged(self):
        assessor = BudgetRiskAssessor()
        risks = assessor.assess(_option(budget_style="backpacker", children=2))
        assert any("young children" in r.lower() for r in risks)

    def test_children_with_comfort_tier_not_flagged_for_suitability(self):
        assessor = BudgetRiskAssessor()
        risks = assessor.assess(_option(budget_style="comfort", children=2))
        assert not any("young children" in r.lower() for r in risks)

    def test_clean_balanced_option_has_minimal_risks(self):
        assessor = BudgetRiskAssessor()
        risks = assessor.assess(_option())
        assert len(risks) == 0
