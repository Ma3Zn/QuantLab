# QuantLab — Instruments Module

## Overview
The `instruments` module defines the **canonical domain model** for what the portfolio holds.
It provides validated, serializable objects for instruments, positions, and portfolio snapshots.
It is intentionally **I/O free** and **pricing-free**: it encodes *economic identity and invariants*, not valuation.

This document describes the **intended MVP design** (not the current implementation status).
The goal is to provide a stable contract for downstream modules (`pricing`, `risk`, `stress`, `optimization`, `decision`)
while integrating cleanly with upstream market data (`data`).

---

## Core principles
- **Pure domain objects**: no provider calls, no file/network I/O, no hidden global state.
- **Composition over inheritance**: instruments are modeled via a base `Instrument` + a typed `spec`.
- **Early validation**: invalid states should fail fast at construction time.
- **Deterministic outputs**: serialization is canonical to support audit and golden/snapshot tests.
- **Stable contracts**: schema versioning and explicit identifiers to avoid destructive refactors.

---

## What the Instruments module provides (MVP target)

### 1. Instrument identity + market data binding
- `InstrumentId`: internal identity used in portfolios and reports.
- `MarketDataId`: identifier used to retrieve time series from `data` (prefer reusing `data.AssetId`).
- Every `Instrument` carries a `market_data_id` (or explicitly declares no market data binding, e.g. reference-only).
  - Indexes use `is_tradable` to express binding intent.
  - Cash/Future/Bond specs use `market_data_binding` to make non-priced instruments explicit.

This separation is deliberate:
instrument identity is not always the same as the identifier used to fetch data
(e.g., futures contracts vs continuous series, synthetic instruments, reference indices).

### 2. Canonical instrument model (composition)
A single `Instrument` object with:
- `instrument_id`
- `instrument_type` (enum)
- `market_data_id`
- `currency` (quote/settlement currency as applicable)
- `spec`: a discriminated union of type-specific specs
- optional metadata (tags, description)

**MVP instrument types**
- Equity / ETF (spot)
- Index (reference or tradable flag)
- Cash
- Future (representation only: expiry + multiplier, no roll/margining logic here)
- Bond (representation only: issuer/maturity/coupon metadata, no accrued-interest logic here)

### 3. Positions (holdings)
- `Position` links an instrument (by `instrument_id` or embedded `Instrument`) to a `quantity`.
- MVP constraint: **long-only** (`quantity >= 0`).
- Optional passive fields (allowed but not “active logic” in MVP):
  - `cost_basis` (stored only, no realized/unrealized accounting)
  - free-form tags (book, strategy label)

### 4. Portfolio snapshot (deterministic container)
- `Portfolio` is a deterministic snapshot:
  - `as_of` timestamp
  - `positions` (canonical ordering in serialization)
  - `cash` as mapping `Currency -> Amount`
  - optional metadata (name, notes, tags)

This representation is designed for `risk` and `stress` to consume directly,
and for `simulation` to produce and store snapshots reproducibly.

### 5. Validation (Pydantic v2)
- Domain objects are implemented as **Pydantic v2 models** with strict validation.
- Type-specific invariants are enforced:
  - futures: require `expiry` and `multiplier > 0`
  - cash: currency required, quantity is amount
  - long-only positions: `quantity >= 0`
  - currency fields must be explicit and validated (ISO-4217 uppercase)
  - tradable instruments require explicit `currency`

### 6. Canonical JSON serialization + schema versioning
- All major objects include `schema_version` (including `Position`).
- Serialization produces canonical JSON suited for:
  - golden/snapshot testing
  - stable report generation
  - deterministic replay and audit

Canonicalization rules (MVP):
- stable field names and ordering
- deterministic ordering for positions collections
- no runtime-dependent fields except explicit inputs (e.g., `as_of`)

### 7. Typed errors and diagnostics
- Validation errors are raised early and include actionable messages.
- A small set of domain-specific error wrappers may exist for clearer semantics
(e.g., `PortfolioInvariantError`), while still leveraging Pydantic’s detail.

