from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from quantlab.risk.metrics.var_es import historical_var_es


def test_historical_var_es_basic_sample() -> None:
    index = [
        date(2024, 1, 2),
        date(2024, 1, 3),
        date(2024, 1, 4),
        date(2024, 1, 5),
        date(2024, 1, 8),
    ]
    returns = pd.Series([0.01, -0.02, 0.03, -0.04, 0.05], index=index)

    var_map, es_map, warnings = historical_var_es(returns, confidence_levels=[0.8])

    losses = -returns
    expected_var = float(losses.quantile(0.8, interpolation="linear"))
    expected_es = float(losses[losses >= expected_var].mean())

    assert warnings == []
    assert var_map[0.8] == pytest.approx(expected_var)
    assert es_map[0.8] == pytest.approx(expected_es)
    assert es_map[0.8] >= var_map[0.8]


def test_historical_var_es_small_sample_warns() -> None:
    index = [date(2024, 1, 2 + day) for day in range(10)]
    returns = pd.Series([0.01 * ((-1) ** day) for day in range(10)], index=index)

    var_map, es_map, warnings = historical_var_es(returns, confidence_levels=[0.99])

    assert warnings
    assert warnings[0].code == "VAR_ES_SMALL_SAMPLE"
    assert es_map[0.99] >= var_map[0.99]
