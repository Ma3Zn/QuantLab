from __future__ import annotations

import pytest
from pydantic import ValidationError

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.specs import CashSpec, IndexSpec


def test_instrument_type_mismatch_rejected() -> None:
    with pytest.raises(ValidationError):
        Instrument(
            instrument_id="EQ.AAPL",
            instrument_type=InstrumentType.EQUITY,
            market_data_id=MarketDataId("EQ:AAPL"),
            currency="USD",
            spec=CashSpec(),
        )


def test_index_tradable_policy_enforced() -> None:
    with pytest.raises(ValidationError):
        Instrument(
            instrument_id="IDX.SP500",
            instrument_type=InstrumentType.INDEX,
            market_data_id=None,
            currency=None,
            spec=IndexSpec(is_tradable=True),
        )

    instrument = Instrument(
        instrument_id="IDX.SP500",
        instrument_type=InstrumentType.INDEX,
        market_data_id=None,
        currency=None,
        spec=IndexSpec(is_tradable=False),
    )

    assert instrument.market_data_id is None


def test_cash_currency_required() -> None:
    with pytest.raises(ValidationError):
        Instrument(
            instrument_id="CASH.USD",
            instrument_type=InstrumentType.CASH,
            market_data_id=None,
            currency=None,
            spec=CashSpec(),
        )
