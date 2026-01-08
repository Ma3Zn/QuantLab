from __future__ import annotations

from typing import cast

import pytest

from quantlab.instruments.instrument import Instrument
from quantlab.instruments.position import Position
from quantlab.pricing.errors import MissingPricerError
from quantlab.pricing.market_data import MarketDataView
from quantlab.pricing.pricers.base import PricingContext
from quantlab.pricing.pricers.registry import PricerRegistry
from quantlab.pricing.schemas.valuation import PositionValuation


class StubPricer:
    def required_fields(self, *, context: PricingContext) -> tuple[str, ...]:
        return (context.price_field,)

    def price(
        self,
        *,
        position: Position,
        instrument: Instrument,
        market_data: MarketDataView,
        context: PricingContext,
    ) -> PositionValuation:
        raise NotImplementedError("stub")


def test_registry_registers_and_resolves_pricers_deterministically() -> None:
    registry = PricerRegistry()
    pricer = StubPricer()

    registry.register("cash", pricer)

    assert cast(StubPricer, registry.resolve("cash")) is pricer
    assert cast(StubPricer, registry.resolve("cash")) is pricer
    assert registry.registered_kinds() == ("cash",)


def test_registry_missing_mapping_raises_typed_error() -> None:
    registry = PricerRegistry()

    with pytest.raises(MissingPricerError) as excinfo:
        registry.resolve("equity")

    assert excinfo.value.context["instrument_kind"] == "equity"
