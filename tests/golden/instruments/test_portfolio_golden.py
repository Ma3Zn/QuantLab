from __future__ import annotations

import json
from pathlib import Path

from quantlab.instruments.portfolio import Portfolio

FIXTURES_DIR = Path(__file__).resolve().parent


def _load_fixture(name: str) -> dict:
    fixture_path = FIXTURES_DIR / name
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_portfolio_equity_cash_golden() -> None:
    fixture = _load_fixture("01_portfolio_equity_cash.json")
    portfolio = Portfolio.model_validate(fixture)
    assert portfolio.to_canonical_dict() == fixture


def test_portfolio_future_golden() -> None:
    fixture = _load_fixture("02_portfolio_future.json")
    portfolio = Portfolio.model_validate(fixture)
    assert portfolio.to_canonical_dict() == fixture


def test_portfolio_multi_currency_cash_golden() -> None:
    fixture = _load_fixture("03_portfolio_multi_currency_cash.json")
    portfolio = Portfolio.model_validate(fixture)
    assert portfolio.to_canonical_dict() == fixture
