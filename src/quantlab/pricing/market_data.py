from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Iterable, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from quantlab.instruments.value_types import FiniteFloat
from quantlab.pricing.warnings import MD_IMPUTED_FFILL, MD_STALE_SOURCE_DATE


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
    """Base model for market data metadata and points."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class MarketDataMeta(MarketDataBaseModel):
    """Metadata describing data quality and lineage for a market point."""

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
    """Market data value plus optional metadata."""

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


QUALITY_FLAG_WARNING_MAP: dict[str, str] = {
    "IMPUTED": MD_IMPUTED_FFILL,
    "STALE": MD_STALE_SOURCE_DATE,
}


def warnings_from_meta(meta: MarketDataMeta | None) -> list[str]:
    """Translate MarketDataMeta quality flags into pricing warning codes."""
    if meta is None or not meta.quality_flags:
        return []
    warnings: list[str] = []
    seen: set[str] = set()
    for flag in meta.quality_flags:
        code = QUALITY_FLAG_WARNING_MAP.get(flag)
        if code and code not in seen:
            warnings.append(code)
            seen.add(code)
    return warnings


def market_data_warnings(
    view: MarketDataView,
    asset_id: str,
    field: str,
    as_of: date,
) -> list[str]:
    """Collect pricing warning codes for a market data point if metadata exists."""
    get_point = getattr(view, "get_point", None)
    if not callable(get_point):
        return []
    point = get_point(asset_id, field, as_of)
    if point is None:
        return []
    return warnings_from_meta(point.meta)


__all__ = [
    "MarketDataMeta",
    "MarketDataView",
    "MarketPoint",
    "QUALITY_FLAG_WARNING_MAP",
    "market_data_warnings",
    "warnings_from_meta",
]
