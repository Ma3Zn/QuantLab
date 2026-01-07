# Instruments Layer Documentation Index

This directory documents the **Instruments layer** of QuantLab: the canonical domain objects for instruments, positions, and portfolio snapshots, and the stable contracts they expose to downstream modules.

## Files
- `src/instruments/README.md` — repo-facing module README (responsibilities, non-goals, quickstart).
- `docs/modules/instruments.md` — detailed module overview (scope, integration, limitations, extension path).
- `docs/instruments/README.md` — documentation directory overview.
- `docs/instruments/QUICKSTART.md` — minimal “construct/validate/serialize” verification steps.
- `docs/instruments/00_instruments_layer_spec_mvp.md` — 1–2 page MVP spec (scope, invariants, determinism).
- `docs/instruments/01_identifier_policy_mvp.md` — InstrumentId vs MarketDataId contract + binding rules to `data/`.
- `docs/instruments/02_pydantic_models_contract.md` — Pydantic v2 modeling contract (config, unions, canonicalization).
- `docs/instruments/03_instrument_specs_mvp.md` — instrument spec models + required fields and invariants (MVP set).
- `docs/instruments/04_position_and_portfolio_semantics.md` — long-only positions + deterministic portfolio snapshots.
- `docs/instruments/05_canonical_json_contract.md` — canonical JSON rules + schema versioning + examples.
- `docs/instruments/06_errors_and_diagnostics.md` — error model + diagnostics requirements.
- `docs/instruments/07_testing_plan_mvp.md` — unit/property/golden test plan and minimum coverage matrix.
- `docs/instruments/08_integration_seams_pricing_risk.md` — seam contracts to `pricing/`, `risk/`, `stress/`.
- `docs/instruments/90_codex_implementation_plan.md` — step-by-step Codex implementation plan mapped to ADRs.
- `docs/instruments/examples/01_portfolio_equity_cash.json` — canonical portfolio example (equities + cash).
- `docs/instruments/examples/02_portfolio_future.json` — canonical portfolio example (future + cash).
- `docs/instruments/examples/03_portfolio_multi_currency_cash.json` — canonical portfolio example (multi-currency cash).

## ADRs
- `docs/adr/0101-instruments-scope-mvp.md` — MVP scope and explicit non-goals.
- `docs/adr/0102-instruments-identifier-contract.md` — identifier contract with `data/`.
- `docs/adr/0103-instruments-pydantic-v2.md` — modeling choice: Pydantic v2.
- `docs/adr/0104-instruments-value-objects.md` — value objects and unit conventions.
- `docs/adr/0105-instruments-composition-over-inheritance.md` — composition + discriminated union specs.
- `docs/adr/0106-instruments-position-long-only.md` — long-only positions in MVP.
- `docs/adr/0107-instruments-portfolio-snapshot.md` — portfolio snapshot determinism.
- `docs/adr/0108-instruments-canonical-json.md` — canonical JSON + schema versioning.
- `docs/adr/0109-instruments-errors-and-tests.md` — error model + test strategy.
- `docs/adr/0110-instruments-seams-pricing-risk.md` — seams as data contracts (no interfaces in instruments).

## Tests and fixtures
- `tests/unit/instruments/` — unit tests for invariants and validation.
- `tests/property/instruments/` — property-based tests for canonicalization and round-trips.
- `tests/golden/instruments/` — golden JSON portfolio fixtures.

## Next planned docs (not yet written)
- Shorting + financing/margin semantics extension (separate module proposal).
- Corporate actions and instrument master data (event model and provenance).
- Derivative payoff specs (options/barriers) with strict separation from pricing.
