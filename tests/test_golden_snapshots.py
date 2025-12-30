from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from quantlab.data.ingestion import IngestionConfig, run_ingestion
from quantlab.data.normalizers import EQUITY_EOD_DATASET_ID, FX_DAILY_DATASET_ID, SCHEMA_VERSION
from quantlab.data.providers import FetchRequest, LocalFileProviderAdapter, TimeRange
from quantlab.data.sessionrules import load_seed_sessionrules
from quantlab.data.universe import load_seed_universe

GOLDEN_ROOT = Path(__file__).resolve().parent / "fixtures" / "golden"
DATASET_VERSION = "2024-01-03.1"
INGEST_RUN_ID = "ing_20240103_071000Z_0001"
CALENDAR_VERSION = "TestCal:2024.1"
ASOF_TS = datetime(2024, 1, 3, 7, 10, tzinfo=timezone.utc)
GENERATED_TS = datetime(2024, 1, 3, 7, 11, tzinfo=timezone.utc)


def _seed_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "seeds" / name


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
    )

    golden_dir = GOLDEN_ROOT / dataset_id
    golden_part = golden_dir / "part-0001.parquet"
    golden_metadata = golden_dir / "_metadata.json"
    drift_note = "Golden snapshot drift detected; bump dataset_version and regenerate fixtures."

    assert result.published_snapshot.part_paths[0].read_bytes() == golden_part.read_bytes(), (
        drift_note
    )
    actual_metadata = json.loads(
        result.published_snapshot.metadata_path.read_text(encoding="utf-8")
    )
    expected_metadata = json.loads(golden_metadata.read_text(encoding="utf-8"))
    assert actual_metadata == expected_metadata, drift_note
