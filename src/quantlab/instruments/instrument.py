from __future__ import annotations

from enum import Enum
from typing import Annotated, Any

from pydantic import Field, model_validator

from quantlab.instruments.errors import (
    InstrumentTypeMismatchError,
    InvalidMarketDataBindingError,
    MissingCurrencyError,
)
from quantlab.instruments.ids import InstrumentId, MarketDataId
from quantlab.instruments.specs import BondSpec, CashSpec, EquitySpec, FutureSpec, IndexSpec
from quantlab.instruments.types import INSTRUMENTS_SCHEMA_VERSION, InstrumentBaseModel
from quantlab.instruments.value_types import Currency

SpecUnion = Annotated[
    EquitySpec | IndexSpec | CashSpec | FutureSpec | BondSpec,
    Field(discriminator="kind"),
]


class InstrumentType(str, Enum):
    EQUITY = "equity"
    INDEX = "index"
    CASH = "cash"
    FUTURE = "future"
    BOND = "bond"


class Instrument(InstrumentBaseModel):
    schema_version: int = INSTRUMENTS_SCHEMA_VERSION
    instrument_id: InstrumentId
    instrument_type: InstrumentType
    market_data_id: MarketDataId | None = None
    currency: Currency | None = None
    spec: SpecUnion
    meta: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _enforce_invariants(self) -> "Instrument":
        instrument_id = str(self.instrument_id)
        if self.spec.kind != self.instrument_type.value:
            raise InstrumentTypeMismatchError(
                instrument_id=instrument_id,
                instrument_type=self.instrument_type.value,
                spec_kind=self.spec.kind,
            )
        if self.instrument_type == InstrumentType.EQUITY:
            if self.market_data_id is None:
                raise InvalidMarketDataBindingError(
                    instrument_id=instrument_id,
                    binding="REQUIRED",
                    market_data_id=None,
                )
        if self.instrument_type == InstrumentType.INDEX:
            if self.spec.is_tradable and self.market_data_id is None:
                raise InvalidMarketDataBindingError(
                    instrument_id=instrument_id,
                    binding="REQUIRED",
                    market_data_id=None,
                )
            if self.spec.is_tradable and self.currency is None:
                raise MissingCurrencyError(
                    instrument_id=instrument_id,
                    instrument_type=self.instrument_type.value,
                )
        if self.instrument_type in {
            InstrumentType.EQUITY,
            InstrumentType.FUTURE,
            InstrumentType.BOND,
        } and self.currency is None:
            raise MissingCurrencyError(
                instrument_id=instrument_id,
                instrument_type=self.instrument_type.value,
            )
        if self.instrument_type == InstrumentType.CASH and self.currency is None:
            raise MissingCurrencyError(
                instrument_id=instrument_id,
                instrument_type=self.instrument_type.value,
            )
        if isinstance(self.spec, (CashSpec, FutureSpec, BondSpec)):
            binding = self.spec.market_data_binding
            if binding == "REQUIRED" and self.market_data_id is None:
                raise InvalidMarketDataBindingError(
                    instrument_id=instrument_id,
                    binding=binding,
                    market_data_id=None,
                )
            if binding == "NONE" and self.market_data_id is not None:
                raise InvalidMarketDataBindingError(
                    instrument_id=instrument_id,
                    binding=binding,
                    market_data_id=str(self.market_data_id),
                )
        return self


__all__ = ["Instrument", "InstrumentType", "SpecUnion"]
