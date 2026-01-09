from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from quantlab.risk.errors import RiskInputError
from quantlab.risk.metrics.returns import build_returns


def test_build_returns_constant_prices_simple() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    frame = pd.DataFrame(
        {"EQ:SPY": [100.0, 100.0, 100.0], "EQ:QQQ": [200.0, 200.0, 200.0]},
        index=index,
    )

    returns, warnings = build_returns(
        frame, return_definition="simple", missing_data_policy="ERROR"
    )

    assert warnings == []
    assert pd.isna(returns.iloc[0]).all()
    assert returns.iloc[1].tolist() == pytest.approx([0.0, 0.0])
    assert returns.iloc[2].tolist() == pytest.approx([0.0, 0.0])


def test_build_returns_simple_vs_log() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    frame = pd.DataFrame({"EQ:SPY": [100.0, 110.0, 121.0]}, index=index)

    simple, _ = build_returns(frame, return_definition="simple", missing_data_policy="ERROR")
    log, _ = build_returns(frame, return_definition="log", missing_data_policy="ERROR")

    assert simple.iloc[1, 0] == pytest.approx(0.1)
    assert simple.iloc[2, 0] == pytest.approx(0.1)
    assert log.iloc[1, 0] == pytest.approx(np.log(1.1))
    assert log.iloc[2, 0] == pytest.approx(np.log(1.1))


def test_build_returns_rejects_nan_and_inf() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    frame_nan = pd.DataFrame({"EQ:SPY": [100.0, None, 101.0]}, index=index)

    with pytest.raises(RiskInputError):
        build_returns(frame_nan, return_definition="simple", missing_data_policy="ERROR")

    frame_inf = pd.DataFrame({"EQ:SPY": [0.0, 100.0, 101.0]}, index=index)
    with pytest.raises(RiskInputError):
        build_returns(frame_inf, return_definition="simple", missing_data_policy="ERROR")


def test_build_returns_partial_emits_warning() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    frame = pd.DataFrame(
        {"EQ:SPY": [100.0, None, 101.0], "EQ:QQQ": [200.0, 201.0, 202.0]},
        index=index,
    )

    returns, warnings = build_returns(
        frame, return_definition="simple", missing_data_policy="PARTIAL"
    )

    assert pd.isna(returns.iloc[1, 0])
    assert warnings
    assert warnings[0].code == "MISSING_DATA_PARTIAL"
