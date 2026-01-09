# ADR-0403 — Shock application policy (price-based)

Status: Proposed
Date: 2026-01-09

## Context
Price-based stress requires a clear rule that maps current prices to shocked prices.

## Decision
Default convention: multiplicative return shock:
- shocked_price = price * (1 + shock)

Alternative convention (opt-in): multiplicative factor:
- shocked_price = price * factor

All scenarios MUST specify which convention is used.
The engine MUST reject shocks that produce invalid prices (negative for instruments that require non-negative prices).

## Consequences
- Avoids silent sign/units errors.
- Enables consistent aggregation across assets.

## Alternatives considered
1. Additive price shock (rejected by default; still allowed as an explicit scenario type later).
