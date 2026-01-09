# ADR-0402 — Scenario contracts and semantics

Status: Proposed
Date: 2026-01-09

## Context
“Scenario” is often overloaded. We need a strict representation to avoid ambiguous stress results.

## Decision
Scenario types (MVP):
- `ParametricShock`: explicit shocks by asset id, expressed as return shocks (e.g., -0.10) or price multipliers.
- `CustomShockVector`: explicit vector with a chosen convention and mandatory units.
- `HistoricalShock`: references a historical period but MUST be materialized as an explicit shock vector before execution
  (historical data fetching is not inside `stress/`).

Each scenario MUST have:
- `scenario_id` (stable),
- `name`,
- `shock_convention` (e.g., multiplicative returns),
- `shock_vector` keyed by `MarketDataId`,
- optional `tags` (e.g., “2008”, “covid”, “rates_up”).

## Consequences
- Stress execution stays pure and testable.
- “Historical” scenarios require an upstream scenario builder (outside `stress/`) that produces the vector.

## Alternatives considered
1. Let `stress/` fetch historical data directly (rejected: violates layering).
