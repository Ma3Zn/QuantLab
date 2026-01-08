# QuantLab Backlog — Pricing Module (MVP)

**Scope:** Implement `src/pricing/` as a pure valuation layer: pricers, FX conversion, and auditable valuation outputs.
**Multi-currency policy:** Policy B (EUR/USD portfolio support with base-currency NAV).
**Start PR numbering:** PR-34 (continues BACKLOG-03 ending at PR-33).

This backlog is intentionally split into **small, low-ambiguity PRs** to keep agentic coding sessions safe and reviewable.

---

## Global acceptance criteria (end state)
By the end of PR-58:
- `src/pricing/` exists as an importable package with clear public entry points.
- The module prices MVP linear instruments: cash, equities, tradable index proxies, linear futures.
- Portfolios containing **EUR and USD** are supported.
- `FX.EURUSD` (USD per EUR) is used as the canonical FX series; inversion is explicit and recorded.
- Outputs are typed (Pydantic v2), serializable, and include audit metadata (inputs used, FX applied, warnings).
- Missing required prices or FX rates cause typed, deterministic errors (no implicit fills in pricing).
- Unit tests + property-based tests + golden snapshot tests exist and run in CI.
- Module documentation and ADRs exist and match the code.

## Non-goals (MVP)
- Curves, discounting, accruals, and bond pricing economics.
- Options/KO/structured products.
- Margining/settlement/roll logic for futures (explicitly not modelled).
- Risk metrics and optimization.

## Dependencies / prerequisites
- `src/instruments/` is complete and provides currency + instrument specs (done).
- `src/data/` provides a canonical daily dataset representation, or at least a minimal adapter can be written.

---


## PR-34 — Add pricing docs skeleton (module page + index + quickstart)

### Goal
Create the documentation entry points for `pricing/` and wire the module into the project docs map.

### References
- `quantlab_mvp_modules.md` pricing section
- `docs/modules/pricing.md` (new)

### Tasks
1. Add `docs/modules/pricing.md` describing responsibilities / non-goals / contracts.
2. Add `docs/pricing/INDEX.md` and `docs/pricing/QUICKSTART.md`.
3. Add `docs/pricing/` directory structure, including `examples/` placeholder.
4. Ensure cross-links from module docs to ADRs and examples.

### Acceptance criteria
- Docs are consistent with QuantLab layering (no data fetching or risk inside pricing).
- The docs explicitly state the multi-currency policy and the canonical FX series.
- Docs are navigable (INDEX contains links to all files in this module).

---

## PR-35 — ADR-0201 pricing scope for MVP

### Goal
Add ADR-0201 and ensure it is referenced by pricing docs and backlog tasks.

### References
- `docs/adr/0201-*.md` (new)
- `docs/pricing/INDEX.md`

### Tasks
1. Add `docs/adr/0201-*.md` with context, options, decision, and consequences.
2. Ensure the ADR does not contradict any existing module docs.
3. Reference the ADR from `docs/pricing/INDEX.md` (and from any relevant spec doc).

### Acceptance criteria
- ADR follows the project ADR template and is concise but unambiguous.
- Decision and consequences are explicit, including limitations and future extensions.
- Links are correct and stable.

---

## PR-36 — ADR-0202 multi-currency base NAV policy (Policy B)

### Goal
Add ADR-0202 and ensure it is referenced by pricing docs and backlog tasks.

### References
- `docs/adr/0202-*.md` (new)
- `docs/pricing/INDEX.md`

### Tasks
1. Add `docs/adr/0202-*.md` with context, options, decision, and consequences.
2. Ensure the ADR does not contradict any existing module docs.
3. Reference the ADR from `docs/pricing/INDEX.md` (and from any relevant spec doc).

### Acceptance criteria
- ADR follows the project ADR template and is concise but unambiguous.
- Decision and consequences are explicit, including limitations and future extensions.
- Links are correct and stable.

---

## PR-37 — ADR-0203 FX quote convention: FX.EURUSD USD per EUR

### Goal
Add ADR-0203 and ensure it is referenced by pricing docs and backlog tasks.

### References
- `docs/adr/0203-*.md` (new)
- `docs/pricing/INDEX.md`

