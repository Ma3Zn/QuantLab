# ADR-0302 — Risk inputs and as-of semantics

Status: Proposed
Date: 2026-01-09

## Context
Risk computations depend on time alignment, window definitions, and “as-of” consistency between:
- portfolio snapshot (positions + instrument metadata),
- price/return series for underlying market data ids,
- optional portfolio valuation series (from `pricing/`).

Inconsistent time semantics are the most common source of silent errors.

## Decision
The `risk/` layer will standardize on an explicit request contract:

- `as_of` (date): the evaluation date.
- `window` (lookback): number of trading days or explicit start/end dates.
- `return_definition`: simple returns by default; log returns optional.
- `annualization`: explicit convention (e.g., 252) and always recorded.
- `missing_data_policy`: explicit (error / drop / forward-fill / partial).
- `input_mode` (explicit):
  - `PORTFOLIO_RETURNS`: compute risk on portfolio return series (preferred).
  - `STATIC_WEIGHTS_X_ASSET_RETURNS`: derive portfolio returns from a single portfolio snapshot (MVP fallback).
- `lineage`: hashes/ids that identify the upstream datasets used.

`risk/` MUST reject inputs when:
- the portfolio contains market data ids not present in the provided time series bundle,
- `as_of` is not present or cannot be made consistent with the time index given the policies,
- the request implies look-ahead (e.g., uses data after `as_of`).

## Consequences
- The report can be reproduced and audited.
- The code path used (preferred vs fallback) is explicit and testable.

## Alternatives considered
1. Infer conventions implicitly from data frequency (rejected: too fragile).
2. Always require valuation series (rejected: blocks MVP, reduces modularity).
