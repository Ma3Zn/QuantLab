# QuantLab Backlog — Risk + Stress Modules (MVP)

**Scope:** Implement `src/risk/` and `src/stress/` as pure computation layers.
**Stress approach:** MVP is **price-based** revaluation for linear instruments (ADR-0401).
**Start PR numbering:** PR-34 (continues the sequence after Instruments).

This backlog is intentionally split into **many small, low-ambiguity PRs**.
Each PR should be reviewable in isolation and should not require large refactors.

---

## Global acceptance criteria (end state)
By the end of this backlog:
- `src/risk/` exposes a stable API to compute:
  - volatility, covariance/correlation, drawdowns, tracking error,
  - historical VaR/ES,
  - exposures (asset, currency) and MVP variance attribution.
- `src/stress/` exposes a stable API to:
  - define scenarios (parametric, custom, historical-materialized),
  - execute price-based stress on linear instruments,
  - produce explainable `StressReport` with max loss across scenarios.
- Both modules produce typed, JSON-serializable reports with explicit conventions and warnings.
- Unit + property (Hypothesis) + golden + integration tests pass.
- No provider/storage I/O occurs inside these modules.

---

## PR-59 — Add risk+stress documentation pack (ADRs + module docs + examples)

### Goal
Commit the prepared documentation for the two modules: ADRs, module docs, index/quickstart, and example JSON files.

### Files to add
- `docs/adr/0301-...` through `0309-...`
- `docs/adr/0401-...` through `0407-...`
- `docs/modules/risk.md`, `docs/modules/stress.md`
- `docs/risk/*`, `docs/risk/examples/*`
- `docs/stress/*`, `docs/stress/examples/*`

### Acceptance criteria
- All docs render correctly in markdown.
- Docs are consistent with the MVP module map.
- Example JSON is valid and coherent.

---

## PR-60 — Create `risk/` package skeleton + error taxonomy

### Goal
Add the minimal package structure and typed exceptions for the risk layer.

### Tasks
1. Create `src/risk/` structure:
   - `__init__.py` (exports only; keep stable)
   - `errors.py` (typed exceptions)
   - `engine.py` (placeholder orchestration, no heavy logic yet)
2. Define typed errors:
   - `RiskError` (base)
   - `RiskInputError`, `RiskComputationError`, `RiskSchemaError`

### Acceptance criteria
- Package imports cleanly.
- No circular imports with `instruments/` or `data/`.

### Tests
- Minimal import tests.

---

## PR-61 — Add typed schemas: `RiskRequest` + `RiskReport` (Pydantic v2)

### Goal
Implement strict, JSON-serializable contracts for requests and outputs.

### References
- ADR-0302, ADR-0308

### Tasks
1. Create `src/risk/schemas/request.py`:
   - request fields and validation rules
2. Create `src/risk/schemas/report.py`:
   - `RiskReport` schema with version field, metadata, warnings
3. Add canonical JSON serialization helper (if needed)

### Acceptance criteria
- `RiskRequest` validates and rejects invalid inputs.
- `RiskReport` can be dumped to canonical JSON.

### Tests
- Unit tests for schema validation + JSON dumps.

---

## PR-62 — Implement returns builder (from aligned prices)

### Goal
Compute return series from aligned price series using explicit conventions.

### References
- ADR-0303

### Tasks
1. Create `src/risk/metrics/returns.py`:
   - simple and log returns
   - missing data policy hooks
2. Add unit tests:
   - constant prices -> zero returns
   - simple vs log correctness
   - NaN/Inf rejection

### Acceptance criteria
- Returns are correct and deterministic.
- Policies are enforced and warnings surfaced.

---

## PR-63 — Implement volatility and sample covariance/correlation

### Goal
Add core time-series risk metrics with correct annualization and diagnostics.

### References
- ADR-0305

### Tasks
1. Create `src/risk/metrics/covariance.py`:
   - sample covariance + correlation
2. Create `src/risk/metrics/volatility.py`
3. Tests:
   - symmetry, scaling, annualization correctness

### Acceptance criteria
- Metrics match known reference computations.
- Covariance is symmetric within tolerance.

---

## PR-64 — Implement drawdown metrics

### Goal
Add drawdown computation with correct definitions and edge-case handling.

### Tasks
1. Create `src/risk/metrics/drawdown.py`:
   - drawdown series
   - max drawdown
2. Tests:
   - monotone increasing wealth -> zero drawdown
   - known sequence -> known max drawdown

### Acceptance criteria
- Drawdown definitions are correct and documented.

---

## PR-65 — Implement tracking error (benchmark optional)

### Goal
Compute annualized tracking error when a benchmark return series is provided.

### Tasks
1. Create `src/risk/metrics/tracking_error.py`
2. Define benchmark alignment expectations in code-level docs
3. Tests for alignment + annualization

### Acceptance criteria
- Tracking error is correct and robust to missing values per policy.

---

## PR-66 — Implement historical VaR and ES

### Goal
Add historical simulation VaR/ES for one-day horizon with explicit loss convention.

### References
- ADR-0304

### Tasks
1. Create `src/risk/metrics/var_es.py`
2. Define quantile interpolation policy (explicit)
3. Tests:
   - VaR/ES on small synthetic samples
   - VaR <= ES in loss convention

### Acceptance criteria
- VaR/ES are correct and reproducible.
- Small sample guardrails exist (warnings/errors).

---

## PR-67 — Implement exposure views: asset + currency

### Goal
Compute exposure decompositions required by the MVP.

### References
- ADR-0306

### Tasks
1. Create `src/risk/exposures/asset.py`
2. Create `src/risk/exposures/currency.py`
3. Decide weight convention:
   - from valuation snapshot if available, otherwise notionals
