from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from io import StringIO
from typing import Mapping, Sequence

from quantlab.data.errors import NormalizationError
from quantlab.data.quality import QualityFlag
from quantlab.data.schemas import Bar, BarRecord, PointRecord, Source, TimestampProvenance
from quantlab.data.schemas.records import AdjustmentBasis
from quantlab.instruments.master import InstrumentMasterRecord, InstrumentType, normalize_ccy

EQUITY_EOD_DATASET_ID = "md.equity.eod.bars"
FX_DAILY_DATASET_ID = "md.fx.spot.daily"
SCHEMA_VERSION = "1.0.0"


def _require_non_empty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _ensure_utc(dt: datetime, name: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise ValueError(f"{name} must be timezone-aware and in UTC")


def _normalize_mic(value: str) -> str:
    _require_non_empty(value, "mic")
    return value.strip().upper()


def _normalize_vendor_symbol(value: str) -> str:
    _require_non_empty(value, "vendor_symbol")
    return value.strip().upper()


def _parse_payload(payload: bytes | str | Mapping[str, object]) -> Mapping[str, object]:
    if isinstance(payload, Mapping):
        return payload
    try:
        raw = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    except UnicodeDecodeError as exc:
        raise NormalizationError("payload must be utf-8", cause=exc) from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return _parse_csv_payload(raw)
    if not isinstance(parsed, Mapping):
        raise NormalizationError("payload must decode to a JSON object")
    return parsed


def _parse_csv_payload(raw: str) -> Mapping[str, object]:
    try:
        reader = csv.DictReader(StringIO(raw), skipinitialspace=True)
    except csv.Error as exc:
        raise NormalizationError("payload must be valid CSV", cause=exc) from exc
    if reader.fieldnames is None:
        raise NormalizationError("payload missing CSV header")
    records: list[dict[str, object]] = []
    for row in reader:
        if row is None:
            continue
        cleaned = {key: value for key, value in row.items() if key is not None}
        if all(value in ("", None) for value in cleaned.values()):
            continue
        records.append(cleaned)
    return {"records": records}


def _get_records(payload: Mapping[str, object]) -> Sequence[object]:
    records = payload.get("records", payload.get("data"))
    if records is None:
        raise NormalizationError("payload missing records")
    if not isinstance(records, Sequence) or isinstance(records, str):
        raise NormalizationError("records must be a sequence")
    return records


def _get_required_str(entry: Mapping[str, object], field: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value:
        raise NormalizationError(f"{field} must be a non-empty string")
    return value


def _get_optional_str(entry: Mapping[str, object], field: str) -> str | None:
    value = entry.get(field)
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not value:
        raise NormalizationError(f"{field} must be a non-empty string when provided")
    return value


def _get_required_float(entry: Mapping[str, object], field: str) -> float:
    value = entry.get(field)
    if value is None:
        raise NormalizationError(f"{field} is required")
    return _parse_float(value, field)


def _get_optional_float(entry: Mapping[str, object], field: str) -> float | None:
    value = entry.get(field)
    if value is None or value == "":
        return None
    return _parse_float(value, field)


def _parse_float(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise NormalizationError(f"{field} must be numeric")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        if not value:
            raise NormalizationError(f"{field} must be numeric")
        try:
            return float(value)
        except ValueError as exc:
            raise NormalizationError(f"{field} must be numeric", cause=exc) from exc
    raise NormalizationError(f"{field} must be numeric")


def _parse_datetime(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise NormalizationError(f"{field} must be a non-empty string")
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise NormalizationError(f"{field} must be ISO-8601 datetime", cause=exc) from exc
    if parsed.tzinfo is None:
        raise NormalizationError(f"{field} must include timezone offset")
    return parsed.astimezone(timezone.utc)


def _parse_optional_date(value: object, field: str) -> date | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not value:
        raise NormalizationError(f"{field} must be a non-empty string when provided")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise NormalizationError(f"{field} must be YYYY-MM-DD", cause=exc) from exc


def _parse_adjustment_basis(value: object) -> AdjustmentBasis | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise NormalizationError("adjustment_basis must be a non-empty string when provided")
    try:
        return AdjustmentBasis(value)
    except ValueError as exc:
        raise NormalizationError("adjustment_basis is invalid", cause=exc) from exc


@dataclass(frozen=True)
class NormalizationContext:
    dataset_id: str
    dataset_version: str
    schema_version: str
    asof_ts: datetime
    ingest_run_id: str
    source: Source

    def __post_init__(self) -> None:
        _require_non_empty(self.dataset_id, "dataset_id")
        _require_non_empty(self.dataset_version, "dataset_version")
        _require_non_empty(self.schema_version, "schema_version")
        _require_non_empty(self.ingest_run_id, "ingest_run_id")
        _ensure_utc(self.asof_ts, "asof_ts")


def normalize_equity_eod(
    payload: bytes | str | Mapping[str, object],
    *,
    context: NormalizationContext,
    instrument_lookup: Mapping[tuple[str, str], InstrumentMasterRecord],
) -> tuple[BarRecord, ...]:
    if context.dataset_id != EQUITY_EOD_DATASET_ID:
        raise NormalizationError(
            "dataset_id mismatch for equity normalizer",
            context={"dataset_id": context.dataset_id},
        )
    parsed = _parse_payload(payload)
    records = _get_records(parsed)
    normalized: list[BarRecord] = []
    for index, entry in enumerate(records):
        if not isinstance(entry, Mapping):
            raise NormalizationError(
                "equity record must be a mapping",
                context={"index": index},
            )
        mic = _normalize_mic(_get_required_str(entry, "mic"))
        vendor_symbol = _normalize_vendor_symbol(_get_required_str(entry, "vendor_symbol"))
        instrument = instrument_lookup.get((mic, vendor_symbol))
        if instrument is None:
            raise NormalizationError(
                "equity instrument not found",
                context={"mic": mic, "vendor_symbol": vendor_symbol},
            )
        if instrument.instrument_type != InstrumentType.EQUITY:
            raise NormalizationError(
                "instrument is not equity",
                context={"instrument_id": instrument.instrument_id},
            )
        ts = _parse_datetime(entry.get("ts"), "ts")
        trading_date = _parse_optional_date(
            entry.get("trading_date") or entry.get("trading_date_local"),
            "trading_date",
        )
        timezone_local = instrument.exchange_timezone or _get_optional_str(entry, "timezone_local")
        currency = instrument.currency or _get_optional_str(entry, "currency")
        bar = Bar(
            open=_get_optional_float(entry, "open"),
            high=_get_optional_float(entry, "high"),
            low=_get_optional_float(entry, "low"),
            close=_get_required_float(entry, "close"),
            volume=_get_optional_float(entry, "volume"),
            adj_close=_get_optional_float(entry, "adj_close"),
            adjustment_basis=_parse_adjustment_basis(entry.get("adjustment_basis")),
            adjustment_note=_get_optional_str(entry, "adjustment_note"),
        )
        flags: list[QualityFlag] = []
        if bar.adj_close is not None or bar.adjustment_basis is not None:
            flags.append(QualityFlag.ADJUSTED_PRICE_PRESENT)
        normalized.append(
            BarRecord(
                dataset_id=context.dataset_id,
                schema_version=context.schema_version,
                dataset_version=context.dataset_version,
                instrument_id=instrument.instrument_id,
                ts=ts,
                asof_ts=context.asof_ts,
                ts_provenance=TimestampProvenance.PROVIDER_EOD,
                source=context.source,
                ingest_run_id=context.ingest_run_id,
                quality_flags=tuple(flags),
                trading_date_local=trading_date,
                timezone_local=timezone_local,
                currency=currency,
                unit=None,
                bar=bar,
            )
        )
    return tuple(normalized)


def normalize_fx_daily(
    payload: bytes | str | Mapping[str, object],
    *,
    context: NormalizationContext,
    instrument_lookup: Mapping[tuple[str, str], InstrumentMasterRecord],
) -> tuple[PointRecord, ...]:
    if context.dataset_id != FX_DAILY_DATASET_ID:
        raise NormalizationError(
            "dataset_id mismatch for fx normalizer",
            context={"dataset_id": context.dataset_id},
        )
    parsed = _parse_payload(payload)
    records = _get_records(parsed)
    normalized: list[PointRecord] = []
    for index, entry in enumerate(records):
        if not isinstance(entry, Mapping):
            raise NormalizationError(
                "fx record must be a mapping",
                context={"index": index},
            )
        base_ccy = normalize_ccy(_get_required_str(entry, "base_ccy"))
        quote_ccy = normalize_ccy(_get_required_str(entry, "quote_ccy"))
        instrument = instrument_lookup.get((base_ccy, quote_ccy))
        if instrument is None:
            raise NormalizationError(
                "fx instrument not found",
                context={"base_ccy": base_ccy, "quote_ccy": quote_ccy},
            )
        if instrument.instrument_type != InstrumentType.FX_SPOT:
            raise NormalizationError(
                "instrument is not fx spot",
                context={"instrument_id": instrument.instrument_id},
            )
        ts = _parse_datetime(entry.get("ts"), "ts")
        trading_date = _parse_optional_date(
            entry.get("fixing_date")
            or entry.get("trading_date")
            or entry.get("trading_date_local"),
            "fixing_date",
        )
        normalized.append(
            PointRecord(
                dataset_id=context.dataset_id,
                schema_version=context.schema_version,
                dataset_version=context.dataset_version,
                instrument_id=instrument.instrument_id,
                ts=ts,
                asof_ts=context.asof_ts,
                ts_provenance=TimestampProvenance.PROVIDER_EOD,
                source=context.source,
                ingest_run_id=context.ingest_run_id,
                quality_flags=tuple(),
                trading_date_local=trading_date,
                timezone_local=_get_optional_str(entry, "timezone_local"),
                currency=None,
                unit=None,
                field=_get_required_str(entry, "field").strip(),
                value=_get_required_float(entry, "value"),
                base_ccy=base_ccy,
                quote_ccy=quote_ccy,
                fixing_convention=_get_optional_str(entry, "fixing_convention"),
            )
        )
    return tuple(normalized)
