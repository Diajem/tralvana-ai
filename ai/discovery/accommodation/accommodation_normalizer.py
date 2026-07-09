from __future__ import annotations

from typing import Any

# Raw provider vocabulary -> canonical AccommodationType values.
_TYPE_MAP: dict[str, str] = {
    "hotel": "HOTEL",
    "apartment": "APARTMENT",
    "hostel": "HOSTEL",
    "villa": "VILLA",
    "resort": "RESORT",
    "serviced_apartment": "SERVICED_APARTMENT",
    "boutique_hotel": "BOUTIQUE_HOTEL",
    "guesthouse": "GUESTHOUSE",
}

_COMFORT_AMENITIES = {"pool", "spa", "private_pool", "private_beach"}
_BUSINESS_AMENITIES = {"workspace", "gym"}
_FAMILY_TYPES = {"APARTMENT", "VILLA", "RESORT", "GUESTHOUSE"}
_CENTRAL_KM = 1.0
_FAR_CENTRE_KM = 6.0
_FAR_TRANSIT_KM = 4.0


class AccommodationNormalizer:
    """
    Converts a raw MockAccommodationProvider record into the canonical
    internal schema, and computes the objective (preference-independent)
    scores every downstream stage relies on: comfort_score, location_score,
    safety_score. These are properties of the accommodation itself — the
    same for every traveller. See docs/DISCOVERY_LAYER_PATTERN.md.
    """

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        accommodation_type = _TYPE_MAP.get(raw["property_type"], "HOTEL")
        amenities = set(raw.get("amenities", []))
        nights = raw["nights"]
        nightly_price = raw["price_per_night"]

        comfort_score = self._comfort_score(raw, amenities)
        location_score = self._location_score(raw)
        safety_score = round(min(max(raw["safety_rating"] / 10, 0.0), 1.0), 2)

        return {
            "destination": raw.get("_destination", ""),
            "property_name": raw["hotel_name"],
            "accommodation_type": accommodation_type,
            "star_rating": raw["star_rating"],
            "neighbourhood": raw["area"],
            "distance_to_centre": raw["km_to_center"],
            "distance_to_transport": raw["km_to_transit"],
            "nightly_price": nightly_price,
            "total_price": round(nightly_price * nights, 2),
            "currency": raw["currency_code"],
            "breakfast_included": raw["includes_breakfast"],
            "cancellation_policy": raw["cancellation"],
            "accessibility_features": raw["accessibility"],
            "family_friendly": self._family_friendly(accommodation_type, amenities),
            "business_friendly": self._business_friendly(accommodation_type, amenities, raw["km_to_center"]),
            "review_score": raw["guest_rating"],
            "safety_score": safety_score,
            "comfort_score": comfort_score,
            "location_score": location_score,
            "check_in_date": raw["check_in_date"],
            "nights": nights,
            "_amenities": list(amenities),
        }

    # ------------------------------------------------------------------

    def _comfort_score(self, raw: dict[str, Any], amenities: set[str]) -> float:
        star_component = raw["star_rating"] / 5
        cleanliness_component = raw["cleanliness_rating"] / 10
        amenity_bonus = 1.0 if amenities & _COMFORT_AMENITIES else 0.5
        score = 0.5 * star_component + 0.3 * cleanliness_component + 0.2 * amenity_bonus
        return round(min(max(score, 0.0), 1.0), 2)

    def _location_score(self, raw: dict[str, Any]) -> float:
        centre_component = max(0.0, 1 - raw["km_to_center"] / _FAR_CENTRE_KM)
        transit_component = max(0.0, 1 - raw["km_to_transit"] / _FAR_TRANSIT_KM)
        score = 0.6 * centre_component + 0.4 * transit_component
        return round(min(max(score, 0.0), 1.0), 2)

    def _family_friendly(self, accommodation_type: str, amenities: set[str]) -> bool:
        return accommodation_type in _FAMILY_TYPES or "kitchen" in amenities

    def _business_friendly(self, accommodation_type: str, amenities: set[str], km_to_center: float) -> bool:
        if amenities & _BUSINESS_AMENITIES or accommodation_type == "SERVICED_APARTMENT":
            return True
        return accommodation_type in {"HOTEL", "BOUTIQUE_HOTEL"} and km_to_center <= _CENTRAL_KM


accommodation_normalizer = AccommodationNormalizer()
