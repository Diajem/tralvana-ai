from ai.discovery.visa.visa_intelligence import VisaIntelligence


class TestVisaIntelligence:
    def test_returns_full_assessment_shape(self):
        engine = VisaIntelligence()
        result = engine.check("UK", "Japan")
        for field in (
            "nationality", "passport_country", "destination_country", "transit_countries",
            "travel_purpose", "intended_length_of_stay", "passport_expiry_date",
            "passport_validity_months", "visa_status", "visa_required", "visa_type",
            "entry_requirements", "supporting_documents", "vaccination_requirements",
            "travel_authorisation_required", "processing_time", "confidence", "risks",
            "assumptions", "recommendation", "explanation",
        ):
            assert field in result, field

    def test_confidence_in_valid_range(self):
        engine = VisaIntelligence()
        result = engine.check("Nigeria", "USA")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_deterministic_same_inputs_same_result(self):
        engine = VisaIntelligence()
        r1 = engine.check("UK", "Japan", intended_length_of_stay=30)
        r2 = engine.check("UK", "Japan", intended_length_of_stay=30)
        assert r1 == r2

    def test_nationality_defaults_to_passport_country(self):
        engine = VisaIntelligence()
        result = engine.check("UK", "Japan")
        assert result["nationality"] == result["passport_country"]

    def test_explicit_nationality_overrides_default(self):
        engine = VisaIntelligence()
        result = engine.check("UK", "Japan", nationality="British")
        assert result["nationality"] == "British"

    def test_unknown_pair_adds_assumption(self):
        engine = VisaIntelligence()
        result = engine.check("Wakanda", "Atlantis")
        assert result["visa_status"] == "CHECK_MANUALLY"
        assert any("not in the mock rule set" in a for a in result["assumptions"])

    def test_no_passport_expiry_adds_assumption(self):
        engine = VisaIntelligence()
        result = engine.check("UK", "Japan", passport_expiry_date=None)
        assert any("expiry date" in a.lower() for a in result["assumptions"])

    def test_mock_data_disclaimer_always_present(self):
        engine = VisaIntelligence()
        result = engine.check("UK", "Japan")
        assert any("not legal advice" in a.lower() for a in result["assumptions"])

    def test_recommendation_matches_visa_status(self):
        engine = VisaIntelligence()
        not_required = engine.check("UK", "Japan")
        required = engine.check("Nigeria", "UK")
        assert "no visa action needed" in not_required["recommendation"].lower()
        assert "apply for a visa" in required["recommendation"].lower()

    def test_transit_country_requiring_action_produces_risk(self):
        engine = VisaIntelligence()
        result = engine.check("Nigeria", "France", transit_countries=["USA"])
        assert any("transiting through usa" in r.lower() for r in result["risks"])

    def test_reasonable_confidence_for_well_known_pair(self):
        engine = VisaIntelligence()
        result = engine.check("UK", "Japan", passport_expiry_date="2030-01-01")
        assert result["confidence"] >= 0.7

    def test_lower_confidence_for_unknown_pair_than_known_pair(self):
        engine = VisaIntelligence()
        unknown = engine.check("Wakanda", "Atlantis")
        known = engine.check("UK", "Japan", passport_expiry_date="2030-01-01")
        assert unknown["confidence"] < known["confidence"]

    def test_all_visa_statuses_have_a_recommendation(self):
        for status in (
            "VISA_NOT_REQUIRED", "VISA_REQUIRED", "ETA_REQUIRED",
            "EVISA_AVAILABLE", "CHECK_MANUALLY", "ENTRY_RESTRICTED",
        ):
            from ai.discovery.visa.visa_intelligence import _RECOMMENDATION
            assert status in _RECOMMENDATION
            assert _RECOMMENDATION[status]
