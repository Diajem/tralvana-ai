"""Deterministic seed entry point for the TravelOS Knowledge Graph.

The public ``seed_graph`` facade is intentionally stable. Seed definitions are
grouped into small domain modules so ontology maintenance does not require one
1,400-line file.
"""

from ai.intelligence.ontology.experiences import (
    _attractions,
    _events,
    _football_clubs,
    _museums,
    _sports_venues,
    _transport,
)
from ai.intelligence.ontology.food import _cuisines, _restaurants
from ai.intelligence.ontology.geography import (
    _cities,
    _countries,
    _currencies,
    _languages,
    _regions,
)
from ai.intelligence.ontology.mobility_lodging import (
    _airlines,
    _airports,
    _hotels,
    _rail_stations,
)
from ai.intelligence.ontology.seed_relationships import _relationships
from ai.intelligence.ontology.travel_requirements import (
    _travel_seasons,
    _visa_requirements,
    _weather,
)


def seed_graph(graph: object) -> None:
    _currencies(graph)
    _languages(graph)
    _countries(graph)
    _regions(graph)
    _cities(graph)
    _airports(graph)
    _rail_stations(graph)
    _airlines(graph)
    _hotels(graph)
    _cuisines(graph)
    _restaurants(graph)
    _sports_venues(graph)
    _football_clubs(graph)
    _attractions(graph)
    _museums(graph)
    _events(graph)
    _transport(graph)
    _visa_requirements(graph)
    _weather(graph)
    _travel_seasons(graph)
    _relationships(graph)
