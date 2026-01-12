# QuantLab — TASKBOARD-05 (Risk + Stress Modules MVP)

This checklist is intended as a **living verification gate** for the `risk/` and `stress/` modules.
It tracks what must exist for a first defensible MVP and what has been completed.

Legend:
- [x] already produced as project artifacts (docs pack) and ready to be committed
- [ ] not yet implemented / not yet merged into the repository

**Scope:** `src/quantlab/risk/` + `src/quantlab/stress/` + unit/property/golden/integration tests + module docs.
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
- [x] `src/quantlab/risk/__init__.py` exports the intended stable API (`RiskRequest`, `RiskReport`, `RiskEngine`, key specs)
- [x] `src/quantlab/risk/errors.py` defines typed exceptions (no silent failures)
- [x] `src/quantlab/risk/schemas/` contains typed request/report models (Pydantic v2)
- [x] `src/quantlab/risk/metrics/` contains pure functions (no I/O)
- [x] `src/quantlab/risk/engine.py` orchestrates the pipeline with no side effects

### 1.2 Layering constraints are enforced
- [x] No imports from `src/data/providers/` or `src/data/storage/` inside `src/quantlab/risk/`
- [x] `risk/` only consumes **already aligned** time series bundles
- [x] Any optional mapping provider is a protocol/interface, not a concrete I/O implementation

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
- [x] missing assets in time series bundle triggers `RiskInputError`
- [x] look-ahead usage triggers `RiskInputError`
- [x] insufficient sample size for VaR/ES triggers error or warning (policy-defined)
- [x] NaN/Inf inputs are rejected (or sanitized with explicit warning, policy-defined)

### 2.3 Lineage is present and stable (ADR-0308)
- [x] portfolio snapshot id/hash is included (via `RiskRequest.lineage`)
- [x] market data bundle id/hash is included
- [x] request canonical hash is included (optional but recommended)
- [x] all hashes are deterministic (canonical JSON encoding)
  - [x] wire portfolio snapshot id/hash source and hashing convention.

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
- [x] report includes covariance/correlation diagnostics (sample size, missing count, symmetry error)
  - [x] add diagnostics fields to `RiskReport` and wire through engine (diagnostics exist in metrics).

### 3.3 Drawdowns
- [x] drawdown series definition is correct and documented
- [x] max drawdown computed correctly
- [x] time-to-recovery computed if feasible (else explicitly omitted)

### 3.4 Tracking error (if benchmark supplied)
- [x] benchmark alignment policy is explicit
- [x] tracking error is annualized correctly
- [ ] report surfaces benchmark id/lineage
  - [ ] add benchmark id/lineage fields and propagation into RiskReport.

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
- [x] if FX aggregation is unsupported, report explicitly states “decomposition only”

### 5.3 Optional mapped exposures (sector/region) via seam (ADR-0306)
- [x] `ExposureMappingProvider` protocol exists
- [x] when provider absent, report emits warning and omits mapped breakdowns
- [x] when provider present, results are deterministic and tested

### 5.4 Variance attribution (ADR-0307)
- [x] compute marginal/component contributions for a static weight vector
- [x] attribution convention is recorded in report
- [x] sanity tests: contributions sum to portfolio variance (within tolerance)

---

## 6) Risk report output quality (ADR-0308)

### 6.1 `RiskReport` is typed and JSON-serializable
- [x] Pydantic v2 models with strict validation
- [x] canonical JSON serialization is stable
- [x] stable field ordering and stable sorting of lists (by id)

### 6.2 Warnings are structured and stable
- [x] warnings include code, short message, minimal context dict
- [x] no long free-form logs in the report
- [x] warnings cover key biases: static weights, raw prices, missing data

---

## 7) Stress module: package boundaries and public API

### 7.1 Package skeleton exists
- [x] `src/quantlab/stress/__init__.py` exports stable API (`Scenario`, `ScenarioSet`, `StressReport`, `StressEngine`)
- [x] `src/quantlab/stress/errors.py` defines typed exceptions
- [x] `src/quantlab/stress/schemas/` contains typed request/report models (Pydantic v2)
- [x] `src/quantlab/stress/scenarios.py` defines scenario models (pure)
- [x] `src/quantlab/stress/engine.py` executes stress (pure)
- [x] `src/quantlab/stress/` package scaffold exists (`__init__`, `errors`, `engine`, `scenarios`, `schemas`)

