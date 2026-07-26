"""Visa, weather, and travel-season seed data."""

from ai.intelligence.knowledge.entities import TravelSeason, VisaRequirement, Weather
from ai.intelligence.ontology.seed_helpers import add_node as _n


def _visa_requirements(g) -> None:
    for v in [
        VisaRequirement(
            "visa_ng_gb",
            "NG",
            "GB",
            "required",
            None,
            "Apply via UK Visas and Immigration",
        ),
        VisaRequirement(
            "visa_ng_fr", "NG", "FR", "required", None, "Schengen visa required"
        ),
        VisaRequirement(
            "visa_ng_ae",
            "NG",
            "AE",
            "visa-on-arrival",
            30,
            "30-day VOA at Dubai Airport",
        ),
        VisaRequirement(
            "visa_ng_us", "NG", "US", "required", None, "B1/B2 non-immigrant visa"
        ),
        VisaRequirement(
            "visa_ng_it", "NG", "IT", "required", None, "Schengen visa required"
        ),
        VisaRequirement(
            "visa_gb_fr",
            "GB",
            "FR",
            "required",
            180,
            "UK nationals need ETA post-Brexit",
        ),
        VisaRequirement(
            "visa_gb_ae", "GB", "AE", "visa-free", 90, "90-day visa-free entry"
        ),
        VisaRequirement(
            "visa_gb_us", "GB", "US", "visa-free", 90, "ESTA required — apply online"
        ),
        VisaRequirement("visa_gb_jp", "GB", "JP", "visa-free", 90, "90-day visa-free"),
        VisaRequirement(
            "visa_us_gb", "US", "GB", "visa-free", 180, "eTA required from 2025"
        ),
        VisaRequirement(
            "visa_us_fr", "US", "FR", "visa-free", 90, "ETIAS required from 2025"
        ),
        VisaRequirement("visa_us_ae", "US", "AE", "visa-free", 30, "30-day visa-free"),
    ]:
        _n(g, v, "VisaRequirement")


def _weather(g) -> None:
    for w in [
        Weather("w_lag_1", "city_lagos", 1, 28.0, "sunny", "dry"),
        Weather("w_lag_7", "city_lagos", 7, 25.0, "rainy", "wet"),
        Weather("w_lag_12", "city_lagos", 12, 29.0, "sunny", "dry"),
        Weather("w_lon_4", "city_london", 4, 11.0, "partly-cloudy", "spring"),
        Weather("w_lon_7", "city_london", 7, 20.0, "sunny", "summer"),
        Weather("w_lon_12", "city_london", 12, 6.0, "cold", "winter"),
        Weather("w_par_4", "city_paris", 4, 13.0, "partly-cloudy", "spring"),
        Weather("w_par_7", "city_paris", 7, 24.0, "sunny", "summer"),
        Weather("w_par_12", "city_paris", 12, 5.0, "cold", "winter"),
        Weather("w_dxb_1", "city_dubai", 1, 22.0, "sunny", "mild"),
        Weather("w_dxb_7", "city_dubai", 7, 41.0, "hot", "summer"),
        Weather("w_dxb_11", "city_dubai", 11, 28.0, "sunny", "autumn"),
        Weather("w_ny_4", "city_new_york", 4, 13.0, "partly-cloudy", "spring"),
        Weather("w_ny_7", "city_new_york", 7, 28.0, "humid", "summer"),
        Weather("w_ny_12", "city_new_york", 12, 3.0, "cold", "winter"),
        Weather("w_rom_4", "city_rome", 4, 16.0, "sunny", "spring"),
        Weather("w_rom_7", "city_rome", 7, 31.0, "hot", "summer"),
        Weather("w_rom_10", "city_rome", 10, 18.0, "partly-cloudy", "autumn"),
        Weather("w_bcn_4", "city_barcelona", 4, 16.0, "sunny", "spring"),
        Weather("w_bcn_7", "city_barcelona", 7, 27.0, "hot", "summer"),
        Weather("w_bcn_10", "city_barcelona", 10, 19.0, "partly-cloudy", "autumn"),
        Weather("w_tok_4", "city_tokyo", 4, 15.0, "sunny", "spring"),
        Weather("w_tok_7", "city_tokyo", 7, 29.0, "humid", "summer"),
        Weather("w_tok_12", "city_tokyo", 12, 8.0, "cold", "winter"),
        Weather("w_cpt_1", "city_cape_town", 1, 26.0, "sunny", "summer"),
        Weather("w_cpt_7", "city_cape_town", 7, 13.0, "rainy", "winter"),
    ]:
        _n(g, w, "Weather")


def _travel_seasons(g) -> None:
    for s in [
        TravelSeason(
            "season_eur_summer",
            "European Peak Summer",
            "peak",
            [6, 7, 8],
            ["city_london", "city_paris", "city_rome", "city_barcelona"],
            ["crowd-high", "prices-high", "weather-ideal", "long-days"],
        ),
        TravelSeason(
            "season_eur_spring",
            "European Spring Shoulder",
            "shoulder",
            [4, 5],
            ["city_london", "city_paris", "city_rome", "city_barcelona"],
            ["crowd-moderate", "prices-moderate", "weather-pleasant", "cherry-blossom"],
        ),
        TravelSeason(
            "season_eur_winter",
            "European Off-Peak Winter",
            "off-peak",
            [11, 12, 1, 2],
            ["city_london", "city_paris", "city_rome"],
            ["crowd-low", "prices-low", "cold", "christmas-markets"],
        ),
        TravelSeason(
            "season_dxb_cool",
            "Dubai Cool Season",
            "peak",
            [10, 11, 12, 1, 2, 3],
            ["city_dubai"],
            ["weather-ideal", "crowd-high", "prices-high", "outdoor-events"],
        ),
        TravelSeason(
            "season_dxb_hot",
            "Dubai Summer Heat",
            "off-peak",
            [6, 7, 8],
            ["city_dubai"],
            ["weather-harsh", "prices-low", "indoor-focus", "prices-low"],
        ),
        TravelSeason(
            "season_ng_harmattan",
            "West Africa Harmattan",
            "harmattan",
            [11, 12, 1, 2],
            ["city_lagos", "city_accra"],
            ["dry", "dusty", "mild-evenings", "haze"],
        ),
    ]:
        _n(g, s, "TravelSeason")
