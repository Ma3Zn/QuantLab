from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from quantlab.risk.metrics.covariance import sample_covariance


def test_sample_covariance_symmetry_and_annualization() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    returns = pd.DataFrame(
        {"EQ:SPY": [0.01, 0.02, 0.03], "EQ:QQQ": [0.02, 0.01, 0.00]},
        index=index,
    )

    daily = sample_covariance(returns)
    annual = sample_covariance(returns, annualization_factor=252)

    assert daily.diagnostics.sample_size == 3
    assert daily.diagnostics.is_symmetric
    assert np.allclose(daily.covariance, daily.covariance.T)
    assert np.allclose(daily.correlation, daily.correlation.T)
    assert np.allclose(np.diag(daily.correlation), 1.0)
    assert annual.covariance.to_numpy() == pytest.approx(daily.covariance.to_numpy() * 252.0)


def test_sample_covariance_scales_quadratically() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    returns = pd.DataFrame(
        {"EQ:SPY": [0.01, -0.02, 0.03], "EQ:QQQ": [0.02, 0.00, -0.01]},
        index=index,
    )

    base = sample_covariance(returns)
    scaled = sample_covariance(returns * 2.0)

    assert scaled.covariance.to_numpy() == pytest.approx(base.covariance.to_numpy() * 4.0)


def test_correlation_handles_zero_variance() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    returns = pd.DataFrame(
        {"EQ:CONST": [0.0, 0.0, 0.0], "EQ:MOVE": [0.01, -0.01, 0.02]},
        index=index,
    )

    result = sample_covariance(returns)

    corr = result.correlation
    assert np.isfinite(corr.to_numpy()).all()
    assert corr.loc["EQ:CONST", "EQ:MOVE"] == pytest.approx(0.0)
    assert corr.loc["EQ:CONST", "EQ:CONST"] == pytest.approx(1.0)
