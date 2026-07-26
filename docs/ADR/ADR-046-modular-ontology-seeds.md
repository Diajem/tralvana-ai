# ADR-046: Split Ontology Seeds by Domain

**Status:** Accepted

**Date:** 2026-07-26

**Task:** T-058

## Context

`ai/intelligence/ontology/travel_ontology.py` had grown to 1,430 lines. It
mixed all deterministic seed entities and 205 relationships in one module,
well beyond the repository's 500-line maintainability limit. The public
dependency surface was small: graph factories and persistence tests import
only `seed_graph`.

## Decision

- Keep `travel_ontology.seed_graph` as the stable public facade.
- Preserve the original seed call order.
- Group definitions into:
  - `geography.py`
  - `mobility_lodging.py`
  - `food.py`
  - `experiences.py`
  - `travel_requirements.py`
  - `seed_relationships.py`
- Put node/edge construction helpers in `seed_helpers.py`.
- Do not change entity constructors, identifiers, values, relationship types,
  weights, metadata, or order.
- Add regression tests for the complete node/edge/type-count snapshot and the
  500-line module limit.

## Consequences

- Every ontology module is below 500 lines.
- Existing factory, persistence, and consumer imports remain unchanged.
- A domain can be maintained without loading an unrelated 1,400-line file.
- The seeded graph remains exactly 199 nodes and 205 edges.

## Rejected alternatives

### Move seed data to JSON or YAML

Rejected because it would introduce a serialization/schema migration and could
change constructor validation or typed relationship handling.

### Keep the file and exempt static data

Rejected because relationships and multiple independent domains were already
hard to navigate; the split is mechanical and fully regression-testable.
