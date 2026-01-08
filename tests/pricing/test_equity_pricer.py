from __future__ import annotations

from datetime import date
from typing import Mapping

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.position import Position
from quantlab.instruments.specs import EquitySpec
from quantlab.pricing.errors import MissingPriceError
from quantlab.pricing.fx.converter import FxConverter
from quantlab.pricing.fx.resolver import FX_EURUSD_ASSET_ID, FxRateResolver
from quantlab.pricing.market_data import MarketPoint
from quantlab.pricing.pricers.base import PricingContext
from quantlab.pricing.pricers.equity import EquityPricer
from quantlab.pricing.schemas.valuation import ValuationInput
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


def _equity_instrument(asset_id: str, currency: str) -> Instrument:
    return Instrument(
        instrument_id=asset_id,
        instrument_type=InstrumentType.EQUITY,
        market_data_id=asset_id,
        currency=currency,
        spec=EquitySpec(),
    )


def test_missing_close_raises_missing_price_error() -> None:
    as_of = date(2024, 1, 2)
    market_data = InMemoryMarketData({})
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = EquityPricer()
    instrument = _equity_instrument("EQ.AAPL", "USD")
    position = Position(instrument_id=instrument.instrument_id, quantity=10.0)

    with pytest.raises(MissingPriceError) as excinfo:
        pricer.price(
            position=position,
            instrument=instrument,
            market_data=market_data,
            context=context,
        )

    assert excinfo.value.context["asset_id"] == "EQ.AAPL"
    assert excinfo.value.context["field"] == "close"
    assert excinfo.value.context["as_of"] == as_of.isoformat()
    assert excinfo.value.context["instrument_id"] == "EQ.AAPL"


def test_eur_equity_in_eur_base_skips_fx() -> None:
    as_of = date(2024, 1, 2)
    data = {("EQ.AAPL", "close", as_of): 200.0}
    market_data = InMemoryMarketData(data)
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = EquityPricer()
    instrument = _equity_instrument("EQ.AAPL", "EUR")
    position = Position(instrument_id=instrument.instrument_id, quantity=2.0)

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
    assert valuation.unit_price == 200.0
    assert valuation.inputs == [
        ValuationInput(
            asset_id="EQ.AAPL",
            field="close",
            date=as_of,
            value=200.0,
        )
    ]


def test_usd_equity_in_eur_base_uses_inverted_eurusd() -> None:
    as_of = date(2024, 1, 2)
    data = {
        ("EQ.AAPL", "close", as_of): 150.0,
        (FX_EURUSD_ASSET_ID, "close", as_of): 1.2,
    }
    market_data = InMemoryMarketData(data)
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = EquityPricer()
    instrument = _equity_instrument("EQ.AAPL", "USD")
    position = Position(instrument_id=instrument.instrument_id, quantity=3.0)

    valuation = pricer.price(
        position=position,
        instrument=instrument,
        market_data=market_data,
        context=context,
    )

    assert valuation.fx_asset_id_used == FX_EURUSD_ASSET_ID
    assert valuation.fx_inverted is True
    assert valuation.fx_rate_effective == pytest.approx(1.0 / 1.2)
    assert valuation.notional_base == pytest.approx(375.0)
    assert valuation.warnings == [FX_INVERTED_QUOTE]


@given(
    quantity=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
    scale=st.floats(min_value=0.0, max_value=1e3, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50)
def test_equity_notional_scales_linearly(quantity: float, scale: float) -> None:
    as_of = date(2024, 1, 2)
    data = {("EQ.AAPL", "close", as_of): 123.45}
    market_data = InMemoryMarketData(data)
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = EquityPricer()
    instrument = _equity_instrument("EQ.AAPL", "EUR")

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
