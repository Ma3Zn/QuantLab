# ADR 0006 — MIC SessionRules as Primary Close-Time Source (With Deterministic Fallbacks)

## Status
Accepted (initial).

## Context
Accurate EOD timestamping depends on close times that are often incomplete in baseline calendars and vary historically. Provider EOD timestamps cannot be assumed to reflect official close times.

## Decision
- Introduce a MIC-indexed **SessionRules** dataset as the primary close-time source.
- Define deterministic hierarchy:
  1) SessionRules,
  2) baseline calendar close time,
  3) provider timestamp + provenance flag.
- Version and hash SessionRules into ingestion and registry metadata.
- Support historical validity intervals (`effective_from`/`effective_to`) as needed.

## Trade-offs
- Additional configuration maintenance vs significantly better time semantics and fewer silent errors.

## Consequences
- Consistent, auditable `ts` construction.
- Reduced reliance on provider quirks and improved cross-venue alignment.

## Follow-ups
- Build an initial SessionRules seed for top MICs used in MVP.
- Add tests for DST and known early-close dates.
