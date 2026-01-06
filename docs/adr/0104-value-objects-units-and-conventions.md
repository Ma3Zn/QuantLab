## Status
Accepted

## Date
2026-01-06

## Decision
Define minimal value/convention standards in `instruments/`:
- `Currency`: ISO-4217 code as uppercase string (validated)
- `Quantity`: numeric value representing units of the instrument (validated constraints)
- `Multiplier`: numeric contract multiplier for derivatives (validated > 0 when applicable)
- `Expiry`: date for expiring instruments (validated for futures)

Conventions:
- All monetary values in domain objects are tagged with an explicit `Currency`.
- No FX conversion occurs in `instruments/`.
- No day-count conventions, accrued interest calculations, or curve references in `instruments/`.

## Context
Ambiguous units and implicit currency assumptions are common sources of silent errors. Early standardization reduces downstream risk.

## Options Considered
1. Minimal primitives (float/str) with explicit constraints (chosen for MVP)
2. Decimal everywhere
3. Strong unit system library

## Trade-offs
- Using floats may introduce rounding issues; acceptable for MVP representation and early valuation prototypes.
- Migration to Decimal is possible later via type aliasing and boundary conversion.

## Consequences
- Downstream pricers/risk engines can rely on explicit units.
- Futures valuation will not be “off by multiplier”.

## Failure Modes Addressed
- Missing multiplier for futures causing incorrect exposures.
- Mixed currencies in a portfolio without explicit labeling.

## Acceptance Criteria
- Currency is always explicit and validated.
- Futures must include expiry and multiplier.
- Index instruments must declare whether they are tradable or reference-only (via spec flag).
