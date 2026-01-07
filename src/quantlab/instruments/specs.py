from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import field_validator

from quantlab.instruments.types import InstrumentBaseModel
from quantlab.instruments.value_types import FiniteFloat


class EquitySpec(InstrumentBaseModel):
    kind: Literal["equity"] = "equity"
    exchange: str | None = None
    country: str | None = None


class IndexSpec(InstrumentBaseModel):
    kind: Literal["index"] = "index"
    is_tradable: bool


class CashSpec(InstrumentBaseModel):
    kind: Literal["cash"] = "cash"


class FutureSpec(InstrumentBaseModel):
    kind: Literal["future"] = "future"
    expiry: date
    multiplier: FiniteFloat
    root: str | None = None
    exchange: str | None = None

    @field_validator("multiplier")
    @classmethod
    def _require_positive_multiplier(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("multiplier must be > 0")
        return value


class BondSpec(InstrumentBaseModel):
    kind: Literal["bond"] = "bond"
    maturity: date
    issuer: str | None = None
    coupon_rate: float | None = None
    coupon_frequency: str | None = None
    day_count: str | None = None


__all__ = [
    "BondSpec",
    "CashSpec",
    "EquitySpec",
    "FutureSpec",
    "IndexSpec",
]
