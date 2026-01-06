# Testing Plan (07)

## Test structure
- `tests/unit/instruments/`:
  - model invariants per Spec
  - position/portfolio invariants
  - canonical ordering and uniqueness

- property-based tests (Hypothesis):
  - portfolio serialization round-trip (object -> JSON -> object)
  - canonicalization stability (same logical portfolio -> same JSON)
  - rejection of invalid values (NaN/Inf, negative quantities)

- `tests/golden/`:
  - canonical JSON snapshots from `docs/instruments/examples/*.json`

## Minimum unit test matrix
### Currency validation
- accepts: EUR, USD
- rejects: eur, EU, EURO, whitespace

### Futures invariants
- expiry required
- multiplier > 0
- multiplier rejects 0, negative

### Position invariants
- quantity >= 0 (reject negative)
- reject NaN/Inf

### Portfolio invariants
- requires `as_of` with tzinfo
- positions uniqueness by instrument_id
- canonical ordering of positions
- cash keys normalized/sorted

## Coverage expectations
- enforce invariants with explicit tests (no “incidental coverage”)
- golden tests should be stable and minimal (3–5 reference portfolios)

## Notes
Do not test pricing. This module does not value instruments.
