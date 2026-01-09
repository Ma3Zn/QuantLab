# Stress — Scenario models (MVP)

## Scenario types
### ParametricShock
Explicit shock vector keyed by `MarketDataId`.
Default convention: return shocks (e.g., -0.10).

### CustomShockVector
Same as parametric but explicitly declares units/convention.

### HistoricalShock
MVP requirement: it must be **materialized** into a shock vector before execution.
Historical data fetching is outside `stress/`.
The scenario can store references (period tags) for provenance, but execution uses the explicit vector.

## Required scenario fields
- scenario_id (stable)
- name
- shock_convention
- shock_vector { MarketDataId -> shock_value }
- tags (optional)

## Validation rules
- All ids in shock_vector must exist in the portfolio market data universe (or policy must state how to treat missing shocks).
- Shocks must not produce invalid prices under the chosen convention.
