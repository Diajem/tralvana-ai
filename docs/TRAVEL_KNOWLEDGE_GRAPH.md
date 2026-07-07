# Travel Knowledge Graph

The TravelOS Knowledge Graph is an in-memory property graph connecting all travel entities through typed relationships. It powers all six reasoning services and the Traveller DNA inference system.

## Package

```
ai/intelligence/knowledge/
├── entities.py          # 20 entity dataclasses (the node types)
├── relationships.py     # RelationshipType enum (22 types) + Relationship dataclass
├── knowledge_graph.py   # KnowledgeGraph — the graph engine
└── knowledge_service.py # KnowledgeService — the public facade
```

## Entity Types (20)

| Entity | Key Fields |
|--------|-----------|
| `Country` | iso_code, continent, safety_level, language_codes, currency_code |
| `City` | country_id, region_id, timezone, tags |
| `Airport` | iata_code, city_id, is_international |
| `Hotel` | star_rating, price_tier, amenities |
| `Airline` | iata_code, hub_airport_id, tier, alliance |
| `RailStation` | city_id, station_code, is_high_speed |
| `Restaurant` | city_id, cuisine_id, price_tier, tags |
| `Cuisine` | origin_country_iso, tags |
| `Museum` | city_id, category, tags |
| `Attraction` | city_id, attraction_type, tags |
| `FootballClub` | city_id, league, stadium_id, founded_year |
| `SportsVenue` | city_id, venue_type, capacity, primary_sport |
| `Event` | city_id, event_type, month, tags |
| `Weather` | city_id, month, avg_temp_c, condition, season |
| `Transport` | city_id, transport_type |
| `VisaRequirement` | from_country_iso, to_country_iso, requirement, max_stay_days |
| `Currency` | code, symbol, country_isos |
| `Language` | iso_code, native_name, speakers_millions |
| `Region` | country_id, region_type, tags |
| `TravelSeason` | season_type, months, city_ids, characteristics |

Plus `TravellerDNA` — a graph node representing an inferred traveller archetype.

## Relationship Types (22)

| Relationship | Example |
|-------------|---------|
| `LOCATED_IN` | Hotel → City; City → Country |
| `BELONGS_TO` | Restaurant → City; Transport → City |
| `SERVES` | Airport → City; Restaurant → Cuisine |
| `PLAYS_IN` | FootballClub → City |
| `PLAYS_AT` | FootballClub → SportsVenue |
| `HOSTS` | City → SportsVenue |
| `OPERATES_FROM` | Airline → Airport (hub) |
| `USES_CURRENCY` | Country → Currency |
| `SPEAKS` | Country → Language |
| `HAS_REGION` | Country → Region |
| `IN_REGION` | City → Region |
| `HAS_WEATHER` | City → Weather |
| `HAS_SEASON` | City → TravelSeason |
| `NEAR` | Attraction → City |
| `PART_OF` | Event → City |
| `CONNECTS` | RailStation → City |
| `REQUIRES_VISA` | Country → Country |
| `HAS_DNA` | Traveller → TravellerDNA |
| `INTERESTED_IN` | Traveller → Interest |
| `VISITED` | Traveller → City |
| `PREFERS` | Traveller → Airline |
| `VISITS` | Trip → City |

## KnowledgeService API

```python
from ai.intelligence import knowledge_service

# Load all entities of a type
cities = knowledge_service.load_entities("City")

# Find by name
paris = knowledge_service.find_entity("City", "Paris")

# Find relationships
edges = knowledge_service.find_relationships(paris.id, RelationshipType.HAS_WEATHER, direction="outbound")

# Get connected entities
hotels = knowledge_service.get_connected_entities(paris.id, "Hotel", RelationshipType.LOCATED_IN, "inbound")

# Expand neighbourhood
subgraph = knowledge_service.expand_graph(paris.id, depth=2)

# Add runtime entities (e.g., from user profile)
knowledge_service.add_entity(my_entity, "City")

# Stats
print(knowledge_service.get_stats())
# → {"total_nodes": 210, "total_edges": 195, "nodes_by_type": {...}}
```

## Sprint 1 Coverage

| Entity | Count |
|--------|-------|
| Countries | 10 |
| Cities | 11 |
| Airports | 11 |
| Rail Stations | 6 |
| Airlines | 8 |
| Hotels | 16 |
| Cuisines | 8 |
| Restaurants | 8 |
| Attractions | 15 |
| Museums | 10 |
| Football Clubs | 8 |
| Sports Venues | 8 |
| Events | 8 |
| Transport systems | 6 |
| Visa requirements | 12 |
| Currencies | 8 |
| Languages | 8 |
| Regions | 6 |
| Travel Seasons | 6 |
| Weather records | 26 |

## Graph DB Migration (Sprint 4)

The `KnowledgeService` and `KnowledgeGraph` are the only two classes that need replacing when migrating to Neo4j or Kuzu. All 6 reasoners call `KnowledgeService` — they require no changes.

Recommended path: **Kuzu** (MIT-licensed, embeddable, Cypher-compatible, no server required).
