from __future__ import annotations

from ai.discovery.accommodation.accommodation_normalizer import accommodation_normalizer


def _raw(**overrides) -> dict:
    raw = {
        "_provider_source": "hbx_hotels",
        "_destination": "Manchester",
        "_provider_property_id": "101",
        "_provider_rate_id": "rate-key",
        "property_name": "HBX Test Hotel",
        "hbx_category_name": "4 STARS",
        "hbx_destination_name": "Manchester",
        "hbx_zone_name": "City Centre",
        "board_code": "BB",
        "total_price": 450.0,
        "nightly_price": 150.0,
        "currency": "GBP",
        "cancellation_policies": [{"amount": "450", "from": "2027-09-14T00:00:00+00:00"}],
        "check_in_date": "2027-09-15",
        "nights": 3,
    }
    raw.update(overrides)
    return raw


def test_hbx_rate_normalizes_without_inventing_static_content():
    result = accommodation_normalizer.normalize(_raw())

    assert result["property_name"] == "HBX Test Hotel"
    assert result["star_rating"] == 4
    assert result["breakfast_included"] is True
    assert result["total_price"] == 450.0
    assert result["_provider_rate_id"] == "rate-key"
    assert result["review_score"] == 5.0
    assert result["safety_score"] == 0.5
    assert result["location_score"] == 0.5
    assert result["image_url"] is None
    assert result["_data_assumptions"]


def test_hbx_board_and_category_mapping_are_provider_specific():
    result = accommodation_normalizer.normalize(
        _raw(hbx_category_name="APARTMENT 3 KEYS", board_code="RO")
    )

    assert result["accommodation_type"] == "APARTMENT"
    assert result["star_rating"] == 3
    assert result["breakfast_included"] is False
