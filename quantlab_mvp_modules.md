# QuantLab — MVP Overview and Module Map

## What QuantLab is
QuantLab is a modular quantitative analysis and risk framework.
It is designed for reproducible portfolio analytics, stress testing, and constraint-aware allocation.
It separates concerns across strict layers.
It is “library-first”, with a thin CLI for demos.

## What a first complete MVP must enable
- Ingest and cache **raw** historical market data for a small universe.
- Align time series to a chosen market calendar.
- Produce lineage and quality diagnostics for every dataset request.
- Represent instruments, positions, and portfolios as **pure domain objects**.
- Mark-to-market portfolios and compute P&L and returns.
- Compute core risk metrics (volatility, drawdown, VaR/ES) and basic exposures.
- Run deterministic stress scenarios and report portfolio impacts.
- Solve at least one realistic constrained optimization problem (e.g., mean-variance with bounds).
- Execute a simple walk-forward simulation that evaluates decisions out-of-sample.
- Output an auditable report (JSON + human-readable summary).

Non-goals for the MVP:
- No “buy/sell signals” as the primary output.
- No corporate-action corrections by default.
- No high-frequency data and no intraday microstructure modeling.
- No complex derivatives pricing unless explicitly required.

---

# Modules required for a complete MVP

## 1) `data/` — Market data access, alignment, cache, lineage
**Role.** Provide a single, stable entrypoint for time series retrieval.

**Core responsibilities**
- Provider adapters (fetch boundary) and symbol mapping.
- Calendar-driven alignment to a target trading session index.
- Raw-only price policy and guardrails (missing data, duplicates, suspect corporate actions).
- Deterministic request hashing and reproducible caching.
- Persistent storage (e.g., Parquet + manifest) and cache replay by request hash.
- Quality and lineage models emitted with every bundle.

**Outputs**
- `TimeSeriesBundle`: aligned panel (date index, multi-asset fields) + `QualityReport` + `LineageMeta`.

**Does not**
- “Fix” data silently.
- Embed portfolio, risk, or strategy logic.

## 2) `instruments/` — Domain model: instruments, positions, portfolio
**Role.** Define the economic objects used everywhere else.

**Core responsibilities**
- Typed definitions for `Instrument`, `Position`, and `Portfolio`.
- Identifier model (instrument id, asset id, currency).
- Portfolio accounting state (quantities, cost basis if needed, cash).
- Serialization (JSON) for audit and reporting.

**Outputs**
- Pure domain objects. No I/O.
- Deterministic, serializable portfolio snapshots.

**Does not**
- Fetch market data.
- Price instruments by itself.

## 3) `pricing/` — Pricing and valuation models
**Role.** Convert market data + instrument specs into valuations.

**Core responsibilities**
- Pricer interfaces (pure functions where possible).
- Mark-to-market valuation for “linear” instruments (cash, equities, simple bonds via price).
- Optional curve construction hooks (only if needed for the MVP).
- Valuation metadata (as-of timestamp, inputs used).

**Outputs**
- Per-position valuation.
- Portfolio NAV and valuation breakdown.

**Does not**
- Own risk aggregation.
- Hide assumptions (every pricer must surface what it assumes).

## 4) `risk/` — Risk metrics and factor/exposure views
**Role.** Turn valuations and returns into risk measures.

**Core responsibilities**
- Time-series risk: volatility, covariance, drawdowns, tracking error.
- Tail risk: historical VaR/ES (MVP), with clear assumptions.
- Exposure decomposition: by asset, sector/region (if mapping exists), currency.
- Risk attribution and contribution (marginal/contribution to variance, MVP-level).

**Outputs**
- Typed `RiskReport` objects.
- Machine-readable metrics plus summary tables.

**Does not**
- Optimize allocations.
- Claim performance without risk context.

## 5) `stress/` — Scenario definition and stress engine
**Role.** Apply deterministic shocks and report impacts.

**Core responsibilities**
- Scenario model (historical shock, parametric shock, custom shock vectors).
- Stress engine that revalues positions under scenarios.
- Stress outputs with max loss, tail behavior, and scenario-by-scenario breakdown.