### 7.2 Layering constraints are enforced
- [x] No imports from provider/storage code inside `src/quantlab/stress/`
- [x] historical scenarios are executed only after materialization into explicit shock vectors

---

## 8) Stress scenario modeling (ADR-0402/0403)

### 8.1 Scenario types exist and validate
- [x] ParametricShock: explicit shock vector keyed by `MarketDataId`
- [x] CustomShockVector: explicit convention and units
- [x] HistoricalShock: must include explicit vector for execution (materialized)

### 8.2 Shock application semantics are explicit (ADR-0403)
- [x] default: multiplicative return shocks: P' = P*(1+shock)
- [x] reject invalid shocked prices where appropriate
- [x] missing shock policy is explicit (zero-with-warning vs error)

### 8.3 Scenario identity and determinism
- [x] stable `scenario_id` is required
- [x] scenario set has a canonical hash (order-independent or order-canonicalized)
- [x] deterministic ordering of scenario results

---

## 9) Stress engine (price-based) correctness (ADR-0401)

### 9.1 Linear instrument revaluation
- [x] equity/index: qty*(P'-P)
- [x] futures: qty*multiplier*(P'-P)
- [x] cash: P&L = 0 in own currency (no FX unless explicit)
- [x] instrument-specific multiplier conventions are tested

### 9.2 Aggregation and breakdown integrity
- [x] portfolio P&L equals sum of position P&L (tolerance)
- [x] asset breakdown sums to portfolio P&L (tolerance)
- [x] currency breakdown sums to portfolio P&L when meaningful
- [x] drivers/top contributors extracted deterministically

---

## 10) Stress report output quality (ADR-0404/0405)

### 10.1 `StressReport` schema is complete and stable
- [x] scenario table includes P&L, ΔNAV, return
- [x] breakdown by position and asset is present
- [x] worst scenario + max loss reported
- [x] report includes explicit disclaimer: “no probabilities, not VaR”

### 10.2 Warnings and errors
- [x] missing market state price triggers typed error (or explicit policy)
- [x] missing shocks handled per policy with warnings

---

## 11) Testing (risk + stress) is serious and reproducible

### 11.1 Unit tests
- [x] metric-level tests for vol/cov/drawdown/TE
- [x] VaR/ES tests with known distributions (synthetic fixtures)
- [x] stress revaluation tests per instrument type

### 11.2 Property-based tests (Hypothesis)
- [x] covariance symmetry / PSD invariants (within tolerance)
- [x] drawdown invariants
- [x] VaR <= ES (loss convention)
- [x] stress aggregation invariants and scenario-order invariance

### 11.3 Golden tests
- [x] canonical `RiskReport` JSON fixtures (small and deterministic)
- [x] canonical `StressReport` JSON fixtures (small and deterministic)

### 11.4 Integration tests
- [x] end-to-end risk pipeline on committed sample dataset
- [x] end-to-end stress pipeline with a small scenario set

---

## 12) Packaging / API exports / docs consistency

### 12.1 Public exports
- [x] `src/quantlab/risk/__init__.py` and `src/quantlab/stress/__init__.py` expose stable names
- [x] docs quickstarts import paths match code
- [x] versioning notes are added where appropriate (schema version fields)

### 12.2 Explicit limitations remain visible
- [x] raw prices assumption documented
- [x] static weights assumption documented (if used)
- [x] price-based stress limitation documented (linear payoffs only)
- [x] multi-currency limitations documented

---

## 13) Completion criteria (“risk+stress MVP done”)
- [ ] All above checkboxes are complete
- [ ] `pytest -q` passes (unit + property + golden + integration)
- [x] No imports from provider/storage layers inside `risk/` and `stress/`
- [ ] Canonical JSON fixtures are stable across runs

---

## 14) Follow-ups (deferred)
- [x] Populate `RiskReport` fields from computed metrics/exposures
- [x] Emit structured warnings for missing data policy usage and raw-price inputs
- [ ] Expand `RiskMetrics` with covariance/correlation summaries when implemented
- [ ] Add FX aggregation policy/base-currency handling for stress NAV/returns
- [ ] Wire optional input lineage ids (portfolio/market_state/scenario_set) into `StressReport` (hashes are wired)