### Tasks
1. Add `docs/adr/0203-*.md` with context, options, decision, and consequences.
2. Ensure the ADR does not contradict any existing module docs.
3. Reference the ADR from `docs/pricing/INDEX.md` (and from any relevant spec doc).

### Acceptance criteria
- ADR follows the project ADR template and is concise but unambiguous.
- Decision and consequences are explicit, including limitations and future extensions.
- Links are correct and stable.

---

## PR-38 — ADR-0204 as-of semantics: date-only daily pricing

### Goal
Add ADR-0204 and ensure it is referenced by pricing docs and backlog tasks.

### References
- `docs/adr/0204-*.md` (new)
- `docs/pricing/INDEX.md`

### Tasks
1. Add `docs/adr/0204-*.md` with context, options, decision, and consequences.
2. Ensure the ADR does not contradict any existing module docs.
3. Reference the ADR from `docs/pricing/INDEX.md` (and from any relevant spec doc).

### Acceptance criteria
- ADR follows the project ADR template and is concise but unambiguous.
- Decision and consequences are explicit, including limitations and future extensions.
- Links are correct and stable.

---

## PR-39 — ADR-0205 missing data policy: fail fast

### Goal
Add ADR-0205 and ensure it is referenced by pricing docs and backlog tasks.

### References
- `docs/adr/0205-*.md` (new)
- `docs/pricing/INDEX.md`

### Tasks
1. Add `docs/adr/0205-*.md` with context, options, decision, and consequences.
2. Ensure the ADR does not contradict any existing module docs.
3. Reference the ADR from `docs/pricing/INDEX.md` (and from any relevant spec doc).

### Acceptance criteria
- ADR follows the project ADR template and is concise but unambiguous.
- Decision and consequences are explicit, including limitations and future extensions.
- Links are correct and stable.

---

## PR-40 — ADR-0206 pricer architecture: composition + registry

### Goal
Add ADR-0206 and ensure it is referenced by pricing docs and backlog tasks.

### References
- `docs/adr/0206-*.md` (new)
- `docs/pricing/INDEX.md`

### Tasks
1. Add `docs/adr/0206-*.md` with context, options, decision, and consequences.
2. Ensure the ADR does not contradict any existing module docs.
3. Reference the ADR from `docs/pricing/INDEX.md` (and from any relevant spec doc).

### Acceptance criteria
- ADR follows the project ADR template and is concise but unambiguous.
- Decision and consequences are explicit, including limitations and future extensions.
- Links are correct and stable.

---

## PR-41 — ADR-0207 valuation outputs: typed + canonical JSON

### Goal
Add ADR-0207 and ensure it is referenced by pricing docs and backlog tasks.

### References
- `docs/adr/0207-*.md` (new)
- `docs/pricing/INDEX.md`

### Tasks
1. Add `docs/adr/0207-*.md` with context, options, decision, and consequences.
2. Ensure the ADR does not contradict any existing module docs.
3. Reference the ADR from `docs/pricing/INDEX.md` (and from any relevant spec doc).

### Acceptance criteria
- ADR follows the project ADR template and is concise but unambiguous.
- Decision and consequences are explicit, including limitations and future extensions.
- Links are correct and stable.

---

## PR-42 — ADR-0208 futures simplification in MVP

### Goal
Add ADR-0208 and ensure it is referenced by pricing docs and backlog tasks.

### References
- `docs/adr/0208-*.md` (new)
- `docs/pricing/INDEX.md`

### Tasks
1. Add `docs/adr/0208-*.md` with context, options, decision, and consequences.
2. Ensure the ADR does not contradict any existing module docs.
3. Reference the ADR from `docs/pricing/INDEX.md` (and from any relevant spec doc).

### Acceptance criteria
- ADR follows the project ADR template and is concise but unambiguous.
- Decision and consequences are explicit, including limitations and future extensions.
- Links are correct and stable.

---

## PR-43 — ADR-0209 testing strategy: invariants + golden snapshots

### Goal
Add ADR-0209 and ensure it is referenced by pricing docs and backlog tasks.

### References
- `docs/adr/0209-*.md` (new)
- `docs/pricing/INDEX.md`

