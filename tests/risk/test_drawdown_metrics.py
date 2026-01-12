from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from quantlab.risk.metrics.drawdown import drawdown_series, max_drawdown, time_to_recovery


def test_drawdown_series_monotone_increasing_zero() -> None:
    index = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    returns = pd.Series([0.01, 0.02, 0.03], index=index)

    drawdowns, warnings = drawdown_series(returns)

    assert warnings == []
    assert drawdowns.to_numpy() == pytest.approx([0.0, 0.0, 0.0])


def test_max_drawdown_known_sequence() -> None:
    index = [
        date(2024, 1, 2),
        date(2024, 1, 3),
        date(2024, 1, 4),
        date(2024, 1, 5),
        date(2024, 1, 8),
    ]
    returns = pd.Series([0.0, 0.1, -0.2, 0.05, -0.1], index=index)

    value, warnings = max_drawdown(returns)

    assert warnings == []
    assert value == pytest.approx(-0.244)


def test_time_to_recovery_returns_days() -> None:
    index = [
        date(2024, 1, 1),
        date(2024, 1, 2),
        date(2024, 1, 3),
        date(2024, 1, 4),
    ]
    returns = pd.Series([0.1, -0.2, 0.25, 0.0], index=index)

    value, warnings = time_to_recovery(returns)

    assert warnings == []
    assert value == 1


def test_time_to_recovery_none_when_unrecovered() -> None:
    index = [
        date(2024, 1, 1),
        date(2024, 1, 2),
        date(2024, 1, 3),
    ]
    returns = pd.Series([0.1, -0.2, 0.05], index=index)

    value, warnings = time_to_recovery(returns)

    assert warnings == []
    assert value is None
