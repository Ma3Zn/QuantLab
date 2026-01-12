from datetime import date, datetime, timezone

import pytest

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position
from quantlab.instruments.specs import EquitySpec
from quantlab.stress.engine import StressEngine
from quantlab.stress.errors import StressInputError
from quantlab.stress.scenarios import ParametricShock, ScenarioSet


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


def _build_multi_currency_portfolio(as_of: date) -> Portfolio:
    as_of_dt = datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc)
    instruments = {
        "EQ.AAPL": Instrument(
            instrument_id="EQ.AAPL",
            instrument_type=InstrumentType.EQUITY,
            market_data_id=MarketDataId("EQ.AAPL"),
            currency="USD",
            spec=EquitySpec(),
        ),
        "EQ.SAP": Instrument(
            instrument_id="EQ.SAP",
            instrument_type=InstrumentType.EQUITY,
            market_data_id=MarketDataId("EQ.SAP"),
            currency="EUR",
            spec=EquitySpec(),
        ),
    }
    positions = [
        Position(instrument_id="EQ.AAPL", quantity=10.0, instrument=instruments["EQ.AAPL"]),
        Position(instrument_id="EQ.SAP", quantity=8.0, instrument=instruments["EQ.SAP"]),
    ]
    return Portfolio(as_of=as_of_dt, positions=positions, cash={})


def test_stress_engine_missing_shock_policy_error() -> None:
    as_of = date(2025, 12, 31)
    portfolio = _build_portfolio(as_of)
    market_state = {
        MarketDataId("EQ.AAPL"): 100.0,
        MarketDataId("EQ.MSFT"): 200.0,
    }
    scenarios = ScenarioSet(
        as_of=as_of,
        missing_shock_policy="ERROR",
        scenarios=[
            ParametricShock(
                scenario_id="S1",
                name="Incomplete shock",
                shock_convention="RETURN_MULTIPLICATIVE",
                shock_vector={MarketDataId("EQ.AAPL"): -0.1},
            )
        ],
    )

    with pytest.raises(StressInputError):
        StressEngine().run(portfolio=portfolio, market_state=market_state, scenarios=scenarios)


def test_stress_engine_lineage_ids_are_propagated() -> None:
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
                scenario_id="S1",
                name="Broad equity -5%",
                shock_convention="RETURN_MULTIPLICATIVE",
                shock_vector={
                    MarketDataId("EQ.AAPL"): -0.05,
                    MarketDataId("EQ.MSFT"): -0.05,
                },
            )
        ],
    )

    report = StressEngine().run(
        portfolio=portfolio,
        market_state=market_state,
        scenarios=scenarios,
        portfolio_snapshot_id="PORT-123",
        market_state_id="MS-456",
        scenario_set_id="SCEN-789",
    )

    assert report.input_lineage is not None
    assert report.input_lineage.portfolio_snapshot_id == "PORT-123"
    assert report.input_lineage.market_state_id == "MS-456"
    assert report.input_lineage.scenario_set_id == "SCEN-789"


def test_stress_engine_multi_currency_warns_without_fx_policy() -> None:
    as_of = date(2025, 12, 31)
    portfolio = _build_multi_currency_portfolio(as_of)
    market_state = {
        MarketDataId("EQ.AAPL"): 100.0,
        MarketDataId("EQ.SAP"): 80.0,
    }
    scenarios = ScenarioSet(
        as_of=as_of,
        missing_shock_policy="ZERO_WITH_WARNING",
        scenarios=[
            ParametricShock(
                scenario_id="S1",
                name="Mixed currency -5%",
                shock_convention="RETURN_MULTIPLICATIVE",
                shock_vector={
                    MarketDataId("EQ.AAPL"): -0.05,
                    MarketDataId("EQ.SAP"): -0.05,
                },
            )
        ],
    )

    report = StressEngine().run(
        portfolio=portfolio,
        market_state=market_state,
        scenarios=scenarios,
    )

    warning_codes = {warning.code for warning in report.warnings}
    assert "FX_AGGREGATION_UNSUPPORTED" in warning_codes


def test_stress_engine_multi_currency_error_policy_blocks() -> None:
    as_of = date(2025, 12, 31)
    portfolio = _build_multi_currency_portfolio(as_of)
    market_state = {
        MarketDataId("EQ.AAPL"): 100.0,
        MarketDataId("EQ.SAP"): 80.0,
    }
    scenarios = ScenarioSet(
        as_of=as_of,
        missing_shock_policy="ZERO_WITH_WARNING",
        scenarios=[
            ParametricShock(
                scenario_id="S1",
                name="Mixed currency -5%",
                shock_convention="RETURN_MULTIPLICATIVE",
                shock_vector={
                    MarketDataId("EQ.AAPL"): -0.05,
                    MarketDataId("EQ.SAP"): -0.05,
                },
            )
        ],
    )

    with pytest.raises(StressInputError):
        StressEngine().run(
            portfolio=portfolio,
            market_state=market_state,
            scenarios=scenarios,
            fx_aggregation_policy="ERROR",
        )