4. Tests:
   - weights sum to 1 when normalizable
   - stable ordering

### Acceptance criteria
- Asset and currency exposures are present in the report and stable.

---

## PR-68 — Add mapping seam for sector/region exposures (optional output)

### Goal
Define a plug-in interface for mapped exposures without coupling to external I/O.

### Tasks
1. Define `ExposureMappingProvider` protocol in `src/risk/exposures/mapping.py`
2. Implement optional aggregation logic when provider is supplied
3. Add tests using a fake mapping provider

### Acceptance criteria
- When provider absent: warning + omitted mapped exposures.
- When provider present: deterministic mapped breakdown.

---

## PR-69 — Implement variance attribution (component contributions)

### Goal
Add MVP variance attribution based on weights and covariance.

### References
- ADR-0307

### Tasks
1. Create `src/risk/attribution/variance.py`
2. Tests:
   - contributions sum to portfolio variance within tolerance
   - behavior on diagonal covariance

### Acceptance criteria
- Attribution is correct, explicit, and recorded in the report.

---

## PR-70 — Implement RiskEngine orchestration and build `RiskReport`

### Goal
Wire schemas + metrics + exposures into a single orchestration path that emits `RiskReport`.

### References
- ADR-0308

### Tasks
1. Implement `src/risk/engine.py`:
   - validate inputs
   - compute returns (or consume portfolio returns)
   - compute metrics + exposures + attribution
   - assemble report with warnings + lineage
2. Add golden fixture for a small deterministic portfolio.

### Acceptance criteria
- `RiskEngine.run()` produces a stable `RiskReport`.
- Golden test passes.

---

## PR-71 — Create `stress/` package skeleton + error taxonomy

### Goal
Add the minimal package structure and typed exceptions for the stress layer.

### Tasks
1. Create `src/stress/` structure:
   - `__init__.py`, `errors.py`, `engine.py`, `scenarios.py`, `schemas/`
2. Define typed errors:
   - `StressError`, `StressInputError`, `StressScenarioError`, `StressComputationError`

### Acceptance criteria
- Package imports cleanly; no circular imports.

---

## PR-72 — Implement scenario models + validation + hashing

### Goal
Define scenario types and a deterministic scenario set representation.

### References
- ADR-0402

### Tasks
1. Implement scenario Pydantic models:
   - ParametricShock, CustomShockVector, HistoricalShock (materialized vector required for execution)
2. Implement canonical hashing for scenario sets
3. Tests:
   - validation rules
   - order-canonicalization behavior

### Acceptance criteria
- Scenario set hash is stable and deterministic.
- Invalid scenarios fail fast with typed errors.

---

## PR-73 — Implement shock application utilities (price-based)

### Goal
Implement shock-to-price mapping with explicit conventions.

### References
- ADR-0403

### Tasks
1. Create `src/stress/shocks.py`:
   - multiplicative return shocks
   - validation (no invalid prices)
2. Tests:
   - known mapping cases
   - invalid price rejection

### Acceptance criteria
- Shock application is correct and convention-driven.

---

## PR-74 — Implement linear revaluation for supported instrument types

### Goal
Compute position-level P&L under shocked prices for linear instruments.

### References
- ADR-0401

### Tasks
1. Create `src/stress/revaluation/linear.py`:
   - equity/index: qty*(P'-P)
   - futures: qty*multiplier*(P'-P)
   - cash: zero in own currency
2. Tests per instrument type using fixtures from `instruments/`

### Acceptance criteria
- Position P&L is correct and deterministic.

---

## PR-75 — Implement StressEngine orchestration and build `StressReport`

### Goal
Wire scenarios + shock application + revaluation into a single execution path.

### References
- ADR-0404, ADR-0405

### Tasks
1. Implement `src/stress/engine.py`:
   - validate market state completeness
   - apply scenario shocks
   - compute scenario results + breakdowns
   - compute summary (worst scenario, max loss)
2. Add `StressReport` schema in `src/stress/schemas/report.py`
3. Add golden fixture for a small deterministic scenario set

### Acceptance criteria
- `StressEngine.run()` produces stable canonical JSON.
- Breakdown sums match totals (tolerance).

---

## PR-76 — Add cross-module integration tests (risk + stress)

### Goal
Add end-to-end tests that validate the complete pipelines on committed sample fixtures.

### Tasks
1. Create `src/risk/tests/integration/test_risk_pipeline.py`
2. Create `src/stress/tests/integration/test_stress_pipeline.py`
3. Ensure fixtures are small and deterministic.

### Acceptance criteria
- Integration tests pass and do not hit network or external caches.

---

## PR-77 — Add property-based tests (Hypothesis) for invariants

### Goal
Add robust invariants that catch common numerical/aggregation bugs.

### References
- ADR-0309, ADR-0406

### Tasks
1. Risk property tests:
   - covariance symmetry/PSD tolerance
   - drawdown invariants
   - VaR <= ES (loss convention)
2. Stress property tests:
   - breakdown sums equal totals
   - scenario ordering invariance

### Acceptance criteria
- Property tests are stable (fixed seeds) and run within reasonable time.

---

## PR-78 — Docs consistency gate + public API verification

### Goal
Ensure docs match real import paths, and the public API is stable and intentional.

### Tasks
1. Verify `docs/*/QUICKSTART.md` import paths against `__init__.py` exports
2. Add a small “public API” unit test that imports intended symbols
3. Update module docs if paths changed during implementation

### Acceptance criteria
- Docs and code are consistent.
- No accidental exports.

---

## Optional follow-ups (explicitly non-MVP)
- Pricing-based revaluation seam (ADR-0407)
- EWMA/shrinkage covariance estimators (ADR-0305 extensions)
- FX policy module for coherent multi-currency aggregation
