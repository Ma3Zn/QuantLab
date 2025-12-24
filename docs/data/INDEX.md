# Data Layer Documentation Index

This directory documents the **Data layer** of QuantLab: how market data is scoped, identified, normalized, and exposed to downstream modules.

## Files
- `docs/data/README.md` — module responsibilities, boundaries, and invariants.
- `docs/data/00_data_layer_spec_mvp.md` — 1–2 page MVP spec (datasets, time semantics, alignment, boundaries).
- `docs/data/01_instrument_universe_mvp.md` — MVP instrument universe and identifier policy.
- `docs/data/02_canonical_schema_contract.md` — canonical schema and metadata (required/optional + examples).
- `docs/data/03_provider_adapter_contract.md` — provider adapter + normalizer/validator boundaries.
- `docs/data/04_storage_cache_strategy.md` — raw vs canonical zoning, dataset registry, versioning.
- `docs/data/05_data_quality_policy_mvp.md` — MVP validation rules and quality flags.
- `docs/data/06_calendar_timezone_alignment_policy.md` — calendar/timezone semantics + alignment policies.
- `docs/data/07_calendar_baseline_and_overrides.md` — baseline calendar source + overrides governance.
- `docs/data/08_venue_close_times_session_rules.md` — MIC SessionRules for close times + fallback hierarchy.
- `docs/data/09_snapshot_layout_and_registry_schema.md` — physical layout + registry schema.
- `docs/data/10_mvp_universe_seed.md` — seed instrument universe.
- `docs/data/11_sessionrules_seed.md` — SessionRules seed for MVP venues.
- `docs/adr/0001-market-data-universe-and-schema.md` — ADR for Steps 1–2.
- `docs/adr/0002-provider-adapter-and-storage.md` — ADR for ingestion boundaries and zoning.
- `docs/adr/0003-data-quality-policy-mvp.md` — ADR for detect+flag quality stance.
- `docs/adr/0004-calendar-timezone-alignment.md` — ADR for canonical time semantics and joins.
- `docs/adr/0005-calendar-baseline-and-overrides.md` — ADR for baseline calendars + overrides.
- `docs/adr/0006-sessionrules-close-times.md` — ADR for SessionRules close-time governance.
- `docs/adr/0007-storage-mvp-choice.md` — ADR for the initial physical storage choice.

## Next planned docs (not yet written)
- Calendar/timezone alignment policy (global venues).
- Corporate actions event model + adjustment pipeline (derived datasets).
- Multi-provider reconciliation policy.
