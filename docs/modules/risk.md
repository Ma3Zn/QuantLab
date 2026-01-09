# QuantLab — Module: risk

## Role
`risk/` converts portfolio exposures and time series into risk diagnostics.
It is a **pure computation** layer: no provider I/O, no caching, no side effects.

## Responsibilities (MVP)
- Time-series risk: volatility, covariance/correlation, drawdowns, tracking error.
- Tail risk: historical VaR/ES with explicit assumptions.
- Exposure views: by asset and currency; sector/region only via mapping plug-in.
- Variance attribution: marginal/component contributions to variance (MVP-level).

## Inputs
- Portfolio snapshot from `instruments/` (positions, ids, multipliers, currency).
- Aligned price/return time series (typically from `data/` outputs).
- Optional portfolio return series (from `pricing/`) when available.

## Outputs
- `RiskReport` (typed, JSON-serializable) with:
  - metrics,
  - exposures,
  - attribution,
  - assumptions + warnings,
  - input lineage.

## Non-goals (MVP)
- No optimization or decision outputs.
- No hidden parametric distribution assumptions.
- No corporate-action corrections (only surface quality flags).

## Design constraints
- Layer separation is strict.
- Composition over inheritance.
- Deterministic outputs. Canonical JSON. Golden tests.

## Where it is documented
- ADRs: `docs/adr/03xx-*`
- Module docs: `docs/risk/*`
