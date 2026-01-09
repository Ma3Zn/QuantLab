# ADR-0406 — Stress testing strategy (unit + property + golden)

Status: Proposed
Date: 2026-01-09

## Context
Stress engines fail via sign errors, missing ids, multiplier mistakes, and aggregation bugs.

## Decision
Testing requirements:
- Unit tests for shock application rules and instrument payoff mapping (linear instruments).
- Property-based tests for aggregation invariants:
  - sum of position P&L equals portfolio P&L,
  - scenario ordering does not change results.
- Golden tests for `StressReport` JSON.
- Integration test that runs stress end-to-end on committed sample fixtures.

## Consequences
- Prevents subtle but catastrophic accounting errors.
