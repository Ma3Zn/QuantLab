from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from quantlab.data.errors import StorageError
from quantlab.data.registry import (
    DatasetRegistryEntry,
    append_registry_entry,
    lookup_registry_entry,
)
from quantlab.data.storage import publish_canonical_snapshot, stage_canonical_snapshot


def _publish_snapshot(tmp_path: Path) -> tuple[Path, str, str, str]:
    dataset_id = "md.equity.eod.bars"
    dataset_version = "2024-12-24.1"
    parts = {"part-0001.parquet": b"alpha"}
    metadata = {"dataset_id": dataset_id, "dataset_version": dataset_version}
    staged = stage_canonical_snapshot(tmp_path, dataset_id, dataset_version, parts, metadata)
    published = publish_canonical_snapshot(staged)
    return (
        published.version_dir,
        published.dataset_id,
        published.dataset_version,
        published.content_hash,
    )


def test_registry_append_and_lookup(tmp_path: Path) -> None:
    _, dataset_id, dataset_version, content_hash = _publish_snapshot(tmp_path)
    entry = DatasetRegistryEntry(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        schema_version="1.0.0",
        created_at_ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ingest_run_id="ing_001",
        universe_hash="universe_v1",
        calendar_version="calendar_v1",
        sessionrules_version="sessionrules_v1",
        source_set=("TEST_PROVIDER",),
        row_count=1,
        content_hash=content_hash,
        notes="seed run",
    )
    registry_path = tmp_path / "registry.jsonl"

    append_registry_entry(registry_path, entry, canonical_root=tmp_path)

    resolved = lookup_registry_entry(registry_path, dataset_id, dataset_version)
    assert resolved == entry


def test_registry_rejects_duplicates(tmp_path: Path) -> None:
    _, dataset_id, dataset_version, content_hash = _publish_snapshot(tmp_path)
    entry = DatasetRegistryEntry(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        schema_version="1.0.0",
        created_at_ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ingest_run_id="ing_001",
        universe_hash="universe_v1",
        calendar_version="calendar_v1",
        sessionrules_version="sessionrules_v1",
        source_set=("TEST_PROVIDER",),
        row_count=1,
        content_hash=content_hash,
    )
    registry_path = tmp_path / "registry.jsonl"

    append_registry_entry(registry_path, entry, canonical_root=tmp_path)

    with pytest.raises(StorageError):
        append_registry_entry(registry_path, entry, canonical_root=tmp_path)


def test_registry_requires_snapshot_consistency(tmp_path: Path) -> None:
    _, dataset_id, dataset_version, _ = _publish_snapshot(tmp_path)
    entry = DatasetRegistryEntry(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        schema_version="1.0.0",
        created_at_ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ingest_run_id="ing_001",
        universe_hash="universe_v1",
        calendar_version="calendar_v1",
        sessionrules_version="sessionrules_v1",
        source_set=("TEST_PROVIDER",),
        row_count=1,
        content_hash="bad_hash",
    )
    registry_path = tmp_path / "registry.jsonl"

    with pytest.raises(StorageError):
        append_registry_entry(registry_path, entry, canonical_root=tmp_path)
