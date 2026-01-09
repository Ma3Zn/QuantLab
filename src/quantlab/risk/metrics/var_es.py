from __future__ import annotations

from typing import Iterable, Literal

import numpy as np
import pandas as pd

from quantlab.risk.errors import RiskInputError
from quantlab.risk.schemas.report import RiskWarning

QuantileInterpolation = Literal["linear", "lower", "higher", "midpoint", "nearest"]

_INTERPOLATION_METHODS: set[QuantileInterpolation] = {
    "linear",
    "lower",
    "higher",
    "midpoint",
    "nearest",
}
_SAMPLE_SIZE_EPS = 1e-12


def historical_var_es(
    returns: pd.Series,
    *,
    confidence_levels: Iterable[float],
    allow_missing: bool = False,
    quantile_interpolation: QuantileInterpolation = "linear",
) -> tuple[dict[float, float], dict[float, float], list[RiskWarning]]:
    """Compute historical VaR/ES using loss = -return with explicit quantile interpolation."""
    if not isinstance(returns, pd.Series):
        raise TypeError("returns must be a pandas Series")
    if quantile_interpolation not in _INTERPOLATION_METHODS:
        raise ValueError(f"unsupported quantile_interpolation: {quantile_interpolation}")

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
                code="VAR_ES_DROPPED_MISSING",
                message="Dropped missing returns before VaR/ES computation.",
                context={"missing_count": missing_count},
            )
        )
        series = series.dropna()

    if series.empty:
        raise RiskInputError(
            "returns must have at least two observations after filtering",
            context={"rows": 0},
        )

    _raise_on_nonfinite(series, label="returns")
    sample_size = int(series.shape[0])
    if sample_size < 2:
        raise RiskInputError(
            "returns must have at least two observations after filtering",
            context={"rows": sample_size},
        )

    levels = _normalize_confidence_levels(confidence_levels)
    losses = -series

    var_map: dict[float, float] = {}
    es_map: dict[float, float] = {}
    for level in levels:
        required = _required_sample_size(level)
        if sample_size < required:
            warnings.append(
                RiskWarning(
                    code="VAR_ES_SMALL_SAMPLE",
                    message=(
                        "Sample size is smaller than the minimum recommended for tail estimates."
                    ),
                    context={
                        "confidence_level": level,
                        "sample_size": sample_size,
                        "required_sample_size": required,
                    },
                )
            )

        var_value = float(losses.quantile(level, interpolation=quantile_interpolation))
        tail = losses[losses >= var_value]
        if tail.empty:
            raise RiskInputError(
                "tail sample is empty for VaR/ES computation",
                context={"confidence_level": level, "var": var_value},
            )
        es_value = float(tail.mean())
        var_map[level] = var_value
        es_map[level] = es_value

    return var_map, es_map, warnings


def _normalize_confidence_levels(levels: Iterable[float]) -> tuple[float, ...]:
    values = [float(level) for level in levels]
    if not values:
        raise ValueError("confidence_levels must be non-empty")
    unique: set[float] = set()
    for level in values:
        if not 0.0 < level < 1.0:
            raise ValueError("confidence_levels must be in (0, 1)")
        unique.add(level)
    return tuple(sorted(unique))


def _required_sample_size(confidence_level: float) -> int:
    value = 1.0 / (1.0 - confidence_level)
    return int(np.ceil(value - _SAMPLE_SIZE_EPS))


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


__all__ = ["QuantileInterpolation", "historical_var_es"]
