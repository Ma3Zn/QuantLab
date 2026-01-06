## Status
Accepted

## Date
2026-01-06

## Decision
Define explicit “seams” (contracts) consumed by downstream modules, without implementing pricing/risk logic in `instruments/`:
- `pricing/` will require from `Instrument`:
  - instrument type and spec fields
  - currency
  - multiplier/expiry where applicable
  - market_data_id to fetch required series (prices, rates, etc.)
- `risk/` and `stress/` will require from `Portfolio`:
  - snapshot structure (as_of, positions, cash)
  - deterministic serialization
  - stable IDs

We do NOT include:
- pricer interfaces
- risk engine interfaces
inside `instruments/`.

## Context
Premature interface definitions for pricing/risk frequently bake in incorrect assumptions. The seam should be a clean data contract: “here is the validated state”.

## Options Considered
1. Data contract seam only (chosen)
2. Define abstract base classes for pricers/risk engines in instruments
3. Hard-couple instruments with pricing implementations

## Trade-offs
- Downstream modules must define their own interfaces (by design).
- Preserves strict layer boundaries and replaceability.

## Acceptance Criteria
- `pricing/` can be implemented purely by consuming `Instrument` and market data via `data/`.
- `risk/` can be implemented purely by consuming `Portfolio` + pricing outputs, without modifying instruments.
