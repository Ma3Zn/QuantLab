from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from quantlab.instruments.instrument import Instrument
from quantlab.instruments.position import Position
from quantlab.instruments.value_types import Currency
from quantlab.pricing.fx.converter import FxConverter
from quantlab.pricing.market_data import MarketDataView
from quantlab.pricing.schemas.valuation import PositionValuation


@dataclass(frozen=True)
class PricingContext:
    as_of: date
    base_currency: Currency
    fx_converter: FxConverter
    price_field: str = "close"


class Pricer(Protocol):
    """Composable pricer contract for deterministic valuation."""

    def required_fields(self, *, context: PricingContext) -> tuple[str, ...]:
        """Declare market data fields required by this pricer."""

    def price(
        self,
        *,
        position: Position,
        instrument: Instrument,
        market_data: MarketDataView,
        context: PricingContext,
    ) -> PositionValuation:
        """Compute a PositionValuation for the given position."""


__all__ = [
    "Pricer",
    "PricingContext",
]
