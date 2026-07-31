from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ai.intelligence.knowledge.relationships import RelationshipType

if TYPE_CHECKING:
    from ai.intelligence.knowledge.knowledge_service import KnowledgeService

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
        ("Gentle Start & Local Discovery", "Leisurely breakfast and an easy neighbourhood walk", "Relax at a café, park, or quiet local attraction", "Unhurried dinner at a well-reviewed local restaurant"),
        ("Spa & Wellness Day", "Morning yoga or meditation session", "Full spa treatment (massage, sauna, pool)", "Healthy dinner and early night"),
        ("Scenic Leisure", "Guided green-space, riverside, or coastal walk where locally suitable", "Afternoon tea, gallery visit, or relaxed scenic tour", "Dinner in a calm neighbourhood restaurant"),
        ("Cultural Afternoon", "Sleep in and enjoy a leisurely breakfast", "Visit one local cultural attraction", "Relaxed evening at a local music venue, theatre, or traditional pub"),
        ("Gardens & Green Spaces", "Slow morning in a major garden or city park", "Picnic or relaxed lunch followed by free time", "Cosy dinner close to the accommodation"),
        ("Local Stories at an Easy Pace", "Guided literary, heritage, or neighbourhood walk", "Coffee break and a small museum or gallery", "Early evening performance or quiet dinner"),
        ("Scenic Day Excursion", "Unhurried train or coach trip to a nearby scenic area", "Explore the destination at a comfortable pace", "Return for a simple local dinner"),
        ("Food & Craft Discovery", "Browse a local food or craft market", "Tasting, workshop, or artisan visit", "Relaxed meal featuring regional cuisine"),
        ("History Without the Rush", "Visit one major historic site with plenty of time", "Long lunch and a gentle old-town walk", "Free evening or neighbourhood restaurant"),
        ("Waterfront or Riverside Day", "Easy walk beside the river, canal, lake, or coast where available", "Scenic cruise or waterside café if locally suitable", "Dinner near a lively but comfortable district"),
        ("Independent Slow Day", "Late breakfast and a flexible morning", "Choose a favourite attraction or return to a preferred neighbourhood", "Book a special dinner or relaxed cultural evening"),
        ("Final Full-Day Highlights", "Visit one remaining priority attraction", "Souvenir shopping and a leisurely lunch", "Farewell dinner celebrating the trip"),
    ],
    "ADVENTURE": [
        ("Adrenaline Opening", "City orientation and gear check", "First adventure activity (hiking / surfing / zip-line)", "Campfire or energetic group dinner"),
        ("Wild Expedition", "Early start — full-day trail or safari", "Midpoint camp lunch", "Evening wildlife briefing and bush dinner"),
        ("Water Adventure", "Kayaking or white-water rafting", "Coastal lunch with sea views", "Seafood dinner with day debrief"),
        ("Urban Exploration", "City parkour or street art walking tour", "Escape room or team challenge", "Craft beer and burger dinner"),
    ],
    "FAMILY_TRIP": [
        ("Family-Friendly City Introduction", "Easy-paced city orientation with regular breaks", "Interactive local attraction suitable for the children's ages", "Early family dinner near the accommodation"),
        ("Hands-On Discovery", "Interactive museum, science centre, or discovery space", "Park, playground, or family workshop", "Casual family-friendly restaurant"),
        ("Stories & Heritage", "Child-friendly historical or cultural tour", "Creative activity connected to the destination", "Relaxed dinner and an early evening"),
        ("Animals & Nature", "Zoo, aquarium, wildlife centre, or nature reserve where locally available", "Outdoor play and a relaxed lunch", "Simple family dinner"),
        ("Family Day Excursion", "Short train or coach trip to a nearby family-suitable place", "Explore at an unhurried pace", "Return for dinner near the accommodation"),
        ("Markets & Local Flavours", "Browse a local market together", "Food tasting or child-friendly cooking activity", "Choose a regional dish at a family restaurant"),
        ("Green Spaces Day", "Visit a major park, garden, or riverside path", "Picnic, playground, or gentle outdoor activity", "Early dinner and free evening"),
        ("Creative City Day", "Art, music, or storytelling activity for families", "Visit a colourful neighbourhood or small gallery", "Family meal followed by a short evening walk"),
        ("Transport & Engineering", "Explore a transport, technology, or engineering attraction", "Scenic public-transport journey through the city", "Casual dinner in a well-connected district"),
        ("Choose-Your-Favourite Day", "Return to a favourite area or attraction", "Flexible family time with rest built in", "Special dinner chosen together"),
        ("Final Priority Attraction", "Visit the family's remaining must-see place", "Souvenir shopping and a leisurely lunch", "Relaxed farewell evening"),
        ("Family Celebration Day", "Slow breakfast and photo stops", "One final age-appropriate experience", "Farewell dinner celebrating the trip"),
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
        ("Art & Design", "Visit a major gallery or design district", "Explore independent studios and local architecture", "Dinner in a creative neighbourhood"),
        ("Green City", "Walk through a major park or garden", "Visit a waterfront, river, or scenic viewpoint where locally suitable", "Relaxed neighbourhood dinner"),
        ("Food & Markets", "Browse a local produce or craft market", "Join a food-focused walk or tasting", "Try a regional speciality"),
        ("Neighbourhood Day", "Explore a residential district beyond the main tourist centre", "Independent shops, cafés, and community spaces", "Dinner where local residents eat"),
        ("Day Excursion", "Take a short train or coach trip to a nearby place", "Explore its main cultural and scenic highlights", "Return for a simple dinner near the accommodation"),
        ("Modern City", "Visit a technology, transport, or contemporary culture attraction", "Explore a modern commercial district", "Evening skyline or city-lights walk"),
        ("Flexible Priority Day", "Visit one remaining priority attraction", "Leave time for shopping, rest, or a booked activity", "Special dinner chosen by the traveller"),
        ("Final Full Day", "Return to a favourite district or visit a final museum", "Souvenir shopping and an unhurried lunch", "Farewell dinner"),
    ],
}

