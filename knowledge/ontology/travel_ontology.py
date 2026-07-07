"""
Seed data for the TravelOS Knowledge Graph.

Covers 8 countries, 10 cities, 10 airports, 6 airlines, 16 hotels,
12 attractions, 8 museums, 8 restaurants, 8 football clubs, 8 events,
6 transport systems, 12 visa rules, and weather profiles.
"""

from __future__ import annotations

from knowledge.graph.entities import (
    Airport, Airline, Attraction, City, Country, Currency,
    Event, FootballClub, Hotel, Museum, Restaurant,
    Transport, VisaRequirement, Weather,
)
from knowledge.graph.relationships import Relationship, RelationshipType


def seed_graph(g: object) -> None:
    _currencies(g)
    _countries(g)
    _cities(g)
    _airports(g)
    _airlines(g)
    _hotels(g)
    _attractions(g)
    _museums(g)
    _restaurants(g)
    _football_clubs(g)
    _events(g)
    _transport(g)
    _visa_requirements(g)
    _weather(g)
    _relationships(g)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _n(g, entity, entity_type: str) -> None:
    g.add_node(entity, entity_type)


def _e(
    g, src_id: str, src_type: str,
    rel: RelationshipType,
    tgt_id: str, tgt_type: str,
    weight: float = 1.0, **meta,
) -> None:
    g.add_edge(Relationship(src_id, src_type, rel, tgt_id, tgt_type, weight, meta))


R = RelationshipType


# ---------------------------------------------------------------------------
# Currencies
# ---------------------------------------------------------------------------

def _currencies(g) -> None:
    data = [
        Currency("cur_ngn", "NGN", "Nigerian Naira",    "₦", ["NG"]),
        Currency("cur_gbp", "GBP", "British Pound",     "£", ["GB"]),
        Currency("cur_eur", "EUR", "Euro",              "€", ["FR", "IT", "ES", "NL", "DE"]),
        Currency("cur_aed", "AED", "UAE Dirham",        "د.إ", ["AE"]),
        Currency("cur_usd", "USD", "US Dollar",         "$", ["US"]),
        Currency("cur_jpy", "JPY", "Japanese Yen",      "¥", ["JP"]),
        Currency("cur_ghc", "GHS", "Ghanaian Cedi",     "₵", ["GH"]),
        Currency("cur_zar", "ZAR", "South African Rand","R", ["ZA"]),
    ]
    for c in data:
        _n(g, c, "Currency")


# ---------------------------------------------------------------------------
# Countries
# ---------------------------------------------------------------------------

def _countries(g) -> None:
    data = [
        Country("country_ng", "Nigeria",       "NG", "Africa",  "city_lagos",    ["en"],          "NGN", "medium"),
        Country("country_gb", "United Kingdom","GB", "Europe",  "city_london",   ["en"],          "GBP", "low"),
        Country("country_fr", "France",        "FR", "Europe",  "city_paris",    ["fr"],          "EUR", "low"),
        Country("country_ae", "UAE",           "AE", "Asia",    "city_dubai",    ["ar", "en"],    "AED", "low"),
        Country("country_us", "United States", "US", "Americas","city_new_york", ["en"],          "USD", "low"),
        Country("country_it", "Italy",         "IT", "Europe",  "city_rome",     ["it"],          "EUR", "low"),
        Country("country_es", "Spain",         "ES", "Europe",  "city_barcelona",["es"],          "EUR", "low"),
        Country("country_jp", "Japan",         "JP", "Asia",    "city_tokyo",    ["ja"],          "JPY", "low"),
        Country("country_gh", "Ghana",         "GH", "Africa",  "city_accra",    ["en"],          "GHS", "low"),
        Country("country_za", "South Africa",  "ZA", "Africa",  "city_cape_town",["en", "af", "zu"], "ZAR", "medium"),
    ]
    for c in data:
        _n(g, c, "Country")


# ---------------------------------------------------------------------------
# Cities
# ---------------------------------------------------------------------------

