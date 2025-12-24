# ADR 0004 — Canonical Time Semantics: UTC `ts` + Local Trading Date + Explicit Alignment Policies

## Status
Accepted (initial).

## Context
Global markets introduce systemic errors if time semantics are implicit:
- different venues have different close times and holidays,
- DST changes create ambiguous timestamps,
- FX “daily” depends on fixing conventions,
- providers disagree on EOD timestamps and may revise data.

Without a clear policy, cross-market joins and risk/stress become irreproducible and can embed look-ahead or hidden fills.

## Decision
1) Canonical `ts` is always stored in **UTC**.
2) Every daily observation carries an explicit **local trading/fixing date** (`trading_date_local`) + `timezone_local`.
3) Daily observations include `ts_provenance` to document how `ts` was formed:
   - `EXCHANGE_CLOSE`, `FIXING_TIME`, `PROVIDER_EOD`, or `UNKNOWN`.
4) Portfolio joins must declare a named **alignment policy** (e.g., INNER vs LEFT-with-missing).
5) Calendar conflicts are not silently corrected; they are retained and flagged (`CALENDAR_CONFLICT`).

## Options considered
- Store timestamps in local exchange time: rejected (cross-asset joins become brittle; DST complexity leaks everywhere).
- Drop provider observations that conflict with calendars: rejected (loses audit trail; may discard genuine special sessions).
- Implicit forward-fill for alignment: rejected (introduces hidden assumptions and masks missingness).

## Trade-offs
- More metadata and complexity upfront vs durable correctness and reproducibility.
- INNER joins reduce sample size; LEFT joins increase missingness handling burden. Both are explicit and selectable.

## Consequences
- Downstream modules can reason about time without vendor-specific hacks.
- Validation and debug workflows improve; conflicts become visible artifacts.
- Later intraday and derivatives extensions can attach to the same time semantics framework.

## Follow-ups
- Decide on baseline calendar library and versioning approach (ADR).
- Define official close-time sources per MIC (data source or static table) and governance for overrides.
