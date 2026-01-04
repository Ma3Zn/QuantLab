# QuantLab — Data Module

## Overview
The `data` module provides a reproducible, auditable, provider-agnostic market data foundation.
It focuses on correctness, traceability, and explicit assumptions over convenience.

This document reflects the **current implementation** and highlights **what is still missing**
to consider the module complete for the first QuantLab MVP.

---

## What the Data module does today

### 1. Provider boundary + symbol mapping
- Provider adapter contract (`FetchRequest`, `RawResponse`, `ProviderAdapter`) for raw ingestion.
- Local file adapter for offline CSV/JSON fixtures (MVP provider choice).
- EOD provider protocol for access-time pulls plus `SymbolMapper` for asset-to-vendor mapping.

### 2. Deterministic ingestion to canonical schema
- Normalizers for **equity EOD bars** and **FX daily points** (JSON or CSV payloads).
- Canonical records (`BarRecord`, `PointRecord`) with required metadata:
  `dataset_id`, `dataset_version`, `schema_version`, `instrument_id`, `ts`, `asof_ts`,
  `ts_provenance`, `source`, `ingest_run_id`, and `quality_flags`.
- Validation pipeline with hard errors + soft flags and a structured `ValidationReport`.

### 3. Raw + canonical storage zoning and registry
- Raw zone storage (immutable payload + metadata) keyed by `ingest_run_id` and `request_fingerprint`.
- Canonical snapshots staged and published with content hashes.
- Registry entries with dataset/version, universe hash, calendar/sessionrules versions, and row counts.

### 4. Access cache + aligned time series retrieval
- `MarketDataService.get_timeseries()` and replay-by-hash API.
- Deterministic request hashing and manifests storing lineage + quality.
- Parquet cache layout per provider/asset/year, aligned to a market calendar.

### 5. Time/calendar scaffolding
- Calendar spec and adapter backed by `pandas_market_calendars`.
- SessionRules seeds and hashing (stored in registry metadata).
- Calendar baseline version helpers (scaffolding for future overrides).

### 6. Quality reporting and structured logging
- Access-layer `QualityReport` (coverage + guardrail flags).
- Canonical `ValidationReport` with hard errors and soft flags.
- Structured logging helpers and typed errors for data operations.

### 7. Tests and fixtures
- Unit + integration + property tests for ingestion, storage, hashing, validation, and service.
- Golden snapshot tests for canonical datasets.
- Offline CSV fixtures under `data/external` and runnable examples under `examples/`.

---

## What is still missing for a complete Data MVP

### 1. Canonical Parquet serialization
Canonical snapshots are currently written as JSON lines under `part-*.parquet`.
The MVP ADR expects **real Parquet serialization** for canonical datasets.

### 2. Calendar/session enforcement for canonical records
The time-semantics policy is only partially enforced:
- no conversion to exchange close times using `SessionRules`,
- no `CALENDAR_CONFLICT` detection vs the chosen calendar,
- no validation that `trading_date_local` and `ts` are consistent with session rules.

### 3. Ingest-run metadata beyond `ingest_run_id`
The provider contract calls for a fuller ingest-run record
(start/end timestamps and config fingerprint). This is not yet modeled or stored.

---

## What the Data module does NOT do (MVP scope)

### 1. No intraday or tick-level data
- No minute bars, ticks, order book data, or real-time feeds.

### 2. No derivatives or complex instruments
- No futures rolls, options chains, or rates curves.

### 3. No implicit data transformations
- No forward/backward filling.
- No silent corporate action adjustments.

### 4. No analytics, pricing, or risk logic
- No returns, factor models, or portfolio aggregation.

### 5. No strategy or decision outputs
- No signals or execution logic.

### 6. No institutional guarantees
- No survivorship-safe guarantees or production SLAs at MVP.

---

## Intended role in the QuantLab architecture
The `data` module is a pure upstream dependency:
it feeds reproducible datasets into pricing, risk, stress, optimization, and decision layers,
while making uncertainty explicit and auditable.
