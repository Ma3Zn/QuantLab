# QuantLab Backlog — Instruments Module (MVP)

**Scope:** Implement `src/instruments/` as a pure domain layer: instruments, positions, portfolio snapshots.
**Start PR numbering:** PR-22 (continues BACKLOG-02 ending at PR-21)

This backlog is intentionally split into **small, low-ambiguity PRs** to keep Codex sessions safe and reviewable.

---

## Global acceptance criteria (end state)
By the end of PR-33:
- `src/instruments/` provides Pydantic v2 domain models for `Instrument`, `Position`, `Portfolio`.
- Instruments are modeled via composition + discriminated-union specs.
- Identifier contract is enforced: `InstrumentId` vs `MarketDataId` (reuse `data.AssetId` where available).
- Positions are long-only (MVP).
- Portfolios are deterministic snapshots with canonical ordering + uniqueness checks.
- Canonical JSON serialization is stable and backed by golden fixtures.
- Unit + property (Hypothesis) + golden tests pass.
- Docs and ADRs for instruments are present and consistent with the implementation.

---

## PR-22 — Add instruments documentation pack (ADRs + module docs + examples)

### Goal
Commit the already-prepared instruments documentation, ADRs, and example JSON files into the repository.

### References
- `docs/instruments/INDEX.md`
- `docs/modules/instruments.md`
- ADRs: `docs/adr/0101` .. `docs/adr/0110`

### Tasks
1. Add documentation files under:
   - `docs/modules/instruments.md`
   - `docs/instruments/*.md`
   - `docs/instruments/examples/*.json`
2. Add ADR files under `docs/adr/0101-...` through `0110-...`.
3. Add repo-facing `src/instruments/README.md`.

### Acceptance criteria
- `docs/instruments/INDEX.md` lists all added files with correct paths.
- No references to non-existent files/paths remain.

---

## PR-23 — Create `src/instruments/` scaffolding + base Pydantic config + schema version

### Goal
Establish the base modeling stance (Pydantic v2, strict, immutable) and a schema version constant.

### References
- ADR-0103: `docs/adr/0103-instruments-pydantic-v2.md`
- ADR-0108: `docs/adr/0108-instruments-canonical-json.md`
- `docs/instruments/02_pydantic_models_contract.md`

### Tasks
1. Create `src/instruments/__init__.py` (empty exports for now).
2. Create `src/instruments/types.py` with:
   - `INSTRUMENTS_SCHEMA_VERSION = 1`
   - a shared Pydantic base config (extra=forbid, frozen=True, strict where feasible)
3. Add a minimal unit test file `tests/unit/instruments/test_base_config.py`:
   - extra fields are rejected
   - model instances are immutable (attempted mutation fails)

### Acceptance criteria
- Unit tests pass and demonstrate config invariants.

---

## PR-24 — Implement identifier types + integrate `MarketDataId` with `data.AssetId`

### Goal
Create strict `InstrumentId` (string-backed) and integrate market-data identifiers by reusing `data.AssetId` where available.

### References
- ADR-0102: `docs/adr/0102-instruments-identifier-contract.md`
- `docs/instruments/01_identifier_policy_mvp.md`

### Tasks
1. Add `src/instruments/ids.py`:
   - `InstrumentId` type (validated string; non-empty; length bound; no whitespace)
   - `MarketDataId` alias:
     - try importing `AssetId` from the canonical location in `src/data/`
     - if not found, implement a minimal forward-compatible `AssetId` in `src/data/ids.py` and use that
2. Add unit tests:
   - accepts `EQ.AAPL`, rejects whitespace or empty strings
   - `MarketDataId` import path works (no circular imports)

### Acceptance criteria
- `InstrumentId` validation is enforced.
- `MarketDataId` resolves to `data.AssetId` (or the minimal shim if absent).

---

## PR-25 — Add Currency type + numeric finite checks (reject NaN/Inf)

### Goal
Standardize currency and numeric hygiene for MVP (no NaN/Inf).

### References
- ADR-0104: `docs/adr/0104-instruments-value-objects.md`
- `docs/instruments/02_pydantic_models_contract.md`

