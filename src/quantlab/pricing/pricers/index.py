from __future__ import annotations

from quantlab.instruments.instrument import Instrument
from quantlab.instruments.position import Position
from quantlab.instruments.specs import IndexSpec
from quantlab.pricing.market_data import MarketDataView
from quantlab.pricing.pricers.base import PricingContext
from quantlab.pricing.pricers.equity import EquityPricer
from quantlab.pricing.schemas.valuation import PositionValuation


class IndexPricer:
    """Price tradable index proxies using equity-style pricing."""

    def __init__(self, equity_pricer: EquityPricer | None = None) -> None:
        self._equity_pricer = equity_pricer or EquityPricer()

    def required_fields(self, *, context: PricingContext) -> tuple[str, ...]:
        return self._equity_pricer.required_fields(context=context)

    def price(
        self,
        *,
        position: Position,
        instrument: Instrument,
        market_data: MarketDataView,
        context: PricingContext,
    ) -> PositionValuation:
        if not isinstance(instrument.spec, IndexSpec):
            raise ValueError("IndexPricer requires IndexSpec instruments")
        if not instrument.spec.is_tradable:
            raise ValueError("Index instruments must be tradable to price")
        return self._equity_pricer.price(
            position=position,
            instrument=instrument,
            market_data=market_data,
            context=context,
        )


__all__ = ["IndexPricer"]
