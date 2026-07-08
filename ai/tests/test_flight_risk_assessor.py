from ai.discovery.flights.flight_risk_assessor import FlightRiskAssessor


def _flight(**overrides) -> dict:
    base = {
        "stops": 0,
        "layover_duration": "",
        "departure_time": "09:00",
        "refundability": "refundable",
        "flexibility": "flexible",
        "baggage_included": True,
        "cabin_class": "economy",
        "_total_duration_minutes": 360,
        "_layover_minutes": 0,
    }
    base.update(overrides)
    return base


class TestFlightRiskAssessor:
    def test_direct_flight_no_layover_risk(self):
        assessor = FlightRiskAssessor()
        risks = assessor.assess(_flight(stops=0))
        assert not any("layover" in r.lower() or "connection" in r.lower() for r in risks)

    def test_short_layover_flags_tight_connection(self):
        assessor = FlightRiskAssessor()
        risks = assessor.assess(_flight(stops=1, layover_duration="45m", _layover_minutes=45))
        assert any("tight connection" in r.lower() for r in risks)

    def test_long_layover_flagged(self):
        assessor = FlightRiskAssessor()
        risks = assessor.assess(_flight(stops=1, layover_duration="5h 0m", _layover_minutes=300))
        assert any("long layover" in r.lower() for r in risks)

    def test_two_stops_flags_connection_risk(self):
        assessor = FlightRiskAssessor()
        risks = assessor.assess(_flight(stops=2, layover_duration="2h 0m", _layover_minutes=120))
        assert any("two connections" in r.lower() for r in risks)

    def test_non_refundable_flagged(self):
        assessor = FlightRiskAssessor()
        risks = assessor.assess(_flight(refundability="non_refundable"))
        assert any("non-refundable" in r.lower() for r in risks)

    def test_fixed_fare_flagged(self):
        assessor = FlightRiskAssessor()
        risks = assessor.assess(_flight(flexibility="fixed"))
        assert any("fixed fare" in r.lower() for r in risks)

    def test_red_eye_departure_flagged(self):
        assessor = FlightRiskAssessor()
        risks = assessor.assess(_flight(departure_time="03:15"))
        assert any("red-eye" in r.lower() for r in risks)

    def test_no_baggage_flagged(self):
        assessor = FlightRiskAssessor()
        risks = assessor.assess(_flight(baggage_included=False))
        assert any("baggage" in r.lower() for r in risks)

    def test_clean_direct_flight_has_minimal_risks(self):
        assessor = FlightRiskAssessor()
        risks = assessor.assess(_flight())
        assert len(risks) == 0
