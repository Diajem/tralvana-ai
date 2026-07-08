from __future__ import annotations

from typing import Any

# (theme_title, morning, afternoon, evening) per goal type
_TEMPLATES: dict[str, list[tuple[str, str, str, str]]] = {
    "FOOTBALL_TRAVEL": [
        ("Stadium & Football Heritage", "Stadium tour and team shop visit", "Football museum or fan gallery", "Pre-match pub dinner and fan culture"),
        ("Match Day Experience", "Fan zone, street food, and team colours", "Watch the match at the ground", "Post-match celebration dinner"),
        ("Football City Walk", "Historic terraces and stadium exterior walk", "Visit legendary fan pubs and football landmarks", "Sports bar dinner with live match screening"),
        ("Rest Day & City Exploration", "City centre sightseeing", "Local market or art district", "Traditional restaurant dinner"),
    ],
    "FOOD_TOUR": [
        ("Morning Market & Street Food", "Dawn visit to the main food market", "Street food tour and tasting", "Dinner at a renowned local restaurant"),
        ("Culinary Masterclass", "Cooking class with a local chef", "Market ingredient shopping", "Rooftop dinner with city views"),
        ("Wine, Cheese & Culture", "Winery or vineyard visit", "Artisan cheese and charcuterie tasting", "Fine dining restaurant — tasting menu"),
        ("Neighbourhood Food Walk", "Bakery and coffee district walk", "Hidden gem lunch spots", "Fusion restaurant exploring local-global flavours"),
    ],
    "RELAXATION": [
        ("Arrival & Unwinding", "Check in and resort orientation", "Pool or beach relaxation", "Sunset cocktails and light dinner"),
        ("Spa & Wellness Day", "Morning yoga or meditation session", "Full spa treatment (massage, sauna, pool)", "Healthy dinner and early night"),
        ("Scenic Leisure", "Guided nature walk or scenic boat trip", "Afternoon beach or pool time", "Dinner at a waterfront restaurant"),
        ("Cultural Afternoon", "Sleep in and leisurely breakfast", "Visit one local cultural attraction", "Relaxed evening at a rooftop bar"),
    ],
    "ADVENTURE": [
        ("Adrenaline Opening", "City orientation and gear check", "First adventure activity (hiking / surfing / zip-line)", "Campfire or energetic group dinner"),
        ("Wild Expedition", "Early start — full-day trail or safari", "Midpoint camp lunch", "Evening wildlife briefing and bush dinner"),
        ("Water Adventure", "Kayaking or white-water rafting", "Coastal lunch with sea views", "Seafood dinner with day debrief"),
        ("Urban Exploration", "City parkour or street art walking tour", "Escape room or team challenge", "Craft beer and burger dinner"),
    ],
    "FAMILY_TRIP": [
        ("Arrival & Kids' First Day", "Airport transfer and hotel check-in", "Hotel pool and kids' club", "Early family dinner with kids' menu"),
        ("Theme Park Day", "Full day at a theme park or family attraction", "On-site lunch and afternoon rides", "Early dinner and return to hotel"),
        ("City Discovery", "City tour suitable for families", "Interactive museum or science centre", "Casual family-friendly restaurant"),
        ("Leisure & Beach Day", "Beach morning (castles, swimming)", "Ice cream and waterfront walk", "BBQ or pizza dinner"),
    ],
    "BUSINESS_TRAVEL": [
        ("Arrival & Office Day", "Flight arrival and hotel check-in", "Afternoon meetings or conference", "Business dinner with colleagues"),
        ("Conference Day", "Keynote and morning sessions", "Networking lunch", "Evening industry drinks"),
        ("Site Visit", "Morning site tour or client presentation", "Working lunch", "Team dinner"),
        ("Debrief & Leisure", "Morning catch-up calls", "City exploration (1-2 hours)", "Farewell dinner before departure"),
    ],
    "PHOTOGRAPHY": [
        ("Golden Hour Opening", "Pre-dawn shoot at a landmark", "Edit and plan afternoon locations", "Blue-hour shoot at cityscape viewpoint"),
        ("Market & Street Photography", "Street market shoot at peak activity", "Post-processing session", "Night photography — light trails and neon"),
        ("Landscape Day", "Sunrise hike to a scenic overlook", "Rural or coastal landscape afternoon shoot", "Review and select best shots over dinner"),
        ("Portraits & Culture", "Portrait session at a local community space", "Cultural event or festival photography", "Workshop reflection dinner"),
    ],
    "PILGRIMAGE": [
        ("Sacred Arrival", "Arrival, prayer, and spiritual orientation", "Visit the main site of significance", "Quiet evening meal and reflection"),
        ("Deep Immersion", "Morning prayers or ritual at the holy site", "Guided spiritual walk", "Community meal with fellow pilgrims"),
        ("Heritage & History", "Visit historical religious sites", "Museum of faith and culture", "Evening service or ceremony"),
        ("Rest & Reflection", "Meditation or prayer morning", "Scenic walk in the spiritual landscape", "Final communal dinner"),
    ],
    "DIASPORA_TRAVEL": [
        ("Homecoming Arrival", "Arrival, family visit, and emotional reconnection", "Neighbourhood walk and memory trail", "Home-cooked family dinner"),
        ("Heritage Discovery", "Visit family ancestral village or town", "Local cultural landmarks and community centre", "Traditional meal in a heritage restaurant"),
        ("Cultural Reconnection", "Local market and artisan visit", "Meet community elders or cultural leaders", "Live music and cultural evening"),
        ("Modern vs Roots", "Contemporary city district exploration", "Tech hub or creative quarter visit", "Fusion dinner blending tradition and modernity"),
    ],
    "ROMANTIC_TRIP": [
        ("Romantic Arrival", "Airport transfer and boutique hotel check-in", "Couples spa or champagne welcome", "Candlelit dinner for two"),
        ("City of Love Day", "Morning stroll through the most scenic district", "Art gallery or private tour", "Sunset cruise or rooftop dinner"),
        ("Day Escape", "Scenic train or car trip to a nearby village", "Picnic lunch in the countryside", "Return for a cosy restaurant dinner"),
        ("Leisure & Intimacy", "Late breakfast in bed", "Shopping or local market exploration", "Chef's table or private dining experience"),
    ],
    "GENERAL_TRAVEL": [
        ("City Orientation", "Guided walking tour of the city centre", "Key landmarks and photo stops", "Welcome dinner at a celebrated local restaurant"),
        ("Culture & History", "Major museum or historical site", "Old town or heritage district walk", "Traditional local cuisine dinner"),
        ("Local Life", "Neighbourhood markets and cafes", "Day trip to a nearby attraction", "Local food street or night market dinner"),
        ("Leisure Day", "Relaxed morning, brunch, and local shops", "Park, viewpoint, or waterfront walk", "Farewell dinner at a rooftop restaurant"),
    ],
}

