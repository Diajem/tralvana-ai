from ai.discovery.weather.weather_scorer import WeatherScorer


def _option(**overrides) -> dict:
    base = {
        "destination": "Japan", "month_of_travel": 4, "month_name": "April",
        "matched": True, "season": "SPRING", "average_temperature": 21,
        "rainfall_level": "LOW", "humidity_level": "LOW", "daylight_hours": 12.5,
        "hazards": [],
        "_temp_comfort": 1.0, "_rainfall_comfort": 1.0, "_humidity_comfort": 1.0,
        "_hazard_penalty": 0.0,
        "outdoor_activity_score": 0.9, "photography_score": 0.9, "family_score": 0.9,
    }
    base.update(overrides)
    return base


class TestWeatherScorer:
    def test_weather_suitability_score_in_range(self):
        scorer = WeatherScorer()
        result = scorer.score(_option())
        assert 0.0 <= result["weather_suitability_score"] <= 1.0

    def test_deterministic_same_inputs_same_score(self):
        scorer = WeatherScorer()
        o = _option()
        r1 = scorer.score(o)
        r2 = scorer.score(o)
        assert r1["weather_suitability_score"] == r2["weather_suitability_score"]

    def test_comfortable_conditions_score_higher_than_hazardous(self):
        scorer = WeatherScorer()
        comfortable = scorer.score(_option())
        hazardous = scorer.score(_option(
            _temp_comfort=0.2, _rainfall_comfort=0.15, _humidity_comfort=0.2,
            _hazard_penalty=0.6, hazards=["hurricane", "flood"],
        ))
        assert comfortable["weather_suitability_score"] > hazardous["weather_suitability_score"]

    def test_matched_destination_has_higher_confidence(self):
        scorer = WeatherScorer()
        matched = scorer.score(_option(matched=True))
        unmatched = scorer.score(_option(matched=False))
        assert matched["confidence"] > unmatched["confidence"]

    def test_dna_photography_tendency_boosts_favourable_month(self):
        scorer = WeatherScorer()
        dna = {"traits": {"photography_tendency": 0.8}}
        o = _option(photography_score=0.8)
        with_dna = scorer.score(o, dna=dna)
        without_dna = scorer.score(o, dna=None)
        assert with_dna["weather_suitability_score"] >= without_dna["weather_suitability_score"]
        assert len(with_dna["dna_notes"]) > 0

    def test_goal_type_family_trip_boosts_family_friendly_month(self):
        scorer = WeatherScorer()
        o = _option(family_score=0.8)
        with_goal = scorer.score(o, goal_type="FAMILY_TRIP")
        without_goal = scorer.score(o, goal_type=None)
        assert with_goal["weather_suitability_score"] >= without_goal["weather_suitability_score"]

    def test_adventure_seeking_reduces_hazard_deterrent(self):
        scorer = WeatherScorer()
        dna = {"traits": {"adventure_seeking": 0.8}}
        o = _option(hazards=["typhoon"], _hazard_penalty=0.2)
        with_dna = scorer.score(o, dna=dna)
        without_dna = scorer.score(o, dna=None)
        assert with_dna["weather_suitability_score"] >= without_dna["weather_suitability_score"]

    def test_personal_suitability_is_a_non_empty_sentence(self):
        scorer = WeatherScorer()
        result = scorer.score(_option())
        assert isinstance(result["personal_suitability"], str)
        assert result["personal_suitability"]

    def test_breakdown_has_five_dimensions(self):
        scorer = WeatherScorer()
        result = scorer.score(_option())
        assert set(result["breakdown"].keys()) == {
            "temp_fit", "rainfall_fit", "humidity_fit", "hazard_fit", "daylight_fit",
        }
