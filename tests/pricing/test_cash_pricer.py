from __future__ import annotations

from datetime import date
from typing import Mapping

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.position import Position
from quantlab.instruments.specs import CashSpec
from quantlab.pricing.fx.converter import FxConverter
from quantlab.pricing.fx.resolver import FX_EURUSD_ASSET_ID, FxRateResolver
from quantlab.pricing.market_data import MarketPoint
from quantlab.pricing.pricers.base import PricingContext
from quantlab.pricing.pricers.cash import CashPricer
from quantlab.pricing.warnings import FX_INVERTED_QUOTE


class InMemoryMarketData:
    def __init__(self, data: Mapping[tuple[str, str, date], float]) -> None:
        self._data = dict(data)

    def get_value(self, asset_id: str, field: str, as_of: date) -> float:
        return self._data[(asset_id, field, as_of)]

    def has_value(self, asset_id: str, field: str, as_of: date) -> bool:
        return (asset_id, field, as_of) in self._data

    def get_point(self, asset_id: str, field: str, as_of: date) -> MarketPoint | None:
        return None


def _cash_instrument(currency: str) -> Instrument:
    return Instrument(
        instrument_id=f"CASH.{currency}",
        instrument_type=InstrumentType.CASH,
        market_data_id=None,
        currency=currency,
        spec=CashSpec(market_data_binding="NONE"),
    )


def test_eur_cash_in_eur_base_has_no_fx_conversion() -> None:
    as_of = date(2024, 1, 2)
    market_data = InMemoryMarketData({})
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = CashPricer()
    instrument = _cash_instrument("EUR")
    position = Position(instrument_id=instrument.instrument_id, quantity=150.0)

    valuation = pricer.price(
        position=position,
        instrument=instrument,
        market_data=market_data,
        context=context,
    )

    assert valuation.fx_rate_effective == 1.0
    assert valuation.fx_asset_id_used is None
    assert valuation.fx_inverted is False
    assert valuation.notional_base == valuation.notional_native
    assert valuation.unit_price == 1.0


def test_usd_cash_in_eur_base_uses_inverted_eurusd() -> None:
    as_of = date(2024, 1, 2)
    data = {(FX_EURUSD_ASSET_ID, "close", as_of): 1.25}
    market_data = InMemoryMarketData(data)
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = CashPricer()
    instrument = _cash_instrument("USD")
    position = Position(instrument_id=instrument.instrument_id, quantity=100.0)

    valuation = pricer.price(
        position=position,
        instrument=instrument,
        market_data=market_data,
        context=context,
    )

    assert valuation.fx_asset_id_used == FX_EURUSD_ASSET_ID
    assert valuation.fx_inverted is True
    assert valuation.fx_rate_effective == pytest.approx(0.8)
    assert valuation.notional_base == pytest.approx(80.0)
    assert valuation.warnings == [FX_INVERTED_QUOTE]


@given(
    quantity=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
    scale=st.floats(min_value=0.0, max_value=1e3, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50)
def test_cash_notional_scales_linearly(quantity: float, scale: float) -> None:
    as_of = date(2024, 1, 2)
    market_data = InMemoryMarketData({})
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = CashPricer()
    instrument = _cash_instrument("EUR")

    base_position = Position(instrument_id=instrument.instrument_id, quantity=quantity)
    scaled_position = Position(
        instrument_id=instrument.instrument_id,
        quantity=quantity * scale,
    )

    base_val = pricer.price(
        position=base_position,
        instrument=instrument,
        market_data=market_data,
        context=context,
    )
    scaled_val = pricer.price(
        position=scaled_position,
        instrument=instrument,
        market_data=market_data,
        context=context,
    )

    assert scaled_val.notional_native == pytest.approx(base_val.notional_native * scale)
    assert scaled_val.notional_base == pytest.approx(base_val.notional_base * scale)
