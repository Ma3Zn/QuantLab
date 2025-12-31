# BACKLOG.md — Data Layer MVP (PR-by-PR)

This backlog defines **reviewable, vertical PRs** for implementing the Data Layer MVP.
Each PR must satisfy its Definition of Done (DoD) before moving on.

Primary references:
- docs/data/*.md
- docs/adr/*.md
- docs/testing/data_layer_test_plan.md

### Local tooling commands
- `python -m pip install -e ".[dev]"` (once per environment)
- `python -m pre-commit install` (once)
- `python -m pre-commit run --all-files`
- `python -m ruff check .`
- `python -m mypy src`
- `python -m pytest`

---

## PR-00 — Tooling baseline + CI minimale
**Goal**: repo is linted, typed, tested.
- pyproject tooling (ruff, mypy, pytest)
- GitHub Actions: lint + type + test

DoD:
- CI green
- Commands documented

---

## PR-01 — Data layer error model + logging utilities
**Goal**: typed errors, structured logs.
- src/data/errors.py
- src/data/logging.py

DoD:
- No silent failures
- Context-rich exceptions

---

## PR-02 — Canonical schema models + versioning
**Goal**: encode canonical contract in code.
- BarRecord, PointRecord, metadata
- UTC enforcement

DoD:
- Unit tests for required fields + UTC

---

## PR-03 — Quality flags + validation report structure
**Goal**: standardize flags and reports.
- flags enum
- report schema

DoD:
- Serializable report
- Unique/stable flags

---

## PR-04 — Request fingerprinting + ingest run identity
**Goal**: determinism.
- request fingerprint hash
- ingest_run_id generator

DoD:
- Fingerprint invariant under key order

---

## PR-05 — Storage layout + atomic publish
**Goal**: raw/canonical zoning + immutability.
- path builders
- raw store
- canonical store
- content hash

DoD:
- No overwrite of published snapshots

---

## PR-06 — Dataset registry (JSONL) + lookup API
**Goal**: discoverability and replay.
- append-only registry
- lookup by (dataset_id, version)

DoD:
- Registry ↔ snapshot consistency

---

## PR-07 — Instrument master + seed universe loader
**Goal**: concrete universe for tests.
- seed universe loader
- stable instrument_id mapping

DoD:
- Deterministic universe hash

---

## PR-08 — SessionRules loader + version hash
**Goal**: close-time governance.
- YAML loader
- version hash

DoD:
- ts_provenance = EXCHANGE_CLOSE when applicable

---

## PR-09 — Calendar baseline abstraction + conflict flags
**Goal**: calendar hooks without lock-in.
- baseline interface
- CALENDAR_CONFLICT flagging

DoD:
- Baseline replaceable

---

## PR-10 — ProviderAdapter interface + MVP adapter
**Goal**: provider boundary.
- adapter interface
- one MVP adapter
- no network in tests

DoD:
- Raw payloads retained
- Typed provider errors

---

## PR-11 — Normalizer (equities + FX daily)
**Goal**: raw → canonical.
- equity_eod normalizer
- fx_daily normalizer

DoD:
- Pure functions
- Deterministic output

---

## PR-12 — Validator: hard rules + soft flags
**Goal**: enforce quality policy.
- hard errors block publish
- soft flags persisted

DoD:
- ValidationReport emitted

---

## PR-13 — Ingestion runner (seed universe)
**Goal**: end-to-end run.
- fetch → raw → normalize → validate → store → registry

DoD:
- Rebuild raw→canonical matches registry metadata

---

## PR-14 — Golden snapshot tests
**Goal**: regression protection.
- golden canonical snapshot
- drift detection

DoD:
- Drift requires version bump

---

## PR-15 — Tooling hardening + final docs
**Goal**: external usability.
- pre-commit (optional)
- quickstart docs

DoD:
- External user can run ingestion end-to-end