def _cities(g) -> None:
    data = [
        City("city_lagos",     "Lagos",     "country_ng", "Africa/Lagos",    15000000, ["coastal", "urban", "business", "nightlife"]),
        City("city_abuja",     "Abuja",     "country_ng", "Africa/Lagos",     3600000, ["urban", "business", "historic"]),
        City("city_london",    "London",    "country_gb", "Europe/London",   9000000, ["urban", "historic", "cultural", "business"]),
        City("city_paris",     "Paris",     "country_fr", "Europe/Paris",    2100000, ["romantic", "cultural", "fashion", "food"]),
        City("city_dubai",     "Dubai",     "country_ae", "Asia/Dubai",      3300000, ["luxury", "urban", "beach", "modern"]),
        City("city_new_york",  "New York",  "country_us", "America/New_York",8300000, ["urban", "cultural", "business", "food"]),
        City("city_rome",      "Rome",      "country_it", "Europe/Rome",     2800000, ["historic", "cultural", "food", "art"]),
        City("city_barcelona", "Barcelona", "country_es", "Europe/Madrid",   1600000, ["beach", "urban", "food", "nightlife", "sport"]),
        City("city_tokyo",     "Tokyo",     "country_jp", "Asia/Tokyo",     14000000, ["urban", "technology", "food", "cultural"]),
        City("city_accra",     "Accra",     "country_gh", "Africa/Accra",    2300000, ["coastal", "urban", "business", "cultural"]),
        City("city_cape_town", "Cape Town", "country_za", "Africa/Johannesburg",4600000, ["coastal", "nature", "beach", "mountain"]),
    ]
    for c in data:
        _n(g, c, "City")


# ---------------------------------------------------------------------------
# Airports
# ---------------------------------------------------------------------------

def _airports(g) -> None:
    data = [
        Airport("airport_los", "Murtala Muhammed International", "LOS", "city_lagos",     True),
        Airport("airport_abv", "Nnamdi Azikiwe International",   "ABV", "city_abuja",     True),
        Airport("airport_lhr", "Heathrow",                        "LHR", "city_london",   True),
        Airport("airport_cdg", "Charles de Gaulle",               "CDG", "city_paris",    True),
        Airport("airport_dxb", "Dubai International",             "DXB", "city_dubai",    True),
        Airport("airport_jfk", "John F. Kennedy International",   "JFK", "city_new_york", True),
        Airport("airport_fco", "Leonardo da Vinci (Fiumicino)",   "FCO", "city_rome",     True),
        Airport("airport_bcn", "El Prat",                         "BCN", "city_barcelona",True),
        Airport("airport_nrt", "Narita International",            "NRT", "city_tokyo",    True),
        Airport("airport_acc", "Kotoka International",            "ACC", "city_accra",    True),
        Airport("airport_cpt", "Cape Town International",         "CPT", "city_cape_town",True),
    ]
    for a in data:
        _n(g, a, "Airport")


# ---------------------------------------------------------------------------
# Airlines
# ---------------------------------------------------------------------------

def _airlines(g) -> None:
    data = [
        Airline("airline_ba", "British Airways",  "BA",  "airport_lhr", "premium"),
        Airline("airline_af", "Air France",       "AF",  "airport_cdg", "premium"),
        Airline("airline_ek", "Emirates",         "EK",  "airport_dxb", "luxury"),
        Airline("airline_dl", "Delta Air Lines",  "DL",  "airport_jfk", "economy"),
        Airline("airline_az", "ITA Airways",      "AZ",  "airport_fco", "economy"),
        Airline("airline_nh", "ANA",              "NH",  "airport_nrt", "premium"),
        Airline("airline_qa", "Qatar Airways",    "QR",  "airport_dxb", "luxury"),
        Airline("airline_w3", "Arik Air",         "W3",  "airport_los", "economy"),
    ]
    for a in data:
        _n(g, a, "Airline")


