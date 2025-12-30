# Data Layer MVP - Remaining Gaps

## Scope
This document captures TASKBOARD items still open that are required or strongly
recommended to complete the Data Layer MVP.

## Required for MVP
1) UTC enforcement + ts_provenance plumbing
- Why: Canonical time semantics are a core invariant; reproducibility and
  alignment depend on it.
- Deliverables:
  - ts_provenance enum and field in canonical records.
  - UTC-only timestamp enforcement in schemas and validators.
  - Quality flag PROVIDER_TIMESTAMP_USED when provenance != EXCHANGE_CLOSE.
  - Provenance metadata carried through normalizers -> validators -> registry.

2) Property-based tests for key invariants
- Why: Guardrails against drift in canonical invariants and validator logic.
- Target invariants:
  - timestamps are timezone-aware and UTC,
  - no silent tz conversion or naive timestamps,
  - OHLC ordering (low <= open/close <= high),
  - bid/ask sanity for PointRecord.

## Recommended for usability
3) Minimal example script under examples/scripts/ingest_seed_universe.py
- Why: Quick end-to-end validation and onboarding.
- Keep it deterministic and offline (reuse fixtures).

## References
- docs/codex/TASKBOARD.md
- docs/data/00_data_layer_spec_mvp.md
- docs/data/06_calendar_timezone_alignment_policy.md
- docs/data/08_venue_close_times_session_rules.md
- docs/testing/data_layer_test_plan.md
