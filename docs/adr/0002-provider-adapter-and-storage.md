# ADR 0002 — Provider Adapter Contract and Storage Zoning (Raw vs Canonical)

## Status
Accepted (initial).

## Decision
- ProviderAdapter returns raw payload unmodified + fetch metadata.
- Storage split into Raw Zone (immutable) and Canonical Zone (versioned).
- Require `ingest_run_id`, `request_fingerprint`, `asof_ts` for traceability.
- Maintain dataset registry keyed by (`dataset_id`, `dataset_version`).

## Rationale
Enables replayability and auditability, and prevents hidden assumptions from contaminating risk/stress layers.
