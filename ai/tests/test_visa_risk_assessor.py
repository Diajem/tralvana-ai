from ai.discovery.visa.visa_risk_assessor import VisaRiskAssessor


def _option(**overrides) -> dict:
    base = {
        "passport_expiry_date": "2030-01-01",
        "passport_validity_months": 42.0,
        "intended_length_of_stay": 14,
        "max_stay_days": 90,
        "transit_status": [],
        "travel_purpose": "TOURISM",
        "matched_type": "tier",
    }
    base.update(overrides)
    return base


class TestVisaRiskAssessor:
    def test_missing_passport_expiry_flagged(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(_option(passport_expiry_date=None, passport_validity_months=None), confidence=0.9)
        assert any("not supplied" in r.lower() for r in risks)

    def test_low_passport_validity_flagged(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(_option(passport_validity_months=3.0), confidence=0.9)
        assert any("6 months" in r for r in risks)

    def test_healthy_passport_validity_not_flagged(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(_option(passport_validity_months=24.0), confidence=0.9)
        assert not any("6 months" in r for r in risks)

    def test_passport_validity_shorter_than_stay_flagged(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(
            _option(passport_validity_months=0.3, intended_length_of_stay=30), confidence=0.9
        )
        assert any("shorter than the intended length of stay" in r.lower() for r in risks)

    def test_stay_exceeds_max_stay_days_flagged(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(
            _option(intended_length_of_stay=120, max_stay_days=90), confidence=0.9
        )
        assert any("exceeds the" in r.lower() and "allowance" in r.lower() for r in risks)

    def test_stay_within_max_stay_days_not_flagged(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(
            _option(intended_length_of_stay=30, max_stay_days=90), confidence=0.9
        )
        assert not any("allowance" in r.lower() for r in risks)

    def test_transit_requiring_action_flagged(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(
            _option(transit_status=[{"country": "USA", "status": "VISA_REQUIRED", "requires_action": True}]),
            confidence=0.9,
        )
        assert any("transiting through usa" in r.lower() for r in risks)

    def test_transit_not_requiring_action_not_flagged(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(
            _option(transit_status=[{"country": "France", "status": "VISA_NOT_REQUIRED", "requires_action": False}]),
            confidence=0.9,
        )
        assert not any("transiting" in r.lower() for r in risks)

    def test_other_travel_purpose_flags_missing_documentation(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(_option(travel_purpose="OTHER"), confidence=0.9)
        assert any("purpose was not specified" in r.lower() for r in risks)

    def test_unknown_rule_flagged(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(_option(matched_type="unknown"), confidence=0.9)
        assert any("no specific rule" in r.lower() for r in risks)

    def test_low_confidence_flagged(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(_option(), confidence=0.3)
        assert any("confidence" in r.lower() and "low" in r.lower() for r in risks)

    def test_high_confidence_not_flagged_for_confidence(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(_option(), confidence=0.9)
        assert not any("confidence in this assessment is low" in r.lower() for r in risks)

    def test_clean_assessment_has_minimal_risks(self):
        assessor = VisaRiskAssessor()
        risks = assessor.assess(_option(), confidence=0.9)
        assert len(risks) == 0
