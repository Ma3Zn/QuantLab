# ADR 0005 — Baseline Exchange Calendars + Versioned Overrides

## Status
Accepted (initial).

## Context
Step 5 requires a stable calendar input. Provider timestamps are inconsistent and cannot serve as the sole calendar source. Premium calendars may be unavailable initially or introduce licensing constraints.

## Decision
- Use an open-source exchange calendar library as the **baseline** for trading days and (when available) open/close times.
- Treat calendars as **versioned configuration inputs**.
- Maintain a **versioned override bundle** for exceptional closures/early closes and baseline defects.
- Overrides are governed: only evidence-backed, reviewed changes; no overrides to hide modeling assumptions.

## Trade-offs
- Open-source calendars may be incomplete vs premium sources, but provenance flags and overrides keep assumptions explicit.
- Operational overhead (overrides) is accepted to gain auditability and determinism.

## Consequences
- Deterministic rebuilds via pinned library version + override hash.
- Calendar conflicts become actionable artifacts rather than hidden bugs.

## Follow-ups
- Decide exact baseline library at implementation time and pin its version in tooling/CI.
- Add automated calendar conflict reporting to validation outputs.
