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


def _compute_wealth(series: pd.Series, *, return_definition: ReturnDefinition) -> pd.Series:
    if return_definition == "simple":
        return (1.0 + series).cumprod()
    if return_definition == "log":
        return np.exp(series.cumsum())
    raise ValueError(f"unsupported return_definition: {return_definition}")


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


__all__ = ["drawdown_series", "max_drawdown"]
