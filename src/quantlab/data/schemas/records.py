from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Tuple


def _require_non_empty(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"{name} must be a non-empty string")


def _ensure_utc(dt: datetime, name: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise ValueError(f"{name} must be timezone-aware and in UTC")


@dataclass(frozen=True)
class Source:
    provider: str
    endpoint: str
    provider_dataset: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.provider, "provider")
        _require_non_empty(self.endpoint, "endpoint")
        if self.provider_dataset is not None:
            _require_non_empty(self.provider_dataset, "provider_dataset")


@dataclass(frozen=True)
class CanonicalRecord:
    dataset_id: str
    schema_version: str
    dataset_version: str
    instrument_id: str
    ts: datetime
    asof_ts: datetime
    source: Source
    ingest_run_id: str
    quality_flags: Tuple[str, ...]
    trading_date_local: date | None
    timezone_local: str | None
    currency: str | None
    unit: str | None

    def __post_init__(self) -> None:
        _require_non_empty(self.dataset_id, "dataset_id")
        _require_non_empty(self.schema_version, "schema_version")
        _require_non_empty(self.dataset_version, "dataset_version")
        _require_non_empty(self.instrument_id, "instrument_id")
        _require_non_empty(self.ingest_run_id, "ingest_run_id")
        _ensure_utc(self.ts, "ts")
        _ensure_utc(self.asof_ts, "asof_ts")
        if self.quality_flags is None:
            raise ValueError("quality_flags must not be None")
        object.__setattr__(self, "quality_flags", tuple(self.quality_flags))

    def metadata_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "dataset_id": self.dataset_id,
            "schema_version": self.schema_version,
            "dataset_version": self.dataset_version,
            "instrument_id": self.instrument_id,
            "ts": self.ts.isoformat(),
            "asof_ts": self.asof_ts.isoformat(),
            "source": {
                "provider": self.source.provider,
                "endpoint": self.source.endpoint,
            },
            "ingest_run_id": self.ingest_run_id,
            "quality_flags": list(self.quality_flags),
        }
        if self.source.provider_dataset is not None:
            payload["source"]["provider_dataset"] = self.source.provider_dataset
        if self.trading_date_local is not None:
            payload["trading_date_local"] = self.trading_date_local.isoformat()
        if self.timezone_local is not None:
            payload["timezone_local"] = self.timezone_local
        if self.currency is not None:
            payload["currency"] = self.currency
        if self.unit is not None:
            payload["unit"] = self.unit
        return payload


class AdjustmentBasis(str, Enum):
    SPLIT_ONLY = "SPLIT_ONLY"
    SPLIT_AND_DIVIDEND = "SPLIT_AND_DIVIDEND"
    PROVIDER_DEFINED = "PROVIDER_DEFINED"


@dataclass(frozen=True)
class Bar:
    close: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: float | None = None
    adj_close: float | None = None
    adjustment_basis: AdjustmentBasis | None = None
    adjustment_note: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(str(self.close), "close")
        if self.adjustment_note is not None and not self.adjustment_note:
            raise ValueError("adjustment_note must be non-empty when provided")


@dataclass(frozen=True)
class BarRecord(CanonicalRecord):
    bar: Bar

    def to_payload(self) -> dict[str, Any]:
        return {
            **self.metadata_payload(),
            "bar": self.bar.__dict__,
        }


@dataclass(frozen=True)
class PointRecord(CanonicalRecord):
    field: str
    value: float
    base_ccy: str
    quote_ccy: str
    fixing_convention: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_non_empty(self.field, "field")
        _require_non_empty(self.base_ccy, "base_ccy")
        _require_non_empty(self.quote_ccy, "quote_ccy")
        if self.fixing_convention is not None:
            _require_non_empty(self.fixing_convention, "fixing_convention")

    def to_payload(self) -> dict[str, Any]:
        payload = self.metadata_payload()
        payload.update(
            {
                "field": self.field,
                "value": self.value,
                "base_ccy": self.base_ccy,
                "quote_ccy": self.quote_ccy,
            }
        )
        if self.fixing_convention is not None:
            payload["fixing_convention"] = self.fixing_convention
        return payload
