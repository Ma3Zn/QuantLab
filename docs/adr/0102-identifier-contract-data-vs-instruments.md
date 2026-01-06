## Status
Accepted

## Date
2026-01-06

## Decision
Introduce a strict identifier contract:
- `InstrumentId`: internal, stable identity of an `Instrument` object (portfolio/book-level identity).
- `MarketDataId` (reusing `data.AssetId` where available): identifier used to fetch time series from `data/`.

Each `Instrument` MUST carry a `market_data_id` (or an explicit “no market data” marker), and downstream modules MUST use `market_data_id` to query `data/`.

We explicitly do **not** conflate `InstrumentId` with `MarketDataId`.

## Context
Market data identity differs from instrument identity in realistic settings (futures chains, continuous series, index references, synthetic baskets). Conflation creates “string soup”, collisions, and silent misbinding of time series.

## Options Considered
1. **Separate InstrumentId and MarketDataId (chosen)**
2. Single ID used for both internal identity and market data
3. Provider-specific tickers as universal keys

## Trade-offs
- Slightly more verbose domain objects (two identifiers).
- Greatly improved correctness and future extensibility.

## Consequences
- `data/` remains the single owner of fetching/caching/versioning of time series keyed by `MarketDataId`.
- `instruments/` remains provider-agnostic and portable.
- Futures can be represented with:
  - `InstrumentId` per contract (e.g., ESZ6)
  - `MarketDataId` per contract OR continuous series OR mapped synthetic series, depending on `data/` capabilities.

## Failure Modes Addressed
- Ticker collisions across venues/currencies.
- Contract roll ambiguity for futures.
- Index vs tradable instrument confusion.

## Migration / Follow-ups
- If `data/` already defines `AssetId`, `instruments/` should import it as `MarketDataId` alias rather than duplicating.
- Add a mapping adapter only in `data/` or a dedicated adapter layer (not in `instruments/`).

## Acceptance Criteria
- Every instrument either:
  - has a valid `market_data_id`, or
  - declares `market_data_id=None` with a clear reason (“non-priced reference”, etc.).
- No module downstream uses raw tickers/strings without explicit type.
