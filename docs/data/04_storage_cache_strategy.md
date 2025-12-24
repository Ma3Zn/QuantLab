# Step 4 — Storage / Cache Strategy (Raw Zone, Canonical Zone, Registry)

## Goal
Enable **immutability**, **replay**, and **audit** via clear zoning and dataset versioning.

---

## Zones

### Raw Zone (source-of-truth)
- Stores provider payloads **exactly as fetched** (immutable).
- Addressable by `ingest_run_id`, `request_fingerprint`, `source`, `fetched_at_ts`.
- Sufficient to re-run normalization deterministically.

### Canonical Zone (normalized)
- Stores canonical records (Step 2), versioned snapshots.
- Records always include `asof_ts`, `ingest_run_id`, `source`, `quality_flags`.

### Derived Zone (later)
- Returns, adjustments, continuous futures, factors, etc.
- MUST record input dataset versions (lineage).

---

## Dataset registry (required)
Keyed by (`dataset_id`, `dataset_version`) and includes:
- `schema_version`, `created_at_ts`, `ingest_run_id`
- `universe_version` (or universe snapshot hash)
- `source_set`
- `content_hash`
- optional stats (row counts, flag counts)

**Rule:** experiments and reports reference data only through the registry key.

---

## Versioning rules (recommended)
- `schema_version`: semantic.
- `dataset_version`: changes when raw payload, universe, or normalization rules change.
  - Example: `2025-12-24.1` (+ optional short hash).

---

## Physical storage options (not decided yet)
- Parquet + filesystem/object-store
- DuckDB for analytics over parquet
- DB for registry + parquet for data

**Initial recommendation (MVP):** Parquet + lightweight registry (JSON/SQLite), upgrade later if query needs justify it.

---

## MVP acceptance criteria
- Zones + invariants are explicit.
- Registry answers: “Which dataset_version produced this report and from which ingest run?”
- Canonical rebuild from raw is feasible in principle.
