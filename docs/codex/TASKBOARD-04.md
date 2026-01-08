# QuantLab — TASKBOARD-04 (Pricing Module MVP)

This checklist is intended as a **living verification gate** for the `pricing/` module.
It tracks what must exist for a first defensible MVP and what has been completed.

Legend:
- [x] completed / merged
- [ ] not yet implemented / not yet merged

**Scope:** `src/pricing/` + its unit/property/golden tests + module docs + ADRs.
**Non-scope:** market-data fetching (`data/providers`), portfolio domain (`instruments/`), risk (`risk/`), stress (`stress/`), optimization (`optimization/`), decision outputs (`decision/`).

---

## 0) Documentation and ADRs are present and consistent

### 0.1 Module docs entry points (PR-34)
- [x] `docs/modules/pricing.md` exists and matches implemented behavior
- [x] `docs/pricing/INDEX.md` exists and links to all pricing docs + ADRs
- [x] `docs/pricing/QUICKSTART.md` exists (conceptual, not implementation)
- [x] `docs/pricing/examples/` exists and contains at least one EUR/USD example set

### 0.2 ADR set (PR-35 … PR-43)
- [x] `docs/adr/0201-pricing-scope-mvp.md`
- [x] `docs/adr/0202-pricing-multi-currency-base-nav.md`
- [x] `docs/adr/0203-pricing-fx-quote-convention-eurusd.md`
- [x] `docs/adr/0204-pricing-as-of-semantics-daily.md`
- [x] `docs/adr/0205-pricing-missing-data-policy.md`
- [x] `docs/adr/0206-pricing-pricer-registry-composition.md`
- [x] `docs/adr/0207-pricing-outputs-canonical-json.md`
- [x] `docs/adr/0208-pricing-futures-simplification.md`
- [x] `docs/adr/0209-pricing-testing-strategy.md`

### 0.3 Spec docs (PR-58 finalization)
- [x] `docs/pricing/01_scope_mvp.md` present and accurate
- [x] `docs/pricing/02_currency_and_fx_policy.md` present and accurate
- [x] `docs/pricing/03_market_data_contract.md` present and accurate
- [x] `docs/pricing/04_pricer_api_and_registry.md` present and accurate
- [x] `docs/pricing/05_valuation_outputs_contract.md` present and accurate
- [x] `docs/pricing/06_fx_conversion_engine.md` present and accurate
- [x] `docs/pricing/07_missing_data_and_quality_flags.md` present and accurate
- [x] `docs/pricing/08_testing_plan_mvp.md` present and accurate
- [x] `docs/pricing/09_integration_seams_risk_stress_optimization.md` present and accurate

---

## 1) Package skeleton and layering constraints

### 1.1 `src/pricing/` package exists (PR-44)
- [x] `src/pricing/__init__.py` exists and has no side effects
- [x] `src/pricing/README.md` exists and describes responsibilities/non-responsibilities
- [ ] Subpackages exist (empty allowed initially):
  - [x] `src/pricing/pricers/`
  - [x] `src/pricing/fx/`
  - [x] `src/pricing/schemas/`
  - [x] `src/pricing/adapters/` (only for protocol adapters)

### 1.2 Dependency rules are respected (ongoing)
- [ ] `pricing/` imports instrument domain objects from `instruments/` only (no I/O)
- [ ] `pricing/` consumes `data/` only through a protocol or stable schema objects (no provider imports)
- [ ] No `pricing/` dependency on `risk/`, `stress/`, `optimization/`, `decision/`
- [ ] All computation is deterministic for identical inputs

---

## 2) Error taxonomy and warning vocabulary

### 2.1 Typed exceptions (PR-45)
- [x] `src/pricing/errors.py` exists
- [x] Errors include actionable context fields (as-of, asset_id, field, instrument_id)
- [ ] Minimum error types exist:
  - [x] `MissingPriceError`
  - [x] `MissingFxRateError`
  - [x] `UnsupportedCurrencyError` (guardrail for MVP)
  - [x] `NonFiniteInputError`
  - [x] `InvalidFxRateError`

