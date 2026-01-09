# Risk — Contracts (MVP)

## Core request object
`RiskRequest` must include:
- `as_of` (date)
- `window` as either:
  - `lookback_trading_days`, or
  - `start_date` + `end_date`
- `return_definition`: `simple` (default) or `log` (opt-in)
- `annualization_factor` (e.g., 252)
- `confidence_levels` for VaR/ES
- `input_mode`: `PORTFOLIO_RETURNS` or `STATIC_WEIGHTS_X_ASSET_RETURNS`
- `missing_data_policy`: explicit
- `lineage` (optional) for upstream dataset hashes

## Core output object
`RiskReport` must be JSON-serializable and include:
- metadata (report_version, generated_at, as_of, window, conventions)
- input lineage (portfolio hash/id, market data bundle hash/id)
- metrics:
  - volatility (portfolio and per-asset optional)
  - covariance/correlation summary
  - drawdown (max drawdown + drawdown series summary)
  - tracking error (if benchmark provided)
  - VaR/ES (historical)
- exposures:
  - asset exposure (weights/notionals)
  - currency exposure
  - optional mapped buckets (sector/region) if provider exists
- attribution:
  - marginal/component contributions to variance
- warnings (structured)

## Explicit limitations to declare in the report
- static weights assumption (if used)
- data quality flags (suspect corporate actions, missing data handling)
- estimator choices (sample covariance)