### Tasks
1. Add `docs/adr/0209-*.md` with context, options, decision, and consequences.
2. Ensure the ADR does not contradict any existing module docs.
3. Reference the ADR from `docs/pricing/INDEX.md` (and from any relevant spec doc).

### Acceptance criteria
- ADR follows the project ADR template and is concise but unambiguous.
- Decision and consequences are explicit, including limitations and future extensions.
- Links are correct and stable.

---

## PR-44 — Create `src/pricing/` package skeleton + README

### Goal
Introduce the pricing package without implementing pricers yet.

### References
- ADR-0201
- ADR-0206
- `src/pricing/README.md` (new)

### Tasks
1. Add `src/pricing/__init__.py` with minimal public exports placeholders.
2. Add `src/pricing/README.md` describing responsibilities and non-responsibilities.
3. Add subpackages placeholders: `pricers/`, `fx/`, `schemas/` (empty for now).
4. Add minimal import smoke test in `tests/` (package imports cleanly).

### Acceptance criteria
- `import quantlab.pricing` (or equivalent) works without side effects.
- No circular imports with `instruments/`.
- README matches the docs/module description.

---

## PR-45 — Define pricing error taxonomy + warning vocabulary

### Goal
Make failure modes explicit before adding valuation logic.

### References
- ADR-0205
- `docs/pricing/07_missing_data_and_quality_flags.md`

### Tasks
1. Add typed exceptions under `src/pricing/errors.py` (MissingPriceError, MissingFxRateError, UnsupportedCurrencyError, NonFiniteInputError, InvalidFxRateError).
2. Add warning code vocabulary (stable strings) under `src/pricing/warnings.py`.
3. Ensure exceptions carry actionable context (asset_id, field, as_of, instrument_id).

### Tests
- Unit tests: each error includes required context fields.
- Unit tests: warning codes are stable strings (no whitespace, uppercase with underscores).

### Acceptance criteria
- All known MVP failure modes have a specific typed exception.
- No generic `ValueError` in the pricing public API surface.
- Warnings are documented and referenced by docs.

---

## PR-46 — Add valuation output schemas (PositionValuation, PortfolioValuation)

### Goal
Define the canonical typed outputs for pricing and enable snapshot testing.

### References
- ADR-0207
- `docs/pricing/05_valuation_outputs_contract.md`

### Tasks
1. Add Pydantic v2 models under `src/pricing/schemas/valuation.py`.
2. Include `schema_version`, `as_of`, currency fields, FX metadata fields, and `inputs` list.
3. Ensure finite-number validation (reject NaN/Inf) for all numeric fields.

### Tests
- Unit tests: JSON serialization uses ISO dates and contains required fields.
- Unit tests: NaN/Inf rejected.
- Unit tests: schema_version present and non-empty.

### Acceptance criteria
- Schemas are sufficient to reproduce and audit the valuation inputs.
- Schemas are forward-compatible (explicit versioning).
- No dependency on pandas inside schemas.

---

## PR-47 — Define `MarketDataView` protocol + MarketPoint metadata

### Goal
Create the stable input contract from the data layer to pricing.

### References
- `docs/pricing/03_market_data_contract.md`
- ADR-0205

### Tasks
1. Add `src/pricing/market_data.py` defining `MarketDataView` (Protocol).
2. Define `MarketPoint` (value + optional metadata) and `MarketDataMeta` (quality flags, source dates, lineage ids).
3. Keep the protocol minimal: `get_value`, `has_value`, optionally `get_point`.

### Tests
- Unit test: a minimal in-memory MarketDataView stub satisfies the protocol and is usable by typing.
- Unit test: `MarketPoint` validation rejects NaN/Inf.

### Acceptance criteria
- Pricing depends only on the protocol, not on concrete data providers.
- Protocol is stable and does not leak storage concerns.
- Metadata is optional but structured for later quality propagation.

---

## PR-48 — Implement FX conversion core (FxRateResolver + FxConverter for EUR/USD)

### Goal
Implement Policy B conversion mechanics with explicit inversion and audit fields.

### References
- ADR-0202
- ADR-0203
- `docs/pricing/06_fx_conversion_engine.md`

