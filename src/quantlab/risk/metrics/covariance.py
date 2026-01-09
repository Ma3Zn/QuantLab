from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from quantlab.risk.errors import RiskInputError
from quantlab.risk.schemas.report import RiskWarning

SYMMETRY_TOLERANCE = 1e-12


@dataclass(frozen=True)
class CovarianceDiagnostics:
    sample_size: int
    missing_count: int
    symmetry_max_error: float
    is_symmetric: bool
    estimator: str = "SAMPLE"


@dataclass(frozen=True)
class CovarianceResult:
    covariance: pd.DataFrame
    correlation: pd.DataFrame
    diagnostics: CovarianceDiagnostics
    warnings: list[RiskWarning]


def sample_covariance(
    returns: pd.DataFrame,
    *,
    annualization_factor: int | None = None,
    allow_missing: bool = False,
    ddof: int = 1,
) -> CovarianceResult:
    """Compute sample covariance and correlation with diagnostics."""
    if not isinstance(returns, pd.DataFrame):
        raise TypeError("returns must be a pandas DataFrame")

    if returns.empty:
        raise RiskInputError("returns must have at least two observations", context={"rows": 0})

    warnings: list[RiskWarning] = []
    frame = _require_numeric_frame(returns, label="returns")
    frame = frame.dropna(how="all")

    missing_count = _count_missing(frame)
    if missing_count and not allow_missing:
        raise RiskInputError(
            "returns contain missing values",
            context={"missing_count": missing_count},
        )
    if missing_count and allow_missing:
        warnings.append(
            RiskWarning(
                code="COVARIANCE_DROPPED_MISSING",
                message="Dropped rows with missing returns before covariance estimation.",
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

    covariance = frame.cov(ddof=ddof)
    if annualization_factor is not None:
        if annualization_factor <= 0:
            raise ValueError("annualization_factor must be positive")
        covariance = covariance * float(annualization_factor)

    correlation = _safe_correlation(covariance)

    symmetry_max_error = _symmetry_max_error(covariance)
    diagnostics = CovarianceDiagnostics(
        sample_size=sample_size,
        missing_count=missing_count,
        symmetry_max_error=symmetry_max_error,
        is_symmetric=symmetry_max_error <= SYMMETRY_TOLERANCE,
    )

    return CovarianceResult(
        covariance=covariance,
        correlation=correlation,
        diagnostics=diagnostics,
        warnings=warnings,
    )


def _require_numeric_frame(frame: pd.DataFrame, *, label: str) -> pd.DataFrame:
    try:
        return frame.astype(float)
    except (TypeError, ValueError) as exc:
        raise RiskInputError(
            f"{label} must be numeric",
            context={"label": label},
            cause=exc,
        ) from exc


def _count_missing(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    missing_mask = frame.isna()
    return int(missing_mask.sum().sum())


def _safe_correlation(covariance: pd.DataFrame) -> pd.DataFrame:
    values = covariance.to_numpy(dtype=float)
    variances = np.diag(values)
    stddev = np.sqrt(np.maximum(variances, 0.0))
    denom = np.outer(stddev, stddev)
    corr_values = np.divide(
        values,
        denom,
        out=np.zeros_like(values),
        where=denom != 0.0,
    )
    np.fill_diagonal(corr_values, 1.0)
    return pd.DataFrame(corr_values, index=covariance.index, columns=covariance.columns)


def _symmetry_max_error(covariance: pd.DataFrame) -> float:
    values = covariance.to_numpy(dtype=float)
    delta = values - values.T
    if delta.size == 0:
        return 0.0
    return float(np.max(np.abs(delta)))


__all__ = ["CovarianceDiagnostics", "CovarianceResult", "sample_covariance"]
