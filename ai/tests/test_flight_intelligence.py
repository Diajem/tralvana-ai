from ai.discovery.flights.flight_intelligence import FlightIntelligence


class TestFlightIntelligence:
    def test_returns_ranked_options(self):
        engine = FlightIntelligence()
        result = engine.recommend(
            origin="London", destination="Tokyo",
            departure_date="2026-09-15", return_date="2026-09-25",
        )
        assert len(result["flight_options"]) > 0

    def test_options_sorted_by_match_score_descending(self):
        engine = FlightIntelligence()
        result = engine.recommend(
            origin="London", destination="Paris",
            departure_date="2026-06-01", return_date="2026-06-05",
        )
        scores = [f["match_score"] for f in result["flight_options"]]
        assert scores == sorted(scores, reverse=True)

    def test_every_option_has_unique_recommendation_type(self):
        engine = FlightIntelligence()
        result = engine.recommend(
            origin="Manchester", destination="Dubai",
            departure_date="2026-08-10", return_date="2026-08-20",
        )
        types = [f["recommendation_type"] for f in result["flight_options"]]
        assert len(types) == len(set(types))

    def test_match_scores_in_valid_range(self):
        engine = FlightIntelligence()
        result = engine.recommend(
            origin="London", destination="Lagos",
            departure_date="2026-07-01", return_date=None,
        )
        for f in result["flight_options"]:
            assert 0.0 <= f["match_score"] <= 1.0

    def test_deterministic_same_route_same_prices(self):
        engine = FlightIntelligence()
        result1 = engine.recommend(
            origin="London", destination="Tokyo",
            departure_date="2026-09-15", return_date="2026-09-25",
        )
        result2 = engine.recommend(
            origin="London", destination="Tokyo",
            departure_date="2026-09-15", return_date="2026-09-25",
        )
        prices1 = sorted(f["estimated_price"] for f in result1["flight_options"])
        prices2 = sorted(f["estimated_price"] for f in result2["flight_options"])
        assert prices1 == prices2

    def test_missing_departure_date_is_defaulted_and_noted(self):
        engine = FlightIntelligence()
        result = engine.recommend(origin="London", destination="Rome", departure_date=None, return_date=None)
        assert result["flight_options"][0]["departure_date"]
        assert any("defaulted" in a.lower() for a in result["assumptions"])

    def test_no_profile_adds_assumption(self):
        engine = FlightIntelligence()
        result = engine.recommend(
            origin="London", destination="Rome",
            departure_date="2026-09-15", return_date="2026-09-20", profile=None,
        )
        assert any("profile" in a.lower() for a in result["assumptions"])

    def test_every_option_has_reasoning_and_fields(self):
        engine = FlightIntelligence()
        result = engine.recommend(
            origin="London", destination="Cape Town",
            departure_date="2026-10-01", return_date="2026-10-15",
        )
        for f in result["flight_options"]:
            assert f["reasoning"]
            assert isinstance(f["risks"], list)
            assert isinstance(f["assumptions"], list)
            assert f["airline"]
            assert f["flight_number"]

    def test_recommended_agents_present(self):
        engine = FlightIntelligence()
        result = engine.recommend(
            origin="London", destination="Barcelona",
            departure_date="2026-05-01", return_date="2026-05-08",
        )
        assert "flight_agent" in result["recommended_agents"]

    def test_summary_mentions_destination(self):
        engine = FlightIntelligence()
        result = engine.recommend(
            origin="London", destination="Singapore",
            departure_date="2026-11-01", return_date="2026-11-14",
        )
        assert "Singapore" in result["summary"]

    def test_dna_available_when_profile_given(self):
        engine = FlightIntelligence()
        profile = {
            "id": "traveller-001",
            "preferences": {"cabin_class": "business", "budget_style": "luxury", "travel_interests": ["luxury"]},
        }
        result = engine.recommend(
            origin="London", destination="Dubai",
            departure_date="2026-09-15", return_date="2026-09-20",
            cabin_class="business", budget_style="luxury", profile=profile,
        )
        assert not any("no traveller profile" in a.lower() for a in result["assumptions"])
