# ADR-0303 — Returns conventions (MVP)

Status: Proposed
Date: 2026-01-09

## Context
Risk metrics depend on how returns are computed from price series (close-to-close, adjusted close, log vs simple).
MVP uses raw prices and explicitly does not correct for corporate actions.

## Decision
Default return definition: **simple close-to-close returns**:
- r_t = P_t / P_{t-1} - 1
- missing dates are handled by the alignment layer (`data/`); `risk/` consumes aligned series.

Optional (opt-in) alternative: log returns:
- r_t = log(P_t / P_{t-1})

The report MUST store:
- return definition,
- price field used (e.g., `close`),
- annualization factor.

If upstream data quality flags indicate suspect corporate actions, the report MUST include a warning:
- “raw prices may contain jumps unrelated to economic returns”.

## Consequences
- Consistency across runs and modules.
- Known bias is explicit, not hidden.

## Alternatives considered
1. Always use adjusted prices (rejected: conflicts with “raw + guardrails” MVP stance).
