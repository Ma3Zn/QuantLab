# AGENTS.md - Data Layer MVP Addendum (Time Semantics + Tests)

This file extends the root AGENTS.md for work that touches time semantics,
validation, and tests.

## Time semantics rules
- All canonical timestamps (ts, asof_ts, generated_ts, created_at_ts) must be
  timezone-aware and UTC.
- Add ts_provenance to canonical records using enum values from docs:
  EXCHANGE_CLOSE, FIXING_TIME, PROVIDER_EOD, UNKNOWN.
- If ts_provenance != EXCHANGE_CLOSE, add quality flag
  PROVIDER_TIMESTAMP_USED.
- Do not guess close times; use provider timestamps and flag when calendar
  info is missing.
- Keep trading_date_local and timezone_local explicit; no implicit local
  conversions.

## Validation rules
- Hard error on naive timestamps in canonical records.
- Flag calendar conflicts when a calendar says closed but a bar is present
  (CALENDAR_CONFLICT).
- Do not silently clean or drop records; use flags or hard errors per policy.

## Tests
- Every change to time semantics must add or update at least one unit test.
- Property-based tests should be small, deterministic, and offline.
