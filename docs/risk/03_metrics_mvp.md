# Risk — Metrics (MVP)

## Volatility
- Compute on the chosen return series.
- Report portfolio vol and optionally per-asset vol.

## Covariance / Correlation
- Default estimator: sample covariance (ADR-0305).
- Report should include at least:
  - covariance matrix (or a summarized form if too large),
  - correlation matrix (or summary),
  - diagnostics: symmetry, missing counts, sample size.

## Drawdown
- Define cumulative wealth index from returns.
- Drawdown is the relative distance from the running maximum.
- Report max drawdown and time-to-recovery if possible.

## Tracking error (optional for MVP)
If a benchmark return series is supplied:
- tracking error = std( portfolio_return - benchmark_return ), annualized.
Report must state whether benchmark is aligned and how missing values were handled.
