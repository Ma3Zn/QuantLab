# Pricing Scope — MVP

## What the module does
- Computes **mark-to-market** valuations for a portfolio at an `as_of` date.
- Produces per-position valuations plus a portfolio-level valuation (NAV).
- Supports **multi-currency portfolios** with explicit FX conversion into a base currency.
- Surfaces assumptions and inputs used (price field, FX pair, inversion).

## What the module does not do (MVP)
- No risk metrics (VaR/ES, volatility, Greeks).
- No optimization or decision outputs.
- No curve construction, discounting, or bond accrual logic.
- No nonlinear derivatives (options, barriers, knock-outs, structured products).
- No transaction costs, slippage, or liquidity constraints.

## Instruments in scope (MVP)
### 1) Cash
- Valuation equals cash amount in its currency.
- If base currency differs, FX conversion is applied.

### 2) Equity (and tradable index proxies)
- Unit price comes from market data (default `close`).
- Notional = `quantity * unit_price`.

### 3) Linear futures
- Unit price comes from market data (default `close`).
- Notional = `quantity * unit_price * contract_multiplier`.
- **Explicit limitation:** margining, settlement, and roll are out of scope.

## Assumptions
- Daily bars are the canonical pricing source for the MVP.
- `as_of` is a date, not a timestamp.
- Market data has been cleaned/aligned upstream by the `data/` module.
- All computation is deterministic.

## Failure modes (must be explicit in code and outputs)
- Missing price for a position at `as_of` → error (no implicit fill here).
- Missing FX rate needed for conversion → error.
- Currency outside the supported set (EUR, USD) → error (MVP guardrail).
- NaN/Inf numeric inputs → error.

## MVP extensions (future)
- FX triangulation beyond EUR/USD.
- Dividend/corporate action adjustments (upstream or via explicit plug-in).
- Curve-based pricing for bonds and swaps.
- Futures roll models and continuous contract handling.
- Options pricers with Greeks and calibration.

## Related docs
- `INDEX.md`
- `02_currency_and_fx_policy.md`
- `../adr/0201-pricing-scope-mvp.md`
- `../adr/0208-pricing-futures-simplification.md`
