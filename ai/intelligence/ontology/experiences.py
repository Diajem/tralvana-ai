"""Sport, attraction, museum, event, and local transport seed data."""

from ai.intelligence.knowledge.entities import (
    Attraction,
    Event,
    FootballClub,
    Museum,
    SportsVenue,
    Transport,
)
from ai.intelligence.ontology.seed_helpers import add_node as _n


def _sports_venues(g) -> None:
    for v in [
        SportsVenue(
            "venue_emirates",
            "Emirates Stadium",
            "city_london",
            "stadium",
            60704,
            "football",
        ),
        SportsVenue(
            "venue_stamford",
            "Stamford Bridge",
            "city_london",
            "stadium",
            40853,
            "football",
        ),
        SportsVenue(
            "venue_wembley",
            "Wembley Stadium",
            "city_london",
            "stadium",
            90000,
            "football",
        ),
        SportsVenue(
            "venue_parc_princes",
            "Parc des Princes",
            "city_paris",
            "stadium",
            48712,
            "football",
        ),
        SportsVenue(
            "venue_camp_nou", "Camp Nou", "city_barcelona", "stadium", 99354, "football"
        ),
        SportsVenue(
            "venue_olimpico",
            "Stadio Olimpico",
            "city_rome",
            "stadium",
            73261,
            "football",
        ),
        SportsVenue(
            "venue_san_siro", "San Siro", "city_rome", "stadium", 80018, "football"
        ),
        SportsVenue(
            "venue_ajinomoto",
            "Ajinomoto Stadium",
            "city_tokyo",
            "stadium",
            47851,
            "football",
        ),
    ]:
        _n(g, v, "SportsVenue")


def _football_clubs(g) -> None:
    for c in [
        FootballClub(
            "club_arsenal",
            "Arsenal FC",
            "city_london",
            "Premier League",
            "venue_emirates",
            1886,
        ),
        FootballClub(
            "club_chelsea",
            "Chelsea FC",
            "city_london",
            "Premier League",
            "venue_stamford",
            1905,
        ),
        FootballClub(
            "club_psg",
            "Paris Saint-Germain",
            "city_paris",
            "Ligue 1",
            "venue_parc_princes",
            1970,
        ),
        FootballClub(
            "club_barca",
            "FC Barcelona",
            "city_barcelona",
            "La Liga",
            "venue_camp_nou",
            1899,
        ),
        FootballClub(
            "club_roma", "AS Roma", "city_rome", "Serie A", "venue_olimpico", 1927
        ),
        FootballClub(
            "club_juve", "Juventus FC", "city_rome", "Serie A", "venue_olimpico", 1897
        ),
        FootballClub(
            "club_inter", "Inter Milan", "city_rome", "Serie A", "venue_san_siro", 1908
        ),
        FootballClub(
            "club_fc_tokyo",
            "FC Tokyo",
            "city_tokyo",
            "J1 League",
            "venue_ajinomoto",
            1999,
        ),
    ]:
        _n(g, c, "FootballClub")


def _attractions(g) -> None:
    for a in [
        Attraction(
            "attr_vi",
            "Victoria Island",
            "city_lagos",
            "entertainment",
            ["beach", "nightlife", "business"],
        ),
        Attraction(
            "attr_olumo", "Olumo Rock", "city_abuja", "natural", ["historic", "nature"]
        ),
        Attraction(
            "attr_tower",
            "Tower of London",
            "city_london",
            "historic",
            ["history", "culture"],
        ),
        Attraction(
            "attr_wembley",
            "Wembley Stadium",
            "city_london",
            "sport",
            ["football", "sport", "music"],
        ),
        Attraction(
            "attr_eiffel",
            "Eiffel Tower",
            "city_paris",
            "landmark",
            ["iconic", "romantic"],
        ),
        Attraction(
            "attr_louvre_at",
            "Louvre Gardens",
            "city_paris",
            "cultural",
            ["art", "culture"],
        ),
        Attraction(
            "attr_burj",
            "Burj Khalifa",
            "city_dubai",
            "landmark",
            ["modern", "views", "luxury"],
        ),
        Attraction(
            "attr_palm", "Palm Jumeirah", "city_dubai", "natural", ["beach", "luxury"]
        ),
        Attraction(
            "attr_empire",
            "Empire State Building",
            "city_new_york",
            "landmark",
            ["views", "iconic"],
        ),
        Attraction(
            "attr_central",
            "Central Park",
            "city_new_york",
            "natural",
            ["nature", "running", "cycling"],
        ),
        Attraction(
            "attr_colosseum",
            "Colosseum",
            "city_rome",
            "historic",
            ["history", "ancient", "culture"],
        ),
        Attraction(
            "attr_sagrada",
            "Sagrada Família",
            "city_barcelona",
            "cultural",
            ["art", "architecture", "religious"],
        ),
        Attraction(
            "attr_senso",
            "Senso-ji Temple",
            "city_tokyo",
            "religious",
            ["culture", "historic", "photography"],
        ),
        Attraction(
            "attr_kakum",
            "Kakum National Park",
            "city_accra",
            "natural",
            ["nature", "adventure", "wildlife"],
        ),
        Attraction(
            "attr_tafelberg",
            "Table Mountain",
            "city_cape_town",
            "natural",
            ["nature", "hiking", "views"],
        ),
    ]:
        _n(g, a, "Attraction")


