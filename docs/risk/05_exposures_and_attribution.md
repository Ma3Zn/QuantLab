# Risk — Exposures and attribution (MVP)

## Asset exposure
At minimum:
- weight per `MarketDataId` (normalized to 1 if possible)
- notionals if weights cannot be normalized (must state convention)

## Currency exposure
Aggregate exposures by instrument currency.
If FX conversion is not supported, currency exposure is a decomposition only, not an aggregation.

## Sector/region exposure (optional)
Only computed if a mapping provider is supplied (ADR-0306).
If mapping is missing, report must include warnings and omit the breakdown.

## Variance attribution
For weight vector w and covariance Σ:
- σ² = wᵀ Σ w
- compute Σ w once; component contributions derive from w ⊙ (Σ w)
Report must state:
- weight definition (snapshot vs time-varying),
- covariance estimator,
- exact attribution convention used.
