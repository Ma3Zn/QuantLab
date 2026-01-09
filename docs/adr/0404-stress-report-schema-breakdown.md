# ADR-0404 — StressReport schema and breakdown requirements

Status: Proposed
Date: 2026-01-09

## Context
Stress is only useful if it explains the drivers and can be audited.

## Decision
`StressReport` MUST include:
- metadata: `report_version`, `as_of`, input lineage hashes
- scenario table: total P&L, ΔNAV, return (P&L / NAV), per scenario
- breakdowns:
  - by position (position id / instrument id)
  - by asset id (market data id)
  - by currency (if supported)
- summary:
  - worst scenario (max loss) and its id
  - distribution summary across scenarios (min/median/max)

The report MUST include a structured `warnings` list.

## Consequences
- Results are interpretable.
- Golden tests can pin the schema.

## Alternatives considered
1. Only total P&L per scenario (rejected: not explainable).
