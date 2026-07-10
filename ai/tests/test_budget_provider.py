from ai.discovery.budget.mock_budget_provider import STYLES, MockBudgetProvider


class TestMockBudgetProvider:
    def test_returns_one_candidate_per_style(self):
        provider = MockBudgetProvider()
        result = provider.search("Tokyo")
        assert len(result) == len(STYLES)
        assert {r["budget_style"] for r in result} == set(STYLES)

    def test_known_city_resolves_its_region(self):
        provider = MockBudgetProvider()
        result = provider.search("Tokyo")
        assert all(r["region"] == "Asia" for r in result)

    def test_unknown_destination_falls_back_to_default_region(self):
        provider = MockBudgetProvider()
        result = provider.search("Atlantis")
        assert all(r["region"] == "default" for r in result)

    def test_no_destination_falls_back_to_default_region(self):
        provider = MockBudgetProvider()
        result = provider.search(None)
        assert all(r["region"] == "default" for r in result)

    def test_city_lookup_case_insensitive(self):
        provider = MockBudgetProvider()
        lower = provider.search("tokyo")
        upper = provider.search("TOKYO")
        assert lower[0]["region"] == upper[0]["region"] == "Asia"

    def test_deterministic_same_inputs_same_results(self):
        provider = MockBudgetProvider()
        first = provider.search("Paris", duration_days=10, adults=2, children=1)
        second = provider.search("Paris", duration_days=10, adults=2, children=1)
        assert first == second

    def test_higher_tier_has_higher_daily_rate(self):
        provider = MockBudgetProvider()
        result = {r["budget_style"]: r for r in provider.search("London")}
        assert result["backpacker"]["daily_pp_usd"] < result["budget"]["daily_pp_usd"]
        assert result["budget"]["daily_pp_usd"] < result["balanced"]["daily_pp_usd"]
        assert result["balanced"]["daily_pp_usd"] < result["comfort"]["daily_pp_usd"]
        assert result["comfort"]["daily_pp_usd"] < result["luxury"]["daily_pp_usd"]

    def test_cabin_class_escalates_with_tier(self):
        provider = MockBudgetProvider()
        result = {r["budget_style"]: r for r in provider.search("Lagos")}
        assert result["backpacker"]["cabin_class"] == "economy"
        assert result["comfort"]["cabin_class"] == "business"
        assert result["luxury"]["cabin_class"] == "first"

    def test_duration_adults_children_propagate(self):
        provider = MockBudgetProvider()
        result = provider.search("Accra", duration_days=14, adults=3, children=2)
        for r in result:
            assert r["duration_days"] == 14
            assert r["adults"] == 3
            assert r["children"] == 2

    def test_styles_helper_returns_all_five(self):
        provider = MockBudgetProvider()
        assert provider.styles() == STYLES
