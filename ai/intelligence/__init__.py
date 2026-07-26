from ai.intelligence.knowledge.factory import build_knowledge_graph
from ai.intelligence.knowledge.knowledge_service import KnowledgeService
from ai.intelligence.traveller_dna.dna_classifier import TravellerDNAInferenceService
from travelos.persistence.session import database_url

_graph = build_knowledge_graph(database_url())

knowledge_service = KnowledgeService(_graph)
dna_inference_service = TravellerDNAInferenceService()