_TOKYO_TEMPLATES = [
    ("Asakusa & Old Tokyo", "Explore Senso-ji and Nakamise-dori", "Walk beside the Sumida River and visit nearby traditional streets", "Dinner in Asakusa"),
    ("Ueno Museums & Park", "Walk through Ueno Park", "Choose a museum in the Ueno cultural district", "Explore Ameya-Yokocho and dine nearby"),
    ("Meiji, Harajuku & Omotesando", "Visit Meiji Shrine", "Explore Harajuku and Omotesando", "Dinner around Aoyama or Shibuya"),
    ("Shibuya", "Explore Shibuya Crossing and surrounding streets", "Visit shops, galleries, or a city viewpoint", "Dinner and an evening walk in Shibuya"),
    ("Tsukiji & Ginza", "Breakfast or food exploration at Tsukiji Outer Market", "Explore Ginza's architecture, shops, and galleries", "Dinner in central Tokyo"),
    ("Shinjuku", "Visit Shinjuku Gyoen or a nearby cultural attraction", "Explore the west-side skyline and department stores", "Evening in Shinjuku"),
    ("Odaiba & Tokyo Bay", "Travel to the Tokyo Bay area", "Explore Odaiba's museums, waterfront, or digital-art attractions", "Return for dinner near the accommodation"),
    ("Kamakura Day Excursion", "Travel to Kamakura", "Explore temples, historic streets, and the coast", "Return to Tokyo for dinner"),
    ("Yanaka & Nezu", "Walk through Yanaka's traditional streets", "Explore Nezu, small galleries, and local cafés", "Quiet neighbourhood dinner"),
    ("Independent Tokyo Day", "Choose a priority attraction not yet visited", "Allow time for shopping or a pre-booked experience", "Special final-evening meal"),
    ("Mount Takao or Western Tokyo", "Take a day trip to Mount Takao or another western Tokyo area", "Enjoy a scenic walk suited to current conditions", "Return for a relaxed dinner"),
    ("Contemporary Tokyo", "Explore a contemporary art or architecture district", "Visit independent shops and design spaces", "Evening city-lights walk"),
]

_DESTINATION_TEMPLATES = {"tokyo": _TOKYO_TEMPLATES}

_ARRIVAL_DAY = ("Arrival & Orientation", "Arrive, transfer, and check in to the selected accommodation", "Rest and explore the local area", "Welcome dinner at a nearby restaurant")
_DEPARTURE_DAY = ("Departure Day", "Leisurely final breakfast and packing", "Last sightseeing or souvenir shopping", "Transfer to airport")

