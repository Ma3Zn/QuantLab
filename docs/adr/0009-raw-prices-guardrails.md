# ADR 0009 — Raw Prices Only + Guardrails (No Corporate Action Adjustments)

## Status
Accepted (initial).

## Context
The MVP data access layer must serve aligned daily time series with reproducible
lineage and deterministic caching. Corporate action handling (splits, dividends,
mergers) is a major source of ambiguity across vendors and requires explicit
governance. Silent adjustments would hide data provenance and make replay
non-deterministic without additional metadata.

## Decision
- Serve **raw prices only** (no split/dividend adjustments).
- Add **guardrails** that detect suspect corporate action discontinuities and
  report them via `QualityReport` without mutating the data.
- Treat guardrails as warning signals by default; downstream code must decide
  how to react or apply explicit adjustments.

## Options considered
1) **Raw-only + guardrails** (chosen).
2) Vendor-adjusted prices (adjusted close) as default output.
3) Auto-correct suspicious jumps (heuristic adjustments).
4) Dual outputs (raw + adjusted) in the MVP bundle.

## Trade-offs
- Raw-only preserves provenance but pushes adjustment logic to downstream users.
- Guardrails improve transparency but do not resolve economic discontinuities.
- Adjusted defaults reduce friction but risk hiding vendor-specific adjustments.

## Consequences
- Consumers must handle corporate actions explicitly if they need adjusted data.
- Quality outputs surface likely split-like events for manual review.
- Manifests and request hashes remain deterministic and audit-friendly.

## Follow-ups
- Add an explicit corporate action dataset and adjustment pipeline (separate PR).
- Document how downstream models should opt into adjusted data when available.