### Tasks
1. Add `src/instruments/value_types.py`:
   - `Currency` validated via regex `^[A-Z]{3}$`
   - helper validator(s) for finite floats (reject NaN/Inf)
2. Unit tests:
   - accept EUR/USD, reject eur/EU/EURO/whitespace
   - reject NaN/Inf for quantity and cash values (where applied)

### Acceptance criteria
- Currency is strict and enforced.
- NaN/Inf rejected consistently (test coverage).

---

## PR-26 — Implement Spec models (discriminated union) + spec-level invariants

### Goal
Create instrument spec models and enforce type-specific invariants.

### References
- ADR-0105: `docs/adr/0105-instruments-composition-over-inheritance.md`
- `docs/instruments/03_instrument_specs_mvp.md`

### Tasks
1. Add `src/instruments/specs.py` with Pydantic v2 models:
   - `EquitySpec(kind="equity", ...)`
   - `IndexSpec(kind="index", is_tradable: bool, ...)`
   - `CashSpec(kind="cash", ...)`
   - `FutureSpec(kind="future", expiry: date, multiplier: float, ...)` (multiplier > 0)
   - `BondSpec(kind="bond", maturity: date, ...)`
2. Add unit tests:
   - FutureSpec rejects multiplier <= 0
   - Required fields are enforced

### Acceptance criteria
- Spec models validate invariants independently (before Instrument is introduced).

---

## PR-27 — Implement Instrument model + cross-validation (type vs spec.kind) + market-data binding rules

### Goal
Implement `Instrument` as the canonical object: composition + discriminated union spec + binding policy.

### References
- ADR-0102, ADR-0105, ADR-0110
- `docs/instruments/02_pydantic_models_contract.md`
- `docs/instruments/03_instrument_specs_mvp.md`
- `docs/instruments/08_integration_seams_pricing_risk.md`

### Tasks
1. In `src/instruments/types.py` (or `instrument.py` if you prefer split files), add:
   - `InstrumentType` enum
   - `Instrument` model:
     - `schema_version` (required; defaults to module constant)
     - `instrument_id: InstrumentId`
     - `instrument_type: InstrumentType`
     - `market_data_id: MarketDataId | None`
     - `currency: Currency | None` (policy depends on type; cash must have currency)
     - `spec: SpecUnion` (discriminated on `kind`)
     - optional `meta: dict[str, Any] | None`
2. Add validators:
   - `instrument_type` must match `spec.kind` mapping
   - market_data binding rules:
     - equity/future tradable: `market_data_id` required
     - index: if `is_tradable=True` market_data_id required; else optional
     - cash: market_data_id typically None (allowed); currency required
3. Unit tests cover:
   - mismatched type/spec rejected
   - index tradable flag policy enforced
   - cash currency required

### Acceptance criteria
- Instrument construction enforces all cross-cutting invariants.

---

## PR-28 — Implement Position (long-only) + invariants

### Goal
Create `Position` and enforce long-only semantics for MVP.

### References
- ADR-0106: `docs/adr/0106-instruments-position-long-only.md`
- `docs/instruments/04_position_and_portfolio_semantics.md`

### Tasks
1. Add `Position` model:
   - `instrument_id: InstrumentId`
   - `quantity: float` (finite, >= 0)
   - optional passive metadata if desired
2. Unit tests:
   - negative quantity rejected
   - NaN/Inf rejected

### Acceptance criteria
- Position is minimal, validated, deterministic.

---

## PR-29 — Implement Portfolio snapshot + uniqueness + canonical ordering

### Goal
Create deterministic `Portfolio` snapshot with strict invariants.

### References
- ADR-0107: `docs/adr/0107-instruments-portfolio-snapshot.md`
- `docs/instruments/04_position_and_portfolio_semantics.md`

### Tasks
1. Add `Portfolio` model:
   - `schema_version` (required; defaults to module constant)
   - `as_of: datetime` (timezone-aware required)
   - `positions: list[Position]`
   - `cash: dict[Currency, float]`
   - optional `meta: dict[str, Any] | None`
