from __future__ import annotations

from typing import Any

# Base nightly rate anchor in USD, scaled by route-seeded variance and template
# multiplier below. Mirrors ai/discovery/flights/flight_intelligence.py's
# _CABIN_BASE_USD anchoring approach.
_BASE_NIGHTLY_USD = 90

# Deliberately raw, provider-shaped records — different field names and
# vocabulary than the domain's canonical AccommodationOption schema. This is
# what a real Booking.com/Expedia adapter's response would look like: the
# Normalizer's job is to absorb exactly this kind of inconsistency so nothing
# downstream (Scorer, Reasoner, Risk Assessor) ever has to change.
_TEMPLATES: list[dict[str, Any]] = [
    {
        "hotel_name": "The {dest} Boutique",
        "property_type": "boutique_hotel",
        "star_rating": 4,
        "area": "City Centre",
        "km_to_center": 0.4,
        "km_to_transit": 0.2,
        "price_multiplier": 1.3,
        "includes_breakfast": True,
        "cancellation": "free_cancellation",
        "accessibility": ["elevator", "step_free_access"],
        "guest_rating": 8.9,
        "cleanliness_rating": 9.0,
        "safety_rating": 8.5,
        "amenities": ["restaurant", "bar", "concierge"],
    },
    {
        "hotel_name": "{dest} Backpackers Hostel",
        "property_type": "hostel",
        "star_rating": 2,
        "area": "Old Town",
        "km_to_center": 0.8,
        "km_to_transit": 0.3,
        "price_multiplier": 0.35,
        "includes_breakfast": False,
        "cancellation": "non_refundable",
        "accessibility": [],
        "guest_rating": 7.2,
        "cleanliness_rating": 6.8,
        "safety_rating": 7.0,
        "amenities": ["shared_kitchen", "lockers"],
    },
    {
        "hotel_name": "{dest} Family Apartments",
        "property_type": "apartment",
        "star_rating": 3,
        "area": "Riverside",
        "km_to_center": 2.5,
        "km_to_transit": 1.0,
        "price_multiplier": 0.75,
        "includes_breakfast": False,
        "cancellation": "partial_refund",
        "accessibility": ["elevator"],
        "guest_rating": 8.0,
        "cleanliness_rating": 7.8,
        "safety_rating": 7.8,
        "amenities": ["kitchen", "washing_machine"],
    },
    {
        "hotel_name": "{dest} Grand Resort & Spa",
        "property_type": "resort",
        "star_rating": 5,
        "area": "Coastal District",
        "km_to_center": 6.0,
        "km_to_transit": 3.5,
        "price_multiplier": 1.9,
        "includes_breakfast": True,
        "cancellation": "free_cancellation",
        "accessibility": ["elevator", "step_free_access", "accessible_bathroom"],
        "guest_rating": 9.2,
        "cleanliness_rating": 9.4,
        "safety_rating": 9.0,
        "amenities": ["pool", "spa", "private_beach"],
    },
    {
        "hotel_name": "{dest} Executive Suites",
        "property_type": "serviced_apartment",
        "star_rating": 4,
        "area": "Business District",
        "km_to_center": 0.6,
        "km_to_transit": 0.3,
        "price_multiplier": 1.15,
        "includes_breakfast": False,
        "cancellation": "free_cancellation",
        "accessibility": ["elevator", "step_free_access"],
        "guest_rating": 8.5,
        "cleanliness_rating": 8.6,
        "safety_rating": 8.3,
        "amenities": ["workspace", "gym", "laundry"],
    },
    {
        "hotel_name": "{dest} Central Hotel",
        "property_type": "hotel",
        "star_rating": 3,
        "area": "City Centre",
        "km_to_center": 0.7,
        "km_to_transit": 0.4,
        "price_multiplier": 1.0,
        "includes_breakfast": True,
        "cancellation": "partial_refund",
        "accessibility": ["elevator"],
        "guest_rating": 7.8,
        "cleanliness_rating": 7.6,
        "safety_rating": 7.5,
        "amenities": ["restaurant", "bar"],
    },
    {
        "hotel_name": "{dest} Private Villa",
        "property_type": "villa",
        "star_rating": 4,
        "area": "Hillside",
        "km_to_center": 5.0,
        "km_to_transit": 4.0,
        "price_multiplier": 1.6,
        "includes_breakfast": False,
        "cancellation": "non_refundable",
        "accessibility": [],
        "guest_rating": 8.7,
        "cleanliness_rating": 8.5,
        "safety_rating": 7.7,
        "amenities": ["private_pool", "kitchen", "garden"],
    },
    {
        "hotel_name": "{dest} Guesthouse",
        "property_type": "guesthouse",
        "star_rating": 3,
        "area": "Local Quarter",
        "km_to_center": 1.2,
        "km_to_transit": 0.6,
        "price_multiplier": 0.55,
        "includes_breakfast": True,
        "cancellation": "free_cancellation",
        "accessibility": [],
        "guest_rating": 8.3,
        "cleanliness_rating": 8.0,
        "safety_rating": 7.6,
        "amenities": ["garden", "shared_lounge"],
    },
]


class MockAccommodationProvider:
    """
    Deterministic mock accommodation inventory — no external calls.

    Same interface a real provider would implement: search(destination,
    check_in_date, nights) -> list[dict] of raw, provider-shaped records.
    Swapping in Booking.com or Expedia later means implementing this method
    against their API and passing the instance to
    AccommodationIntelligence(provider=...) — nothing downstream changes.

    adults/children/rooms (T-039) are accepted for interface parity with
    DuffelStaysProvider — which needs them to build a real Duffel
    request — and deliberately ignored here: mock inventory has never
    varied by occupancy, and this task didn't ask for that to change.
    """

    def search(
        self,
        destination: str,
        check_in_date: str,
        nights: int,
        adults: int = 1,
        children: int = 0,
        rooms: int = 1,
    ) -> list[dict[str, Any]]:
        seed = sum(ord(c) for c in destination.lower()) or 1
        route_price_factor = 0.7 + (seed % 61) / 100

        candidates: list[dict[str, Any]] = []
        for i, tpl in enumerate(_TEMPLATES):
            nightly = _BASE_NIGHTLY_USD * tpl["price_multiplier"] * route_price_factor
            nightly = round(nightly / 5) * 5

            candidates.append({
                "hotel_name": tpl["hotel_name"].format(dest=destination),
                "property_type": tpl["property_type"],
                "star_rating": tpl["star_rating"],
                "area": tpl["area"],
                "km_to_center": tpl["km_to_center"],
                "km_to_transit": tpl["km_to_transit"],
                "price_per_night": nightly,
                "currency_code": "USD",
                "includes_breakfast": tpl["includes_breakfast"],
                "cancellation": tpl["cancellation"],
                "accessibility": tpl["accessibility"],
                "guest_rating": tpl["guest_rating"],
                "cleanliness_rating": tpl["cleanliness_rating"],
                "safety_rating": tpl["safety_rating"],
                "amenities": tpl["amenities"],
                "check_in_date": check_in_date,
                "nights": nights,
                "_template_index": i,
                "_destination": destination,
            })
        return candidates