### 2.2 Warning codes (PR-45)
- [x] `src/pricing/warnings.py` exists
- [x] Warning codes are stable strings (uppercase + underscores)
- [ ] Minimum warning codes exist:
  - [x] `FX_INVERTED_QUOTE`
  - [x] `MD_IMPUTED_FFILL` (only if upstream meta exists)
  - [x] `MD_STALE_SOURCE_DATE` (optional)

---

## 3) Valuation output schemas and canonical JSON

### 3.1 `PositionValuation` schema (PR-46)
- [x] Model exists under `src/pricing/schemas/`
- [x] Fields present (minimum):
  - [x] `schema_version`
  - [x] `as_of`
  - [x] `instrument_id`
  - [x] `market_data_id (if applicable)`
  - [x] `instrument_kind`
  - [x] `quantity`
  - [x] `instrument_currency`
  - [x] `unit_price`
  - [x] `notional_native`
  - [x] `base_currency`
  - [x] `fx_asset_id_used`
  - [x] `fx_inverted`
  - [x] `fx_rate_effective`
  - [x] `notional_base`
  - [x] `inputs`
  - [x] `warnings`
- [x] Finite-number validation is enforced for all numeric fields
- [x] Dates serialize as ISO `YYYY-MM-DD`

### 3.2 `PortfolioValuation` schema (PR-46, PR-53)
- [x] Model exists under `src/pricing/schemas/`
- [x] Fields present (minimum):
  - [x] `schema_version`
  - [x] `as_of`
  - [x] `base_currency`
  - [x] `nav_base`
  - [x] `positions`
  - [x] `breakdown_by_currency`
  - [x] `warnings`
  - [x] `lineage`
- [x] `breakdown_by_currency` contains both native and base totals per currency
- [x] `lineage` exists (may be placeholder until PR-56)

---

## 4) Market data input protocol (`MarketDataView`)

### 4.1 Protocol exists (PR-47)
- [x] `src/pricing/market_data.py` exists
- [x] `MarketDataView` Protocol defines:
  - [x] `get_value(asset_id, field, as_of) -> float`
  - [x] `has_value(asset_id, field, as_of) -> bool`
  - [x] optional `get_point(...) -> MarketPoint`

### 4.2 MarketPoint metadata is structured (PR-47)
- [x] `MarketPoint.value` is finite
- [x] `MarketPoint.meta` is optional
- [x] `MarketDataMeta` supports (at least):
  - [x] quality flags (list/set)
  - [x] source date vs aligned date (if available)
  - [x] dataset snapshot id / lineage id (if available)

---

## 5) FX conversion (EUR/USD policy B)

### 5.1 Canonical FX series (PR-48)
- [x] Canonical FX asset id is `FX.EURUSD`
- [x] Quote convention: USD per 1 EUR
- [x] Conversion rules implemented:
  - [x] native==base → rate 1, no FX asset id
  - [x] EUR→USD uses EURUSD directly
  - [x] USD→EUR uses inverse of EURUSD and records inversion

### 5.2 Error handling (PR-48)
- [x] Missing `FX.EURUSD` → `MissingFxRateError`
- [x] `eurusd <= 0` → `InvalidFxRateError`
- [x] Unsupported currency (not EUR/USD) → `UnsupportedCurrencyError`

### 5.3 Audit fields (PR-48, PR-46)
- [x] `fx_asset_id_used` recorded for non-base positions
- [x] `fx_inverted` recorded correctly
- [x] `fx_rate_effective` equals the rate applied to native amounts

---

## 6) Pricer registry and pricer plugins

### 6.1 Pricer interface and registry (PR-49)
- [x] Base pricer interface exists (no inheritance tree required)
- [x] Registry maps instrument kinds/specs → pricer components
- [x] Missing pricer mapping fails fast with a typed error

### 6.2 CashPricer (PR-50)
- [x] Values cash as `quantity * 1.0` in native currency
- [x] Applies FX conversion if cash currency != base currency
- [x] Does not require market price points

