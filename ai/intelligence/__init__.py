from ai.intelligence.knowledge.knowledge_graph import KnowledgeGraph
from ai.intelligence.knowledge.knowledge_service import KnowledgeService
from ai.intelligence.ontology.travel_ontology import seed_graph
from ai.intelligence.traveller_dna.dna_classifier import TravellerDNAInferenceService

_graph = KnowledgeGraph()
seed_graph(_graph)

knowledge_service = KnowledgeService(_graph)
dna_inference_service = TravellerDNAInferenceService()
