"""Knowledge graph construction for local and persistent environments."""

from __future__ import annotations

from ai.intelligence.knowledge.knowledge_graph import KnowledgeGraph
from ai.intelligence.knowledge.sql_knowledge_graph import SqlAlchemyKnowledgeGraph
from ai.intelligence.ontology.travel_ontology import seed_graph
from travelos.persistence.session import create_engine_from_url, create_session_factory


def build_knowledge_graph(
    configured_database_url: str | None,
) -> KnowledgeGraph | SqlAlchemyKnowledgeGraph:
    """Build the seeded in-memory graph or its SQL-backed equivalent."""
    baseline = KnowledgeGraph()
    seed_graph(baseline)
    if not configured_database_url:
        return baseline

    engine = create_engine_from_url(configured_database_url)
    graph = SqlAlchemyKnowledgeGraph(create_session_factory(engine))
    graph.seed_from(baseline)
    return graph