# ---------------------------------------------------------------------------
# Hotels
# ---------------------------------------------------------------------------

def _hotels(g) -> None:
    data = [
        Hotel("hotel_eko",        "Eko Hotels & Suites",   "city_lagos",     5, "luxury",    ["pool", "spa", "wifi", "gym"]),
        Hotel("hotel_radisson_ng","Radisson Blu Lagos",    "city_lagos",     4, "comfort",   ["wifi", "gym", "restaurant"]),
        Hotel("hotel_ritz",       "The Ritz London",       "city_london",    5, "luxury",    ["spa", "wifi", "pool", "restaurant"]),
        Hotel("hotel_premier_lon","Premier Inn London",    "city_london",    3, "mid-range", ["wifi", "breakfast"]),
        Hotel("hotel_le_meurice", "Le Meurice",            "city_paris",     5, "luxury",    ["spa", "wifi", "restaurant"]),
        Hotel("hotel_ibis_paris", "Ibis Paris Centre",     "city_paris",     2, "budget",    ["wifi"]),
        Hotel("hotel_atlantis",   "Atlantis The Palm",     "city_dubai",     5, "luxury",    ["pool", "beach", "spa", "gym"]),
        Hotel("hotel_premier_dxb","Premier Inn Dubai",     "city_dubai",     4, "mid-range", ["pool", "wifi", "gym"]),
        Hotel("hotel_plaza",      "The Plaza Hotel",       "city_new_york",  5, "luxury",    ["spa", "wifi", "restaurant"]),
        Hotel("hotel_citizenm",   "citizenM New York",     "city_new_york",  4, "mid-range", ["wifi", "gym"]),
        Hotel("hotel_cavalieri",  "Rome Cavalieri",        "city_rome",      5, "luxury",    ["pool", "spa", "wifi"]),
        Hotel("hotel_hotel_art",  "Hotel Art Rome",        "city_rome",      4, "mid-range", ["wifi", "breakfast"]),
        Hotel("hotel_arts",       "Hotel Arts Barcelona",  "city_barcelona", 5, "luxury",    ["pool", "beach", "spa"]),
        Hotel("hotel_catalonia",  "Catalonia Barcelona",   "city_barcelona", 3, "mid-range", ["wifi", "breakfast"]),
        Hotel("hotel_palace_tok", "Palace Hotel Tokyo",    "city_tokyo",     5, "luxury",    ["spa", "pool", "wifi"]),
        Hotel("hotel_dormy",      "Dormy Inn Tokyo",       "city_tokyo",     3, "mid-range", ["wifi", "breakfast"]),
    ]
    for h in data:
        _n(g, h, "Hotel")


# ---------------------------------------------------------------------------
# Attractions
# ---------------------------------------------------------------------------

def _attractions(g) -> None:
    data = [
        Attraction("attr_vi",        "Victoria Island",      "city_lagos",     "entertainment", ["beach", "nightlife", "business"]),
        Attraction("attr_olumo",     "Olumo Rock",           "city_abuja",     "natural",       ["historic", "nature"]),
        Attraction("attr_tower",     "Tower of London",      "city_london",    "historic",      ["history", "culture"]),
        Attraction("attr_wembley",   "Wembley Stadium",      "city_london",    "sport",         ["football", "sport", "music"]),
        Attraction("attr_eiffel",    "Eiffel Tower",         "city_paris",     "landmark",      ["iconic", "romantic"]),
        Attraction("attr_louvre_at", "Louvre Museum Gardens","city_paris",     "cultural",      ["art", "culture"]),
        Attraction("attr_burj",      "Burj Khalifa",         "city_dubai",     "landmark",      ["modern", "views", "luxury"]),
        Attraction("attr_palm",      "Palm Jumeirah",        "city_dubai",     "natural",       ["beach", "luxury"]),
        Attraction("attr_empire",    "Empire State Building","city_new_york",  "landmark",      ["views", "iconic"]),
        Attraction("attr_central",   "Central Park",         "city_new_york",  "natural",       ["nature", "running", "cycling"]),
        Attraction("attr_colosseum", "Colosseum",            "city_rome",      "historic",      ["history", "ancient", "culture"]),
        Attraction("attr_sagrada",   "Sagrada Família",      "city_barcelona", "cultural",      ["art", "architecture", "religious"]),
        Attraction("attr_senso",     "Senso-ji Temple",      "city_tokyo",     "religious",     ["culture", "historic", "photography"]),
        Attraction("attr_kakum",     "Kakum National Park",  "city_accra",     "natural",       ["nature", "adventure", "wildlife"]),
        Attraction("attr_tafelberg", "Table Mountain",       "city_cape_town", "natural",       ["nature", "hiking", "views"]),
    ]
    for a in data:
        _n(g, a, "Attraction")


