from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from quantlab.data.errors import ValidationError
from quantlab.data.normalizers import (
    EQUITY_EOD_DATASET_ID,
    FX_DAILY_DATASET_ID,
    SCHEMA_VERSION,
)
from quantlab.data.quality import QualityFlag
from quantlab.data.schemas import Bar, BarRecord, PointRecord, Source
from quantlab.data.validators import validate_records

_ASOF_TS = datetime(2024, 1, 3, 7, 10, tzinfo=timezone.utc)


def _equity_record(ts: datetime, close: float) -> BarRecord:
    return BarRecord(
        dataset_id=EQUITY_EOD_DATASET_ID,
        schema_version=SCHEMA_VERSION,
        dataset_version="2024-01-03",
        instrument_id="inst_eq_1",
        ts=ts,
        asof_ts=_ASOF_TS,
        source=Source(provider="TEST", endpoint="eod_bars"),
        ingest_run_id="ing_001",
        quality_flags=(),
        trading_date_local=None,
        timezone_local=None,
        currency="USD",
        unit=None,
        bar=Bar(close=close),
    )


def _fx_record(ts: datetime, field: str, value: float, base_ccy: str) -> PointRecord:
    return PointRecord(
        dataset_id=FX_DAILY_DATASET_ID,
        schema_version=SCHEMA_VERSION,
        dataset_version="2024-01-03",
        instrument_id="inst_fx_1",
        ts=ts,
        asof_ts=_ASOF_TS,
        source=Source(provider="TEST", endpoint="fx_daily"),
        ingest_run_id="ing_001",
        quality_flags=(),
        trading_date_local=None,
        timezone_local=None,
        currency=None,
        unit=None,
        field=field,
        value=value,
        base_ccy=base_ccy,
        quote_ccy="USD",
    )


def test_validate_equity_flags_outlier_and_stale() -> None:
    start = datetime(2024, 1, 1, 21, 0, tzinfo=timezone.utc)
    records = (
        _equity_record(start, close=100.0),
        _equity_record(start + timedelta(days=1), close=100.0),
        _equity_record(start + timedelta(days=2), close=100.0),
        _equity_record(start + timedelta(days=3), close=140.0),
    )

    validated, report = validate_records(
        records,
        generated_ts=datetime(2024, 1, 4, tzinfo=timezone.utc),
        raise_on_hard_error=False,
    )

    assert QualityFlag.STALE in validated[2].quality_flags
    assert QualityFlag.OUTLIER_SUSPECT in validated[3].quality_flags
    assert report.hard_errors == ()
    assert report.flag_counts[QualityFlag.STALE] == 1
    assert report.flag_counts[QualityFlag.OUTLIER_SUSPECT] == 1


def test_validate_fx_hard_errors_raise() -> None:
    ts = datetime(2024, 1, 2, 17, 0, tzinfo=timezone.utc)
    records = (
        _fx_record(ts, field="bid", value=1.2, base_ccy="EURO"),
        _fx_record(ts, field="ask", value=1.1, base_ccy="EURO"),
    )

    _, report = validate_records(
        records,
        generated_ts=datetime(2024, 1, 3, tzinfo=timezone.utc),
        raise_on_hard_error=False,
    )

    assert report.hard_errors

    with pytest.raises(ValidationError):
        validate_records(
            records,
            generated_ts=datetime(2024, 1, 3, tzinfo=timezone.utc),
            raise_on_hard_error=True,
        )
