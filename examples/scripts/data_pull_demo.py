from __future__ import annotations

import argparse
import importlib.util
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Literal, Mapping, Sequence, cast

import pandas as pd

from quantlab.data.providers import SymbolMapper
from quantlab.data.schemas.errors import ProviderFetchError
from quantlab.data.schemas.quality import QualityFlag
from quantlab.data.schemas.requests import AssetId, CalendarSpec, TimeSeriesRequest
from quantlab.data.service import MarketDataService
from quantlab.data.storage.parquet_store import ParquetMarketDataStore
from quantlab.data.transforms.calendars import MarketCalendarAdapter

FieldLiteral = Literal["close", "open", "high", "low", "volume"]
_FIELD_LITERALS: set[FieldLiteral] = {"close", "open", "high", "low", "volume"}


@dataclass(frozen=True)
class DemoConfig:
    provider: str
    calendar: str
    assets: list[AssetId]
    symbol_map: dict[AssetId, str]
    start: date
    end: date
    fields: list[str]
    data_path: Path
    report_path: Path
    cache_path: Path


class CsvEodProvider:
    name: str

    def __init__(self, name: str, csv_path: Path) -> None:
        self.name = name
        self._csv_path = csv_path

    def fetch_eod(
        self,
        provider_symbols: Sequence[str],
        start: date,
        end: date,
        fields: Sequence[str],
    ) -> pd.DataFrame:
        if not self._csv_path.exists():
            raise ProviderFetchError(
                "sample CSV missing",
                context={"path": str(self._csv_path)},
            )
        data = pd.read_csv(self._csv_path)
        required_columns = {"date", "symbol"}
        missing_columns = required_columns - set(data.columns)
        if missing_columns:
            raise ProviderFetchError(
                "sample CSV missing required columns",
                context={"missing_columns": sorted(missing_columns)},
            )
        missing_fields = [field for field in fields if field not in data.columns]
        if missing_fields:
            raise ProviderFetchError(
                "sample CSV missing requested fields",
                context={"missing_fields": missing_fields},
            )

        data["date"] = pd.to_datetime(data["date"]).dt.date
        symbols = set(data["symbol"].astype(str))
        missing_symbols = [symbol for symbol in provider_symbols if symbol not in symbols]
        if missing_symbols:
            raise ProviderFetchError(
                "sample CSV missing requested symbols",
                context={"missing_symbols": missing_symbols},
            )

        mask = (
            data["symbol"].isin(provider_symbols) & (data["date"] >= start) & (data["date"] <= end)
        )
        subset = data.loc[mask]
        if subset.empty:
            raise ProviderFetchError(
                "sample CSV has no rows for requested range",
                context={
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "symbols": provider_symbols,
                },
            )

        frames: list[pd.DataFrame] = []
        for field in fields:
            pivoted = subset.pivot(index="date", columns="symbol", values=field)
            pivoted = pivoted.reindex(columns=provider_symbols)
            pivoted.columns = pd.MultiIndex.from_product([pivoted.columns, [field]])
            frames.append(pivoted)
        combined = pd.concat(frames, axis=1)
        combined = combined.sort_index()
        return combined


def _require_parquet_engine() -> None:
    if (
        importlib.util.find_spec("pyarrow") is None
        and importlib.util.find_spec("fastparquet") is None
    ):
        raise SystemExit(
            "Parquet engine not installed. Install pyarrow or fastparquet to run the demo."
        )


def _load_config(path: Path) -> DemoConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assets = [AssetId(asset) for asset in payload["assets"]]
    symbol_map = {AssetId(key): str(value) for key, value in payload["symbol_map"].items()}
    return DemoConfig(
        provider=str(payload["provider"]),
        calendar=str(payload["calendar"]),
        assets=assets,
        symbol_map=symbol_map,
        start=date.fromisoformat(str(payload["start"])),
        end=date.fromisoformat(str(payload["end"])),
        fields=list(payload["fields"]),
        data_path=Path(payload["data_path"]),
        report_path=Path(payload["report_path"]),
        cache_path=Path(payload["cache_path"]),
    )


def _build_report(
    request_hash: str,
    coverage: Mapping[AssetId, float],
    suspect_dates: Mapping[AssetId, list[str]],
) -> dict[str, object]:
    return {
        "request_hash": request_hash,
        "coverage": {str(asset): value for asset, value in coverage.items()},
        "suspect_corp_action_dates": {str(asset): dates for asset, dates in suspect_dates.items()},
    }


def _normalize_fields(values: Sequence[str]) -> set[FieldLiteral]:
    if not values:
        raise SystemExit("fields must be non-empty")
    unknown = [value for value in values if value not in _FIELD_LITERALS]
    if unknown:
        raise SystemExit(f"unknown fields in config: {unknown}")
    return cast(set[FieldLiteral], set(values))


def _extract_suspect_dates(
    assets: Iterable[AssetId],
    examples: Mapping[AssetId, Mapping[QualityFlag, list[str]]],
) -> dict[AssetId, list[str]]:
    suspect: dict[AssetId, list[str]] = {}
    for asset in assets:
        asset_examples = examples.get(asset, {})
        suspect[asset] = asset_examples.get(QualityFlag.SUSPECT_CORP_ACTION, [])
    return suspect


def main() -> None:
    parser = argparse.ArgumentParser(description="QuantLab data pull demo")
    parser.add_argument(
        "--config",
        default="data/sample/data_pull_config.json",
        help="Path to JSON config file",
    )
    args = parser.parse_args()
    config_path = Path(args.config)
    config = _load_config(config_path)

    _require_parquet_engine()

    provider = CsvEodProvider(config.provider, config.data_path)
    store = ParquetMarketDataStore(config.cache_path, provider=config.provider)
    symbol_mapper = SymbolMapper(config.symbol_map)

    service = MarketDataService(
        provider=provider,
        store=store,
        calendar_factory=lambda spec: MarketCalendarAdapter(spec.market),
        symbol_mapper=symbol_mapper,
    )

    request = TimeSeriesRequest(
        assets=config.assets,
        start=config.start,
        end=config.end,
        fields=_normalize_fields(config.fields),
        calendar=CalendarSpec(market=config.calendar),
    )

    bundle = service.get_timeseries(request)
    suspect_dates = _extract_suspect_dates(config.assets, bundle.quality.flag_examples)
    report = _build_report(bundle.lineage.request_hash, bundle.quality.coverage, suspect_dates)

    report_path = config.report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    print("Coverage:")
    for asset, value in bundle.quality.coverage.items():
        print(f"  {asset}: {value:.2%}")
    print("Suspect corporate action dates:")
    for asset, dates in suspect_dates.items():
        print(f"  {asset}: {dates or 'none'}")
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
