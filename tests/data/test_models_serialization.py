from __future__ import annotations

from datetime import date, datetime, timezone

from quantlab.data.schemas.lineage import LineageMeta
from quantlab.data.schemas.quality import QualityFlag, QualityReport
from quantlab.data.schemas.requests import (
    AlignmentPolicy,
    AssetId,
    CalendarSpec,
    MissingDataPolicy,
    TimeSeriesRequest,
    ValidationPolicy,
)


def test_policy_round_trip_json() -> None:
    calendar = CalendarSpec(market="XNYS")
    alignment = AlignmentPolicy()
    missing = MissingDataPolicy(policy="DROP_DATES", min_coverage=0.95)
    validation = ValidationPolicy(
        deduplicate="FIRST",
        max_abs_return=0.25,
        corp_action_jump_threshold=0.5,
        monotonic_index=False,
        type_checks=False,
    )

    assert CalendarSpec.from_json(calendar.to_json()) == calendar
    assert AlignmentPolicy.from_json(alignment.to_json()) == alignment
    assert MissingDataPolicy.from_json(missing.to_json()) == missing
    assert ValidationPolicy.from_json(validation.to_json()) == validation


def test_request_round_trip_json() -> None:
    request = TimeSeriesRequest(
        assets=[AssetId("EQ:SPY"), AssetId("EQ:QQQ")],
        start=date(2024, 1, 2),
        end=date(2024, 1, 5),
        fields={"close", "volume"},
        calendar=CalendarSpec(market="XNYS"),
        alignment=AlignmentPolicy(),
        missing=MissingDataPolicy(policy="NAN_OK"),
        validate=ValidationPolicy(),
        as_of=datetime(2024, 1, 6, 12, 0, tzinfo=timezone.utc),
    )

    assert TimeSeriesRequest.from_json(request.to_json()) == request


def test_quality_report_round_trip_json() -> None:
    report = QualityReport(
        coverage={AssetId("EQ:SPY"): 0.98},
        flag_counts={
            AssetId("EQ:SPY"): {
                QualityFlag.MISSING: 2,
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

    assert QualityReport.from_json(report.to_json()) == report


def test_lineage_meta_round_trip_json() -> None:
    lineage = LineageMeta(
        request_hash="abc123",
        request_json={"assets": ["EQ:SPY"], "start": "2024-01-02"},
        provider="TEST",
        ingestion_ts_utc="2024-01-06T12:00:00+00:00",
        as_of_utc="2024-01-06T12:00:00+00:00",
        dataset_version="2024-01-06",
        code_version="deadbeef",
        storage_paths=["data/cache/market/TEST/EQ:SPY/1D/part-2024.parquet"],
    )

    assert LineageMeta.from_json(lineage.to_json()) == lineage