class ItineraryBuilder:
    """
    Builds a day-by-day itinerary using goal_type templates and optional
    knowledge graph destination data.

    Knowledge-graph enrichment is resolved at build time so runtime graph
    changes are reflected immediately. Sprint 3+: integrate live activity
    APIs (Viator, GetYourGuide).
    """

    def __init__(self, knowledge_service: KnowledgeService | None = None) -> None:
        if knowledge_service is not None:
            self._knowledge_service = knowledge_service
        else:
            # Lazy import avoids coupling module import order to graph seeding.
            from ai.intelligence import knowledge_service as default_knowledge_service

            self._knowledge_service = default_knowledge_service

    def build(
        self,
        destination: str,
        duration_days: int,
        goal_type: str,
        budget_style: str,
        interests: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        templates = (
            _DESTINATION_TEMPLATES.get(destination.strip().casefold())
            if goal_type == "GENERAL_TRAVEL"
            else None
        ) or _TEMPLATES.get(goal_type, _TEMPLATES["GENERAL_TRAVEL"])
        enrich = self._destination_enrichment(destination)
        itinerary: list[dict[str, Any]] = []

        for day_num in range(1, duration_days + 1):
            if day_num == 1:
                theme = _ARRIVAL_DAY
            elif day_num == duration_days and duration_days > 1:
                theme = _DEPARTURE_DAY
            else:
                idx = day_num - 2
                theme = (
                    templates[idx]
                    if idx < len(templates)
                    else _TEMPLATES["GENERAL_TRAVEL"][
                        idx % len(_TEMPLATES["GENERAL_TRAVEL"])
                    ]
                )

            title, morning, afternoon, evening = theme

            # Enrich with knowledge graph data where applicable
            if enrich and day_num not in (1, duration_days):
                morning, afternoon, evening = self._enrich(
                    morning, afternoon, evening, day_num, enrich, goal_type
                )

            if interests and day_num not in (1, duration_days):
                morning, afternoon, evening = self._apply_interest(
                    morning, afternoon, evening, day_num, destination, interests
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
                "accommodation": f"Accommodation to be confirmed in {destination}",
                "notes": notes,
            })

        return itinerary

    # ------------------------------------------------------------------

    def _destination_enrichment(self, destination: str) -> dict[str, list[str]]:
        """Load current destination venues from the shared knowledge graph."""
        city = self._knowledge_service.find_entity("City", destination.strip())
        if city is None:
            return {}

        queries = {
            "landmarks": ("Attraction", RelationshipType.NEAR),
            "museums": ("Museum", RelationshipType.LOCATED_IN),
            "restaurants": ("Restaurant", RelationshipType.BELONGS_TO),
        }
        enrich: dict[str, list[str]] = {}
        for key, (entity_type, relationship_type) in queries.items():
            entities = self._knowledge_service.get_connected_entities(
                city.id,
                entity_type,
                relationship_type,
                "inbound",
            )
            names = {
                str(entity.name).strip()
                for entity in entities
                if str(getattr(entity, "name", "")).strip()
            }
            if names:
                enrich[key] = sorted(names, key=str.casefold)
        return enrich

    def _apply_interest(
        self,
        morning: str,
        afternoon: str,
        evening: str,
        day: int,
        destination: str,
        interests: list[str],
    ) -> tuple[str, str, str]:
        """Carry explicitly requested interests into the daily plan.

        This is deliberately lightweight until a live events provider is
        connected: it schedules a relevant activity and tells the traveller
        to confirm date-specific fixtures/events rather than inventing one.
        """
        interest_index = day - 2
        if interest_index >= len(interests):
            return morning, afternoon, evening
        interest = interests[interest_index].lower()
        if any(term in interest for term in ("fashion", "style")):
            afternoon = (
                "Explore the fashion district or a fashion exhibition; "
                "check current event listings for the travel date"
            )
        elif any(term in interest for term in ("soccer", "football")):
            afternoon = (
                f"Stadium visit or local soccer experience; confirm the {destination} "
                "fixture calendar before booking"
            )
        elif any(term in interest for term in ("dining", "dine", "food", "restaurant")):
            evening = "Dine out at a well-reviewed local restaurant"
        elif any(
            term in interest
            for term in ("attraction", "landmark", "significant interest", "sightseeing")
        ):
            morning = "Visit a major place of historical or cultural significance"

        return morning, afternoon, evening

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
        enrichment_index = day - 2
        if museums and enrichment_index < len(museums) and (
            goal_type in ("GENERAL_TRAVEL", "FAMILY_TRIP", "RELAXATION", "PHOTOGRAPHY")
        ):
            pick = museums[enrichment_index]
            afternoon = f"Visit {pick}"

        if landmarks and enrichment_index < len(landmarks):
            pick = landmarks[enrichment_index]
            morning = f"Explore {pick}"

        if restaurants and enrichment_index < len(restaurants):
            pick = restaurants[enrichment_index]
            evening = f"Dinner at {pick}"

        return morning, afternoon, evening


itinerary_builder = ItineraryBuilder()
