# QuantLab — TASKBOARD-05 (Risk + Stress Modules MVP)

This checklist is intended as a **living verification gate** for the `risk/` and `stress/` modules.
It tracks what must exist for a first defensible MVP and what has been completed.

Legend:
- [x] already produced as project artifacts (docs pack) and ready to be committed
- [ ] not yet implemented / not yet merged into the repository

**Scope:** `src/risk/` + `src/stress/` + unit/property/golden/integration tests + module docs.
**Non-scope:** data fetching and caching (`data/`), instrument definitions (`instruments/`), allocation (`optimization/`), decision layer.

**Stress approach (MVP):** price-based revaluation for linear instruments only (ADR-0401).

---

## 0) Documentation and ADRs are present and wired

### 0.1 Risk ADRs (must be in `docs/adr/`)
- [x] `docs/adr/0301-risk-scope-mvp.md`
- [x] `docs/adr/0302-risk-inputs-and-as-of-semantics.md`
- [x] `docs/adr/0303-risk-returns-conventions-mvp.md`
- [x] `docs/adr/0304-risk-var-es-historical-mvp.md`
- [x] `docs/adr/0305-risk-covariance-estimation-mvp.md`
- [x] `docs/adr/0306-risk-exposure-mapping-seam-mvp.md`
- [x] `docs/adr/0307-risk-variance-attribution-mvp.md`
- [x] `docs/adr/0308-risk-report-schema-warnings-determinism.md`
- [x] `docs/adr/0309-risk-testing-strategy.md`

### 0.2 Stress ADRs (must be in `docs/adr/`)
- [x] `docs/adr/0401-stress-scope-mvp-price-based.md`
- [x] `docs/adr/0402-stress-scenario-contract-and-semantics.md`
- [x] `docs/adr/0403-stress-shock-application-policy.md`
- [x] `docs/adr/0404-stress-report-schema-breakdown.md`
- [x] `docs/adr/0405-stress-max-loss-tail-metrics-mvp.md`
- [x] `docs/adr/0406-stress-testing-strategy.md`
- [x] `docs/adr/0407-stress-future-seam-pricing-based.md`

### 0.3 Module docs and examples exist
- [x] `docs/modules/risk.md`
- [x] `docs/modules/stress.md`
- [x] `docs/risk/INDEX.md`
- [x] `docs/risk/QUICKSTART.md`
- [x] `docs/risk/examples/risk_request_example.json`
- [x] `docs/risk/examples/risk_report_example.json`
- [x] `docs/stress/INDEX.md`
- [x] `docs/stress/QUICKSTART.md`
- [x] `docs/stress/examples/stress_scenarios_example.json`
- [x] `docs/stress/examples/stress_report_example.json`

---

## 1) Risk module: package boundaries and public API

### 1.1 Package skeleton exists
- [ ] `src/risk/__init__.py` exports the intended stable API (`RiskRequest`, `RiskReport`, `RiskEngine`, key specs)
- [x] `src/risk/errors.py` defines typed exceptions (no silent failures)
- [x] `src/risk/__init__.py` exports the intended stable API (`RiskRequest`, `RiskReport`, `RiskEngine`, key specs)
- [x] `src/risk/schemas/` contains typed request/report models (Pydantic v2)
- [x] `src/risk/metrics/` contains pure functions (no I/O)
- [x] `src/risk/engine.py` orchestrates the pipeline with no side effects

### 1.2 Layering constraints are enforced
- [ ] No imports from `src/data/providers/` or `src/data/storage/` inside `src/risk/`
- [ ] `risk/` only consumes **already aligned** time series bundles
- [ ] Any optional mapping provider is a protocol/interface, not a concrete I/O implementation

---

## 2) Risk contracts: inputs, policies, lineage

