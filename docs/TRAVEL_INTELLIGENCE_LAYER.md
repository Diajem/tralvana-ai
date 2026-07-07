# Travel Intelligence Layer (TIL)

The Travel Intelligence Layer is TravelOS's foundational AI reasoning system. It makes TravelOS think like an experienced travel consultant rather than a search engine — reasoning using relationships between entities instead of matching isolated facts.

## Overview

```
ai/intelligence/
├── knowledge/           # Knowledge Graph (entities + relationships + engine + service)
├── ontology/            # Seed data (countries, cities, hotels, cuisines, seasons, ...)
├── traveller_dna/       # Traveller archetype inference (12 DNA types)
└── reasoning/           # 6 reasoning services with consistent interface
```

## Layers

### 1. Knowledge Graph (`knowledge/`)

An in-memory property graph storing 20 entity types and 22 relationship types. The graph is seeded on import from `ontology/travel_ontology.py`.

Sprint 1 coverage: ~200 nodes, ~200 edges across 11 cities and 10 countries.

**Interface entry point:** `KnowledgeService` — callers never interact with the raw `KnowledgeGraph` directly.

### 2. Ontology (`ontology/`)

Controlled vocabulary definitions and Sprint 1 seed data. The ontology defines:
- All 20 entity types and their field vocabularies
- 22 relationship types and their semantics
- Seed data for 10 countries, 11 cities, 11 airports, 6 rail stations, 8 cuisines, 6 travel seasons, and more

### 3. Traveller DNA (`traveller_dna/`)

Deterministic inference of a traveller's primary travel archetype from their TIP profile.

12 DNA types: Explorer, Luxury Traveller, Budget Traveller, Football Traveller, Food Traveller, Photography Traveller, Family Traveller, Business Traveller, Adventure Traveller, Digital Nomad, Pilgrimage Traveller, Diaspora Traveller.

### 4. Reasoning Layer (`reasoning/`)

Six services that answer specific travel intelligence questions using graph knowledge:

| Service | Question |
|---------|----------|
| `DestinationReasoner` | "What do I need to know about X?" |
| `ExperienceReasoner` | "What should I do/eat/see in X given my interests?" |
| `BudgetReasoner` | "How much will a trip to X cost me?" |
| `TimelineReasoner` | "When is the best time to visit X?" |
| `SeasonReasoner` | "What season is X in right now and how does that affect my trip?" |
| `SafetyReasoner` | "Is it safe to travel to X? Do I need a visa?" |

All reasoners expose a consistent `reason(**kwargs) -> ReasoningResult` interface.

## Using the TIL

```python
from ai.intelligence import knowledge_service, dna_inference_service
from ai.intelligence.reasoning.destination_reasoner import destination_reasoner
from ai.intelligence.reasoning.safety_reasoner import safety_reasoner

# Graph queries via KnowledgeService
london = knowledge_service.find_entity("City", "London")
expanded = knowledge_service.expand_graph(london.id, depth=2)

# DNA inference
dna = dna_inference_service.infer({
    "id": "traveller_abc",
    "preferences": {
        "budget_style": "luxury",
        "cabin_class": "first",
        "travel_interests": ["luxury", "culture", "food_drink"],
    }
})
# dna.primary_type → "Luxury Traveller"

# Reasoning
result = destination_reasoner.reason("Paris")
result = safety_reasoner.reason("Lagos", passport_country_iso="GB")
```

## Sprint Roadmap

| Sprint | Enhancement |
|--------|-------------|
| 1 (current) | In-memory graph, static seed data, rule-based DNA, 6 reasoners |
| 2 | Expand to 50+ cities; add live weather API integration |
| 3 | ML-ranked experiences; DNA trained on trip history |
| 4 | Graph DB migration (Kuzu / Neo4j); real-time advisories |
