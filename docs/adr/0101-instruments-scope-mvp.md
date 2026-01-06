## Status
Accepted

## Date
2026-01-06

## Decision
Implement the `instruments/` module as a **pure domain layer** defining economic objects and invariants for:
- Instrument definitions (minimal set)
- Positions (holdings)
- Portfolio snapshots (container of positions + cash)

The MVP scope includes:
- **Equity / ETF** (spot instruments)
- **Index** (as a reference instrument, not necessarily tradable)
- **Cash** (multi-currency ready, single-currency acceptable initially)
- **Future** (representation only; no roll/margining logic in `instruments/`)
- **Bond** (representation only; no accrued interest or curve-based pricing in `instruments/`)

Explicitly out of scope for MVP:
- Options, knock-outs, leveraged certificates, structured products
- Corporate actions (splits/dividends), tax lots, FIFO/LIFO accounting
- Margining/financing, collateral, borrow costs
- FX conversion, curve building, carry models
- Order/trade lifecycle (fills, executions, order management)

## Context
Downstream modules (`pricing/`, `risk/`, `stress/`, `optimization/`, `decision/`) require stable, serializable, validated domain objects. Mixing pricing/risk logic into `instruments/` increases coupling and leads to destructive refactors later.

## Options Considered
1. **Minimal representation + strict invariants (chosen)**
2. Include pricing-ready logic (accrued interest, roll, etc.) in `instruments/`
3. Defer `instruments/` and start from `pricing/`

## Trade-offs
- The chosen approach limits early “end-to-end valuation realism” (e.g., futures margining, bond accrued interest).
- It substantially reduces architectural risk and clarifies ownership of responsibilities.

## Consequences
- `pricing/` will be responsible for valuation mechanics (including conventions).
- `risk/` and `stress/` will consume portfolio snapshots in a deterministic format.
- Extensions to derivatives/structured products will be added later via new instrument specs without changing core contracts.

## Migration / Follow-ups
- Add ADRs for: identifier contract with `data/`, modeling choice, serialization canonicalization, error model/testing.

## Acceptance Criteria
- Domain objects are I/O free, deterministic, and JSON-serializable.
- Clear documentation of supported vs unsupported instruments for MVP.
- Explicit non-goals recorded to prevent scope creep.
