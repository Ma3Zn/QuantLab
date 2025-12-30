# Data Layer MVP - Execution Plan (Remaining Items)

## Plan overview
1) UTC enforcement + ts_provenance plumbing
2) Property-based tests
3) Example script

Provider focus (MVP): Stooq via offline CSV fixtures and LocalFileProviderAdapter.
Fixture location: `data/external`.
First dataset_id: `md.equity.eod.bars` (EOD equities).

## Step 1: UTC enforcement + ts_provenance
Read:
- docs/data/00_data_layer_spec_mvp.md
- docs/data/06_calendar_timezone_alignment_policy.md
- docs/data/08_venue_close_times_session_rules.md

Implementation sketch:
- Add ts_provenance enum and field to canonical record schema.
- Extend normalizers to set ts_provenance and local time metadata.
- Extend validators to:
  - enforce UTC timestamps,
  - add PROVIDER_TIMESTAMP_USED when ts_provenance != EXCHANGE_CLOSE,
  - capture calendar conflict flags where hooks exist.
- Propagate provenance into registry metadata or snapshot parts if required.
- Stooq-specific: map CSV timestamps to UTC and set ts_provenance to
  PROVIDER_EOD unless close times are explicitly known.

Likely touch points:
- src/quantlab/data/schemas/records.py
- src/quantlab/data/normalizers.py
- src/quantlab/data/validators.py
- src/quantlab/data/quality.py
- tests/test_canonical_schema.py
- tests/test_normalizers.py
- tests/test_validators.py
- tests/test_quality_flags_and_reports.py
 - tests/fixtures (Stooq CSV fixtures)

Acceptance notes:
- Canonical records serialize ts_provenance.
- Records without a known close time fall back to provider timestamp and are
  flagged.
- No naive timestamps allowed anywhere in canonical output.

## Step 2: Property-based tests
Implementation sketch:
- Add Hypothesis tests for record invariants in a new file.
- Keep strategies bounded and deterministic; avoid external calls.
- Ensure fixtures remain offline and consistent with Stooq CSV schema.

Suggested tests:
- BarRecord: low <= min(open, close) and high >= max(open, close).
- CanonicalRecord: ts and asof_ts are timezone-aware UTC.
- PointRecord: bid/ask sanity when both fields exist.
- Validator: duplicate ts per instrument results in hard error.

Likely touch points:
- tests/test_property_invariants.py
- pyproject.toml (only if Hypothesis is not already in dev deps)

## Step 3: Example script
Implementation sketch:
- Add examples/scripts/ingest_seed_universe.py calling ingestion runner with
  Stooq CSV fixtures from `data/external` (via LocalFileProviderAdapter).
- Write logs to stdout and output to data/ under registry.
- Document how to run it (no network calls).

Likely touch points:
- examples/scripts/ingest_seed_universe.py
- docs/codex/TASKBOARD.md (mark done)
- docs/README or docs/data references if needed

## Commands (after each step)
- python -m pytest -q
- python -m ruff check .
- python -m mypy src
