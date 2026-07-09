from ai.discovery.accommodation.accommodation_scorer import AccommodationScorer


def _accommodation(**overrides) -> dict:
    base = {
        "property_name": "Test Hotel",
        "accommodation_type": "HOTEL",
        "star_rating": 3,
        "neighbourhood": "City Centre",
        "distance_to_centre": 0.5,
        "distance_to_transport": 0.3,
        "nightly_price": 100.0,
        "total_price": 500.0,
        "currency": "USD",
        "breakfast_included": True,
        "cancellation_policy": "free_cancellation",
        "accessibility_features": ["elevator"],
        "family_friendly": False,
        "business_friendly": False,
        "review_score": 8.0,
        "safety_score": 0.8,
        "comfort_score": 0.7,
        "location_score": 0.8,
        "_price_anchor": 100.0,
    }
    base.update(overrides)
    return base


class TestAccommodationScorer:
    def test_match_score_in_range(self):
        scorer = AccommodationScorer()
        result = scorer.score(_accommodation(), preferences={})
        assert 0.0 <= result["match_score"] <= 1.0

    def test_deterministic_same_inputs_same_score(self):
        scorer = AccommodationScorer()
        a = _accommodation()
        prefs = {"max_price_usd": 150}
        r1 = scorer.score(a, prefs)
        r2 = scorer.score(a, prefs)
        assert r1["match_score"] == r2["match_score"]

    def test_cheaper_option_scores_higher_price_fit(self):
        scorer = AccommodationScorer()
        prefs = {"max_price_usd": 150}
        cheap = scorer.score(_accommodation(nightly_price=80), prefs)
        expensive = scorer.score(_accommodation(nightly_price=280), prefs)
        assert cheap["breakdown"]["price_fit"] > expensive["breakdown"]["price_fit"]

    def test_matching_accommodation_type_scores_higher(self):
        scorer = AccommodationScorer()
        prefs = {"accommodation_type": "VILLA"}
        match = scorer.score(_accommodation(accommodation_type="VILLA"), prefs)
        mismatch = scorer.score(_accommodation(accommodation_type="HOSTEL"), prefs)
        assert match["breakdown"]["type_preference_fit"] > mismatch["breakdown"]["type_preference_fit"]

    def test_central_location_preference_uses_objective_location_score(self):
        scorer = AccommodationScorer()
        prefs = {"location_preference": "central"}
        result = scorer.score(_accommodation(location_score=0.9), prefs)
        assert result["breakdown"]["location_fit"] == 0.9

    def test_breakfast_required_but_missing_penalised(self):
        scorer = AccommodationScorer()
        prefs = {"needs_breakfast": True}
        with_breakfast = scorer.score(_accommodation(breakfast_included=True), prefs)
        without_breakfast = scorer.score(_accommodation(breakfast_included=False), prefs)
        assert with_breakfast["breakdown"]["breakfast_fit"] > without_breakfast["breakdown"]["breakfast_fit"]

    def test_accessibility_required_but_missing_heavily_penalised(self):
        scorer = AccommodationScorer()
        prefs = {"accessibility_required": True}
        with_features = scorer.score(_accommodation(accessibility_features=["elevator"]), prefs)
        without_features = scorer.score(_accommodation(accessibility_features=[]), prefs)
        assert with_features["breakdown"]["accessibility_fit"] > without_features["breakdown"]["accessibility_fit"]
        assert without_features["breakdown"]["accessibility_fit"] <= 0.2

    def test_family_needs_favour_family_friendly_property(self):
        scorer = AccommodationScorer()
        prefs = {"has_children": True}
        family = scorer.score(_accommodation(family_friendly=True), prefs)
        not_family = scorer.score(_accommodation(family_friendly=False), prefs)
        assert family["breakdown"]["family_fit"] > not_family["breakdown"]["family_fit"]

    def test_business_needs_favour_business_friendly_property(self):
        scorer = AccommodationScorer()
        prefs = {"is_business_trip": True}
        business = scorer.score(_accommodation(business_friendly=True), prefs)
        not_business = scorer.score(_accommodation(business_friendly=False), prefs)
        assert business["breakdown"]["business_fit"] > not_business["breakdown"]["business_fit"]

    def test_dna_luxury_orientation_boosts_high_star_rating(self):
        scorer = AccommodationScorer()
        dna = {"traits": {"luxury_orientation": 0.8}}
        a = _accommodation(star_rating=5)
        with_dna = scorer.score(a, {}, dna=dna)
        without_dna = scorer.score(a, {}, dna=None)
        assert with_dna["match_score"] >= without_dna["match_score"]
        assert len(with_dna["dna_notes"]) > 0

    def test_persona_scores_present_for_all_six_personas(self):
        scorer = AccommodationScorer()
        result = scorer.score(_accommodation(), preferences={})
        assert set(result["persona_scores"].keys()) == {
            "value", "location", "comfort", "family", "business", "budget",
        }
