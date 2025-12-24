from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from quantlab.data.errors import StorageError
from quantlab.data.storage import build_canonical_paths, compute_content_hash


def _require_non_empty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _ensure_utc(dt: datetime, name: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise ValueError(f"{name} must be timezone-aware and in UTC")


def _normalize_source_set(source_set: Sequence[str]) -> tuple[str, ...]:
    if isinstance(source_set, str):
        raise ValueError("source_set must be a sequence of strings")
    if not source_set:
        raise ValueError("source_set must not be empty")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in source_set:
        if not isinstance(item, str):
            raise ValueError("source_set values must be strings")
        _require_non_empty(item, "source_set")
        if item in seen:
            raise ValueError("source_set must not contain duplicates")
        normalized.append(item)
        seen.add(item)
    return tuple(normalized)


@dataclass(frozen=True)
class DatasetRegistryEntry:
    dataset_id: str
    dataset_version: str
    schema_version: str
    created_at_ts: datetime
    ingest_run_id: str
    universe_hash: str
    calendar_version: str
    sessionrules_version: str
    source_set: tuple[str, ...]
    row_count: int
    content_hash: str
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.dataset_id, "dataset_id")
        _require_non_empty(self.dataset_version, "dataset_version")
        _require_non_empty(self.schema_version, "schema_version")
        _require_non_empty(self.ingest_run_id, "ingest_run_id")
        _require_non_empty(self.universe_hash, "universe_hash")
        _require_non_empty(self.calendar_version, "calendar_version")
        _require_non_empty(self.sessionrules_version, "sessionrules_version")
        _require_non_empty(self.content_hash, "content_hash")
        _ensure_utc(self.created_at_ts, "created_at_ts")
        if isinstance(self.row_count, bool) or not isinstance(self.row_count, int):
            raise ValueError("row_count must be an integer")
        if self.row_count < 0:
            raise ValueError("row_count must be non-negative")
        if self.notes is not None and not isinstance(self.notes, str):
            raise ValueError("notes must be a string when provided")
        if self.notes is not None and not self.notes:
            raise ValueError("notes must be non-empty when provided")

        normalized_sources = _normalize_source_set(self.source_set)
        object.__setattr__(self, "source_set", normalized_sources)

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "schema_version": self.schema_version,
            "created_at_ts": self.created_at_ts.isoformat(),
            "ingest_run_id": self.ingest_run_id,
            "universe_hash": self.universe_hash,
            "calendar_version": self.calendar_version,
            "sessionrules_version": self.sessionrules_version,
            "source_set": list(self.source_set),
            "row_count": self.row_count,
            "content_hash": self.content_hash,
        }
        if self.notes is not None:
            payload["notes"] = self.notes
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> DatasetRegistryEntry:
        def _get_required_str(field: str) -> str:
            value = payload.get(field)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field} must be a non-empty string")
            return value

        created_at_raw = _get_required_str("created_at_ts")
        created_at_ts = datetime.fromisoformat(created_at_raw)
        row_count = payload.get("row_count")
        source_set = payload.get("source_set")
        if not isinstance(row_count, int) or isinstance(row_count, bool):
            raise ValueError("row_count must be an integer")
        if not isinstance(source_set, Sequence) or isinstance(source_set, str):
            raise ValueError("source_set must be a sequence")

        notes = payload.get("notes")
        if notes is not None and not isinstance(notes, str):
            raise ValueError("notes must be a string when provided")

        return cls(
            dataset_id=_get_required_str("dataset_id"),
            dataset_version=_get_required_str("dataset_version"),
            schema_version=_get_required_str("schema_version"),
            created_at_ts=created_at_ts,
            ingest_run_id=_get_required_str("ingest_run_id"),
            universe_hash=_get_required_str("universe_hash"),
            calendar_version=_get_required_str("calendar_version"),
            sessionrules_version=_get_required_str("sessionrules_version"),
            source_set=tuple(source_set),
            row_count=row_count,
            content_hash=_get_required_str("content_hash"),
            notes=notes,
        )


