# Stress — MVP overview (price-based)

## Cosa fa (MVP)
- Applies deterministic shocks to an as-of market state.
- Revalues linear instruments and produces explainable scenario impacts.

## Cosa non fa
- No market data fetching.
- No statistical fitting.
- No nonlinear derivative pricing.
- No FX conversion or base-currency aggregation; this must be handled upstream.

## Why price-based for MVP
Price-based stress keeps the engine modular and auditable.
It avoids coupling to incomplete pricing for complex instruments.

## FX/base-currency policy (MVP)
- If the portfolio spans multiple currencies, stress NAV/returns require an explicit policy.
- Default behavior emits a structured warning; you can choose to block via
  `fx_aggregation_policy="ERROR"`.