# ---------------------------------------------------------------------------
# Museums
# ---------------------------------------------------------------------------

def _museums(g) -> None:
    data = [
        Museum("museum_british",  "British Museum",              "city_london",    "history",  ["ancient", "world", "free"]),
        Museum("museum_tate",     "Tate Modern",                 "city_london",    "art",      ["modern-art", "free"]),
        Museum("museum_louvre",   "Louvre",                      "city_paris",     "art",      ["renaissance", "mona-lisa"]),
        Museum("museum_orsay",    "Musée d'Orsay",               "city_paris",     "art",      ["impressionism", "van-gogh"]),
        Museum("museum_vatican",  "Vatican Museums",             "city_rome",      "art",      ["sistine-chapel", "renaissance"]),
        Museum("museum_prado",    "Prado Museum",                "city_barcelona", "art",      ["spanish-masters", "goya"]),
        Museum("museum_met",      "Metropolitan Museum of Art",  "city_new_york",  "art",      ["world-class", "ancient"]),
        Museum("museum_national_gh","National Museum of Ghana",  "city_accra",     "history",  ["african-history", "culture"]),
        Museum("museum_tokyo_nat","Tokyo National Museum",       "city_tokyo",     "history",  ["japanese-art", "samurai"]),
        Museum("museum_iziko",    "Iziko South African Museum",  "city_cape_town", "natural",  ["natural-history", "african-culture"]),
    ]
    for m in data:
        _n(g, m, "Museum")


# ---------------------------------------------------------------------------
# Restaurants
# ---------------------------------------------------------------------------

def _restaurants(g) -> None:
    data = [
        Restaurant("rest_nok",      "Nok by Alara",         "city_lagos",     "Nigerian",      "luxury",    ["fine-dining", "afro-fusion"]),
        Restaurant("rest_sketch",   "Sketch",               "city_london",    "European",      "luxury",    ["fine-dining", "afternoon-tea"]),
        Restaurant("rest_ledou",    "Le Doyen",             "city_paris",     "French",        "luxury",    ["michelin", "fine-dining"]),
        Restaurant("rest_nobu_dxb", "Nobu Dubai",           "city_dubai",     "Japanese",      "luxury",    ["fusion", "sushi"]),
        Restaurant("rest_eleven",   "Eleven Madison Park",  "city_new_york",  "American",      "luxury",    ["michelin", "plant-based"]),
        Restaurant("rest_roscioli", "Roscioli",             "city_rome",      "Italian",       "mid-range", ["pasta", "wine", "local"]),
        Restaurant("rest_tickets",  "Tickets",              "city_barcelona", "Spanish",       "luxury",    ["tapas", "avant-garde"]),
        Restaurant("rest_sushi_sai","Sushi Saito",          "city_tokyo",     "Japanese",      "luxury",    ["omakase", "michelin"]),
    ]
    for r in data:
        _n(g, r, "Restaurant")


# ---------------------------------------------------------------------------
# Football clubs
# ---------------------------------------------------------------------------

