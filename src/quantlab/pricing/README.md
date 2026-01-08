# `pricing/`

This package implements the pricing / valuation layer of QuantLab.

## Responsibilities (MVP)
- Deterministic mark-to-market valuation for linear instruments (cash, equity, tradable index proxies, linear futures).
- Multi-currency valuation for EUR/USD portfolios with base-currency NAV.
- Explicit FX conversion using canonical `FX.EURUSD` (USD per EUR) and recorded inversion.
- Typed, serializable valuation outputs with audit metadata (inputs used, FX applied, warnings).

## Non-responsibilities
- Market data fetching, storage, or alignment (belongs to `data/`).
- Risk metrics and analytics (belongs to `risk/`).
- Scenario stress or shocks (belongs to `stress/`).
- Allocation/optimization/decision outputs (belongs to `optimization/` and `decision/`).

## Design constraints
- Pure computation: identical inputs produce identical outputs.
- Layering: depends on `instruments/` and consumes `data/` only via protocols or stable schemas.
- Composition over inheritance for pricer components.

## Entry points (conceptual, forthcoming)
- `ValuationEngine`
- `PricerRegistry`
- `FxConverter`

See `docs/modules/pricing.md` and `docs/pricing/INDEX.md` for the full contract.
