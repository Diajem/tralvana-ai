from ai.discovery.visa.visa_reasoner import VisaReasoner


def _option(**overrides) -> dict:
    base = {
        "nationality": "British", "destination_country": "Japan",
        "travel_purpose": "TOURISM", "visa_status": "VISA_NOT_REQUIRED",
        "max_stay_days": 90, "intended_length_of_stay": 14,
        "passport_validity_months": 24.0, "transit_countries": [], "transit_status": [],
        "matched_type": "tier", "processing_time": "Not applicable",
    }
    base.update(overrides)
    return base


def _score_result() -> dict:
    return {"confidence": 0.9, "breakdown": {}}


class TestVisaReasoner:
    def test_explains_visa_not_required(self):
        reasoner = VisaReasoner()
        explanation = reasoner.explain(_option(), _score_result())
        assert "no visa is required" in explanation.lower()

    def test_explains_visa_required(self):
        reasoner = VisaReasoner()
        explanation = reasoner.explain(_option(visa_status="VISA_REQUIRED"), _score_result())
        assert "a visa is required" in explanation.lower()

    def test_explains_eta_required(self):
        reasoner = VisaReasoner()
        explanation = reasoner.explain(_option(visa_status="ETA_REQUIRED"), _score_result())
        assert "electronic travel authorisation" in explanation.lower()

    def test_mentions_passport_validity_when_known(self):
        reasoner = VisaReasoner()
        explanation = reasoner.explain(_option(passport_validity_months=24.0), _score_result())
        assert "24.0 month" in explanation

    def test_flags_short_passport_validity(self):
        reasoner = VisaReasoner()
        explanation = reasoner.explain(_option(passport_validity_months=2.0), _score_result())
        assert "below the 6 months" in explanation.lower()

    def test_mentions_missing_passport_expiry(self):
        reasoner = VisaReasoner()
        explanation = reasoner.explain(_option(passport_validity_months=None), _score_result())
        assert "not supplied" in explanation.lower()

    def test_mentions_transit_when_present_and_flagged(self):
        reasoner = VisaReasoner()
        explanation = reasoner.explain(
            _option(
                transit_countries=["USA"],
                transit_status=[{"country": "USA", "status": "VISA_REQUIRED", "requires_action": True}],
            ),
            _score_result(),
        )
        assert "transiting through usa" in explanation.lower()

    def test_mentions_no_transit_when_absent(self):
        reasoner = VisaReasoner()
        explanation = reasoner.explain(_option(transit_countries=[]), _score_result())
        assert "no transit countries" in explanation.lower()

    def test_flags_exceeding_max_stay(self):
        reasoner = VisaReasoner()
        explanation = reasoner.explain(
            _option(intended_length_of_stay=120, max_stay_days=90), _score_result()
        )
        assert "exceeds that allowance" in explanation.lower()

    def test_mentions_unknown_rule_assumption(self):
        reasoner = VisaReasoner()
        explanation = reasoner.explain(_option(matched_type="unknown"), _score_result())
        assert "general estimate only" in explanation.lower()

    def test_includes_next_step_for_visa_required(self):
        reasoner = VisaReasoner()
        explanation = reasoner.explain(
            _option(visa_status="VISA_REQUIRED", processing_time="Around 3 weeks"), _score_result()
        )
        assert "apply for the required visa" in explanation.lower()
        assert "around 3 weeks" in explanation.lower()

    def test_includes_next_step_for_check_manually(self):
        reasoner = VisaReasoner()
        explanation = reasoner.explain(_option(visa_status="CHECK_MANUALLY"), _score_result())
        assert "contact the destination's embassy" in explanation.lower()
