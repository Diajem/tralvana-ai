from ai.discovery.budget.budget_scorer import BudgetScorer


def _option(**overrides) -> dict:
    base = {
        "destination": "Tokyo", "budget_style": "balanced",
        "total_cost_usd": 2000,
        "affordability_score": 0.6, "comfort_score": 0.6,
        "cost_certainty_score": 0.85, "family_suitability_score": 0.85,
    }
    base.update(overrides)
    return base


class TestBudgetScorer:
    def test_match_score_in_range(self):
        scorer = BudgetScorer()
        result = scorer.score(_option(), preferences={})
        assert 0.0 <= result["match_score"] <= 1.0

    def test_deterministic_same_inputs_same_score(self):
        scorer = BudgetScorer()
        o = _option()
        prefs = {"budget_style": "balanced"}
        r1 = scorer.score(o, prefs)
        r2 = scorer.score(o, prefs)
        assert r1["match_score"] == r2["match_score"]

    def test_under_cap_scores_higher_than_over_cap(self):
        scorer = BudgetScorer()
        under = scorer.score(_option(total_cost_usd=1500), {"budget_max_usd": 2000})
        over = scorer.score(_option(total_cost_usd=5000), {"budget_max_usd": 2000})
        assert under["breakdown"]["cap_fit"] > over["breakdown"]["cap_fit"]
        assert under["match_score"] > over["match_score"]

    def test_no_cap_supplied_uses_neutral_cap_fit(self):
        scorer = BudgetScorer()
        result = scorer.score(_option(), {})
        assert result["breakdown"]["cap_fit"] == 0.6

    def test_far_over_cap_drives_score_toward_avoid_range(self):
        scorer = BudgetScorer()
        result = scorer.score(_option(total_cost_usd=10000), {"budget_max_usd": 1000})
        assert result["breakdown"]["cap_fit"] == 0.0

    def test_matching_style_scores_full_style_fit(self):
        scorer = BudgetScorer()
        result = scorer.score(_option(budget_style="luxury"), {"budget_style": "luxury"})
        assert result["breakdown"]["style_fit"] == 1.0

    def test_distant_style_scores_low_style_fit(self):
        scorer = BudgetScorer()
        result = scorer.score(_option(budget_style="backpacker"), {"budget_style": "luxury"})
        assert result["breakdown"]["style_fit"] <= 0.25

    def test_backpacker_preference_uses_affordability_score_directly(self):
        scorer = BudgetScorer()
        result = scorer.score(_option(affordability_score=0.9), {"budget_style": "backpacker"})
        assert result["breakdown"]["affordability_fit"] == 0.9

    def test_luxury_preference_softens_affordability_penalty(self):
        scorer = BudgetScorer()
        result = scorer.score(_option(affordability_score=0.1), {"budget_style": "luxury"})
        assert result["breakdown"]["affordability_fit"] == 0.55

    def test_children_present_uses_family_suitability_directly(self):
        scorer = BudgetScorer()
        result = scorer.score(_option(family_suitability_score=0.9), {"has_children": True})
        assert result["breakdown"]["family_fit"] == 0.9

    def test_no_children_uses_neutral_family_fit(self):
        scorer = BudgetScorer()
        result = scorer.score(_option(family_suitability_score=0.9), {"has_children": False})
        assert result["breakdown"]["family_fit"] == 0.6

    def test_dna_budget_consciousness_boosts_leaner_tier(self):
        scorer = BudgetScorer()
        dna = {"traits": {"budget_consciousness": 0.8}}
        o = _option(budget_style="backpacker")
        with_dna = scorer.score(o, {}, dna=dna)
        without_dna = scorer.score(o, {}, dna=None)
        assert with_dna["match_score"] >= without_dna["match_score"]
        assert len(with_dna["dna_notes"]) > 0

    def test_goal_type_business_travel_boosts_comfort_tier(self):
        scorer = BudgetScorer()
        o = _option(budget_style="comfort")
        with_goal = scorer.score(o, {}, goal_type="BUSINESS_TRAVEL")
        without_goal = scorer.score(o, {}, goal_type=None)
        assert with_goal["match_score"] >= without_goal["match_score"]

    def test_persona_scores_present_for_both_personas(self):
        scorer = BudgetScorer()
        result = scorer.score(_option(), preferences={})
        assert set(result["persona_scores"].keys()) == {"value", "family"}
