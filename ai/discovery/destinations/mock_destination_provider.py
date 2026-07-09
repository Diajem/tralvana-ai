from __future__ import annotations

from typing import Any

# City-level attributes shared by every entry within that city. Ratings are
# illustrative mock data for deterministic scoring demos — not real safety
# or travel advisories. Sprint 4+ replaces this with a live provider; see
# docs/DESTINATION_INTELLIGENCE_ENGINE.md.
_CITY_BASE: dict[str, dict[str, Any]] = {
    "Tokyo": {
        "country": "Japan", "region": "Asia",
        "safety_rating": 9.2, "budget_tier": "expensive", "transport_rating": 9.5,
        "food_scene_rating": 9.5, "culture_rating": 9.0, "football_reputation": 3.0,
        "peak_months": [3, 4, 10, 11],
    },
    "Osaka": {
        "country": "Japan", "region": "Asia",
        "safety_rating": 9.0, "budget_tier": "moderate", "transport_rating": 9.0,
        "food_scene_rating": 9.3, "culture_rating": 8.0, "football_reputation": 4.0,
        "peak_months": [3, 4, 10, 11],
    },
    "Barcelona": {
        "country": "Spain", "region": "Europe",
        "safety_rating": 7.5, "budget_tier": "moderate", "transport_rating": 8.5,
        "food_scene_rating": 8.5, "culture_rating": 8.5, "football_reputation": 9.5,
        "peak_months": [6, 7, 8],
    },
    "Paris": {
        "country": "France", "region": "Europe",
        "safety_rating": 7.3, "budget_tier": "expensive", "transport_rating": 8.5,
        "food_scene_rating": 9.0, "culture_rating": 9.5, "football_reputation": 8.0,
        "peak_months": [5, 6, 9],
    },
    "London": {
        "country": "United Kingdom", "region": "Europe",
        "safety_rating": 8.0, "budget_tier": "expensive", "transport_rating": 9.0,
        "food_scene_rating": 7.5, "culture_rating": 9.0, "football_reputation": 9.5,
        "peak_months": [6, 7, 8],
    },
    "New York": {
        "country": "United States", "region": "North America",
        "safety_rating": 7.0, "budget_tier": "expensive", "transport_rating": 8.0,
        "food_scene_rating": 8.8, "culture_rating": 8.5, "football_reputation": 4.0,
        "peak_months": [9, 10, 12],
    },
    "Lagos": {
        "country": "Nigeria", "region": "Africa",
        "safety_rating": 5.5, "budget_tier": "moderate", "transport_rating": 4.5,
        "food_scene_rating": 7.5, "culture_rating": 7.0, "football_reputation": 6.0,
        "peak_months": [11, 12, 1, 2, 3],
    },
    "Accra": {
        "country": "Ghana", "region": "Africa",
        "safety_rating": 7.0, "budget_tier": "budget", "transport_rating": 5.0,
        "food_scene_rating": 7.0, "culture_rating": 8.0, "football_reputation": 5.5,
        "peak_months": [11, 12, 1],
    },
    "Kingston": {
        "country": "Jamaica", "region": "Caribbean",
        "safety_rating": 6.0, "budget_tier": "moderate", "transport_rating": 4.0,
        "food_scene_rating": 7.5, "culture_rating": 8.5, "football_reputation": 3.0,
        "peak_months": [12, 1, 2, 3, 4],
    },
    "Dubai": {
        "country": "United Arab Emirates", "region": "Middle East",
        "safety_rating": 8.5, "budget_tier": "luxury", "transport_rating": 8.0,
        "food_scene_rating": 8.0, "culture_rating": 6.0, "football_reputation": 4.0,
        "peak_months": [11, 12, 1, 2, 3],
    },
}