### 2.1 `RiskRequest` covers required fields (ADR-0302/0303)
- [x] as_of date + explicit window definition (days or start/end)
- [x] annualization factor is explicit and recorded
- [x] return definition is explicit (simple default; log optional)
- [x] missing data policy is explicit
- [x] confidence levels for VaR/ES are explicit
- [x] input mode is explicit (`PORTFOLIO_RETURNS` vs `STATIC_WEIGHTS_X_ASSET_RETURNS`)
- [x] covariance estimator spec recorded (sample default)

### 2.2 Input validation failures are typed and actionable
- [ ] missing assets in time series bundle triggers `RiskInputError`
- [ ] look-ahead usage triggers `RiskInputError`
- [ ] insufficient sample size for VaR/ES triggers error or warning (policy-defined)
- [x] NaN/Inf inputs are rejected (or sanitized with explicit warning, policy-defined)

### 2.3 Lineage is present and stable (ADR-0308)
- [ ] portfolio snapshot id/hash is included
- [ ] market data bundle id/hash is included
- [ ] request canonical hash is included (optional but recommended)
- [ ] all hashes are deterministic (canonical JSON encoding)

---

## 3) Risk core computations (time-series)

### 3.1 Returns builder (ADR-0303)
- [x] supports simple returns from prices
- [x] supports log returns (opt-in)
- [x] handles missing values per policy (error/drop/ffill/partial)
- [x] emits structured warnings when policy may bias results

### 3.2 Volatility and covariance/correlation (ADR-0305)
- [x] sample covariance estimator implemented and tested
- [x] portfolio volatility annualized correctly (unit-tested)
- [x] covariance symmetry enforced (numeric tolerance)
- [x] correlation computed consistently and safely (division by zero handled)

### 3.3 Drawdowns
- [x] drawdown series definition is correct and documented
- [x] max drawdown computed correctly
- [ ] time-to-recovery computed if feasible (else explicitly omitted)

### 3.4 Tracking error (if benchmark supplied)
- [x] benchmark alignment policy is explicit
- [x] tracking error is annualized correctly
- [ ] report surfaces benchmark id/lineage

---

## 4) Risk tail risk (VaR/ES)

### 4.1 Historical VaR/ES (ADR-0304)
- [x] loss convention is explicit and consistent
- [x] VaR quantile definition is stable (ties, interpolation policy)
- [x] ES computed as average beyond VaR with correct inequality convention
- [x] small sample guardrails (warnings or errors)

---

## 5) Risk exposures and attribution

### 5.1 Asset exposures
- [x] weight computation defined (from snapshot valuation or notionals)
- [x] exposure sums to 1 (when normalizable) or report states alternative convention
- [x] exposure is keyed by `MarketDataId` and stable ordering is enforced

### 5.2 Currency exposures
- [x] decomposition by instrument currency exists
- [ ] if FX aggregation is unsupported, report explicitly states “decomposition only”

### 5.3 Optional mapped exposures (sector/region) via seam (ADR-0306)
- [ ] `ExposureMappingProvider` protocol exists
- [ ] when provider absent, report emits warning and omits mapped breakdowns
- [ ] when provider present, results are deterministic and tested

### 5.4 Variance attribution (ADR-0307)
- [ ] compute marginal/component contributions for a static weight vector
- [ ] attribution convention is recorded in report
- [ ] sanity tests: contributions sum to portfolio variance (within tolerance)

---

## 6) Risk report output quality (ADR-0308)

### 6.1 `RiskReport` is typed and JSON-serializable
- [x] Pydantic v2 models with strict validation
- [x] canonical JSON serialization is stable
- [x] stable field ordering and stable sorting of lists (by id)

### 6.2 Warnings are structured and stable
- [x] warnings include code, short message, minimal context dict
- [ ] no long free-form logs in the report
- [ ] warnings cover key biases: static weights, raw prices, missing data

---

## 7) Stress module: package boundaries and public API

### 7.1 Package skeleton exists
- [ ] `src/stress/__init__.py` exports stable API (`Scenario`, `ScenarioSet`, `StressReport`, `StressEngine`)
- [ ] `src/stress/errors.py` defines typed exceptions
- [ ] `src/stress/schemas/` contains typed request/report models (Pydantic v2)
- [ ] `src/stress/scenarios.py` defines scenario models (pure)
- [ ] `src/stress/engine.py` executes stress (pure)

