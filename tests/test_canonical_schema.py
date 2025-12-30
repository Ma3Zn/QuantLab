from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

import pytest

from quantlab.data.schemas import Bar, BarRecord, PointRecord, Source, TimestampProvenance


def _base_metadata() -> dict[str, Any]:
    return {
        "dataset_id": "md.equity.eod.bars",
        "schema_version": "1.0.0",
        "dataset_version": "2024-12-24",
        "instrument_id": "inst_123",
        "ts": datetime(2024, 12, 23, 21, 0, tzinfo=timezone.utc),
        "asof_ts": datetime(2024, 12, 24, 7, 10, 3, tzinfo=timezone.utc),
        "ts_provenance": TimestampProvenance.EXCHANGE_CLOSE,
        "source": Source(provider="TEST", endpoint="eod_bars"),
        "ingest_run_id": "ing_001",
        "quality_flags": (),
        "trading_date_local": None,
        "timezone_local": None,
        "currency": None,
        "unit": None,
    }


def test_bar_record_requires_utc_and_close() -> None:
    metadata = _base_metadata() | {
        "trading_date_local": date(2024, 12, 23),
        "timezone_local": "America/New_York",
        "currency": "USD",
        "quality_flags": ("MISSING_VALUE",),
    }
    record = BarRecord(**metadata, bar=Bar(open=1.0, high=2.0, low=0.5, close=1.5, volume=10))

    assert record.ts.tzinfo == timezone.utc
    payload = record.to_payload()
    assert payload["bar"]["close"] == 1.5
    assert payload["quality_flags"] == ["MISSING_VALUE"]
    assert payload["trading_date_local"] == "2024-12-23"
    assert payload["ts_provenance"] == "EXCHANGE_CLOSE"


def test_point_record_requires_utc_and_fields() -> None:
    metadata = _base_metadata() | {"dataset_id": "md.fx.spot.daily"}
    record = PointRecord(
        **metadata,
        field="mid",
        value=1.2345,
        base_ccy="EUR",
        quote_ccy="USD",
    )

    assert record.asof_ts.tzinfo == timezone.utc
    payload = record.to_payload()
    assert payload["field"] == "mid"
    assert payload["base_ccy"] == "EUR"
    assert payload["quote_ccy"] == "USD"
    assert payload["ts_provenance"] == "EXCHANGE_CLOSE"


@pytest.mark.parametrize(
    "ts_value",
    [
        datetime(2024, 12, 23, 21, 0),  # naive
        datetime(2024, 12, 23, 21, 0, tzinfo=timezone(timedelta(hours=1))),  # non-UTC tz
    ],
)
def test_utc_enforcement_for_ts(ts_value: datetime) -> None:
    metadata = _base_metadata() | {"ts": ts_value}

    with pytest.raises(ValueError):
        BarRecord(**metadata, bar=Bar(close=1.0))
