from ai.discovery.accommodation.accommodation_normalizer import AccommodationNormalizer


def _raw(**overrides) -> dict:
    base = {
        "hotel_name": "Test Hotel",
        "property_type": "hotel",
        "star_rating": 3,
        "area": "City Centre",
        "km_to_center": 0.5,
        "km_to_transit": 0.3,
        "price_per_night": 100.0,
        "currency_code": "USD",
        "includes_breakfast": True,
        "cancellation": "free_cancellation",
        "accessibility": ["elevator"],
        "guest_rating": 8.0,
        "cleanliness_rating": 8.0,
        "safety_rating": 8.0,
        "amenities": ["restaurant"],
        "check_in_date": "2026-09-15",
        "nights": 5,
        "_destination": "Testville",
    }
    base.update(overrides)
    return base


class TestAccommodationNormalizer:
    def test_maps_raw_property_type_to_canonical_enum_value(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw(property_type="boutique_hotel"))
        assert result["accommodation_type"] == "BOUTIQUE_HOTEL"

    def test_unknown_property_type_falls_back_to_hotel(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw(property_type="something_unrecognised"))
        assert result["accommodation_type"] == "HOTEL"

    def test_total_price_is_nightly_times_nights(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw(price_per_night=100.0, nights=5))
        assert result["total_price"] == 500.0

    def test_comfort_score_in_range(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw())
        assert 0.0 <= result["comfort_score"] <= 1.0

    def test_higher_star_rating_increases_comfort_score(self):
        normalizer = AccommodationNormalizer()
        low = normalizer.normalize(_raw(star_rating=2, cleanliness_rating=6.0))
        high = normalizer.normalize(_raw(star_rating=5, cleanliness_rating=9.5))
        assert high["comfort_score"] > low["comfort_score"]

    def test_location_score_in_range(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw())
        assert 0.0 <= result["location_score"] <= 1.0

    def test_closer_to_centre_scores_higher_location(self):
        normalizer = AccommodationNormalizer()
        central = normalizer.normalize(_raw(km_to_center=0.2, km_to_transit=0.1))
        far = normalizer.normalize(_raw(km_to_center=8.0, km_to_transit=6.0))
        assert central["location_score"] > far["location_score"]

    def test_safety_score_normalized_to_0_1(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw(safety_rating=9.0))
        assert result["safety_score"] == 0.9

    def test_family_friendly_true_for_apartment_type(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw(property_type="apartment", amenities=[]))
        assert result["family_friendly"] is True

    def test_family_friendly_true_when_kitchen_amenity_present(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw(property_type="hotel", amenities=["kitchen"]))
        assert result["family_friendly"] is True

    def test_family_friendly_false_for_plain_hostel(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw(property_type="hostel", amenities=["lockers"]))
        assert result["family_friendly"] is False

    def test_business_friendly_true_for_serviced_apartment(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw(property_type="serviced_apartment", amenities=[]))
        assert result["business_friendly"] is True

    def test_business_friendly_true_when_workspace_amenity_present(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw(property_type="hostel", amenities=["workspace"]))
        assert result["business_friendly"] is True

    def test_review_score_passed_through_on_0_to_10_scale(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw(guest_rating=7.3))
        assert result["review_score"] == 7.3

    def test_destination_carried_through(self):
        normalizer = AccommodationNormalizer()
        result = normalizer.normalize(_raw(_destination="Lisbon"))
        assert result["destination"] == "Lisbon"
