from __future__ import annotations

from datetime import date, datetime, timezone
from math import fsum
from typing import Mapping

import pytest

from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position
from quantlab.instruments.specs import EquitySpec
from quantlab.pricing.engine import ValuationEngine
from quantlab.pricing.fx.resolver import FX_EURUSD_ASSET_ID
from quantlab.pricing.market_data import MarketPoint
from quantlab.pricing.pricers.cash import CashPricer
from quantlab.pricing.pricers.equity import EquityPricer
from quantlab.pricing.pricers.registry import PricerRegistry


class InMemoryMarketData:
    def __init__(self, data: Mapping[tuple[str, str, date], float]) -> None:
        self._data = dict(data)

    def get_value(self, asset_id: str, field: str, as_of: date) -> float:
        return self._data[(asset_id, field, as_of)]

    def has_value(self, asset_id: str, field: str, as_of: date) -> bool:
        return (asset_id, field, as_of) in self._data

    def get_point(self, asset_id: str, field: str, as_of: date) -> MarketPoint | None:
        return None


def _equity_instrument(instrument_id: str, currency: str) -> Instrument:
    return Instrument(
        instrument_id=instrument_id,
        instrument_type=InstrumentType.EQUITY,
        market_data_id=instrument_id,
        currency=currency,
        spec=EquitySpec(),
    )


def test_engine_prices_multi_currency_portfolio() -> None:
    as_of = date(2026, 1, 2)
    market_data = InMemoryMarketData(
        {
            ("EQ.SAP", "close", as_of): 120.0,
            ("EQ.AAPL", "close", as_of): 200.0,
            (FX_EURUSD_ASSET_ID, "close", as_of): 1.1,
        }
    )
    instruments = {
        "EQ.SAP": _equity_instrument("EQ.SAP", "EUR"),
        "EQ.AAPL": _equity_instrument("EQ.AAPL", "USD"),
    }
    portfolio = Portfolio(
        as_of=datetime(2026, 1, 2, tzinfo=timezone.utc),
        positions=[
            Position(instrument_id="EQ.SAP", quantity=10.0),
            Position(instrument_id="EQ.AAPL", quantity=5.0),
        ],
        cash={"EUR": 1000.0, "USD": 500.0},
    )

    registry = PricerRegistry(
        {
            "cash": CashPricer(),
            "equity": EquityPricer(),
        }
    )
    engine = ValuationEngine(registry)

    valuation = engine.value_portfolio(
        portfolio=portfolio,
        instruments=instruments,
        market_data=market_data,
        base_currency="EUR",
    )

    assert valuation.as_of == as_of
    assert valuation.nav_base == pytest.approx(3563.6363636364)
    assert valuation.breakdown_by_currency["EUR"].notional_base == pytest.approx(2200.0)
    assert valuation.breakdown_by_currency["USD"].notional_base == pytest.approx(1363.6363636364)
    assert valuation.warnings == ["FX_INVERTED_QUOTE"]
    assert len(valuation.positions) == 4

    by_instrument = {str(position.instrument_id): position for position in valuation.positions}
    assert by_instrument["CASH.USD"].notional_base == pytest.approx(454.5454545455)
    assert by_instrument["EQ.AAPL"].notional_base == pytest.approx(909.0909090909)
    assert "FX_INVERTED_QUOTE" in by_instrument["EQ.AAPL"].warnings


def test_breakdown_totals_match_position_sums() -> None:
    as_of = date(2026, 1, 2)
    market_data = InMemoryMarketData(
        {
            ("EQ.SAP", "close", as_of): 120.0,
            ("EQ.AAPL", "close", as_of): 200.0,
            (FX_EURUSD_ASSET_ID, "close", as_of): 1.1,
        }
    )
    instruments = {
        "EQ.SAP": _equity_instrument("EQ.SAP", "EUR"),
        "EQ.AAPL": _equity_instrument("EQ.AAPL", "USD"),
    }
    portfolio = Portfolio(
        as_of=datetime(2026, 1, 2, tzinfo=timezone.utc),
        positions=[
            Position(instrument_id="EQ.SAP", quantity=10.0),
            Position(instrument_id="EQ.AAPL", quantity=5.0),
        ],
        cash={"EUR": 1000.0, "USD": 500.0},
    )

    registry = PricerRegistry(
        {
            "cash": CashPricer(),
            "equity": EquityPricer(),
        }
    )
    engine = ValuationEngine(registry)

    valuation = engine.value_portfolio(
        portfolio=portfolio,
        instruments=instruments,
        market_data=market_data,
        base_currency="EUR",
    )

    for currency, breakdown in valuation.breakdown_by_currency.items():
        positions = [
            position for position in valuation.positions if position.instrument_currency == currency
        ]
        native_sum = fsum(position.notional_native for position in positions)
        base_sum = fsum(position.notional_base for position in positions)
        assert breakdown.notional_native == pytest.approx(native_sum)
        assert breakdown.notional_base == pytest.approx(base_sum)

    nav_sum = fsum(position.notional_base for position in valuation.positions)
    assert valuation.nav_base == pytest.approx(nav_sum)
