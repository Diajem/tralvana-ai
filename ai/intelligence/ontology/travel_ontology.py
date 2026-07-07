"""
Seed data for the TravelOS Knowledge Graph.

Sprint 1 coverage: 10 countries, 11 cities, 8 currencies, 8 languages,
6 regions, 11 airports, 6 rail stations, 8 airlines, 16 hotels, 15 attractions,
10 museums, 8 restaurants, 8 cuisines, 8 football clubs, 8 sports venues,
8 events, 6 transport systems, 12 visa requirements, 26 weather records,
6 travel seasons.
"""
from __future__ import annotations

from ai.intelligence.knowledge.entities import (
    Airline, Airport, Attraction, City, Country, Cuisine, Currency,
    Event, FootballClub, Hotel, Language, Museum, RailStation,
    Region, Restaurant, SportsVenue, Transport, TravelSeason,
    VisaRequirement, Weather,
)
from ai.intelligence.knowledge.relationships import Relationship, RelationshipType


def seed_graph(g: object) -> None:
    _currencies(g)
    _languages(g)
    _countries(g)
    _regions(g)
    _cities(g)
    _airports(g)
    _rail_stations(g)
    _airlines(g)
    _hotels(g)
    _cuisines(g)
    _restaurants(g)
    _sports_venues(g)
    _football_clubs(g)
    _attractions(g)
    _museums(g)
    _events(g)
    _transport(g)
    _visa_requirements(g)
    _weather(g)
    _travel_seasons(g)
    _relationships(g)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _n(g, entity, entity_type: str) -> None:
    g.add_node(entity, entity_type)


def _e(g, src_id, src_type, rel, tgt_id, tgt_type, weight=1.0, **meta) -> None:
    g.add_edge(Relationship(src_id, src_type, rel, tgt_id, tgt_type, weight, meta))


R = RelationshipType


# ---------------------------------------------------------------------------

def _currencies(g) -> None:
    for c in [
        Currency("cur_ngn", "NGN", "Nigerian Naira",    "₦",  ["NG"]),
        Currency("cur_gbp", "GBP", "British Pound",     "£",  ["GB"]),
        Currency("cur_eur", "EUR", "Euro",              "€",  ["FR", "IT", "ES", "NL", "DE"]),
        Currency("cur_aed", "AED", "UAE Dirham",        "د.إ",["AE"]),
        Currency("cur_usd", "USD", "US Dollar",         "$",  ["US"]),
        Currency("cur_jpy", "JPY", "Japanese Yen",      "¥",  ["JP"]),
        Currency("cur_ghs", "GHS", "Ghanaian Cedi",     "₵",  ["GH"]),
        Currency("cur_zar", "ZAR", "South African Rand","R",  ["ZA"]),
    ]:
        _n(g, c, "Currency")


def _languages(g) -> None:
    for l in [
        Language("lang_en", "English",  "en", "English",   1500),
        Language("lang_fr", "French",   "fr", "Français",   321),
        Language("lang_ar", "Arabic",   "ar", "العربية",    310),
        Language("lang_it", "Italian",  "it", "Italiano",    67),
        Language("lang_es", "Spanish",  "es", "Español",    559),
        Language("lang_ja", "Japanese", "ja", "日本語",      125),
        Language("lang_yo", "Yoruba",   "yo", "Yorùbá",      46),
        Language("lang_ha", "Hausa",    "ha", "Hausa",       77),
    ]:
        _n(g, l, "Language")


def _countries(g) -> None:
    for c in [
        Country("country_ng","Nigeria",        "NG","Africa",  "city_lagos",    ["yo","ha","en"],"NGN","medium"),
        Country("country_gb","United Kingdom", "GB","Europe",  "city_london",   ["en"],          "GBP","low"),
        Country("country_fr","France",         "FR","Europe",  "city_paris",    ["fr"],          "EUR","low"),
        Country("country_ae","UAE",            "AE","Asia",    "city_dubai",    ["ar","en"],     "AED","low"),
        Country("country_us","United States",  "US","Americas","city_new_york", ["en"],          "USD","low"),
        Country("country_it","Italy",          "IT","Europe",  "city_rome",     ["it"],          "EUR","low"),
        Country("country_es","Spain",          "ES","Europe",  "city_barcelona",["es"],          "EUR","low"),
        Country("country_jp","Japan",          "JP","Asia",    "city_tokyo",    ["ja"],          "JPY","low"),
        Country("country_gh","Ghana",          "GH","Africa",  "city_accra",    ["en"],          "GHS","low"),
        Country("country_za","South Africa",   "ZA","Africa",  "city_cape_town",["en","af","zu"],"ZAR","medium"),
    ]:
        _n(g, c, "Country")


