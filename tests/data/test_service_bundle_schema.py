from __future__ import annotations

import importlib.util
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Sequence

import pandas as pd
import pytest

from quantlab.data.providers import SymbolMapper
from quantlab.data.schemas.quality import QualityReport
from quantlab.data.schemas.requests import AssetId, CalendarSpec, TimeSeriesRequest
from quantlab.data.service import MarketDataService
from quantlab.data.storage.parquet_store import ParquetMarketDataStore
from quantlab.data.transforms.calendars import TradingCalendar
from quantlab.data.transforms.hashing import request_hash


def _require_parquet_engine() -> None:
    if (
        importlib.util.find_spec("pyarrow") is None
        and importlib.util.find_spec("fastparquet") is None
    ):
        pytest.skip("parquet engine not installed")


class _StaticCalendar:
    def __init__(self, sessions: list[date]) -> None:
        self._sessions = sessions

    def sessions(self, start: date, end: date) -> list[date]:
        return [value for value in self._sessions if start <= value <= end]


class _StubProvider:
    name = "TEST"

    def __init__(self, frame: pd.DataFrame) -> None:
        self._frame = frame

    def fetch_eod(
        self,
        provider_symbols: Sequence[str],
        start: date,
        end: date,
        fields: Sequence[str],
    ) -> pd.DataFrame:
        return self._frame


def test_service_bundle_schema(tmp_path: Path) -> None:
    _require_parquet_engine()

    sessions = [date(2024, 1, 2), date(2024, 1, 3)]
    columns = pd.MultiIndex.from_tuples(
        [
            ("SPY", "close"),
            ("QQQ", "close"),
        ]
    )
    raw_frame = pd.DataFrame(
        [[100.0, 200.0], [101.0, 201.0]],
        index=sessions,
        columns=columns,
    )

    provider = _StubProvider(raw_frame)
    store = ParquetMarketDataStore(tmp_path, provider="TEST")
    symbol_mapper = SymbolMapper(
        {
            AssetId("EQ:SPY"): "SPY",
            AssetId("EQ:QQQ"): "QQQ",
        }
    )

    def calendar_factory(_: CalendarSpec) -> TradingCalendar:
        return _StaticCalendar(sessions)

    service = MarketDataService(
        provider=provider,
        store=store,
        calendar_factory=calendar_factory,
        symbol_mapper=symbol_mapper,
        dataset_version="2024-01-03",
        clock=lambda: datetime(2024, 1, 4, tzinfo=timezone.utc),
    )

    request = TimeSeriesRequest(
        assets=[AssetId("EQ:SPY"), AssetId("EQ:QQQ")],
        start=date(2024, 1, 2),
        end=date(2024, 1, 3),
        calendar=CalendarSpec(market="XNYS"),
    )

    bundle = service.get_timeseries(request)

    assert isinstance(bundle.data.columns, pd.MultiIndex)
    assert bundle.data.columns.names == ["asset_id", "field"]
    assert list(bundle.data.columns.get_level_values(0)) == ["EQ:SPY", "EQ:QQQ"]
    assert bundle.data.index.name == "date"
    assert all(isinstance(value, date) for value in bundle.data.index)
    assert bundle.lineage.request_hash == request_hash(request)
    assert isinstance(bundle.quality, QualityReport)
    assert bundle.assets_meta[AssetId("EQ:SPY")]["provider_symbol"] == "SPY"
