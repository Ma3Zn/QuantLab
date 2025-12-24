# QuantLab — Data Module

## Overview
The `data` module provides a **reproducible, auditable, provider-agnostic market data foundation** for QuantLab.
It is designed to support serious quantitative research and risk systems, prioritizing correctness,
traceability, and explicit assumptions over convenience.

This document summarizes **what the module will be able to do** and **what it will explicitly not do** for the actual release.

---

## What the Data module WILL be able to do

### 1. Deterministic market data ingestion
- Ingest **EOD global equities** and **daily FX spot** data through a provider-agnostic interface.
- Persist **raw provider payloads immutably**, enabling full replay and audit.
- Generate deterministic ingestion identities (`ingest_run_id`, request fingerprint).

### 2. Canonical normalization with strict contracts
- Normalize raw data into **typed canonical records** (`BarRecord`, `PointRecord`).
- Enforce a stable **canonical schema** with explicit required/optional fields.
- Guarantee core invariants:
  - UTC timestamps,
  - explicit `asof_ts` (anti–look-ahead),
  - stable internal `instrument_id` usage.

### 3. Explicit time, calendar, and session semantics
- Attach **local trading dates**, timezones, and timestamp provenance to every record.
- Apply venue close times via **SessionRules** with deterministic fallbacks.
- Detect and flag **calendar conflicts** instead of silently correcting them.

### 4. Transparent data quality enforcement
- Apply **hard validation rules** that block publishing invalid datasets.
- Surface **soft data issues** (missing values, suspicious prices, provider timestamps, calendar conflicts)
  via record-level quality flags.
- Emit structured **validation reports** for every ingestion run.

### 5. Versioned storage and dataset registry
- Store data in clearly separated **Raw**, **Canonical**, and (future) **Derived** zones.
- Publish **immutable, versioned dataset snapshots** (Parquet).
- Maintain a **dataset registry** capturing lineage:
  - dataset versions,
  - universe hash,
  - calendar and SessionRules versions,
  - content hashes.

### 6. Reproducibility and regression protection
- Rebuild canonical datasets from raw payloads deterministically.
- Protect semantics with **golden snapshot tests** and explicit version bumps.
- Enable confident refactoring without silent behavioral drift.

### 7. Testability and engineering hygiene
- Full unit, integration, and property-based test coverage for the data pipeline.
- Clear error taxonomy and structured logging.
- Tooling and CI enforcing linting, typing, and test execution.

---

## What the Data module will NOT do (by design, at MVP)

### 1. No intraday or tick-level data [WiP]
- No minute bars, ticks, order book data, or microstructure modeling.
- No latency-sensitive ingestion or real-time feeds.

### 2. No derivatives or complex instruments [WiP]
- No futures rolls or continuous futures.
- No options chains, implied volatility surfaces, or dividend term structures.
- No rates curves or instrument-specific day-count conventions.

### 3. No implicit data transformations
- No forward/backward filling.
- No silent corporate action adjustments.
- No smoothing, interpolation, or “cleaning” beyond explicit flags.

### 4. No analytics, pricing, or risk logic
- No returns computation, factor construction, or signals.
- No pricing models or valuation logic.
- No portfolio aggregation, risk metrics, or stress testing.

### 5. No strategy or decision outputs
- No buy/sell signals.
- No portfolio weights or execution logic.

### 6. No institutional guarantees
- MVP provider data is not survivorship-safe.
- Corporate actions may be incomplete or approximate.
- Regulatory or production-grade SLAs are out of scope.

---

## Intended role in the QuantLab architecture
The `data` module is a **pure upstream dependency**:
- it feeds clean, well-specified datasets into pricing, risk, stress, optimization, and decision layers;
- it does not embed modeling assumptions that belong downstream;
- it makes uncertainty and data imperfections explicit rather than hidden.

In short: **the Data module makes it possible to trust everything built on top of it — or to know exactly why you should not.**