_ARRIVAL_DAY = ("Arrival & Orientation", "Fly to destination and hotel check-in", "Rest and explore the local area", "Welcome dinner at a nearby restaurant")
_DEPARTURE_DAY = ("Departure Day", "Leisurely final breakfast and packing", "Last sightseeing or souvenir shopping", "Transfer to airport")

_ACCOMMODATION_TIERS: dict[str, str] = {
    "backpacker": "hostel / budget guesthouse",
    "budget": "budget hotel (2-star)",
    "balanced": "mid-range hotel (3-4 star)",
    "comfort": "4-star hotel or boutique property",
    "luxury": "5-star hotel or luxury resort",
}

_DAILY_COSTS: dict[str, int] = {
    "backpacker": 40, "budget": 65, "balanced": 150,
    "comfort": 300, "luxury": 650,
}

# Destination-aware enrichment (knowledge graph cities → notable venues/activities)
_KG_ENRICHMENTS: dict[str, dict[str, list[str]]] = {
    "london": {
        "landmarks": ["Tower of London", "Buckingham Palace", "Hyde Park", "Borough Market"],
        "museums": ["British Museum", "National Gallery", "Tate Modern"],
        "restaurants": ["local gastro pubs", "Borough Market stalls", "West End brasseries"],
    },
    "paris": {
        "landmarks": ["Eiffel Tower", "Montmartre", "Champs-Elysees", "Sainte-Chapelle"],
        "museums": ["Louvre", "Musée d'Orsay", "Centre Pompidou"],
        "restaurants": ["Le Marais bistros", "Montmartre cafes", "Seine-side brasseries"],
    },
    "tokyo": {
        "landmarks": ["Shibuya Crossing", "Senso-ji Temple", "Shinjuku", "Tsukiji Outer Market"],
        "museums": ["Tokyo National Museum", "teamLab Borderless"],
        "restaurants": ["ramen shops", "izakayas", "sushi counters"],
    },
    "barcelona": {
        "landmarks": ["Sagrada Familia", "Park Guell", "Las Ramblas", "Gothic Quarter"],
        "museums": ["Picasso Museum", "Miro Foundation"],
        "restaurants": ["La Boqueria market", "tapas bars", "beachfront paella restaurants"],
    },
    "dubai": {
        "landmarks": ["Burj Khalifa", "Dubai Mall", "Gold Souk", "Desert Safari"],
        "museums": ["Dubai Museum", "Al Fahidi Fort"],
        "restaurants": ["rooftop restaurants", "spice souk cafes", "international dining"],
    },
    "rome": {
        "landmarks": ["Colosseum", "Vatican Museums", "Trevi Fountain", "Piazza Navona"],
        "museums": ["Vatican Museums", "Borghese Gallery", "Capitoline Museums"],
        "restaurants": ["Trastevere trattorias", "Campo de' Fiori markets", "gelato shops"],
    },
    "cape town": {
        "landmarks": ["Table Mountain", "V&A Waterfront", "Robben Island", "Boulders Beach"],
        "museums": ["District Six Museum", "Iziko South African Museum"],
        "restaurants": ["waterfront seafood", "wine farm restaurants", "Bo-Kaap cafes"],
    },
    "lagos": {
        "landmarks": ["Lekki Conservation Centre", "Nike Art Gallery", "Bar Beach", "National Museum"],
        "museums": ["National Museum Lagos", "Nike Art Gallery"],
        "restaurants": ["suya spots", "Ikoyi restaurants", "waterfront dining"],
    },
    "new york": {
        "landmarks": ["Central Park", "Brooklyn Bridge", "Times Square", "High Line"],
        "museums": ["Met Museum", "MoMA", "Natural History Museum"],
        "restaurants": ["NYC delis", "rooftop bars", "ethnic cuisine in Queens"],
    },
}


