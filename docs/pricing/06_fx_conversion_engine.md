# FX Conversion Engine

## Objective
Convert native-currency notionals into the portfolio base currency with explicit, auditable logic.

## MVP constraints
- Supported currencies: EUR and USD.
- Canonical FX asset: `FX.EURUSD` quoted as USD per EUR.
- No triangulation.
- No intraday timestamps.

## Components (conceptual)
### 1) `FxRateResolver`
- Reads the required FX point(s) from `MarketDataView`.
- Produces the effective conversion rate `r` such that:
  `amount_in_base = amount_in_native * r`
- Records:
  - `fx_asset_id_used`
  - `fx_inverted`
  - `fx_rate_effective`

### 2) `FxConverter`
- Applies the effective rate to amounts.
- Centralizes numeric hygiene and guards:
  - rejects non-positive FX
  - rejects NaN/Inf

## Algorithm (MVP)
Given:
- `base_currency` ∈ {EUR, USD}
- `native_currency` ∈ {EUR, USD}
- `eurusd = MarketDataView.get_value("FX.EURUSD", "close", as_of)` (USD per EUR)

Compute:
- if native == base: `r = 1`
- if native == EUR and base == USD: `r = eurusd` (not inverted)
- if native == USD and base == EUR: `r = 1 / eurusd` (inverted)

## Error policy
- Missing `FX.EURUSD` point → error.
- `eurusd <= 0` → error.
- Unsupported currencies → error.

## Future extensions
- Add more canonical FX assets.
- Add an FX graph for triangulation.
- Add `datetime` and session rules.
