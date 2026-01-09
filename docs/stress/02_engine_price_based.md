# Stress — Engine (price-based)

## Market state
The engine consumes an as-of market state:
- price per `MarketDataId` (typically close)

## Shock application
Default: multiplicative return shock:
- shocked_price = price * (1 + shock)

## Linear revaluation (MVP)
For each position:
- Equity/ETF/Index: P&L = qty * (P_shocked - P)
- Futures: P&L = qty * multiplier * (P_shocked - P)
- Cash: P&L = 0 in its own currency (unless FX stress exists upstream)

Aggregation:
- portfolio P&L is sum of position P&L
- breakdowns must sum exactly (within floating tolerance)

## Policies
- Missing shocks for an asset: choose one of
  - treat as 0 shock (default with warning),
  - error.
This must be explicit in `StressRequest` or scenario set policy.
