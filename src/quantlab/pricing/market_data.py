from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Iterable, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from quantlab.instruments.value_types import FiniteFloat


def _normalize_str_sequence(values: Iterable[object] | None, field_name: str) -> tuple[str, ...]:
    if values is None:
        return tuple()
    normalized: list[str] = []
    for value in values:
        if isinstance(value, Enum):
            value = value.value
        value_str = str(value)
        if not value_str:
            raise ValueError(f"{field_name} entries must be non-empty")
        normalized.append(value_str)
    return tuple(normalized)


class MarketDataBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class MarketDataMeta(MarketDataBaseModel):
    quality_flags: tuple[str, ...] = Field(default_factory=tuple)
    source_date: date | None = None
    aligned_date: date | None = None
    lineage_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("quality_flags", "lineage_ids", mode="before")
    @classmethod
    def _normalize_string_sequences(
        cls,
        values: Iterable[object] | None,
        info: ValidationInfo,
    ) -> tuple[str, ...]:
        field_name = info.field_name or "sequence"
        return _normalize_str_sequence(values, field_name)


class MarketPoint(MarketDataBaseModel):
    value: FiniteFloat
    meta: MarketDataMeta | None = None


@runtime_checkable
class MarketDataView(Protocol):
    """Read-only adapter over the canonical data layer."""

    def get_value(self, asset_id: str, field: str, as_of: date) -> float:
        """Return the numeric market value for the asset/field/as-of key."""

    def has_value(self, asset_id: str, field: str, as_of: date) -> bool:
        """Return True if the market value exists for the asset/field/as-of key."""

    def get_point(self, asset_id: str, field: str, as_of: date) -> MarketPoint | None:
        """Return the value plus optional metadata if available."""


__all__ = [
    "MarketDataMeta",
    "MarketDataView",
    "MarketPoint",
]
