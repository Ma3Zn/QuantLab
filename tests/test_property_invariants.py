from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quantlab.data.normalizers import EQUITY_EOD_DATASET_ID, FX_DAILY_DATASET_ID, SCHEMA_VERSION
from quantlab.data.schemas import Bar, BarRecord, PointRecord, Source, TimestampProvenance
from quantlab.data.validators import validate_records

_ASOF_TS = datetime(2024, 1, 3, 7, 10, tzinfo=timezone.utc)
_SOURCE = Source(provider="TEST", endpoint="fixtures")

_UTC_DATETIMES = st.datetimes(timezones=st.just(timezone.utc))
_NAIVE_DATETIMES = st.datetimes(timezones=st.none())
_PRICES = st.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False)


@st.composite
def _ordered_ohlc(draw: Any) -> tuple[float, float, float, float]:
    open_price = draw(_PRICES)
    close_price = draw(_PRICES)
    low_max = min(open_price, close_price)
    high_min = max(open_price, close_price)
    low = draw(
        st.floats(
            min_value=0.01,
            max_value=low_max,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    high = draw(
        st.floats(
            min_value=high_min,
            max_value=high_min + 1000,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    return open_price, high, low, close_price


def _equity_record(ts: datetime, *, bar: Bar) -> BarRecord:
    return BarRecord(
        dataset_id=EQUITY_EOD_DATASET_ID,
        schema_version=SCHEMA_VERSION,
        dataset_version="2024-01-03",
        instrument_id="inst_eq_1",
        ts=ts,
        asof_ts=_ASOF_TS,
        ts_provenance=TimestampProvenance.EXCHANGE_CLOSE,
        source=_SOURCE,
        ingest_run_id="ing_001",
        quality_flags=(),
        trading_date_local=None,
        timezone_local=None,
        currency="USD",
        unit=None,
        bar=bar,
    )


def _fx_record(ts: datetime, *, field: str, value: float) -> PointRecord:
    return PointRecord(
        dataset_id=FX_DAILY_DATASET_ID,
        schema_version=SCHEMA_VERSION,
        dataset_version="2024-01-03",
        instrument_id="inst_fx_1",
        ts=ts,
        asof_ts=_ASOF_TS,
        ts_provenance=TimestampProvenance.EXCHANGE_CLOSE,
        source=_SOURCE,
        ingest_run_id="ing_001",
        quality_flags=(),
        trading_date_local=None,
        timezone_local=None,
        currency=None,
        unit=None,
        field=field,
        value=value,
        base_ccy="EUR",
        quote_ccy="USD",
    )


@given(ts=_UTC_DATETIMES, asof_ts=_UTC_DATETIMES)
@settings(max_examples=25, deadline=None)
def test_canonical_records_accept_utc_timestamps(ts: datetime, asof_ts: datetime) -> None:
    record = BarRecord(
        dataset_id=EQUITY_EOD_DATASET_ID,
        schema_version=SCHEMA_VERSION,
        dataset_version="2024-01-03",
        instrument_id="inst_eq_1",
        ts=ts,
        asof_ts=asof_ts,
        ts_provenance=TimestampProvenance.EXCHANGE_CLOSE,
        source=_SOURCE,
        ingest_run_id="ing_001",
        quality_flags=(),
        trading_date_local=None,
        timezone_local=None,
        currency="USD",
        unit=None,
        bar=Bar(close=1.0),
    )

    assert record.ts.tzinfo == timezone.utc
    assert record.asof_ts.tzinfo == timezone.utc


@given(ts=_NAIVE_DATETIMES)
@settings(max_examples=25, deadline=None)
def test_canonical_records_reject_naive_ts(ts: datetime) -> None:
    with pytest.raises(ValueError):
        _equity_record(ts, bar=Bar(close=1.0))


@given(ts=_NAIVE_DATETIMES)
@settings(max_examples=25, deadline=None)
def test_canonical_records_reject_naive_asof_ts(ts: datetime) -> None:
    with pytest.raises(ValueError):
        BarRecord(
            dataset_id=EQUITY_EOD_DATASET_ID,
            schema_version=SCHEMA_VERSION,
            dataset_version="2024-01-03",
            instrument_id="inst_eq_1",
            ts=datetime(2024, 1, 2, 21, 0, tzinfo=timezone.utc),
            asof_ts=ts,
            ts_provenance=TimestampProvenance.EXCHANGE_CLOSE,
            source=_SOURCE,
            ingest_run_id="ing_001",
            quality_flags=(),
            trading_date_local=None,
            timezone_local=None,
            currency="USD",
            unit=None,
            bar=Bar(close=1.0),
        )


@given(ts=_UTC_DATETIMES, ohlc=_ordered_ohlc())
@settings(max_examples=25, deadline=None)
def test_validator_accepts_ordered_ohlc(
    ts: datetime, ohlc: tuple[float, float, float, float]
) -> None:
    open_price, high_price, low_price, close_price = ohlc
    record = _equity_record(
        ts,
        bar=Bar(
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
        ),
    )

    _, report = validate_records(
        (record,),
        generated_ts=datetime(2024, 1, 4, tzinfo=timezone.utc),
        raise_on_hard_error=False,
    )

    assert report.hard_errors == ()


@given(ts=_UTC_DATETIMES, bid=_PRICES, ask=_PRICES)
@settings(max_examples=25, deadline=None)
def test_validator_flags_bid_ask_inversion(ts: datetime, bid: float, ask: float) -> None:
    assume(bid > ask)
    records = (
        _fx_record(ts, field="bid", value=bid),
        _fx_record(ts, field="ask", value=ask),
    )

    _, report = validate_records(
        records,
        generated_ts=datetime(2024, 1, 4, tzinfo=timezone.utc),
        raise_on_hard_error=False,
    )

    assert report.hard_errors


@given(ts=_UTC_DATETIMES, close=_PRICES)
@settings(max_examples=25, deadline=None)
def test_validator_rejects_duplicate_ts(ts: datetime, close: float) -> None:
    records = (
        _equity_record(ts, bar=Bar(close=close)),
        _equity_record(ts, bar=Bar(close=close)),
    )

    _, report = validate_records(
        records,
        generated_ts=datetime(2024, 1, 4, tzinfo=timezone.utc),
        raise_on_hard_error=False,
    )

    assert report.hard_errors
