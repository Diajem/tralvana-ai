# Travel Knowledge Graph

The TravelOS Knowledge Graph is an in-memory property graph that connects all travel entities — countries, cities, airports, hotels, airlines, attractions, restaurants, museums, football clubs, events, transport systems, visa requirements, currencies, and weather records — through typed relationships.

## Architecture

```
knowledge/
├── __init__.py                  # Creates and seeds the default graph singleton
├── graph/
│   ├── entities.py              # 16 entity dataclasses (the node types)
│   ├── relationships.py         # RelationshipType enum + Relationship dataclass
│   └── knowledge_graph.py       # KnowledgeGraph class (the engine)
├── ontology/
│   ├── travel_ontology.py       # Seed data — countries, cities, airports, etc.
│   └── dna_classifier.py        # Traveller DNA inference service
└── reasoning/
    ├── destination_reasoner.py  # Aggregate destination knowledge
    ├── budget_reasoner.py       # Cost estimation
    ├── experience_reasoner.py   # Interest-matched experiences
    └── timeline_reasoner.py     # Best time to visit + weather
```

## Entity Types (Nodes)

| Entity | Key Fields | Description |
|--------|-----------|-------------|
| `Country` | iso_code, continent, safety_level | National entity with language/currency links |
| `City` | country_id, timezone, tags | Urban destination with descriptive tags |
| `Airport` | iata_code, city_id, is_international | Entry/exit point for flights |
| `Hotel` | star_rating, price_tier, amenities | Accommodation with tier classification |
| `Airline` | iata_code, hub_airport_id, tier | Carrier with hub and service tier |
| `Attraction` | attraction_type, tags | Sightseeing point with type and interest tags |
| `Restaurant` | cuisine, price_tier, tags | Dining venue with cuisine and budget info |
| `Museum` | category, tags | Cultural institution |
| `Sport` | category | Sport classification |
| `FootballClub` | league, stadium, founded_year | Football club with stadium and league |
| `Event` | event_type, month, tags | Festival, concert, or sporting event |
| `Transport` | transport_type, city_id | Local transport system |
| `VisaRequirement` | from_country_iso, to_country_iso, requirement | Visa rules between country pairs |
| `Currency` | code, symbol, country_isos | ISO 4217 currency with linked countries |
| `Weather` | month, avg_temp_c, condition, season | Monthly weather profile for a city |
| `TravellerDNA` | primary_type, secondary_types, traits | Inferred traveller archetype |

## Relationship Types (Edges)

| Relationship | From → To | Meaning |
|-------------|-----------|---------|
| `LOCATED_IN` | City→Country, Airport→City, Museum→City | Spatial containment |
| `BELONGS_TO` | Hotel→City, FootballClub→City, Restaurant→City | Membership |
| `OPERATES_FROM` | Airline→Airport | Hub airport |
| `USES_CURRENCY` | Country→Currency | Currency used |
| `HAS_WEATHER` | City→Weather | Monthly weather record |
| `NEAR` | Attraction→City | Attraction located near city |
| `PART_OF` | Event→City | Event held in city |
| `HAS_DNA` | Traveller→TravellerDNA | DNA inference link |
| `REQUIRES_VISA` | Country→Country | Visa requirement between nations |

## KnowledgeGraph API

```python
from knowledge import knowledge_graph

# Node lookup
city = knowledge_graph.find_node_by_name("City", "London")
hotel = knowledge_graph.get_node("hotel_ritz")
hotels = knowledge_graph.get_nodes_by_type("Hotel")

# Edge traversal
edges = knowledge_graph.get_outbound_edges("city_london", RelationshipType.HAS_WEATHER)
nearby = knowledge_graph.traverse("city_london", RelationshipType.NEAR, depth=1)

# Stats
print(knowledge_graph.stats())
# → {"total_nodes": 120, "total_edges": 180, "nodes_by_type": {...}}
```

## Sprint 1 Coverage

| Entity | Count |
|--------|-------|
| Countries | 10 |
| Cities | 11 |
| Airports | 11 |
| Airlines | 8 |
| Hotels | 16 |
| Attractions | 15 |
| Museums | 10 |
| Restaurants | 8 |
| Football Clubs | 8 |
| Events | 8 |
| Transport systems | 6 |
| Visa requirements | 12 |
| Currencies | 8 |
| Weather records | 25 |

## Future Graph Database Migration

The `KnowledgeGraph` class exposes a stable interface. Sprint 4 migration plan:

1. Replace `KnowledgeGraph` implementation with a Neo4j/ArangoDB/Memgraph driver
2. Move `seed_graph()` to a database seeding script
3. All call sites in reasoners and agents remain unchanged — no refactor required
