from __future__ import annotations

from typing import Literal

import pandas as pd

from quantlab.data.schemas.errors import DataValidationError

ReturnMissingPolicy = Literal["ALLOW_NAN", "DROP_DATES", "ERROR"]
ReturnMethod = Literal["simple"]


def compute_returns(
    frame: pd.DataFrame,
    *,
    field: str = "close",
    method: ReturnMethod = "simple",
    missing_policy: ReturnMissingPolicy = "ALLOW_NAN",
) -> pd.DataFrame:
    """Compute returns from an aligned price frame without silent fills."""
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    if not field:
        raise ValueError("field must be a non-empty string")

    prices = _select_field(frame, field)
    returns = _compute_returns(prices, method=method)
    returns.columns = _build_return_columns(prices.columns, field)
    return _apply_missing_policy(returns, missing_policy)


def _select_field(frame: pd.DataFrame, field: str) -> pd.DataFrame:
    if isinstance(frame.columns, pd.MultiIndex):
        selector = frame.columns.get_level_values(-1) == field
        if not selector.any():
            raise DataValidationError(
                "field not available in frame",
                context={"field": field},
            )
        return frame.loc[:, selector]
    if field in frame.columns:
        return frame[[field]]
    return frame.copy()


def _compute_returns(frame: pd.DataFrame, *, method: ReturnMethod) -> pd.DataFrame:
    if method == "simple":
        return frame.pct_change(fill_method=None)
    raise ValueError(f"unsupported return method: {method}")


def _build_return_columns(columns: pd.Index, field: str) -> pd.Index:
    if isinstance(columns, pd.MultiIndex):
        tuples: list[tuple[object, ...]] = []
        for entry in columns.to_list():
            levels = list(entry)
            levels[-1] = f"{field}_return"
            tuples.append(tuple(levels))
        return pd.MultiIndex.from_tuples(tuples, names=columns.names)
    return pd.Index([f"{column}_return" for column in columns], name=columns.name)


def _apply_missing_policy(frame: pd.DataFrame, missing_policy: ReturnMissingPolicy) -> pd.DataFrame:
    if missing_policy == "ALLOW_NAN":
        return frame
    if missing_policy == "DROP_DATES":
        return frame.dropna(how="any")
    if missing_policy != "ERROR":
        raise ValueError(f"unsupported missing_policy: {missing_policy}")

    if frame.empty:
        return frame
    missing_mask = frame.isna()
    if len(frame.index) > 0:
        first_index = frame.index[0]
        missing_mask.loc[first_index] = False
    if missing_mask.any().any():
        raise DataValidationError(
            "returns contain missing values",
            context={"missing_policy": missing_policy},
        )
    return frame


__all__ = ["ReturnMethod", "ReturnMissingPolicy", "compute_returns"]
