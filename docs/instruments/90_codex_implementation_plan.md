# Codex Implementation Plan — instruments/ (90)

This document is written for an agentic coding workflow (Codex).
It translates the ADRs into an incremental implementation plan with concrete file targets and acceptance criteria.

## Guardrails (non-negotiable)
- No I/O in `src/instruments/` (no provider calls, no filesystem).
- No pricing or risk logic in this module.
- Composition over inheritance.
- Deterministic serialization (canonical ordering).
- Validation must be strict: invalid states fail fast.

## Primary implementation files
- `src/instruments/types.py`:
  - Pydantic v2 models for `Instrument`, `Position`, `Portfolio`
  - `InstrumentType` enum
  - `Spec` models + discriminated union
  - schema version constant
  - canonicalization/validators
- `src/instruments/__init__.py`: export public types
- `tests/unit/instruments/test_*.py`: invariants and deterministic behavior
- `tests/golden/instruments/` (or similar): golden JSON snapshots (minimal set)

## Step-by-step PR plan

### PR-INS-01 — Scaffolding + schema version + base config
Implements ADR-0103, ADR-0108.
- Add `INSTRUMENTS_SCHEMA_VERSION = 1`.
- Define a shared BaseModel config:
  - `extra='forbid'`, `frozen=True`
- Implement `Currency` validation type (regex `^[A-Z]{3}$`).

Acceptance:
- unit tests for currency validation.
- objects reject extra fields.

### PR-INS-02 — Instrument specs + discriminated union
Implements ADR-0105, ADR-0104.
- Create `EquitySpec`, `IndexSpec`, `CashSpec`, `FutureSpec`, `BondSpec`.
- Use discriminator key `kind`.
- Implement `Instrument` with `instrument_id`, `market_data_id`, `currency`, `spec`, `instrument_type`.
- Validate `instrument_type` matches `spec.kind`.

Acceptance:
- unit tests for required fields and invariants (future expiry, multiplier > 0).
- invalid combos fail (e.g., index non-tradable but with required market_data_id policy mismatch).

### PR-INS-03 — Positions + Portfolio snapshot + determinism
Implements ADR-0106, ADR-0107.
- Implement `Position` (long-only).
- Implement `Portfolio`:
  - tz-aware `as_of`
  - unique positions by `instrument_id` (reject duplicates)
  - canonical sorting of positions and cash

Acceptance:
- tests for long-only.
- tests for duplicate positions rejection.
- tests for canonical ordering (positions sorted).

### PR-INS-04 — Canonical JSON + golden fixtures
Implements ADR-0108.
- Provide stable `.model_dump_json()` (possibly via `.to_canonical_dict()`).
- Add fixtures under `docs/instruments/examples/`.
- Add golden tests that compare canonical JSON output to fixtures.

Acceptance:
- byte-identical JSON with fixture (no whitespace sensitivity unless normalized).
- round-trip object<->json semantics preserved.

### PR-INS-05 — Property-based tests + error messages
Implements ADR-0109.
- Hypothesis: generate portfolios and ensure round-trip and determinism.
- Ensure invalid numeric values (NaN/Inf) are rejected.
- Optional: thin error wrappers if pydantic messages are insufficient.

Acceptance:
- property tests pass reliably.
- error messages mention offending instrument_id/field.

### PR-INS-06 — Docs wiring + exports
- Ensure `src/instruments/__init__.py` exports the intended public API.
- Ensure docs reference correct import paths (update README quickstart accordingly).

## “Definition of Done”
- All ADR acceptance criteria met.
- Tests: unit + property + golden.
- Docs: module README + docs/instruments + ADRs + index updated.
