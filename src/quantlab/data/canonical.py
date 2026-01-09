from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd

from quantlab.data.errors import StorageError
from quantlab.data.storage.canonical_parquet import parquet_engine_available


def _require_non_empty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _read_metadata(metadata_path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(
            "failed to read canonical metadata",
            context={"path": str(metadata_path)},
            cause=exc,
        ) from exc
    if not isinstance(payload, Mapping):
        raise StorageError(
            "canonical metadata payload invalid",
            context={"path": str(metadata_path)},
        )
    return payload


def _get_required_str(payload: Mapping[str, object], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise StorageError(
            f"canonical metadata missing {field}",
            context={"field": field},
        )
    return value


def _load_parquet_parts(snapshot_dir: Path) -> pd.DataFrame:
    if not parquet_engine_available():
        raise StorageError(
            "parquet engine not installed",
            context={"engines": ["pyarrow", "fastparquet"]},
        )
    part_paths = sorted(snapshot_dir.glob("part-*.parquet"))
    if not part_paths:
        raise StorageError(
            "canonical snapshot missing parts",
            context={"path": str(snapshot_dir)},
        )
    frames: list[pd.DataFrame] = []
    for part_path in part_paths:
        try:
            frames.append(pd.read_parquet(part_path))
        except (ImportError, ValueError, OSError) as exc:
            raise StorageError(
                "failed to read canonical parquet",
                context={"path": str(part_path)},
                cause=exc,
            ) from exc
    if len(frames) == 1:
        return frames[0]
    return pd.concat(frames, ignore_index=True)


@dataclass(frozen=True)
class CanonicalDataset:
    dataset_id: str
    dataset_version: str
    schema_version: str
    snapshot_path: Path
    metadata: Mapping[str, object]
    frame: pd.DataFrame

    def __post_init__(self) -> None:
        _require_non_empty(self.dataset_id, "dataset_id")
        _require_non_empty(self.dataset_version, "dataset_version")
        _require_non_empty(self.schema_version, "schema_version")

    @classmethod
    def from_snapshot_dir(cls, snapshot_dir: Path) -> CanonicalDataset:
        if not snapshot_dir.exists():
            raise StorageError(
                "canonical snapshot directory missing",
                context={"path": str(snapshot_dir)},
            )
        if not snapshot_dir.is_dir():
            raise StorageError(
                "canonical snapshot path is not a directory",
                context={"path": str(snapshot_dir)},
            )
        metadata_path = snapshot_dir / "_metadata.json"
        if not metadata_path.exists():
            raise StorageError(
                "canonical metadata missing",
                context={"path": str(metadata_path)},
            )
        metadata = _read_metadata(metadata_path)
        dataset_id = _get_required_str(metadata, "dataset_id")
        dataset_version = _get_required_str(metadata, "dataset_version")
        schema_version = _get_required_str(metadata, "schema_version")
        frame = _load_parquet_parts(snapshot_dir)
        return cls(
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            schema_version=schema_version,
            snapshot_path=snapshot_dir,
            metadata=metadata,
            frame=frame,
        )

    def lineage(self) -> dict[str, str]:
        lineage: dict[str, str] = {}
        for key in ("dataset_id", "dataset_version", "ingest_run_id", "schema_version", "asof_ts"):
            value = self.metadata.get(key)
            if isinstance(value, str) and value:
                lineage[key] = value
        return lineage


__all__ = ["CanonicalDataset"]
