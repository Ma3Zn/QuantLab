## Status
Accepted

## Date
2026-01-06

## Decision
Model instruments using composition:
- `Instrument` has:
  - `instrument_id` (internal identity)
  - `market_data_id` (binding to `data/`)
  - `instrument_type` (enum)
  - `spec` (a discriminated union of spec models)
  - `currency` (quote/settlement currency as applicable)
  - metadata (optional tags)

Avoid deep inheritance hierarchies like `EquityInstrument(FinancialInstrument)`.

## Context
Inheritance-based domain modeling becomes brittle with derivatives/structured products and makes schema evolution/serialization harder. Discriminated unions keep the surface clean and extensible.

## Options Considered
1. Composition with discriminated union specs (chosen)
2. Class inheritance tree
3. Single model with many optional fields

## Trade-offs
- Requires a bit more upfront type structure (spec classes).
- Greatly improves clarity and validation (each type has mandatory fields).

## Consequences
- Adding new instrument kinds becomes additive (new spec + enum entry).
- Serialization remains stable and explicit.

## Acceptance Criteria
- Each instrument type has a dedicated spec with required fields.
- No “mega Instrument” with dozens of optional fields.
- Specs remain free of pricing logic.
