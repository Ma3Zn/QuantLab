from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from quantlab.instruments.errors import EmbeddedInstrumentMismatchError
from quantlab.instruments.ids import InstrumentId
from quantlab.instruments.instrument import Instrument
from quantlab.instruments.types import INSTRUMENTS_SCHEMA_VERSION, InstrumentBaseModel
from quantlab.instruments.value_types import FiniteFloat


class Position(InstrumentBaseModel):
    schema_version: int = INSTRUMENTS_SCHEMA_VERSION
    instrument_id: InstrumentId
    instrument: Instrument | None = None
    quantity: FiniteFloat = Field(ge=0)
    cost_basis: FiniteFloat | None = None
    meta: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_embedded_instrument(self) -> "Position":
        if self.instrument is None:
            return self
        if self.instrument.instrument_id != self.instrument_id:
            raise EmbeddedInstrumentMismatchError(str(self.instrument_id))
        return self


__all__ = ["Position"]
