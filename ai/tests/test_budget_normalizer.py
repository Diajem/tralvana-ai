from ai.discovery.budget.budget_normalizer import BudgetNormalizer


def _raw(**overrides) -> dict:
    base = {
        "destination": "Tokyo", "region": "Asia", "budget_style": "balanced",
        "duration_days": 7, "adults": 1, "children": 0,
        "daily_pp_usd": 130, "cabin_class": "economy", "flight_pp_usd": 900,
        "haul": "long", "_child_cost_factor": 0.75,
    }
    base.update(overrides)
    return base


class TestBudgetNormalizer:
    def test_all_objective_scores_in_range(self):
        normalizer = BudgetNormalizer()
        result = normalizer.normalize(_raw())
        for field in (
            "affordability_score", "comfort_score",
            "cost_certainty_score", "family_suitability_score",
        ):
            assert 0.0 <= result[field] <= 1.0, field

    def test_backpacker_more_affordable_than_luxury(self):
        normalizer = BudgetNormalizer()
        backpacker = normalizer.normalize(_raw(budget_style="backpacker"))
        luxury = normalizer.normalize(_raw(budget_style="luxury"))
        assert backpacker["affordability_score"] > luxury["affordability_score"]

    def test_luxury_more_comfortable_than_backpacker(self):
        normalizer = BudgetNormalizer()
        backpacker = normalizer.normalize(_raw(budget_style="backpacker"))
        luxury = normalizer.normalize(_raw(budget_style="luxury"))
        assert luxury["comfort_score"] > backpacker["comfort_score"]

    def test_cost_breakdown_sums_to_total(self):
        normalizer = BudgetNormalizer()
        result = normalizer.normalize(_raw())
        parts = (
            result["flight_cost_usd"] + result["accommodation_usd"]
            + result["food_usd"] + result["activities_usd"] + result["misc_usd"]
        )
        assert parts == result["total_cost_usd"]

    def test_more_adults_increases_total_cost(self):
        normalizer = BudgetNormalizer()
        one = normalizer.normalize(_raw(adults=1))
        three = normalizer.normalize(_raw(adults=3))
        assert three["total_cost_usd"] > one["total_cost_usd"]

    def test_children_cost_less_than_adults(self):
        normalizer = BudgetNormalizer()
        with_adult = normalizer.normalize(_raw(adults=2, children=0))
        with_child = normalizer.normalize(_raw(adults=1, children=1))
        assert with_adult["total_cost_usd"] > with_child["total_cost_usd"]

    def test_cost_per_day_is_total_over_duration(self):
        normalizer = BudgetNormalizer()
        result = normalizer.normalize(_raw(duration_days=10))
        assert result["cost_per_day_usd"] == round(result["total_cost_usd"] / 10)

    def test_currency_is_usd(self):
        normalizer = BudgetNormalizer()
        result = normalizer.normalize(_raw())
        assert result["currency"] == "USD"

    def test_longer_duration_increases_daily_costs_but_not_flights(self):
        normalizer = BudgetNormalizer()
        short = normalizer.normalize(_raw(duration_days=3))
        long = normalizer.normalize(_raw(duration_days=14))
        assert long["accommodation_usd"] > short["accommodation_usd"]
        assert long["flight_cost_usd"] == short["flight_cost_usd"]
