from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position
from quantlab.instruments.specs import EquitySpec
from quantlab.stress.engine import StressEngine
from quantlab.stress.scenarios import ParametricShock, ScenarioSet

FIXTURE_DIR = Path(__file__).resolve().parent
FIXTURE_NAME = "01_stress_report_basic.json"


def _load_fixture() -> dict:
    return json.loads((FIXTURE_DIR / FIXTURE_NAME).read_text(encoding="utf-8"))


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


def test_stress_report_golden() -> None:
    fixture = _load_fixture()
    as_of = date(2025, 12, 31)
    portfolio = _build_portfolio(as_of)
    market_state = {
        MarketDataId("EQ.AAPL"): 100.0,
        MarketDataId("EQ.MSFT"): 200.0,
    }
    scenarios = ScenarioSet(
        as_of=as_of,
        missing_shock_policy="ZERO_WITH_WARNING",
        scenarios=[
            ParametricShock(
                scenario_id="S2",
                name="Broad equity -20%",
                shock_convention="RETURN_MULTIPLICATIVE",
                shock_vector={
                    MarketDataId("EQ.AAPL"): -0.2,
                    MarketDataId("EQ.MSFT"): -0.1,
                },
            ),
            ParametricShock(
                scenario_id="S1",
                name="AAPL -10% only",
                shock_convention="RETURN_MULTIPLICATIVE",
                shock_vector={MarketDataId("EQ.AAPL"): -0.1},
            ),
        ],
    )

    report = StressEngine().run(
        portfolio=portfolio,
        market_state=market_state,
        scenarios=scenarios,
        portfolio_snapshot_id="PORT-001",
        market_state_id="MKT-001",
        scenario_set_id="SCEN-001",
        generated_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert report.to_canonical_dict() == fixture
