from __future__ import annotations

from datetime import date
from typing import Mapping

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.position import Position
from quantlab.instruments.specs import FutureSpec
from quantlab.pricing.errors import MissingPriceError, NonFiniteInputError
from quantlab.pricing.fx.converter import FxConverter
from quantlab.pricing.fx.resolver import FxRateResolver
from quantlab.pricing.market_data import MarketPoint
from quantlab.pricing.pricers.base import PricingContext
from quantlab.pricing.pricers.future import FuturePricer
from quantlab.pricing.warnings import FUTURE_MTM_ONLY


class InMemoryMarketData:
    def __init__(self, data: Mapping[tuple[str, str, date], float]) -> None:
        self._data = dict(data)

    def get_value(self, asset_id: str, field: str, as_of: date) -> float:
        return self._data[(asset_id, field, as_of)]

    def has_value(self, asset_id: str, field: str, as_of: date) -> bool:
        return (asset_id, field, as_of) in self._data

    def get_point(self, asset_id: str, field: str, as_of: date) -> MarketPoint | None:
        return None


def _future_instrument(asset_id: str, currency: str, multiplier: float) -> Instrument:
    return Instrument(
        instrument_id=asset_id,
        instrument_type=InstrumentType.FUTURE,
        market_data_id=asset_id,
        currency=currency,
        spec=FutureSpec(
            expiry=date(2024, 12, 20),
            multiplier=multiplier,
            market_data_binding="REQUIRED",
        ),
    )


def test_future_notional_includes_multiplier() -> None:
    as_of = date(2024, 1, 2)
    data = {("FUT.ES", "close", as_of): 100.0}
    market_data = InMemoryMarketData(data)
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = FuturePricer()
    instrument = _future_instrument("FUT.ES", "EUR", multiplier=50.0)
    position = Position(instrument_id=instrument.instrument_id, quantity=2.0)

    valuation = pricer.price(
        position=position,
        instrument=instrument,
        market_data=market_data,
        context=context,
    )

    assert valuation.notional_native == pytest.approx(100.0 * 2.0 * 50.0)
    assert valuation.notional_base == valuation.notional_native
    assert valuation.warnings == [FUTURE_MTM_ONLY]


def test_missing_close_raises_missing_price_error() -> None:
    as_of = date(2024, 1, 2)
    market_data = InMemoryMarketData({})
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = FuturePricer()
    instrument = _future_instrument("FUT.ES", "EUR", multiplier=50.0)
    position = Position(instrument_id=instrument.instrument_id, quantity=1.0)

    with pytest.raises(MissingPriceError) as excinfo:
        pricer.price(
            position=position,
            instrument=instrument,
            market_data=market_data,
            context=context,
        )

    assert excinfo.value.context["asset_id"] == "FUT.ES"
    assert excinfo.value.context["field"] == "close"
    assert excinfo.value.context["as_of"] == as_of.isoformat()
    assert excinfo.value.context["instrument_id"] == "FUT.ES"


def test_non_finite_close_raises_non_finite_input_error() -> None:
    as_of = date(2024, 1, 2)
    market_data = InMemoryMarketData({("FUT.ES", "close", as_of): float("nan")})
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = FuturePricer()
    instrument = _future_instrument("FUT.ES", "EUR", multiplier=50.0)
    position = Position(instrument_id=instrument.instrument_id, quantity=1.0)

    with pytest.raises(NonFiniteInputError) as excinfo:
        pricer.price(
            position=position,
            instrument=instrument,
            market_data=market_data,
            context=context,
        )

    assert excinfo.value.context["asset_id"] == "FUT.ES"
    assert excinfo.value.context["field"] == "close"
    assert excinfo.value.context["as_of"] == as_of.isoformat()
    assert excinfo.value.context["instrument_id"] == "FUT.ES"


def test_future_spec_requires_positive_multiplier() -> None:
    with pytest.raises(ValueError, match="multiplier must be > 0"):
        _future_instrument("FUT.BAD", "EUR", multiplier=0.0)


@given(
    quantity=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
    scale=st.floats(min_value=0.0, max_value=1e3, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50)
def test_future_notional_scales_linearly(quantity: float, scale: float) -> None:
    as_of = date(2024, 1, 2)
    data = {("FUT.ES", "close", as_of): 123.45}
    market_data = InMemoryMarketData(data)
    resolver = FxRateResolver(market_data)
    context = PricingContext(
        as_of=as_of,
        base_currency="EUR",
        fx_converter=FxConverter(resolver),
    )
    pricer = FuturePricer()
    instrument = _future_instrument("FUT.ES", "EUR", multiplier=25.0)

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