class ItineraryBuilder:
    """
    Builds a day-by-day itinerary using goal_type templates and optional
    knowledge graph destination data.

    Sprint 3+: integrate live activity APIs (Viator, GetYourGuide).
    """

    def build(
        self,
        destination: str,
        duration_days: int,
        goal_type: str,
        budget_style: str,
        interests: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        templates = _TEMPLATES.get(goal_type, _TEMPLATES["GENERAL_TRAVEL"])
        enrich = _KG_ENRICHMENTS.get(destination.lower(), {})
        accommodation = _ACCOMMODATION_TIERS.get(budget_style, _ACCOMMODATION_TIERS["balanced"])
        daily_cost = _DAILY_COSTS.get(budget_style, _DAILY_COSTS["balanced"])

        itinerary: list[dict[str, Any]] = []

        for day_num in range(1, duration_days + 1):
            if day_num == 1:
                theme = _ARRIVAL_DAY
            elif day_num == duration_days and duration_days > 1:
                theme = _DEPARTURE_DAY
            else:
                # Cycle through goal templates
                idx = (day_num - 2) % len(templates)
                theme = templates[idx]

            title, morning, afternoon, evening = theme

            # Enrich with knowledge graph data where applicable
            if enrich and day_num not in (1, duration_days):
                morning, afternoon, evening = self._enrich(
                    morning, afternoon, evening, day_num, enrich, goal_type
                )

            notes = ""
            if day_num == 1:
                notes = "Allow extra time for immigration and transfer — aim to arrive before evening."
            elif day_num == duration_days:
                notes = "Check airline requirements for check-in time."

            itinerary.append({
                "day": day_num,
                "title": f"Day {day_num}: {title}",
                "theme": title,
                "morning": morning,
                "afternoon": afternoon,
                "evening": evening,
                "accommodation": f"{accommodation.title()}, {destination}",
                "estimated_daily_cost_usd": daily_cost,
                "notes": notes,
            })

        return itinerary

    # ------------------------------------------------------------------

    def _enrich(
        self,
        morning: str,
        afternoon: str,
        evening: str,
        day: int,
        enrich: dict[str, list[str]],
        goal_type: str,
    ) -> tuple[str, str, str]:
        landmarks = enrich.get("landmarks", [])
        museums = enrich.get("museums", [])
        restaurants = enrich.get("restaurants", [])

        # Pick a landmark or museum for the day (rotate by day index)
        if museums and (goal_type in ("GENERAL_TRAVEL", "FAMILY_TRIP", "RELAXATION", "PHOTOGRAPHY")):
            pick = museums[(day - 2) % len(museums)]
            afternoon = f"Visit {pick}"

        if landmarks:
            pick = landmarks[(day - 2) % len(landmarks)]
            morning = f"Explore {pick}"

        if restaurants:
            pick = restaurants[(day - 2) % len(restaurants)]
            evening = f"Dinner at {pick}"

        return morning, afternoon, evening


itinerary_builder = ItineraryBuilder()
