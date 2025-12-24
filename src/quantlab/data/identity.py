from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


def _ensure_utc(dt: datetime, name: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise ValueError(f"{name} must be timezone-aware and in UTC")


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _normalize_value(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_value(val) for val in value]
    if isinstance(value, (set, frozenset)):
        normalized_items = [_normalize_value(val) for val in value]
        return sorted(
            normalized_items,
            key=lambda item: json.dumps(
                item, sort_keys=True, separators=(",", ":"), ensure_ascii=True
            ),
        )
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _normalize_value(asdict(value))
    return value


def request_fingerprint(payload: Mapping[str, Any]) -> str:
    """Return a deterministic hash for a provider request payload."""

    normalized_payload = _normalize_value(payload)
    encoded = json.dumps(
        normalized_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def generate_ingest_run_id(
    started_at: datetime | None = None, *, sequence: int = 1
) -> str:
    """Generate a deterministic ingestion run identifier."""

    if sequence < 1:
        raise ValueError("sequence must be >= 1")
    timestamp = started_at or datetime.now(timezone.utc)
    _ensure_utc(timestamp, "started_at")
    return f"ing_{timestamp:%Y%m%d_%H%M%S}Z_{sequence:04d}"
