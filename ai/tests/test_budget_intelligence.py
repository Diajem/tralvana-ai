from ai.discovery.budget.budget_intelligence import BudgetIntelligence

_ALL_TYPES = {
    "BEST_OVERALL", "LOWEST_COST", "MOST_COMFORTABLE",
    "BEST_VALUE", "BEST_FOR_FAMILY", "AVOID",
}


class TestBudgetIntelligence:
    def test_returns_five_ranked_options(self):
        engine = BudgetIntelligence()
        result = engine.recommend(destination="Tokyo")
        assert len(result["budget_options"]) == 5

    def test_options_sorted_by_match_score_descending(self):
        engine = BudgetIntelligence()
        result = engine.recommend(destination="Barcelona")
        scores = [o["match_score"] for o in result["budget_options"]]
        assert scores == sorted(scores, reverse=True)

    def test_every_option_gets_a_unique_recommendation_type(self):
        engine = BudgetIntelligence()
        for destination in ["Tokyo", "Paris", "Lagos", None]:
            result = engine.recommend(destination=destination)
            types = [o["recommendation_type"] for o in result["budget_options"]]
            assert len(types) == len(set(types)), destination
            assert all(t in _ALL_TYPES for t in types)

    def test_match_scores_in_valid_range(self):
        engine = BudgetIntelligence()
        result = engine.recommend(destination="Dubai")
        for o in result["budget_options"]:
            assert 0.0 <= o["match_score"] <= 1.0

    def test_deterministic_same_inputs_same_results(self):
        engine = BudgetIntelligence()
        result1 = engine.recommend(destination="Tokyo", budget_style="comfort")
        result2 = engine.recommend(destination="Tokyo", budget_style="comfort")
        costs1 = sorted(o["total_cost_usd"] for o in result1["budget_options"])
        costs2 = sorted(o["total_cost_usd"] for o in result2["budget_options"])
        assert costs1 == costs2

    def test_no_destination_still_returns_options(self):
        engine = BudgetIntelligence()
        result = engine.recommend(destination=None)
        assert len(result["budget_options"]) == 5
        assert any("no destination" in a.lower() for a in result["assumptions"])

    def test_no_profile_adds_assumption(self):
        engine = BudgetIntelligence()
        result = engine.recommend(destination="Paris", profile=None)
        assert any("profile" in a.lower() for a in result["assumptions"])

    def test_no_goal_budget_adds_assumption(self):
        engine = BudgetIntelligence()
        result = engine.recommend(destination="Paris", goal=None)
        assert any("goal budget cap" in a.lower() for a in result["assumptions"])

    def test_every_option_has_reasoning_and_fields(self):
        engine = BudgetIntelligence()
        result = engine.recommend(destination="Accra")
        for o in result["budget_options"]:
            assert o["reasoning"]
            assert isinstance(o["risks"], list)
            assert isinstance(o["assumptions"], list)
            assert o["total_cost_usd"] > 0

    def test_recommended_agents_present(self):
        engine = BudgetIntelligence()
        result = engine.recommend(destination="London")
        assert "budget_agent" in result["recommended_agents"]

    def test_summary_mentions_destination_when_given(self):
        engine = BudgetIntelligence()
        result = engine.recommend(destination="Dubai")
        assert "Dubai" in result["summary"]

    def test_tight_budget_cap_favours_leaner_tier(self):
        engine = BudgetIntelligence()
        result = engine.recommend(
            destination="Paris", duration_days=10, adults=2,
            goal={"budget": {"max_usd": 1500, "currency": "USD"}},
        )
        top = next(o for o in result["budget_options"] if o["recommendation_type"] == "BEST_OVERALL")
        assert top["budget_style"] in ("backpacker", "budget")

    def test_wildly_over_cap_tier_is_labelled_avoid(self):
        engine = BudgetIntelligence()
        result = engine.recommend(
            destination="Paris", duration_days=10, adults=2,
            goal={"budget": {"max_usd": 1500, "currency": "USD"}},
        )
        luxury = next(o for o in result["budget_options"] if o["budget_style"] == "luxury")
        assert luxury["recommendation_type"] == "AVOID"

    def test_lowest_cost_label_matches_actual_cheapest_option(self):
        engine = BudgetIntelligence()
        result = engine.recommend(destination="Tokyo")
        lowest = next(o for o in result["budget_options"] if o["recommendation_type"] == "LOWEST_COST")
        cheapest = min(result["budget_options"], key=lambda o: o["total_cost_usd"])
        assert lowest["total_cost_usd"] == cheapest["total_cost_usd"]

    def test_most_comfortable_label_matches_highest_comfort_score(self):
        engine = BudgetIntelligence()
        result = engine.recommend(destination="Tokyo")
        most_comfortable = next(
            o for o in result["budget_options"] if o["recommendation_type"] == "MOST_COMFORTABLE"
        )
        assert most_comfortable["budget_style"] == "luxury"
