# AGENTS.md — QuantLab / QuantDev Codex Operating Manual (Project Instructions)

## Mission
Implement the **Data layer MVP** of this repository as a production-grade foundation:
- provider adapters (I/O boundary),
- normalization to canonical schema,
- validation + quality flags,
- raw/canonical storage zoning + registry,
- calendars/time semantics scaffolding,
- tests (unit + integration + golden) and tooling.

Primary source of truth: documentation under `docs/` and ADRs under `docs/adr/`.

## Non-negotiable architecture rules
- Strict layer separation: `data/` must not depend on `pricing/`, `risk/`, `stress/`, `optimization/`, `decision/`.
- Composition over inheritance.
- Domain objects in `instruments/` are pure (no I/O).
- Deterministic + replayable ingestion: raw payloads retained, `asof_ts` present, dataset versioning via registry.
- No silent cleaning: hard errors block publishing; soft issues are flags.

## Definition of Done (per task)
1) Code compiles, lint/type checks pass, tests pass locally.
2) Public APIs are typed; errors are typed; logging is structured.
3) Docs updated if behavior/contract changes (update ADR if decision changes).
4) No ad-hoc scripts committed unless placed under `examples/` or `tools/` with docs.
5) Every new feature includes at least one unit test; integration tests when touching ingestion/storage.

## Working style for long sessions
- Create a dedicated branch per task.
- At start: summarize plan (files to touch, commands to run, tests to add).
- Commit in small, reviewable steps.
- Keep diffs minimal and coherent (no drive-by refactors).
- If uncertain, write an ADR stub and proceed with the conservative choice.

## Commands you may run
Safe commands (preferred):
- `python -m pytest -q`
- `python -m ruff check .` / `python -m ruff format .`
- `python -m mypy src`
- `python -m pip install -e ".[dev]"` (or the equivalent for the chosen toolchain)

Avoid:
- destructive filesystem operations (rm -rf outside `data/cache`/`data/external`)
- network calls in tests
- introducing heavy dependencies without an ADR.

## MVP scope (Data layer only)
Implement MVP described by:
- `docs/data/00_data_layer_spec_mvp_onepager.md`
- `docs/data/02a_canonical_schema_contract_onepager.md`
- `docs/adr/0007-storage-mvp-choice.md`
- `docs/adr/0008-mvp-provider-choice.md`
- `docs/data/09_snapshot_layout_and_registry_schema.md`
- `docs/testing/data_layer_test_plan.md`

Do not implement intraday, futures, options, or portfolio/risk logic.
