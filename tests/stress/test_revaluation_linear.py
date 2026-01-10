from datetime import date

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.position import Position
from quantlab.instruments.specs import CashSpec, EquitySpec, FutureSpec, IndexSpec
from quantlab.stress.revaluation.linear import linear_position_pnl


def test_linear_revaluation_equity() -> None:
    instrument = Instrument(
        instrument_id="EQ.AAPL",
        instrument_type=InstrumentType.EQUITY,
        market_data_id=MarketDataId("EQ.AAPL"),
        currency="USD",
        spec=EquitySpec(),
    )
    position = Position(
        instrument_id=instrument.instrument_id,
        instrument=instrument,
        quantity=10.0,
    )
    assert instrument.market_data_id is not None
    base_prices = {instrument.market_data_id: 100.0}
    shocked_prices = {instrument.market_data_id: 110.0}

    assert linear_position_pnl(position, base_prices, shocked_prices) == 100.0


def test_linear_revaluation_index() -> None:
    instrument = Instrument(
        instrument_id="IDX.SPX",
        instrument_type=InstrumentType.INDEX,
        market_data_id=MarketDataId("IDX.SPX"),
        currency="USD",
        spec=IndexSpec(is_tradable=True),
    )
    position = Position(
        instrument_id=instrument.instrument_id,
        instrument=instrument,
        quantity=5.0,
    )
    assert instrument.market_data_id is not None
    base_prices = {instrument.market_data_id: 50.0}
    shocked_prices = {instrument.market_data_id: 48.0}

    assert linear_position_pnl(position, base_prices, shocked_prices) == -10.0


def test_linear_revaluation_future() -> None:
    instrument = Instrument(
        instrument_id="FUT.ES",
        instrument_type=InstrumentType.FUTURE,
        market_data_id=MarketDataId("FUT.ES"),
        currency="USD",
        spec=FutureSpec(
            expiry=date(2030, 1, 1),
            multiplier=50.0,
            market_data_binding="REQUIRED",
        ),
    )
    position = Position(
        instrument_id=instrument.instrument_id,
        instrument=instrument,
        quantity=2.0,
    )
    assert instrument.market_data_id is not None
    base_prices = {instrument.market_data_id: 100.0}
    shocked_prices = {instrument.market_data_id: 101.5}

    assert linear_position_pnl(position, base_prices, shocked_prices) == 150.0


def test_linear_revaluation_cash_is_zero() -> None:
    instrument = Instrument(
        instrument_id="CASH.USD",
        instrument_type=InstrumentType.CASH,
        currency="USD",
        spec=CashSpec(market_data_binding="NONE"),
    )
    position = Position(
        instrument_id=instrument.instrument_id,
        instrument=instrument,
        quantity=1.0,
    )

    assert linear_position_pnl(position, {}, {}) == 0.0
