# Identifier Policy (01)

## Why two identifiers
The instruments layer distinguishes:
- `InstrumentId`: internal identity used in positions and reports.
- `MarketDataId`: identifier used to query `data/` for time series.

Do **not** treat tickers as universal identifiers.

## Proposed formats (MVP)
### InstrumentId
A stable, human-readable string with a prefix namespace:
- `EQ.<SYMBOL>` (equity/ETF)
- `IDX.<NAME>` (index reference)
- `CASH.<CCY>`
- `FUT.<ROOT>.<YYYYMM>` or `FUT.<ROOT>.<CONTRACT>` (choose one and document)
- `BOND.<ISSUER>.<YYYYMMDD>` (metadata reference)

Constraints:
- 1..64 chars
- uppercase recommended
- no whitespace

### MarketDataId
Prefer reusing `data.AssetId` (typed). If `data.AssetId` supports venue/MIC, include it.
Examples:
- equity: `AssetId(symbol="AAPL", venue="XNAS")`
- index: `AssetId(symbol="SPX", venue="INDEX")` (if supported) or `None` if reference-only
- futures: either contract-level ID or continuous-series ID (explicitly documented)

## Binding rules
- If an instrument is intended to be priced from market data, `market_data_id` MUST be set.
- If reference-only, `market_data_id` MAY be `None` but this must be explicit via a flag in the spec.

## Failure modes
- ticker collisions across venues/currencies
- futures roll ambiguity
- synthetic instruments sharing a data series unintentionally

## Implementation requirement
Codex must locate the existing `AssetId` (or equivalent) in `src/data/` and import it.
If not present, create `src/data/ids.py` with a minimal, forward-compatible `AssetId` model and update imports.
