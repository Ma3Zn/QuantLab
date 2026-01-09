# ADR-0307 — Variance attribution (MVP)

Status: Proposed
Date: 2026-01-09

## Context
The MVP calls for “risk attribution and contribution” at least at the variance level.
Full factor models are out of scope.

## Decision
MVP implements variance attribution for a static weight vector w and covariance Σ:
- Portfolio variance: σ² = wᵀ Σ w
- Marginal contribution to variance (MCV): ∂σ²/∂w = 2 Σ w
- Component contribution to variance (CCV): w ⊙ (Σ w) (up to a constant factor; report the exact convention)

The report MUST:
- record the attribution convention,
- declare whether weights are static (single snapshot) or time-varying (if supplied later).

## Consequences
- Provides actionable diagnostics (concentration, dominant risk drivers).
- Does not pretend to explain returns or alpha.

## Alternatives considered
1. Factor model attribution (rejected for MVP; requires taxonomy and regression discipline).