def _football_clubs(g) -> None:
    data = [
        FootballClub("club_arsenal",  "Arsenal FC",       "city_london",    "Premier League", "Emirates Stadium",   1886),
        FootballClub("club_chelsea",  "Chelsea FC",       "city_london",    "Premier League", "Stamford Bridge",    1905),
        FootballClub("club_psg",      "Paris Saint-Germain","city_paris",   "Ligue 1",        "Parc des Princes",   1970),
        FootballClub("club_barca",    "FC Barcelona",     "city_barcelona", "La Liga",        "Camp Nou",           1899),
        FootballClub("club_roma",     "AS Roma",          "city_rome",      "Serie A",        "Stadio Olimpico",    1927),
        FootballClub("club_juventus", "Juventus FC",      "city_rome",      "Serie A",        "Allianz Stadium",    1897),
        FootballClub("club_inter",    "Inter Milan",      "city_rome",      "Serie A",        "San Siro",           1908),
        FootballClub("club_gamba",    "Gamba Osaka",      "city_tokyo",     "J1 League",      "Panasonic Stadium",  1980),
    ]
    for c in data:
        _n(g, c, "FootballClub")


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

def _events(g) -> None:
    data = [
        Event("evt_afrobeats",  "Lagos Afrobeats Festival",      "city_lagos",     "festival",    12, ["music", "culture", "nightlife"]),
        Event("evt_notting",    "Notting Hill Carnival",         "city_london",    "festival",    8,  ["music", "culture", "carnival"]),
        Event("evt_fashion_par","Paris Fashion Week",            "city_paris",     "exhibition",  10, ["fashion", "luxury"]),
        Event("evt_expo_dxb",   "Dubai Expo",                    "city_dubai",     "exhibition",  10, ["technology", "culture", "business"]),
        Event("evt_marathon_ny","New York City Marathon",        "city_new_york",  "sport",       11, ["sport", "running"]),
        Event("evt_tomato",     "La Tomatina",                   "city_barcelona", "festival",    8,  ["culture", "fun", "quirky"]),
        Event("evt_cherry",     "Hanami Cherry Blossom Festival","city_tokyo",     "festival",    4,  ["nature", "culture", "photography"]),
        Event("evt_panafest",   "PANAFEST",                      "city_accra",     "cultural",    7,  ["african-heritage", "culture"]),
    ]
    for e in data:
        _n(g, e, "Event")


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------

def _transport(g) -> None:
    data = [
        Transport("trans_tube",     "London Underground",        "metro",  "city_london"),
        Transport("trans_rer",      "Paris RER",                 "rail",   "city_paris"),
        Transport("trans_metro_dxb","Dubai Metro",               "metro",  "city_dubai"),
        Transport("trans_subway_ny","New York Subway",           "metro",  "city_new_york"),
        Transport("trans_metro_bcn","Barcelona Metro",           "metro",  "city_barcelona"),
        Transport("trans_shinkansen","Shinkansen (Bullet Train)", "rail",   "city_tokyo"),
    ]
    for t in data:
        _n(g, t, "Transport")


# ---------------------------------------------------------------------------
# Visa requirements (selective)
# ---------------------------------------------------------------------------

def _visa_requirements(g) -> None:
    data = [
        VisaRequirement("visa_ng_gb", "NG", "GB", "required",        None,  "Apply via UK embassy"),
        VisaRequirement("visa_ng_fr", "NG", "FR", "required",        None,  "Schengen visa required"),
        VisaRequirement("visa_ng_ae", "NG", "AE", "visa-on-arrival", 30,    "30-day visa on arrival"),
        VisaRequirement("visa_ng_us", "NG", "US", "required",        None,  "B1/B2 visa required"),
        VisaRequirement("visa_ng_it", "NG", "IT", "required",        None,  "Schengen visa required"),
        VisaRequirement("visa_gb_fr", "GB", "FR", "required",        180,   "ETA or visa post-Brexit"),
        VisaRequirement("visa_gb_ae", "GB", "AE", "visa-free",       90,    "90-day visa-free"),
        VisaRequirement("visa_gb_us", "GB", "US", "visa-free",       90,    "ESTA required"),
        VisaRequirement("visa_gb_jp", "GB", "JP", "visa-free",       90,    "90-day visa-free"),
        VisaRequirement("visa_us_gb", "US", "GB", "visa-free",       180,   "eTA required"),
        VisaRequirement("visa_us_fr", "US", "FR", "visa-free",       90,    "Schengen — ETIAS required from 2025"),
        VisaRequirement("visa_us_ae", "US", "AE", "visa-free",       30,    "30-day visa-free"),
    ]
    for v in data:
        _n(g, v, "VisaRequirement")


