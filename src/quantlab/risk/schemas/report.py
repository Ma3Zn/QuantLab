from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping, cast

from pydantic import Field, field_validator, model_validator

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.value_types import Currency, FiniteFloat
from quantlab.risk.schemas.base import RiskBaseModel
from quantlab.risk.schemas.request import ReturnDefinition

SchemaVersion = str | int
RISK_REPORT_VERSION = "1.0"


class RiskWarning(RiskBaseModel):
    """Structured warning emitted during risk computations."""

    code: str
    message: str
    context: dict[str, Any] = Field(default_factory=dict)


class RiskWindow(RiskBaseModel):
    """Window definition for a risk report."""

    lookback_trading_days: int | None = None
    start: date | None = None
    end: date | None = None

    @model_validator(mode="after")
    def _validate_window(self) -> RiskWindow:
        has_lookback = self.lookback_trading_days is not None
        has_start = self.start is not None
        has_end = self.end is not None

        if has_lookback:
            if self.lookback_trading_days is not None and self.lookback_trading_days <= 0:
                raise ValueError("lookback_trading_days must be positive")
        else:
            if not (has_start and has_end):
                raise ValueError("start/end are required when no lookback is given")
            if self.start and self.end and self.start > self.end:
                raise ValueError("start must be on or before end")

        return self


class RiskConventions(RiskBaseModel):
    """Convention metadata for a report."""

    return_definition: ReturnDefinition
    annualization_factor: int
    loss_definition: str

    @field_validator("annualization_factor")
    @classmethod
    def _require_positive_annualization(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("annualization_factor must be positive")
        return value


class RiskInputLineage(RiskBaseModel):
    """Identifiers/hashes for upstream datasets."""

    portfolio_snapshot_id: str | None = None
    portfolio_snapshot_hash: str | None = None
    market_data_bundle_id: str | None = None
    market_data_bundle_hash: str | None = None
    request_hash: str | None = None


class RiskCovarianceDiagnostics(RiskBaseModel):
    """Diagnostics for covariance/correlation estimation."""

    sample_size: int
    missing_count: int
    symmetry_max_error: float
    is_symmetric: bool
    estimator: str


class RiskMetrics(RiskBaseModel):
    """Core numerical metrics output for the risk report."""

    portfolio_vol_annualized: FiniteFloat | None = None
    max_drawdown: FiniteFloat | None = None
    tracking_error_annualized: FiniteFloat | None = None
    var: dict[str, FiniteFloat] | None = None
    es: dict[str, FiniteFloat] | None = None
    covariance_diagnostics: RiskCovarianceDiagnostics | None = None

    @field_validator("var", "es", mode="before")
    @classmethod
    def _normalize_tail_risk_map(
        cls, value: Mapping[object, object] | None
    ) -> dict[str, float] | None:
        if value is None:
            return None
        normalized: dict[str, float] = {}
        for key, raw_value in value.items():
            level = float(cast(float | int | str, key))
            if not 0.0 < level < 1.0:
                raise ValueError("tail risk confidence levels must be in (0, 1)")
            normalized[str(level)] = float(cast(float | int | str, raw_value))
        return dict(sorted(normalized.items(), key=lambda item: item[0]))


class AssetExposure(RiskBaseModel):
    asset_id: MarketDataId
    weight: FiniteFloat


class CurrencyExposure(RiskBaseModel):
    currency: Currency
    weight: FiniteFloat


class RiskExposures(RiskBaseModel):
    by_asset: list[AssetExposure]
    by_currency: list[CurrencyExposure]
    mapped: dict[str, list[AssetExposure]] | None = None

    @field_validator("by_asset")
    @classmethod
    def _sort_by_asset(cls, value: list[AssetExposure]) -> list[AssetExposure]:
        return sorted(value, key=lambda item: item.asset_id)

    @field_validator("by_currency")
    @classmethod
    def _sort_by_currency(cls, value: list[CurrencyExposure]) -> list[CurrencyExposure]:
        return sorted(value, key=lambda item: item.currency)

    @field_validator("mapped", mode="before")
    @classmethod
    def _normalize_mapped(
        cls, value: Mapping[str, Iterable[Mapping[str, object]]] | None
    ) -> dict[str, list[AssetExposure]] | None:
        if value is None:
            return None
        normalized: dict[str, list[AssetExposure]] = {}
        for bucket, items in value.items():
            exposures = [AssetExposure.model_validate(item) for item in items]
            normalized[bucket] = sorted(exposures, key=lambda item: item.asset_id)
        return dict(sorted(normalized.items(), key=lambda item: item[0]))


class VarianceContribution(RiskBaseModel):
    asset_id: MarketDataId
    component: FiniteFloat


class RiskAttribution(RiskBaseModel):
    variance_contributions: list[VarianceContribution]
    convention: str

    @field_validator("variance_contributions")
    @classmethod
    def _sort_variance_contributions(
        cls, value: list[VarianceContribution]
    ) -> list[VarianceContribution]:
        return sorted(value, key=lambda item: item.asset_id)


class RiskReport(RiskBaseModel):
    """Typed, deterministic risk report."""

    report_version: SchemaVersion = RISK_REPORT_VERSION
    generated_at_utc: datetime
    as_of: date
    window: RiskWindow
    conventions: RiskConventions
    input_lineage: RiskInputLineage | None = None
    metrics: RiskMetrics
    exposures: RiskExposures
    attribution: RiskAttribution
    warnings: list[RiskWarning] = Field(default_factory=list)

    @field_validator("generated_at_utc")
    @classmethod
    def _require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
            raise ValueError("generated_at_utc must be timezone-aware and in UTC")
        return value

    @field_validator("warnings")
    @classmethod
    def _sort_warnings(cls, value: list[RiskWarning]) -> list[RiskWarning]:
        return sorted(value, key=lambda item: (item.code, item.message))

    @model_validator(mode="after")
    def _validate_window_vs_as_of(self) -> RiskReport:
        if self.window.end and self.window.end > self.as_of:
            raise ValueError("window.end cannot be after as_of")
        if self.window.start and self.window.start > self.as_of:
            raise ValueError("window.start cannot be after as_of")
        return self


__all__ = [
    "AssetExposure",
    "CurrencyExposure",
    "RiskAttribution",
    "RiskConventions",
    "RiskCovarianceDiagnostics",
    "RiskExposures",
    "RiskInputLineage",
    "RiskMetrics",
    "RiskReport",
    "RiskWarning",
    "RiskWindow",
    "RISK_REPORT_VERSION",
    "SchemaVersion",
    "VarianceContribution",
]
