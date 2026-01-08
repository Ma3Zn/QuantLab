# `pricing/`

This package implements the **pricing / valuation** layer of QuantLab.

## Responsibilities
- Mark-to-market valuation for MVP linear instruments.
- Multi-currency support (EUR/USD) with explicit FX conversion to a base currency.
- Typed, serializable valuation outputs with audit metadata.

## Non-responsibilities
- Market data fetching or storage (belongs to `data/`).
- Risk metrics (belongs to `risk/`).
- Scenario shocks (belongs to `stress/`).
- Allocation decisions (belongs to `optimization/` and `decision/`).

## Entry points (conceptual)
- `ValuationEngine`
- `PricerRegistry`
- `FxConverter`

See `docs/modules/pricing.md` and `docs/pricing/INDEX.md`.