# Raw, provider-shaped entries — one "city" overview plus a handful of
# representative places per city. destination_normalizer.py is the only
# place that translates place_type/tags into the canonical schema and
# objective scores.
_ENTRIES: list[dict[str, Any]] = [
    # --- Tokyo ---
    {"city": "Tokyo", "name": "Tokyo", "place_type": "city",
     "description": "Japan's ultra-modern capital blending neon-lit skyscrapers with centuries-old temples.",
     "tags": ["food", "culture", "shopping"], "distance_from_centre_km": 0, "popularity": 9,
     "best_for": ["first-time visitors", "food lovers", "city energy"]},
    {"city": "Tokyo", "name": "Shibuya", "place_type": "neighbourhood",
     "description": "Iconic scramble crossing, youth fashion, and buzzing nightlife.",
     "tags": ["nightlife", "shopping", "photography"], "distance_from_centre_km": 6, "popularity": 9,
     "best_for": ["nightlife", "shopping", "people-watching"]},
    {"city": "Tokyo", "name": "Tsukiji Outer Market", "place_type": "food_district",
     "description": "Fresh seafood stalls and street food institutions.",
     "tags": ["food", "market"], "distance_from_centre_km": 5, "popularity": 8,
     "best_for": ["fresh seafood", "street food", "early mornings"]},
    {"city": "Tokyo", "name": "Tokyo National Museum", "place_type": "museum",
     "description": "Japan's oldest and largest museum of art and antiquities.",
     "tags": ["culture", "history", "photography"], "distance_from_centre_km": 4, "popularity": 6,
     "best_for": ["art", "Japanese history"]},
    {"city": "Tokyo", "name": "Shinjuku Station", "place_type": "transport_hub",
     "description": "The world's busiest railway station, gateway to the whole city.",
     "tags": ["transport", "shopping"], "distance_from_centre_km": 5, "popularity": 5,
     "best_for": ["connections", "convenience"]},
    {"city": "Tokyo", "name": "Shinjuku Golden Gai", "place_type": "nightlife_area",
     "description": "Tiny alleyway bars packed into a handful of atmospheric blocks.",
     "tags": ["nightlife", "photography"], "distance_from_centre_km": 5, "popularity": 4,
     "best_for": ["intimate bars", "hidden gems"]},

    # --- Osaka ---
    {"city": "Osaka", "name": "Osaka", "place_type": "city",
     "description": "Japan's kitchen — bold street food, castle history, and a laid-back energy.",
     "tags": ["food", "culture"], "distance_from_centre_km": 0, "popularity": 7,
     "best_for": ["street food", "relaxed pace"]},
    {"city": "Osaka", "name": "Dotonbori", "place_type": "food_district",
     "description": "Neon canal-side street food strip famous for takoyaki and okonomiyaki.",
     "tags": ["food", "nightlife", "photography"], "distance_from_centre_km": 2, "popularity": 9,
     "best_for": ["street food", "neon photography"]},
    {"city": "Osaka", "name": "Osaka Castle", "place_type": "historic_site",
     "description": "Restored 16th-century castle set in a large park.",
     "tags": ["culture", "history", "photography"], "distance_from_centre_km": 3, "popularity": 7,
     "best_for": ["history", "cherry blossoms"]},
    {"city": "Osaka", "name": "Panasonic Stadium Suita", "place_type": "football_venue",
     "description": "Home of Gamba Osaka, a modern J-League stadium.",
     "tags": ["football", "sport"], "distance_from_centre_km": 12, "popularity": 4,
     "best_for": ["football fans"]},
    {"city": "Osaka", "name": "Shinsaibashi", "place_type": "shopping_district",
     "description": "Covered shopping arcade running through the city centre.",
     "tags": ["shopping"], "distance_from_centre_km": 2, "popularity": 6,
     "best_for": ["shopping"]},
    {"city": "Osaka", "name": "Namba", "place_type": "neighbourhood",
     "description": "Compact entertainment district next to Dotonbori.",
     "tags": ["nightlife", "food"], "distance_from_centre_km": 2, "popularity": 6,
     "best_for": ["nightlife", "food"]},

    # --- Barcelona ---
    {"city": "Barcelona", "name": "Barcelona", "place_type": "city",
     "description": "Gaudí architecture, Mediterranean beaches, and a football-mad culture.",
     "tags": ["culture", "football", "beach"], "distance_from_centre_km": 0, "popularity": 9,
     "best_for": ["football fans", "architecture", "beach + city combo"]},
    {"city": "Barcelona", "name": "Camp Nou", "place_type": "football_venue",
     "description": "FC Barcelona's legendary home ground and museum.",
     "tags": ["football", "sport"], "distance_from_centre_km": 4, "popularity": 9,
     "best_for": ["football fans"]},
    {"city": "Barcelona", "name": "Sagrada Família", "place_type": "historic_site",
     "description": "Gaudí's still-unfinished basilica masterpiece.",
     "tags": ["culture", "history", "photography"], "distance_from_centre_km": 3, "popularity": 10,
     "best_for": ["architecture", "photography"]},
    {"city": "Barcelona", "name": "Barceloneta", "place_type": "beach",
     "description": "City beach with seafood restaurants along the promenade.",
     "tags": ["beach", "food", "family"], "distance_from_centre_km": 2, "popularity": 7,
     "best_for": ["beach time", "families"]},
    {"city": "Barcelona", "name": "La Boqueria Market", "place_type": "food_district",
     "description": "Historic covered market just off Las Ramblas.",
     "tags": ["food", "market"], "distance_from_centre_km": 1, "popularity": 8,
     "best_for": ["tapas", "fresh produce"]},
    {"city": "Barcelona", "name": "Gothic Quarter", "place_type": "neighbourhood",
     "description": "Medieval maze of narrow streets and hidden plazas.",
     "tags": ["culture", "photography"], "distance_from_centre_km": 1, "popularity": 6,
     "best_for": ["wandering", "photography"]},

    # --- Paris ---
    {"city": "Paris", "name": "Paris", "place_type": "city",
     "description": "World capital of art, fashion, and gastronomy.",
     "tags": ["culture", "food"], "distance_from_centre_km": 0, "popularity": 10,
     "best_for": ["art lovers", "romance", "fine dining"]},
    {"city": "Paris", "name": "Louvre Museum", "place_type": "museum",
     "description": "The world's most visited museum, home to the Mona Lisa.",
     "tags": ["culture", "photography"], "distance_from_centre_km": 2, "popularity": 10,
     "best_for": ["art", "history"]},
    {"city": "Paris", "name": "Eiffel Tower", "place_type": "historic_site",
     "description": "The iconic 19th-century iron tower over the Seine.",
     "tags": ["culture", "photography", "family"], "distance_from_centre_km": 4, "popularity": 10,
     "best_for": ["photography", "families"]},
    {"city": "Paris", "name": "Le Marais", "place_type": "neighbourhood",
     "description": "Historic Jewish quarter turned trendy boutique district.",
     "tags": ["shopping", "food"], "distance_from_centre_km": 2, "popularity": 6,
     "best_for": ["boutique shopping", "cafés"]},
    {"city": "Paris", "name": "Rue Mouffetard", "place_type": "food_district",
     "description": "Cobblestone market street of cheese, wine, and bakeries.",
     "tags": ["food", "market"], "distance_from_centre_km": 3, "popularity": 5,
     "best_for": ["local food", "hidden gems"]},
    {"city": "Paris", "name": "Pigalle", "place_type": "nightlife_area",
     "description": "Historic cabaret and nightlife district near Montmartre.",
     "tags": ["nightlife"], "distance_from_centre_km": 4, "popularity": 6,
     "best_for": ["nightlife", "live music"]},

    # --- London ---
    {"city": "London", "name": "London", "place_type": "city",
     "description": "A global hub of history, football, and world-class museums.",
     "tags": ["culture", "football"], "distance_from_centre_km": 0, "popularity": 9,
     "best_for": ["football fans", "museums", "history"]},
    {"city": "London", "name": "Emirates Stadium", "place_type": "football_venue",
     "description": "Home of Arsenal FC, with matchday tours available.",
     "tags": ["football", "sport"], "distance_from_centre_km": 6, "popularity": 7,
     "best_for": ["football fans"]},
    {"city": "London", "name": "British Museum", "place_type": "museum",
     "description": "World history and antiquities under one roof, free entry.",
     "tags": ["culture", "family", "photography"], "distance_from_centre_km": 3, "popularity": 9,
     "best_for": ["families", "world history"]},
    {"city": "London", "name": "Notting Hill", "place_type": "neighbourhood",
     "description": "Pastel townhouses, Portobello Market, and quiet garden squares.",
     "tags": ["shopping", "photography"], "distance_from_centre_km": 6, "popularity": 6,
     "best_for": ["photography", "markets"]},
    {"city": "London", "name": "Borough Market", "place_type": "food_district",
     "description": "London's oldest food market, by London Bridge.",
     "tags": ["food", "market"], "distance_from_centre_km": 3, "popularity": 8,
     "best_for": ["food markets", "artisan produce"]},
    {"city": "London", "name": "King's Cross St Pancras", "place_type": "transport_hub",
     "description": "Major rail hub linking London to Europe and the north.",
     "tags": ["transport"], "distance_from_centre_km": 3, "popularity": 4,
     "best_for": ["connections"]},

    # --- New York ---
    {"city": "New York", "name": "New York", "place_type": "city",
     "description": "The city that never sleeps — culture, food, and skyline views.",
     "tags": ["culture", "food", "shopping"], "distance_from_centre_km": 0, "popularity": 10,
     "best_for": ["first-time visitors", "skyline views"]},
    {"city": "New York", "name": "Central Park", "place_type": "nature_area",
     "description": "843-acre green heart of Manhattan.",
     "tags": ["family", "photography"], "distance_from_centre_km": 0, "popularity": 9,
     "best_for": ["families", "outdoor time"]},
    {"city": "New York", "name": "MoMA", "place_type": "museum",
     "description": "Museum of Modern Art, a landmark of 20th-century art.",
     "tags": ["culture", "photography"], "distance_from_centre_km": 1, "popularity": 8,
     "best_for": ["modern art"]},
    {"city": "New York", "name": "Chelsea Market", "place_type": "food_district",
     "description": "Indoor food hall in a converted 19th-century factory.",
     "tags": ["food", "market"], "distance_from_centre_km": 3, "popularity": 7,
     "best_for": ["food halls"]},
    {"city": "New York", "name": "Fifth Avenue", "place_type": "shopping_district",
     "description": "Flagship stores and iconic Manhattan shopping.",
     "tags": ["shopping"], "distance_from_centre_km": 2, "popularity": 7,
     "best_for": ["shopping"]},
    {"city": "New York", "name": "Meatpacking District", "place_type": "nightlife_area",
     "description": "Former warehouse district turned nightlife and design hub.",
     "tags": ["nightlife"], "distance_from_centre_km": 3, "popularity": 5,
     "best_for": ["nightlife", "design"]},

    # --- Lagos ---
    {"city": "Lagos", "name": "Lagos", "place_type": "city",
     "description": "Nigeria's commercial powerhouse — beaches, Afrobeats, and buzzing markets.",
     "tags": ["culture", "football", "food"], "distance_from_centre_km": 0, "popularity": 6,
     "best_for": ["nightlife", "music culture", "diaspora travel"]},
    {"city": "Lagos", "name": "Lekki", "place_type": "neighbourhood",
     "description": "Modern waterfront district of malls, beaches, and nightlife.",
     "tags": ["shopping", "nightlife", "family"], "distance_from_centre_km": 15, "popularity": 6,
     "best_for": ["families", "shopping"]},
    {"city": "Lagos", "name": "Elegushi Beach", "place_type": "beach",
     "description": "Popular weekend beach with live music and beachside grills.",
     "tags": ["beach", "nightlife", "food"], "distance_from_centre_km": 18, "popularity": 5,
     "best_for": ["beach time", "live music"]},
    {"city": "Lagos", "name": "National Museum Lagos", "place_type": "historic_site",
     "description": "Nigerian art, artefacts, and independence history.",
     "tags": ["culture", "history"], "distance_from_centre_km": 3, "popularity": 3,
     "best_for": ["Nigerian history"]},
    {"city": "Lagos", "name": "Yaba Food Street", "place_type": "food_district",
     "description": "Local suya grills and street food stalls.",
     "tags": ["food"], "distance_from_centre_km": 8, "popularity": 3,
     "best_for": ["local food", "hidden gems"]},
    {"city": "Lagos", "name": "Victoria Island", "place_type": "nightlife_area",
     "description": "Business and nightlife district with rooftop bars.",
     "tags": ["nightlife", "shopping"], "distance_from_centre_km": 10, "popularity": 6,
     "best_for": ["nightlife", "business travel"]},

    # --- Accra ---
    {"city": "Accra", "name": "Accra", "place_type": "city",
     "description": "Ghana's welcoming capital and the heart of the Year of Return heritage movement.",
     "tags": ["culture", "heritage", "food"], "distance_from_centre_km": 0, "popularity": 6,
     "best_for": ["heritage travel", "diaspora travel"]},
    {"city": "Accra", "name": "Cape Coast Castle", "place_type": "historic_site",
     "description": "UNESCO former slave-trade fort, a major heritage pilgrimage site.",
     "tags": ["culture", "heritage", "history"], "distance_from_centre_km": 140, "popularity": 8,
     "best_for": ["heritage travel", "diaspora travel"]},
    {"city": "Accra", "name": "Labadi Beach", "place_type": "beach",
     "description": "Lively public beach with music, food stalls, and horseback rides.",
     "tags": ["beach", "nightlife", "family"], "distance_from_centre_km": 6, "popularity": 6,
     "best_for": ["families", "beach time"]},
    {"city": "Accra", "name": "Osu", "place_type": "neighbourhood",
     "description": "Buzzing strip of restaurants, bars, and craft markets.",
     "tags": ["food", "nightlife", "shopping"], "distance_from_centre_km": 4, "popularity": 5,
     "best_for": ["nightlife", "crafts"]},
    {"city": "Accra", "name": "Makola Market", "place_type": "shopping_district",
     "description": "Sprawling open-air market at the centre of Accra's trade.",
     "tags": ["shopping"], "distance_from_centre_km": 2, "popularity": 4,
     "best_for": ["local markets"]},
    {"city": "Accra", "name": "Osu Night Market", "place_type": "food_district",
     "description": "Street food stalls serving jollof, waakye, and grilled tilapia.",
     "tags": ["food"], "distance_from_centre_km": 4, "popularity": 3,
     "best_for": ["street food", "hidden gems"]},

    # --- Kingston ---
    {"city": "Kingston", "name": "Kingston", "place_type": "city",
     "description": "Jamaica's capital, birthplace of reggae and a living music heritage.",
     "tags": ["culture", "heritage"], "distance_from_centre_km": 0, "popularity": 5,
     "best_for": ["music heritage", "culture"]},
    {"city": "Kingston", "name": "Bob Marley Museum", "place_type": "historic_site",
     "description": "The reggae icon's former home, now a heritage museum.",
     "tags": ["culture", "heritage", "photography"], "distance_from_centre_km": 3, "popularity": 8,
     "best_for": ["music heritage", "photography"]},
    {"city": "Kingston", "name": "Hellshire Beach", "place_type": "beach",
     "description": "Fishing-village beach known for fried fish and festival.",
     "tags": ["beach", "food"], "distance_from_centre_km": 20, "popularity": 4,
     "best_for": ["local food", "hidden gems"]},
    {"city": "Kingston", "name": "New Kingston", "place_type": "neighbourhood",
     "description": "The city's business and hotel district.",
     "tags": ["shopping", "transport"], "distance_from_centre_km": 2, "popularity": 4,
     "best_for": ["convenience", "business travel"]},
    {"city": "Kingston", "name": "Uptown Kingston", "place_type": "nightlife_area",
     "description": "Live reggae and dancehall venues.",
     "tags": ["nightlife"], "distance_from_centre_km": 3, "popularity": 4,
     "best_for": ["live music", "nightlife"]},
    {"city": "Kingston", "name": "Papine Market", "place_type": "food_district",
     "description": "Local produce and jerk food stalls near the university.",
     "tags": ["food"], "distance_from_centre_km": 6, "popularity": 2,
     "best_for": ["local food", "hidden gems"]},

    # --- Dubai ---
    {"city": "Dubai", "name": "Dubai", "place_type": "city",
     "description": "Futuristic skyline, desert adventures, and luxury shopping.",
     "tags": ["shopping"], "distance_from_centre_km": 0, "popularity": 9,
     "best_for": ["luxury travel", "shopping", "skyline views"]},
    {"city": "Dubai", "name": "Burj Khalifa", "place_type": "attraction",
     "description": "World's tallest building with an observation deck.",
     "tags": ["photography", "family"], "distance_from_centre_km": 0, "popularity": 10,
     "best_for": ["photography", "families"]},
    {"city": "Dubai", "name": "Dubai Mall", "place_type": "shopping_district",
     "description": "One of the world's largest malls, beside the Burj Khalifa.",
     "tags": ["shopping", "family"], "distance_from_centre_km": 0, "popularity": 9,
     "best_for": ["shopping", "families"]},
    {"city": "Dubai", "name": "Jumeirah Beach", "place_type": "beach",
     "description": "White-sand public beach with skyline views.",
     "tags": ["beach", "family"], "distance_from_centre_km": 8, "popularity": 7,
     "best_for": ["families", "beach time"]},
    {"city": "Dubai", "name": "Al Fahidi Spice Souk", "place_type": "food_district",
     "description": "Historic trading district of spice and textile stalls.",
     "tags": ["food"], "distance_from_centre_km": 12, "popularity": 4,
     "best_for": ["local markets", "hidden gems"]},
    {"city": "Dubai", "name": "Downtown Dubai", "place_type": "neighbourhood",
     "description": "Fountain shows, high-rises, and waterfront promenades.",
     "tags": ["shopping", "photography"], "distance_from_centre_km": 1, "popularity": 7,
     "best_for": ["photography", "evening walks"]},
]


class MockDestinationProvider:
    """
    Deterministic mock destination catalogue — no external calls.

    Same interface a real provider would implement: search(city) -> list[dict].
    Swapping in Google Places or a similar provider later means implementing
    this method against their API and passing the instance to
    DestinationIntelligence(provider=...) — nothing downstream changes.

    Two modes, matching how travellers actually ask:
    - city given: returns the specific places *within* that city (neighbourhoods,
      food areas, attractions, ...) — "what should I do in Tokyo?"
    - city omitted: returns the top-level city overviews across the whole
      catalogue — "where should I go?"
    """

    def search(self, city: str | None = None) -> list[dict[str, Any]]:
        if city:
            matches = [
                e for e in _ENTRIES
                if e["city"].lower() == city.lower() and e["place_type"] != "city"
            ]
        else:
            matches = [e for e in _ENTRIES if e["place_type"] == "city"]

        return [self._with_city_base(e) for e in matches]

    def cities(self) -> list[str]:
        return sorted(_CITY_BASE.keys())

    def _with_city_base(self, entry: dict[str, Any]) -> dict[str, Any]:
        base = _CITY_BASE[entry["city"]]
        return {**entry, **base}
