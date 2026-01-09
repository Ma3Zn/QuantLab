# ADR-0308 — RiskReport schema, warnings, and determinism

Status: Proposed
Date: 2026-01-09

## Context
QuantLab aims for auditable outputs. Risk reports must be machine-readable and stable across runs.

## Decision
`RiskReport` MUST be:
- typed (Pydantic v2),
- JSON-serializable with canonical field ordering,
- deterministic given the same inputs.

`RiskReport` MUST include:
- `report_version`
- `as_of`, `window`, `annualization`, `return_definition`
- `input_lineage` (hashes/ids of portfolio snapshot and time series bundle)
- `metrics` (vol, cov/corr summary, drawdown, tracking error, VaR/ES)
- `exposures` (asset, currency, optional mapped buckets)
- `attribution` (variance contributions, if applicable)
- `warnings`: structured list with codes and short context

## Consequences
- Golden tests can assert report stability.
- Downstream UI/reporting layers can rely on the schema.

## Alternatives considered
1. “Free-form dict” reports (rejected: unstable and hard to validate).
