from ai.discovery.weather.weather_reasoner import WeatherReasoner


def _option(**overrides) -> dict:
    base = {
        "destination": "Japan", "month_of_travel": 4, "month_name": "April",
        "matched": True, "season": "SPRING", "average_temperature": 15,
        "rainfall_level": "MODERATE", "humidity_level": "MODERATE", "daylight_hours": 12.5,
        "hazards": [], "photography_score": 0.6, "family_score": 0.6,
    }
    base.update(overrides)
    return base


def _score_result(**overrides) -> dict:
    base = {
        "weather_suitability_score": 0.8,
        "breakdown": {"temp_fit": 0.8, "rainfall_fit": 0.7, "humidity_fit": 0.7,
                      "hazard_fit": 1.0, "daylight_fit": 0.8},
        "personal_suitability": "This is a good match for your travel style.",
        "dna_notes": [],
    }
    base.update(overrides)
    return base


class TestWeatherReasoner:
    def test_explains_destination_month_and_score(self):
        reasoner = WeatherReasoner()
        explanation = reasoner.explain(_option(), _score_result(), [])
        assert "Japan" in explanation
        assert "April" in explanation
        assert "0.8" in explanation

    def test_flags_heavy_rainfall_trade_off(self):
        reasoner = WeatherReasoner()
        explanation = reasoner.explain(
            _option(rainfall_level="VERY_HIGH"),
            _score_result(breakdown={"temp_fit": 0.8, "rainfall_fit": 0.15, "humidity_fit": 0.7,
                                      "hazard_fit": 1.0, "daylight_fit": 0.8}),
            [],
        )
        assert "trade-off" in explanation.lower()

    def test_mentions_hazards_when_present(self):
        reasoner = WeatherReasoner()
        explanation = reasoner.explain(
            _option(hazards=["typhoon"]),
            _score_result(breakdown={"temp_fit": 0.8, "rainfall_fit": 0.7, "humidity_fit": 0.7,
                                      "hazard_fit": 0.5, "daylight_fit": 0.8}),
            [],
        )
        assert "typhoon" in explanation.lower()

    def test_flags_strong_outdoor_suitability(self):
        reasoner = WeatherReasoner()
        explanation = reasoner.explain(
            _option(),
            _score_result(breakdown={"temp_fit": 0.9, "rainfall_fit": 0.7, "humidity_fit": 0.7,
                                      "hazard_fit": 1.0, "daylight_fit": 0.8}),
            [],
        )
        assert "outdoor suitability is strong" in explanation.lower()

    def test_flags_good_photography_conditions(self):
        reasoner = WeatherReasoner()
        explanation = reasoner.explain(_option(photography_score=0.8), _score_result(), [])
        assert "photography" in explanation.lower()

    def test_flags_family_suitability(self):
        reasoner = WeatherReasoner()
        explanation = reasoner.explain(_option(family_score=0.8), _score_result(), [])
        assert "children" in explanation.lower()

    def test_mentions_alternative_month_when_provided(self):
        reasoner = WeatherReasoner()
        alternatives = [{"month_name": "March", "weather_suitability_score": 0.92}]
        explanation = reasoner.explain(_option(), _score_result(), alternatives)
        assert "March" in explanation
        assert "0.92" in explanation

    def test_no_alternative_mention_when_none_provided(self):
        reasoner = WeatherReasoner()
        explanation = reasoner.explain(_option(), _score_result(), [])
        assert "flexible" not in explanation.lower()

    def test_mentions_unmatched_destination(self):
        reasoner = WeatherReasoner()
        explanation = reasoner.explain(_option(matched=False), _score_result(), [])
        assert "general estimate" in explanation.lower()

    def test_packing_advice_flags_rain(self):
        reasoner = WeatherReasoner()
        advice = reasoner.packing_advice(_option(rainfall_level="HIGH"))
        assert any("waterproof" in a.lower() for a in advice)

    def test_packing_advice_flags_heat(self):
        reasoner = WeatherReasoner()
        advice = reasoner.packing_advice(_option(average_temperature=35))
        assert any("lightweight" in a.lower() or "sun protection" in a.lower() for a in advice)

    def test_packing_advice_flags_cold(self):
        reasoner = WeatherReasoner()
        advice = reasoner.packing_advice(_option(average_temperature=2))
        assert any("warm layers" in a.lower() for a in advice)

    def test_packing_advice_flags_hurricane_insurance(self):
        reasoner = WeatherReasoner()
        advice = reasoner.packing_advice(_option(hazards=["hurricane"]))
        assert any("insurance" in a.lower() for a in advice)

    def test_packing_advice_has_fallback_when_nothing_notable(self):
        reasoner = WeatherReasoner()
        advice = reasoner.packing_advice(_option(
            rainfall_level="LOW", humidity_level="LOW", average_temperature=20,
            daylight_hours=12.0, hazards=[],
        ))
        assert len(advice) >= 1
