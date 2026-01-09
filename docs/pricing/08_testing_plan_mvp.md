# Pricing Testing Plan (MVP)

## Principles
- Test invariants, not just examples.
- Prefer small deterministic fixtures.
- Include golden snapshots for auditable outputs.

## Unit tests
### Value objects and errors
- schema version present
- dates serialized as ISO
- numeric values must be finite
- currency guardrails enforced (EUR/USD)

### FX conversion
- EUR→USD uses `FX.EURUSD`
- USD→EUR inverts `FX.EURUSD`
- same currency yields rate 1
- invalid FX (<=0, NaN/Inf) raises error

### Pricers
- Cash: notional equals quantity; no price lookup required
- Equity: notional equals `q * close`
- Future: notional equals `q * close * multiplier`

## Property-based tests (Hypothesis)
- Linearity: scaling quantity scales notional (native and base) linearly.
- Currency invariance: if base==native then `notional_base == notional_native`.
- FX inversion: USD→EUR equals EUR→USD inverse, given same `eurusd`.

## Golden snapshot tests
- Fixed portfolio + fixed market data → stable JSON output.
- Snapshot includes:
  - inputs used
  - fx inversion flags
  - nav and breakdown
- Snapshots normalize floats to 10 decimal places for stable diffs (valuation outputs remain unrounded).

## Integration test
- Minimal `MarketDataView` adapter over a canonical dataset object.
- End-to-end: Portfolio → ValuationEngine → `PortfolioValuation`.

## Non-goals (MVP)
- Statistical tests.
- Performance benchmarks (add later once scale is known).

## Related docs
- `INDEX.md`
- `05_valuation_outputs_contract.md`
- `../adr/0209-pricing-testing-strategy.md`
