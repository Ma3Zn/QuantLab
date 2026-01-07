from datetime import date

import pytest
from pydantic import ValidationError

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.position import Position
from quantlab.instruments.specs import CashSpec, FutureSpec


def test_position_rejects_negative_quantity() -> None:
    with pytest.raises(ValidationError):
        Position(instrument_id="EQ.AAPL", quantity=-1.0)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_position_rejects_non_finite_quantity(value: float) -> None:
    with pytest.raises(ValidationError):
        Position(instrument_id="EQ.AAPL", quantity=value)


def test_position_rejects_mismatched_embedded_instrument() -> None:
    instrument = Instrument(
        instrument_id="CASH.USD",
        instrument_type=InstrumentType.CASH,
        market_data_id=None,
        currency="USD",
        spec=CashSpec(market_data_binding="NONE"),
    )
    with pytest.raises(ValidationError):
        Position(
            instrument_id="CASH.EUR",
            instrument=instrument,
            quantity=1.0,
        )


def test_position_cost_basis_requires_finite_value() -> None:
    instrument = Instrument(
        instrument_id="FUT.ES.202603",
        instrument_type=InstrumentType.FUTURE,
        market_data_id=MarketDataId("FUT:ESZ6"),
        currency="USD",
        spec=FutureSpec(
            expiry=date(2026, 3, 20),
            multiplier=50.0,
            market_data_binding="REQUIRED",
        ),
    )
    with pytest.raises(ValidationError):
        Position(
            instrument_id=instrument.instrument_id,
            instrument=instrument,
            quantity=1.0,
            cost_basis=float("nan"),
        )
