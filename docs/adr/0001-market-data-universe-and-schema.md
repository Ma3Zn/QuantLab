# ADR 0001 — Market Data Universe (MVP) and Canonical Schema (Steps 1–2)

## Status
Accepted (initial).

## Decision
- MVP universe: global cash equities (EOD OHLCV) + daily FX spot.
- Downstream keys only on internal `instrument_id`.
- Canonical records require `asof_ts`, `source`, `ingest_run_id`.
- Canonical timestamps stored in UTC; local exchange time is metadata.

## Rationale
Prevents vendor lock-in and enables “as-of” replay (anti-lookahead) and auditability.
