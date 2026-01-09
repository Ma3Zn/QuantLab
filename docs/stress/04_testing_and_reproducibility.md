# Stress — Testing and reproducibility

## Determinism
Stress results must be identical given the same:
- portfolio snapshot,
- as-of market state,
- scenario set (including ordering).

## Test plan (minimum)
- Unit tests:
  - shock application,
  - linear revaluation for each supported instrument class,
  - handling missing shocks.
- Property-based tests:
  - aggregation invariants (sum of breakdown equals total),
  - scenario ordering invariance.
- Golden tests:
  - `StressReport` canonical JSON.

## Diagnostics
Use typed errors and structured warnings.
Do not silently drop positions or assets.