def _load_registry_entries(registry_path: Path) -> list[DatasetRegistryEntry]:
    if not registry_path.exists():
        return []
    if not registry_path.is_file():
        raise StorageError("registry path is not a file", context={"path": str(registry_path)})
    entries: list[DatasetRegistryEntry] = []
    try:
        with registry_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise StorageError(
                        "invalid registry entry",
                        context={"path": str(registry_path), "line": line_number},
                        cause=exc,
                    ) from exc
                try:
                    entry = DatasetRegistryEntry.from_payload(payload)
                except (TypeError, ValueError) as exc:
                    raise StorageError(
                        "invalid registry entry",
                        context={"path": str(registry_path), "line": line_number},
                        cause=exc,
                    ) from exc
                entries.append(entry)
    except OSError as exc:
        raise StorageError(
            "failed to read registry", context={"path": str(registry_path)}, cause=exc
        ) from exc
    return entries


def _read_snapshot_metadata(metadata_path: Path) -> Mapping[str, object]:
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


def _ensure_snapshot_matches_entry(entry: DatasetRegistryEntry, canonical_root: Path) -> None:
    paths = build_canonical_paths(canonical_root, entry.dataset_id, entry.dataset_version)
    if not paths.version_dir.exists():
        raise StorageError(
            "canonical snapshot missing",
            context={
                "dataset_id": entry.dataset_id,
                "dataset_version": entry.dataset_version,
                "path": str(paths.version_dir),
            },
        )
    if not paths.version_dir.is_dir():
        raise StorageError(
            "canonical snapshot path is not a directory",
            context={"path": str(paths.version_dir)},
        )
    if not paths.metadata_path.exists():
        raise StorageError(
            "canonical metadata missing",
            context={"path": str(paths.metadata_path)},
        )
    metadata = _read_snapshot_metadata(paths.metadata_path)
    metadata_dataset_id = metadata.get("dataset_id")
    metadata_dataset_version = metadata.get("dataset_version")
    if metadata_dataset_id != entry.dataset_id:
        raise StorageError(
            "canonical metadata dataset_id mismatch",
            context={
                "expected": entry.dataset_id,
                "actual": metadata_dataset_id,
            },
        )
    if metadata_dataset_version != entry.dataset_version:
        raise StorageError(
            "canonical metadata dataset_version mismatch",
            context={
                "expected": entry.dataset_version,
                "actual": metadata_dataset_version,
            },
        )
    part_paths = list(paths.version_dir.glob("part-*.parquet"))
    if not part_paths:
        raise StorageError(
            "canonical snapshot missing parts",
            context={"path": str(paths.version_dir)},
        )
    content_hash = compute_content_hash(part_paths)
    if content_hash != entry.content_hash:
        raise StorageError(
            "content hash mismatch",
            context={
                "dataset_id": entry.dataset_id,
                "dataset_version": entry.dataset_version,
                "expected": entry.content_hash,
                "actual": content_hash,
            },
        )


def append_registry_entry(
    registry_path: Path,
    entry: DatasetRegistryEntry,
    *,
    canonical_root: Path,
) -> None:
    existing = lookup_registry_entry(registry_path, entry.dataset_id, entry.dataset_version)
    if existing is not None:
        raise StorageError(
            "registry entry already exists",
            context={
                "dataset_id": entry.dataset_id,
                "dataset_version": entry.dataset_version,
            },
        )
    _ensure_snapshot_matches_entry(entry, canonical_root)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with registry_path.open("a", encoding="utf-8") as handle:
            serialized = json.dumps(entry.to_payload(), sort_keys=True, ensure_ascii=True)
            handle.write(serialized)
            handle.write("\n")
    except OSError as exc:
        raise StorageError(
            "failed to append registry entry",
            context={"path": str(registry_path)},
            cause=exc,
        ) from exc


def lookup_registry_entry(
    registry_path: Path, dataset_id: str, dataset_version: str
) -> DatasetRegistryEntry | None:
    _require_non_empty(dataset_id, "dataset_id")
    _require_non_empty(dataset_version, "dataset_version")
    matches: list[DatasetRegistryEntry] = []
    for entry in _load_registry_entries(registry_path):
        if entry.dataset_id == dataset_id and entry.dataset_version == dataset_version:
            matches.append(entry)
    if len(matches) > 1:
        raise StorageError(
            "registry contains duplicate entries",
            context={"dataset_id": dataset_id, "dataset_version": dataset_version},
        )
    return matches[0] if matches else None