def _regions(g) -> None:
    for r in [
        Region("region_lagos_st",  "Lagos State",      "country_ng", "state",    ["coastal","urban"]),
        Region("region_london",    "Greater London",   "country_gb", "county",   ["urban","diverse"]),
        Region("region_idf",       "Île-de-France",    "country_fr", "province", ["urban","cultural"]),
        Region("region_lazio",     "Lazio",            "country_it", "province", ["historic","cultural"]),
        Region("region_catalonia", "Catalonia",        "country_es", "province", ["beach","culture","sport"]),
        Region("region_kanto",     "Kantō Region",     "country_jp", "district", ["urban","tech","food"]),
    ]:
        _n(g, r, "Region")


def _cities(g) -> None:
    for c in [
        City("city_lagos",    "Lagos",     "country_ng","region_lagos_st","Africa/Lagos",     15_000_000,["coastal","urban","business","nightlife"]),
        City("city_abuja",    "Abuja",     "country_ng", None,            "Africa/Lagos",      3_600_000,["urban","business","modern"]),
        City("city_london",   "London",    "country_gb","region_london",  "Europe/London",     9_000_000,["urban","historic","cultural","business"]),
        City("city_paris",    "Paris",     "country_fr","region_idf",     "Europe/Paris",      2_100_000,["romantic","cultural","fashion","food"]),
        City("city_dubai",    "Dubai",     "country_ae", None,            "Asia/Dubai",        3_300_000,["luxury","urban","beach","modern"]),
        City("city_new_york", "New York",  "country_us", None,            "America/New_York",  8_300_000,["urban","cultural","business","food"]),
        City("city_rome",     "Rome",      "country_it","region_lazio",   "Europe/Rome",       2_800_000,["historic","cultural","food","art"]),
        City("city_barcelona","Barcelona", "country_es","region_catalonia","Europe/Madrid",    1_600_000,["beach","urban","food","nightlife","sport"]),
        City("city_tokyo",    "Tokyo",     "country_jp","region_kanto",   "Asia/Tokyo",       14_000_000,["urban","technology","food","cultural"]),
        City("city_accra",    "Accra",     "country_gh", None,            "Africa/Accra",      2_300_000,["coastal","urban","business","cultural"]),
        City("city_cape_town","Cape Town", "country_za", None,            "Africa/Johannesburg",4_600_000,["coastal","nature","beach","mountain"]),
    ]:
        _n(g, c, "City")


def _airports(g) -> None:
    for a in [
        Airport("airport_los","Murtala Muhammed Intl","LOS","city_lagos",     True),
        Airport("airport_abv","Nnamdi Azikiwe Intl",  "ABV","city_abuja",     True),
        Airport("airport_lhr","Heathrow",              "LHR","city_london",    True),
        Airport("airport_cdg","Charles de Gaulle",     "CDG","city_paris",     True),
        Airport("airport_dxb","Dubai International",   "DXB","city_dubai",     True),
        Airport("airport_jfk","JFK International",     "JFK","city_new_york",  True),
        Airport("airport_fco","Fiumicino",             "FCO","city_rome",      True),
        Airport("airport_bcn","El Prat",               "BCN","city_barcelona", True),
        Airport("airport_nrt","Narita International",  "NRT","city_tokyo",     True),
        Airport("airport_acc","Kotoka International",  "ACC","city_accra",     True),
        Airport("airport_cpt","Cape Town International","CPT","city_cape_town", True),
    ]:
        _n(g, a, "Airport")


def _rail_stations(g) -> None:
    for s in [
        RailStation("rail_stpancras", "London St Pancras Intl", "city_london",   "STP", True),
        RailStation("rail_euston",    "London Euston",           "city_london",   "EUS", False),
        RailStation("rail_gdnord",    "Paris Gare du Nord",      "city_paris",    "GDN", True),
        RailStation("rail_termini",   "Roma Termini",            "city_rome",     "RZT", False),
        RailStation("rail_sants",     "Barcelona Sants",         "city_barcelona","BRC", True),
        RailStation("rail_shinjuku",  "Tokyo Shinjuku",          "city_tokyo",    "SJK", True),
    ]:
        _n(g, s, "RailStation")


def _airlines(g) -> None:
    for a in [
        Airline("airline_ba","British Airways",  "BA","airport_lhr","premium", "OneWorld"),
        Airline("airline_af","Air France",       "AF","airport_cdg","premium", "SkyTeam"),
        Airline("airline_ek","Emirates",         "EK","airport_dxb","luxury",  ""),
        Airline("airline_dl","Delta Air Lines",  "DL","airport_jfk","economy", "SkyTeam"),
        Airline("airline_az","ITA Airways",      "AZ","airport_fco","economy", "SkyTeam"),
        Airline("airline_nh","ANA",              "NH","airport_nrt","premium", "Star Alliance"),
        Airline("airline_qr","Qatar Airways",    "QR","airport_dxb","luxury",  "OneWorld"),
        Airline("airline_w3","Arik Air",         "W3","airport_los","economy", ""),
    ]:
        _n(g, a, "Airline")


