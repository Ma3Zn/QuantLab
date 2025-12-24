# ADR 0007 — Storage MVP Choice: Parquet Snapshots + Lightweight Registry (No DB Server)

## Status
Accepted (initial).

## Context
We need a storage solution that is:
- reproducible (versioned snapshots, content hashes),
- auditable (raw payload retention),
- low operational overhead in MVP,
- portable across developer machines and CI,
- upgradeable to richer query layers later (e.g., DuckDB) without breaking contracts.

The design already requires:
- Raw Zone (immutable payloads),
- Canonical Zone (normalized snapshots),
- Dataset Registry keyed by (`dataset_id`, `dataset_version`).

## Decision
**MVP physical storage** will be:
1) **Parquet** (canonical datasets) stored as versioned snapshot directories/files.
2) **Raw payloads** stored in a raw-zone directory structure keyed by `ingest_run_id` and `request_fingerprint`.
3) A **lightweight registry** implemented as either:
   - JSON Lines / JSON (single-writer MVP), or
   - SQLite (recommended when concurrency or richer queries are needed).

DuckDB may be used as an **analytics/query tool** over parquet, but it is not the canonical source of truth in MVP.

## Options considered
- DuckDB as canonical store: deferred (good DX, but introduces governance/concurrency concerns and can hide snapshot semantics if misused).
- Full DB server (Postgres): rejected for MVP (operational overhead; unnecessary before multi-writer needs are proven).
- Canonical-only storage (no raw zone): rejected (loses auditability and ability to re-normalize).

## Trade-offs
- File-based registry is simpler but weaker for concurrency and complex metadata queries.
- Parquet snapshots can duplicate data; acceptable in MVP for immutability and replay guarantees.

## Consequences
- Deterministic rebuilds are straightforward (raw → canonical).
- Migration path is clear: keep logical contracts stable; swap physical layers when justified.
- Team/process discipline is required to prevent “ad-hoc overwrites” (append-only publishing rule).

## Migration triggers (explicit)
Move beyond MVP when one or more are true:
- frequent ad-hoc querying becomes a bottleneck,
- multi-writer ingestion is required,
- registry needs transactional guarantees,
- dataset catalog grows beyond manageable file-based metadata.

## Follow-ups
- Document snapshot directory conventions and atomic publish workflow (staging → publish).
- Add CI checks ensuring registry entries are consistent with file presence and content hashes.
