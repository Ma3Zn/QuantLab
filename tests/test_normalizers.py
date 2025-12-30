from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from quantlab.data.errors import NormalizationError
from quantlab.data.normalizers import (
    EQUITY_EOD_DATASET_ID,
    FX_DAILY_DATASET_ID,
    SCHEMA_VERSION,
    NormalizationContext,
    normalize_equity_eod,
    normalize_fx_daily,
)
from quantlab.data.quality import QualityFlag
from quantlab.data.schemas import Source, TimestampProvenance
from quantlab.data.universe import load_seed_universe
from quantlab.instruments.master import InstrumentMasterRecord, InstrumentType


def _seed_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "seeds" / "universe_v1.yaml"


def _equity_lookup() -> dict[tuple[str, str], InstrumentMasterRecord]:
    snapshot = load_seed_universe(_seed_path())
    return {
        (record.mic or "", record.vendor_symbol or ""): record
        for record in snapshot.instruments
        if record.instrument_type == InstrumentType.EQUITY
    }


def _fx_lookup() -> dict[tuple[str, str], InstrumentMasterRecord]:
    snapshot = load_seed_universe(_seed_path())
    return {
        (record.base_ccy or "", record.quote_ccy or ""): record
        for record in snapshot.instruments
        if record.instrument_type == InstrumentType.FX_SPOT
    }


def test_normalize_equity_eod_payload_bytes() -> None:
    context = NormalizationContext(
        dataset_id=EQUITY_EOD_DATASET_ID,
        schema_version=SCHEMA_VERSION,
        dataset_version="2024-01-03",
        asof_ts=datetime(2024, 1, 3, 7, 10, tzinfo=timezone.utc),
        ingest_run_id="ing_20240103_071000Z_0001",
        source=Source(provider="TEST", endpoint="eod_bars"),
    )
    payload = {
        "records": [
            {
                "mic": "XNYS",
                "vendor_symbol": "AAPL",
                "ts": "2024-01-02T21:00:00Z",
                "trading_date": "2024-01-02",
                "open": 190.0,
                "high": 193.5,
                "low": 188.2,
                "close": 192.8,
                "volume": 1200,
                "adj_close": 191.9,
                "adjustment_basis": "SPLIT_ONLY",
            }
        ]
    }

    records = normalize_equity_eod(
        json.dumps(payload).encode("utf-8"),
        context=context,
        instrument_lookup=_equity_lookup(),
    )

    assert len(records) == 1
    record = records[0]
    assert record.ts == datetime(2024, 1, 2, 21, 0, tzinfo=timezone.utc)
    assert record.trading_date_local == date(2024, 1, 2)
    assert record.timezone_local == "America/New_York"
    assert record.currency == "USD"
    assert record.bar.close == 192.8
    assert record.bar.adjustment_basis is not None
    assert record.quality_flags == (QualityFlag.ADJUSTED_PRICE_PRESENT,)
    assert record.ts_provenance is TimestampProvenance.PROVIDER_EOD


def test_normalize_equity_eod_payload_csv() -> None:
    context = NormalizationContext(
        dataset_id=EQUITY_EOD_DATASET_ID,
        schema_version=SCHEMA_VERSION,
        dataset_version="2024-01-03",
        asof_ts=datetime(2024, 1, 3, 7, 10, tzinfo=timezone.utc),
        ingest_run_id="ing_20240103_071000Z_0001",
        source=Source(provider="TEST", endpoint="eod_bars"),
    )
    payload = (
        "mic,vendor_symbol,ts,trading_date,close\nXNYS,AAPL,2024-01-02T21:00:00Z,2024-01-02,192.8\n"
    )

    records = normalize_equity_eod(
        payload,
        context=context,
        instrument_lookup=_equity_lookup(),
    )

    assert len(records) == 1
    record = records[0]
    assert record.bar.close == 192.8
    assert record.trading_date_local == date(2024, 1, 2)
    assert record.ts_provenance is TimestampProvenance.PROVIDER_EOD


def test_normalize_fx_daily_payload_mapping() -> None:
    context = NormalizationContext(
        dataset_id=FX_DAILY_DATASET_ID,
        schema_version=SCHEMA_VERSION,
        dataset_version="2024-01-03",
        asof_ts=datetime(2024, 1, 3, 7, 10, tzinfo=timezone.utc),
        ingest_run_id="ing_20240103_071000Z_0001",
        source=Source(provider="TEST", endpoint="fx_daily"),
    )
    payload = {
        "records": [
            {
                "base_ccy": "EUR",
                "quote_ccy": "USD",
                "ts": "2024-01-02T17:00:00Z",
                "fixing_date": "2024-01-02",
                "field": "mid",
                "value": 1.0785,
                "fixing_convention": "provider_eod_fix",
            }
        ]
    }

    records = normalize_fx_daily(
        payload,
        context=context,
        instrument_lookup=_fx_lookup(),
    )

    assert len(records) == 1
    record = records[0]
    assert record.base_ccy == "EUR"
    assert record.quote_ccy == "USD"
    assert record.field == "mid"
    assert record.value == 1.0785
    assert record.trading_date_local == date(2024, 1, 2)
    assert record.ts_provenance is TimestampProvenance.PROVIDER_EOD


def test_normalize_equity_eod_missing_instrument_raises() -> None:
    context = NormalizationContext(
        dataset_id=EQUITY_EOD_DATASET_ID,
        schema_version=SCHEMA_VERSION,
        dataset_version="2024-01-03",
        asof_ts=datetime(2024, 1, 3, 7, 10, tzinfo=timezone.utc),
        ingest_run_id="ing_20240103_071000Z_0001",
        source=Source(provider="TEST", endpoint="eod_bars"),
    )
    payload = {
        "records": [
            {
                "mic": "XNYS",
                "vendor_symbol": "UNKNOWN",
                "ts": "2024-01-02T21:00:00Z",
                "trading_date": "2024-01-02",
                "close": 192.8,
            }
        ]
    }

    with pytest.raises(NormalizationError):
        normalize_equity_eod(payload, context=context, instrument_lookup=_equity_lookup())