def _hotels(g) -> None:
    for h in [
        Hotel("hotel_eko",        "Eko Hotels & Suites",  "city_lagos",     5,"luxury",    ["pool","spa","wifi","gym"]),
        Hotel("hotel_radisson_ng","Radisson Blu Lagos",   "city_lagos",     4,"mid-range", ["wifi","gym","restaurant"]),
        Hotel("hotel_ritz",       "The Ritz London",      "city_london",    5,"luxury",    ["spa","wifi","pool","restaurant"]),
        Hotel("hotel_premier_lon","Premier Inn London",   "city_london",    3,"mid-range", ["wifi","breakfast"]),
        Hotel("hotel_le_meurice", "Le Meurice",           "city_paris",     5,"luxury",    ["spa","wifi","restaurant"]),
        Hotel("hotel_ibis_paris", "Ibis Paris Centre",    "city_paris",     2,"budget",    ["wifi"]),
        Hotel("hotel_atlantis",   "Atlantis The Palm",    "city_dubai",     5,"luxury",    ["pool","beach","spa","gym"]),
        Hotel("hotel_premier_dxb","Premier Inn Dubai",    "city_dubai",     4,"mid-range", ["pool","wifi","gym"]),
        Hotel("hotel_plaza",      "The Plaza Hotel",      "city_new_york",  5,"luxury",    ["spa","wifi","restaurant"]),
        Hotel("hotel_citizenm",   "citizenM New York",    "city_new_york",  4,"mid-range", ["wifi","gym"]),
        Hotel("hotel_cavalieri",  "Rome Cavalieri",       "city_rome",      5,"luxury",    ["pool","spa","wifi"]),
        Hotel("hotel_hotel_art",  "Hotel Art Rome",       "city_rome",      4,"mid-range", ["wifi","breakfast"]),
        Hotel("hotel_arts",       "Hotel Arts Barcelona", "city_barcelona", 5,"luxury",    ["pool","beach","spa"]),
        Hotel("hotel_catalonia",  "Catalonia Barcelona",  "city_barcelona", 3,"mid-range", ["wifi","breakfast"]),
        Hotel("hotel_palace_tok", "Palace Hotel Tokyo",   "city_tokyo",     5,"luxury",    ["spa","pool","wifi"]),
        Hotel("hotel_dormy",      "Dormy Inn Tokyo",      "city_tokyo",     3,"mid-range", ["wifi","breakfast"]),
    ]:
        _n(g, h, "Hotel")


def _cuisines(g) -> None:
    for c in [
        Cuisine("cuisine_nigerian","Nigerian",      "NG",["spicy","stew","halal-options","rice-based"]),
        Cuisine("cuisine_british", "British",       "GB",["meat","pub-style","mild"]),
        Cuisine("cuisine_french",  "French",        "FR",["wine","cheese","fine-dining","sauces"]),
        Cuisine("cuisine_italian", "Italian",       "IT",["pasta","pizza","gelato","wine"]),
        Cuisine("cuisine_spanish", "Spanish",       "ES",["tapas","seafood","paella","jamón"]),
        Cuisine("cuisine_japanese","Japanese",      "JP",["sushi","ramen","umami","vegetarian-friendly"]),
        Cuisine("cuisine_american","American",      "US",["burgers","bbq","portions-large","diverse"]),
        Cuisine("cuisine_arab",    "Arab/Levantine","AE",["halal","rice","lamb","mezze"]),
    ]:
        _n(g, c, "Cuisine")


def _restaurants(g) -> None:
    for r in [
        Restaurant("rest_nok",     "Nok by Alara",        "city_lagos",    "cuisine_nigerian","luxury",    ["fine-dining","afro-fusion"]),
        Restaurant("rest_sketch",  "Sketch",              "city_london",   "cuisine_british", "luxury",    ["fine-dining","afternoon-tea"]),
        Restaurant("rest_ledou",   "Le Doyen",            "city_paris",    "cuisine_french",  "luxury",    ["michelin","fine-dining"]),
        Restaurant("rest_nobu_dxb","Nobu Dubai",          "city_dubai",    "cuisine_japanese","luxury",    ["fusion","sushi"]),
        Restaurant("rest_eleven",  "Eleven Madison Park", "city_new_york", "cuisine_american","luxury",    ["michelin","plant-based"]),
        Restaurant("rest_roscioli","Roscioli",            "city_rome",     "cuisine_italian", "mid-range", ["pasta","wine","local"]),
        Restaurant("rest_tickets", "Tickets",             "city_barcelona","cuisine_spanish", "luxury",    ["tapas","avant-garde"]),
        Restaurant("rest_sushi_s", "Sushi Saito",         "city_tokyo",    "cuisine_japanese","luxury",    ["omakase","michelin"]),
    ]:
        _n(g, r, "Restaurant")


