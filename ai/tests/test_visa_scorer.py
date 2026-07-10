from ai.discovery.visa.visa_scorer import VisaScorer


def _option(**overrides) -> dict:
    base = {
        "matched_type": "tier",
        "passport_expiry_date": "2030-01-01",
        "travel_purpose": "TOURISM",
        "transit_countries": [],
    }
    base.update(overrides)
    return base


class TestVisaScorer:
    def test_confidence_in_range(self):
        scorer = VisaScorer()
        result = scorer.score(_option())
        assert 0.0 <= result["confidence"] <= 1.0

    def test_deterministic_same_inputs_same_confidence(self):
        scorer = VisaScorer()
        o = _option()
        r1 = scorer.score(o)
        r2 = scorer.score(o)
        assert r1["confidence"] == r2["confidence"]

    def test_override_match_scores_higher_rule_specificity_than_unknown(self):
        scorer = VisaScorer()
        override = scorer.score(_option(matched_type="override"))
        unknown = scorer.score(_option(matched_type="unknown"))
        assert override["breakdown"]["rule_specificity"] > unknown["breakdown"]["rule_specificity"]
        assert override["confidence"] > unknown["confidence"]

    def test_tier_match_scores_higher_than_unknown(self):
        scorer = VisaScorer()
        tier = scorer.score(_option(matched_type="tier"))
        unknown = scorer.score(_option(matched_type="unknown"))
        assert tier["confidence"] > unknown["confidence"]

    def test_missing_passport_expiry_lowers_data_completeness(self):
        scorer = VisaScorer()
        with_expiry = scorer.score(_option(passport_expiry_date="2030-01-01"))
        without_expiry = scorer.score(_option(passport_expiry_date=None))
        assert with_expiry["breakdown"]["data_completeness"] > without_expiry["breakdown"]["data_completeness"]

    def test_other_purpose_lowers_purpose_clarity(self):
        scorer = VisaScorer()
        tourism = scorer.score(_option(travel_purpose="TOURISM"))
        other = scorer.score(_option(travel_purpose="OTHER"))
        assert tourism["breakdown"]["purpose_clarity"] > other["breakdown"]["purpose_clarity"]

    def test_study_purpose_less_clear_than_tourism(self):
        scorer = VisaScorer()
        tourism = scorer.score(_option(travel_purpose="TOURISM"))
        study = scorer.score(_option(travel_purpose="STUDY"))
        assert tourism["breakdown"]["purpose_clarity"] > study["breakdown"]["purpose_clarity"]

    def test_more_transit_countries_lowers_transit_simplicity(self):
        scorer = VisaScorer()
        none = scorer.score(_option(transit_countries=[]))
        two = scorer.score(_option(transit_countries=["USA", "UAE"]))
        assert none["breakdown"]["transit_simplicity"] > two["breakdown"]["transit_simplicity"]

    def test_transit_simplicity_has_a_floor(self):
        scorer = VisaScorer()
        result = scorer.score(_option(transit_countries=["A", "B", "C", "D", "E", "F"]))
        assert result["breakdown"]["transit_simplicity"] >= 0.3

    def test_no_transit_countries_gives_full_transit_simplicity(self):
        scorer = VisaScorer()
        result = scorer.score(_option(transit_countries=[]))
        assert result["breakdown"]["transit_simplicity"] == 1.0
