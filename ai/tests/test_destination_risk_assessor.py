from ai.discovery.destinations.destination_risk_assessor import DestinationRiskAssessor


def _destination(**overrides) -> dict:
    base = {
        "safety_score": 0.8,
        "distance_from_centre": 3.0,
        "transport_access_score": 0.7,
        "season_score": 0.8,
        "_popularity": 5,
    }
    base.update(overrides)
    return base


class TestDestinationRiskAssessor:
    def test_low_safety_score_flagged(self):
        assessor = DestinationRiskAssessor()
        risks = assessor.assess(_destination(safety_score=0.4))
        assert any("safety" in r.lower() for r in risks)

    def test_high_safety_score_not_flagged(self):
        assessor = DestinationRiskAssessor()
        risks = assessor.assess(_destination(safety_score=0.9))
        assert not any("safety rating" in r.lower() for r in risks)

    def test_far_from_centre_flagged(self):
        assessor = DestinationRiskAssessor()
        risks = assessor.assess(_destination(distance_from_centre=20.0))
        assert any("centre" in r.lower() for r in risks)

    def test_poor_transport_access_flagged(self):
        assessor = DestinationRiskAssessor()
        risks = assessor.assess(_destination(transport_access_score=0.2))
        assert any("transport" in r.lower() for r in risks)

    def test_off_season_flagged(self):
        assessor = DestinationRiskAssessor()
        risks = assessor.assess(_destination(season_score=0.5))
        assert any("season" in r.lower() for r in risks)

    def test_very_popular_flagged_for_crowds(self):
        assessor = DestinationRiskAssessor()
        risks = assessor.assess(_destination(_popularity=10))
        assert any("crowd" in r.lower() for r in risks)

    def test_clean_low_key_destination_has_minimal_risks(self):
        assessor = DestinationRiskAssessor()
        risks = assessor.assess(_destination(_popularity=5, season_score=0.8))
        assert len(risks) == 0
