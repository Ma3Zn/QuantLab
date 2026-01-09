# Integration Seams: Pricing ↔ Risk/Stress/Optimization

## Purpose
Define stable boundaries so later modules can plug in without refactoring `pricing/`.

## What pricing provides downstream
- `PortfolioValuation` with:
  - per-position base-currency values
  - native-currency values
  - explicit FX conversion metadata
  - warnings and lineage

This is the minimum information required for:
- returns computation
- exposure reporting
- risk aggregation

## What pricing does not provide
- returns time series (belongs to risk or analytics layer)
- covariance, VaR/ES, drawdown
- scenario shocks (stress)
- allocation decisions (optimization/decision)

## Required downstream assumptions
Downstream modules must not assume:
- prices were “clean” beyond what data layer states
- FX conversion was perfect; it is only as good as the input series
- futures were fully modelled (margining/roll are out of scope)

## Recommended downstream contracts
- Risk consumes:
  - time series of portfolio valuations or P&L derived consistently
  - exposures by asset and currency
- Stress consumes:
  - a way to reprice under shocked market data (scenario modifies `MarketDataView`)

## Extension notes
- Scenario repricing is easiest if stress produces a wrapper `MarketDataView` that applies shocks.
- That keeps pricing unchanged and deterministic.

## Related docs
- `INDEX.md`
- `../instruments/08_integration_seams_pricing_risk.md`
