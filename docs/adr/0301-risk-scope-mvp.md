# ADR-0301 — Risk module scope (MVP)

Status: Proposed
Date: 2026-01-09

## Context
QuantLab needs a risk layer that converts portfolio exposures and time series into defensible risk diagnostics.
The project architecture requires strict separation of layers: `data/` (I/O, calendars, alignment), `instruments/` (domain),
`pricing/` (valuation), `risk/` (metrics), `stress/` (scenarios), `optimization/` (allocation), `decision/` (outputs).

Risk metrics are often “small math” but the failure modes are operational:
look-ahead, survivorship, inconsistent as-of dates, missing data, unstable conventions, and silent fallbacks.

## Decision
For the first MVP, `risk/` MUST:
- Compute core time-series risk metrics: volatility, covariance/correlation, drawdowns, tracking error.
- Compute tail risk using **historical** VaR/ES (no parametric normality claims by default).
- Provide exposure views by asset and currency.
- Provide MVP-level variance attribution: marginal and component contributions to variance (static-weights assumption is allowed but must be explicit).
- Emit a typed, JSON-serializable `RiskReport` with metadata, assumptions, and warnings.

`risk/` MUST NOT:
- Fetch market data (no provider I/O).
- Optimize allocations or emit buy/sell actions.
- Apply corporate action corrections (it can only surface upstream quality flags).
- Silently assume normality or parametric distributions unless explicitly requested.

## Consequences
- The risk layer remains deterministic and testable.
- Any “better” statistical modeling (e.g., EWMA, shrinkage, EVT) becomes explicit extensions, not hidden defaults.
- If full portfolio valuation time series are unavailable, the MVP may compute portfolio returns using a static weights approximation,
  but the report MUST surface that assumption.

## Alternatives considered
1. Implement parametric VaR immediately (rejected for MVP: encourages false confidence and complicated assumptions).
2. Couple risk directly to data providers (rejected: violates layering and reproducibility).

## Notes
This ADR defines scope, not implementation details.
