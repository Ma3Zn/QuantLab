# ADR-0407 — Future extension seam: pricing-based revaluation (non-MVP)

Status: Proposed
Date: 2026-01-09

## Context
Eventually, stress must cover nonlinear payoffs and instruments that cannot be approximated as linear in spot.

## Decision
Define a future seam:
- `RevaluationProvider` protocol that maps (portfolio, scenario, market_state) -> valuation snapshot.

MVP price-based engine remains the default.
When this extension is implemented, it must be opt-in and must not change the meaning of existing scenario contracts.

## Consequences
- Evolution without breaking backward compatibility.
