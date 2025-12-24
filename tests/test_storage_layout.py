from __future__ import annotations

import json
from pathlib import Path

import pytest

from quantlab.data.errors import StorageError
from quantlab.data.storage import (
    compute_content_hash,
    publish_canonical_snapshot,
    stage_canonical_snapshot,
    store_raw_payload,
)


def test_store_raw_payload_writes_paths_and_is_immutable(tmp_path: Path) -> None:
    payload = b'{"ok": true}'
    metadata = {"ingest_run_id": "run-1", "source": "dummy"}

    paths = store_raw_payload(
        tmp_path, "run-1", "req-1", payload, metadata, ext="json"
    )

    assert paths.base_dir == tmp_path / "ingest_run_id=run-1" / "request=req-1"
    assert paths.payload_path.read_bytes() == payload
    assert json.loads(paths.metadata_path.read_text(encoding="utf-8")) == metadata

    with pytest.raises(StorageError):
        store_raw_payload(tmp_path, "run-1", "req-1", payload, metadata)


def test_canonical_stage_and_publish_prevents_overwrite(tmp_path: Path) -> None:
    parts = {
        "part-0001.parquet": b"alpha",
        "part-0002.parquet": b"beta",
    }
    metadata = {
        "dataset_id": "md.equity.eod.bars",
        "dataset_version": "2025-01-01.1",
    }

    staged = stage_canonical_snapshot(
        tmp_path, "md.equity.eod.bars", "2025-01-01.1", parts, metadata
    )
    assert staged.content_hash == compute_content_hash(staged.part_paths)

    published = publish_canonical_snapshot(staged)
    assert published.version_dir == (
        tmp_path
        / "dataset_id=md.equity.eod.bars"
        / "dataset_version=2025-01-01.1"
    )
    assert published.metadata_path.exists()
    assert json.loads(published.metadata_path.read_text(encoding="utf-8")) == metadata
    assert all(path.exists() for path in published.part_paths)

    with pytest.raises(StorageError):
        stage_canonical_snapshot(
            tmp_path, "md.equity.eod.bars", "2025-01-01.1", parts, metadata
        )


def test_content_hash_is_order_invariant(tmp_path: Path) -> None:
    first = tmp_path / "part-0002.parquet"
    second = tmp_path / "part-0001.parquet"
    first.write_bytes(b"beta")
    second.write_bytes(b"alpha")

    assert compute_content_hash([first, second]) == compute_content_hash([second, first])
