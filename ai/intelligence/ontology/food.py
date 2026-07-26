"""Cuisine and restaurant seed data."""

from ai.intelligence.knowledge.entities import Cuisine, Restaurant
from ai.intelligence.ontology.seed_helpers import add_node as _n


def _cuisines(g) -> None:
    for c in [
        Cuisine(
            "cuisine_nigerian",
            "Nigerian",
            "NG",
            ["spicy", "stew", "halal-options", "rice-based"],
        ),
        Cuisine("cuisine_british", "British", "GB", ["meat", "pub-style", "mild"]),
        Cuisine(
            "cuisine_french",
            "French",
            "FR",
            ["wine", "cheese", "fine-dining", "sauces"],
        ),
        Cuisine(
            "cuisine_italian", "Italian", "IT", ["pasta", "pizza", "gelato", "wine"]
        ),
        Cuisine(
            "cuisine_spanish", "Spanish", "ES", ["tapas", "seafood", "paella", "jamón"]
        ),
        Cuisine(
            "cuisine_japanese",
            "Japanese",
            "JP",
            ["sushi", "ramen", "umami", "vegetarian-friendly"],
        ),
        Cuisine(
            "cuisine_american",
            "American",
            "US",
            ["burgers", "bbq", "portions-large", "diverse"],
        ),
        Cuisine(
            "cuisine_arab", "Arab/Levantine", "AE", ["halal", "rice", "lamb", "mezze"]
        ),
    ]:
        _n(g, c, "Cuisine")


def _restaurants(g) -> None:
    for r in [
        Restaurant(
            "rest_nok",
            "Nok by Alara",
            "city_lagos",
            "cuisine_nigerian",
            "luxury",
            ["fine-dining", "afro-fusion"],
        ),
        Restaurant(
            "rest_sketch",
            "Sketch",
            "city_london",
            "cuisine_british",
            "luxury",
            ["fine-dining", "afternoon-tea"],
        ),
        Restaurant(
            "rest_ledou",
            "Le Doyen",
            "city_paris",
            "cuisine_french",
            "luxury",
            ["michelin", "fine-dining"],
        ),
        Restaurant(
            "rest_nobu_dxb",
            "Nobu Dubai",
            "city_dubai",
            "cuisine_japanese",
            "luxury",
            ["fusion", "sushi"],
        ),
        Restaurant(
            "rest_eleven",
            "Eleven Madison Park",
            "city_new_york",
            "cuisine_american",
            "luxury",
            ["michelin", "plant-based"],
        ),
        Restaurant(
            "rest_roscioli",
            "Roscioli",
            "city_rome",
            "cuisine_italian",
            "mid-range",
            ["pasta", "wine", "local"],
        ),
        Restaurant(
            "rest_tickets",
            "Tickets",
            "city_barcelona",
            "cuisine_spanish",
            "luxury",
            ["tapas", "avant-garde"],
        ),
        Restaurant(
            "rest_sushi_s",
            "Sushi Saito",
            "city_tokyo",
            "cuisine_japanese",
            "luxury",
            ["omakase", "michelin"],
        ),
    ]:
        _n(g, r, "Restaurant")
