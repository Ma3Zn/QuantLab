# Data Layer (QuantDev)

## What this module does
- Defines a **canonical representation** for market data consumed by pricing, risk, stress, and optimization layers.
- Defines the **instrument universe** (MVP) and the **identifier strategy** needed for stable joins across sources.
- Enforces **reproducibility hooks** at the contract level (e.g., `asof_ts`, `source`, `ingest_run_id`).

## What this module does *not* do
- No pricing, risk, stress, portfolio optimization, or decision logic.
- No alpha logic and no “buy/sell” outputs.
- No silent corporate-action adjustments; adjustments are either explicit fields or separate datasets.

## Assumptions
- Market data is represented as time series indexed by an internal `instrument_id` and a timestamp `ts`.
- Timestamps are stored in **UTC** in canonical datasets; local exchange time is metadata.
- Every observation can be traced to a source and ingestion run via metadata.

## Core invariants (non-negotiable)
- **Stable internal identifiers**: downstream code never keys on vendor tickers.
- **No look-ahead by construction**: canonical records support `asof_ts` for “as-of” replay.
- **Schema versioning**: canonical datasets have an explicit schema version and dataset version.

## Deliverables for the MVP (Steps 1–6)
- Instrument universe spec + identifier policy.
- Canonical schema + metadata contract for EOD bars and FX spot.
- Provider adapter / normalizer / validator boundary contract.
- Storage zoning (raw vs canonical) + dataset registry.
- MVP data quality policy (detect + flag).
- Calendar/timezone alignment policy (global venues) + explicit join policies.
- Baseline calendar source + versioned overrides governance.
- MIC SessionRules for venue close times + deterministic fallbacks.

## Known limitations (current MVP)
- Corporate actions handled minimally (adj close or explicit adjustment factors), no survivorship-safe universe yet.
- EOD-only; intraday microstructure and futures rolls are explicitly out of scope for this phase.

## References
See `docs/data/INDEX.md` for the documentation map.
