# Persistent Knowledge Graph

T-029 makes Tralvana's shared travel knowledge survive API restarts and worker
boundaries without introducing a second production database.

## Runtime selection

| Environment | Graph backend | Behaviour |
|---|---|---|
| `DATABASE_URL` absent | `KnowledgeGraph` | Seeded in memory; zero-setup local and unit-test operation |
| `DATABASE_URL` present | `SqlAlchemyKnowledgeGraph` | Nodes and edges persist in the configured PostgreSQL database |

Both backends implement the same contract consumed by `KnowledgeService`.
Reasoners, itinerary assembly, the demo, and SDK callers do not select or
inspect the backend.

## Relational representation

Alembic revision `0005` adds:

- `knowledge_nodes`: stable node ID, entity type, insertion order, and JSON
  dataclass payload;
- `knowledge_edges`: directed source/target IDs, relationship type, weight,
  metadata, insertion order, and a deterministic identity key;
- indexes for typed node reads and inbound/outbound relationship traversal.

The deterministic edge key makes baseline seeding idempotent. Repeated startup
does not duplicate the 205 baseline relationships. A node with the same stable
ID is updated so corrected ontology data reaches the persistent graph.

## Startup and failure policy

The existing ontology is first built as a deterministic in-memory baseline.
When PostgreSQL is configured, the baseline is upserted transactionally into
the persistent graph and all subsequent reads and runtime mutations use that
database.

A configured database is authoritative. Missing migration tables or an
unreachable database fail startup clearly rather than silently falling back to
process-local data and creating different knowledge across workers.

Local operation remains unchanged when no database is configured.

## Why PostgreSQL instead of Kuzu

The original backlog named Kuzu when it was an actively maintained embedded
graph database. Its maintainers archived the project on 10 October 2025 and
state that it is no longer actively supported:
<https://github.com/kuzudb/kuzu>.

Tralvana already depends on PostgreSQL, SQLAlchemy, and Alembic for its
commercial ledger, Goals, and Trips. Reusing that stack:

- adds no abandoned or second database dependency;
- keeps one migration/readiness path;
- preserves the `KnowledgeService` boundary for a later specialised graph
  backend if scale measurements justify one;
- supports the current graph size and one-to-few-hop query patterns without a
  separate paid service.

## Non-goals

T-029 does not add:

- live destination facts or automatic web ingestion;
- vector search, embeddings, or RAG;
- a public knowledge mutation API;
- a graph administration UI;
- a claim that seeded facts are live availability, pricing, or regulation.
