# ADR-0306 — Exposure views and mapping seam (MVP)

Status: Proposed
Date: 2026-01-09

## Context
The MVP requires exposure decomposition by asset and currency, and optionally by sector/region if mapping exists.
Mapping is typically provided by an external taxonomy (e.g., GICS, custom tags) and should not live inside `risk/`.

## Decision
`risk/` will compute:
- asset exposure: weights or notionals per market data id,
- currency exposure: aggregation by instrument currency.

Sector/region exposures are optional and implemented via a **mapping seam**:
- `ExposureMappingProvider` interface that maps `MarketDataId -> {sector, region, ...}`.
- If no provider is supplied, the report includes `mapping_missing` warnings and omits those breakdowns.

## Consequences
- The core remains pure and modular.
- Adding sector/region is a plug-in, not a refactor.

## Alternatives considered
1. Hardcode sector/region fields into instruments (rejected: contaminates domain layer).
