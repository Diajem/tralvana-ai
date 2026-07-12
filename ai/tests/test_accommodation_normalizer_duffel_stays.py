"""
AccommodationNormalizer._normalize_duffel_stays() (T-039) — every raw
Duffel Stays field maps into the canonical schema, and every field
Duffel simply doesn't provide gets a documented, neutral default,
never a fabricated value.
"""

from __future__ import annotations

from ai.discovery.accommodation.accommodation_normalizer import accommodation_normalizer


def _raw(**overrides) -> dict:
    base = {
        "_provider_source": "duffel_stays",
        "_destination": "Tokyo",
        "_provider_property_id": "acc_1",
        "_provider_rate_id": "rate_1",
        "property_name": "Test Hotel",
        "duffel_rating": 4,
        "duffel_review_score": 8.5,
        "duffel_review_count": 200,
        "duffel_amenities": ["pool", "workspace"],
        "duffel_latitude": 35.68,
        "duffel_longitude": 139.65,
        "duffel_city_name": "Tokyo",
        "duffel_region": "Tokyo Prefecture",
        "search_latitude": 35.6762,
        "search_longitude": 139.6503,
        "nightly_price": 120.0,
        "total_price": 240.0,
        "currency": "USD",
        "board_type": "breakfast",
        "cancellation_timeline": [{"refund_amount": "240.00", "currency": "USD", "before": "2026-09-25T00:00:00Z"}],
        "check_in_date": "2026-10-01",
        "nights": 2,
    }
    base.update(overrides)
    return base


class TestBasicFieldMapping:
    def test_property_name_and_price_mapped_directly(self):
        result = accommodation_normalizer.normalize(_raw())
        assert result["property_name"] == "Test Hotel"
        assert result["nightly_price"] == 120.0
        assert result["total_price"] == 240.0
        assert result["currency"] == "USD"

    def test_accommodation_type_defaults_to_hotel(self):
        result = accommodation_normalizer.normalize(_raw())
        assert result["accommodation_type"] == "HOTEL"

    def test_star_rating_mapped_from_duffel_rating(self):
        result = accommodation_normalizer.normalize(_raw(duffel_rating=5))
        assert result["star_rating"] == 5

    def test_star_rating_defaults_to_zero_when_absent(self):
        result = accommodation_normalizer.normalize(_raw(duffel_rating=None))
        assert result["star_rating"] == 0

    def test_neighbourhood_prefers_city_name_falls_back_to_region(self):
        result = accommodation_normalizer.normalize(_raw(duffel_city_name=None, duffel_region="Kanto"))
        assert result["neighbourhood"] == "Kanto"

    def test_provider_ids_preserved(self):
        result = accommodation_normalizer.normalize(_raw())
        assert result["_provider_property_id"] == "acc_1"
        assert result["_provider_rate_id"] == "rate_1"


class TestDistanceComputation:
    def test_same_coordinates_yield_zero_distance(self):
        result = accommodation_normalizer.normalize(
            _raw(duffel_latitude=35.6762, duffel_longitude=139.6503, search_latitude=35.6762, search_longitude=139.6503)
        )
        assert result["distance_to_centre"] == 0.0

    def test_nonzero_distance_computed_via_haversine(self):
        result = accommodation_normalizer.normalize(_raw())
        assert result["distance_to_centre"] > 0.0

    def test_missing_coordinates_default_to_zero_not_fabricated(self):
        result = accommodation_normalizer.normalize(_raw(duffel_latitude=None, duffel_longitude=None))
        assert result["distance_to_centre"] == 0.0

    def test_distance_to_transport_approximated_as_distance_to_centre(self):
        result = accommodation_normalizer.normalize(_raw())
        assert result["distance_to_transport"] == result["distance_to_centre"]


class TestReviewScoreAndSafety:
    def test_review_score_mapped_directly(self):
        result = accommodation_normalizer.normalize(_raw(duffel_review_score=9.1))
        assert result["review_score"] == 9.1

    def test_review_score_defaults_to_neutral_five_when_absent(self):
        result = accommodation_normalizer.normalize(_raw(duffel_review_score=None))
        assert result["review_score"] == 5.0

    def test_safety_score_always_neutral_duffel_provides_no_signal(self):
        result = accommodation_normalizer.normalize(_raw())
        assert result["safety_score"] == 0.5


