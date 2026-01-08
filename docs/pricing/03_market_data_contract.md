# Market Data Contract for Pricing

## Goal
Allow `pricing/` to consume market data without depending on concrete providers or storage.

Pricing must depend only on a **read-only protocol**.

## Core protocol: `MarketDataView`
The view is an adapter over the `data/` layer canonical store.

Minimum capabilities (MVP):
- Retrieve a numeric value for `(asset_id, field, as_of_date)`
- Optionally retrieve metadata for the same point (quality, provenance)

### Required methods (conceptual)
- `get_value(asset_id, field, as_of) -> float`
- `has_value(asset_id, field, as_of) -> bool`

### Optional methods (recommended)
- `get_point(asset_id, field, as_of) -> MarketPoint`
  - `MarketPoint.value: float`
  - `MarketPoint.meta: MarketDataMeta | None`

## Asset identifiers
Pricing treats `asset_id` as an opaque identifier.
It expects the `instruments/` layer to provide each instrument's `MarketDataId` (usually `data.AssetId`).

### FX asset id (MVP)
- `FX.EURUSD` is required for EUR/USD conversion.
- Quote convention is defined in ADR-0203.

## Fields (MVP)
- For equities/futures: default field is `close`.
- For cash: no field required.

Field names must be documented and stable.
If you later add `open/high/low/volume`, do so without changing `close`.

## Missing data
Pricing does not decide how to fill missing data.
If the data layer chooses to provide imputed values (e.g., forward-fill), it should mark them via metadata.

Pricing policy:
- Missing required point → error.
- Imputed point with a quality flag → allowed, but warning is propagated.

## Determinism requirement
`MarketDataView` must be deterministic for a given dataset version.
Pricing outputs must include enough lineage to identify the dataset snapshot used.
