# Step 3 — Provider Adapter Contract (I/O Boundary)

## Goal
Define a **provider-agnostic** contract for fetching market data, while isolating authentication, rate limits, pagination, and vendor quirks from the rest of the system.

## Components (logical)
- **ProviderAdapter**: I/O only; returns raw payload + fetch metadata.
- **Normalizer**: pure transform raw → canonical records (Step 2).
- **Validator**: schema + sanity checks; emits hard errors and soft flags.
- **IngestRun**: traceable unit of ingestion work.

---

## FetchRequest (logical)
A request is defined by:
- `dataset_id`
- `instrument_ids` (preferred) or a resolvable selector
- `time_range` (explicit inclusivity policy)
- `fields`
- `granularity` (EOD for MVP)
- optional `vendor_overrides` (must be logged)

## RawResponse (logical)
Returned by ProviderAdapter:
- `payload` (unmodified)
- `payload_format` (json/csv/…)
- `source` {provider, endpoint, provider_dataset}
- `fetched_at_ts` (UTC)
- `request_fingerprint` (hash)
- transport metadata (status, retries, pagination)
- optional `provider_revision`

## IngestRun (required)
- `ingest_run_id`
- `started_at_ts`, `finished_at_ts`
- `config_fingerprint` (includes universe snapshot)
- optional `environment_fingerprint`

---

## Behavioral requirements

### ProviderAdapter MUST
- Never mutate payloads.
- Emit complete metadata (`source`, `fetched_at_ts`, `request_fingerprint`).
- Surface failures explicitly (typed errors); no silent drops.
- Respect rate limits and expose throttling metrics.

### ProviderAdapter MUST NOT
- Apply corporate-action adjustments, FX conversion, or calendar logic.

### Normalizer MUST
- Be pure and deterministic given payload + mapping context.
- Populate `asof_ts` (default = fetched_at_ts), `source`, `ingest_run_id`, `quality_flags`.

### Validator MUST
- Separate **hard errors** (block publishing) from **soft flags** (publish with warnings).
- Never “fix” values unless via explicit, versioned transformations (derived datasets).

---

## MVP acceptance criteria
- End-to-end lineage: request fingerprint → raw payload → canonical records → dataset snapshot id.
- Failures are diagnosable and reproducible.
