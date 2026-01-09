# ADR-0401 — Stress module scope (MVP, price-based)

Status: Proposed
Date: 2026-01-09

## Context
QuantLab needs deterministic stress testing that is independent from statistical fitting and can be audited.
For the MVP, a price-based revaluation engine is preferred to avoid coupling to a full pricing stack.

## Decision
For the first MVP, `stress/` MUST:
- Define scenario models: historical shock, parametric shock, custom shock vector.
- Apply shocks **price-based** to revalue positions with linear payoffs.
- Produce a typed, JSON-serializable `StressReport` with scenario-by-scenario P&L and breakdown by driver/position.
- Report worst-case (max loss across scenarios) and basic tail behavior across the defined scenario set.

`stress/` MUST NOT:
- Fetch market data (no provider I/O).
- Fit statistical distributions or assume normality by default.
- Attempt to price nonlinear derivatives (options, KO, path-dependent products) in MVP price-based mode.

## Consequences
- Stress is deterministic and modular.
- Extension to “revalue via `pricing/`” remains a clean future path.

## Alternatives considered
1. Revaluation via pricing from day 1 (rejected for MVP: increases coupling and complexity).
