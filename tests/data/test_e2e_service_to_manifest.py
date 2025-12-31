from __future__ import annotations

import importlib.util
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence, cast

import pandas as pd
import pytest

from quantlab.data.providers import SymbolMapper
from quantlab.data.schemas.lineage import LineageMeta
from quantlab.data.schemas.requests import AssetId, CalendarSpec, TimeSeriesRequest
from quantlab.data.service import MarketDataService
from quantlab.data.storage.layout import manifest_path
from quantlab.data.storage.manifests import read_manifest
from quantlab.data.storage.parquet_store import ParquetMarketDataStore
from quantlab.data.transforms.calendars import TradingCalendar


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
        self.calls = 0
        self._frame = frame

    def fetch_eod(
        self,
        provider_symbols: Sequence[str],
        start: date,
        end: date,
        fields: Sequence[str],
    ) -> pd.DataFrame:
        self.calls += 1
        return self._frame


def test_e2e_service_to_manifest(tmp_path: Path) -> None:
    _require_parquet_engine()

    sessions = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    columns = pd.MultiIndex.from_tuples(
        [
            ("SPY", "close"),
            ("QQQ", "close"),
        ]
    )
    raw_frame = pd.DataFrame(
        [[100.0, 200.0], [101.0, 201.0], [102.0, 202.0]],
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
        dataset_version="2024-01-04",
        clock=lambda: datetime(2024, 1, 5, tzinfo=timezone.utc),
    )

    request = TimeSeriesRequest(
        assets=[AssetId("EQ:SPY"), AssetId("EQ:QQQ")],
        start=date(2024, 1, 2),
        end=date(2024, 1, 4),
        calendar=CalendarSpec(market="XNYS"),
    )

    bundle = service.get_timeseries(request)

    assert provider.calls == 1
    manifest_file = manifest_path(tmp_path, bundle.lineage.request_hash)
    assert manifest_file.exists()

    payload = read_manifest(tmp_path, bundle.lineage.request_hash)
    lineage = LineageMeta.from_dict(payload)

    payload_map = cast(Mapping[str, object], payload)
    assert payload_map["request_hash"] == bundle.lineage.request_hash
    assert payload_map["provider"] == "TEST"
    assert lineage.dataset_version == "2024-01-04"
    quality = payload_map.get("quality")
    assert isinstance(quality, Mapping)
    assert quality.get("coverage")
    storage_paths = payload_map.get("storage_paths")
    assert isinstance(storage_paths, list)
    assert storage_paths
    assert all(Path(path).exists() for path in storage_paths)

    service.get_timeseries(request)

    assert provider.calls == 1
