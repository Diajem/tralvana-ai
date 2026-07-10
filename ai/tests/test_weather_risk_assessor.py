from ai.discovery.weather.weather_risk_assessor import WeatherRiskAssessor


def _option(**overrides) -> dict:
    base = {
        "matched": True, "average_temperature": 20, "rainfall_level": "LOW",
        "humidity_level": "LOW", "hazards": [],
    }
    base.update(overrides)
    return base


class TestWeatherRiskAssessor:
    def test_heavy_rain_flagged(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(rainfall_level="HIGH"))
        assert any("rainfall" in r.lower() for r in result["risks"])

    def test_low_rainfall_not_flagged(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(rainfall_level="LOW"))
        assert not any("rainfall expected" in r.lower() for r in result["risks"])

    def test_extreme_heat_flagged_by_hazard_tag(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(hazards=["extreme_heat"]))
        assert any("extreme heat" in r.lower() for r in result["risks"])

    def test_extreme_heat_flagged_by_temperature_threshold(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(average_temperature=35))
        assert any("extreme heat" in r.lower() for r in result["risks"])

    def test_extreme_cold_flagged(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(average_temperature=-5))
        assert any("extreme cold" in r.lower() for r in result["risks"])

    def test_typhoon_season_flagged(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(hazards=["typhoon"]))
        assert any("typhoon" in r.lower() for r in result["risks"])

    def test_hurricane_season_flagged(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(hazards=["hurricane"]))
        assert any("hurricane" in r.lower() for r in result["risks"])

    def test_flood_risk_flagged(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(hazards=["flood"]))
        assert any("flood" in r.lower() for r in result["risks"])

    def test_wildfire_season_flagged(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(hazards=["wildfire"]))
        assert any("wildfire" in r.lower() for r in result["risks"])

    def test_transport_disruption_high_when_flood_present(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(hazards=["flood"]))
        assert result["transport_disruption_risk"] == "HIGH"

    def test_transport_disruption_low_when_clear(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option())
        assert result["transport_disruption_risk"] == "LOW"

    def test_health_risk_high_for_hot_humid_conditions(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(average_temperature=30, humidity_level="VERY_HIGH"))
        assert result["health_risk"] == "HIGH"

    def test_health_risk_low_for_mild_conditions(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option())
        assert result["health_risk"] == "LOW"

    def test_natural_hazard_risk_severe_for_hurricane(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(hazards=["hurricane"]))
        assert result["natural_hazard_risk"] == "SEVERE"

    def test_natural_hazard_risk_low_when_no_hazards(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option())
        assert result["natural_hazard_risk"] == "LOW"

    def test_unmatched_destination_flagged(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option(matched=False))
        assert any("no specific climate data" in r.lower() for r in result["risks"])

    def test_safety_summary_present(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option())
        assert result["safety_summary"]

    def test_clean_conditions_have_no_risks(self):
        assessor = WeatherRiskAssessor()
        result = assessor.assess(_option())
        assert result["risks"] == []
