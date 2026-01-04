from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


def _require_non_empty(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"{name} must be a non-empty string")


def _ensure_utc(dt: datetime, name: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise ValueError(f"{name} must be timezone-aware and in UTC")


@dataclass(frozen=True)
class IngestRunMeta:
    ingest_run_id: str
    started_at_ts: datetime
    finished_at_ts: datetime
    config_fingerprint: str
    environment_fingerprint: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.ingest_run_id, "ingest_run_id")
        _require_non_empty(self.config_fingerprint, "config_fingerprint")
        _ensure_utc(self.started_at_ts, "started_at_ts")
        _ensure_utc(self.finished_at_ts, "finished_at_ts")
        if self.finished_at_ts < self.started_at_ts:
            raise ValueError("finished_at_ts must be on or after started_at_ts")
        if self.environment_fingerprint is not None:
            _require_non_empty(self.environment_fingerprint, "environment_fingerprint")

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "ingest_run_id": self.ingest_run_id,
            "started_at_ts": self.started_at_ts.isoformat(),
            "finished_at_ts": self.finished_at_ts.isoformat(),
            "config_fingerprint": self.config_fingerprint,
        }
        if self.environment_fingerprint is not None:
            payload["environment_fingerprint"] = self.environment_fingerprint
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_payload(), sort_keys=True)

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> IngestRunMeta:
        def _get_required_str(field: str) -> str:
            value = payload.get(field)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field} must be a non-empty string")
            return value

        started_at = datetime.fromisoformat(_get_required_str("started_at_ts"))
        finished_at = datetime.fromisoformat(_get_required_str("finished_at_ts"))
        environment = payload.get("environment_fingerprint")
        if environment is not None and (not isinstance(environment, str) or not environment):
            raise ValueError("environment_fingerprint must be a non-empty string when provided")

        return cls(
            ingest_run_id=_get_required_str("ingest_run_id"),
            started_at_ts=started_at,
            finished_at_ts=finished_at,
            config_fingerprint=_get_required_str("config_fingerprint"),
            environment_fingerprint=environment,
        )

    @classmethod
    def from_json(cls, payload: str) -> IngestRunMeta:
        return cls.from_payload(json.loads(payload))


__all__ = ["IngestRunMeta"]
