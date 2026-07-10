from ai.discovery.weather.mock_weather_provider import MockWeatherProvider

_EXPECTED_DESTINATIONS = {
    "JAPAN", "SPAIN", "FRANCE", "UK", "IRELAND",
    "USA", "NIGERIA", "GHANA", "JAMAICA", "UAE",
}


class TestMockWeatherProvider:
    def test_includes_all_required_destinations(self):
        provider = MockWeatherProvider()
        assert _EXPECTED_DESTINATIONS.issubset(set(provider.known_destinations()))

    def test_known_destination_returns_matched_record(self):
        provider = MockWeatherProvider()
        result = provider.month("Japan", 7)
        assert result["matched"] is True
        assert result["avg_temp_c"] is not None

    def test_unknown_destination_returns_unmatched_record(self):
        provider = MockWeatherProvider()
        result = provider.month("Atlantis", 7)
        assert result["matched"] is False
        assert result["avg_temp_c"] is None

    def test_case_insensitive_lookup(self):
        provider = MockWeatherProvider()
        lower = provider.month("japan", 7)
        upper = provider.month("JAPAN", 7)
        assert lower["avg_temp_c"] == upper["avg_temp_c"]

    def test_every_month_of_year_has_a_record(self):
        provider = MockWeatherProvider()
        for destination in provider.known_destinations():
            for month in range(1, 13):
                result = provider.month(destination, month)
                assert result["matched"], (destination, month)

    def test_year_returns_twelve_months(self):
        provider = MockWeatherProvider()
        result = provider.year("Ireland")
        assert len(result) == 12
        assert [r["month_of_travel"] for r in result] == list(range(1, 13))

    def test_year_returns_empty_for_unknown_destination(self):
        provider = MockWeatherProvider()
        assert provider.year("Atlantis") == []

    def test_deterministic_same_inputs_same_result(self):
        provider = MockWeatherProvider()
        first = provider.month("Spain", 8)
        second = provider.month("Spain", 8)
        assert first == second

    def test_hot_season_hotter_than_mild_season_for_uae(self):
        provider = MockWeatherProvider()
        mild = provider.month("UAE", 1)
        hot = provider.month("UAE", 7)
        assert hot["avg_temp_c"] > mild["avg_temp_c"]

    def test_jamaica_hurricane_season_flagged(self):
        provider = MockWeatherProvider()
        result = provider.month("Jamaica", 9)
        assert "hurricane" in result["hazards"]

    def test_jamaica_dry_season_no_hurricane_hazard(self):
        provider = MockWeatherProvider()
        result = provider.month("Jamaica", 2)
        assert "hurricane" not in result["hazards"]

    def test_japan_summer_flags_typhoon(self):
        provider = MockWeatherProvider()
        result = provider.month("Japan", 8)
        assert "typhoon" in result["hazards"]

    def test_spain_summer_flags_wildfire(self):
        provider = MockWeatherProvider()
        result = provider.month("Spain", 7)
        assert "wildfire" in result["hazards"]

    def test_usa_winter_flags_extreme_cold(self):
        provider = MockWeatherProvider()
        result = provider.month("USA", 1)
        assert "extreme_cold" in result["hazards"]

    def test_uk_and_united_kingdom_resolve_the_same(self):
        provider = MockWeatherProvider()
        short = provider.month("UK", 3)
        long_form = provider.month("United Kingdom", 3)
        assert short["avg_temp_c"] == long_form["avg_temp_c"]

    def test_display_name_used_for_acronym_destinations(self):
        provider = MockWeatherProvider()
        result = provider.month("UK", 3)
        assert result["destination"] == "United Kingdom"
