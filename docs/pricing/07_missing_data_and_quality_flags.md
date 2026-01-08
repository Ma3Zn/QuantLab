# Missing Data and Quality Flags

## Goal
Make data quality explicit.
Do not hide missing data or imputation.

## Pricing policy (MVP)
### Missing required market data
- If a required price is missing at `as_of`, pricing fails fast with a typed error.
- If `FX.EURUSD` is required and missing, pricing fails fast.

### Imputed or adjusted values
Pricing must not create imputed values.
If the data layer provides an imputed value, it should be accompanied by a quality flag.

Pricing behavior:
- propagate quality flags to `warnings`
- never change the numeric value

## Warning vocabulary (MVP)
Warnings are stable string codes defined in `src/quantlab/pricing/warnings.py`:
- `FX_INVERTED_QUOTE`
- `FUTURE_MTM_ONLY`
- `MD_IMPUTED_FFILL`
- `MD_STALE_SOURCE_DATE`

## Error taxonomy (MVP)
Errors are typed and defined in `src/quantlab/pricing/errors.py`:
- `MissingPriceError`
- `MissingFxRateError`
- `UnsupportedCurrencyError`
- `NonFiniteInputError`
- `InvalidFxRateError`

## Deterministic handling
Warnings must be deterministic given inputs.
No probabilistic or heuristic decisions in the MVP.

## Future
- Severity levels (INFO/WARN/ERROR).
- Policy-driven tolerance (e.g., allow stale FX within 1 business day).
