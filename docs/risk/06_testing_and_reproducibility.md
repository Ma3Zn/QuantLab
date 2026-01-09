# Risk — Testing and reproducibility

## Determinism
Given identical inputs (portfolio snapshot + time series + request), the report must be identical.
If any non-determinism exists (e.g., unordered dict iteration), it must be removed.

## Test plan (minimum)
- Unit tests per metric and edge cases (NaN/Inf, empty window, constant prices).
- Property-based tests:
  - covariance symmetry and PSD (within tolerance),
  - drawdown invariants,
  - VaR <= ES in loss convention.
- Golden tests for `RiskReport` JSON.

## Diagnostics
Errors must be typed and informative.
Warnings must be structured and stable.