# ---------------------------------------------------------------------------
# Weather (key months for key cities)
# ---------------------------------------------------------------------------

def _weather(g) -> None:
    data = [
        # Lagos: hot tropical
        Weather("w_lag_1",  "city_lagos",     1,  28.0, "sunny",        "dry"),
        Weather("w_lag_7",  "city_lagos",     7,  25.0, "rainy",        "wet"),
        Weather("w_lag_12", "city_lagos",     12, 29.0, "sunny",        "dry"),
        # London: mild, variable
        Weather("w_lon_4",  "city_london",    4,  11.0, "partly-cloudy","spring"),
        Weather("w_lon_7",  "city_london",    7,  20.0, "sunny",        "summer"),
        Weather("w_lon_12", "city_london",    12,  6.0, "cold",         "winter"),
        # Paris: temperate
        Weather("w_par_4",  "city_paris",     4,  13.0, "partly-cloudy","spring"),
        Weather("w_par_7",  "city_paris",     7,  24.0, "sunny",        "summer"),
        Weather("w_par_12", "city_paris",     12,  5.0, "cold",         "winter"),
        # Dubai: hot, dry
        Weather("w_dxb_1",  "city_dubai",     1,  22.0, "sunny",        "mild"),
        Weather("w_dxb_7",  "city_dubai",     7,  41.0, "hot",          "summer"),
        Weather("w_dxb_11", "city_dubai",     11, 28.0, "sunny",        "autumn"),
        # New York
        Weather("w_ny_4",   "city_new_york",  4,  13.0, "partly-cloudy","spring"),
        Weather("w_ny_7",   "city_new_york",  7,  28.0, "humid",        "summer"),
        Weather("w_ny_12",  "city_new_york",  12,  3.0, "cold",         "winter"),
        # Rome
        Weather("w_rom_4",  "city_rome",      4,  16.0, "sunny",        "spring"),
        Weather("w_rom_7",  "city_rome",      7,  31.0, "hot",          "summer"),
        Weather("w_rom_10", "city_rome",      10, 18.0, "partly-cloudy","autumn"),
        # Barcelona
        Weather("w_bcn_4",  "city_barcelona", 4,  16.0, "sunny",        "spring"),
        Weather("w_bcn_7",  "city_barcelona", 7,  27.0, "hot",          "summer"),
        Weather("w_bcn_10", "city_barcelona", 10, 19.0, "partly-cloudy","autumn"),
        # Tokyo
        Weather("w_tok_4",  "city_tokyo",     4,  15.0, "sunny",        "spring"),
        Weather("w_tok_7",  "city_tokyo",     7,  29.0, "humid",        "summer"),
        Weather("w_tok_12", "city_tokyo",     12,  8.0, "cold",         "winter"),
        # Cape Town
        Weather("w_cpt_1",  "city_cape_town", 1,  26.0, "sunny",        "summer"),
        Weather("w_cpt_7",  "city_cape_town", 7,  13.0, "rainy",        "winter"),
    ]
    for w in data:
        _n(g, w, "Weather")


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------

