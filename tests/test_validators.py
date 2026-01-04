from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from quantlab.data.errors import ValidationError
from quantlab.data.normalizers import (
    EQUITY_EOD_DATASET_ID,
    FX_DAILY_DATASET_ID,
    SCHEMA_VERSION,
)
from quantlab.data.quality import QualityFlag
from quantlab.data.schemas import Bar, BarRecord, PointRecord, Source, TimestampProvenance
from quantlab.data.sessionrules import load_seed_sessionrules
from quantlab.data.universe import load_seed_universe
from quantlab.data.validators import TimeSemanticsContext, validate_records

_ASOF_TS = datetime(2024, 1, 3, 7, 10, tzinfo=timezone.utc)


def _equity_record(
    ts: datetime,
    close: float,
    *,
    ts_provenance: TimestampProvenance = TimestampProvenance.EXCHANGE_CLOSE,
) -> BarRecord:
    return BarRecord(
        dataset_id=EQUITY_EOD_DATASET_ID,
        schema_version=SCHEMA_VERSION,
        dataset_version="2024-01-03",
        instrument_id="inst_eq_1",
        ts=ts,
        asof_ts=_ASOF_TS,
        ts_provenance=ts_provenance,
        source=Source(provider="TEST", endpoint="eod_bars"),
        ingest_run_id="ing_001",
        quality_flags=(),
        trading_date_local=None,
        timezone_local=None,
        currency="USD",
        unit=None,
        bar=Bar(close=close),
    )


def _fx_record(
    ts: datetime,
    field: str,
    value: float,
    base_ccy: str,
    *,
    ts_provenance: TimestampProvenance = TimestampProvenance.EXCHANGE_CLOSE,
) -> PointRecord:
    return PointRecord(
        dataset_id=FX_DAILY_DATASET_ID,
        schema_version=SCHEMA_VERSION,
        dataset_version="2024-01-03",
        instrument_id="inst_fx_1",
        ts=ts,
        asof_ts=_ASOF_TS,
        ts_provenance=ts_provenance,
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


def test_validate_records_adds_provider_timestamp_flag() -> None:
    ts = datetime(2024, 1, 2, 21, 0, tzinfo=timezone.utc)
    records = (_equity_record(ts, close=100.0, ts_provenance=TimestampProvenance.PROVIDER_EOD),)

    validated, report = validate_records(
        records,
        generated_ts=datetime(2024, 1, 3, tzinfo=timezone.utc),
        raise_on_hard_error=False,
    )

    assert QualityFlag.PROVIDER_TIMESTAMP_USED in validated[0].quality_flags
    assert report.flag_counts[QualityFlag.PROVIDER_TIMESTAMP_USED] == 1


class _ClosedCalendar:
    def sessions(self, start: date, end: date) -> list[date]:
        return []


def test_validate_records_flags_calendar_conflict_on_closed_day() -> None:
    universe = load_seed_universe(
        Path(__file__).resolve().parents[1] / "data" / "seeds" / "universe_v1.yaml"
    )
    sessionrules = load_seed_sessionrules(
        Path(__file__).resolve().parents[1] / "data" / "seeds" / "sessionrules_v1.yaml"
    )
    instrument = next(
        record for record in universe.instruments if record.vendor_symbol == "AAPL"
    )
    record = BarRecord(
        dataset_id=EQUITY_EOD_DATASET_ID,
        schema_version=SCHEMA_VERSION,
        dataset_version="2024-01-03",
        instrument_id=instrument.instrument_id,
        ts=datetime(2024, 1, 2, 21, 0, tzinfo=timezone.utc),
        asof_ts=_ASOF_TS,
        ts_provenance=TimestampProvenance.PROVIDER_EOD,
        source=Source(provider="TEST", endpoint="eod_bars"),
        ingest_run_id="ing_001",
        quality_flags=(),
        trading_date_local=date(2024, 1, 2),
        timezone_local=instrument.exchange_timezone,
        currency=instrument.currency,
        unit=None,
        bar=Bar(close=192.8),
    )

    time_context = TimeSemanticsContext(
        universe=universe,
        sessionrules=sessionrules,
        calendar_factory=lambda _mic: _ClosedCalendar(),
    )

    validated, report = validate_records(
        (record,),
        generated_ts=datetime(2024, 1, 3, tzinfo=timezone.utc),
        time_context=time_context,
        raise_on_hard_error=False,
    )

    assert QualityFlag.CALENDAR_CONFLICT in validated[0].quality_flags
    assert report.flag_counts[QualityFlag.CALENDAR_CONFLICT] == 1
