from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position
from quantlab.instruments.specs import EquitySpec
from quantlab.stress.engine import StressEngine
from quantlab.stress.scenarios import ScenarioSet

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "integration"


def _load_market_state() -> tuple[date, dict[MarketDataId, float]]:
    payload = json.loads((FIXTURE_DIR / "stress_market_state.json").read_text(encoding="utf-8"))
    as_of = date.fromisoformat(payload["as_of"])
    prices = {MarketDataId(asset_id): float(value) for asset_id, value in payload["prices"].items()}
    return as_of, prices


def _load_scenarios() -> ScenarioSet:
    payload = json.loads((FIXTURE_DIR / "stress_scenarios.json").read_text(encoding="utf-8"))
    return ScenarioSet.from_payload(payload)


def _build_portfolio(as_of: date) -> Portfolio:
    as_of_dt = datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc)
    instruments = {
        "EQ.AAPL": Instrument(
            instrument_id="EQ.AAPL",
            instrument_type=InstrumentType.EQUITY,
            market_data_id=MarketDataId("EQ.AAPL"),
            currency="USD",
            spec=EquitySpec(),
        ),
        "EQ.MSFT": Instrument(
            instrument_id="EQ.MSFT",
            instrument_type=InstrumentType.EQUITY,
            market_data_id=MarketDataId("EQ.MSFT"),
            currency="USD",
            spec=EquitySpec(),
        ),
    }
    positions = [
        Position(instrument_id="EQ.AAPL", quantity=10.0, instrument=instruments["EQ.AAPL"]),
        Position(instrument_id="EQ.MSFT", quantity=5.0, instrument=instruments["EQ.MSFT"]),
    ]
    return Portfolio(as_of=as_of_dt, positions=positions, cash={})


def test_stress_pipeline_from_fixtures() -> None:
    as_of, market_state = _load_market_state()
    scenarios = _load_scenarios()
    portfolio = _build_portfolio(as_of)

    report = StressEngine().run(
        portfolio=portfolio,
        market_state=market_state,
        scenarios=scenarios,
        generated_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert report.as_of == as_of
    assert report.summary.worst_scenario_id == "S2"
    assert report.summary.max_loss == pytest.approx(-300.0)
    assert len(report.scenario_results) == 2
    warning_codes = {warning.code for warning in report.warnings}
    assert "NO_PROBABILITIES" in warning_codes
    assert "MISSING_SHOCKS_ASSUMED_ZERO" in warning_codes
