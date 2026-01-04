from __future__ import annotations

import json
from pathlib import Path

from quantlab.data.errors import StorageError
from quantlab.data.schemas.ingest_run import IngestRunMeta


def ingest_run_dir(raw_root: Path, ingest_run_id: str) -> Path:
    if not ingest_run_id:
        raise ValueError("ingest_run_id must be non-empty")
    return raw_root / f"ingest_run_id={ingest_run_id}"


def ingest_run_metadata_path(raw_root: Path, ingest_run_id: str) -> Path:
    return ingest_run_dir(raw_root, ingest_run_id) / "ingest_run.json"


def write_ingest_run_meta(raw_root: Path, meta: IngestRunMeta) -> Path:
    target_path = ingest_run_metadata_path(raw_root, meta.ingest_run_id)
    if target_path.exists():
        raise StorageError(
            "ingest run metadata already exists",
            context={"path": str(target_path), "ingest_run_id": meta.ingest_run_id},
        )
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            meta.to_payload(), sort_keys=True, ensure_ascii=True, separators=(",", ":")
        )
        target_path.write_text(payload, encoding="utf-8")
    except (OSError, TypeError, ValueError) as exc:
        raise StorageError(
            "failed to write ingest run metadata",
            context={"path": str(target_path), "ingest_run_id": meta.ingest_run_id},
            cause=exc,
        ) from exc
    return target_path


def read_ingest_run_meta(raw_root: Path, ingest_run_id: str) -> IngestRunMeta:
    target_path = ingest_run_metadata_path(raw_root, ingest_run_id)
    if not target_path.exists():
        raise StorageError(
            "ingest run metadata missing",
            context={"path": str(target_path), "ingest_run_id": ingest_run_id},
        )
    try:
        payload = json.loads(target_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(
            "failed to read ingest run metadata",
            context={"path": str(target_path), "ingest_run_id": ingest_run_id},
            cause=exc,
        ) from exc
    if not isinstance(payload, dict):
        raise StorageError(
            "ingest run metadata payload invalid",
            context={"path": str(target_path), "ingest_run_id": ingest_run_id},
        )
    try:
        return IngestRunMeta.from_payload(payload)
    except ValueError as exc:
        raise StorageError(
            "ingest run metadata invalid",
            context={"path": str(target_path), "ingest_run_id": ingest_run_id},
            cause=exc,
        ) from exc


__all__ = [
    "ingest_run_dir",
    "ingest_run_metadata_path",
    "write_ingest_run_meta",
    "read_ingest_run_meta",
]
