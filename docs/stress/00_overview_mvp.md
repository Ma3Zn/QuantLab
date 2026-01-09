# Stress — MVP overview (price-based)

## Cosa fa (MVP)
- Applies deterministic shocks to an as-of market state.
- Revalues linear instruments and produces explainable scenario impacts.

## Cosa non fa
- No market data fetching.
- No statistical fitting.
- No nonlinear derivative pricing.

## Why price-based for MVP
Price-based stress keeps the engine modular and auditable.
It avoids coupling to incomplete pricing for complex instruments.
