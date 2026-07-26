from pathlib import Path

from ai.intelligence.knowledge.knowledge_graph import KnowledgeGraph
from ai.intelligence.ontology.travel_ontology import seed_graph


def test_split_ontology_preserves_complete_seed_graph():
    graph = KnowledgeGraph()

    seed_graph(graph)

    assert graph.stats() == {
        "total_nodes": 199,
        "total_edges": 205,
        "nodes_by_type": {
            "Currency": 8,
            "Language": 8,
            "Country": 10,
            "Region": 6,
            "City": 11,
            "Airport": 11,
            "RailStation": 6,
            "Airline": 8,
            "Hotel": 16,
            "Cuisine": 8,
            "Restaurant": 8,
            "SportsVenue": 8,
            "FootballClub": 8,
            "Attraction": 15,
            "Museum": 10,
            "Event": 8,
            "Transport": 6,
            "VisaRequirement": 12,
            "Weather": 26,
            "TravelSeason": 6,
        },
    }


def test_ontology_modules_stay_within_repository_file_limit():
    ontology_directory = Path(__file__).parents[1] / "intelligence" / "ontology"

    oversized = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in ontology_directory.glob("*.py")
        if len(path.read_text(encoding="utf-8").splitlines()) > 500
    }

    assert oversized == {}
