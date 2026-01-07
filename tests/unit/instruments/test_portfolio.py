from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position


def test_portfolio_rejects_naive_as_of() -> None:
    with pytest.raises(ValidationError):
        Portfolio(as_of=datetime(2024, 1, 1), positions=[], cash={})


def test_portfolio_rejects_duplicate_positions() -> None:
    positions = [
        Position(instrument_id="EQ.AAPL", quantity=1.0),
        Position(instrument_id="EQ.AAPL", quantity=2.0),
    ]
    with pytest.raises(ValidationError):
        Portfolio(
            as_of=datetime(2024, 1, 1, tzinfo=timezone.utc),
            positions=positions,
            cash={},
        )


def test_portfolio_positions_sorted() -> None:
    positions = [
        Position(instrument_id="EQ.MSFT", quantity=1.0),
        Position(instrument_id="EQ.AAPL", quantity=2.0),
    ]
    portfolio = Portfolio(
        as_of=datetime(2024, 1, 1, tzinfo=timezone.utc),
        positions=positions,
        cash={},
    )
    assert [position.instrument_id for position in portfolio.positions] == [
        "EQ.AAPL",
        "EQ.MSFT",
    ]


def test_portfolio_cash_normalized_and_sorted() -> None:
    portfolio = Portfolio(
        as_of=datetime(2024, 1, 1, tzinfo=timezone.utc),
        positions=[],
        cash={"usd": 10.0, "eur": 5.0},
    )
    assert list(portfolio.cash.keys()) == ["EUR", "USD"]


def test_portfolio_rejects_duplicate_cash_currency() -> None:
    with pytest.raises(ValidationError):
        Portfolio(
            as_of=datetime(2024, 1, 1, tzinfo=timezone.utc),
            positions=[],
            cash={"USD": 10.0, "usd": 5.0},
        )
