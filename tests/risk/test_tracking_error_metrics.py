from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from quantlab.risk.metrics.tracking_error import tracking_error_annualized


def test_tracking_error_aligns_on_intersection() -> None:
    portfolio_index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    benchmark_index = [date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)]
    portfolio = pd.Series([0.01, 0.02, 0.04], index=portfolio_index)
    benchmark = pd.Series([0.005, -0.01, 0.0], index=benchmark_index)

    value, warnings = tracking_error_annualized(
        portfolio,
        benchmark,
        annualization_factor=252,
        missing_data_policy="DROP_DATES",
    )

    active = pd.Series([0.02 - 0.005, 0.04 - (-0.01)])
    expected = active.std(ddof=1) * np.sqrt(252)
    assert warnings == []
    assert value == pytest.approx(float(expected))


def test_tracking_error_partial_emits_warning() -> None:
    portfolio_index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    benchmark_index = [date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)]
    portfolio = pd.Series([0.01, 0.02, 0.04], index=portfolio_index)
    benchmark = pd.Series([0.005, -0.01, 0.0], index=benchmark_index)

    value, warnings = tracking_error_annualized(
        portfolio,
        benchmark,
        annualization_factor=252,
        missing_data_policy="PARTIAL",
    )

    active = pd.Series([0.02 - 0.005, 0.04 - (-0.01)])
    expected = active.std(ddof=1) * np.sqrt(252)
    assert warnings
    assert warnings[0].code == "TRACKING_ERROR_PARTIAL"
    assert value == pytest.approx(float(expected))


def test_tracking_error_annualization_matches_std() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    portfolio = pd.Series([0.01, -0.02, 0.03], index=index)
    benchmark = pd.Series([0.0, 0.0, 0.0], index=index)

    value, warnings = tracking_error_annualized(
        portfolio, benchmark, annualization_factor=12, missing_data_policy="ERROR"
    )

    expected = portfolio.std(ddof=1) * np.sqrt(12)
    assert warnings == []
    assert value == pytest.approx(float(expected))
