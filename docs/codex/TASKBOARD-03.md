# QuantLab — TASKBOARD-03 (Instruments Module MVP)

This checklist is intended as a **living verification gate** for the `instruments/` module.
It tracks what must exist for a first defensible MVP and what has been completed.

Legend:
- [x] already produced as project artifacts (docs pack) and ready to be committed
- [ ] not yet implemented / not yet merged into the repository

**Scope:** `src/instruments/` + its unit/property/golden tests + module docs.
**Non-scope:** market-data fetching (`data/`), pricing (`pricing/`), risk (`risk/`), stress (`stress/`), optimization (`optimization/`).

---

## 0) Documentation and ADRs are present and wired

### 0.1 ADRs (must be in `docs/adr/`)
- [x] `docs/adr/0101-instruments-scope-mvp.md`
- [x] `docs/adr/0102-instruments-identifier-contract.md`
- [x] `docs/adr/0103-instruments-pydantic-v2.md`
- [x] `docs/adr/0104-instruments-value-objects.md`
- [x] `docs/adr/0105-instruments-composition-over-inheritance.md`
- [x] `docs/adr/0106-instruments-position-long-only.md`
- [x] `docs/adr/0107-instruments-portfolio-snapshot.md`
- [x] `docs/adr/0108-instruments-canonical-json.md`
- [x] `docs/adr/0109-instruments-errors-and-tests.md`
- [x] `docs/adr/0110-instruments-seams-pricing-risk.md`

### 0.2 Module docs (must be in `docs/` and repo-facing README)
- [x] `docs/modules/instruments.md` exists and matches MVP intent
- [x] `docs/instruments/INDEX.md` exists and lists *all* instruments docs/artifacts
- [x] `docs/instruments/00_instruments_layer_spec_mvp.md` exists
- [x] `docs/instruments/90_codex_implementation_plan.md` exists
- [x] `src/instruments/README.md` exists and reflects responsibilities + non-goals

### 0.3 Canonical examples (docs-only, later used as golden fixtures)
- [x] `docs/instruments/examples/01_portfolio_equity_cash.json`
- [x] `docs/instruments/examples/02_portfolio_future.json`
- [x] `docs/instruments/examples/03_portfolio_multi_currency_cash.json`

---

## 1) Public contracts and modeling stance (Pydantic v2, strict)

### 1.1 Base modeling configuration (PR-23 / PR-25)
- [ ] Pydantic v2 is the modeling basis for all public models:
  - [x] `extra='forbid'` (no silent fields)
  - [x] `frozen=True` (immutable domain objects)
  - [ ] strict typing where feasible (e.g., StrictStr for IDs)
- [ ] NaN/Inf rejected in numeric inputs (quantity, cash amounts, multiplier)

### 1.2 Schema versioning (PR-23)
- [x] `INSTRUMENTS_SCHEMA_VERSION = 1` exists (single source of truth)
- [ ] `schema_version` is present in `Instrument` and `Portfolio` (and in `Position` if chosen)
- [ ] Breaking-change policy documented (bump + migration notes)

---

## 2) Identifier contract with `data/` (InstrumentId vs MarketDataId)

### 2.1 InstrumentId (PR-24)
- [x] `InstrumentId` type exists (string-backed, validated)
  - [x] non-empty, trimmed
  - [x] length bounds (e.g., 1..64)
  - [x] forbids whitespace
- [x] Recommended namespace convention documented (EQ./IDX./CASH./FUT./BOND.)

### 2.2 MarketDataId integration with `data/` (PR-24)
- [x] A typed alias `MarketDataId` exists and **reuses** `data.AssetId` if present
- [ ] No “ticker string soup” in public APIs
- [ ] `Instrument.market_data_id` is optional only where explicit in spec rules

---

## 3) Instrument Specs (discriminated union, composition-over-inheritance)

### 3.1 Spec models exist (PR-26)
- [ ] `EquitySpec(kind="equity", ...)`
- [ ] `IndexSpec(kind="index", is_tradable: bool, ...)`
- [ ] `CashSpec(kind="cash", ...)`
- [ ] `FutureSpec(kind="future", expiry: date, multiplier: float, ...)`
- [ ] `BondSpec(kind="bond", maturity: date, ...)`
- [ ] Specs contain only identity/descriptor fields (no pricing logic)

