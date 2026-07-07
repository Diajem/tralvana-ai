# ADR-002: In-Memory Property Graph for Sprint 1

**Status:** Accepted  
**Date:** 2026-07-07  
**Deciders:** Engineering

---

## Context

TravelOS requires structured knowledge about travel entities — destinations, airports, airlines, hotels, attractions, visa rules, and more — to power AI recommendations. The system must be able to:

1. Look up entities by name or ID
2. Traverse typed relationships (e.g. "hotels in London", "airports serving Paris")
3. Support deterministic traveller DNA inference
4. Support four specialist reasoners (Destination, Budget, Experience, Timeline)

Sprint 1 constraints: no database, no external APIs, in-memory only.

---

## Decision

Implement a custom in-memory property graph (`KnowledgeGraph`) backed by Python dicts and a flat edge list. Entities are Python dataclasses (nodes). Relationships are typed `Relationship` dataclass instances (edges).

Seed data (10 countries, 11 cities, ~120 nodes, ~180 edges) is loaded from `knowledge/ontology/travel_ontology.py` on import.

---

## Alternatives Considered

### A. Flat Python dicts (lookup tables)
Simple but no relationship traversal, no graph queries, no path finding. Would require duplicating city→airport→airline chains everywhere. Rejected.

### B. NetworkX in-memory graph
NetworkX is a capable graph library but adds a non-trivial dependency for what is a small graph in Sprint 1. The custom `KnowledgeGraph` class is ~100 lines and exposes exactly the API we need. Rejected for Sprint 1; worth revisiting in Sprint 3 if graph queries become complex.

### C. Neo4j (cloud)
Production-ready, Cypher query language, excellent tooling. But requires a running Neo4j instance, adds infra complexity, costs money, and conflicts with Sprint 1's "no database" constraint. Rejected for Sprint 1.

### D. SQLite with graph queries (recursive CTEs)
SQLite is zero-config and ships with Python, but modelling a property graph in SQL requires awkward EAV tables and complex recursive CTEs for traversal. Rejected.

---

## Consequences

**Good:**
- Zero dependencies added — pure Python dataclasses and dicts
- Fast lookups (O(1) node by ID, O(n) edge scan acceptable for Sprint 1 graph size)
- The `KnowledgeGraph` interface is stable — Sprint 4 migration to Neo4j/ArangoDB only changes the implementation class, not any call site
- Full Python typing — IDE autocomplete and type checking work correctly on entity fields

**Neutral:**
- Edge traversal is O(n) over all edges. Acceptable for ~200 edges; will need indexing at 10,000+ edges
- Seed data is hardcoded in Python — changes require a code deploy, not a data migration

**Bad:**
- No persistence — graph resets on every process restart
- No query language — callers must write Python traversal logic
- No graph visualisation out of the box

---

## Migration Path (Sprint 4)

1. Replace `KnowledgeGraph.__init__` and methods with a Neo4j Bolt driver implementation
2. Write `scripts/seed_neo4j.py` to load `travel_ontology.py` seed data into Neo4j on first deploy
3. Translate Python traversal methods to Cypher queries inside `KnowledgeGraph`
4. All reasoners and agents remain unchanged — they only call `KnowledgeGraph` methods

The `KnowledgeGraph` class acts as an anti-corruption layer: it hides the graph database choice from the application layer.

---

## Graph Database Candidates for Sprint 4

| Option | License | Query Language | Strengths |
|--------|---------|---------------|-----------|
| Neo4j | Community (free) / Enterprise | Cypher | Mature ecosystem, strong Python driver |
| ArangoDB | Apache 2 | AQL | Multi-model (document + graph), good Python support |
| Memgraph | BSL | Cypher (compatible) | Neo4j-compatible, in-memory optimised |
| Kuzu | MIT | Cypher | Embeddable, no server required |

Kuzu is the recommended migration target: it is embeddable (no server), MIT-licensed, Cypher-compatible, and optimised for in-process graph workloads — a natural evolution from the current in-memory `KnowledgeGraph`.
