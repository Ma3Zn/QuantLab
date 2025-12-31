from __future__ import annotations

from datetime import date
from typing import Any, Iterable, Literal

import pandas as pd
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quantlab.data.schemas.requests import (
    AssetId,
    CalendarSpec,
    MissingDataPolicy,
    TimeSeriesRequest,
)
from quantlab.data.transforms.alignment import align_frame
from quantlab.data.transforms.hashing import request_hash


@st.composite
def _aligned_cases(draw: Any) -> tuple[pd.DataFrame, list[date]]:
    target_dates = draw(
        st.lists(
            st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31)),
            min_size=1,
            max_size=20,
            unique=True,
        )
    )
    target_dates_sorted = sorted(target_dates)
    subset = draw(
        st.lists(
            st.sampled_from(target_dates_sorted),
            min_size=1,
            max_size=len(target_dates_sorted),
            unique=True,
        )
    )
    subset_sorted = sorted(subset)
    values = draw(
        st.lists(
            st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=len(subset_sorted),
            max_size=len(subset_sorted),
        )
    )
    frame = pd.DataFrame({"close": values}, index=subset_sorted)
    return frame, target_dates_sorted


@st.composite
def _request_assets(draw: Any) -> list[AssetId]:
    suffixes = draw(
        st.lists(
            st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=1, max_size=4),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )
    return [AssetId(f"EQ:{suffix}") for suffix in suffixes]


_FIELD_LITERALS: tuple[Literal["close", "open", "high", "low", "volume"], ...] = (
    "close",
    "open",
    "high",
    "low",
    "volume",
)


@st.composite
def _request_fields(draw: Any) -> list[Literal["close", "open", "high", "low", "volume"]]:
    return draw(
        st.lists(
            st.sampled_from(_FIELD_LITERALS),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )


@given(case=_aligned_cases())
@settings(max_examples=25, deadline=None)
def test_alignment_output_index_unique_monotonic(case: tuple[pd.DataFrame, list[date]]) -> None:
    frame, target_dates = case

    aligned = align_frame(frame, target_dates, MissingDataPolicy(policy="NAN_OK"))

    assert aligned.index.is_unique
    assert aligned.index.is_monotonic_increasing
    assert list(aligned.index) == target_dates


@given(case=_aligned_cases())
@settings(max_examples=25, deadline=None)
def test_alignment_idempotent(case: tuple[pd.DataFrame, list[date]]) -> None:
    frame, target_dates = case

    aligned_once = align_frame(frame, target_dates, MissingDataPolicy(policy="NAN_OK"))
    aligned_twice = align_frame(aligned_once, target_dates, MissingDataPolicy(policy="NAN_OK"))

    assert aligned_once.equals(aligned_twice)


@given(assets=_request_assets(), fields=_request_fields())
@settings(max_examples=25, deadline=None)
def test_request_hash_order_invariant(
    assets: list[AssetId],
    fields: list[Literal["close", "open", "high", "low", "volume"]],
) -> None:
    assume(len(assets) >= 1)
    assume(len(fields) >= 1)
    permuted_assets = list(reversed(assets))

    request_a = _make_request(assets, fields)
    request_b = _make_request(permuted_assets, fields)

    assert request_hash(request_a) == request_hash(request_b)


def _make_request(
    assets: Iterable[AssetId],
    fields: Iterable[Literal["close", "open", "high", "low", "volume"]],
) -> TimeSeriesRequest:
    return TimeSeriesRequest(
        assets=list(assets),
        start=date(2024, 1, 2),
        end=date(2024, 1, 5),
        calendar=CalendarSpec(market="XNYS"),
        fields=set(fields),
    )