def _sports_venues(g) -> None:
    for v in [
        SportsVenue("venue_emirates",    "Emirates Stadium",   "city_london",    "stadium",60704, "football"),
        SportsVenue("venue_stamford",    "Stamford Bridge",    "city_london",    "stadium",40853, "football"),
        SportsVenue("venue_wembley",     "Wembley Stadium",    "city_london",    "stadium",90000, "football"),
        SportsVenue("venue_parc_princes","Parc des Princes",   "city_paris",     "stadium",48712, "football"),
        SportsVenue("venue_camp_nou",    "Camp Nou",           "city_barcelona", "stadium",99354, "football"),
        SportsVenue("venue_olimpico",    "Stadio Olimpico",    "city_rome",      "stadium",73261, "football"),
        SportsVenue("venue_san_siro",    "San Siro",           "city_rome",      "stadium",80018, "football"),
        SportsVenue("venue_panasonic",   "Panasonic Stadium",  "city_tokyo",     "stadium",39694, "football"),
    ]:
        _n(g, v, "SportsVenue")


def _football_clubs(g) -> None:
    for c in [
        FootballClub("club_arsenal", "Arsenal FC",         "city_london",    "Premier League","venue_emirates",    1886),
        FootballClub("club_chelsea", "Chelsea FC",         "city_london",    "Premier League","venue_stamford",    1905),
        FootballClub("club_psg",     "Paris Saint-Germain","city_paris",     "Ligue 1",       "venue_parc_princes",1970),
        FootballClub("club_barca",   "FC Barcelona",       "city_barcelona", "La Liga",       "venue_camp_nou",    1899),
        FootballClub("club_roma",    "AS Roma",            "city_rome",      "Serie A",       "venue_olimpico",    1927),
        FootballClub("club_juve",    "Juventus FC",        "city_rome",      "Serie A",       "venue_olimpico",    1897),
        FootballClub("club_inter",   "Inter Milan",        "city_rome",      "Serie A",       "venue_san_siro",    1908),
        FootballClub("club_gamba",   "Gamba Osaka",        "city_tokyo",     "J1 League",     "venue_panasonic",   1980),
    ]:
        _n(g, c, "FootballClub")


def _attractions(g) -> None:
    for a in [
        Attraction("attr_vi",       "Victoria Island",       "city_lagos",    "entertainment",["beach","nightlife","business"]),
        Attraction("attr_olumo",    "Olumo Rock",            "city_abuja",    "natural",       ["historic","nature"]),
        Attraction("attr_tower",    "Tower of London",       "city_london",   "historic",      ["history","culture"]),
        Attraction("attr_wembley",  "Wembley Stadium",       "city_london",   "sport",         ["football","sport","music"]),
        Attraction("attr_eiffel",   "Eiffel Tower",          "city_paris",    "landmark",      ["iconic","romantic"]),
        Attraction("attr_louvre_at","Louvre Gardens",        "city_paris",    "cultural",      ["art","culture"]),
        Attraction("attr_burj",     "Burj Khalifa",          "city_dubai",    "landmark",      ["modern","views","luxury"]),
        Attraction("attr_palm",     "Palm Jumeirah",         "city_dubai",    "natural",       ["beach","luxury"]),
        Attraction("attr_empire",   "Empire State Building", "city_new_york", "landmark",      ["views","iconic"]),
        Attraction("attr_central",  "Central Park",          "city_new_york", "natural",       ["nature","running","cycling"]),
        Attraction("attr_colosseum","Colosseum",             "city_rome",     "historic",      ["history","ancient","culture"]),
        Attraction("attr_sagrada",  "Sagrada Família",       "city_barcelona","cultural",      ["art","architecture","religious"]),
        Attraction("attr_senso",    "Senso-ji Temple",       "city_tokyo",    "religious",     ["culture","historic","photography"]),
        Attraction("attr_kakum",    "Kakum National Park",   "city_accra",    "natural",       ["nature","adventure","wildlife"]),
        Attraction("attr_tafelberg","Table Mountain",        "city_cape_town","natural",       ["nature","hiking","views"]),
    ]:
        _n(g, a, "Attraction")


