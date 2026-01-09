from __future__ import annotations

import numpy as np
import pandas as pd

from quantlab.risk.errors import RiskInputError
from quantlab.risk.schemas.report import RiskWarning
from quantlab.risk.schemas.request import MissingDataPolicy, ReturnDefinition


def build_returns(
    prices: pd.DataFrame,
    *,
    return_definition: ReturnDefinition = "simple",
    missing_data_policy: MissingDataPolicy = "ERROR",
) -> tuple[pd.DataFrame, list[RiskWarning]]:
    """Compute return series from aligned price inputs with explicit policies."""
    if not isinstance(prices, pd.DataFrame):
        raise TypeError("prices must be a pandas DataFrame")

    if prices.empty:
        return prices.copy(), []

    warnings: list[RiskWarning] = []
    prices_frame = prices.copy()

    if return_definition == "log":
        _require_positive_prices(prices_frame)

    if missing_data_policy == "FORWARD_FILL":
        missing_before = _count_missing_prices(prices_frame)
        if missing_before:
            warnings.append(
                RiskWarning(
                    code="MISSING_DATA_FORWARD_FILL",
                    message=(
                        "Forward-filled missing prices before returns; results may be biased."
                    ),
                    context={"missing_count": missing_before},
                )
            )
        prices_frame = prices_frame.ffill()

    returns = _compute_returns(prices_frame, return_definition=return_definition)
    _raise_on_infinite_returns(returns, return_definition=return_definition)

    if missing_data_policy == "ERROR":
        _raise_on_missing_returns(returns)
    elif missing_data_policy == "DROP_DATES":
        returns = _drop_missing_returns(returns)
    elif missing_data_policy == "FORWARD_FILL":
        _raise_on_missing_returns(returns)
    elif missing_data_policy == "PARTIAL":
        missing_after = _count_missing_returns(returns)
        if missing_after:
            warnings.append(
                RiskWarning(
                    code="MISSING_DATA_PARTIAL",
                    message=(
                        "Partial missing data retained in returns; downstream metrics should"
                        " align on intersections."
                    ),
                    context={"missing_count": missing_after},
                )
            )
    else:
        raise ValueError(f"unsupported missing_data_policy: {missing_data_policy}")

    return returns, warnings


def _require_positive_prices(prices: pd.DataFrame) -> None:
    try:
        nonpositive = (prices <= 0).to_numpy()
    except TypeError as exc:
        raise RiskInputError(
            "prices must be numeric to compute log returns",
            context={"return_definition": "log"},
            cause=exc,
        ) from exc
    if np.any(nonpositive):
        raise RiskInputError(
            "log returns require strictly positive prices",
            context={"return_definition": "log"},
        )


def _compute_returns(prices: pd.DataFrame, *, return_definition: ReturnDefinition) -> pd.DataFrame:
    if return_definition == "simple":
        return prices.pct_change(fill_method=None)
    if return_definition == "log":
        return np.log(prices / prices.shift(1))
    raise ValueError(f"unsupported return_definition: {return_definition}")


def _raise_on_infinite_returns(
    returns: pd.DataFrame, *, return_definition: ReturnDefinition
) -> None:
    values = _to_float_array(returns, "returns")
    if np.isinf(values).any():
        raise RiskInputError(
            "returns contain infinite values",
            context={"return_definition": return_definition},
        )


def _raise_on_missing_returns(returns: pd.DataFrame) -> None:
    if returns.empty:
        return
    missing_mask = returns.isna()
    first_index = returns.index[0]
    missing_mask.loc[first_index] = False
    if missing_mask.any().any():
        raise RiskInputError("returns contain missing values", context={"policy": "ERROR"})


def _drop_missing_returns(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.dropna(how="any")


def _count_missing_prices(prices: pd.DataFrame) -> int:
    return int(prices.isna().sum().sum())


def _count_missing_returns(returns: pd.DataFrame) -> int:
    if returns.empty:
        return 0
    missing_mask = returns.isna()
    first_index = returns.index[0]
    missing_mask.loc[first_index] = False
    return int(missing_mask.sum().sum())


def _to_float_array(frame: pd.DataFrame, label: str) -> np.ndarray:
    try:
        return frame.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise RiskInputError(
            f"{label} must be numeric",
            context={"label": label},
            cause=exc,
        ) from exc


__all__ = ["build_returns"]
