from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from quantlab.data.ingestion import IngestionConfig, run_ingestion
from quantlab.data.normalizers import EQUITY_EOD_DATASET_ID, FX_DAILY_DATASET_ID, SCHEMA_VERSION
from quantlab.data.providers import FetchRequest, LocalFileProviderAdapter, TimeRange
from quantlab.data.sessionrules import load_seed_sessionrules
from quantlab.data.storage.canonical_parquet import (
    CANONICAL_BAR_COLUMNS,
    CANONICAL_POINT_COLUMNS,
)
from quantlab.data.universe import load_seed_universe

GOLDEN_ROOT = Path(__file__).resolve().parent / "fixtures" / "golden"
DATASET_VERSION = "2024-01-03.1"
INGEST_RUN_ID = "ing_20240103_071000Z_0001"
CALENDAR_VERSION = "TestCal:2024.1"
ASOF_TS = datetime(2024, 1, 3, 7, 10, tzinfo=timezone.utc)
GENERATED_TS = datetime(2024, 1, 3, 7, 11, tzinfo=timezone.utc)


def _seed_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "seeds" / name


def _require_parquet_engine() -> None:
    if (
        importlib.util.find_spec("pyarrow") is None
        and importlib.util.find_spec("fastparquet") is None
    ):
        pytest.skip("parquet engine not installed")


def _flags_json(flags: list[str]) -> str:
    return json.dumps(flags, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@pytest.mark.parametrize(
    ("dataset_id", "endpoint", "payload", "instrument_ids"),
    [
        (
            EQUITY_EOD_DATASET_ID,
            "eod_bars",
            {
                "records": [
                    {
                        "mic": "XNYS",
                        "vendor_symbol": "AAPL",
                        "ts": "2024-01-02T21:00:00Z",
                        "trading_date": "2024-01-02",
                        "close": 192.8,
                    }
                ]
            },
            ("EQ-0001",),
        ),
        (
            FX_DAILY_DATASET_ID,
            "fx_daily",
            {
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
            },
            ("FX-0001",),
        ),
    ],
)
def test_golden_canonical_snapshot(
    tmp_path: Path,
    dataset_id: str,
    endpoint: str,
    payload: dict[str, object],
    instrument_ids: tuple[str, ...],
) -> None:
    _require_parquet_engine()
    universe = load_seed_universe(_seed_path("universe_v1.yaml"))
    sessionrules = load_seed_sessionrules(_seed_path("sessionrules_v1.yaml"))

    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    adapter = LocalFileProviderAdapter(
        provider="TEST",
        endpoint=endpoint,
        payload_path=payload_path,
        payload_format="json",
    )
    request = FetchRequest(
        dataset_id=dataset_id,
        instrument_ids=instrument_ids,
        time_range=TimeRange(
            start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end=datetime(2024, 1, 3, tzinfo=timezone.utc),
        ),
        fields=("close",),
    )
    config = IngestionConfig(
        dataset_id=dataset_id,
        dataset_version=DATASET_VERSION,
        ingest_run_id=INGEST_RUN_ID,
        raw_root=tmp_path / "raw",
        canonical_root=tmp_path / "canonical",
        registry_path=tmp_path / "registry.jsonl",
        calendar_version=CALENDAR_VERSION,
        schema_version=SCHEMA_VERSION,
    )

    result = run_ingestion(
        request,
        adapter,
        config=config,
        universe=universe,
        sessionrules=sessionrules,
        asof_ts=ASOF_TS,
        generated_ts=GENERATED_TS,
        created_at_ts=GENERATED_TS,
        started_at_ts=ASOF_TS,
        finished_at_ts=GENERATED_TS,
    )

    drift_note = "Golden snapshot drift detected; bump dataset_version and regenerate fixtures."

    result_frame = pd.read_parquet(result.published_snapshot.part_paths[0])

    if dataset_id == EQUITY_EOD_DATASET_ID:
        instrument = next(
            record
            for record in universe.instruments
            if record.vendor_symbol == "AAPL" and record.mic == "XNYS"
        )
        expected = pd.DataFrame(
            [
                {
                    "dataset_id": dataset_id,
                    "schema_version": SCHEMA_VERSION,
                    "dataset_version": DATASET_VERSION,
                    "instrument_id": instrument.instrument_id,
                    "ts": "2024-01-02T21:00:00+00:00",
                    "asof_ts": ASOF_TS.isoformat(),
                    "ts_provenance": "PROVIDER_EOD",
                    "source_provider": "TEST",
                    "source_endpoint": "eod_bars",
                    "source_provider_dataset": None,
                    "ingest_run_id": INGEST_RUN_ID,
                    "quality_flags": _flags_json(["PROVIDER_TIMESTAMP_USED"]),
                    "trading_date_local": "2024-01-02",
                    "timezone_local": instrument.exchange_timezone,
                    "currency": instrument.currency,
                    "unit": None,
                    "bar_open": None,
                    "bar_high": None,
                    "bar_low": None,
                    "bar_close": 192.8,
                    "bar_volume": None,
                    "bar_adj_close": None,
                    "bar_adjustment_basis": None,
                    "bar_adjustment_note": None,
                }
            ],
            columns=CANONICAL_BAR_COLUMNS,
        )
    else:
        instrument = next(
            record
            for record in universe.instruments
            if record.base_ccy == "EUR" and record.quote_ccy == "USD"
        )
        expected = pd.DataFrame(
            [
                {
                    "dataset_id": dataset_id,
                    "schema_version": SCHEMA_VERSION,
                    "dataset_version": DATASET_VERSION,
                    "instrument_id": instrument.instrument_id,
                    "ts": "2024-01-02T17:00:00+00:00",
                    "asof_ts": ASOF_TS.isoformat(),
                    "ts_provenance": "PROVIDER_EOD",
                    "source_provider": "TEST",
                    "source_endpoint": "fx_daily",
                    "source_provider_dataset": None,
                    "ingest_run_id": INGEST_RUN_ID,
                    "quality_flags": _flags_json(["PROVIDER_TIMESTAMP_USED"]),
                    "trading_date_local": "2024-01-02",
                    "timezone_local": None,
                    "currency": None,
                    "unit": None,
                    "field": "mid",
                    "value": 1.0785,
                    "base_ccy": "EUR",
                    "quote_ccy": "USD",
                    "fixing_convention": "provider_eod_fix",
                }
            ],
            columns=CANONICAL_POINT_COLUMNS,
        )

    pd.testing.assert_frame_equal(result_frame, expected, check_dtype=False)
    actual_metadata = json.loads(
        result.published_snapshot.metadata_path.read_text(encoding="utf-8")
    )
    golden_dir = GOLDEN_ROOT / dataset_id
    golden_metadata = golden_dir / "_metadata.json"
    expected_metadata = json.loads(golden_metadata.read_text(encoding="utf-8"))
    assert actual_metadata == expected_metadata, drift_note