### 3.2 Spec invariants enforced (PR-26)
- [ ] Futures: `expiry` required, `multiplier > 0`
- [ ] Currency: ISO-4217 uppercase validation (`^[A-Z]{3}$`)
- [ ] Index: `is_tradable=False` allows `market_data_id=None` (explicit); `is_tradable=True` requires market data binding

---

## 4) Instrument model (canonical, validated)

### 4.1 InstrumentType + spec-kind consistency (PR-27)
- [ ] `InstrumentType` enum exists (EQUITY, INDEX, CASH, FUTURE, BOND)
- [ ] `Instrument.spec` is a discriminated union (`kind` discriminator)
- [ ] Validation enforces `instrument_type` matches `spec.kind` mapping
- [ ] Validation enforces market_data binding policy (per spec)

### 4.2 Instrument is pure domain (PR-27)
- [ ] No provider mapping logic
- [ ] No I/O or caching logic
- [ ] No pricing logic

---

## 5) Position model (long-only MVP)

### 5.1 Position fields and invariants (PR-28)
- [ ] `Position(instrument_id, quantity)` exists
- [ ] long-only: `quantity >= 0`
- [ ] quantity rejects NaN/Inf

### 5.2 Optional metadata (if included) (PR-28)
- [ ] metadata/tags are passive, non-semantic (no strategy engine coupling)

---

## 6) Portfolio snapshot (deterministic and reproducible)

### 6.1 Portfolio structure (PR-29)
- [ ] `Portfolio(as_of, positions, cash, meta, schema_version)` exists
- [ ] `as_of` must be timezone-aware
- [ ] `cash` is mapping `Currency -> float` (or Decimal if adopted later)

### 6.2 Uniqueness + canonical ordering (PR-29)
- [ ] positions are unique by `instrument_id` (reject duplicates; do not silently merge)
- [ ] positions are canonical-sorted by `instrument_id`
- [ ] cash keys canonicalized to uppercase and sorted deterministically

---

## 7) Canonical serialization (JSON) + golden fixtures

### 7.1 Canonical dict/json methods (PR-30)
- [ ] `Portfolio.to_canonical_dict()` exists
- [ ] `Portfolio.to_canonical_json()` exists and is stable (no whitespace variance)
- [ ] Serialization excludes `None` where appropriate (consistent policy)

### 7.2 Golden fixtures exist and tests pass (PR-31)
- [ ] Golden fixtures live under `docs/instruments/examples/*.json` (or copied to `tests/golden/`)
- [ ] Golden tests load fixture JSON and compare to canonical output deterministically

---

## 8) Tests (unit, property, golden)

### 8.1 Unit tests (PR-25..PR-29)
- [ ] Currency validation test matrix (accept EUR/USD; reject eur/EU/whitespace)
- [ ] FutureSpec invariants (expiry required, multiplier > 0)
- [ ] Position invariants (long-only; reject NaN/Inf)
- [ ] Portfolio invariants:
  - [ ] tz-aware as_of required
  - [ ] duplicate positions rejected
  - [ ] canonical ordering enforced

### 8.2 Property-based tests (Hypothesis) (PR-32)
- [ ] round-trip: object → canonical JSON → object preserves semantics
- [ ] determinism: same logical portfolio → identical canonical JSON
- [ ] rejects invalid numeric values (NaN/Inf)

---

## 9) Packaging / API exports / docs consistency

### 9.1 Public exports (PR-33)
- [ ] `src/instruments/__init__.py` exports the intended stable API
- [ ] README quickstart imports match real module paths

### 9.2 Docs consistency gate (PR-33)
- [ ] `docs/modules/instruments.md` references the final import paths
- [ ] `docs/instruments/QUICKSTART.md` reflects how to run tests in this repo
- [ ] `docs/instruments/INDEX.md` lists all newly added tests/fixtures paths

---

## 10) Explicit limitations (must remain visible)
- [ ] Long-only positions are explicitly documented (README + module doc)
- [ ] Futures are representational only (no roll/margining) documented
- [ ] Bonds are representational only (no accrued interest / conventions) documented
- [ ] FX conversion is out of scope for instruments documented

---

## 11) Completion criterion (“instruments MVP done”)
- [ ] All above checkboxes are complete
- [ ] `pytest -q` passes (unit + golden + property tests)
- [ ] No imports from provider/data fetching code inside `src/instruments/`
- [ ] Canonical JSON fixtures pass and are stable across runs