**Outputs**
- `StressReport`: P&L / NAV change per scenario, plus drivers.

**Does not**
- Fit statistical models in the background.
- Assume “normality” unless explicitly declared.

## 6) `optimization/` — Constrained portfolio construction
**Role.** Solve allocation problems with realistic constraints.

**Core responsibilities**
- Objective functions (e.g., mean-variance, min-variance, risk-parity as extension).
- Constraint set: long-only, leverage cap, turnover cap, sector/currency bounds, risk budgets.
- Solver wrappers (CVX/OSQP/SciPy) behind a stable interface.
- Feasibility diagnostics when constraints conflict.

**Outputs**
- `OptimizationResult`: target weights, constraint slack, solver status, logs.

**Does not**
- Decide when to rebalance.
- Hide infeasibility (must be explicit and reproducible).

## 7) `decision/` — Policy layer and explainability
**Role.** Convert analytics into **risk-aware targets**, not trade signals.

**Core responsibilities**
- Decision policies that map inputs to target exposures or risk budgets.
- Confidence and rationale objects (inputs used, constraints, dominant risks).
- Guardrails at decision time (max drawdown stop, volatility targeting, etc., if chosen).

**Outputs**
- `DecisionOutput`: target weights/exposures + rationale + warnings.

**Does not**
- Execute trades.
- Embed a monolithic “strategy” into the core (strategies remain plugins).

## 8) `simulation/` (new) — Walk-forward validation and execution model
**Role.** Provide defensible out-of-sample evaluation.

**Core responsibilities**
- Walk-forward splitting (train window, test window, rebalance schedule).
- Transaction cost model (spread/fees) and turnover tracking.
- Liquidity constraints (MVP: simple volume-based cap or notional cap).
- Portfolio evolution: apply decisions, rebalance, compute realized P&L.
- Audit trails: configs, seeds, data request hashes per run.

**Outputs**
- `SimulationResult`: equity curve, turnover, costs, risk over time, run metadata.

**Does not**
- Overfit by default.
- Use future information (explicit anti look-ahead checks are required).

## 9) `report/` — Serialization and human-facing outputs
**Role.** Produce auditable artifacts.

**Core responsibilities**
- JSON as the “source of truth” output format.
- Optional Markdown/HTML summaries for quick review.
- Report templates and golden snapshot tests for stability.

**Outputs**
- Versioned reports that embed config + data lineage + code version (when available).

**Does not**
- Contain business logic.
- Depend on external services to render.

## 10) `utils/` — Cross-cutting concerns
**Role.** Shared infrastructure with strict boundaries.

**Core responsibilities**
- Typed exceptions and error taxonomy.
- Structured logging with context (request hash, run id, asset id).
- Timezone and calendar helpers.
- Configuration loading (YAML/JSON) and validation (typed).

**Outputs**
- Small reusable utilities.
- No circular dependencies.

---

# Supporting project infrastructure (required for the MVP)

## `tests/`
- Unit tests per module (payoffs/pricers/risk/stress/constraints).
- Property-based tests for invariants (hash stability, alignment idempotence).
- Integration tests end-to-end (data → pricing → risk → stress → optimization → decision → simulation).
- Golden/snapshot tests for reports.

## `docs/`
- Architecture overview and module READMEs.
- ADRs for key trade-offs (raw-only data, chosen solver stack, simulation assumptions).
- Testing plan and reproducibility policy.

## `configs/`
- Small, versioned YAML configs (universe, mappings, policies, simulation schedule).
- Defaults that are conservative and explicit.

## `tools/` (optional but useful)
- Minimal CLI to run: data pull, risk report, stress report, walk-forward run.
- CLI must remain a thin wrapper around the library API.

## `examples/`
- Minimal scripts showing the “happy path”.
- One end-to-end demo that produces a full JSON report.

---

# MVP “happy path” pipeline (one-liner view)
`data` → `instruments` → `pricing` → `risk` + `stress` → `optimization` → `decision` → `simulation` → `report`