def _museums(g) -> None:
    for m in [
        Museum(
            "museum_british",
            "British Museum",
            "city_london",
            "history",
            ["ancient", "world", "free"],
        ),
        Museum(
            "museum_tate", "Tate Modern", "city_london", "art", ["modern-art", "free"]
        ),
        Museum(
            "museum_louvre", "Louvre", "city_paris", "art", ["renaissance", "mona-lisa"]
        ),
        Museum(
            "museum_orsay",
            "Musée d'Orsay",
            "city_paris",
            "art",
            ["impressionism", "van-gogh"],
        ),
        Museum(
            "museum_vatican",
            "Vatican Museums",
            "city_rome",
            "art",
            ["sistine-chapel", "renaissance", "religious"],
        ),
        Museum(
            "museum_prado",
            "Prado Museum",
            "city_barcelona",
            "art",
            ["spanish-masters", "goya"],
        ),
        Museum(
            "museum_met",
            "Metropolitan Museum of Art",
            "city_new_york",
            "art",
            ["world-class", "ancient"],
        ),
        Museum(
            "museum_ghana_nat",
            "National Museum of Ghana",
            "city_accra",
            "history",
            ["african-history", "culture"],
        ),
        Museum(
            "museum_tokyo_nat",
            "Tokyo National Museum",
            "city_tokyo",
            "history",
            ["japanese-art", "samurai"],
        ),
        Museum(
            "museum_iziko",
            "Iziko South African Museum",
            "city_cape_town",
            "natural",
            ["natural-history", "african"],
        ),
    ]:
        _n(g, m, "Museum")


def _events(g) -> None:
    for e in [
        Event(
            "evt_afrobeats",
            "Lagos Afrobeats Festival",
            "city_lagos",
            "festival",
            12,
            ["music", "culture", "nightlife"],
        ),
        Event(
            "evt_notting",
            "Notting Hill Carnival",
            "city_london",
            "festival",
            8,
            ["music", "culture", "carnival"],
        ),
        Event(
            "evt_fashion",
            "Paris Fashion Week",
            "city_paris",
            "exhibition",
            10,
            ["fashion", "luxury"],
        ),
        Event(
            "evt_expo_dxb",
            "Dubai Expo City",
            "city_dubai",
            "exhibition",
            10,
            ["technology", "culture", "business"],
        ),
        Event(
            "evt_marathon",
            "NYC Marathon",
            "city_new_york",
            "sport",
            11,
            ["sport", "running"],
        ),
        Event(
            "evt_tomato",
            "La Tomatina",
            "city_barcelona",
            "festival",
            8,
            ["culture", "fun"],
        ),
        Event(
            "evt_cherry",
            "Hanami Cherry Blossom Festival",
            "city_tokyo",
            "festival",
            4,
            ["nature", "culture", "photography"],
        ),
        Event(
            "evt_panafest",
            "PANAFEST",
            "city_accra",
            "cultural",
            7,
            ["african-heritage", "culture", "diaspora"],
        ),
    ]:
        _n(g, e, "Event")


def _transport(g) -> None:
    for t in [
        Transport("trans_tube", "London Underground", "metro", "city_london"),
        Transport("trans_rer", "Paris RER", "rail", "city_paris"),
        Transport("trans_metro_dxb", "Dubai Metro", "metro", "city_dubai"),
        Transport("trans_subway_ny", "New York Subway", "metro", "city_new_york"),
        Transport("trans_metro_bcn", "Barcelona Metro", "metro", "city_barcelona"),
        Transport(
            "trans_shinkansen", "Shinkansen (Bullet Train)", "rail", "city_tokyo"
        ),
    ]:
        _n(g, t, "Transport")
