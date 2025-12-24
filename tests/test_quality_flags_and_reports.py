from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from quantlab.data.quality import QualityFlag, ValidationReport
from quantlab.data.schemas import Bar, BarRecord, Source


def _base_metadata() -> dict[str, Any]:
    return {
        "dataset_id": "md.equity.eod.bars",
        "schema_version": "1.0.0",
        "dataset_version": "2024-12-24",
        "instrument_id": "inst_123",
        "ts": datetime(2024, 12, 23, 21, 0, tzinfo=timezone.utc),
        "asof_ts": datetime(2024, 12, 24, 7, 10, 3, tzinfo=timezone.utc),
        "source": Source(provider="TEST", endpoint="eod_bars"),
        "ingest_run_id": "ing_001",
        "quality_flags": (),
        "trading_date_local": None,
        "timezone_local": None,
        "currency": None,
        "unit": None,
    }


def test_quality_flag_enum_is_stable() -> None:
    expected = {
        "MISSING_VALUE",
        "STALE",
        "OUTLIER_SUSPECT",
        "ADJUSTED_PRICE_PRESENT",
        "PROVIDER_TIMESTAMP_USED",
        "IMPUTED",
    }
    assert {flag.value for flag in QualityFlag} == expected
    assert QualityFlag("MISSING_VALUE") is QualityFlag.MISSING_VALUE


def test_canonical_record_normalizes_quality_flags() -> None:
    metadata = _base_metadata() | {
        "quality_flags": ("MISSING_VALUE", QualityFlag.OUTLIER_SUSPECT),
    }
    record = BarRecord(**metadata, bar=Bar(close=1.0))

    assert record.quality_flags == (
        QualityFlag.MISSING_VALUE,
        QualityFlag.OUTLIER_SUSPECT,
    )
    payload = record.to_payload()
    assert payload["quality_flags"] == ["MISSING_VALUE", "OUTLIER_SUSPECT"]


def test_canonical_record_rejects_unknown_flags() -> None:
    metadata = _base_metadata() | {"quality_flags": ("UNKNOWN_FLAG",)}

    with pytest.raises(ValueError):
        BarRecord(**metadata, bar=Bar(close=1.0))


def test_validation_report_serializes_with_flag_counts() -> None:
    generated_ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    report = ValidationReport(
        dataset_id="md.equity.eod.bars",
        dataset_version="2024-12-24",
        ingest_run_id="ing_001",
        generated_ts=generated_ts,
        total_records=2,
        hard_errors=("missing asof_ts",),
        flag_counts={QualityFlag.MISSING_VALUE: 1, QualityFlag.STALE: 0},
    )

    payload = report.to_payload()
    assert payload["dataset_id"] == "md.equity.eod.bars"
    assert payload["generated_ts"] == "2024-01-01T00:00:00+00:00"
    assert payload["hard_errors"] == ["missing asof_ts"]
    assert payload["flag_counts"] == {"MISSING_VALUE": 1, "STALE": 0}
