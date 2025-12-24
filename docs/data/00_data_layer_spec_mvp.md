# Data Layer Spec (MVP) — One‑Pager

## Purpose
Provide a minimal, defensible **market data foundation** for QuantDev with:
- stable instrument identifiers,
- reproducible ingestion (“as‑of” replay),
- explicit calendar/timezone semantics,
- provider-agnostic storage and access contracts.

This document is the **entry point** for the Data layer MVP.

---

## MVP datasets (canonical)
**EOD Equities (global)**
- `dataset_id`: `md.equity.eod.bars`
- frequency: EOD
- record type: `BarRecord`
- required fields: `close` (+ required metadata)
- recommended: `open`, `high`, `low`, `volume`, optional `adj_close` (explicit basis)

**FX Spot Daily**
- `dataset_id`: `md.fx.spot.daily`
- frequency: daily
- record type: `PointRecord`
- required fields: `field`, `value`, `base_ccy`, `quote_ccy` (+ required metadata)
- recommended: `fixing_convention`

**Out of scope (MVP)**
- intraday bars/ticks, futures rolls/continuous series, options chains/surfaces, rates curves/conventions.

---

## Instrument universe and identifiers
- Downstream modules MUST key on internal `instrument_id` only (opaque, stable).
- Vendor symbols, tickers, ISIN/FIGI are mapping attributes in an instrument master.
- Equities are **listing-level** instruments (per MIC + currency).

Reference: `01_instrument_universe_mvp.md`

---

## Canonical time semantics (daily data)
- `ts`: canonical timestamp, **always UTC**
- `asof_ts`: when the observation was known/ingested (**anti-lookahead**)
- `trading_date_local`: local session (equity) or fixing (FX) date
- `timezone_local`: IANA tz for the venue/convention
- `ts_provenance`: `{EXCHANGE_CLOSE, FIXING_TIME, PROVIDER_EOD, UNKNOWN}` (recommended)

**Equity EOD**
- Preferred: `ts = exchange close (local) → UTC`, provenance `EXCHANGE_CLOSE`
- Fallback: provider timestamp, provenance `PROVIDER_EOD` + flag `PROVIDER_TIMESTAMP_USED`

**FX Daily**
- Requires explicit fixing convention (recommended).
- `ts` corresponds to the fixing time when known; otherwise provider timestamp with provenance.

Reference: `06_calendar_timezone_alignment_policy.md`

---

## Alignment policy for portfolio joins
Alignment is an explicit, named policy recorded in every experiment/report.

**Default MVP**: `INNER` on `alignment_date` (conservative; no implicit fills).
**Alternative**: `LEFT` with explicit missingness (no fills; missing records flagged/absent).

Hard rule: no forward-fill/backfill in canonical datasets.

Reference: `06_calendar_timezone_alignment_policy.md`

---

## Ingestion boundary (provider-agnostic)
- ProviderAdapter returns **raw payload unmodified** + fetch metadata.
- Normalizer maps raw → canonical records (pure, deterministic).
- Validator enforces hard rules and emits soft flags.
- Every run has `ingest_run_id` and `request_fingerprint`.

Reference: `03_provider_adapter_contract.md`

---

## Storage zoning + registry (reproducibility)
- Raw Zone (immutable provider payloads)
- Canonical Zone (versioned snapshots)
- Derived Zone (later; transformations with lineage)

Dataset registry key: (`dataset_id`, `dataset_version`).

Reference: `04_storage_cache_strategy.md`

---

## Quality stance (MVP)
- Hard errors block publishing.
- Suspicious data retained with record-level flags.
- Corporate actions are explicit (adj_close with basis OR event datasets later).
- No implicit imputation in canonical data.

Reference: `05_data_quality_policy_mvp.md`

---

## MVP acceptance checklist
- Canonical records contain required metadata (`dataset_id`, versions, `instrument_id`, `ts`, `asof_ts`, `source`, `ingest_run_id`, `quality_flags`).
- Calendar/time provenance populated or appropriately flagged.
- A dataset snapshot is reproducible from raw payloads and registry metadata.
