from ai.discovery.weather.weather_normalizer import WeatherNormalizer


def _raw(**overrides) -> dict:
    base = {
        "destination": "Japan", "month_of_travel": 4, "matched": True,
        "season": "SPRING", "avg_temp_c": 15, "rainfall": "MODERATE",
        "humidity": "MODERATE", "daylight_hours": 12.5, "hazards": [],
    }
    base.update(overrides)
    return base


class TestWeatherNormalizer:
    def test_month_name_mapped_correctly(self):
        normalizer = WeatherNormalizer()
        result = normalizer.normalize(_raw(month_of_travel=7))
        assert result["month_name"] == "July"

    def test_all_objective_scores_in_range(self):
        normalizer = WeatherNormalizer()
        result = normalizer.normalize(_raw())
        for field in ("outdoor_activity_score", "photography_score", "family_score"):
            assert 0.0 <= result[field] <= 1.0, field

    def test_ideal_temperature_scores_higher_outdoor_activity(self):
        normalizer = WeatherNormalizer()
        ideal = normalizer.normalize(_raw(avg_temp_c=21))
        extreme = normalizer.normalize(_raw(avg_temp_c=40))
        assert ideal["outdoor_activity_score"] > extreme["outdoor_activity_score"]

    def test_low_rainfall_scores_higher_photography(self):
        normalizer = WeatherNormalizer()
        dry = normalizer.normalize(_raw(rainfall="LOW"))
        wet = normalizer.normalize(_raw(rainfall="VERY_HIGH"))
        assert dry["photography_score"] > wet["photography_score"]

    def test_hazards_reduce_family_score(self):
        normalizer = WeatherNormalizer()
        clean = normalizer.normalize(_raw(hazards=[]))
        hazardous = normalizer.normalize(_raw(hazards=["hurricane", "flood"]))
        assert clean["family_score"] > hazardous["family_score"]

    def test_unmatched_destination_handles_none_values(self):
        normalizer = WeatherNormalizer()
        result = normalizer.normalize(_raw(matched=False, avg_temp_c=None, daylight_hours=None,
                                            rainfall="UNKNOWN", humidity="UNKNOWN"))
        assert result["matched"] is False
        for field in ("outdoor_activity_score", "photography_score", "family_score"):
            assert 0.0 <= result[field] <= 1.0, field

    def test_more_daylight_hours_boosts_photography_score(self):
        normalizer = WeatherNormalizer()
        short = normalizer.normalize(_raw(daylight_hours=8.0))
        long_day = normalizer.normalize(_raw(daylight_hours=16.0))
        assert long_day["photography_score"] > short["photography_score"]

    def test_deterministic_same_inputs_same_scores(self):
        normalizer = WeatherNormalizer()
        r1 = normalizer.normalize(_raw())
        r2 = normalizer.normalize(_raw())
        assert r1 == r2
