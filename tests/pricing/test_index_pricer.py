from __future__ import annotations

from datetime import date
from typing import Mapping

import pytest

from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.position import Position
from quantlab.instruments.specs import IndexSpec
from quantlab.pricing.fx.converter import FxConverter
from quantlab.pricing.fx.resolver import FxRateResolver
from quantlab.pricing.market_data import MarketPoint
from quantlab.pricing.pricers.base import PricingContext
from quantlab.pricing.pricers.index import IndexPricer


class InMemoryMarketData:
    def __init__(self, data: Mapping[tuple[str, str, date], float]) -> None:
        self._data = dict(data)

    def get_value(self, asset_id: str, field: str, as_of: date) -> float:
        return self._data[(asset_id, field, as_of)]

    def has_value(self, asset_id: str, field: str, as_of: date) -> bool:
        return (asset_id, field, as_of) in self._data

    def get_point(self, asset_id: str, field: str, as_of: date) -> MarketPoint | None:
        return None


def _index_instrument(asset_id: str, currency: str | None, *, tradable: bool) -> Instrument:
    return Instrument(
        instrument_id=asset_id,
        instrument_type=InstrumentType.INDEX,
        market_data_id=asset_id if tradable else None,
        currency=currency,
        spec=IndexSpec(is_tradable=tradable),
    )


def test_non_tradable_index_raises_value_error() -> None:
    as_of = date(2024, 1, 2)
    market_data = InMemoryMarketData({})
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = IndexPricer()
    instrument = _index_instrument("IDX.EUROSTOXX", None, tradable=False)
    position = Position(instrument_id=instrument.instrument_id, quantity=1.0)

    with pytest.raises(ValueError, match="tradable"):
        pricer.price(
            position=position,
            instrument=instrument,
            market_data=market_data,
            context=context,
        )


def test_tradable_index_prices_like_equity() -> None:
    as_of = date(2024, 1, 2)
    data = {("IDX.EUROSTOXX", "close", as_of): 4200.0}
    market_data = InMemoryMarketData(data)
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = IndexPricer()
    instrument = _index_instrument("IDX.EUROSTOXX", "EUR", tradable=True)
    position = Position(instrument_id=instrument.instrument_id, quantity=2.0)

    valuation = pricer.price(
        position=position,
        instrument=instrument,
        market_data=market_data,
        context=context,
    )

    assert valuation.instrument_kind == "index"
    assert valuation.unit_price == 4200.0
    assert valuation.notional_native == pytest.approx(8400.0)
    assert valuation.notional_base == pytest.approx(8400.0)
