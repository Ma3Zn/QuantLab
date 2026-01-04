from __future__ import annotations

import importlib.util
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import pandas as pd
import pytest

from quantlab.data.identity import request_fingerprint
from quantlab.data.ingestion import IngestionConfig, build_canonical_parts, run_ingestion
from quantlab.data.normalizers import (
    EQUITY_EOD_DATASET_ID,
    FX_DAILY_DATASET_ID,
    SCHEMA_VERSION,
    NormalizationContext,
    normalize_equity_eod,
    normalize_fx_daily,
)
from quantlab.data.providers import FetchRequest, LocalFileProviderAdapter, TimeRange
from quantlab.data.registry import lookup_registry_entry
from quantlab.data.schemas import CanonicalRecord, Source
from quantlab.data.sessionrules import load_seed_sessionrules
from quantlab.data.storage import compute_content_hash, read_ingest_run_meta
from quantlab.data.universe import load_seed_universe
from quantlab.data.validators import ValidationContext, validate_records
from quantlab.instruments.master import InstrumentType


def _universe_seed_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "seeds" / "universe_v1.yaml"


def _sessionrules_seed_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "seeds" / "sessionrules_v1.yaml"


def _write_payload(tmp_path: Path, payload: dict[str, object]) -> Path:
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    return payload_path


def _require_parquet_engine() -> None:
    if (
        importlib.util.find_spec("pyarrow") is None
        and importlib.util.find_spec("fastparquet") is None
    ):
        pytest.skip("parquet engine not installed")


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
def test_run_ingestion_pipeline_rebuilds_from_raw(
    tmp_path: Path,
    dataset_id: str,
    endpoint: str,
    payload: dict[str, object],
    instrument_ids: tuple[str, ...],
) -> None:
    _require_parquet_engine()
    universe = load_seed_universe(_universe_seed_path())
    sessionrules = load_seed_sessionrules(_sessionrules_seed_path())

    payload_path = _write_payload(tmp_path, payload)
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
        dataset_version="2024-01-03.1",
        ingest_run_id="ing_20240103_071000Z_0001",
        raw_root=tmp_path / "raw",
        canonical_root=tmp_path / "canonical",
        registry_path=tmp_path / "registry.jsonl",
        calendar_version="TestCal:2024.1",
        schema_version=SCHEMA_VERSION,
        notes="seed run",
    )
    asof_ts = datetime(2024, 1, 3, 7, 10, tzinfo=timezone.utc)
    generated_ts = datetime(2024, 1, 3, 7, 11, tzinfo=timezone.utc)
    started_at_ts = datetime(2024, 1, 3, 7, 9, tzinfo=timezone.utc)
    finished_at_ts = datetime(2024, 1, 3, 7, 12, tzinfo=timezone.utc)

    result = run_ingestion(
        request,
        adapter,
        config=config,
        universe=universe,
        sessionrules=sessionrules,
        asof_ts=asof_ts,
        generated_ts=generated_ts,
        created_at_ts=generated_ts,
        started_at_ts=started_at_ts,
        finished_at_ts=finished_at_ts,
    )

    assert result.registry_entry.dataset_id == dataset_id
    assert result.registry_entry.row_count == 1
    assert result.registry_entry.universe_hash == universe.universe_hash
    assert result.registry_entry.sessionrules_version == sessionrules.sessionrules_hash
    assert result.registry_entry.content_hash == result.published_snapshot.content_hash

    metadata = json.loads(result.published_snapshot.metadata_path.read_text(encoding="utf-8"))
    assert metadata["dataset_id"] == dataset_id
    assert metadata["row_count"] == 1

    registry_entry = lookup_registry_entry(
        config.registry_path,
        config.dataset_id,
        config.dataset_version,
    )
    assert registry_entry == result.registry_entry
    assert compute_content_hash(result.published_snapshot.part_paths) == registry_entry.content_hash

    raw_metadata = json.loads(result.raw_paths.metadata_path.read_text(encoding="utf-8"))
    raw_payload = result.raw_paths.payload_path.read_bytes()
    rebuilt_context = ValidationContext(
        dataset_id=raw_metadata["dataset_id"],
        dataset_version=raw_metadata["dataset_version"],
        ingest_run_id=raw_metadata["ingest_run_id"],
    )
    normalizer_context = NormalizationContext(
        dataset_id=raw_metadata["dataset_id"],
        schema_version=raw_metadata["schema_version"],
        dataset_version=raw_metadata["dataset_version"],
        asof_ts=datetime.fromisoformat(raw_metadata["asof_ts"]),
        ingest_run_id=raw_metadata["ingest_run_id"],
        source=Source(**raw_metadata["source"]),
    )

    normalized: Sequence[CanonicalRecord]

    if dataset_id == EQUITY_EOD_DATASET_ID:
        lookup = {
            (record.mic or "", record.vendor_symbol or ""): record
            for record in universe.instruments
            if record.instrument_type == InstrumentType.EQUITY
        }
        normalized = normalize_equity_eod(
            raw_payload,
            context=normalizer_context,
            instrument_lookup=lookup,
        )
    else:
        lookup = {
            (record.base_ccy or "", record.quote_ccy or ""): record
            for record in universe.instruments
            if record.instrument_type == InstrumentType.FX_SPOT
        }
        normalized = normalize_fx_daily(
            raw_payload,
            context=normalizer_context,
            instrument_lookup=lookup,
        )

    rebuilt, _ = validate_records(
        normalized,
        context=rebuilt_context,
        generated_ts=generated_ts,
        raise_on_hard_error=True,
    )
    rebuilt_parts = build_canonical_parts(rebuilt)
    rebuilt_payload = rebuilt_parts["part-0001.parquet"]
    stored_payload = result.published_snapshot.part_paths[0].read_bytes()
    rebuilt_frame = pd.read_parquet(io.BytesIO(rebuilt_payload))
    stored_frame = pd.read_parquet(io.BytesIO(stored_payload))
    pd.testing.assert_frame_equal(rebuilt_frame, stored_frame, check_dtype=False)

    expected_fingerprint = request_fingerprint(
        {
            "dataset_id": config.dataset_id,
            "dataset_version": config.dataset_version,
            "schema_version": config.schema_version,
            "calendar_version": config.calendar_version,
            "universe_hash": universe.universe_hash,
            "sessionrules_version": sessionrules.sessionrules_hash,
            "notes": config.notes,
        }
    )
    assert result.ingest_run_meta.config_fingerprint == expected_fingerprint
    assert result.ingest_run_meta.started_at_ts == started_at_ts
    assert result.ingest_run_meta.finished_at_ts == finished_at_ts

    stored_meta = read_ingest_run_meta(config.raw_root, config.ingest_run_id)
    assert stored_meta == result.ingest_run_meta
