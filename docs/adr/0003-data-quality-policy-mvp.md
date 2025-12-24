# ADR 0003 — Data Quality Policy (MVP): Detect + Flag, No Silent Fixes

## Status
Accepted (initial).

## Decision
- Canonical datasets publish only if hard validation passes.
- Suspicious data retained with record-level flags.
- No implicit imputation; fixes live in derived datasets with lineage.
- Corporate actions must be explicit (adj_close with basis or event datasets).

## Rationale
Avoids opaque cleaning and look-ahead; makes assumptions auditable and testable.
