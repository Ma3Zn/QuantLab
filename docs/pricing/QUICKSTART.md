# Pricing — Quickstart (Conceptual)

This is a **conceptual** quickstart.
It documents intended contracts and data flow.
It is not an implementation guide.

## Goal
Compute a portfolio valuation (NAV) at a chosen `as_of` date.

## Inputs you provide
1. A `Portfolio` object with:
   - a list of `Position` objects
   - a declared `base_currency` (EUR or USD in the MVP)
2. A `MarketDataView` that can return:
   - instrument prices (e.g., `close`) for each position's `MarketDataId`
   - the FX rate asset needed for EUR/USD conversion (canonical `FX.EURUSD`)

## Data flow (intended)
1. `ValuationEngine` iterates positions.
2. For each position:
   - select the registered pricer for the instrument kind
   - read the required market data point(s)
   - compute native-currency notional
   - convert notional into portfolio base currency via `FxConverter`
   - emit a `PositionValuation` containing prices and FX used
3. Engine aggregates:
   - NAV in base currency
   - per-currency breakdown
   - warnings and lineage

## Expected invariants
- Deterministic results for identical inputs.
- No silent fills:
  - missing price → error
  - missing FX → error
- Currency conversion is explicit in output:
  - which FX pair was used
  - whether the quote was inverted
  - the effective rate applied to convert into base currency

## Minimal example artifacts
See `docs/pricing/examples/`:
- `portfolio_multi_ccy.json`
- `market_data_minimal_multi_ccy.json`
- `expected_portfolio_valuation_multi_ccy.json`
