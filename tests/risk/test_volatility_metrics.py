from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from quantlab.risk.metrics.volatility import (
    annualized_volatility,
    annualized_volatility_frame,
)


def test_annualized_volatility_series_matches_std() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    returns = pd.Series([0.01, -0.01, 0.02], index=index)

    vol, warnings = annualized_volatility(returns, annualization_factor=252)

    expected = returns.std(ddof=1) * np.sqrt(252)
    assert warnings == []
    assert vol == pytest.approx(float(expected))


def test_annualized_volatility_frame_scales_linearly() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    returns = pd.DataFrame(
        {"EQ:SPY": [0.01, -0.02, 0.03], "EQ:QQQ": [0.00, 0.01, -0.01]},
        index=index,
    )

    base, _ = annualized_volatility_frame(returns, annualization_factor=252)
    scaled, _ = annualized_volatility_frame(returns * 3.0, annualization_factor=252)

    assert scaled.to_numpy() == pytest.approx(base.to_numpy() * 3.0)