def _museums(g) -> None:
    for m in [
        Museum("museum_british",  "British Museum",            "city_london",   "history",["ancient","world","free"]),
        Museum("museum_tate",     "Tate Modern",               "city_london",   "art",    ["modern-art","free"]),
        Museum("museum_louvre",   "Louvre",                    "city_paris",    "art",    ["renaissance","mona-lisa"]),
        Museum("museum_orsay",    "Musée d'Orsay",             "city_paris",    "art",    ["impressionism","van-gogh"]),
        Museum("museum_vatican",  "Vatican Museums",           "city_rome",     "art",    ["sistine-chapel","renaissance","religious"]),
        Museum("museum_prado",    "Prado Museum",              "city_barcelona","art",    ["spanish-masters","goya"]),
        Museum("museum_met",      "Metropolitan Museum of Art","city_new_york", "art",    ["world-class","ancient"]),
        Museum("museum_ghana_nat","National Museum of Ghana",  "city_accra",    "history",["african-history","culture"]),
        Museum("museum_tokyo_nat","Tokyo National Museum",     "city_tokyo",    "history",["japanese-art","samurai"]),
        Museum("museum_iziko",    "Iziko South African Museum","city_cape_town","natural",["natural-history","african"]),
    ]:
        _n(g, m, "Museum")


def _events(g) -> None:
    for e in [
        Event("evt_afrobeats","Lagos Afrobeats Festival",       "city_lagos",    "festival",  12,["music","culture","nightlife"]),
        Event("evt_notting",  "Notting Hill Carnival",          "city_london",   "festival",  8, ["music","culture","carnival"]),
        Event("evt_fashion",  "Paris Fashion Week",             "city_paris",    "exhibition",10,["fashion","luxury"]),
        Event("evt_expo_dxb", "Dubai Expo City",                "city_dubai",    "exhibition",10,["technology","culture","business"]),
        Event("evt_marathon", "NYC Marathon",                   "city_new_york", "sport",     11,["sport","running"]),
        Event("evt_tomato",   "La Tomatina",                    "city_barcelona","festival",  8, ["culture","fun"]),
        Event("evt_cherry",   "Hanami Cherry Blossom Festival", "city_tokyo",    "festival",  4, ["nature","culture","photography"]),
        Event("evt_panafest", "PANAFEST",                       "city_accra",    "cultural",  7, ["african-heritage","culture","diaspora"]),
    ]:
        _n(g, e, "Event")


def _transport(g) -> None:
    for t in [
        Transport("trans_tube",     "London Underground",        "metro","city_london"),
        Transport("trans_rer",      "Paris RER",                 "rail", "city_paris"),
        Transport("trans_metro_dxb","Dubai Metro",               "metro","city_dubai"),
        Transport("trans_subway_ny","New York Subway",           "metro","city_new_york"),
        Transport("trans_metro_bcn","Barcelona Metro",           "metro","city_barcelona"),
        Transport("trans_shinkansen","Shinkansen (Bullet Train)","rail", "city_tokyo"),
    ]:
        _n(g, t, "Transport")


def _visa_requirements(g) -> None:
    for v in [
        VisaRequirement("visa_ng_gb","NG","GB","required",        None,"Apply via UK Visas and Immigration"),
        VisaRequirement("visa_ng_fr","NG","FR","required",        None,"Schengen visa required"),
        VisaRequirement("visa_ng_ae","NG","AE","visa-on-arrival", 30,  "30-day VOA at Dubai Airport"),
        VisaRequirement("visa_ng_us","NG","US","required",        None,"B1/B2 non-immigrant visa"),
        VisaRequirement("visa_ng_it","NG","IT","required",        None,"Schengen visa required"),
        VisaRequirement("visa_gb_fr","GB","FR","required",        180, "UK nationals need ETA post-Brexit"),
        VisaRequirement("visa_gb_ae","GB","AE","visa-free",       90,  "90-day visa-free entry"),
        VisaRequirement("visa_gb_us","GB","US","visa-free",       90,  "ESTA required — apply online"),
        VisaRequirement("visa_gb_jp","GB","JP","visa-free",       90,  "90-day visa-free"),
        VisaRequirement("visa_us_gb","US","GB","visa-free",       180, "eTA required from 2025"),
        VisaRequirement("visa_us_fr","US","FR","visa-free",       90,  "ETIAS required from 2025"),
        VisaRequirement("visa_us_ae","US","AE","visa-free",       30,  "30-day visa-free"),
    ]:
        _n(g, v, "VisaRequirement")


