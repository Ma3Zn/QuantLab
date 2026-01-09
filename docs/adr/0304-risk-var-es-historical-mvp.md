# ADR-0304 — VaR/ES method: Historical simulation (MVP)

Status: Proposed
Date: 2026-01-09

## Context
VaR/ES are common tail metrics but are easy to misuse. Parametric VaR adds hidden distributional assumptions.
Historical simulation is simple, transparent, and defensible for an MVP.

## Decision
MVP tail risk uses **historical simulation** on the chosen return series:
- VaR at level α is the empirical quantile of losses.
- ES at level α is the empirical mean of losses beyond VaR.

Required report fields:
- confidence level(s),
- horizon (default: 1 day),
- sample size used (after missing policy),
- whether returns are portfolio returns or derived from static weights.

The implementation MUST:
- define losses consistently (loss = -return or -P&L/NAV),
- handle small sample sizes with explicit errors or warnings.

## Consequences
- Transparent tail metric with minimal assumptions.
- Users can extend later to parametric / EVT / filtered historical.

## Alternatives considered
1. Gaussian VaR (rejected for MVP).
2. Cornish-Fisher / skew-kurtosis adjustments (rejected: adds complexity without robust validation).