class TestAmenityDrivenFields:
    def test_accessibility_feature_detected_from_amenity_keyword(self):
        result = accommodation_normalizer.normalize(_raw(duffel_amenities=["pool", "wheelchair_accessible"]))
        assert "wheelchair_accessible" in result["accessibility_features"]

    def test_no_accessibility_keywords_yields_empty_list(self):
        result = accommodation_normalizer.normalize(_raw(duffel_amenities=["pool", "bar"]))
        assert result["accessibility_features"] == []

    def test_business_friendly_true_for_workspace_amenity(self):
        result = accommodation_normalizer.normalize(_raw(duffel_amenities=["workspace"]))
        assert result["business_friendly"] is True


class TestBreakfastMapping:
    def test_breakfast_board_type_included(self):
        result = accommodation_normalizer.normalize(_raw(board_type="breakfast"))
        assert result["breakfast_included"] is True

    def test_all_inclusive_board_type_included(self):
        result = accommodation_normalizer.normalize(_raw(board_type="all_inclusive"))
        assert result["breakfast_included"] is True

    def test_room_only_board_type_not_included(self):
        result = accommodation_normalizer.normalize(_raw(board_type="room_only"))
        assert result["breakfast_included"] is False

    def test_missing_board_type_defaults_to_not_included(self):
        result = accommodation_normalizer.normalize(_raw(board_type=None))
        assert result["breakfast_included"] is False


class TestCancellationPolicyMapping:
    def test_full_refund_maps_to_free_cancellation(self):
        result = accommodation_normalizer.normalize(
            _raw(total_price=240.0, cancellation_timeline=[{"refund_amount": "240.00"}])
        )
        assert result["cancellation_policy"] == "free_cancellation"

    def test_zero_refund_maps_to_non_refundable(self):
        result = accommodation_normalizer.normalize(
            _raw(total_price=240.0, cancellation_timeline=[{"refund_amount": "0.00"}])
        )
        assert result["cancellation_policy"] == "non_refundable"

    def test_partial_refund_maps_to_partial_refund(self):
        result = accommodation_normalizer.normalize(
            _raw(total_price=240.0, cancellation_timeline=[{"refund_amount": "100.00"}])
        )
        assert result["cancellation_policy"] == "partial_refund"

    def test_missing_timeline_maps_to_unknown(self):
        result = accommodation_normalizer.normalize(_raw(cancellation_timeline=None))
        assert result["cancellation_policy"] == "unknown"

    def test_malformed_timeline_entry_maps_to_unknown_not_a_crash(self):
        result = accommodation_normalizer.normalize(_raw(cancellation_timeline=[{"no_refund_amount_key": True}]))
        assert result["cancellation_policy"] == "unknown"


class TestScoresAreValidRange:
    def test_comfort_and_location_scores_within_bounds(self):
        result = accommodation_normalizer.normalize(_raw())
        assert 0.0 <= result["comfort_score"] <= 1.0
        assert 0.0 <= result["location_score"] <= 1.0

    def test_scoring_pipeline_accepts_duffel_normalized_output(self):
        """The real contract this normalizer must satisfy — no
        adapter-specific field ever required downstream."""
        from ai.discovery.accommodation.accommodation_reasoner import accommodation_reasoner
        from ai.discovery.accommodation.accommodation_risk_assessor import accommodation_risk_assessor
        from ai.discovery.accommodation.accommodation_scorer import accommodation_scorer

        normalized = accommodation_normalizer.normalize(_raw())
        normalized["_price_anchor"] = 100.0
        prefs = {
            "accommodation_type": None, "max_price_usd": 300, "location_preference": "central",
            "needs_breakfast": False, "needs_flexible_cancellation": False,
            "accessibility_required": False, "has_children": False, "is_business_trip": False,
        }
        score_result = accommodation_scorer.score(normalized, prefs)
        assert 0.0 <= score_result["match_score"] <= 1.0
        explanation = accommodation_reasoner.explain(normalized, score_result, prefs)
        assert normalized["property_name"] in explanation
        risks = accommodation_risk_assessor.assess(normalized)
        assert isinstance(risks, list)


class TestMockPathUnaffected:
    def test_mock_shaped_raw_record_still_uses_the_original_path(self):
        mock_raw = {
            "hotel_name": "Mock Hotel", "property_type": "hotel", "star_rating": 3, "area": "Centre",
            "km_to_center": 0.5, "km_to_transit": 0.3, "price_per_night": 100, "currency_code": "USD",
            "includes_breakfast": True, "cancellation": "free_cancellation", "accessibility": [],
            "guest_rating": 8.0, "cleanliness_rating": 8.0, "safety_rating": 8.0, "amenities": [],
            "check_in_date": "2026-10-01", "nights": 2, "_destination": "Paris",
        }
        result = accommodation_normalizer.normalize(mock_raw)
        assert result["property_name"] == "Mock Hotel"
        assert result["safety_score"] == 0.8  # from safety_rating, not the Duffel neutral default
