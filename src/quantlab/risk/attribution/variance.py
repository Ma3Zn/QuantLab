from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from quantlab.risk.errors import RiskInputError

CONVENTION_COMPONENT = "component = weight * (covariance @ weight)"


@dataclass(frozen=True)
class VarianceAttributionResult:
    contributions: pd.Series
    portfolio_variance: float
    convention: str = CONVENTION_COMPONENT


def variance_attribution(
    weights: pd.Series,
    covariance: pd.DataFrame,
) -> VarianceAttributionResult:
    """Compute component variance contributions for a static weight vector."""
    if not isinstance(weights, pd.Series):
        raise TypeError("weights must be a pandas Series")
    if not isinstance(covariance, pd.DataFrame):
        raise TypeError("covariance must be a pandas DataFrame")

    series = _require_numeric_series(weights, label="weights")
    frame = _require_numeric_frame(covariance, label="covariance")

    if frame.empty:
        raise RiskInputError("covariance must be non-empty", context={"rows": 0})
    if series.empty:
        raise RiskInputError("weights must be non-empty", context={"rows": 0})
    if frame.shape[0] != frame.shape[1]:
        raise RiskInputError(
            "covariance must be square",
            context={"rows": frame.shape[0], "columns": frame.shape[1]},
        )

    if set(frame.index) != set(frame.columns):
        raise RiskInputError(
            "covariance index/columns must match",
            context={"index_size": len(frame.index), "column_size": len(frame.columns)},
        )
    if set(series.index) != set(frame.index):
        raise RiskInputError(
            "weights index must match covariance labels",
            context={"weights_size": len(series.index), "covariance_size": len(frame.index)},
        )

    aligned_cov = frame.loc[frame.index, frame.index]
    aligned_weights = series.reindex(aligned_cov.index)

    _raise_on_nonfinite(aligned_weights, label="weights")
    _raise_on_nonfinite_frame(aligned_cov, label="covariance")

    marginal = aligned_cov @ aligned_weights
    components = aligned_weights * marginal
    portfolio_variance = float(components.sum())

    return VarianceAttributionResult(
        contributions=components,
        portfolio_variance=portfolio_variance,
    )


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


def _raise_on_nonfinite(series: pd.Series, *, label: str) -> None:
    values = series.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise RiskInputError(
            f"{label} contain non-finite values",
            context={"label": label},
        )


def _raise_on_nonfinite_frame(frame: pd.DataFrame, *, label: str) -> None:
    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise RiskInputError(
            f"{label} contain non-finite values",
            context={"label": label},
        )


__all__ = ["CONVENTION_COMPONENT", "VarianceAttributionResult", "variance_attribution"]
