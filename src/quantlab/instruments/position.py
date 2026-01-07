from __future__ import annotations

from typing import Any

from pydantic import Field

from quantlab.instruments.ids import InstrumentId
from quantlab.instruments.types import InstrumentBaseModel
from quantlab.instruments.value_types import FiniteFloat


class Position(InstrumentBaseModel):
    instrument_id: InstrumentId
    quantity: FiniteFloat = Field(ge=0)
    meta: dict[str, Any] | None = None


__all__ = ["Position"]
