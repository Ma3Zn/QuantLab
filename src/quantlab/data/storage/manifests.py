from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from quantlab.data.schemas.errors import StorageError
from quantlab.data.schemas.lineage import LineageMeta
from quantlab.data.schemas.quality import QualityReport
from quantlab.data.storage.layout import manifest_path


def write_manifest(
    root_path: Path,
    request_hash: str,
    lineage: LineageMeta,
    quality: QualityReport,
    paths: Iterable[Path],
) -> Path:
    """Write a manifest JSON file for a cached request."""

    if request_hash != lineage.request_hash:
        raise StorageError(
            "request_hash does not match lineage",
            context={"request_hash": request_hash, "lineage_hash": lineage.request_hash},
        )

    storage_paths = _normalize_paths(paths)
    if lineage.storage_paths and list(lineage.storage_paths) != storage_paths:
        raise StorageError(
            "storage_paths do not match lineage",
            context={"request_hash": request_hash},
        )

    payload = _build_manifest_payload(lineage, quality, storage_paths)
    target_path = manifest_path(root_path, request_hash)
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")),
            encoding="utf-8",
        )
    except OSError as exc:
        raise StorageError(
            "failed to write manifest",
            context={"path": str(target_path), "request_hash": request_hash},
            cause=exc,
        ) from exc
    return target_path


def read_manifest(root_path: Path, request_hash: str) -> dict[str, object]:
    """Read a manifest JSON file for a cached request."""

    target_path = manifest_path(root_path, request_hash)
    if not target_path.exists():
        raise StorageError(
            "manifest missing",
            context={"path": str(target_path), "request_hash": request_hash},
        )
    try:
        payload = json.loads(target_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(
            "failed to read manifest",
            context={"path": str(target_path), "request_hash": request_hash},
            cause=exc,
        ) from exc
    return payload


def _normalize_paths(paths: Iterable[Path]) -> list[str]:
    normalized: list[str] = []
    for path in paths:
        normalized.append(Path(path).as_posix())
    return sorted(normalized)


def _build_manifest_payload(
    lineage: LineageMeta, quality: QualityReport, storage_paths: list[str]
) -> dict[str, object]:
    return {
        "request_hash": lineage.request_hash,
        "request_json": lineage.request_json,
        "provider": lineage.provider,
        "ingestion_ts_utc": lineage.ingestion_ts_utc,
        "as_of_utc": lineage.as_of_utc,
        "dataset_version": lineage.dataset_version,
        "code_version": lineage.code_version,
        "storage_paths": storage_paths,
        "quality": quality.to_dict(),
    }
