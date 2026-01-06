# Instruments Layer — MVP Spec (00)

## Goal
Provide a validated, deterministic, serializable representation of:
- what instruments exist (economic identity)
- what the portfolio holds (positions)
- the portfolio state at a point in time (snapshot)

This is the contract surface consumed by `pricing/`, `risk/`, `stress/`, `optimization/`, `decision/`, and `simulation/`.

## Non-goals
- market data ingestion/storage (belongs to `data/`)
- pricing conventions and valuation (belongs to `pricing/`)
- risk metrics and scenarios (belongs to `risk/` + `stress/`)
- corporate actions and lot accounting
- orders/trades/execution lifecycle

## MVP instrument universe (representation-level)
- Equity / ETF
- Index (reference or tradable flag)
- Cash
- Future (expiry + multiplier)
- Bond (metadata only)

## Portfolio semantics (MVP)
- Positions are long-only: `quantity >= 0`.
- Portfolio is a deterministic snapshot:
  - `as_of` (timezone-aware timestamp)
  - unique positions by `instrument_id`
  - cash mapping (Currency -> amount)

## Determinism requirements
- Serialization is canonical:
  - positions sorted by `instrument_id`
  - cash keys sorted lexicographically
  - stable field naming and schema versions

## Acceptance criteria
- Creating invalid objects fails fast.
- Two serializations of the same logical snapshot are byte-identical.
- The layer is independent of providers and market data formats.
