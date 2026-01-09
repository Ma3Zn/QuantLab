from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantlab.risk.attribution.variance import variance_attribution


def test_variance_attribution_sums_to_portfolio_variance() -> None:
    weights = pd.Series([0.6, 0.4], index=["EQ:SPY", "EQ:QQQ"])
    covariance = pd.DataFrame(
        [[0.04, 0.006], [0.006, 0.09]],
        index=["EQ:SPY", "EQ:QQQ"],
        columns=["EQ:SPY", "EQ:QQQ"],
    )

    result = variance_attribution(weights, covariance)

    expected = float(weights @ (covariance @ weights))
    assert result.portfolio_variance == pytest.approx(expected)
    assert float(result.contributions.sum()) == pytest.approx(expected)


def test_variance_attribution_diagonal_covariance() -> None:
    weights = pd.Series([0.25, 0.75], index=["EQ:AAA", "EQ:BBB"])
    covariance = pd.DataFrame(
        np.diag([0.04, 0.09]),
        index=["EQ:AAA", "EQ:BBB"],
        columns=["EQ:AAA", "EQ:BBB"],
    )

    result = variance_attribution(weights, covariance)

    expected_components = pd.Series(
        [0.04 * 0.25**2, 0.09 * 0.75**2],
        index=["EQ:AAA", "EQ:BBB"],
    )

    assert result.contributions.to_numpy() == pytest.approx(expected_components.to_numpy())
