from __future__ import annotations

from enum import Enum


class DNAType(str, Enum):
    EXPLORER = "Explorer"
    LUXURY_TRAVELLER = "Luxury Traveller"
    BUDGET_TRAVELLER = "Budget Traveller"
    FOOTBALL_TRAVELLER = "Football Traveller"
    FOOD_TRAVELLER = "Food Traveller"
    PHOTOGRAPHY_TRAVELLER = "Photography Traveller"
    FAMILY_TRAVELLER = "Family Traveller"
    BUSINESS_TRAVELLER = "Business Traveller"
    ADVENTURE_TRAVELLER = "Adventure Traveller"
    DIGITAL_NOMAD = "Digital Nomad"
    PILGRIMAGE_TRAVELLER = "Pilgrimage Traveller"
    DIASPORA_TRAVELLER = "Diaspora Traveller"


# Ordered list of traits used in scoring.
# Each trait is a 0.0–1.0 score derived deterministically from TIP profile fields.
TRAITS: list[str] = [
    "adventure_seeking",       # adventure, nature, sport interests
    "luxury_orientation",      # first/business cabin, luxury budget, luxury interests
    "budget_consciousness",    # backpacker/budget style, hostel accommodation
    "cultural_curiosity",      # culture, history interests; breadth of interests
    "food_focus",              # food_drink interests, dietary requirements
    "sport_focus",             # sport interests
    "business_orientation",    # business cabin, business interests, airline loyalty
    "family_orientation",      # resort accommodation, beach/wellness interests
    "digital_mobility",        # city interests, apartment accommodation, balanced budget
    "photography_tendency",    # nature/culture/city interests (proxy signal)
    "spiritual_orientation",   # religious, pilgrimage, spiritual interests
    "heritage_connection",     # heritage, diaspora, roots, family interests
]


# Human-readable descriptions for each DNA type (used in docs / responses)
DNA_DESCRIPTIONS: dict[str, str] = {
    DNAType.EXPLORER: (
        "Curious and wide-ranging traveller who seeks new destinations and diverse experiences."
    ),
    DNAType.LUXURY_TRAVELLER: (
        "Prioritises premium comfort — five-star hotels, business/first class, and exclusive experiences."
    ),
    DNAType.BUDGET_TRAVELLER: (
        "Maximises destination count over creature comforts; hostel stays, budget airlines, free activities."
    ),
    DNAType.FOOTBALL_TRAVELLER: (
        "Plans trips around live football matches, stadium tours, and sports events."
    ),
    DNAType.FOOD_TRAVELLER: (
        "Uses cuisine as the primary lens for destination choice — food tours, Michelin restaurants, markets."
    ),
    DNAType.PHOTOGRAPHY_TRAVELLER: (
        "Frames every trip as a visual story — golden-hour spots, iconic backdrops, local faces."
    ),
    DNAType.FAMILY_TRAVELLER: (
        "Optimises for all ages — resort stays, child-friendly venues, low-risk itineraries."
    ),
    DNAType.BUSINESS_TRAVELLER: (
        "Travels for work; values efficiency, lounge access, city-centre hotels, reliable Wi-Fi."
    ),
    DNAType.ADVENTURE_TRAVELLER: (
        "Seeks adrenaline — trekking, diving, climbing, safaris, and off-the-beaten-path routes."
    ),
    DNAType.DIGITAL_NOMAD: (
        "Combines remote work with slow travel; apartment stays, co-working spaces, monthly rentals."
    ),
    DNAType.PILGRIMAGE_TRAVELLER: (
        "Motivated by faith or spirituality — religious sites, sacred journeys, holy cities."
    ),
    DNAType.DIASPORA_TRAVELLER: (
        "Travels to reconnect with cultural roots, heritage, or family in an ancestral homeland."
    ),
}
