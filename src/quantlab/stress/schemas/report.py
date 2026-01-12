from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from pydantic import Field, field_validator, model_validator

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.value_types import Currency, FiniteFloat
from quantlab.stress.schemas.base import StressBaseModel

SchemaVersion = str | int
STRESS_REPORT_VERSION = "1.0"


class StressWarning(StressBaseModel):
    """Structured warning emitted during stress computations."""

    code: str
    message: str
    context: dict[str, Any] = Field(default_factory=dict)


class StressInputLineage(StressBaseModel):
    """Identifiers/hashes for upstream inputs."""

    portfolio_snapshot_id: str | None = None
    portfolio_snapshot_hash: str | None = None
    market_state_id: str | None = None
    market_state_hash: str | None = None
    scenario_set_id: str | None = None
    scenario_set_hash: str | None = None


class StressDriver(StressBaseModel):
    position_id: str
    pnl: FiniteFloat


class StressScenarioResult(StressBaseModel):
    scenario_id: str
    pnl: FiniteFloat
    delta_nav: FiniteFloat
    return_: FiniteFloat = Field(serialization_alias="return")
    top_drivers: list[StressDriver] | None = None

    @field_validator("scenario_id")
    @classmethod
    def _require_non_empty(cls, value: str) -> str:
        if not str(value).strip():
            raise ValueError("scenario_id must be non-empty")
        return str(value).strip()

    @field_validator("top_drivers")
    @classmethod
    def _sort_top_drivers(cls, value: list[StressDriver] | None) -> list[StressDriver] | None:
        if value is None:
            return None
        return sorted(value, key=lambda item: (-abs(float(item.pnl)), item.position_id))


class StressScenarioLoss(StressBaseModel):
    scenario_id: str
    pnl: FiniteFloat
    return_: FiniteFloat = Field(serialization_alias="return")

    @field_validator("scenario_id")
    @classmethod
    def _require_non_empty(cls, value: str) -> str:
        if not str(value).strip():
            raise ValueError("scenario_id must be non-empty")
        return str(value).strip()


class StressBreakdownByPosition(StressBaseModel):
    position_id: str
    scenario_id: str
    pnl: FiniteFloat


class StressBreakdownByAsset(StressBaseModel):
    asset_id: MarketDataId
    scenario_id: str
    pnl: FiniteFloat


class StressBreakdownByCurrency(StressBaseModel):
    currency: Currency
    scenario_id: str
    pnl: FiniteFloat


class StressBreakdowns(StressBaseModel):
    by_position: list[StressBreakdownByPosition]
    by_asset: list[StressBreakdownByAsset]
    by_currency: list[StressBreakdownByCurrency]

    @field_validator("by_position")
    @classmethod
    def _sort_by_position(
        cls, value: list[StressBreakdownByPosition]
    ) -> list[StressBreakdownByPosition]:
        return sorted(value, key=lambda item: (item.scenario_id, item.position_id))

    @field_validator("by_asset")
    @classmethod
    def _sort_by_asset(cls, value: list[StressBreakdownByAsset]) -> list[StressBreakdownByAsset]:
        return sorted(value, key=lambda item: (item.scenario_id, item.asset_id))

    @field_validator("by_currency")
    @classmethod
    def _sort_by_currency(
        cls, value: list[StressBreakdownByCurrency]
    ) -> list[StressBreakdownByCurrency]:
        return sorted(value, key=lambda item: (item.scenario_id, item.currency))


class StressSummary(StressBaseModel):
    worst_scenario_id: str
    max_loss: FiniteFloat
    max_loss_return: FiniteFloat
    min_return: FiniteFloat
    median_return: FiniteFloat
    max_return: FiniteFloat
    top_k_losses: list[StressScenarioLoss] | None = None
    top_drivers: list[StressDriver] | None = None

    @field_validator("worst_scenario_id")
    @classmethod
    def _require_non_empty(cls, value: str) -> str:
        if not str(value).strip():
            raise ValueError("worst_scenario_id must be non-empty")
        return str(value).strip()

    @field_validator("top_k_losses")
    @classmethod
    def _sort_top_losses(
        cls, value: list[StressScenarioLoss] | None
    ) -> list[StressScenarioLoss] | None:
        if value is None:
            return None
        return sorted(value, key=lambda item: (float(item.pnl), item.scenario_id))

    @field_validator("top_drivers")
    @classmethod
    def _sort_top_drivers(cls, value: list[StressDriver] | None) -> list[StressDriver] | None:
        if value is None:
            return None
        return sorted(value, key=lambda item: (-abs(float(item.pnl)), item.position_id))


class StressReport(StressBaseModel):
    """Typed, deterministic stress report."""

    report_version: SchemaVersion = STRESS_REPORT_VERSION
    generated_at_utc: datetime
    as_of: date
    input_lineage: StressInputLineage | None = None
    scenario_results: list[StressScenarioResult]
    breakdowns: StressBreakdowns
    summary: StressSummary
    warnings: list[StressWarning] = Field(default_factory=list)

    @field_validator("generated_at_utc")
    @classmethod
    def _require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
            raise ValueError("generated_at_utc must be timezone-aware and in UTC")
        return value

    @field_validator("scenario_results")
    @classmethod
    def _sort_scenario_results(
        cls, value: list[StressScenarioResult]
    ) -> list[StressScenarioResult]:
        return sorted(value, key=lambda item: item.scenario_id)

    @field_validator("warnings")
    @classmethod
    def _sort_warnings(cls, value: list[StressWarning]) -> list[StressWarning]:
        return sorted(value, key=lambda item: (item.code, item.message))

    @model_validator(mode="after")
    def _validate_summary(self) -> StressReport:
        scenario_ids = {result.scenario_id for result in self.scenario_results}
        if self.summary.worst_scenario_id not in scenario_ids:
            raise ValueError("summary.worst_scenario_id must appear in scenario_results")
        return self

    def to_canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, by_alias=True)


__all__ = [
    "SchemaVersion",
    "STRESS_REPORT_VERSION",
    "StressBreakdownByAsset",
    "StressBreakdownByCurrency",
    "StressBreakdownByPosition",
    "StressBreakdowns",
    "StressDriver",
    "StressInputLineage",
    "StressReport",
    "StressScenarioLoss",
    "StressScenarioResult",
    "StressSummary",
    "StressWarning",
]
