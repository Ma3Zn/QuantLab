from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from quantlab.data.schemas.errors import DataValidationError
from quantlab.data.transforms.returns import compute_returns


def test_compute_returns_multiindex_simple() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3)]
    columns = pd.MultiIndex.from_tuples(
        [("EQ:SPY", "close"), ("EQ:QQQ", "close")],
        names=["asset_id", "field"],
    )
    frame = pd.DataFrame(
        [[100.0, 200.0], [110.0, 220.0]],
        index=index,
        columns=columns,
    )

    returns = compute_returns(frame, field="close")

    expected_columns = pd.MultiIndex.from_tuples(
        [("EQ:SPY", "close_return"), ("EQ:QQQ", "close_return")],
        names=["asset_id", "field"],
    )
    assert returns.columns.equals(expected_columns)
    assert pd.isna(returns.iloc[0, 0])
    assert pd.isna(returns.iloc[0, 1])
    assert returns.iloc[1, 0] == pytest.approx(0.1)
    assert returns.iloc[1, 1] == pytest.approx(0.1)


def test_compute_returns_error_on_missing_after_first_row() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    columns = pd.MultiIndex.from_tuples(
        [("EQ:SPY", "close"), ("EQ:QQQ", "close")],
        names=["asset_id", "field"],
    )
    frame = pd.DataFrame(
        [[100.0, 200.0], [101.0, None], [102.0, 204.0]],
        index=index,
        columns=columns,
    )

    with pytest.raises(DataValidationError):
        compute_returns(frame, field="close", missing_policy="ERROR")


def test_compute_returns_drop_dates_removes_nan_rows() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3)]
    columns = pd.MultiIndex.from_tuples(
        [("EQ:SPY", "close"), ("EQ:QQQ", "close")],
        names=["asset_id", "field"],
    )
    frame = pd.DataFrame(
        [[100.0, 200.0], [110.0, 220.0]],
        index=index,
        columns=columns,
    )

    returns = compute_returns(frame, field="close", missing_policy="DROP_DATES")

    assert list(returns.index) == [date(2024, 1, 3)]
    assert returns.iloc[0, 0] == pytest.approx(0.1)
    assert returns.iloc[0, 1] == pytest.approx(0.1)
