from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from quantlab.instruments.ids import InstrumentId, MarketDataId
from quantlab.instruments.value_types import Currency, FiniteFloat

SchemaVersion = str | int
VALUATION_SCHEMA_VERSION = "0.1"


class PricingBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    @field_validator("schema_version", check_fields=False)
    @classmethod
    def _schema_version_non_empty(cls, value: SchemaVersion) -> SchemaVersion:
        if isinstance(value, str):
            if not value.strip():
                raise ValueError("schema_version must be non-empty")
            return value
        if isinstance(value, int):
            if value <= 0:
                raise ValueError("schema_version must be positive")
            return value
        raise TypeError("schema_version must be str or int")


class ValuationInput(PricingBaseModel):
    asset_id: str
    field: str
    date: date
    value: FiniteFloat


class CurrencyBreakdown(PricingBaseModel):
    notional_native: FiniteFloat
    notional_base: FiniteFloat


class PositionValuation(PricingBaseModel):
    schema_version: SchemaVersion = VALUATION_SCHEMA_VERSION
    as_of: date
    instrument_id: InstrumentId
    market_data_id: MarketDataId | None = None
    instrument_kind: str
    quantity: FiniteFloat
    instrument_currency: Currency
    unit_price: FiniteFloat | None = None
    notional_native: FiniteFloat
    base_currency: Currency
    fx_asset_id_used: str | None = None
    fx_inverted: bool
    fx_rate_effective: FiniteFloat
    notional_base: FiniteFloat
    inputs: list[ValuationInput] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PortfolioValuation(PricingBaseModel):
    schema_version: SchemaVersion = VALUATION_SCHEMA_VERSION
    as_of: date
    base_currency: Currency
    nav_base: FiniteFloat
    positions: list[PositionValuation]
    breakdown_by_currency: dict[Currency, CurrencyBreakdown]
    warnings: list[str] = Field(default_factory=list)
    lineage: dict[str, str] | None = None


__all__ = [
    "CurrencyBreakdown",
    "PortfolioValuation",
    "PositionValuation",
    "SchemaVersion",
    "ValuationInput",
    "VALUATION_SCHEMA_VERSION",
]
