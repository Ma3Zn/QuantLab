## Status
Accepted

## Date
2026-01-06

## Decision
All `instruments/` domain objects must:
- include `schema_version` (module-level or per-model)
- support JSON serialization via Pydantic v2
- produce **canonical JSON** suitable for snapshot tests:
  - stable field naming
  - deterministic ordering for collections (positions)
  - no runtime-dependent fields except explicit timestamps provided by inputs

## Context
The project requires reproducibility, auditability, and golden tests for reports. Canonical JSON is the simplest “stable contract” across modules and for storage/reporting layers.

## Options Considered
1. Canonical JSON + schema_version (chosen)
2. Ad-hoc JSON dumps without versioning
3. Binary formats first (parquet/arrow) at domain level

## Trade-offs
- Requires explicit canonicalization steps for ordering.
- Long-term: other formats can be derived from the canonical JSON.

## Consequences
- Downstream modules can store/load snapshots consistently.
- Breaking changes must increment schema_version and document migration.

## Acceptance Criteria
- Two serializations of the same logical portfolio yield byte-identical JSON (assuming same inputs).
- Schema version is present and documented.
