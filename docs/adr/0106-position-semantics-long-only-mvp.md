## Status
Accepted

## Date
2026-01-06

## Decision
For MVP, positions are **long-only**:
- `quantity >= 0` invariant enforced at model validation time.
- Shorting and margin/borrow costs are explicitly deferred.

`Position` contains:
- `instrument_id` (or full `Instrument` reference depending on architecture preference)
- `quantity`
- optional `tags/metadata`
- optional `cost_basis` fields are permitted only as passive data (no accounting logic)

## Context
Supporting shorting correctly quickly requires borrow costs, margining rules, and risk constraints that belong to later modules. Long-only is sufficient for building the pipeline and validating architecture.

## Options Considered
1. Long-only positions for MVP (chosen)
2. Allow signed quantities (long/short) immediately
3. Fully model trade lifecycle with lots and realized P&L

## Trade-offs
- Limits some realistic portfolios early.
- Prevents premature coupling with financing and accounting.

## Consequences
- Downstream `risk/` and `optimization/` can assume non-negative holdings unless explicitly extended.
- Extension path: ADR update to allow signed quantities + dedicated financing/margin module.

## Acceptance Criteria
- Validation rejects negative quantities.
- Clear documentation of limitation and planned extension.
