from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Annotated, Iterable, Literal, Mapping

from pydantic import Field, ValidationError, field_validator, model_validator

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.value_types import FiniteFloat
from quantlab.stress.errors import StressScenarioError
from quantlab.stress.schemas.base import StressBaseModel

ShockConvention = Literal["RETURN_MULTIPLICATIVE", "PRICE_MULTIPLIER"]
MissingShockPolicy = Literal["ZERO_WITH_WARNING", "ERROR"]
ScenarioType = Literal["ParametricShock", "CustomShockVector", "HistoricalShock"]


def _canonical_shock_vector(
    shock_vector: Mapping[MarketDataId, FiniteFloat],
) -> dict[str, float]:
    return {
        str(asset_id): float(value)
        for asset_id, value in sorted(shock_vector.items(), key=lambda item: str(item[0]))
    }


class ScenarioBase(StressBaseModel):
    """Base model for stress scenarios."""

    scenario_id: str
    name: str
    type: ScenarioType
    shock_convention: ShockConvention
    shock_vector: dict[MarketDataId, FiniteFloat]
    tags: tuple[str, ...] | None = None

    @field_validator("scenario_id", "name")
    @classmethod
    def _require_non_empty(cls, value: str) -> str:
        if not str(value).strip():
            raise ValueError("scenario_id and name must be non-empty")
        return str(value).strip()

    @field_validator("shock_convention", mode="before")
    @classmethod
    def _normalize_convention(cls, value: str) -> str:
        return str(value).upper()

    @field_validator("shock_vector")
    @classmethod
    def _validate_shock_vector(
        cls, value: Mapping[MarketDataId, FiniteFloat]
    ) -> dict[MarketDataId, FiniteFloat]:
        if not value:
            raise ValueError("shock_vector must be non-empty")
        for asset_id in value.keys():
            if not str(asset_id).strip():
                raise ValueError("shock_vector keys must be non-empty")
        return dict(value)

    @field_validator("tags", mode="before")
    @classmethod
    def _normalize_tags(cls, value: Iterable[object] | None) -> tuple[str, ...] | None:
        if value is None:
            return None
        tags = [str(item).strip() for item in value]
        if any(not tag for tag in tags):
            raise ValueError("tags must be non-empty strings")
        return tuple(sorted(set(tags)))

    def to_canonical_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "type": self.type,
            "shock_convention": self.shock_convention,
            "shock_vector": _canonical_shock_vector(self.shock_vector),
        }
        if self.tags:
            payload["tags"] = list(self.tags)
        return payload


class ParametricShock(ScenarioBase):
    type: Literal["ParametricShock"] = "ParametricShock"


class CustomShockVector(ScenarioBase):
    type: Literal["CustomShockVector"] = "CustomShockVector"


class HistoricalShock(ScenarioBase):
    type: Literal["HistoricalShock"] = "HistoricalShock"


Scenario = Annotated[
    ParametricShock | CustomShockVector | HistoricalShock,
    Field(discriminator="type"),
]


class ScenarioSet(StressBaseModel):
    """Scenario set with deterministic ordering and hashing helpers."""

    as_of: date
    shock_convention: ShockConvention | None = None
    missing_shock_policy: MissingShockPolicy
    scenarios: list[Scenario]

    @field_validator("shock_convention", "missing_shock_policy", mode="before")
    @classmethod
    def _normalize_upper_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(value).upper()

    @field_validator("scenarios")
    @classmethod
    def _sort_scenarios(cls, value: list[Scenario]) -> list[Scenario]:
        if not value:
            raise ValueError("scenarios must be non-empty")
        return sorted(value, key=lambda item: item.scenario_id)

    @model_validator(mode="after")
    def _validate_scenarios(self) -> ScenarioSet:
        scenario_ids = [scenario.scenario_id for scenario in self.scenarios]
        if len(set(scenario_ids)) != len(scenario_ids):
            raise ValueError("scenario_id values must be unique")
        if self.shock_convention is not None:
            for scenario in self.scenarios:
                if scenario.shock_convention != self.shock_convention:
                    raise ValueError(
                        "scenario shock_convention must match scenario set shock_convention"
                    )
        return self

    def to_canonical_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "as_of": self.as_of.isoformat(),
            "missing_shock_policy": self.missing_shock_policy,
            "scenarios": [
                scenario.to_canonical_dict()
                for scenario in sorted(self.scenarios, key=lambda item: item.scenario_id)
            ],
        }
        if self.shock_convention is not None:
            payload["shock_convention"] = self.shock_convention
        return payload

    def canonical_hash(self) -> str:
        return scenario_set_hash(self)

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> ScenarioSet:
        try:
            return cls.model_validate(payload)
        except ValidationError as exc:
            raise StressScenarioError(
                "scenario set validation failed",
                context={"errors": exc.errors()},
                cause=exc,
            ) from exc


def scenario_set_hash(scenario_set: ScenarioSet) -> str:
    payload = scenario_set.to_canonical_dict()
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


__all__ = [
    "CustomShockVector",
    "HistoricalShock",
    "MissingShockPolicy",
    "ParametricShock",
    "Scenario",
    "ScenarioBase",
    "ScenarioSet",
    "ScenarioType",
    "ShockConvention",
    "scenario_set_hash",
]
