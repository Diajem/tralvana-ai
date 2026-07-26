from __future__ import annotations

from ai.intelligence.knowledge.entities import Attraction, City
from ai.intelligence.knowledge.factory import build_knowledge_graph
from ai.intelligence.knowledge.knowledge_graph import KnowledgeGraph
from ai.intelligence.knowledge.knowledge_service import KnowledgeService
from ai.intelligence.knowledge.relationships import Relationship, RelationshipType
from ai.intelligence.knowledge.sql_knowledge_graph import SqlAlchemyKnowledgeGraph
from ai.intelligence.ontology.travel_ontology import seed_graph
from travelos.persistence.base import Base
from travelos.persistence.session import create_engine_from_url, create_session_factory


def _persistent_graph(tmp_path):
    engine = create_engine_from_url(
        f"sqlite+pysqlite:///{tmp_path / 'knowledge.db'}"
    )
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    return engine, factory, SqlAlchemyKnowledgeGraph(factory)


def _baseline() -> KnowledgeGraph:
    graph = KnowledgeGraph()
    seed_graph(graph)
    return graph


def test_factory_preserves_zero_setup_in_memory_graph():
    graph = build_knowledge_graph(None)

    assert isinstance(graph, KnowledgeGraph)
    assert graph.stats() == _baseline().stats()


def test_factory_selects_and_seeds_sql_backend_when_configured(tmp_path):
    database_path = tmp_path / "factory.db"
    url = f"sqlite+pysqlite:///{database_path}"
    engine = create_engine_from_url(url)
    Base.metadata.create_all(engine)
    engine.dispose()

    graph = build_knowledge_graph(url)

    assert isinstance(graph, SqlAlchemyKnowledgeGraph)
    assert graph.stats() == _baseline().stats()


def test_seed_persists_complete_graph_across_instances(tmp_path):
    engine, factory, graph = _persistent_graph(tmp_path)
    graph.seed_from(_baseline())

    reloaded = SqlAlchemyKnowledgeGraph(factory)

    assert reloaded.stats() == _baseline().stats()
    assert reloaded.find_node_by_name("City", "New York").id == "city_new_york"
    assert reloaded.get_node_type("city_new_york") == "City"
    engine.dispose()


def test_reseeding_is_idempotent_and_updates_node_payloads(tmp_path):
    engine, factory, graph = _persistent_graph(tmp_path)
    baseline = _baseline()
    graph.seed_from(baseline)
    graph.seed_from(baseline)

    updated = City(
        id="city_new_york",
        name="New York",
        country_id="country_us",
        timezone="America/New_York",
        population=9_000_000,
        tags=["urban", "fashion"],
    )
    graph.add_node(updated, "City")

    reloaded = SqlAlchemyKnowledgeGraph(factory)
    assert reloaded.stats() == baseline.stats()
    assert reloaded.get_node("city_new_york") == updated
    engine.dispose()


def test_runtime_entity_and_relationship_survive_process_boundary(tmp_path):
    engine, factory, graph = _persistent_graph(tmp_path)
    graph.seed_from(_baseline())
    attraction = Attraction(
        id="attr_test_gallery",
        name="Test Gallery",
        city_id="city_new_york",
        attraction_type="cultural",
        tags=["fashion"],
    )
    relationship = Relationship(
        source_id=attraction.id,
        source_type="Attraction",
        relationship_type=RelationshipType.NEAR,
        target_id="city_new_york",
        target_type="City",
        metadata={"source": "test"},
    )
    graph.add_node(attraction, "Attraction")
    graph.add_edge(relationship)

    service = KnowledgeService(SqlAlchemyKnowledgeGraph(factory))
    connected = service.get_connected_entities(
        "city_new_york",
        target_type="Attraction",
        rel_type=RelationshipType.NEAR,
        direction="inbound",
    )

    assert attraction in connected
    assert service.find_entity_by_id(attraction.id) == attraction
    engine.dispose()


def test_exact_duplicate_relationships_are_idempotent(tmp_path):
    engine, _, graph = _persistent_graph(tmp_path)
    graph.seed_from(_baseline())
    edge = Relationship(
        source_id="attr_empire",
        source_type="Attraction",
        relationship_type=RelationshipType.NEAR,
        target_id="city_new_york",
        target_type="City",
    )
    before = graph.stats()["total_edges"]

    graph.add_edge(edge)
    graph.add_edge(edge)

    assert graph.stats()["total_edges"] == before
    engine.dispose()


def test_search_traversal_and_neighbourhood_match_contract(tmp_path):
    engine, _, graph = _persistent_graph(tmp_path)
    graph.seed_from(_baseline())

    assert [city.name for city in graph.search_nodes("City", "new")] == [
        "New York"
    ]
    assert graph.find_nodes("City", country_id="COUNTRY_US")[0].name == "New York"
    located = graph.traverse(
        "city_london",
        RelationshipType.HOSTS,
        depth=1,
    )
    neighbourhood = graph.neighbourhood("city_new_york", depth=1)

    assert located
    assert any(venue.name == "Emirates Stadium" for venue in located)
    assert "NEAR" in neighbourhood
    engine.dispose()
