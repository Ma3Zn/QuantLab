# ADR-0309 — Risk testing strategy (unit + property + golden)

Status: Proposed
Date: 2026-01-09

## Context
Risk functions are easy to get subtly wrong (annualization, sign conventions, edge cases).
A serious MVP requires more than a couple of unit tests.

## Decision
Testing requirements:
- Unit tests for each metric and edge case.
- Property-based tests (Hypothesis) for invariants:
  - covariance is symmetric and PSD up to numeric tolerance,
  - drawdown is non-positive and resets at new highs,
  - VaR <= ES in loss convention.
- Golden tests for canonical JSON reports using small deterministic fixtures.
- Integration tests that run the end-to-end risk pipeline on committed sample data.

## Consequences
- Higher confidence in correctness and stability.
- Slightly higher upfront test engineering, but less debugging later.

## Alternatives considered
1. Unit tests only (rejected).
