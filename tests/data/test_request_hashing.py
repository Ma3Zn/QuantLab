from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone

from quantlab.data.schemas.requests import (
    AlignmentPolicy,
    AssetId,
    CalendarSpec,
    MissingDataPolicy,
    TimeSeriesRequest,
    ValidationPolicy,
)
from quantlab.data.transforms.hashing import request_hash


def _base_request() -> TimeSeriesRequest:
    return TimeSeriesRequest(
        assets=[AssetId("EQ:SPY"), AssetId("EQ:QQQ")],
        start=date(2024, 1, 2),
        end=date(2024, 1, 5),
        fields={"close", "open"},
        calendar=CalendarSpec(market="XNYS"),
        alignment=AlignmentPolicy(),
        missing=MissingDataPolicy(),
        validate=ValidationPolicy(),
        as_of=datetime(2024, 1, 6, 12, 0, tzinfo=timezone.utc),
    )


def test_request_hash_is_order_invariant() -> None:
    request_a = _base_request()
    request_b = TimeSeriesRequest(
        assets=[AssetId("EQ:QQQ"), AssetId("EQ:SPY")],
        start=request_a.start,
        end=request_a.end,
        fields={"open", "close"},
        calendar=request_a.calendar,
        alignment=request_a.alignment,
        missing=request_a.missing,
        validate=request_a.validate,
        as_of=request_a.as_of,
    )

    assert request_hash(request_a) == request_hash(request_b)


def test_request_hash_changes_on_policy_updates() -> None:
    base = _base_request()
    updated_missing = replace(base, missing=MissingDataPolicy(policy="ERROR"))
    updated_validation = replace(base, validate=ValidationPolicy(corp_action_jump_threshold=0.55))
    updated_calendar = replace(base, calendar=CalendarSpec(market="XNAS"))

    base_hash = request_hash(base)
    assert request_hash(updated_missing) != base_hash
    assert request_hash(updated_validation) != base_hash
    assert request_hash(updated_calendar) != base_hash
