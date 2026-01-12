from __future__ import annotations

import numpy as np
import pandas as pd

from quantlab.risk.errors import RiskInputError
from quantlab.risk.schemas.report import RiskWarning
from quantlab.risk.schemas.request import ReturnDefinition


def drawdown_series(
    returns: pd.Series,
    *,
    return_definition: ReturnDefinition = "simple",
    allow_missing: bool = False,
) -> tuple[pd.Series, list[RiskWarning]]:
    """Compute the drawdown series from a return series."""
    series, warnings = _prepare_returns(returns, allow_missing=allow_missing)
    wealth = _compute_wealth(series, return_definition=return_definition)
    running_max = wealth.cummax()
    drawdown = wealth / running_max - 1.0
    drawdown.name = "drawdown"
    return drawdown, warnings


def max_drawdown(
    returns: pd.Series,
    *,
    return_definition: ReturnDefinition = "simple",
    allow_missing: bool = False,
) -> tuple[float, list[RiskWarning]]:
    """Compute the maximum drawdown (most negative drawdown)."""
    series, warnings = drawdown_series(
        returns,
        return_definition=return_definition,
        allow_missing=allow_missing,
    )
    return float(series.min()), warnings


def drawdown_metrics(
    returns: pd.Series,
    *,
    return_definition: ReturnDefinition = "simple",
    allow_missing: bool = False,
) -> tuple[float, int | None, list[RiskWarning]]:
    """Compute max drawdown and time-to-recovery from a return series."""
    series, warnings = _prepare_returns(returns, allow_missing=allow_missing)
    wealth = _compute_wealth(series, return_definition=return_definition)
    running_max = wealth.cummax()
    drawdown = wealth / running_max - 1.0
    max_dd = float(drawdown.min())
    time_to_recovery_days = _time_to_recovery_days(wealth, running_max)
    return max_dd, time_to_recovery_days, warnings


def time_to_recovery(
    returns: pd.Series,
    *,
    return_definition: ReturnDefinition = "simple",
    allow_missing: bool = False,
) -> tuple[int | None, list[RiskWarning]]:
    """Compute time-to-recovery in days from the max drawdown trough."""
    series, warnings = _prepare_returns(returns, allow_missing=allow_missing)
    wealth = _compute_wealth(series, return_definition=return_definition)
    running_max = wealth.cummax()
    return _time_to_recovery_days(wealth, running_max), warnings


def _prepare_returns(
    returns: pd.Series,
    *,
    allow_missing: bool,
) -> tuple[pd.Series, list[RiskWarning]]:
    if not isinstance(returns, pd.Series):
        raise TypeError("returns must be a pandas Series")

    warnings: list[RiskWarning] = []
    series = _require_numeric_series(returns, label="returns")
    series = series.dropna(how="all")

    missing_count = int(series.isna().sum())
    if missing_count and not allow_missing:
        raise RiskInputError(
            "returns contain missing values",
            context={"missing_count": missing_count},
        )
    if missing_count and allow_missing:
        warnings.append(
            RiskWarning(
                code="DRAWDOWN_DROPPED_MISSING",
                message="Dropped missing returns before drawdown computation.",
                context={"missing_count": missing_count},
            )
        )
        series = series.dropna()

    if series.empty:
        raise RiskInputError(
            "returns must have at least one observation after filtering",
            context={"rows": 0},
        )

    _raise_on_nonfinite(series, label="returns")
    return series, warnings


def _compute_wealth(series: pd.Series, *, return_definition: ReturnDefinition) -> pd.Series:
    if return_definition == "simple":
        return (1.0 + series).cumprod()
    if return_definition == "log":
        return np.exp(series.cumsum())
    raise ValueError(f"unsupported return_definition: {return_definition}")


def _time_to_recovery_days(wealth: pd.Series, running_max: pd.Series) -> int | None:
    drawdown = wealth / running_max - 1.0
    min_drawdown = float(drawdown.min())
    if min_drawdown >= 0.0:
        return 0

    trough_idx = drawdown.idxmin()
    target_level = float(running_max.loc[trough_idx])
    after_trough = wealth.loc[wealth.index > trough_idx]
    if after_trough.empty:
        return None

    recovered = after_trough[after_trough >= target_level]
    if recovered.empty:
        return None

    recovery_idx = recovered.index[0]
    delta = pd.Timestamp(recovery_idx) - pd.Timestamp(trough_idx)
    return int(delta.days)


def _require_numeric_series(series: pd.Series, *, label: str) -> pd.Series:
    try:
        return series.astype(float)
    except (TypeError, ValueError) as exc:
        raise RiskInputError(
            f"{label} must be numeric",
            context={"label": label},
            cause=exc,
        ) from exc


def _raise_on_nonfinite(series: pd.Series, *, label: str) -> None:
    values = series.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise RiskInputError(
            f"{label} contain non-finite values",
            context={"label": label},
        )


__all__ = ["drawdown_metrics", "drawdown_series", "max_drawdown", "time_to_recovery"]
