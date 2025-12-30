from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from math import isfinite
from typing import Callable, Hashable, Iterable, Sequence

from quantlab.data.errors import ValidationError
from quantlab.data.normalizers import EQUITY_EOD_DATASET_ID, FX_DAILY_DATASET_ID
from quantlab.data.quality import QualityFlag, ValidationReport
from quantlab.data.schemas import (
    BarRecord,
    CanonicalRecord,
    PointRecord,
    TimestampProvenance,
)

DEFAULT_EQUITY_OUTLIER_THRESHOLD = 0.30
DEFAULT_FX_OUTLIER_THRESHOLD = 0.05
DEFAULT_STALE_WINDOW = 3


def _require_non_empty(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"{name} must be a non-empty string")


def _ensure_utc(dt: datetime, name: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise ValueError(f"{name} must be timezone-aware and in UTC")


def _is_positive_finite(value: float) -> bool:
    return isfinite(value) and value > 0


def _is_non_negative_finite(value: float) -> bool:
    return isfinite(value) and value >= 0


def _is_iso_ccy(value: str) -> bool:
    return len(value) == 3 and value.isalpha() and value.upper() == value


def _merge_flags(
    existing: tuple[QualityFlag, ...],
    additions: Iterable[QualityFlag],
) -> tuple[QualityFlag, ...]:
    merged = list(existing)
    for flag in additions:
        if flag not in merged:
            merged.append(flag)
    return tuple(merged)


def _apply_outlier_and_stale_flags(
    records: Sequence[CanonicalRecord],
    additions: list[set[QualityFlag]],
    *,
    key_fn: Callable[[CanonicalRecord], Hashable],
    value_fn: Callable[[CanonicalRecord], float | None],
    outlier_threshold: float,
    stale_window: int,
) -> None:
    grouped: dict[Hashable, list[tuple[datetime, int, float]]] = {}
    for index, record in enumerate(records):
        value = value_fn(record)
        if value is None or not isfinite(value):
            continue
        key = key_fn(record)
        grouped.setdefault(key, []).append((record.ts, index, value))

    for entries in grouped.values():
        entries.sort(key=lambda item: (item[0], item[1]))
        prev_value: float | None = None
        stale_count = 0
        for _, index, value in entries:
            if prev_value is not None and prev_value > 0:
                change = abs((value - prev_value) / prev_value)
                if change > outlier_threshold:
                    additions[index].add(QualityFlag.OUTLIER_SUSPECT)
            if prev_value is not None and value == prev_value:
                stale_count += 1
            else:
                stale_count = 1
            if stale_count >= stale_window:
                additions[index].add(QualityFlag.STALE)
            prev_value = value


@dataclass(frozen=True)
class ValidationContext:
    dataset_id: str
    dataset_version: str
    ingest_run_id: str

    def __post_init__(self) -> None:
        _require_non_empty(self.dataset_id, "dataset_id")
        _require_non_empty(self.dataset_version, "dataset_version")
        _require_non_empty(self.ingest_run_id, "ingest_run_id")


def validate_records(
    records: Sequence[CanonicalRecord],
    *,
    context: ValidationContext | None = None,
    generated_ts: datetime | None = None,
    equity_outlier_threshold: float = DEFAULT_EQUITY_OUTLIER_THRESHOLD,
    fx_outlier_threshold: float = DEFAULT_FX_OUTLIER_THRESHOLD,
    stale_window: int = DEFAULT_STALE_WINDOW,
    raise_on_hard_error: bool = True,
) -> tuple[tuple[CanonicalRecord, ...], ValidationReport]:
    if stale_window < 2:
        raise ValueError("stale_window must be >= 2")
    if context is None:
        if not records:
            raise ValueError("records must not be empty when context is not provided")
        first = records[0]
        context = ValidationContext(
            dataset_id=first.dataset_id,
            dataset_version=first.dataset_version,
            ingest_run_id=first.ingest_run_id,
        )
    dataset_id = context.dataset_id

    generated_ts = generated_ts or datetime.now(timezone.utc)
    _ensure_utc(generated_ts, "generated_ts")

    hard_errors: list[str] = []
    additions: list[set[QualityFlag]] = [set() for _ in records]

    for index, record in enumerate(records):
        if record.dataset_id != context.dataset_id:
            hard_errors.append(f"record {index} dataset_id mismatch: {record.dataset_id}")
        if record.dataset_version != context.dataset_version:
            hard_errors.append(f"record {index} dataset_version mismatch: {record.dataset_version}")
        if record.ingest_run_id != context.ingest_run_id:
            hard_errors.append(f"record {index} ingest_run_id mismatch: {record.ingest_run_id}")
        if record.ts_provenance != TimestampProvenance.EXCHANGE_CLOSE:
            additions[index].add(QualityFlag.PROVIDER_TIMESTAMP_USED)

        if dataset_id == EQUITY_EOD_DATASET_ID:
            if not isinstance(record, BarRecord):
                hard_errors.append(f"record {index} expected BarRecord for equity dataset")
                continue
            bar = record.bar
            if bar.adj_close is not None or bar.adjustment_basis is not None:
                additions[index].add(QualityFlag.ADJUSTED_PRICE_PRESENT)

            prices = {
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "adj_close": bar.adj_close,
            }
            for field, value in prices.items():
                if value is None:
                    continue
                if not _is_positive_finite(value):
                    hard_errors.append(f"record {index} {field} must be finite and > 0")
            if bar.volume is not None and not _is_non_negative_finite(bar.volume):
                hard_errors.append(f"record {index} volume must be finite and >= 0")

            if bar.high is not None:
                ref_values = [bar.close]
                if bar.open is not None:
                    ref_values.append(bar.open)
                if bar.high < max(ref_values):
                    hard_errors.append(f"record {index} high must be >= max(open, close)")
            if bar.low is not None:
                ref_values = [bar.close]
                if bar.open is not None:
                    ref_values.append(bar.open)
                if bar.low > min(ref_values):
                    hard_errors.append(f"record {index} low must be <= min(open, close)")
            if bar.high is not None and bar.low is not None and bar.high < bar.low:
                hard_errors.append(f"record {index} high must be >= low")

        elif dataset_id == FX_DAILY_DATASET_ID:
            if not isinstance(record, PointRecord):
                hard_errors.append(f"record {index} expected PointRecord for fx dataset")
                continue
            if not _is_positive_finite(record.value):
                hard_errors.append(f"record {index} value must be finite and > 0")
            if not _is_iso_ccy(record.base_ccy):
                hard_errors.append(f"record {index} base_ccy must be ISO 4217")
            if not _is_iso_ccy(record.quote_ccy):
                hard_errors.append(f"record {index} quote_ccy must be ISO 4217")
        else:
            hard_errors.append(f"unsupported dataset_id: {dataset_id}")
            break

    if dataset_id == EQUITY_EOD_DATASET_ID:
        seen_equity: set[tuple[str, datetime]] = set()
        for record in records:
            if not isinstance(record, BarRecord):
                continue
            key_equity = (record.instrument_id, record.ts)
            if key_equity in seen_equity:
                hard_errors.append(
                    f"duplicate record for {record.instrument_id} at {record.ts.isoformat()}"
                )
            else:
                seen_equity.add(key_equity)
    elif dataset_id == FX_DAILY_DATASET_ID:
        seen_fx: set[tuple[str, str, datetime]] = set()
        for record in records:
            if not isinstance(record, PointRecord):
                continue
            field = record.field.strip().lower()
            key_fx = (record.instrument_id, field, record.ts)
            if key_fx in seen_fx:
                hard_errors.append(
                    "duplicate record for "
                    f"{record.instrument_id}/{field} at {record.ts.isoformat()}"
                )
            else:
                seen_fx.add(key_fx)

    if dataset_id == FX_DAILY_DATASET_ID:
        bid_ask: dict[tuple[str, datetime], dict[str, float]] = {}
        for record in records:
            if not isinstance(record, PointRecord):
                continue
            field = record.field.strip().lower()
            if field not in {"bid", "ask"}:
                continue
            bid_ask.setdefault((record.instrument_id, record.ts), {})[field] = record.value
        for (instrument_id, ts), values in bid_ask.items():
            bid = values.get("bid")
            ask = values.get("ask")
            if bid is not None and ask is not None and bid > ask:
                hard_errors.append(f"bid/ask inversion for {instrument_id} at {ts.isoformat()}")

    if dataset_id == EQUITY_EOD_DATASET_ID:
        _apply_outlier_and_stale_flags(
            records,
            additions,
            key_fn=lambda record: record.instrument_id,
            value_fn=lambda record: record.bar.close if isinstance(record, BarRecord) else None,
            outlier_threshold=equity_outlier_threshold,
            stale_window=stale_window,
        )
    elif dataset_id == FX_DAILY_DATASET_ID:
        _apply_outlier_and_stale_flags(
            records,
            additions,
            key_fn=lambda record: (
                record.instrument_id,
                record.field.strip().lower() if isinstance(record, PointRecord) else "",
            ),
            value_fn=lambda record: record.value if isinstance(record, PointRecord) else None,
            outlier_threshold=fx_outlier_threshold,
            stale_window=stale_window,
        )

    validated_records: list[CanonicalRecord] = []
    for index, record in enumerate(records):
        merged = _merge_flags(record.quality_flags, additions[index])
        if merged != record.quality_flags:
            validated_records.append(replace(record, quality_flags=merged))
        else:
            validated_records.append(record)

    flag_counts: dict[QualityFlag, int] = {}
    for record in validated_records:
        for flag in record.quality_flags:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

    report = ValidationReport(
        dataset_id=context.dataset_id,
        dataset_version=context.dataset_version,
        ingest_run_id=context.ingest_run_id,
        generated_ts=generated_ts,
        total_records=len(validated_records),
        hard_errors=tuple(hard_errors),
        flag_counts=flag_counts,
    )

    if hard_errors and raise_on_hard_error:
        raise ValidationError(
            "validation failed",
            context={"report": report.to_payload()},
        )

    return tuple(validated_records), report
