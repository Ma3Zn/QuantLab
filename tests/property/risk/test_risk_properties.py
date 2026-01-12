from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from hypothesis import given, seed, settings
from hypothesis import strategies as st

from quantlab.risk.metrics.covariance import sample_covariance
from quantlab.risk.metrics.drawdown import drawdown_series
from quantlab.risk.metrics.var_es import historical_var_es

_RETURN_VALUES = st.floats(
    min_value=-0.5,
    max_value=0.5,
    allow_nan=False,
    allow_infinity=False,
)
_SIMPLE_RETURNS = st.floats(
    min_value=-0.95,
    max_value=0.95,
    allow_nan=False,
    allow_infinity=False,
)


@st.composite
def _returns_frame(draw: Any) -> pd.DataFrame:
    rows = draw(st.integers(min_value=3, max_value=40))
    cols = draw(st.integers(min_value=1, max_value=6))
    data = draw(
        st.lists(
            st.lists(_RETURN_VALUES, min_size=cols, max_size=cols),
            min_size=rows,
            max_size=rows,
        )
    )
    return pd.DataFrame(data, columns=[f"asset_{idx}" for idx in range(cols)])


@seed(20240501)
@given(frame=_returns_frame())
@settings(max_examples=40, deadline=None)
def test_covariance_is_symmetric_and_psd(frame: pd.DataFrame) -> None:
    result = sample_covariance(frame)
    values = result.covariance.to_numpy(dtype=float)
    symmetry_error = float(np.max(np.abs(values - values.T)))
    assert symmetry_error <= 1e-10

    eigenvalues = np.linalg.eigvalsh(values)
    assert float(np.min(eigenvalues)) >= -1e-10


@seed(20240502)
@given(values=st.lists(_SIMPLE_RETURNS, min_size=1, max_size=200))
@settings(max_examples=40, deadline=None)
def test_drawdown_invariants(values: list[float]) -> None:
    series = pd.Series(values, name="returns")
    drawdown, _ = drawdown_series(series)
    wealth = (1.0 + series).cumprod()
    running_max = wealth.cummax()

    tolerance = 1e-12
    assert (drawdown <= tolerance).all()

    at_highs = wealth == running_max
    assert np.allclose(drawdown[at_highs], 0.0, atol=tolerance)


@seed(20240503)
@given(values=st.lists(_RETURN_VALUES, min_size=2, max_size=200))
@settings(max_examples=40, deadline=None)
def test_var_not_exceed_es(values: list[float]) -> None:
    series = pd.Series(values, name="returns")
    var_map, es_map, _ = historical_var_es(series, confidence_levels=(0.95, 0.99))

    tolerance = 1e-12
    for level, var_value in var_map.items():
        assert var_value <= es_map[level] + tolerance
