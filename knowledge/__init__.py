from knowledge.graph.knowledge_graph import KnowledgeGraph

knowledge_graph = KnowledgeGraph()

from knowledge.ontology.travel_ontology import seed_graph  # noqa: E402
seed_graph(knowledge_graph)
