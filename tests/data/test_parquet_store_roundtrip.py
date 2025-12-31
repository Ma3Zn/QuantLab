from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from quantlab.data.schemas.requests import AssetId
from quantlab.data.storage.parquet_store import ParquetMarketDataStore


def _require_parquet_engine() -> None:
    if (
        importlib.util.find_spec("pyarrow") is None
        and importlib.util.find_spec("fastparquet") is None
    ):
        pytest.skip("parquet engine not installed")


def test_parquet_store_roundtrip(tmp_path: Path) -> None:
    _require_parquet_engine()

    store = ParquetMarketDataStore(tmp_path, provider="TEST")
    frame = pd.DataFrame(
        {
            "close": [10.0, 11.0, 12.0],
            "volume": [100, 150, 175],
        },
        index=[date(2023, 12, 29), date(2024, 1, 2), date(2024, 1, 3)],
    )

    paths = store.write_asset_frame(
        AssetId("EQ:SPY"),
        frame,
        meta={
            "vendor_symbol": "SPY",
            "ingestion_ts_utc": "2024-01-06T12:00:00+00:00",
        },
    )

    assert sorted(path.name for path in paths) == ["part-2023.parquet", "part-2024.parquet"]

    loaded = store.read_assets(
        [AssetId("EQ:SPY")],
        start=date(2023, 12, 29),
        end=date(2024, 1, 3),
        fields=["close", "volume"],
    )
    loaded_frame = loaded[AssetId("EQ:SPY")]

    expected = frame.copy()
    expected.index.name = "date"
    pd.testing.assert_frame_equal(loaded_frame, expected)
    assert loaded_frame.attrs["vendor_symbol"] == "SPY"
    assert loaded_frame.attrs["ingestion_ts_utc"] == "2024-01-06T12:00:00+00:00"
    assert loaded_frame.attrs["provider"] == "TEST"
