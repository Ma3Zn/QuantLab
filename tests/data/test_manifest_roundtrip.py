from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from quantlab.data.schemas.lineage import LineageMeta
from quantlab.data.schemas.quality import QualityFlag, QualityReport
from quantlab.data.schemas.requests import AssetId, CalendarSpec, TimeSeriesRequest
from quantlab.data.storage.layout import asset_cache_path
from quantlab.data.storage.manifests import read_manifest, write_manifest
from quantlab.data.transforms.hashing import request_hash


def _build_request() -> TimeSeriesRequest:
    return TimeSeriesRequest(
        assets=[AssetId("EQ:SPY")],
        start=date(2024, 1, 2),
        end=date(2024, 1, 5),
        calendar=CalendarSpec(market="XNYS"),
    )


def _build_quality() -> QualityReport:
    return QualityReport(
        coverage={AssetId("EQ:SPY"): 0.75},
        flag_counts={
            AssetId("EQ:SPY"): {
                QualityFlag.MISSING: 1,
                QualityFlag.SUSPECT_CORP_ACTION: 1,
            }
        },
        flag_examples={
            AssetId("EQ:SPY"): {
                QualityFlag.MISSING: ["2024-01-03"],
                QualityFlag.SUSPECT_CORP_ACTION: ["2024-01-04"],
            }
        },
        actions={"deduplicate": "LAST"},
    )


def test_manifest_roundtrip_and_golden(tmp_path: Path) -> None:
    request = _build_request()
    req_hash = request_hash(request)

    lineage = LineageMeta(
        request_hash=req_hash,
        request_json=request.to_dict(),
        provider="TEST",
        ingestion_ts_utc="2024-01-06T12:00:00+00:00",
        as_of_utc=None,
        dataset_version="2024-01-06",
        code_version="deadbeef",
        storage_paths=[],
    )

    paths = [
        asset_cache_path(Path("data/cache"), "TEST", AssetId("EQ:SPY"), 2024),
        asset_cache_path(Path("data/cache"), "TEST", AssetId("EQ:SPY"), 2023),
    ]

    manifest_path = write_manifest(tmp_path, req_hash, lineage, _build_quality(), paths)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    golden_path = Path("tests/data/golden/manifests") / f"{req_hash}.json"
    expected_payload = json.loads(golden_path.read_text(encoding="utf-8"))

    assert payload == expected_payload
    assert read_manifest(tmp_path, req_hash) == expected_payload
