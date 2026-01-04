from __future__ import annotations

import importlib.util
import io
import json
from typing import Callable, Sequence, TypeVar

import pandas as pd

from quantlab.data.errors import StorageError
from quantlab.data.quality import QualityFlag
from quantlab.data.schemas.records import BarRecord, CanonicalRecord, PointRecord

CANONICAL_COMMON_COLUMNS = [
    "dataset_id",
    "schema_version",
    "dataset_version",
    "instrument_id",
    "ts",
    "asof_ts",
    "ts_provenance",
    "source_provider",
    "source_endpoint",
    "source_provider_dataset",
    "ingest_run_id",
    "quality_flags",
    "trading_date_local",
    "timezone_local",
    "currency",
    "unit",
]

CANONICAL_BAR_COLUMNS = CANONICAL_COMMON_COLUMNS + [
    "bar_open",
    "bar_high",
    "bar_low",
    "bar_close",
    "bar_volume",
    "bar_adj_close",
    "bar_adjustment_basis",
    "bar_adjustment_note",
]

CANONICAL_POINT_COLUMNS = CANONICAL_COMMON_COLUMNS + [
    "field",
    "value",
    "base_ccy",
    "quote_ccy",
    "fixing_convention",
]


def parquet_engine_available() -> bool:
    return (
        importlib.util.find_spec("pyarrow") is not None
        or importlib.util.find_spec("fastparquet") is not None
    )


def canonical_records_to_frame(records: Sequence[CanonicalRecord]) -> pd.DataFrame:
    if not records:
        raise ValueError("records must not be empty")

    if isinstance(records[0], BarRecord):
        return _records_to_frame(records, CANONICAL_BAR_COLUMNS, _bar_row, BarRecord)
    elif isinstance(records[0], PointRecord):
        return _records_to_frame(records, CANONICAL_POINT_COLUMNS, _point_row, PointRecord)
    else:  # pragma: no cover - defensive
        raise ValueError("unsupported canonical record type")


def serialize_canonical_records(records: Sequence[CanonicalRecord]) -> bytes:
    if not parquet_engine_available():
        raise StorageError(
            "parquet engine not installed",
            context={"engines": ["pyarrow", "fastparquet"]},
        )

    frame = canonical_records_to_frame(records)
    buffer = io.BytesIO()
    try:
        engine = "pyarrow" if importlib.util.find_spec("pyarrow") is not None else "fastparquet"
        frame.to_parquet(buffer, index=False, engine=engine)
    except (ImportError, ValueError, OSError) as exc:
        raise StorageError(
            "failed to serialize canonical parquet",
            context={"record_count": len(records)},
            cause=exc,
        ) from exc
    return buffer.getvalue()


TCanonicalRecord = TypeVar("TCanonicalRecord", bound=CanonicalRecord)


def _records_to_frame(
    records: Sequence[CanonicalRecord],
    columns: Sequence[str],
    row_builder: Callable[[TCanonicalRecord], dict[str, object]],
    record_type: type[TCanonicalRecord],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for index, record in enumerate(records):
        if not isinstance(record, record_type):
            raise ValueError(f"record {index} type mismatch in canonical payload")
        rows.append(row_builder(record))

    return pd.DataFrame(rows, columns=columns)


def _serialize_quality_flags(flags: Sequence[QualityFlag]) -> str:
    normalized = [QualityFlag(flag).value for flag in flags]
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _common_row(record: CanonicalRecord) -> dict[str, object]:
    return {
        "dataset_id": record.dataset_id,
        "schema_version": record.schema_version,
        "dataset_version": record.dataset_version,
        "instrument_id": record.instrument_id,
        "ts": record.ts.isoformat(),
        "asof_ts": record.asof_ts.isoformat(),
        "ts_provenance": record.ts_provenance.value,
        "source_provider": record.source.provider,
        "source_endpoint": record.source.endpoint,
        "source_provider_dataset": record.source.provider_dataset,
        "ingest_run_id": record.ingest_run_id,
        "quality_flags": _serialize_quality_flags(record.quality_flags),
        "trading_date_local": record.trading_date_local.isoformat()
        if record.trading_date_local
        else None,
        "timezone_local": record.timezone_local,
        "currency": record.currency,
        "unit": record.unit,
    }


def _bar_row(record: BarRecord) -> dict[str, object]:
    payload = _common_row(record)
    bar = record.bar
    payload.update(
        {
            "bar_open": bar.open,
            "bar_high": bar.high,
            "bar_low": bar.low,
            "bar_close": bar.close,
            "bar_volume": bar.volume,
            "bar_adj_close": bar.adj_close,
            "bar_adjustment_basis": bar.adjustment_basis.value if bar.adjustment_basis else None,
            "bar_adjustment_note": bar.adjustment_note,
        }
    )
    return payload


def _point_row(record: PointRecord) -> dict[str, object]:
    payload = _common_row(record)
    payload.update(
        {
            "field": record.field,
            "value": record.value,
            "base_ccy": record.base_ccy,
            "quote_ccy": record.quote_ccy,
            "fixing_convention": record.fixing_convention,
        }
    )
    return payload


__all__ = [
    "CANONICAL_COMMON_COLUMNS",
    "CANONICAL_BAR_COLUMNS",
    "CANONICAL_POINT_COLUMNS",
    "parquet_engine_available",
    "canonical_records_to_frame",
    "serialize_canonical_records",
]
