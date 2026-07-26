"""Airport, railway, airline, and accommodation seed data."""

from ai.intelligence.knowledge.entities import Airline, Airport, Hotel, RailStation
from ai.intelligence.ontology.seed_helpers import add_node as _n


def _airports(g) -> None:
    for a in [
        Airport("airport_los", "Murtala Muhammed Intl", "LOS", "city_lagos", True),
        Airport("airport_abv", "Nnamdi Azikiwe Intl", "ABV", "city_abuja", True),
        Airport("airport_lhr", "Heathrow", "LHR", "city_london", True),
        Airport("airport_cdg", "Charles de Gaulle", "CDG", "city_paris", True),
        Airport("airport_dxb", "Dubai International", "DXB", "city_dubai", True),
        Airport("airport_jfk", "JFK International", "JFK", "city_new_york", True),
        Airport("airport_fco", "Fiumicino", "FCO", "city_rome", True),
        Airport("airport_bcn", "El Prat", "BCN", "city_barcelona", True),
        Airport("airport_nrt", "Narita International", "NRT", "city_tokyo", True),
        Airport("airport_acc", "Kotoka International", "ACC", "city_accra", True),
        Airport(
            "airport_cpt", "Cape Town International", "CPT", "city_cape_town", True
        ),
    ]:
        _n(g, a, "Airport")


def _rail_stations(g) -> None:
    for s in [
        RailStation(
            "rail_stpancras", "London St Pancras Intl", "city_london", "STP", True
        ),
        RailStation("rail_euston", "London Euston", "city_london", "EUS", False),
        RailStation("rail_gdnord", "Paris Gare du Nord", "city_paris", "GDN", True),
        RailStation("rail_termini", "Roma Termini", "city_rome", "RZT", False),
        RailStation("rail_sants", "Barcelona Sants", "city_barcelona", "BRC", True),
        RailStation("rail_shinjuku", "Tokyo Shinjuku", "city_tokyo", "SJK", True),
    ]:
        _n(g, s, "RailStation")


def _airlines(g) -> None:
    for a in [
        Airline(
            "airline_ba", "British Airways", "BA", "airport_lhr", "premium", "OneWorld"
        ),
        Airline("airline_af", "Air France", "AF", "airport_cdg", "premium", "SkyTeam"),
        Airline("airline_ek", "Emirates", "EK", "airport_dxb", "luxury", ""),
        Airline(
            "airline_dl", "Delta Air Lines", "DL", "airport_jfk", "economy", "SkyTeam"
        ),
        Airline("airline_az", "ITA Airways", "AZ", "airport_fco", "economy", "SkyTeam"),
        Airline("airline_nh", "ANA", "NH", "airport_nrt", "premium", "Star Alliance"),
        Airline(
            "airline_qr", "Qatar Airways", "QR", "airport_dxb", "luxury", "OneWorld"
        ),
        Airline("airline_w3", "Arik Air", "W3", "airport_los", "economy", ""),
    ]:
        _n(g, a, "Airline")


def _hotels(g) -> None:
    for h in [
        Hotel(
            "hotel_eko",
            "Eko Hotels & Suites",
            "city_lagos",
            5,
            "luxury",
            ["pool", "spa", "wifi", "gym"],
        ),
        Hotel(
            "hotel_radisson_ng",
            "Radisson Blu Lagos",
            "city_lagos",
            4,
            "mid-range",
            ["wifi", "gym", "restaurant"],
        ),
        Hotel(
            "hotel_ritz",
            "The Ritz London",
            "city_london",
            5,
            "luxury",
            ["spa", "wifi", "pool", "restaurant"],
        ),
        Hotel(
            "hotel_premier_lon",
            "Premier Inn London",
            "city_london",
            3,
            "mid-range",
            ["wifi", "breakfast"],
        ),
        Hotel(
            "hotel_le_meurice",
            "Le Meurice",
            "city_paris",
            5,
            "luxury",
            ["spa", "wifi", "restaurant"],
        ),
        Hotel(
            "hotel_ibis_paris", "Ibis Paris Centre", "city_paris", 2, "budget", ["wifi"]
        ),
        Hotel(
            "hotel_atlantis",
            "Atlantis The Palm",
            "city_dubai",
            5,
            "luxury",
            ["pool", "beach", "spa", "gym"],
        ),
        Hotel(
            "hotel_premier_dxb",
            "Premier Inn Dubai",
            "city_dubai",
            4,
            "mid-range",
            ["pool", "wifi", "gym"],
        ),
        Hotel(
            "hotel_plaza",
            "The Plaza Hotel",
            "city_new_york",
            5,
            "luxury",
            ["spa", "wifi", "restaurant"],
        ),
        Hotel(
            "hotel_citizenm",
            "citizenM New York",
            "city_new_york",
            4,
            "mid-range",
            ["wifi", "gym"],
        ),
        Hotel(
            "hotel_cavalieri",
            "Rome Cavalieri",
            "city_rome",
            5,
            "luxury",
            ["pool", "spa", "wifi"],
        ),
        Hotel(
            "hotel_hotel_art",
            "Hotel Art Rome",
            "city_rome",
            4,
            "mid-range",
            ["wifi", "breakfast"],
        ),
        Hotel(
            "hotel_arts",
            "Hotel Arts Barcelona",
            "city_barcelona",
            5,
            "luxury",
            ["pool", "beach", "spa"],
        ),
        Hotel(
            "hotel_catalonia",
            "Catalonia Barcelona",
            "city_barcelona",
            3,
            "mid-range",
            ["wifi", "breakfast"],
        ),
        Hotel(
            "hotel_palace_tok",
            "Palace Hotel Tokyo",
            "city_tokyo",
            5,
            "luxury",
            ["spa", "pool", "wifi"],
        ),
        Hotel(
            "hotel_dormy",
            "Dormy Inn Tokyo",
            "city_tokyo",
            3,
            "mid-range",
            ["wifi", "breakfast"],
        ),
    ]:
        _n(g, h, "Hotel")
