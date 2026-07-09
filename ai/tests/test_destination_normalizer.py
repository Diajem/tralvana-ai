from ai.discovery.destinations.destination_normalizer import DestinationNormalizer


def _raw(**overrides) -> dict:
    base = {
        "city": "Testville", "name": "Test Place", "place_type": "food_district",
        "description": "A test place.", "tags": ["food"], "distance_from_centre_km": 2,
        "popularity": 5, "best_for": ["testing"],
        "country": "Testland", "region": "Testregion",
        "safety_rating": 8.0, "budget_tier": "moderate", "transport_rating": 7.0,
        "food_scene_rating": 8.0, "culture_rating": 6.0, "football_reputation": 3.0,
        "peak_months": [6, 7],
    }
    base.update(overrides)
    return base


class TestDestinationNormalizer:
    def test_maps_raw_place_type_to_canonical_enum_value(self):
        normalizer = DestinationNormalizer()
        result = normalizer.normalize(_raw(place_type="football_venue"))
        assert result["destination_type"] == "FOOTBALL_VENUE"

    def test_unknown_place_type_falls_back_to_attraction(self):
        normalizer = DestinationNormalizer()
        result = normalizer.normalize(_raw(place_type="something_unrecognised"))
        assert result["destination_type"] == "ATTRACTION"

    def test_city_entry_has_empty_neighbourhood(self):
        normalizer = DestinationNormalizer()
        result = normalizer.normalize(_raw(place_type="city"))
        assert result["neighbourhood"] == ""

    def test_non_city_entry_uses_name_as_neighbourhood(self):
        normalizer = DestinationNormalizer()
        result = normalizer.normalize(_raw(place_type="neighbourhood", name="Shibuya"))
        assert result["neighbourhood"] == "Shibuya"

    def test_all_objective_scores_in_range(self):
        normalizer = DestinationNormalizer()
        result = normalizer.normalize(_raw())
        for field in (
            "transport_access_score", "food_score", "culture_score", "football_score",
            "nightlife_score", "family_score", "safety_score", "budget_score", "season_score",
        ):
            assert 0.0 <= result[field] <= 1.0, field

    def test_food_district_boosts_food_score(self):
        normalizer = DestinationNormalizer()
        food_district = normalizer.normalize(_raw(place_type="food_district", tags=[]))
        neighbourhood = normalizer.normalize(_raw(place_type="neighbourhood", tags=[]))
        assert food_district["food_score"] > neighbourhood["food_score"]

    def test_football_venue_boosts_football_score(self):
        normalizer = DestinationNormalizer()
        venue = normalizer.normalize(_raw(place_type="football_venue", football_reputation=9.0))
        other = normalizer.normalize(_raw(place_type="museum", football_reputation=9.0))
        assert venue["football_score"] > other["football_score"]

    def test_nightlife_area_boosts_nightlife_score(self):
        normalizer = DestinationNormalizer()
        result = normalizer.normalize(_raw(place_type="nightlife_area", tags=[]))
        assert result["nightlife_score"] == 0.9

    def test_family_tag_boosts_family_score(self):
        normalizer = DestinationNormalizer()
        with_family = normalizer.normalize(_raw(place_type="beach", tags=["family"]))
        without_family = normalizer.normalize(_raw(place_type="nightlife_area", tags=[]))
        assert with_family["family_score"] > without_family["family_score"]

    def test_safety_score_normalized_to_0_1(self):
        normalizer = DestinationNormalizer()
        result = normalizer.normalize(_raw(safety_rating=9.0))
        assert result["safety_score"] == 0.9

    def test_budget_score_reflects_affordability_not_cost(self):
        normalizer = DestinationNormalizer()
        cheap = normalizer.normalize(_raw(budget_tier="budget"))
        luxury = normalizer.normalize(_raw(budget_tier="luxury"))
        assert cheap["budget_score"] > luxury["budget_score"]

    def test_season_score_neutral_when_no_travel_month(self):
        normalizer = DestinationNormalizer()
        result = normalizer.normalize(_raw(), travel_month=None)
        assert result["season_score"] == 0.6

    def test_season_score_high_in_peak_month(self):
        normalizer = DestinationNormalizer()
        result = normalizer.normalize(_raw(peak_months=[6, 7]), travel_month=6)
        assert result["season_score"] == 1.0

    def test_season_score_lower_outside_peak_month(self):
        normalizer = DestinationNormalizer()
        result = normalizer.normalize(_raw(peak_months=[6, 7]), travel_month=12)
        assert result["season_score"] < 1.0