def _weather(g) -> None:
    for w in [
        Weather("w_lag_1",  "city_lagos",     1, 28.0,"sunny",        "dry"),
        Weather("w_lag_7",  "city_lagos",     7, 25.0,"rainy",        "wet"),
        Weather("w_lag_12", "city_lagos",     12,29.0,"sunny",        "dry"),
        Weather("w_lon_4",  "city_london",    4, 11.0,"partly-cloudy","spring"),
        Weather("w_lon_7",  "city_london",    7, 20.0,"sunny",        "summer"),
        Weather("w_lon_12", "city_london",    12, 6.0,"cold",         "winter"),
        Weather("w_par_4",  "city_paris",     4, 13.0,"partly-cloudy","spring"),
        Weather("w_par_7",  "city_paris",     7, 24.0,"sunny",        "summer"),
        Weather("w_par_12", "city_paris",     12, 5.0,"cold",         "winter"),
        Weather("w_dxb_1",  "city_dubai",     1, 22.0,"sunny",        "mild"),
        Weather("w_dxb_7",  "city_dubai",     7, 41.0,"hot",          "summer"),
        Weather("w_dxb_11", "city_dubai",     11,28.0,"sunny",        "autumn"),
        Weather("w_ny_4",   "city_new_york",  4, 13.0,"partly-cloudy","spring"),
        Weather("w_ny_7",   "city_new_york",  7, 28.0,"humid",        "summer"),
        Weather("w_ny_12",  "city_new_york",  12, 3.0,"cold",         "winter"),
        Weather("w_rom_4",  "city_rome",      4, 16.0,"sunny",        "spring"),
        Weather("w_rom_7",  "city_rome",      7, 31.0,"hot",          "summer"),
        Weather("w_rom_10", "city_rome",      10,18.0,"partly-cloudy","autumn"),
        Weather("w_bcn_4",  "city_barcelona", 4, 16.0,"sunny",        "spring"),
        Weather("w_bcn_7",  "city_barcelona", 7, 27.0,"hot",          "summer"),
        Weather("w_bcn_10", "city_barcelona", 10,19.0,"partly-cloudy","autumn"),
        Weather("w_tok_4",  "city_tokyo",     4, 15.0,"sunny",        "spring"),
        Weather("w_tok_7",  "city_tokyo",     7, 29.0,"humid",        "summer"),
        Weather("w_tok_12", "city_tokyo",     12, 8.0,"cold",         "winter"),
        Weather("w_cpt_1",  "city_cape_town", 1, 26.0,"sunny",        "summer"),
        Weather("w_cpt_7",  "city_cape_town", 7, 13.0,"rainy",        "winter"),
    ]:
        _n(g, w, "Weather")


def _travel_seasons(g) -> None:
    for s in [
        TravelSeason("season_eur_summer","European Peak Summer",  "peak",     [6,7,8],
                     ["city_london","city_paris","city_rome","city_barcelona"],
                     ["crowd-high","prices-high","weather-ideal","long-days"]),
        TravelSeason("season_eur_spring","European Spring Shoulder","shoulder",[4,5],
                     ["city_london","city_paris","city_rome","city_barcelona"],
                     ["crowd-moderate","prices-moderate","weather-pleasant","cherry-blossom"]),
        TravelSeason("season_eur_winter","European Off-Peak Winter","off-peak", [11,12,1,2],
                     ["city_london","city_paris","city_rome"],
                     ["crowd-low","prices-low","cold","christmas-markets"]),
        TravelSeason("season_dxb_cool",  "Dubai Cool Season",      "peak",     [10,11,12,1,2,3],
                     ["city_dubai"],
                     ["weather-ideal","crowd-high","prices-high","outdoor-events"]),
        TravelSeason("season_dxb_hot",   "Dubai Summer Heat",      "off-peak", [6,7,8],
                     ["city_dubai"],
                     ["weather-harsh","prices-low","indoor-focus","prices-low"]),
        TravelSeason("season_ng_harmattan","West Africa Harmattan", "harmattan",[11,12,1,2],
                     ["city_lagos","city_accra"],
                     ["dry","dusty","mild-evenings","haze"]),
    ]:
        _n(g, s, "TravelSeason")


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------

