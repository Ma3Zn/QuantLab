from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Mapping

from quantlab.data.schemas.requests import AssetId
from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position
from quantlab.instruments.specs import EquitySpec
from quantlab.pricing.engine import ValuationEngine
from quantlab.pricing.market_data import MarketPoint
from quantlab.pricing.pricers.cash import CashPricer
from quantlab.pricing.pricers.equity import EquityPricer
from quantlab.pricing.pricers.registry import PricerRegistry

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "docs" / "pricing" / "examples"
PORTFOLIO_FIXTURE = "portfolio_multi_ccy.json"
MARKET_DATA_FIXTURE = "market_data_minimal_multi_ccy.json"
EXPECTED_FIXTURE = "expected_portfolio_valuation_multi_ccy.json"
FLOAT_ROUND_DECIMALS = 10


class InMemoryMarketData:
    def __init__(self, data: Mapping[tuple[str, str, date], float]) -> None:
        self._data = dict(data)

    def get_value(self, asset_id: str, field: str, as_of: date) -> float:
        return self._data[(asset_id, field, as_of)]

    def has_value(self, asset_id: str, field: str, as_of: date) -> bool:
        return (asset_id, field, as_of) in self._data

    def get_point(self, asset_id: str, field: str, as_of: date) -> MarketPoint | None:
        return None


def _load_fixture(name: str) -> dict:
    fixture_path = FIXTURE_DIR / name
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def _as_of_datetime(as_of_str: str) -> datetime:
    as_of_date = date.fromisoformat(as_of_str)
    return datetime.combine(as_of_date, datetime.min.time(), tzinfo=timezone.utc)


def _build_portfolio(fixture: dict) -> tuple[Portfolio, date]:
    as_of = _as_of_datetime(fixture["as_of"])
    cash: dict[str, float] = {}
    positions: list[Position] = []
    for position in fixture["positions"]:
        instrument_id = position["instrument_id"]
        quantity = position["quantity"]
        if instrument_id.startswith("CASH."):
            currency = instrument_id.split(".", 1)[1]
            cash[currency] = quantity
        else:
            positions.append(Position(instrument_id=instrument_id, quantity=quantity))
    return Portfolio(as_of=as_of, positions=positions, cash=cash), as_of.date()


def _build_market_data(fixture: dict) -> tuple[InMemoryMarketData, dict[str, str]]:
    data: dict[tuple[str, str, date], float] = {}
    currencies: dict[str, str] = {}
    for point in fixture["points"]:
        asset_id = point["asset_id"]
        field = point["field"]
        point_date = date.fromisoformat(point["date"])
        data[(asset_id, field, point_date)] = point["value"]
        currency = point.get("currency")
        if currency is not None:
            currencies[asset_id] = currency
    return InMemoryMarketData(data), currencies


def _equity_instrument(instrument_id: str, currency: str) -> Instrument:
    return Instrument(
        instrument_id=instrument_id,
        instrument_type=InstrumentType.EQUITY,
        market_data_id=AssetId(instrument_id),
        currency=currency,
        spec=EquitySpec(),
    )


def _normalize_floats(payload: object) -> object:
    if isinstance(payload, dict):
        return {key: _normalize_floats(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_normalize_floats(item) for item in payload]
    if isinstance(payload, float):
        return round(payload, FLOAT_ROUND_DECIMALS)
    return payload


def test_portfolio_valuation_matches_golden_snapshot() -> None:
    portfolio_fixture = _load_fixture(PORTFOLIO_FIXTURE)
    market_data_fixture = _load_fixture(MARKET_DATA_FIXTURE)
    expected = _load_fixture(EXPECTED_FIXTURE)

    portfolio, as_of = _build_portfolio(portfolio_fixture)
    market_data, currencies = _build_market_data(market_data_fixture)

    instruments = {
        instrument_id: _equity_instrument(instrument_id, currency)
        for instrument_id, currency in sorted(currencies.items())
        if not instrument_id.startswith("FX.")
    }

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
        base_currency=portfolio_fixture["base_currency"],
        as_of=as_of,
        lineage=expected["lineage"],
    )

    payload = valuation.model_dump(mode="json")
    normalized_payload = _normalize_floats(payload)
    normalized_expected = _normalize_floats(expected)

    assert normalized_payload == normalized_expected


def test_pricing_schema_versions_match_expected() -> None:
    expected = _load_fixture(EXPECTED_FIXTURE)
    portfolio_fixture = _load_fixture(PORTFOLIO_FIXTURE)
    market_data_fixture = _load_fixture(MARKET_DATA_FIXTURE)

    portfolio, as_of = _build_portfolio(portfolio_fixture)
    market_data, currencies = _build_market_data(market_data_fixture)

    instruments = {
        instrument_id: _equity_instrument(instrument_id, currency)
        for instrument_id, currency in sorted(currencies.items())
        if not instrument_id.startswith("FX.")
    }

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
        base_currency=portfolio_fixture["base_currency"],
        as_of=as_of,
        lineage=expected["lineage"],
    )

    payload = valuation.model_dump(mode="json")

    assert payload["schema_version"] == expected["schema_version"]
    for position in payload["positions"]:
        assert position["schema_version"] == expected["schema_version"]
