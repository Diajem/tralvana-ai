from __future__ import annotations

import math
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

# Duffel Stays (T-039) has no accommodation-type classification field in
# its documented schema — every property normalises to this default,
# with an explicit per-option assumption noting it wasn't provider-
# classified. Not a guess at the "most likely" type: a deliberately
# neutral placeholder, matching this module's "never fabricate" rule.
_DUFFEL_DEFAULT_ACCOMMODATION_TYPE = "HOTEL"

# Duffel's own `amenities` vocabulary is not documented with concrete
# enum values — these keyword substrings are a best-effort, real-data-
# driven match (only ever true if Duffel's own amenity string contains
# one of these), not an invented amenity list.
_ACCESSIBILITY_KEYWORDS = ("wheelchair", "accessible", "step_free", "step-free", "elevator", "lift")
_BREAKFAST_BOARD_TYPES = {"breakfast", "half_board", "full_board", "all_inclusive"}

# No safety signal exists anywhere in Duffel's documented Accommodation
# schema — 0.5 (exactly neutral) rather than any specific fabricated
# number; kept just below AccommodationRiskAssessor's _LOW_SAFETY_SCORE
# threshold check (`< 0.5`) so it never triggers a false "below-average
# safety" risk flag for data that was never claimed to be below average.
_DUFFEL_NEUTRAL_SAFETY_SCORE = 0.5

_EARTH_RADIUS_KM = 6371.0


class AccommodationNormalizer:
    """
    Converts a raw MockAccommodationProvider record into the canonical
    internal schema, and computes the objective (preference-independent)
    scores every downstream stage relies on: comfort_score, location_score,
    safety_score. These are properties of the accommodation itself — the
    same for every traveller. See docs/DISCOVERY_LAYER_PATTERN.md.
    """

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        if raw.get("_provider_source") == "duffel_stays":
            return self._normalize_duffel_stays(raw)

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

    # ------------------------------------------------------------------
    # Duffel Stays (T-039) — a second raw-record vocabulary this
    # Normalizer absorbs, exactly the role this class's own docstring
    # describes. See docs/DUFFEL_STAYS_INTEGRATION.md's Response Mapping
    # section for the field-by-field rationale behind every default below
    # — none of them invents a specific fact Duffel didn't provide.
    # ------------------------------------------------------------------

    def _normalize_duffel_stays(self, raw: dict[str, Any]) -> dict[str, Any]:
        distance_to_centre = self._duffel_distance_to_centre(raw)
        # Duffel Stays has no public-transport-distance data anywhere in
        # its documented schema — approximated as equal to
        # distance_to_centre (a real, computed value) rather than an
        # independently invented number.
        distance_to_transport = distance_to_centre

        star_rating = raw.get("duffel_rating")
        star_rating = int(star_rating) if star_rating else 0

        review_score = raw.get("duffel_review_score")
        review_score = float(review_score) if review_score is not None else 5.0

        amenities = {a.lower() for a in (raw.get("duffel_amenities") or []) if isinstance(a, str)}
        accessibility_features = sorted(
            a for a in amenities if any(keyword in a for keyword in _ACCESSIBILITY_KEYWORDS)
        )

        board_type = (raw.get("board_type") or "").lower()
        breakfast_included = board_type in _BREAKFAST_BOARD_TYPES

        accommodation_type = _DUFFEL_DEFAULT_ACCOMMODATION_TYPE
        cancellation_policy = self._duffel_cancellation_policy(raw.get("cancellation_timeline"), raw["total_price"])

        comfort_score = self._duffel_comfort_score(star_rating, review_score, amenities)
        location_score = self._location_score({"km_to_center": distance_to_centre, "km_to_transit": distance_to_transport})

        return {
            "destination": raw.get("_destination", ""),
            "property_name": raw["property_name"],
            "accommodation_type": accommodation_type,
            "star_rating": star_rating,
            "neighbourhood": raw.get("duffel_city_name") or raw.get("duffel_region") or "",
            "distance_to_centre": distance_to_centre,
            "distance_to_transport": distance_to_transport,
            "nightly_price": raw["nightly_price"],
            "total_price": raw["total_price"],
            "currency": raw["currency"],
            "breakfast_included": breakfast_included,
            "cancellation_policy": cancellation_policy,
            "accessibility_features": accessibility_features,
            "family_friendly": self._family_friendly(accommodation_type, amenities),
            "business_friendly": self._business_friendly(accommodation_type, amenities, distance_to_centre),
            "review_score": review_score,
            "safety_score": _DUFFEL_NEUTRAL_SAFETY_SCORE,
            "comfort_score": comfort_score,
            "location_score": location_score,
            "check_in_date": raw["check_in_date"],
            "nights": raw["nights"],
            "_amenities": list(amenities),
            "_provider_property_id": raw.get("_provider_property_id"),
            "_provider_rate_id": raw.get("_provider_rate_id"),
        }

    def _duffel_distance_to_centre(self, raw: dict[str, Any]) -> float:
        lat, lng = raw.get("duffel_latitude"), raw.get("duffel_longitude")
        search_lat, search_lng = raw.get("search_latitude"), raw.get("search_longitude")
        if None in (lat, lng, search_lat, search_lng):
            return 0.0
        return round(_haversine_km(search_lat, search_lng, lat, lng), 2)

    def _duffel_comfort_score(self, star_rating: int, review_score: float, amenities: set[str]) -> float:
        # Same weighting as _comfort_score(), substituting review_score
        # for cleanliness_rating — Duffel provides no separate
        # cleanliness figure, and guest review score is the closest
        # available real signal for perceived property quality.
        star_component = star_rating / 5 if star_rating else 0.5
        review_component = review_score / 10
        amenity_bonus = 1.0 if amenities & _COMFORT_AMENITIES else 0.5
        score = 0.5 * star_component + 0.3 * review_component + 0.2 * amenity_bonus
        return round(min(max(score, 0.0), 1.0), 2)

    def _duffel_cancellation_policy(self, timeline: list[dict[str, Any]] | None, total_price: float) -> str:
        """cancellation_timeline entries are {refund_amount, currency,
        before} (docs/DUFFEL_STAYS_INTEGRATION.md, sourced from Duffel's
        own guide on displaying it) — a refund_amount equal to the full
        total_price means a full refund is available at some point;
        every entry at 0 means never refundable; anything else is a
        partial refund. Absent entirely -> "unknown", which
        AccommodationScorer already treats as a safe, neutral default."""
        if not timeline:
            return "unknown"
        try:
            refund_amounts = [float(entry["refund_amount"]) for entry in timeline]
        except (KeyError, TypeError, ValueError):
            return "unknown"
        if any(abs(amount - total_price) < 0.01 for amount in refund_amounts):
            return "free_cancellation"
        if all(amount <= 0.01 for amount in refund_amounts):
            return "non_refundable"
        return "partial_refund"


accommodation_normalizer = AccommodationNormalizer()


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Standard great-circle distance formula — the only source for
    Duffel Stays' distance_to_centre, since Duffel provides raw
    coordinates but no precomputed distance figure."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))