2. Validators:
   - reject naive datetimes (`tzinfo is None`)
   - reject duplicate positions by `instrument_id`
   - canonical sort positions by `instrument_id`
   - normalize cash keys to uppercase (Currency) and sort deterministically
3. Unit tests cover:
   - naive datetime rejected
   - duplicate positions rejected
   - positions sorted after validation
   - cash normalized and stable ordering

### Acceptance criteria
- Portfolio serialization is deterministic for equivalent inputs.

---

## PR-30 — Add canonical serialization helpers (`to_canonical_dict/json`) and stability tests

### Goal
Guarantee stable, whitespace-independent canonical JSON for golden tests and reproducibility.

### References
- ADR-0108: `docs/adr/0108-instruments-canonical-json.md`
- `docs/instruments/05_canonical_json_contract.md`

### Tasks
1. Implement on `Portfolio`:
   - `to_canonical_dict()` returning a plain dict with canonical ordering
   - `to_canonical_json()` using `json.dumps(..., separators=(',', ':'), ensure_ascii=False)`
2. Ensure policy is consistent:
   - exclude `None` fields if and only if documented (choose one policy and stick to it)
3. Unit tests:
   - same logical portfolio created from differently ordered inputs yields identical canonical JSON

### Acceptance criteria
- Canonical JSON is byte-identical across runs for same logical snapshot.

---

## PR-31 — Add golden fixtures + golden tests against canonical JSON

### Goal
Introduce a minimal golden suite to lock the contract.

### References
- `docs/instruments/examples/*.json`
- `docs/instruments/07_testing_plan_mvp.md`

### Tasks
1. Copy or reference fixtures for tests:
   - Either load directly from `docs/instruments/examples/`
   - Or copy to `tests/golden/instruments/` (preferred if tests should not depend on docs paths)
2. Add golden tests:
   - load fixture JSON
   - build equivalent `Portfolio` instance
   - assert `portfolio.to_canonical_dict()` equals fixture dict (preferred)
   - optionally assert `to_canonical_json()` equals a compact canonical JSON string derived from fixture dict

### Acceptance criteria
- Golden tests pass and are stable.
- Fixture set is small (3 portfolios) and representative.

---

## PR-32 — Add Hypothesis property-based tests (round-trip + determinism + invalid values)

### Goal
Strengthen robustness against edge cases and regressions.

### References
- ADR-0109: `docs/adr/0109-instruments-errors-and-tests.md`
- `docs/instruments/07_testing_plan_mvp.md`

### Tasks
1. Add Hypothesis strategies for:
   - valid instrument_ids and quantities
   - positions lists without duplicates
   - cash mappings with valid Currency keys
2. Property tests:
   - round-trip: `Portfolio -> canonical_json -> Portfolio` preserves semantics
   - determinism: same logical portfolio -> identical canonical JSON
   - rejects NaN/Inf and negative quantity
3. Ensure test runtime is bounded (set max_examples sensibly).

### Acceptance criteria
- Property tests pass reliably and complete quickly in CI.

---

## PR-33 — Public API exports + docs alignment + minimal quickstart validation

### Goal
Finalize the module surface and ensure docs match the real import paths.

### References
- `src/instruments/README.md`
- `docs/modules/instruments.md`
- `docs/instruments/QUICKSTART.md`
- ADR-0110: seams (contracts only)

### Tasks
1. Update `src/instruments/__init__.py` to export:
   - `Instrument`, `InstrumentType`
   - `Position`, `Portfolio`
   - spec models (or keep them internal and document—choose and be consistent)
2. Ensure quickstart snippets in README/docs compile (no stale paths).
3. Optional: add a tiny example script under `examples/` that:
   - constructs a portfolio
   - prints canonical JSON (no I/O)

### Acceptance criteria
- A developer can follow the quickstart and run tests successfully.
- The module clearly states limitations (long-only, futures/bonds representational only).

---

## Notes (Codex safety)
- Keep PRs small and strictly scoped; do not “helpfully” add pricing/risk logic.
- Do not introduce pandas/numpy as dependencies in `instruments/`.
- Reject duplicates rather than silently merging positions.
- Ensure timezone-aware `as_of` is enforced; do not default to `datetime.now()`.
