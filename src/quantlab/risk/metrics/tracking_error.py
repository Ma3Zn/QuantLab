from __future__ import annotations

import numpy as np
import pandas as pd

from quantlab.risk.errors import RiskInputError
from quantlab.risk.schemas.report import RiskWarning
from quantlab.risk.schemas.request import MissingDataPolicy


def tracking_error_annualized(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    *,
    annualization_factor: int,
    ddof: int = 1,
    missing_data_policy: MissingDataPolicy = "ERROR",
) -> tuple[float, list[RiskWarning]]:
    """Compute annualized tracking error from aligned return series.

    Alignment expectation: the portfolio and benchmark returns should share the same index;
    when indices differ, alignment is performed on the union and the missing_data_policy
    determines whether to error, drop dates, or forward-fill.
    """
    if not isinstance(portfolio_returns, pd.Series):
        raise TypeError("portfolio_returns must be a pandas Series")
    if not isinstance(benchmark_returns, pd.Series):
        raise TypeError("benchmark_returns must be a pandas Series")
    if annualization_factor <= 0:
        raise ValueError("annualization_factor must be positive")

    warnings: list[RiskWarning] = []
    portfolio = _require_numeric_series(portfolio_returns, label="portfolio_returns")
    benchmark = _require_numeric_series(benchmark_returns, label="benchmark_returns")

    aligned = _align_returns(portfolio, benchmark)
    aligned = aligned.dropna(how="all")

    missing_mask = aligned.isna().any(axis=1)
    missing_count = int(missing_mask.sum())
    if missing_data_policy == "ERROR":
        if missing_count:
            raise RiskInputError(
                "returns contain missing values",
                context={"missing_count": missing_count},
            )
    elif missing_data_policy == "DROP_DATES":
        aligned = aligned.loc[~missing_mask]
    elif missing_data_policy == "FORWARD_FILL":
        if missing_count:
            warnings.append(
                RiskWarning(
                    code="TRACKING_ERROR_FORWARD_FILL",
                    message="Forward-filled missing returns before tracking error computation.",
                    context={"missing_count": missing_count},
                )
            )
        aligned = aligned.ffill()
        missing_mask = aligned.isna().any(axis=1)
        missing_count = int(missing_mask.sum())
        if missing_count:
            raise RiskInputError(
                "returns contain missing values after forward fill",
                context={"missing_count": missing_count},
            )
    elif missing_data_policy == "PARTIAL":
        if missing_count:
            warnings.append(
                RiskWarning(
                    code="TRACKING_ERROR_PARTIAL",
                    message=(
                        "Dropped dates with missing benchmark/portfolio returns; tracking error"
                        " computed on intersection."
                    ),
                    context={"missing_count": missing_count},
                )
            )
        aligned = aligned.loc[~missing_mask]
    else:
        raise ValueError(f"unsupported missing_data_policy: {missing_data_policy}")

    if aligned.empty:
        raise RiskInputError(
            "returns must have at least two observations after filtering",
            context={"rows": 0},
        )

    _raise_on_nonfinite(aligned, label="returns")
    active_returns = aligned["portfolio"] - aligned["benchmark"]

    sample_size = int(len(active_returns))
    if sample_size <= ddof:
        raise RiskInputError(
            "returns must have at least two observations after filtering",
            context={"rows": sample_size},
        )

    std = float(active_returns.std(ddof=ddof))
    tracking_error = std * float(np.sqrt(annualization_factor))
    return tracking_error, warnings


def _align_returns(portfolio: pd.Series, benchmark: pd.Series) -> pd.DataFrame:
    return pd.concat({"portfolio": portfolio, "benchmark": benchmark}, axis=1)


def _require_numeric_series(series: pd.Series, *, label: str) -> pd.Series:
    try:
        return series.astype(float)
    except (TypeError, ValueError) as exc:
        raise RiskInputError(
            f"{label} must be numeric",
            context={"label": label},
            cause=exc,
        ) from exc


def _raise_on_nonfinite(frame: pd.DataFrame, *, label: str) -> None:
    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise RiskInputError(
            f"{label} contain non-finite values",
            context={"label": label},
        )


__all__ = ["tracking_error_annualized"]