### Tasks
1. Add `src/pricing/fx/resolver.py` implementing EUR/USD logic using `FX.EURUSD` (USD per EUR).
2. Expose `effective_rate(native, base, as_of) -> (rate, fx_asset_id, inverted)`.
3. Add `src/pricing/fx/converter.py` applying the rate to amounts with numeric hygiene.

### Tests
- Unit tests: EUR→USD uses direct EURUSD rate.
- Unit tests: USD→EUR uses inverted EURUSD rate and emits `FX_INVERTED_QUOTE` warning.
- Unit tests: same currency returns rate 1 with no FX asset id.
- Unit tests: missing FX raises MissingFxRateError.
- Unit tests: non-positive FX raises InvalidFxRateError.

### Acceptance criteria
- All conversions are deterministic and auditable.
- Outputs explicitly record FX asset id and inversion flag.
- No triangulation logic is introduced in MVP.

---

## PR-49 — Define pricer interface + pricer registry

### Goal
Create the pricer plugin boundary before implementing specific instruments.

### References
- ADR-0206
- `docs/pricing/04_pricer_api_and_registry.md`

### Tasks
1. Add `src/pricing/pricers/base.py` defining a small pricer interface.
2. Add `src/pricing/pricers/registry.py` mapping instrument spec kind to pricer.
3. Define failure behavior: missing pricer → typed error.

### Tests
- Unit test: registry registers and resolves pricers deterministically.
- Unit test: missing mapping raises a specific error.

### Acceptance criteria
- Adding a pricer does not require modifying existing pricers.
- No inheritance tree is introduced.
- Registry can be instantiated in tests with stub pricers.

---

## PR-50 — Implement CashPricer + tests

### Goal
Price cash positions in native currency and convert into base currency.

### References
- ADR-0201
- ADR-0202

### Tasks
1. Add `CashPricer` implementation under `src/pricing/pricers/cash.py`.
2. Cash value uses `quantity` as amount; unit_price=1.0 (documented).
3. Apply FX conversion when cash currency != base currency.

### Tests
- Unit test: EUR cash in EUR base yields fx_rate 1 and notional_base==notional_native.
- Unit test: USD cash in EUR base uses inverted EURUSD.
- Property test: scaling quantity scales notionals linearly.

### Acceptance criteria
- Cash valuation is deterministic and does not require market price points.
- FX conversion metadata is correctly populated.

---

## PR-51 — Implement EquityPricer (and tradable Index proxy) + tests

### Goal
Price equities using `close` (configurable) and convert into base currency.

### References
- ADR-0201
- ADR-0205

### Tasks
1. Add `EquityPricer` under `src/pricing/pricers/equity.py`.
2. Lookup `close` (or configured field) from `MarketDataView` using instrument's MarketDataId.
3. Compute notional_native = quantity * unit_price.
4. Apply FX conversion when needed and record inputs used.

### Tests
- Unit test: missing close raises MissingPriceError with context.
- Unit test: EUR equity in EUR base does not request FX.
- Unit test: USD equity in EUR base requests FX.EURUSD and inverts.
- Property test: scaling quantity scales notional.

### Acceptance criteria
- Equity pricing uses only MarketDataView and no direct data-layer imports.
- Inputs used (asset_id, field, date, value) are recorded in the output.

---

## PR-52 — Implement FuturePricer + tests (mark-to-market only)

### Goal
Price linear futures as `q * price * multiplier` and explicitly expose limitations.

### References
- ADR-0201
- ADR-0208

### Tasks
1. Add `FuturePricer` under `src/pricing/pricers/future.py`.
2. Read `close` via MarketDataView.
3. Multiply by instrument contract multiplier from instruments spec.
4. Apply FX conversion and record assumptions and inputs.

### Tests
- Unit test: future notional includes multiplier.
- Unit test: missing price raises MissingPriceError.
- Property test: scaling quantity scales notional.

### Acceptance criteria
- Pricer does not implement margining, settlement, or roll.
- Limitations are documented and/or included as warnings in the output.

---

## PR-53 — Implement ValuationEngine (portfolio → PortfolioValuation)

### Goal
Aggregate position valuations into a portfolio NAV with breakdown and lineage placeholders.

### References
- ADR-0202
- ADR-0207

