# ADR-0405 — Max loss and scenario-set tail metrics (MVP)

Status: Proposed
Date: 2026-01-09

## Context
Price-based stress does not model probability. Still, the scenario set can reveal worst-case and sensitivity.

## Decision
MVP tail behavior across scenarios:
- `max_loss` (worst P&L)
- `max_loss_return` (worst P&L / NAV)
- `top_k_losses` (optional, K small)
- basic sensitivity ranking by absolute contribution (top drivers)

No probabilistic claims. The report MUST clearly state that scenario-set metrics are not VaR.

## Consequences
- Honest reporting that avoids false precision.

## Alternatives considered
1. Assign probabilities to scenarios (rejected for MVP).