def _relationships(g) -> None:
    L  = R.LOCATED_IN
    B  = R.BELONGS_TO
    SV = R.SERVES
    PI = R.PLAYS_IN
    PA = R.PLAYS_AT
    OP = R.OPERATES_FROM
    UC = R.USES_CURRENCY
    SP = R.SPEAKS
    HR = R.HAS_REGION
    IR = R.IN_REGION
    HW = R.HAS_WEATHER
    HS = R.HAS_SEASON
    PT = R.PART_OF
    NR = R.NEAR
    CN = R.CONNECTS
    HO = R.HOSTS

    # City → Country
    for cty, ctry in [
        ("city_lagos","country_ng"),("city_abuja","country_ng"),
        ("city_london","country_gb"),("city_paris","country_fr"),
        ("city_dubai","country_ae"),("city_new_york","country_us"),
        ("city_rome","country_it"),("city_barcelona","country_es"),
        ("city_tokyo","country_jp"),("city_accra","country_gh"),
        ("city_cape_town","country_za"),
    ]:
        _e(g, cty, "City", L, ctry, "Country")

    # Airport → City
    for ap, cty in [
        ("airport_los","city_lagos"),("airport_abv","city_abuja"),
        ("airport_lhr","city_london"),("airport_cdg","city_paris"),
        ("airport_dxb","city_dubai"),("airport_jfk","city_new_york"),
        ("airport_fco","city_rome"),("airport_bcn","city_barcelona"),
        ("airport_nrt","city_tokyo"),("airport_acc","city_accra"),
        ("airport_cpt","city_cape_town"),
    ]:
        _e(g, ap, "Airport", SV, cty, "City")

    # RailStation → City
    for rs, cty in [
        ("rail_stpancras","city_london"),("rail_euston","city_london"),
        ("rail_gdnord","city_paris"),("rail_termini","city_rome"),
        ("rail_sants","city_barcelona"),("rail_shinjuku","city_tokyo"),
    ]:
        _e(g, rs, "RailStation", CN, cty, "City")

    # Airline → Airport (hub)
    for al, ap in [
        ("airline_ba","airport_lhr"),("airline_af","airport_cdg"),
        ("airline_ek","airport_dxb"),("airline_dl","airport_jfk"),
        ("airline_az","airport_fco"),("airline_nh","airport_nrt"),
        ("airline_w3","airport_los"),
    ]:
        _e(g, al, "Airline", OP, ap, "Airport")

    # Hotel → City
    for h, cty in [
        ("hotel_eko","city_lagos"),("hotel_radisson_ng","city_lagos"),
        ("hotel_ritz","city_london"),("hotel_premier_lon","city_london"),
        ("hotel_le_meurice","city_paris"),("hotel_ibis_paris","city_paris"),
        ("hotel_atlantis","city_dubai"),("hotel_premier_dxb","city_dubai"),
        ("hotel_plaza","city_new_york"),("hotel_citizenm","city_new_york"),
        ("hotel_cavalieri","city_rome"),("hotel_hotel_art","city_rome"),
        ("hotel_arts","city_barcelona"),("hotel_catalonia","city_barcelona"),
        ("hotel_palace_tok","city_tokyo"),("hotel_dormy","city_tokyo"),
    ]:
        _e(g, h, "Hotel", L, cty, "City")

    # Restaurant → City + Restaurant → Cuisine
    rest_data = [
        ("rest_nok","city_lagos","cuisine_nigerian"),
        ("rest_sketch","city_london","cuisine_british"),
        ("rest_ledou","city_paris","cuisine_french"),
        ("rest_nobu_dxb","city_dubai","cuisine_japanese"),
        ("rest_eleven","city_new_york","cuisine_american"),
        ("rest_roscioli","city_rome","cuisine_italian"),
        ("rest_tickets","city_barcelona","cuisine_spanish"),
        ("rest_sushi_s","city_tokyo","cuisine_japanese"),
    ]
    for r_id, cty, cuis in rest_data:
        _e(g, r_id, "Restaurant", B, cty, "City")
        _e(g, r_id, "Restaurant", SV, cuis, "Cuisine")

    # FootballClub → City + FootballClub → SportsVenue
    for fc, cty, venue in [
        ("club_arsenal","city_london","venue_emirates"),
        ("club_chelsea","city_london","venue_stamford"),
        ("club_psg","city_paris","venue_parc_princes"),
        ("club_barca","city_barcelona","venue_camp_nou"),
        ("club_roma","city_rome","venue_olimpico"),
        ("club_juve","city_rome","venue_olimpico"),
        ("club_inter","city_rome","venue_san_siro"),
        ("club_gamba","city_tokyo","venue_panasonic"),
    ]:
        _e(g, fc, "FootballClub", PI, cty, "City")
        _e(g, fc, "FootballClub", PA, venue, "SportsVenue")

    # SportsVenue → City
    for v, cty in [
        ("venue_emirates","city_london"),("venue_stamford","city_london"),
        ("venue_wembley","city_london"),("venue_parc_princes","city_paris"),
        ("venue_camp_nou","city_barcelona"),("venue_olimpico","city_rome"),
        ("venue_san_siro","city_rome"),("venue_panasonic","city_tokyo"),
    ]:
        _e(g, cty, "City", HO, v, "SportsVenue")

    # Attraction → City
    for at, cty in [
        ("attr_vi","city_lagos"),("attr_olumo","city_abuja"),
        ("attr_tower","city_london"),("attr_wembley","city_london"),
        ("attr_eiffel","city_paris"),("attr_louvre_at","city_paris"),
        ("attr_burj","city_dubai"),("attr_palm","city_dubai"),
        ("attr_empire","city_new_york"),("attr_central","city_new_york"),
        ("attr_colosseum","city_rome"),("attr_sagrada","city_barcelona"),
        ("attr_senso","city_tokyo"),("attr_kakum","city_accra"),
        ("attr_tafelberg","city_cape_town"),
    ]:
        _e(g, at, "Attraction", NR, cty, "City")

    # Museum → City
    for m, cty in [
        ("museum_british","city_london"),("museum_tate","city_london"),
        ("museum_louvre","city_paris"),("museum_orsay","city_paris"),
        ("museum_vatican","city_rome"),("museum_prado","city_barcelona"),
        ("museum_met","city_new_york"),("museum_ghana_nat","city_accra"),
        ("museum_tokyo_nat","city_tokyo"),("museum_iziko","city_cape_town"),
    ]:
        _e(g, m, "Museum", L, cty, "City")

    # Event → City
    for ev, cty in [
        ("evt_afrobeats","city_lagos"),("evt_notting","city_london"),
        ("evt_fashion","city_paris"),("evt_expo_dxb","city_dubai"),
        ("evt_marathon","city_new_york"),("evt_tomato","city_barcelona"),
        ("evt_cherry","city_tokyo"),("evt_panafest","city_accra"),
    ]:
        _e(g, ev, "Event", PT, cty, "City")

    # Transport → City
    for t, cty in [
        ("trans_tube","city_london"),("trans_rer","city_paris"),
        ("trans_metro_dxb","city_dubai"),("trans_subway_ny","city_new_york"),
        ("trans_metro_bcn","city_barcelona"),("trans_shinkansen","city_tokyo"),
    ]:
        _e(g, t, "Transport", B, cty, "City")

    # Country → Currency
    for ctry, cur in [
        ("country_ng","cur_ngn"),("country_gb","cur_gbp"),
        ("country_fr","cur_eur"),("country_ae","cur_aed"),
        ("country_us","cur_usd"),("country_it","cur_eur"),
        ("country_es","cur_eur"),("country_jp","cur_jpy"),
        ("country_gh","cur_ghs"),("country_za","cur_zar"),
    ]:
        _e(g, ctry, "Country", UC, cur, "Currency")

    # Country → Language
    for ctry, lang in [
        ("country_ng","lang_yo"),("country_ng","lang_ha"),("country_ng","lang_en"),
        ("country_gb","lang_en"),("country_fr","lang_fr"),("country_ae","lang_ar"),
        ("country_us","lang_en"),("country_it","lang_it"),("country_es","lang_es"),
        ("country_jp","lang_ja"),("country_gh","lang_en"),("country_za","lang_en"),
    ]:
        _e(g, ctry, "Country", SP, lang, "Language")

    # Country → Region + City → Region
    for ctry, reg in [
        ("country_ng","region_lagos_st"),("country_gb","region_london"),
        ("country_fr","region_idf"),("country_it","region_lazio"),
        ("country_es","region_catalonia"),("country_jp","region_kanto"),
    ]:
        _e(g, ctry, "Country", HR, reg, "Region")

    for cty, reg in [
        ("city_lagos","region_lagos_st"),("city_london","region_london"),
        ("city_paris","region_idf"),("city_rome","region_lazio"),
        ("city_barcelona","region_catalonia"),("city_tokyo","region_kanto"),
    ]:
        _e(g, cty, "City", IR, reg, "Region")

    # City → Weather
    for w, cty in [
        ("w_lag_1","city_lagos"),("w_lag_7","city_lagos"),("w_lag_12","city_lagos"),
        ("w_lon_4","city_london"),("w_lon_7","city_london"),("w_lon_12","city_london"),
        ("w_par_4","city_paris"),("w_par_7","city_paris"),("w_par_12","city_paris"),
        ("w_dxb_1","city_dubai"),("w_dxb_7","city_dubai"),("w_dxb_11","city_dubai"),
        ("w_ny_4","city_new_york"),("w_ny_7","city_new_york"),("w_ny_12","city_new_york"),
        ("w_rom_4","city_rome"),("w_rom_7","city_rome"),("w_rom_10","city_rome"),
        ("w_bcn_4","city_barcelona"),("w_bcn_7","city_barcelona"),("w_bcn_10","city_barcelona"),
        ("w_tok_4","city_tokyo"),("w_tok_7","city_tokyo"),("w_tok_12","city_tokyo"),
        ("w_cpt_1","city_cape_town"),("w_cpt_7","city_cape_town"),
    ]:
        _e(g, cty, "City", HW, w, "Weather")

    # City → TravelSeason
    for season_id, city_ids in [
        ("season_eur_summer",  ["city_london","city_paris","city_rome","city_barcelona"]),
        ("season_eur_spring",  ["city_london","city_paris","city_rome","city_barcelona"]),
        ("season_eur_winter",  ["city_london","city_paris","city_rome"]),
        ("season_dxb_cool",    ["city_dubai"]),
        ("season_dxb_hot",     ["city_dubai"]),
        ("season_ng_harmattan",["city_lagos","city_accra"]),
    ]:
        for cty in city_ids:
            _e(g, cty, "City", HS, season_id, "TravelSeason")
