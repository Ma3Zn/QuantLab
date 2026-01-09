# QuantLab — Module: stress

## Role
`stress/` defines deterministic scenarios and applies them to a portfolio.
In the MVP it uses a **price-based** revaluation engine for linear instruments.

## Responsibilities (MVP)
- Scenario models:
  - historical (materialized as shock vectors),
  - parametric shocks,
  - custom shock vectors.
- Stress engine:
  - apply shocks to as-of prices,
  - compute scenario P&L and drivers.
- Report:
  - scenario-by-scenario results,
  - breakdown by position/asset/currency,
  - max loss across scenarios (scenario-set tail behavior).

## Inputs
- Portfolio snapshot from `instruments/`.
- As-of market state (prices) for underlying market data ids.
- Scenario set expressed as explicit shock vectors (no data fetching inside `stress/`).

## Outputs
- `StressReport` (typed, JSON-serializable) with explainable breakdowns.

## Non-goals (MVP)
- No statistical fitting.
- No nonlinear derivative pricing (options, KO, path-dependent).
- No probability assignment to scenarios.

## Design constraints
- Pure computation layer. Deterministic.
- Canonical JSON + golden tests.
- Clear extension seam towards pricing-based revaluation.

## Where it is documented
- ADRs: `docs/adr/04xx-*`
- Module docs: `docs/stress/*`
