# Codex Taskboard — Data Layer MVP

This file is intended to be used as a living checklist during Codex sessions.
Update it as tasks are completed. Keep tasks small and reviewable.

## Milestone: Data Layer MVP “end-to-end”
### Tooling baseline (required before writing much code)
- [x] Add `pyproject.toml` dev tooling (ruff, pytest, mypy) and minimal config
- [x] Add pre-commit config (optional but recommended)
- [x] Add GitHub Actions CI: lint + typecheck + tests

### Core domain & schemas
- [ ] Implement canonical record models (BarRecord, PointRecord) + metadata contract
- [ ] Implement quality flag vocabulary + typed enums
- [ ] Implement typed exceptions and structured logging utilities for data layer

### Storage + registry
- [ ] Implement snapshot directory conventions (raw/canonical) per docs
- [ ] Implement registry (JSONL first; SQLite optional)
- [ ] Implement atomic publish workflow (staging → publish)
- [ ] Add content hashing utilities

### Provider + ingestion
- [ ] Implement ProviderAdapter interface + one MVP adapter
- [ ] Implement request fingerprinting
- [ ] Implement Normalizer raw→canonical for EOD equities and FX daily
- [ ] Implement Validator hard rules + soft flags + reports
- [ ] Implement ingestion runner that produces: raw payloads + canonical snapshot + registry entry

### Calendars/time semantics scaffolding
- [ ] Implement UTC enforcement + ts_provenance plumbing
- [ ] Implement minimal SessionRules config loader for seed MICs
- [ ] Implement calendar conflict flagging hooks (even if baseline calendar is stubbed)

### Tests
- [ ] Unit tests for schema invariants
- [ ] Property-based tests (Hypothesis) for key invariants
- [ ] Integration test: seed universe ingestion run (network calls mocked/recorded)
- [ ] Golden snapshot test: stable canonical output for a fixed seed payload

### Documentation & examples
- [ ] `docs/` updated to reflect actual config paths and commands
- [ ] Minimal example script under `examples/scripts/ingest_seed_universe.py`
