# Step 2 — Canonical Market Data Schema + Metadata Contract

## Goal
Define the **canonical schema** for market data records consumed by downstream modules, with enough metadata to support:
- reproducibility (“as-of” replay),
- auditability (source traceability),
- safe joins across markets (timezone/currency explicit).

## What this step includes
- Canonical schemas for:
  - **EOD bars** (cash equities)
  - **Daily FX spot**
- Metadata contract: required vs optional fields.
- Versioning conventions at dataset and schema level.

## What this step excludes
- Provider adapter contract (I/O specifics).
- Storage format decisions (parquet/duckdb/etc.) beyond logical structure.
- Full data-quality policy (missing, outliers, stale ticks) beyond minimal flags.

---

## Design principle: logical schema vs physical layout
We standardize the **logical schema**. Physical storage may use “wide” columns for performance, but must be isomorphic to the logical schema.

We define two logical record types:

1) **BarRecord** — for OHLCV-style data (equities EOD).
2) **PointRecord** — generic scalar observation (FX mid, rates fixings, etc.).

Downstream code should target these logical types, not vendor payloads.

---

## Canonical Record: common metadata (required for all datasets)

### Required fields
- `dataset_id`: string (e.g., `md.equity.eod.bars`)
- `schema_version`: string (e.g., `1.0.0`)
- `dataset_version`: string (semantic or date-stamped, e.g., `2025-12-24`)
- `instrument_id`: string (internal stable ID)
- `ts`: timestamp (UTC, ISO 8601)
- `asof_ts`: timestamp (UTC) — when this observation was known/ingested (anti-lookahead)
- `source`: object
  - `provider`: string
  - `endpoint`: string (or logical name)
  - `provider_dataset`: string (if applicable)
- `ingest_run_id`: string (unique per ingestion run)
- `quality_flags`: array[string] (can be empty, but must exist)

### Recommended fields
- `trading_date_local`: date (when applicable)
- `timezone_local`: IANA string
- `currency`: ISO 4217 code (for price-like fields)
- `unit`: string (e.g., `shares`, `index_points`)

---

## Canonical schema: BarRecord (Equity EOD)

### Logical fields
- Common metadata (above)
- `bar` object:
  - `open`: float?
  - `high`: float?
  - `low`: float?
  - `close`: float (required)
  - `volume`: float?
  - `adj_close`: float? (optional, but if present must declare adjustment basis)

### Adjustment metadata (if `adj_close` used)
Add to record (recommended when `adj_close` present):
- `adjustment_basis`: enum {`SPLIT_ONLY`, `SPLIT_AND_DIVIDEND`, `PROVIDER_DEFINED`}
- `adjustment_note`: free text (short)

### Minimal example (JSON)
```json
{
  "dataset_id": "md.equity.eod.bars",
  "schema_version": "1.0.0",
  "dataset_version": "2025-12-24",
  "instrument_id": "inst_2cdd0b9d-2b6a-4a61-9a31-1a7b9f0c5b2a",
  "ts": "2025-12-23T21:00:00Z",
  "asof_ts": "2025-12-24T07:10:03Z",
  "source": {"provider": "PROVIDER_X", "endpoint": "eod_bars", "provider_dataset": "global_equities"},
  "ingest_run_id": "ing_20251224_071003Z_0001",
  "quality_flags": [],
  "currency": "USD",
  "bar": {"open": 191.2, "high": 194.0, "low": 190.8, "close": 193.5, "volume": 52103421}
}
```

---

## Canonical schema: PointRecord (FX Spot Daily)

### Logical fields
- Common metadata (above)
- `field`: string (e.g., `mid`, `bid`, `ask`)
- `value`: float (required)
- `base_ccy`: ISO 4217 (required)
- `quote_ccy`: ISO 4217 (required)
- `fixing_convention`: string (recommended; provider-specific but explicit)

### Minimal example (JSON)
```json
{
  "dataset_id": "md.fx.spot.daily",
  "schema_version": "1.0.0",
  "dataset_version": "2025-12-24",
  "instrument_id": "inst_7bd7a0a1-5f8a-4a2b-9b93-6fd2a7a7c1f1",
  "ts": "2025-12-23T17:00:00Z",
  "asof_ts": "2025-12-24T07:10:03Z",
  "source": {"provider": "PROVIDER_X", "endpoint": "fx_daily", "provider_dataset": "fx_spot"},
  "ingest_run_id": "ing_20251224_071003Z_0001",
  "quality_flags": [],
  "field": "mid",
  "value": 1.1042,
  "base_ccy": "EUR",
  "quote_ccy": "USD",
  "fixing_convention": "provider_eod_fix"
}
```

---

## Quality flags (MVP vocabulary)
Flags are intentionally minimal in this phase; they exist mainly to avoid silent assumptions.

- `MISSING_VALUE`
- `STALE`
- `OUTLIER_SUSPECT`
- `ADJUSTED_PRICE_PRESENT`
- `PROVIDER_TIMESTAMP_USED`
- `IMPUTED`

Later we will expand this into a formal policy + validation rules.

---

## Versioning rules
- `schema_version`: changes only when the logical schema changes.
- `dataset_version`: changes with new ingestion snapshots, provider revisions, or instrument universe changes.
- Every downstream artifact (returns, risk reports, stress outputs) must record the input dataset versions used.

---

## Bias / failure modes (explicitly acknowledged)
- **Provider revisions**: without `asof_ts`, backtests become non-replayable. This schema mandates `asof_ts`.
- **Silent currency/unit errors**: schema requires currency/unit where applicable.
- **Field ambiguity**: point data must declare `field` and (where relevant) conventions.

---

## MVP acceptance criteria (Step 2)
- A canonical schema that supports EOD equities and daily FX spot with mandatory metadata.
- At least one deterministic “replay contract”: a dataset snapshot is uniquely identified by (`dataset_id`, `dataset_version`) and every record has `ingest_run_id` and `asof_ts`.
