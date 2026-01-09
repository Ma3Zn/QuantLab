# Valuation Outputs Contract (Typed + Canonical JSON)

## Design goals
- Outputs are typed and serializable.
- Outputs are audit-friendly.
- Outputs preserve enough information to reproduce the valuation.

## `PositionValuation` (MVP)
Minimum fields:
- `schema_version` (string or int, documented)
- `as_of` (date)
- `instrument_id`
- `market_data_id` (asset id used for pricing, if any)
- `instrument_kind`
- `quantity`
- `instrument_currency`
- `unit_price` (native currency; `None` for cash is acceptable if documented)
- `notional_native`
- `base_currency`
- `fx_asset_id_used` (e.g., `FX.EURUSD`, or `None` if same currency)
- `fx_inverted` (bool)
- `fx_rate_effective` (float; equals 1.0 if same currency)
- `notional_base`
- `inputs` (structured list of points used: asset_id/field/value/date)
- `warnings` (list of string codes, stable vocabulary)

## `PortfolioValuation` (MVP)
Minimum fields:
- `schema_version`
- `as_of`
- `base_currency`
- `nav_base`
- `positions` (list of `PositionValuation`)
- `breakdown_by_currency`:
  - per native currency: total native notional
  - per native currency: total base notional
- `warnings` (aggregated)
- `lineage` (dataset version identifiers, request hashes, etc.)

## Canonical JSON rules
- Deterministic field ordering is not required, but stable schema is.
- Floats must be finite (no NaN/Inf).
- Dates serialized as ISO `YYYY-MM-DD`.
- Enumerations serialized by their stable string value.

## Example (illustrative)
See `docs/pricing/examples/expected_portfolio_valuation_multi_ccy.json`.

## Related docs
- `INDEX.md`
- `08_testing_plan_mvp.md`
- `../adr/0207-pricing-outputs-canonical-json.md`
