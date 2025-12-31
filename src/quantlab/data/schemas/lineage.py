from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LineageMeta:
    """Lineage metadata for market data requests and cache manifests."""

    request_hash: str
    request_json: dict[str, Any]
    provider: str
    ingestion_ts_utc: str
    as_of_utc: str | None
    dataset_version: str
    code_version: str | None = None
    storage_paths: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.request_hash:
            raise ValueError("request_hash must be non-empty")
        if not self.provider:
            raise ValueError("provider must be non-empty")
        if not self.ingestion_ts_utc:
            raise ValueError("ingestion_ts_utc must be non-empty")
        if not self.dataset_version:
            raise ValueError("dataset_version must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_hash": self.request_hash,
            "request_json": self.request_json,
            "provider": self.provider,
            "ingestion_ts_utc": self.ingestion_ts_utc,
            "as_of_utc": self.as_of_utc,
            "dataset_version": self.dataset_version,
            "code_version": self.code_version,
            "storage_paths": list(self.storage_paths),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> LineageMeta:
        return cls(
            request_hash=str(payload["request_hash"]),
            request_json=dict(payload["request_json"]),
            provider=str(payload["provider"]),
            ingestion_ts_utc=str(payload["ingestion_ts_utc"]),
            as_of_utc=payload.get("as_of_utc"),
            dataset_version=str(payload["dataset_version"]),
            code_version=payload.get("code_version"),
            storage_paths=list(payload.get("storage_paths") or []),
        )

    @classmethod
    def from_json(cls, payload: str) -> LineageMeta:
        return cls.from_dict(json.loads(payload))
