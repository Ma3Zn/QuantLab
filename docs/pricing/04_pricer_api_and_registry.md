# Pricer API and Registry

## Objectives
- Keep pricers small and composable.
- Avoid inheritance hierarchies.
- Ensure every pricer is deterministic and explainable.

## Pricer contract (conceptual)
A pricer is a component that can:
- declare what market data fields it requires
- compute a `PositionValuation` for a position

### Conceptual signature
`price(position, instrument, market_data_view, context) -> PositionValuation`

Where `context` contains:
- `as_of` (date)
- `base_currency`
- `price_field` (default `close`)
- `fx_converter`

## Registry
A `PricerRegistry` maps instrument kind/spec to a pricer instance.
Examples:
- `CashSpec` → `CashPricer`
- `EquitySpec` → `EquityPricer`
- `FutureSpec` → `FuturePricer`

The registry must:
- fail fast if a pricer is missing for a supported instrument kind
- be easily extendable without changing existing pricers

## Determinism and purity
Pricers must be side-effect free:
- no I/O
- no global state
- no time-dependent behavior

## Explainability requirements
Each `PositionValuation` must include:
- price(s) used (value + field + asset_id + date)
- assumptions specific to the pricer (e.g., futures multiplier)
- FX conversion used (if any)

## Extension points
- Add bond pricer once curve contracts exist.
- Add option pricer only after risk layer requirements are explicit.

## Related docs
- `INDEX.md`
- `05_valuation_outputs_contract.md`
- `../adr/0206-pricing-pricer-registry-composition.md`
