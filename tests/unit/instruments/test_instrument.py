from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.specs import BondSpec, CashSpec, EquitySpec, FutureSpec, IndexSpec


def test_instrument_type_mismatch_rejected() -> None:
    with pytest.raises(ValidationError):
        Instrument(
            instrument_id="EQ.AAPL",
            instrument_type=InstrumentType.EQUITY,
            market_data_id=MarketDataId("EQ:AAPL"),
            currency="USD",
            spec=CashSpec(market_data_binding="NONE"),
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
            spec=CashSpec(market_data_binding="NONE"),
        )


def test_cash_binding_requires_market_data_id_when_required() -> None:
    with pytest.raises(ValidationError):
        Instrument(
            instrument_id="CASH.USD",
            instrument_type=InstrumentType.CASH,
            market_data_id=None,
            currency="USD",
            spec=CashSpec(market_data_binding="REQUIRED"),
        )


def test_equity_requires_currency() -> None:
    with pytest.raises(ValidationError):
        Instrument(
            instrument_id="EQ.AAPL",
            instrument_type=InstrumentType.EQUITY,
            market_data_id=MarketDataId("EQ:AAPL"),
            currency=None,
            spec=EquitySpec(),
        )


def test_future_requires_currency_and_binding() -> None:
    with pytest.raises(ValidationError):
        Instrument(
            instrument_id="FUT.ES.202603",
            instrument_type=InstrumentType.FUTURE,
            market_data_id=MarketDataId("FUT:ESZ6"),
            currency=None,
            spec=FutureSpec(
                expiry=date(2026, 3, 20),
                multiplier=50.0,
                market_data_binding="REQUIRED",
            ),
        )
    with pytest.raises(ValidationError):
        Instrument(
            instrument_id="FUT.ES.202603",
            instrument_type=InstrumentType.FUTURE,
            market_data_id=MarketDataId("FUT:ESZ6"),
            currency="USD",
            spec=FutureSpec(
                expiry=date(2026, 3, 20),
                multiplier=50.0,
                market_data_binding="NONE",
            ),
        )


def test_bond_binding_requires_market_data_id_policy() -> None:
    with pytest.raises(ValidationError):
        Instrument(
            instrument_id="BOND.ACME.20300101",
            instrument_type=InstrumentType.BOND,
            market_data_id=MarketDataId("BOND:ACME"),
            currency="USD",
            spec=BondSpec(maturity=date(2030, 1, 1), market_data_binding="NONE"),
        )
