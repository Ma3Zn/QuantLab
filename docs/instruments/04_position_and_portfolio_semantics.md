# Positions and Portfolio Semantics (04)

## Position
A Position is a holding:
- `schema_version`
- `instrument_id`
- optional embedded `instrument` (must match `instrument_id`)
- `quantity`

MVP rule:
- long-only: `quantity >= 0`

Optional metadata:
- tags/book labels (strings)
- passive cost basis fields (stored only; no accounting logic)

## Portfolio snapshot
A Portfolio is a deterministic snapshot:
- `schema_version`
- `as_of` (timezone-aware)
- `positions` (list of unique holdings)
- `cash` mapping currency -> amount
- metadata (optional)

### Uniqueness
Positions must be unique by `instrument_id`.
If duplicates are provided, validation fails (preferred) rather than silently merging.

### Canonical ordering
- positions sorted by `instrument_id`
- cash keys sorted lexicographically

### Cash semantics
- cash amounts are numeric in the stated currency.
- negative cash is allowed only if explicitly documented (choose policy):
  - MVP recommendation: allow negative cash (to avoid artificial constraints), but keep it explicit.

## Failure modes guarded
- duplicated instruments leading to double counting
- non-deterministic ordering breaking snapshot tests
- implicit currency assumptions in cash
