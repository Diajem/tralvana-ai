# ADR-002: Travel Intelligence Layer — In-Memory Property Graph

**Status:** Accepted  
**Date:** 2026-07-07  
**Supersedes:** ADR-002-knowledge-graph.md (Sprint 1 v1)  
**Deciders:** Engineering

---

## Context

TravelOS requires structured knowledge about travel entities to power AI recommendations. The system must:

1. Store 20 entity types and their relationships
2. Support graph traversal (e.g., hotels in a city, languages spoken in a country)
3. Power 6 reasoning services and DNA inference
4. Keep everything in-memory for Sprint 1 (no database dependency)
5. Have a stable interface so the graph implementation can be replaced in Sprint 4

**New in this ADR vs. v1:** The entity model expanded from 16 to 20 types (adding RailStation, Cuisine, SportsVenue, Language, Region, TravelSeason), the DNA system expanded from 10 to 12 archetypes, and 2 new reasoning services were added (SeasonReasoner, SafetyReasoner). The package was moved from `knowledge/` (root) to `ai/intelligence/` (under the AI layer).

---

## Decision

### 1. Package location: `ai/intelligence/`

The Travel Intelligence Layer lives under `ai/intelligence/` alongside agents, concierge, manager, and memory. This makes the system architecture explicit: the `ai/` directory is the intelligence layer, not just an agent collection.

```
ai/
├── agents/          # Specialist agents
├── concierge/       # TravelConcierge + ConversationEngine
├── intelligence/    # Travel Intelligence Layer ← THIS ADR
├── manager/         # TravelManager
├── memory/          # TIP enrichment
├── orchestration/   # Orchestrator + registry
├── registry/        # Agent registry
└── shared/          # Shared types
```

### 2. KnowledgeService as the public interface

All callers (reasoners, agents, API routes) interact with `KnowledgeService`, not `KnowledgeGraph`. This anti-corruption layer means that swapping the graph implementation only requires updating `KnowledgeGraph` — no call sites change.

```python
# ✓ Correct: use KnowledgeService
from ai.intelligence import knowledge_service
cities = knowledge_service.load_entities("City")

# ✗ Wrong: bypass the service layer
from ai.intelligence.knowledge.knowledge_graph import KnowledgeGraph
```

### 3. In-memory implementation for Sprint 1

`KnowledgeGraph` stores nodes in a Python dict and edges in a flat list. Traversal is O(n) over edges — acceptable for ~200 edges in Sprint 1. Beyond ~10,000 edges, indexing will be required.

### 4. Consistent reasoner interface

All 6 reasoners extend `BaseReasoner` and return `ReasoningResult`. This means:
- Agents can call any reasoner interchangeably
- Results can be serialised directly to JSON
- New reasoners can be added without changing callers

---

## Alternatives Considered

### A. Flat lookup dicts
Simple but no traversal, no relationship queries. Cannot answer "what hotels are in London?" without duplicating city→hotel mappings everywhere. Rejected.

### B. NetworkX
Capable graph library but adds a dependency for a small Sprint 1 graph. Custom `KnowledgeGraph` is 130 lines and exposes exactly the API needed. Revisit in Sprint 3 if query complexity warrants it.

### C. SQLite with recursive CTEs
Zero-config, ships with Python. But EAV tables for a property graph are awkward, and recursive CTEs for multi-hop traversal are complex to maintain. Rejected.

### D. Neo4j / ArangoDB
Production-ready. But requires a running server, adds infra cost, and violates Sprint 1's no-database constraint. The **recommended Sprint 4 migration target**.

### E. Kuzu (embedded graph DB)
MIT-licensed, embeddable (no server), Cypher-compatible. An ideal Sprint 4 migration because it eliminates the server requirement while keeping Cypher query capability. **Primary Sprint 4 recommendation.**

---

## Consequences

**Good:**
- Zero new dependencies in Sprint 1
- `KnowledgeService` interface is stable — Sprint 4 migration is localised to two classes
- Full Python typing on all entity fields
- 6 reasoners with consistent output contract — easy for agents to consume
- 12 DNA types cover full diversity of traveller motivations including Diaspora and Pilgrimage

**Neutral:**
- Edge traversal is O(n); acceptable now, will need an index at scale
- Seed data is hardcoded Python — changes require a code deploy in Sprint 1

**Bad:**
- No persistence — graph resets on process restart
- No query language — callers write Python traversal logic

---

## Sprint 4 Migration Path

1. Replace `KnowledgeGraph` methods with a Kuzu (or Neo4j) driver implementation
2. Write `scripts/seed_kuzu.py` from `travel_ontology.py` seed data
3. Translate Python traversal in `KnowledgeGraph` to Cypher queries
4. All `KnowledgeService` callers are unchanged — zero call-site migration

---

## Related

- `docs/TRAVEL_INTELLIGENCE_LAYER.md` — architecture overview
- `docs/TRAVEL_KNOWLEDGE_GRAPH.md` — entity and relationship reference
- `docs/TRAVELLER_DNA.md` — DNA inference algorithm
- `docs/REASONING_ENGINE.md` — 6 reasoners reference
- `docs/ONTOLOGY.md` — controlled vocabulary and type hierarchy
