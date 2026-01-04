# QuantLab Data Access Layer (MVP)

## Responsibilities
- Provide a single façade for aligned daily time series via `MarketDataService`.
- Normalize index semantics to market calendar `date` sessions.
- Persist raw, unadjusted prices to a deterministic cache + manifest registry.
- Emit quality guardrails (missing data, duplicates, suspect corporate actions).
- Attach lineage metadata (request hash, as-of, ingestion timestamp, storage paths).

## Non-goals
- Intraday data, futures/options, FX conversion, portfolio/risk logic.
- Corporate action adjustments (no split/dividend corrections).
- Silent cleaning or heuristic fixes beyond explicit flagging.

## Public API (MVP)
- `TimeSeriesRequest` (schemas/requests.py)
- `MarketDataService.get_timeseries(request) -> TimeSeriesBundle` (service.py)
- `MarketDataService.get_timeseries_from_cache(request_hash) -> TimeSeriesBundle` (service.py)
- `TimeSeriesBundle` contains `data`, `assets_meta`, `quality`, `lineage`.

Example (see `examples/scripts/data_pull_demo.py` for a runnable demo):

```python
from datetime import date
from pathlib import Path

from quantlab.data.providers import SymbolMapper
from quantlab.data.schemas.requests import AssetId, CalendarSpec, TimeSeriesRequest
from quantlab.data.service import MarketDataService
from quantlab.data.storage.parquet_store import ParquetMarketDataStore
from quantlab.data.transforms.calendars import MarketCalendarAdapter

service = MarketDataService(
    provider=my_provider,
    store=ParquetMarketDataStore(Path("data/cache"), provider="DEMO"),
    calendar_factory=lambda spec: MarketCalendarAdapter(spec.market),
    symbol_mapper=SymbolMapper({AssetId("EQ:SPY"): "SPY"}),
)

request = TimeSeriesRequest(
    assets=[AssetId("EQ:SPY")],
    start=date(2024, 1, 2),
    end=date(2024, 1, 5),
    calendar=CalendarSpec(market="XNYS"),
)

bundle = service.get_timeseries(request)
```

Demo config and sample data live under `data/sample/`:
`python examples/scripts/data_pull_demo.py --config data/sample/data_pull_config.json`

## Alignment semantics
- The target index is the market calendar sessions between `start` and `end`.
- Output index type is `date`, monotonic and unique.
- Alignment always occurs before validation.

## Missing-data policies
- `NAN_OK`: keep calendar dates and leave gaps as NaN.
- `DROP_DATES`: remove any date with missing values.
- `ERROR`: raise a `DataValidationError` on missing data.

## Guardrails and limitations
- Prices are **raw-only**. No corporate action adjustments are applied.
- Suspect corporate actions are flagged when absolute returns exceed a threshold.
- Nonpositive prices raise by default (configurable via `ValidationPolicy`).

Known limitations:
- Survivorship bias is possible if delistings are not represented in the universe.
- Provider "close" semantics may vary; treat vendor metadata as authoritative.
- Guardrails flag issues but do not correct them.

## Reproducibility and storage
- Each request has a deterministic `request_hash`.
- Cached parquet lives under `data/cache/market/<provider>/<asset_id>/1D/`.
- Each request writes a manifest under `data/cache/manifests/<request_hash>.json`.
- `as_of` is recorded in manifests and request hashes; historical as-of replay is best-effort.

## Failure modes (typed)
- Missing symbol mapping: `ProviderFetchError`.
- Missing calendar or invalid dates: `DataValidationError`.
- Storage read/write failures: `StorageError`.