### 6.3 EquityPricer (and tradable index proxies) (PR-51)
- [x] Reads `close` (or configured field) from MarketDataView
- [x] Records input points used in `inputs`
- [x] Missing price fails fast with `MissingPriceError`
- [x] Applies FX conversion if needed and records FX metadata

### 6.4 FuturePricer (PR-52)
- [x] Computes notional as `q * close * multiplier`
- [x] Multiplier comes from instrument spec (not hard-coded)
- [x] Limitations are explicit (no margining/roll)
- [x] Applies FX conversion and records FX metadata

---

## 7) ValuationEngine and portfolio aggregation

### 7.1 Engine exists and is pure (PR-53)
- [x] `ValuationEngine` iterates positions deterministically
- [x] Uses `PricerRegistry` to price each position
- [x] Produces `PortfolioValuation` with base NAV and breakdown
- [x] Aggregates warnings deterministically

### 7.2 Breakdown by currency (PR-53)
- [x] For each native currency, totals include:
  - [x] `notional_native` sum
  - [x] `notional_base` sum
- [x] Breakdown sums reconcile with positions and NAV

### 7.3 Lineage plumbing (PR-56)
- [ ] PortfolioValuation includes dataset snapshot id when available
- [ ] Valuation outputs include enough metadata to reproduce the run

---

## 8) Data quality propagation

### 8.1 Quality meta → warnings mapping (PR-54)
- [x] If `MarketDataView.get_point` provides meta flags, they are propagated to `warnings`
- [x] Pricing does not change values based on quality flags
- [x] Mapping is documented and stable

---

## 9) Testing completeness

### 9.1 Unit tests (PR-45 … PR-53)
- [ ] Errors carry correct context
- [ ] FX conversion rules correct (direct/inverse/same-currency)
- [ ] Each pricer has edge-case tests (missing price, invalid multiplier, etc.)
- [ ] Schemas reject NaN/Inf

### 9.2 Property-based tests (PR-50 … PR-52)
- [ ] Scaling quantity scales notional (native and base) linearly
- [ ] Base==native ⇒ notional_base == notional_native
- [ ] EURUSD inversion consistency (USD→EUR equals 1/EURUSD)

### 9.3 Golden snapshot tests (PR-55)
- [ ] At least one EUR/USD portfolio fixture exists
- [ ] Snapshot includes inputs used + FX inversion flags
- [ ] Snapshot diffs are informative

### 9.4 Integration tests (PR-53, PR-56)
- [ ] Engine + adapter over canonical dataset produces expected valuation
- [ ] No network calls or external dependencies in tests

---

## 10) Examples and reproducibility artifacts

### 10.1 Example inputs/outputs (PR-55)
- [ ] `docs/pricing/examples/portfolio_multi_ccy.json`
- [ ] `docs/pricing/examples/market_data_minimal_multi_ccy.json`
- [ ] `docs/pricing/examples/expected_portfolio_valuation_multi_ccy.json`

### 10.2 Deterministic formatting (PR-55)
- [ ] Rounding/float formatting policy is documented (if any)
- [ ] Snapshots do not depend on non-deterministic ordering or timestamps

---

## 11) Observability (non-functional)

### 11.1 Structured logging (PR-57)
- [ ] ValuationEngine logs start/end with portfolio_id, as_of, base_currency
- [ ] Logs summarize counts (positions priced, warnings count)
- [ ] Logs do not leak into outputs (no timestamps in valuation objects)

---

## 12) Final module sign-off checklist (PR-58)

- [ ] All docs in `docs/pricing/` are accurate and internally consistent
- [ ] ADR decisions are reflected in code and tests
- [ ] CI passes (lint/typecheck/tests) with pricing module included
- [ ] No dependency-layer violations (pricing remains pure)
- [ ] Known limitations are clearly stated (futures margining/roll, no derivatives, etc.)
- [ ] A new reader can understand and run the pricing demo in <30 minutes (conceptually)
