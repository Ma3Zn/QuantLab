# `pricing/` Module — MVP Specification

## Purpose
`pricing/` converts **instrument specifications** plus **market data** into **auditable valuations**.

It is a pure computation layer.
It must not fetch data.
It must not compute risk.
It must not make decisions.

## Scope (MVP)
### Instruments priced in the MVP
- Cash
- Equity
- Index (only if modeled as tradable, i.e., an “ETF-like” proxy or similar)
- Linear futures (mark-to-market only; **no** margining, settlement, roll, or term-structure logic)

### Multi-currency support (Policy B)
- Portfolio may contain at least **EUR** and **USD** instruments.
- Valuation produces:
  - **native-currency** amounts per position, and
  - **base-currency** amounts using a deterministic FX conversion policy.

## Inputs
### Domain inputs
- `Instrument`, `Position`, `Portfolio` from `src/instruments/` (pure domain objects).
- `as_of` date (daily pricing semantics).

### Market data input
- A `MarketDataView` (read-only protocol) provided by the `data/` layer (adapter pattern).
- Pricing assumes market data is already cleaned/aligned upstream.
- Pricing does **not** forward-fill or “fix” missing data.

## Outputs
- `PositionValuation` per position.
- `PortfolioValuation` (NAV + breakdown + metadata).
- Outputs are typed, serializable, and include enough lineage to audit:
  - `as_of`
  - price fields used
  - FX pair(s) and inversion flags
  - quality / warning flags (if available from the data layer)

## Non-goals (explicit)
- Curves, discounting, and accrual logic for fixed income.
- Nonlinear derivatives (options, barriers, KO, structured products).
- Risk metrics (volatility, VaR/ES, Greeks).
- Optimization and allocation decisions.
- Transaction costs and liquidity modelling.

## Key design constraints
- **Layering:** `pricing/` depends on `instruments/` and consumes `data/` via a protocol, not via concrete providers.
- **Purity:** valuation must be deterministic for the same inputs.
- **Composition over inheritance:** pricers are small components registered in a registry.
- **Explainability:** every valuation must expose what inputs were used and what assumptions were made.

## Extension points (post-MVP)
- FX triangulation beyond EUR/USD.
- Curve construction (separate `curves/` submodule) and discounting.
- Bond accruals and day-count conventions.
- Futures roll models and continuous contract logic.
- Options pricers + Greeks (but only after risk layer contracts are stable).

## Testing expectations
- Unit tests per pricer (including edge cases).
- Property-based tests for linear scaling and currency invariants.
- Golden snapshot tests for stable JSON outputs.
- Integration test: instruments + market data view + valuation engine → reproducible report.

## Documentation map
- `docs/pricing/INDEX.md` (entry point)
- ADRs under `docs/adr/02xx-*.md`
- Examples under `docs/pricing/examples/`
