# Currency and FX Policy (Policy B)

## Objective
Support portfolios that include positions in at least **EUR** and **USD** while producing a single base-currency NAV.

## Supported currencies (MVP)
- EUR
- USD

Any other currency is rejected in the MVP.
This is a guardrail, not a long-term design decision.

## Base currency
- The portfolio declares a `base_currency` (EUR or USD).
- Every position has a native currency (`instrument_currency`).
- Valuation produces both:
  - native-currency notional, and
  - base-currency notional.

## Canonical FX storage convention (MVP)
Pricing assumes the market data layer exposes a canonical FX asset:

- `FX.EURUSD` with price field `close`
- Quote convention: **USD per 1 EUR**

This is the single FX time series required for EUR/USD conversion in the MVP.

## Effective conversion rate
Pricing computes an **effective rate** `r` such that:

`amount_in_base = amount_in_native * r`

Rules using `FX.EURUSD = USD per EUR`:

- If native = base: `r = 1`
- If native = EUR and base = USD: `r = FX.EURUSD`
- If native = USD and base = EUR: `r = 1 / FX.EURUSD`

The output must record:
- which FX asset id was used (`FX.EURUSD`)
- whether inversion was applied
- the effective rate `r`

## Error policy
- Missing `FX.EURUSD` at `as_of` → error.
- Non-positive FX rates → error.
- If portfolio uses both EUR and USD, `FX.EURUSD` is mandatory even if base currency equals one of them.

## Quality and “as_of alignment”
- If the data layer aligns markets with carry-forward, it must surface a quality flag.
- Pricing may propagate these flags as warnings but must not alter values.

## Extensions (future)
- Add additional canonical pairs (e.g., `FX.EURGBP`).
- Add triangulation via a small FX graph.
- Add intraday timestamps and session rules.