def _relationships(g) -> None:
    L = R.LOCATED_IN
    B = R.BELONGS_TO
    O = R.OPERATES_FROM
    UC = R.USES_CURRENCY
    HW = R.HAS_WEATHER
    PT = R.PART_OF

    # City → Country
    for city_id, country_id in [
        ("city_lagos", "country_ng"), ("city_abuja", "country_ng"),
        ("city_london", "country_gb"), ("city_paris", "country_fr"),
        ("city_dubai", "country_ae"), ("city_new_york", "country_us"),
        ("city_rome", "country_it"), ("city_barcelona", "country_es"),
        ("city_tokyo", "country_jp"), ("city_accra", "country_gh"),
        ("city_cape_town", "country_za"),
    ]:
        _e(g, city_id, "City", L, country_id, "Country")

    # Airport → City
    for ap_id, city_id in [
        ("airport_los", "city_lagos"), ("airport_abv", "city_abuja"),
        ("airport_lhr", "city_london"), ("airport_cdg", "city_paris"),
        ("airport_dxb", "city_dubai"), ("airport_jfk", "city_new_york"),
        ("airport_fco", "city_rome"), ("airport_bcn", "city_barcelona"),
        ("airport_nrt", "city_tokyo"), ("airport_acc", "city_accra"),
        ("airport_cpt", "city_cape_town"),
    ]:
        _e(g, ap_id, "Airport", L, city_id, "City")

    # Hotel → City
    hotel_city = [
        ("hotel_eko", "city_lagos"), ("hotel_radisson_ng", "city_lagos"),
        ("hotel_ritz", "city_london"), ("hotel_premier_lon", "city_london"),
        ("hotel_le_meurice", "city_paris"), ("hotel_ibis_paris", "city_paris"),
        ("hotel_atlantis", "city_dubai"), ("hotel_premier_dxb", "city_dubai"),
        ("hotel_plaza", "city_new_york"), ("hotel_citizenm", "city_new_york"),
        ("hotel_cavalieri", "city_rome"), ("hotel_hotel_art", "city_rome"),
        ("hotel_arts", "city_barcelona"), ("hotel_catalonia", "city_barcelona"),
        ("hotel_palace_tok", "city_tokyo"), ("hotel_dormy", "city_tokyo"),
    ]
    for h_id, c_id in hotel_city:
        _e(g, h_id, "Hotel", B, c_id, "City")

    # Airline → Airport (hub)
    for al_id, ap_id in [
        ("airline_ba", "airport_lhr"), ("airline_af", "airport_cdg"),
        ("airline_ek", "airport_dxb"), ("airline_dl", "airport_jfk"),
        ("airline_az", "airport_fco"), ("airline_nh", "airport_nrt"),
        ("airline_w3", "airport_los"),
    ]:
        _e(g, al_id, "Airline", O, ap_id, "Airport")

    # Attraction → City
    attr_city = [
        ("attr_vi", "city_lagos"), ("attr_olumo", "city_abuja"),
        ("attr_tower", "city_london"), ("attr_wembley", "city_london"),
        ("attr_eiffel", "city_paris"), ("attr_louvre_at", "city_paris"),
        ("attr_burj", "city_dubai"), ("attr_palm", "city_dubai"),
        ("attr_empire", "city_new_york"), ("attr_central", "city_new_york"),
        ("attr_colosseum", "city_rome"), ("attr_sagrada", "city_barcelona"),
        ("attr_senso", "city_tokyo"), ("attr_kakum", "city_accra"),
        ("attr_tafelberg", "city_cape_town"),
    ]
    for a_id, c_id in attr_city:
        _e(g, a_id, "Attraction", R.NEAR, c_id, "City")

    # Museum → City
    mus_city = [
        ("museum_british", "city_london"), ("museum_tate", "city_london"),
        ("museum_louvre", "city_paris"), ("museum_orsay", "city_paris"),
        ("museum_vatican", "city_rome"), ("museum_prado", "city_barcelona"),
        ("museum_met", "city_new_york"), ("museum_national_gh", "city_accra"),
        ("museum_tokyo_nat", "city_tokyo"), ("museum_iziko", "city_cape_town"),
    ]
    for m_id, c_id in mus_city:
        _e(g, m_id, "Museum", L, c_id, "City")

    # Restaurant → City
    rest_city = [
        ("rest_nok", "city_lagos"), ("rest_sketch", "city_london"),
        ("rest_ledou", "city_paris"), ("rest_nobu_dxb", "city_dubai"),
        ("rest_eleven", "city_new_york"), ("rest_roscioli", "city_rome"),
        ("rest_tickets", "city_barcelona"), ("rest_sushi_sai", "city_tokyo"),
    ]
    for r_id, c_id in rest_city:
        _e(g, r_id, "Restaurant", B, c_id, "City")

    # FootballClub → City
    club_city = [
        ("club_arsenal", "city_london"), ("club_chelsea", "city_london"),
        ("club_psg", "city_paris"), ("club_barca", "city_barcelona"),
        ("club_roma", "city_rome"), ("club_gamba", "city_tokyo"),
    ]
    for fc_id, c_id in club_city:
        _e(g, fc_id, "FootballClub", B, c_id, "City")

    # Event → City
    evt_city = [
        ("evt_afrobeats", "city_lagos"), ("evt_notting", "city_london"),
        ("evt_fashion_par", "city_paris"), ("evt_expo_dxb", "city_dubai"),
        ("evt_marathon_ny", "city_new_york"), ("evt_tomato", "city_barcelona"),
        ("evt_cherry", "city_tokyo"), ("evt_panafest", "city_accra"),
    ]
    for e_id, c_id in evt_city:
        _e(g, e_id, "Event", PT, c_id, "City")

    # Transport → City
    trans_city = [
        ("trans_tube", "city_london"), ("trans_rer", "city_paris"),
        ("trans_metro_dxb", "city_dubai"), ("trans_subway_ny", "city_new_york"),
        ("trans_metro_bcn", "city_barcelona"), ("trans_shinkansen", "city_tokyo"),
    ]
    for t_id, c_id in trans_city:
        _e(g, t_id, "Transport", B, c_id, "City")

    # Country → Currency
    country_currency = [
        ("country_ng", "cur_ngn"), ("country_gb", "cur_gbp"),
        ("country_fr", "cur_eur"), ("country_ae", "cur_aed"),
        ("country_us", "cur_usd"), ("country_it", "cur_eur"),
        ("country_es", "cur_eur"), ("country_jp", "cur_jpy"),
        ("country_gh", "cur_ghc"), ("country_za", "cur_zar"),
    ]
    for ctry_id, cur_id in country_currency:
        _e(g, ctry_id, "Country", UC, cur_id, "Currency")

    # City → Weather
    weather_city = [
        ("w_lag_1", "city_lagos"), ("w_lag_7", "city_lagos"), ("w_lag_12", "city_lagos"),
        ("w_lon_4", "city_london"), ("w_lon_7", "city_london"), ("w_lon_12", "city_london"),
        ("w_par_4", "city_paris"), ("w_par_7", "city_paris"), ("w_par_12", "city_paris"),
        ("w_dxb_1", "city_dubai"), ("w_dxb_7", "city_dubai"), ("w_dxb_11", "city_dubai"),
        ("w_ny_4", "city_new_york"), ("w_ny_7", "city_new_york"), ("w_ny_12", "city_new_york"),
        ("w_rom_4", "city_rome"), ("w_rom_7", "city_rome"), ("w_rom_10", "city_rome"),
        ("w_bcn_4", "city_barcelona"), ("w_bcn_7", "city_barcelona"), ("w_bcn_10", "city_barcelona"),
        ("w_tok_4", "city_tokyo"), ("w_tok_7", "city_tokyo"), ("w_tok_12", "city_tokyo"),
        ("w_cpt_1", "city_cape_town"), ("w_cpt_7", "city_cape_town"),
    ]
    for w_id, c_id in weather_city:
        _e(g, c_id, "City", HW, w_id, "Weather")