### 7.2 Layering constraints are enforced
- [ ] No imports from provider/storage code inside `src/stress/`
- [ ] historical scenarios are executed only after materialization into explicit shock vectors

---

## 8) Stress scenario modeling (ADR-0402/0403)

### 8.1 Scenario types exist and validate
- [ ] ParametricShock: explicit shock vector keyed by `MarketDataId`
- [ ] CustomShockVector: explicit convention and units
- [ ] HistoricalShock: must include explicit vector for execution (materialized)

### 8.2 Shock application semantics are explicit (ADR-0403)
- [ ] default: multiplicative return shocks: P' = P*(1+shock)
- [ ] reject invalid shocked prices where appropriate
- [ ] missing shock policy is explicit (zero-with-warning vs error)

### 8.3 Scenario identity and determinism
- [ ] stable `scenario_id` is required
- [ ] scenario set has a canonical hash (order-independent or order-canonicalized)
- [ ] deterministic ordering of scenario results

---

## 9) Stress engine (price-based) correctness (ADR-0401)

### 9.1 Linear instrument revaluation
- [ ] equity/index: qty*(P'-P)
- [ ] futures: qty*multiplier*(P'-P)
- [ ] cash: P&L = 0 in own currency (no FX unless explicit)
- [ ] instrument-specific multiplier conventions are tested

### 9.2 Aggregation and breakdown integrity
- [ ] portfolio P&L equals sum of position P&L (tolerance)
- [ ] asset breakdown sums to portfolio P&L (tolerance)
- [ ] currency breakdown sums to portfolio P&L when meaningful
- [ ] drivers/top contributors extracted deterministically

---

## 10) Stress report output quality (ADR-0404/0405)

### 10.1 `StressReport` schema is complete and stable
- [ ] scenario table includes P&L, ΔNAV, return
- [ ] breakdown by position and asset is present
- [ ] worst scenario + max loss reported
- [ ] report includes explicit disclaimer: “no probabilities, not VaR”

### 10.2 Warnings and errors
- [ ] missing market state price triggers typed error (or explicit policy)
- [ ] missing shocks handled per policy with warnings

---

## 11) Testing (risk + stress) is serious and reproducible

### 11.1 Unit tests
- [x] metric-level tests for vol/cov/drawdown/TE
- [x] VaR/ES tests with known distributions (synthetic fixtures)
- [ ] stress revaluation tests per instrument type

### 11.2 Property-based tests (Hypothesis)
- [ ] covariance symmetry / PSD invariants (within tolerance)
- [ ] drawdown invariants
- [ ] VaR <= ES (loss convention)
- [ ] stress aggregation invariants and scenario-order invariance

### 11.3 Golden tests
- [ ] canonical `RiskReport` JSON fixtures (small and deterministic)
- [ ] canonical `StressReport` JSON fixtures (small and deterministic)

### 11.4 Integration tests
- [ ] end-to-end risk pipeline on committed sample dataset
- [ ] end-to-end stress pipeline with a small scenario set

---

## 12) Packaging / API exports / docs consistency

### 12.1 Public exports
- [ ] `src/risk/__init__.py` and `src/stress/__init__.py` expose stable names
- [ ] docs quickstarts import paths match code
- [ ] versioning notes are added where appropriate (schema version fields)

### 12.2 Explicit limitations remain visible
- [ ] raw prices assumption documented
- [ ] static weights assumption documented (if used)
- [ ] price-based stress limitation documented (linear payoffs only)
- [ ] multi-currency limitations documented

---

## 13) Completion criteria (“risk+stress MVP done”)
- [ ] All above checkboxes are complete
- [ ] `pytest -q` passes (unit + property + golden + integration)
- [ ] No imports from provider/storage layers inside `risk/` and `stress/`
- [ ] Canonical JSON fixtures are stable across runs
