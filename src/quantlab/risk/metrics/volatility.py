from __future__ import annotations

import numpy as np
import pandas as pd

from quantlab.risk.errors import RiskInputError
from quantlab.risk.schemas.report import RiskWarning


def annualized_volatility(
    returns: pd.Series,
    *,
    annualization_factor: int,
    ddof: int = 1,
    allow_missing: bool = False,
) -> tuple[float, list[RiskWarning]]:
    """Compute annualized volatility for a single return series."""
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
                code="VOLATILITY_DROPPED_MISSING",
                message="Dropped missing returns before volatility computation.",
                context={"missing_count": missing_count},
            )
        )
        series = series.dropna()

    sample_size = int(series.shape[0])
    if sample_size <= ddof:
        raise RiskInputError(
            "returns must have at least two observations after filtering",
            context={"rows": sample_size},
        )
    if annualization_factor <= 0:
        raise ValueError("annualization_factor must be positive")

    std = float(series.std(ddof=ddof))
    vol = std * float(np.sqrt(annualization_factor))
    return vol, warnings


def annualized_volatility_frame(
    returns: pd.DataFrame,
    *,
    annualization_factor: int,
    ddof: int = 1,
    allow_missing: bool = False,
) -> tuple[pd.Series, list[RiskWarning]]:
    """Compute annualized volatility per column for a return frame."""
    if not isinstance(returns, pd.DataFrame):
        raise TypeError("returns must be a pandas DataFrame")

    warnings: list[RiskWarning] = []
    frame = _require_numeric_frame(returns, label="returns")
    frame = frame.dropna(how="all")

    missing_count = int(frame.isna().sum().sum())
    if missing_count and not allow_missing:
        raise RiskInputError(
            "returns contain missing values",
            context={"missing_count": missing_count},
        )
    if missing_count and allow_missing:
        warnings.append(
            RiskWarning(
                code="VOLATILITY_DROPPED_MISSING",
                message="Dropped rows with missing returns before volatility computation.",
                context={"missing_count": missing_count},
            )
        )
        frame = frame.dropna(how="any")

    sample_size = int(len(frame))
    if sample_size <= ddof:
        raise RiskInputError(
            "returns must have at least two observations after filtering",
            context={"rows": sample_size},
        )
    if annualization_factor <= 0:
        raise ValueError("annualization_factor must be positive")

    std = frame.std(ddof=ddof)
    vol = std * float(np.sqrt(annualization_factor))
    return vol, warnings


def _require_numeric_series(series: pd.Series, *, label: str) -> pd.Series:
    try:
        return series.astype(float)
    except (TypeError, ValueError) as exc:
        raise RiskInputError(
            f"{label} must be numeric",
            context={"label": label},
            cause=exc,
        ) from exc


def _require_numeric_frame(frame: pd.DataFrame, *, label: str) -> pd.DataFrame:
    try:
        return frame.astype(float)
    except (TypeError, ValueError) as exc:
        raise RiskInputError(
            f"{label} must be numeric",
            context={"label": label},
            cause=exc,
        ) from exc


__all__ = ["annualized_volatility", "annualized_volatility_frame"]
