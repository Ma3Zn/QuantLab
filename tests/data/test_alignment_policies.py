from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from quantlab.data.schemas.errors import DataValidationError
from quantlab.data.schemas.requests import MissingDataPolicy
from quantlab.data.transforms.alignment import align_frame


def _raw_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {"close": [100.0, 101.0]},
        index=[date(2024, 1, 2), date(2024, 1, 4)],
    )


def _target_dates() -> list[date]:
    return [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]


def test_align_nan_ok_retains_missing_rows() -> None:
    aligned = align_frame(_raw_frame(), _target_dates(), MissingDataPolicy(policy="NAN_OK"))

    assert list(aligned.index) == _target_dates()
    assert pd.isna(aligned.loc[date(2024, 1, 3), "close"])


def test_align_drop_dates_removes_missing_rows() -> None:
    aligned = align_frame(_raw_frame(), _target_dates(), MissingDataPolicy(policy="DROP_DATES"))

    assert list(aligned.index) == [date(2024, 1, 2), date(2024, 1, 4)]


def test_align_error_raises_on_missing_rows() -> None:
    with pytest.raises(DataValidationError):
        align_frame(_raw_frame(), _target_dates(), MissingDataPolicy(policy="ERROR"))
