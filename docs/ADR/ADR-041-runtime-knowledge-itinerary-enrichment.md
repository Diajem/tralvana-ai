# ADR-041: Resolve Itinerary Enrichment from the Runtime Knowledge Graph

**Status:** Accepted

**Date:** 2026-07-26

**Task:** T-028

## Context

`ItineraryBuilder` contained `_KG_ENRICHMENTS`, a second, hardcoded catalogue
of landmarks, museums, and restaurant descriptions for nine cities. The
shared knowledge graph already models Cities, Attractions, Museums, and
Restaurants. Because the duplicate catalogue was captured in code, graph
additions and corrections never reached generated itineraries. Some entries
also had no corresponding graph evidence.

Both the legacy Trip Planner and Trip Brain use the same module-level
`ItineraryBuilder`, so repairing this boundary once can improve both paths
without changing their public response shapes.

## Decision

- Remove `_KG_ENRICHMENTS`.
- Inject `KnowledgeService` into `ItineraryBuilder`, with the seeded shared
  service as its default.
- Resolve the destination City at the start of every `build()` call.
- Query only explicitly connected entities:
  - Attraction → City via inbound `NEAR`
  - Museum → City via inbound `LOCATED_IN`
  - Restaurant → City via inbound `BELONGS_TO`
- Deduplicate names and sort them case-insensitively so graph backend ordering
  cannot make an itinerary nondeterministic.
- Keep the existing goal templates when a City or entity category has no
  matching graph data.

## Consequences

- Graph mutations are visible to the next itinerary build without changing
  or recreating the builder.
- There is one destination-venue source instead of a graph plus a drifting
  source-code snapshot.
- Itinerary content is limited to entities the graph can support; the planner
  no longer emits static venue descriptions that are absent from the graph.
- The injected service makes runtime-query behaviour testable with a small
  isolated graph and prepares T-029's graph-backend replacement without
  changing `ItineraryBuilder`.
- This remains internal knowledge enrichment, not a claim of live inventory,
  opening hours, availability, event dates, prices, or bookability.

## Rejected alternatives

### Synchronise `_KG_ENRICHMENTS` whenever seed data changes

Rejected because it preserves two sources of truth and relies on manual
discipline to keep them aligned.

### Read entity `city_id` fields directly

Rejected because it bypasses the graph relationship contract and would not
exercise the same `KnowledgeService` boundary intended for T-029.

### Query every connected entity without relationship filters

Rejected because overloaded or future relationships could present an entity
in the wrong itinerary role. Explicit type and relationship filters make the
grounding rule reviewable.
