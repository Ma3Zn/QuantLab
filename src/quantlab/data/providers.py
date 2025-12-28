from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol

from quantlab.data.errors import ProviderRequestError, ProviderResponseError
from quantlab.data.identity import request_fingerprint
from quantlab.data.schemas import Source


def _ensure_utc(dt: datetime, name: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise ValueError(f"{name} must be timezone-aware and in UTC")


def _require_non_empty(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True)
class TimeRange:
    start: datetime
    end: datetime
    inclusive_start: bool = True
    inclusive_end: bool = True

    def __post_init__(self) -> None:
        _ensure_utc(self.start, "start")
        _ensure_utc(self.end, "end")
        if self.start > self.end:
            raise ValueError("time range start must be <= end")

    def to_payload(self) -> dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "inclusive_start": self.inclusive_start,
            "inclusive_end": self.inclusive_end,
        }


@dataclass(frozen=True)
class FetchRequest:
    dataset_id: str
    time_range: TimeRange
    instrument_ids: tuple[str, ...] | None = None
    selector: Mapping[str, Any] | None = None
    fields: tuple[str, ...] = ()
    granularity: str = "EOD"
    vendor_overrides: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.dataset_id:
            raise ProviderRequestError("dataset_id must be a non-empty string")
        if not self.granularity:
            raise ProviderRequestError("granularity must be a non-empty string")
        if self.instrument_ids is not None:
            if not self.instrument_ids:
                raise ProviderRequestError("instrument_ids must not be empty")
            object.__setattr__(self, "instrument_ids", tuple(self.instrument_ids))
        if self.selector is not None and not self.selector:
            raise ProviderRequestError("selector must not be empty")
        object.__setattr__(self, "fields", tuple(self.fields))
        if self.vendor_overrides is not None and not self.vendor_overrides:
            raise ProviderRequestError("vendor_overrides must not be empty")
        if self.instrument_ids is None and self.selector is None:
            raise ProviderRequestError("instrument_ids or selector is required")

    def request_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "dataset_id": self.dataset_id,
            "time_range": self.time_range.to_payload(),
            "granularity": self.granularity,
        }
        if self.instrument_ids is not None:
            payload["instrument_ids"] = list(self.instrument_ids)
        if self.selector is not None:
            payload["selector"] = dict(self.selector)
        if self.fields:
            payload["fields"] = list(self.fields)
        if self.vendor_overrides is not None:
            payload["vendor_overrides"] = dict(self.vendor_overrides)
        return payload

    def fingerprint(self) -> str:
        return request_fingerprint(self.request_payload())


@dataclass(frozen=True)
class RawResponse:
    payload: bytes
    payload_format: str
    source: Source
    fetched_at_ts: datetime
    request_fingerprint: str
    status_code: int | None = None
    retries: int = 0
    pagination: Mapping[str, Any] | None = None
    provider_revision: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.payload_format, "payload_format")
        _require_non_empty(self.request_fingerprint, "request_fingerprint")
        _ensure_utc(self.fetched_at_ts, "fetched_at_ts")
        if self.retries < 0:
            raise ValueError("retries must be >= 0")
        if self.pagination is not None and not self.pagination:
            raise ValueError("pagination must not be empty when provided")
        if self.provider_revision is not None and not self.provider_revision:
            raise ValueError("provider_revision must be non-empty when provided")


class ProviderAdapter(Protocol):
    def fetch(self, request: FetchRequest) -> RawResponse:
        """Fetch raw payloads from a provider-specific source."""


@dataclass(frozen=True)
class LocalFileProviderAdapter:
    provider: str
    endpoint: str
    payload_path: Path
    payload_format: str = "json"
    provider_dataset: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.provider, "provider")
        _require_non_empty(self.endpoint, "endpoint")
        _require_non_empty(self.payload_format, "payload_format")
        if self.provider_dataset is not None and not self.provider_dataset:
            raise ValueError("provider_dataset must be non-empty when provided")

    def fetch(self, request: FetchRequest) -> RawResponse:
        if not self.payload_path.exists():
            raise ProviderResponseError(
                "payload file missing",
                context={"path": str(self.payload_path), "provider": self.provider},
            )
        try:
            payload = self.payload_path.read_bytes()
        except OSError as exc:
            raise ProviderResponseError(
                "failed to read payload file",
                context={"path": str(self.payload_path), "provider": self.provider},
                cause=exc,
            ) from exc
        return RawResponse(
            payload=payload,
            payload_format=self.payload_format,
            source=Source(
                provider=self.provider,
                endpoint=self.endpoint,
                provider_dataset=self.provider_dataset,
            ),
            fetched_at_ts=datetime.now(timezone.utc),
            request_fingerprint=request.fingerprint(),
        )
