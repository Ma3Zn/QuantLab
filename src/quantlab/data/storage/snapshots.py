from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from quantlab.data.errors import StorageError


def _require_non_empty(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"{name} must be a non-empty string")


def _normalize_extension(ext: str) -> str:
    normalized = ext[1:] if ext.startswith(".") else ext
    _require_non_empty(normalized, "ext")
    return normalized


def _normalize_parts(
    parts: Mapping[str, bytes] | Sequence[tuple[str, bytes]],
) -> list[tuple[str, bytes]]:
    if isinstance(parts, Mapping):
        normalized = list(parts.items())
    else:
        normalized = list(parts)
    if not normalized:
        raise ValueError("parts must not be empty")
    return normalized


@dataclass(frozen=True)
class RawPaths:
    base_dir: Path
    payload_path: Path
    metadata_path: Path


@dataclass(frozen=True)
class CanonicalPaths:
    dataset_dir: Path
    version_dir: Path
    metadata_path: Path


@dataclass(frozen=True)
class StagedSnapshot:
    dataset_id: str
    dataset_version: str
    staging_dir: Path
    final_dir: Path
    part_paths: tuple[Path, ...]
    metadata_path: Path
    content_hash: str


@dataclass(frozen=True)
class PublishedSnapshot:
    dataset_id: str
    dataset_version: str
    version_dir: Path
    part_paths: tuple[Path, ...]
    metadata_path: Path
    content_hash: str


def build_raw_paths(
    raw_root: Path,
    ingest_run_id: str,
    request_fingerprint: str,
    *,
    ext: str = "json",
) -> RawPaths:
    _require_non_empty(ingest_run_id, "ingest_run_id")
    _require_non_empty(request_fingerprint, "request_fingerprint")
    extension = _normalize_extension(ext)
    base_dir = raw_root / f"ingest_run_id={ingest_run_id}" / f"request={request_fingerprint}"
    payload_path = base_dir / f"payload.{extension}"
    metadata_path = base_dir / "metadata.json"
    return RawPaths(base_dir=base_dir, payload_path=payload_path, metadata_path=metadata_path)


def store_raw_payload(
    raw_root: Path,
    ingest_run_id: str,
    request_fingerprint: str,
    payload: bytes,
    metadata: Mapping[str, object],
    *,
    ext: str = "json",
) -> RawPaths:
    paths = build_raw_paths(raw_root, ingest_run_id, request_fingerprint, ext=ext)
    if paths.base_dir.exists():
        raise StorageError(
            "raw payload already exists",
            context={
                "ingest_run_id": ingest_run_id,
                "request_fingerprint": request_fingerprint,
            },
        )
    try:
        paths.base_dir.mkdir(parents=True, exist_ok=False)
        paths.payload_path.write_bytes(payload)
        metadata_payload = json.dumps(dict(metadata), sort_keys=True, ensure_ascii=True)
        paths.metadata_path.write_text(metadata_payload, encoding="utf-8")
    except (OSError, TypeError, ValueError) as exc:
        raise StorageError(
            "failed to store raw payload",
            context={
                "ingest_run_id": ingest_run_id,
                "request_fingerprint": request_fingerprint,
            },
            cause=exc,
        ) from exc
    return paths


def build_canonical_paths(
    canonical_root: Path,
    dataset_id: str,
    dataset_version: str,
) -> CanonicalPaths:
    _require_non_empty(dataset_id, "dataset_id")
    _require_non_empty(dataset_version, "dataset_version")
    dataset_dir = canonical_root / f"dataset_id={dataset_id}"
    version_dir = dataset_dir / f"dataset_version={dataset_version}"
    metadata_path = version_dir / "_metadata.json"
    return CanonicalPaths(
        dataset_dir=dataset_dir,
        version_dir=version_dir,
        metadata_path=metadata_path,
    )


def compute_content_hash(paths: Sequence[Path]) -> str:
    if not paths:
        raise ValueError("paths must not be empty")
    hasher = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.name):
        if not path.exists():
            raise StorageError("content hash path missing", context={"path": str(path)})
        hasher.update(path.name.encode("utf-8"))
        hasher.update(b"\0")
        try:
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(8192), b""):
                    hasher.update(chunk)
        except OSError as exc:
            raise StorageError(
                "failed to read content for hash",
                context={"path": str(path)},
                cause=exc,
            ) from exc
    return hasher.hexdigest()


def stage_canonical_snapshot(
    canonical_root: Path,
    dataset_id: str,
    dataset_version: str,
    parts: Mapping[str, bytes] | Sequence[tuple[str, bytes]],
    metadata: Mapping[str, object],
) -> StagedSnapshot:
    paths = build_canonical_paths(canonical_root, dataset_id, dataset_version)
    if paths.version_dir.exists():
        raise StorageError(
            "canonical snapshot already exists",
            context={"dataset_id": dataset_id, "dataset_version": dataset_version},
        )
    paths.dataset_dir.mkdir(parents=True, exist_ok=True)
    staging_dir = paths.dataset_dir / f".staging-{dataset_version}-{uuid.uuid4().hex}"
    try:
        staging_dir.mkdir()
        part_paths: list[Path] = []
        for name, data in _normalize_parts(parts):
            _require_non_empty(name, "part_name")
            part_path = staging_dir / name
            if part_path.exists():
                raise StorageError(
                    "duplicate part file",
                    context={
                        "dataset_id": dataset_id,
                        "dataset_version": dataset_version,
                        "part": name,
                    },
                )
            part_path.write_bytes(data)
            part_paths.append(part_path)
        metadata_path = staging_dir / "_metadata.json"
        metadata_payload = json.dumps(dict(metadata), sort_keys=True, ensure_ascii=True)
        metadata_path.write_text(metadata_payload, encoding="utf-8")
    except StorageError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise StorageError(
            "failed to stage canonical snapshot",
            context={"dataset_id": dataset_id, "dataset_version": dataset_version},
            cause=exc,
        ) from exc
    content_hash = compute_content_hash(part_paths)
    return StagedSnapshot(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        staging_dir=staging_dir,
        final_dir=paths.version_dir,
        part_paths=tuple(part_paths),
        metadata_path=metadata_path,
        content_hash=content_hash,
    )


def publish_canonical_snapshot(
    staged: StagedSnapshot,
) -> PublishedSnapshot:
    if not staged.staging_dir.exists():
        raise StorageError(
            "staging directory missing",
            context={
                "dataset_id": staged.dataset_id,
                "dataset_version": staged.dataset_version,
                "staging_dir": str(staged.staging_dir),
            },
        )
    if staged.final_dir.exists():
        raise StorageError(
            "canonical snapshot already exists",
            context={
                "dataset_id": staged.dataset_id,
                "dataset_version": staged.dataset_version,
            },
        )
    try:
        staged.staging_dir.rename(staged.final_dir)
    except OSError as exc:
        raise StorageError(
            "failed to publish canonical snapshot",
            context={
                "dataset_id": staged.dataset_id,
                "dataset_version": staged.dataset_version,
            },
            cause=exc,
        ) from exc
    part_paths = tuple(staged.final_dir / path.name for path in staged.part_paths)
    metadata_path = staged.final_dir / "_metadata.json"
    return PublishedSnapshot(
        dataset_id=staged.dataset_id,
        dataset_version=staged.dataset_version,
        version_dir=staged.final_dir,
        part_paths=part_paths,
        metadata_path=metadata_path,
        content_hash=staged.content_hash,
    )
