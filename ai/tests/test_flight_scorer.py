from ai.discovery.flights.flight_scorer import FlightScorer


def _flight(**overrides) -> dict:
    base = {
        "airline": "AeroLondon",
        "flight_number": "AL100",
        "cabin_class": "economy",
        "stops": 0,
        "layover_duration": "",
        "departure_time": "09:00",
        "arrival_time": "15:00",
        "total_duration": "6h 0m",
        "estimated_price": 650,
        "currency": "USD",
        "baggage_included": True,
        "refundability": "refundable",
        "flexibility": "flexible",
        "departure_date": "2026-09-15",
        "return_date": None,
        "_total_duration_minutes": 360,
        "_layover_minutes": 0,
        "_price_anchor": 650,
    }
    base.update(overrides)
    return base


class TestFlightScorer:
    def test_match_score_in_range(self):
        scorer = FlightScorer()
        result = scorer.score(_flight(), preferences={"cabin_class": "economy"})
        assert 0.0 <= result["match_score"] <= 1.0

    def test_deterministic_same_inputs_same_score(self):
        scorer = FlightScorer()
        flight = _flight()
        prefs = {"cabin_class": "economy", "max_price_usd": 900}
        r1 = scorer.score(flight, prefs)
        r2 = scorer.score(flight, prefs)
        assert r1["match_score"] == r2["match_score"]

    def test_cheaper_flight_scores_higher_price_fit(self):
        scorer = FlightScorer()
        prefs = {"cabin_class": "economy", "max_price_usd": 1000}
        cheap = scorer.score(_flight(estimated_price=500), prefs)
        expensive = scorer.score(_flight(estimated_price=1500), prefs)
        assert cheap["breakdown"]["price_fit"] > expensive["breakdown"]["price_fit"]

    def test_matching_cabin_class_scores_higher(self):
        scorer = FlightScorer()
        prefs = {"cabin_class": "business"}
        match = scorer.score(_flight(cabin_class="business"), prefs)
        mismatch = scorer.score(_flight(cabin_class="economy"), prefs)
        assert match["breakdown"]["cabin_match"] > mismatch["breakdown"]["cabin_match"]

    def test_low_layover_tolerance_penalises_stops(self):
        scorer = FlightScorer()
        prefs = {"cabin_class": "economy", "layover_tolerance": "low"}
        direct = scorer.score(_flight(stops=0), prefs)
        one_stop = scorer.score(_flight(stops=1), prefs)
        assert direct["breakdown"]["layover_tolerance"] > one_stop["breakdown"]["layover_tolerance"]

    def test_no_baggage_penalised_when_needed(self):
        scorer = FlightScorer()
        prefs = {"cabin_class": "economy", "needs_baggage": True}
        with_bag = scorer.score(_flight(baggage_included=True), prefs)
        without_bag = scorer.score(_flight(baggage_included=False), prefs)
        assert with_bag["breakdown"]["baggage_fit"] > without_bag["breakdown"]["baggage_fit"]

    def test_red_eye_departure_scores_lower(self):
        scorer = FlightScorer()
        prefs = {"cabin_class": "economy"}
        redeye = scorer.score(_flight(departure_time="02:30"), prefs)
        daytime = scorer.score(_flight(departure_time="10:00"), prefs)
        assert redeye["breakdown"]["time_of_day_fit"] < daytime["breakdown"]["time_of_day_fit"]

    def test_short_trip_penalises_long_duration_more(self):
        scorer = FlightScorer()
        prefs = {"cabin_class": "economy"}
        long_flight = _flight(_total_duration_minutes=900)
        short_trip = scorer.score(long_flight, prefs, trip_duration_days=2)
        long_trip = scorer.score(long_flight, prefs, trip_duration_days=14)
        assert short_trip["breakdown"]["duration_fit"] <= long_trip["breakdown"]["duration_fit"]

    def test_dna_business_orientation_boosts_flexible_direct_flight(self):
        scorer = FlightScorer()
        prefs = {"cabin_class": "business"}
        dna = {"traits": {"business_orientation": 0.8}}
        flight = _flight(cabin_class="business", stops=0, flexibility="flexible")
        with_dna = scorer.score(flight, prefs, dna=dna)
        without_dna = scorer.score(flight, prefs, dna=None)
        assert with_dna["match_score"] >= without_dna["match_score"]
        assert len(with_dna["dna_notes"]) > 0

    def test_persona_scores_present_for_all_four_personas(self):
        scorer = FlightScorer()
        result = scorer.score(_flight(), preferences={"cabin_class": "economy"})
        assert set(result["persona_scores"].keys()) == {"family", "business", "comfort", "budget"}