### Tasks
1. Add `ValuationEngine` under `src/pricing/engine.py`.
2. Engine iterates portfolio positions, resolves instruments, calls registry pricer, aggregates NAV in base currency.
3. Compute `breakdown_by_currency` (native totals + base totals).
4. Aggregate warnings deterministically.

### Tests
- Integration test: small multi-currency portfolio valuation matches expected numbers.
- Unit test: breakdown_by_currency sums match position sums.

### Acceptance criteria
- NAV is base-currency numeric and finite.
- Engine is deterministic and side-effect free.
- Engine does not depend on risk or stress modules.

---

## PR-54 — Quality propagation: map MarketDataMeta → valuation warnings

### Goal
Carry upstream data quality information into pricing outputs without altering values.

### References
- ADR-0205
- `docs/pricing/07_missing_data_and_quality_flags.md`

### Tasks
1. If `MarketDataView.get_point` is available, propagate meta flags into `PositionValuation.warnings`.
2. Do not change numeric values based on quality.
3. Document the warning mapping and keep it stable.

### Tests
- Unit test: an imputed MarketPoint emits `MD_IMPUTED_FFILL` (or configured mapping).
- Unit test: missing meta does not break pricing.

### Acceptance criteria
- Warnings are deterministic and audit-friendly.
- Pricing remains fill-free (no new imputation introduced).

---

## PR-55 — Golden fixtures + example artifacts for EUR/USD portfolio valuation

### Goal
Add stable examples and snapshot tests for audit and regression coverage.

### References
- ADR-0209
- `docs/pricing/examples/*`

### Tasks
1. Add JSON examples under `docs/pricing/examples/` (portfolio + market data + expected valuation).
2. Add golden snapshot test(s) under `tests/pricing/` that compare output JSON to expected snapshot.
3. Ensure float formatting and rounding is consistent and documented.

### Tests
- Golden test: output matches `expected_portfolio_valuation_multi_ccy.json`.
- Unit test: schema versions match expected.

### Acceptance criteria
- Fixtures are tiny, deterministic, and committed.
- Golden tests fail with informative diffs.

---

## PR-56 — Data-layer adapter: `MarketDataView` wrapper over canonical dataset

### Goal
Provide a real adapter from `data/` canonical storage to the pricing protocol.

### References
- `docs/pricing/03_market_data_contract.md`

### Tasks
1. Implement an adapter class under `src/pricing/adapters/data_view.py` that wraps a canonical dataset object (from `src/data/`).
2. Adapter must not fetch network data.
3. Expose dataset lineage ids to pricing outputs (lineage placeholders filled where available).

### Tests
- Integration test: adapter reads known canonical dataset fixture and produces correct values.
- Unit test: adapter raises MissingPriceError consistently on missing points.

### Acceptance criteria
- No new dependency edges are introduced (pricing imports only from stable data schemas).
- Adapter is replaceable and tested.

### Notes
If the data module does not yet expose a convenient canonical dataset object, implement a minimal shim that can be replaced later without changing the pricing public API.

---

## PR-57 — Observability: structured logging for valuation runs

### Goal
Add diagnostics without changing deterministic results.

### References
- Project logging utilities (if present)
- ADR-0205

### Tasks
1. Add structured logging hooks in ValuationEngine (start/end, counts, warnings summary).
2. Ensure logs never include non-deterministic timestamps inside outputs.
3. Add log context: portfolio_id, as_of, base_currency, dataset lineage id if available.

### Tests
- Unit test: logging does not crash and includes expected keys (can use caplog).

### Acceptance criteria
- Logs are useful for debugging missing-data failures.
- Outputs remain unchanged (logging is side-channel only).

---

## PR-58 — Docs finalization and cross-module wiring

### Goal
Ensure documentation matches code and is complete for MVP sign-off.

### References
- `docs/pricing/*.md`
- `docs/modules/pricing.md`

### Tasks
1. Fill in `docs/pricing/01..09` with final file names and links.
2. Ensure every public type/function has docstrings that match the docs.
3. Add an integration seam note to `docs/instruments/08_integration_seams_pricing_risk.md` if that file exists.
4. Run a doc link check (manual or scripted) and fix broken paths.

### Acceptance criteria
- Docs accurately describe the implemented behavior and limitations.
- No contradictory statements across ADRs, backlog, and module docs.

---
