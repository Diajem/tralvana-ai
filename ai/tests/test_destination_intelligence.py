from ai.discovery.destinations.destination_intelligence import DestinationIntelligence

_ALL_TYPES = {
    "BEST_OVERALL", "BEST_FOR_FOOD", "BEST_FOR_FOOTBALL", "BEST_FOR_CULTURE",
    "BEST_FOR_FAMILY", "BEST_FOR_BUDGET", "BEST_FOR_PHOTOGRAPHY", "BEST_HIDDEN_GEM", "AVOID",
}


class TestDestinationIntelligence:
    def test_city_mode_returns_ranked_options(self):
        engine = DestinationIntelligence()
        result = engine.recommend(city="Tokyo")
        assert len(result["destination_options"]) > 0

    def test_catalogue_mode_returns_one_option_per_city(self):
        engine = DestinationIntelligence()
        result = engine.recommend(city=None)
        assert len(result["destination_options"]) == 10
        assert all(d["destination_type"] == "CITY" for d in result["destination_options"])

    def test_options_sorted_by_match_score_descending(self):
        engine = DestinationIntelligence()
        result = engine.recommend(city="Barcelona")
        scores = [d["match_score"] for d in result["destination_options"]]
        assert scores == sorted(scores, reverse=True)

    def test_city_mode_every_option_has_unique_recommendation_type(self):
        # City mode always has fewer candidates (<=6) than the 9 available
        # categories, so uniqueness is guaranteed — see DISCOVERY_LAYER_PATTERN.md.
        engine = DestinationIntelligence()
        for city in ["Tokyo", "Osaka", "Barcelona", "Paris", "London",
                     "New York", "Lagos", "Accra", "Kingston", "Dubai"]:
            result = engine.recommend(city=city)
            types = [d["recommendation_type"] for d in result["destination_options"]]
            assert len(types) == len(set(types)), city

    def test_every_option_gets_a_valid_recommendation_type(self):
        # Catalogue mode has 10 candidates vs. 9 categories — one expected
        # duplicate is fine (documented pattern), but every option must still
        # get a real label, never none.
        engine = DestinationIntelligence()
        result = engine.recommend(city=None)
        for d in result["destination_options"]:
            assert d["recommendation_type"] in _ALL_TYPES

    def test_match_scores_in_valid_range(self):
        engine = DestinationIntelligence()
        result = engine.recommend(city="Lagos")
        for d in result["destination_options"]:
            assert 0.0 <= d["match_score"] <= 1.0

    def test_deterministic_same_city_same_results(self):
        engine = DestinationIntelligence()
        result1 = engine.recommend(city="Tokyo", interests=["food"])
        result2 = engine.recommend(city="Tokyo", interests=["food"])
        names1 = sorted(d["name"] for d in result1["destination_options"])
        names2 = sorted(d["name"] for d in result2["destination_options"])
        assert names1 == names2

    def test_unknown_city_returns_no_options_and_assumption(self):
        engine = DestinationIntelligence()
        result = engine.recommend(city="Atlantis")
        assert result["destination_options"] == []
        assert any("not in the mock destination catalogue" in a for a in result["assumptions"])

    def test_no_profile_adds_assumption(self):
        engine = DestinationIntelligence()
        result = engine.recommend(city="Paris", profile=None)
        assert any("profile" in a.lower() for a in result["assumptions"])

    def test_every_option_has_reasoning_and_fields(self):
        engine = DestinationIntelligence()
        result = engine.recommend(city="Accra")
        for d in result["destination_options"]:
            assert d["reasoning"]
            assert isinstance(d["risks"], list)
            assert isinstance(d["assumptions"], list)
            assert d["name"]

    def test_interests_matched_reflects_requested_interests(self):
        engine = DestinationIntelligence()
        result = engine.recommend(city="Tokyo", interests=["food"])
        food_district = next(d for d in result["destination_options"] if d["name"] == "Tsukiji Outer Market")
        assert "food" in food_district["interests_matched"]

    def test_recommended_agents_present(self):
        engine = DestinationIntelligence()
        result = engine.recommend(city="London")
        assert "experience_agent" in result["recommended_agents"]

    def test_summary_mentions_city_when_given(self):
        engine = DestinationIntelligence()
        result = engine.recommend(city="Dubai")
        assert "Dubai" in result["summary"]

    def test_football_goal_type_favours_football_relevant_city(self):
        engine = DestinationIntelligence()
        result = engine.recommend(city=None, goal={"goal_type": "FOOTBALL_TRAVEL"})
        top = next(d for d in result["destination_options"] if d["recommendation_type"] == "BEST_OVERALL")
        assert top["football_score"] > 0.3
