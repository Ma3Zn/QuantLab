from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Sequence

import pandas as pd

from quantlab.data.schemas.errors import DataValidationError
from quantlab.data.schemas.requests import MissingDataPolicy, TimeSeriesRequest
from quantlab.data.transforms.calendars import MarketCalendarAdapter


def build_target_index(request: TimeSeriesRequest) -> pd.Index:
    """Build the target date index from the request calendar."""

    if request.calendar is None:
        raise DataValidationError(
            "calendar must be provided", context={"request": request.to_dict()}
        )
    if request.calendar.kind != "MARKET":
        raise DataValidationError(
            "calendar kind must be MARKET",
            context={"calendar_kind": request.calendar.kind},
        )
    calendar = MarketCalendarAdapter(request.calendar.market)
    sessions = calendar.sessions(request.start, request.end)
    target_index = pd.Index(sessions, name="date")
    if not target_index.is_unique:
        raise DataValidationError(
            "target calendar sessions must be unique",
            context={"market": request.calendar.market},
        )
    if not target_index.is_monotonic_increasing:
        raise DataValidationError(
            "target calendar sessions must be monotonic increasing",
            context={"market": request.calendar.market},
        )
    return target_index


def align_frame(
    raw_frame: pd.DataFrame,
    target_dates: Sequence[date] | pd.Index,
    missing_policy: MissingDataPolicy,
) -> pd.DataFrame:
    """Align a raw frame to the target dates and apply missing data policy."""

    if not isinstance(raw_frame, pd.DataFrame):
        raise TypeError("raw_frame must be a pandas DataFrame")
    target_index = _normalize_target_index(target_dates)
    normalized = _normalize_frame_index(raw_frame)
    aligned = normalized.reindex(target_index)
    aligned.index.name = "date"

    if missing_policy.policy == "NAN_OK":
        return aligned
    if missing_policy.policy == "DROP_DATES":
        return aligned.dropna(how="any")
    if missing_policy.policy == "ERROR":
        _raise_on_missing(aligned)
        return aligned
    raise ValueError(f"unknown missing policy: {missing_policy.policy}")


def _normalize_target_index(target_dates: Sequence[date] | pd.Index) -> pd.Index:
    if isinstance(target_dates, pd.Index):
        values: Iterable[object] = target_dates
    else:
        values = list(target_dates)
    normalized = pd.Index([_coerce_date(value) for value in values], name="date")
    if not normalized.is_unique:
        duplicates = normalized[normalized.duplicated()].unique().tolist()
        raise DataValidationError(
            "target_dates must be unique",
            context={"duplicate_dates": _format_dates(duplicates)},
        )
    if not normalized.is_monotonic_increasing:
        raise DataValidationError("target_dates must be monotonic increasing")
    return normalized


def _normalize_frame_index(raw_frame: pd.DataFrame) -> pd.DataFrame:
    values = [_coerce_date(value) for value in raw_frame.index]
    normalized = raw_frame.copy()
    normalized.index = pd.Index(values, name="date")
    if not normalized.index.is_unique:
        duplicates = normalized.index[normalized.index.duplicated()].unique().tolist()
        raise DataValidationError(
            "raw_frame index contains duplicate dates",
            context={"duplicate_dates": _format_dates(duplicates)},
        )
    return normalized


def _coerce_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise DataValidationError(
                "target date must be YYYY-MM-DD",
                context={"value": value},
                cause=exc,
            ) from exc
    raise DataValidationError("target date must be a date or ISO string", context={"value": value})


def _raise_on_missing(aligned: pd.DataFrame) -> None:
    if aligned.empty:
        if not aligned.index.empty:
            raise DataValidationError("aligned frame has missing data for all dates")
        return
    missing_rows = aligned.isna().any(axis=1)
    if missing_rows.any():
        missing_dates = aligned.index[missing_rows].tolist()
        raise DataValidationError(
            "aligned frame has missing values",
            context={
                "missing_count": int(missing_rows.sum()),
                "missing_dates": _format_dates(missing_dates),
            },
        )


def _format_dates(values: Iterable[object]) -> list[str]:
    formatted: list[str] = []
    for value in values:
        if isinstance(value, datetime):
            formatted.append(value.date().isoformat())
        elif isinstance(value, date):
            formatted.append(value.isoformat())
        else:
            formatted.append(str(value))
        if len(formatted) >= 5:
            break
    return formatted