---

## What the Instruments module does NOT do (MVP scope)

### 1. No market data fetching or storage
- No provider adapters.
- No symbol mapping to vendors.
- No caching, no raw zone, no canonical data ingestion.

These belong to `data`.

### 2. No pricing logic
- No discounting, no curve building, no accrued interest, no carry/roll logic.
- No pricing interfaces baked into `instruments`.
- No FX conversion or rate application inside `instruments`.

These belong to `pricing`.

### 3. No risk/stress logic
- No VaR/ES, Greeks, factor risk, stress scenarios, or aggregation.

These belong to `risk` and `stress`.

### 4. No corporate actions or accounting engine
- No splits/dividends adjustments.
- No tax lots, FIFO/LIFO, realized P&L accounting.

(These are separate projects and should not be mixed into `instruments`.)

### 5. No execution, orders, or trade lifecycle
- No orders, fills, partial executions, or stateful position evolution.

These belong to a future `execution` or `simulation` event layer, not the domain model.

---

## Integration with the rest of QuantLab

### Upstream dependency: `data`
- `data` is the source of truth for time series retrieval.
- `instruments` binds an instrument to data via `market_data_id`.
- `instruments` MUST remain provider-agnostic; any mapping from human symbols to vendor IDs belongs upstream.

### Downstream consumers
- `pricing` consumes `Instrument` + market data retrieved via `data` and outputs valuations.
- `risk` consumes `Portfolio` snapshots + pricing outputs to compute exposures and risk metrics.
- `stress` consumes the same snapshots and applies scenario perturbations.
- `optimization` consumes risk measures, constraints, and produces target exposures/weights.
- `decision` consumes optimization output and produces explainable, risk-aware recommendations.
- `simulation` orchestrates time progression and generates sequences of portfolio snapshots.
- `report` serializes canonical JSON outputs and collects evidence/lineage.

**Key architectural intent**
`instruments` is the bridge between “market data exists” and “portfolio state exists”:
it defines the *semantic meaning* of holdings in a way that pricing and risk can trust.

---

## Known limitations and failure modes (explicit)
- Long-only positions in MVP: cannot represent short books without an extension.
- Futures are representational only: without roll/margining, downstream valuation is incomplete.
- Bonds are representational only: without conventions (day count, calendars), pricing is deferred.
- Float quantities can introduce rounding issues; acceptable for MVP but should be revisited if cash accounting becomes strict.
- Identifier drift is a systemic risk: the `InstrumentId` vs `MarketDataId` contract must remain consistent across modules.

---

## Extension path (post-MVP)
- Enable shorting with explicit financing/margin semantics (likely a dedicated module).
- Corporate actions and instrument master data (splits/dividends) with explicit provenance.
- Rich derivatives:
  - options (European/American), barrier/KO, structured products
  - payoff specs remain in `instruments`; pricing stays in `pricing`
- Event-sourced portfolio evolution (trades/events) built in `simulation` / `execution`.
- Stronger numeric types for money/quantity (Decimal or fixed-point) once accounting requirements harden.
- Multi-venue and calendar-aware conventions as explicit dependencies (not hidden globals).

---

## Testing strategy (MVP target)
- Unit tests for invariants per instrument/spec and for portfolio constraints.
- Property-based tests:
  - object → JSON → object round-trip
  - canonicalization stability (same inputs → identical JSON)
- Golden snapshot tests for a small set of reference portfolios:
  - equities-only portfolio with cash
  - portfolio with a future (expiry/multiplier)
  - mixed-currency cash portfolio

---

## Deliverables for a “complete instruments MVP”
- Stable Pydantic v2 domain models for `Instrument`, `Position`, `Portfolio`.
- Deterministic canonical JSON serialization with schema versioning.
- Clear documentation of supported instrument types and non-goals.
- Test suite (unit + property + golden) enforcing invariants and reproducibility.
