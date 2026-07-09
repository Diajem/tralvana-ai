from ai.discovery.accommodation.accommodation_risk_assessor import AccommodationRiskAssessor


def _accommodation(**overrides) -> dict:
    base = {
        "distance_to_centre": 0.5,
        "distance_to_transport": 0.3,
        "cancellation_policy": "free_cancellation",
        "review_score": 8.0,
        "safety_score": 0.8,
        "breakfast_included": True,
        "accessibility_features": ["elevator"],
    }
    base.update(overrides)
    return base


class TestAccommodationRiskAssessor:
    def test_close_to_transport_no_risk(self):
        assessor = AccommodationRiskAssessor()
        risks = assessor.assess(_accommodation(distance_to_transport=0.3))
        assert not any("public transport" in r.lower() for r in risks)

    def test_far_from_transport_flagged(self):
        assessor = AccommodationRiskAssessor()
        risks = assessor.assess(_accommodation(distance_to_transport=2.5))
        assert any("public transport" in r.lower() for r in risks)

    def test_far_from_centre_flagged(self):
        assessor = AccommodationRiskAssessor()
        risks = assessor.assess(_accommodation(distance_to_centre=6.0))
        assert any("city centre" in r.lower() for r in risks)

    def test_non_refundable_flagged(self):
        assessor = AccommodationRiskAssessor()
        risks = assessor.assess(_accommodation(cancellation_policy="non_refundable"))
        assert any("non-refundable" in r.lower() for r in risks)

    def test_low_review_score_flagged(self):
        assessor = AccommodationRiskAssessor()
        risks = assessor.assess(_accommodation(review_score=5.5))
        assert any("guest reviews" in r.lower() for r in risks)

    def test_low_safety_score_flagged(self):
        assessor = AccommodationRiskAssessor()
        risks = assessor.assess(_accommodation(safety_score=0.3))
        assert any("safety rating" in r.lower() for r in risks)

    def test_no_accessibility_features_flagged(self):
        assessor = AccommodationRiskAssessor()
        risks = assessor.assess(_accommodation(accessibility_features=[]))
        assert any("accessibility" in r.lower() for r in risks)

    def test_clean_central_option_has_minimal_risks(self):
        assessor = AccommodationRiskAssessor()
        risks = assessor.assess(_accommodation())
        assert len(risks) == 0
