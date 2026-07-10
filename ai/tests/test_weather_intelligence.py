from ai.discovery.weather.weather_intelligence import WeatherIntelligence

_ALL_STATUSES = {"EXCELLENT", "GOOD", "ACCEPTABLE", "CHALLENGING", "NOT_RECOMMENDED"}


class TestWeatherIntelligence:
    def test_returns_full_assessment_shape(self):
        engine = WeatherIntelligence()
        result = engine.analyse("Japan", 7)
        for field in (
            "destination", "month_of_travel", "season", "average_temperature",
            "rainfall_level", "humidity_level", "daylight_hours", "weather_summary",
            "weather_suitability_score", "outdoor_activity_score", "photography_score",
            "family_score", "transport_disruption_risk", "natural_hazard_risk", "health_risk",
            "personal_suitability", "packing_recommendations", "safety_summary", "risks",
            "assumptions", "confidence", "weather_status", "recommendation", "explanation",
            "alternative_months",
        ):
            assert field in result, field

    def test_weather_status_is_valid(self):
        engine = WeatherIntelligence()
        result = engine.analyse("Japan", 7)
        assert result["weather_status"] in _ALL_STATUSES

    def test_score_and_confidence_in_valid_range(self):
        engine = WeatherIntelligence()
        result = engine.analyse("Nigeria", 6)
        assert 0.0 <= result["weather_suitability_score"] <= 1.0
        assert 0.0 <= result["confidence"] <= 1.0

    def test_deterministic_same_inputs_same_result(self):
        engine = WeatherIntelligence()
        r1 = engine.analyse("Japan", 7)
        r2 = engine.analyse("Japan", 7)
        assert r1 == r2

    def test_specific_month_mode_uses_requested_month(self):
        engine = WeatherIntelligence()
        result = engine.analyse("Spain", 8)
        assert result["month_of_travel"] == 8

    def test_omitted_month_finds_the_best_month(self):
        engine = WeatherIntelligence()
        with_month = engine.analyse("Spain", 3)
        best_month_mode = engine.analyse("Spain")
        assert best_month_mode["weather_suitability_score"] >= with_month["weather_suitability_score"]

    def test_omitted_month_adds_assumption(self):
        engine = WeatherIntelligence()
        result = engine.analyse("Spain")
        assert any("best month to visit" in a.lower() for a in result["assumptions"])

    def test_unknown_destination_still_returns_assessment(self):
        engine = WeatherIntelligence()
        result = engine.analyse("Atlantis", 5)
        assert result["confidence"] < 0.5
        assert any("not in the mock climate catalogue" in a for a in result["assumptions"])

    def test_no_profile_adds_assumption(self):
        engine = WeatherIntelligence()
        result = engine.analyse("Japan", 7, profile=None)
        assert any("profile" in a.lower() for a in result["assumptions"])

    def test_mock_data_disclaimer_always_present(self):
        engine = WeatherIntelligence()
        result = engine.analyse("Japan", 7)
        assert any("not a forecast" in a.lower() for a in result["assumptions"])

    def test_recommendation_present_for_every_status(self):
        engine = WeatherIntelligence()
        for destination, month in [("Japan", 3), ("Japan", 8), ("Jamaica", 9), ("UAE", 7)]:
            result = engine.analyse(destination, month)
            assert result["recommendation"]

    def test_hurricane_season_produces_risk_and_reflected_status(self):
        engine = WeatherIntelligence()
        result = engine.analyse("Jamaica", 9)
        assert any("hurricane" in r.lower() for r in result["risks"])
        assert result["weather_status"] in ("ACCEPTABLE", "CHALLENGING", "NOT_RECOMMENDED")

    def test_alternative_months_only_include_better_scoring_months(self):
        engine = WeatherIntelligence()
        result = engine.analyse("Japan", 7)
        primary_score = result["weather_suitability_score"]
        for alt in result["alternative_months"]:
            assert alt["weather_suitability_score"] >= primary_score

    def test_best_month_mode_has_no_better_alternatives(self):
        engine = WeatherIntelligence()
        result = engine.analyse("Spain")
        assert result["alternative_months"] == []

    def test_packing_recommendations_non_empty(self):
        engine = WeatherIntelligence()
        result = engine.analyse("UAE", 7)
        assert len(result["packing_recommendations"]) > 0
