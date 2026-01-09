from __future__ import annotations

from datetime import date
from typing import Iterable, Literal, cast

from pydantic import Field, field_validator, model_validator

from quantlab.risk.schemas.base import RiskBaseModel

ReturnDefinition = Literal["simple", "log"]
InputMode = Literal["PORTFOLIO_RETURNS", "STATIC_WEIGHTS_X_ASSET_RETURNS"]
MissingDataPolicy = Literal["ERROR", "DROP_DATES", "FORWARD_FILL", "PARTIAL"]


class CovarianceEstimator(RiskBaseModel):
    """Configuration for the covariance estimator."""

    type: Literal["SAMPLE"] = "SAMPLE"


class RiskRequest(RiskBaseModel):
    """Typed request for risk computations."""

    as_of: date
    lookback_trading_days: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    return_definition: ReturnDefinition = "simple"
    annualization_factor: int
    confidence_levels: tuple[float, ...]
    input_mode: InputMode
    missing_data_policy: MissingDataPolicy
    covariance_estimator: CovarianceEstimator = Field(default_factory=CovarianceEstimator)
    lineage: dict[str, str] | None = None
    notes: str | None = None

    @field_validator("return_definition", mode="before")
    @classmethod
    def _normalize_return_definition(cls, value: str | ReturnDefinition) -> ReturnDefinition:
        return cast(ReturnDefinition, str(value).lower())

    @field_validator("input_mode", "missing_data_policy", mode="before")
    @classmethod
    def _normalize_upper_fields(cls, value: str) -> str:
        return str(value).upper()

    @field_validator("annualization_factor")
    @classmethod
    def _require_positive_annualization(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("annualization_factor must be positive")
        return value

    @field_validator("confidence_levels", mode="before")
    @classmethod
    def _normalize_confidence_levels(cls, value: Iterable[float | int | str]) -> tuple[float, ...]:
        levels = [float(level) for level in value]
        if not levels:
            raise ValueError("confidence_levels must be non-empty")
        unique: set[float] = set()
        for level in levels:
            if not 0.0 < level < 1.0:
                raise ValueError("confidence_levels must be in (0, 1)")
            unique.add(level)
        return tuple(sorted(unique))

    @model_validator(mode="after")
    def _validate_window(self) -> RiskRequest:
        has_lookback = self.lookback_trading_days is not None
        has_start = self.start_date is not None
        has_end = self.end_date is not None

        if has_lookback:
            if self.lookback_trading_days is not None and self.lookback_trading_days <= 0:
                raise ValueError("lookback_trading_days must be positive")
            if has_start or has_end:
                raise ValueError("start_date/end_date cannot be used with lookback_trading_days")
        else:
            if not (has_start and has_end):
                raise ValueError("start_date and end_date are required when no lookback is given")
            if self.start_date and self.end_date and self.start_date > self.end_date:
                raise ValueError("start_date must be on or before end_date")
            if self.end_date and self.end_date > self.as_of:
                raise ValueError("end_date cannot be after as_of")
            if self.start_date and self.start_date > self.as_of:
                raise ValueError("start_date cannot be after as_of")

        return self


__all__ = [
    "CovarianceEstimator",
    "InputMode",
    "MissingDataPolicy",
    "ReturnDefinition",
    "RiskRequest",
]
