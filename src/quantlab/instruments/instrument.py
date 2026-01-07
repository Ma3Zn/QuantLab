from __future__ import annotations

from enum import Enum
from typing import Annotated, Any

from pydantic import Field, model_validator

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
        if self.spec.kind != self.instrument_type.value:
            raise ValueError("instrument_type must match spec.kind")
        if self.instrument_type in {InstrumentType.EQUITY, InstrumentType.FUTURE}:
            if self.market_data_id is None:
                raise ValueError("market_data_id is required for tradable instruments")
        if self.instrument_type == InstrumentType.INDEX:
            if not isinstance(self.spec, IndexSpec):
                raise ValueError("index instrument must use IndexSpec")
            if self.spec.is_tradable and self.market_data_id is None:
                raise ValueError("market_data_id is required for tradable indexes")
        if self.instrument_type == InstrumentType.CASH and self.currency is None:
            raise ValueError("currency is required for cash instruments")
        return self


__all__ = ["Instrument", "InstrumentType", "SpecUnion"]
