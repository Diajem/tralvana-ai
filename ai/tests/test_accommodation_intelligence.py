from ai.discovery.accommodation.accommodation_intelligence import AccommodationIntelligence

_ALL_TYPES = {
    "BEST_OVERALL", "BEST_VALUE", "BEST_LOCATION", "BEST_COMFORT",
    "BEST_FOR_FAMILY", "BEST_FOR_BUSINESS", "BEST_BUDGET", "AVOID",
}


class TestAccommodationIntelligence:
    def test_returns_ranked_options(self):
        engine = AccommodationIntelligence()
        result = engine.recommend(destination="Tokyo", check_in_date="2026-09-15", nights=5)
        assert len(result["accommodation_options"]) > 0

    def test_options_sorted_by_match_score_descending(self):
        engine = AccommodationIntelligence()
        result = engine.recommend(destination="Paris", check_in_date="2026-06-01", nights=4)
        scores = [a["match_score"] for a in result["accommodation_options"]]
        assert scores == sorted(scores, reverse=True)

    def test_every_option_has_unique_recommendation_type(self):
        engine = AccommodationIntelligence()
        result = engine.recommend(destination="Dubai", check_in_date="2026-08-10", nights=3)
        types = [a["recommendation_type"] for a in result["accommodation_options"]]
        assert len(types) == len(set(types))

    def test_recommendation_types_are_valid(self):
        engine = AccommodationIntelligence()
        result = engine.recommend(destination="Lagos", check_in_date="2026-07-01", nights=6)
        for a in result["accommodation_options"]:
            assert a["recommendation_type"] in _ALL_TYPES

    def test_match_scores_in_valid_range(self):
        engine = AccommodationIntelligence()
        result = engine.recommend(destination="Lagos", check_in_date="2026-07-01", nights=6)
        for a in result["accommodation_options"]:
            assert 0.0 <= a["match_score"] <= 1.0

    def test_deterministic_same_destination_same_prices(self):
        engine = AccommodationIntelligence()
        result1 = engine.recommend(destination="Tokyo", check_in_date="2026-09-15", nights=5)
        result2 = engine.recommend(destination="Tokyo", check_in_date="2026-09-15", nights=5)
        prices1 = sorted(a["nightly_price"] for a in result1["accommodation_options"])
        prices2 = sorted(a["nightly_price"] for a in result2["accommodation_options"])
        assert prices1 == prices2

    def test_missing_check_in_date_is_defaulted_and_noted(self):
        engine = AccommodationIntelligence()
        result = engine.recommend(destination="Rome", check_in_date=None, nights=5)
        assert all(a["nightly_price"] > 0 for a in result["accommodation_options"])
        assert any("defaulted" in a.lower() for a in result["assumptions"])

    def test_no_profile_adds_assumption(self):
        engine = AccommodationIntelligence()
        result = engine.recommend(destination="Rome", check_in_date="2026-09-15", nights=5, profile=None)
        assert any("profile" in a.lower() for a in result["assumptions"])

    def test_every_option_has_reasoning_and_fields(self):
        engine = AccommodationIntelligence()
        result = engine.recommend(destination="Cape Town", check_in_date="2026-10-01", nights=10)
        for a in result["accommodation_options"]:
            assert a["reasoning"]
            assert isinstance(a["risks"], list)
            assert isinstance(a["assumptions"], list)
            assert a["property_name"]
            assert a["total_price"] == round(a["nightly_price"] * 10, 2)

    def test_recommended_agents_present(self):
        engine = AccommodationIntelligence()
        result = engine.recommend(destination="Barcelona", check_in_date="2026-05-01", nights=7)
        assert "hotel_agent" in result["recommended_agents"]

    def test_summary_mentions_destination(self):
        engine = AccommodationIntelligence()
        result = engine.recommend(destination="Singapore", check_in_date="2026-11-01", nights=14)
        assert "Singapore" in result["summary"]

    def test_dna_available_when_profile_given(self):
        engine = AccommodationIntelligence()
        profile = {
            "id": "traveller-001",
            "preferences": {"cabin_class": "business", "budget_style": "luxury", "travel_interests": ["luxury"]},
        }
        result = engine.recommend(
            destination="Dubai", check_in_date="2026-09-15", nights=5,
            budget_style="luxury", profile=profile,
        )
        assert not any("no traveller profile" in a.lower() for a in result["assumptions"])

    def test_business_trip_boosts_business_friendly_ranking(self):
        engine = AccommodationIntelligence()
        result = engine.recommend(
            destination="London", check_in_date="2026-09-15", nights=3, business_trip=True,
        )
        best = next(a for a in result["accommodation_options"] if a["recommendation_type"] == "BEST_FOR_BUSINESS")
        assert best["business_friendly"] is True

    def test_family_traveller_boosts_family_friendly_ranking(self):
        engine = AccommodationIntelligence()
        result = engine.recommend(
            destination="Orlando", check_in_date="2026-09-15", nights=7, children=2,
        )
        best = next(a for a in result["accommodation_options"] if a["recommendation_type"] == "BEST_FOR_FAMILY")
        assert best["family_friendly"] is True
