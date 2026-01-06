# Canonical JSON Contract (05)

## Purpose
Canonical JSON enables:
- golden/snapshot tests
- reproducible simulation replay
- audit-friendly reports

## Requirements
- `schema_version` present
- stable field names
- deterministic ordering:
  - positions sorted by `instrument_id`
  - cash keys sorted
- timestamps are timezone-aware ISO-8601 strings

## Canonical Portfolio example (MVP)
```json
{
  "schema_version": 1,
  "as_of": "2026-01-06T00:00:00+00:00",
  "positions": [
    {"instrument_id": "EQ.AAPL", "quantity": 10.0},
    {"instrument_id": "EQ.MSFT", "quantity": 5.0}
  ],
  "cash": {"EUR": 1000.0, "USD": 50.0},
  "meta": {"name": "demo"}
}
```

## Canonicalization rules
- Disallow NaN/Inf in numeric fields.
- Normalize currency keys to uppercase.
- Reject unknown fields (extra='forbid').

## Schema evolution
- breaking changes bump `schema_version`
- provide migration notes in ADR or docs
