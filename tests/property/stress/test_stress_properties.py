from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any

from hypothesis import given, seed, settings
from hypothesis import strategies as st

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position
from quantlab.instruments.specs import EquitySpec
from quantlab.stress.engine import StressEngine
from quantlab.stress.scenarios import ParametricShock, ScenarioSet

_AS_OF_DATE = date(2025, 1, 1)
_AS_OF_DATETIME = datetime(2025, 1, 1, tzinfo=timezone.utc)
_GENERATED_AT = datetime(2025, 1, 2, tzinfo=timezone.utc)

_ASSET_IDS = st.lists(
    st.integers(min_value=1, max_value=9999),
    min_size=1,
    max_size=4,
    unique=True,
)
_PRICES = st.floats(min_value=1.0, max_value=500.0, allow_nan=False, allow_infinity=False)
_QUANTITIES = st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False)
_SHOCKS = st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False)


@st.composite
def _stress_fixture(
    draw: Any,
    *,
    min_scenarios: int = 1,
    max_scenarios: int = 4,
) -> tuple[Portfolio, dict[MarketDataId, float], list[ParametricShock]]:
    asset_tokens = draw(_ASSET_IDS)
    asset_ids = [f"EQ.{token}" for token in asset_tokens]
    market_ids = [MarketDataId(asset_id) for asset_id in asset_ids]

    prices = draw(st.lists(_PRICES, min_size=len(asset_ids), max_size=len(asset_ids)))
    quantities = draw(st.lists(_QUANTITIES, min_size=len(asset_ids), max_size=len(asset_ids)))

    positions: list[Position] = []
    market_state: dict[MarketDataId, float] = {}
    for asset_id, market_id, price, quantity in zip(
        asset_ids, market_ids, prices, quantities, strict=True
    ):
        instrument = Instrument(
            instrument_id=asset_id,
            instrument_type=InstrumentType.EQUITY,
            market_data_id=market_id,
            currency="USD",
            spec=EquitySpec(),
        )
        positions.append(
            Position(
                instrument_id=asset_id,
                quantity=quantity,
                instrument=instrument,
            )
        )
        market_state[market_id] = price

    portfolio = Portfolio(as_of=_AS_OF_DATETIME, positions=positions, cash={})

    scenario_count = draw(st.integers(min_value=min_scenarios, max_value=max_scenarios))
    scenarios: list[ParametricShock] = []
    for idx in range(scenario_count):
        shocks = draw(st.lists(_SHOCKS, min_size=len(asset_ids), max_size=len(asset_ids)))
        shock_vector = {
            market_id: shock for market_id, shock in zip(market_ids, shocks, strict=True)
        }
        scenarios.append(
            ParametricShock(
                scenario_id=f"S{idx + 1}",
                name=f"Scenario {idx + 1}",
                shock_convention="RETURN_MULTIPLICATIVE",
                shock_vector=shock_vector,
            )
        )

    return portfolio, market_state, scenarios


@seed(20240510)
@given(fixture=_stress_fixture())
@settings(max_examples=20, deadline=None)
def test_stress_breakdowns_sum_to_totals(
    fixture: tuple[Portfolio, dict[MarketDataId, float], list[ParametricShock]],
) -> None:
    portfolio, market_state, scenarios = fixture
    scenario_set = ScenarioSet(
        as_of=_AS_OF_DATE,
        shock_convention="RETURN_MULTIPLICATIVE",
        missing_shock_policy="ZERO_WITH_WARNING",
        scenarios=scenarios,
    )
    report = StressEngine().run(
        portfolio=portfolio,
        market_state=market_state,
        scenarios=scenario_set,
        generated_at_utc=_GENERATED_AT,
    )

    totals = {result.scenario_id: float(result.pnl) for result in report.scenario_results}
    by_position: dict[str, float] = defaultdict(float)
    by_asset: dict[str, float] = defaultdict(float)
    by_currency: dict[str, float] = defaultdict(float)

    for entry in report.breakdowns.by_position:
        by_position[entry.scenario_id] += float(entry.pnl)
    for entry in report.breakdowns.by_asset:
        by_asset[entry.scenario_id] += float(entry.pnl)
    for entry in report.breakdowns.by_currency:
        by_currency[entry.scenario_id] += float(entry.pnl)

    tolerance = 1e-9
    for scenario_id, total in totals.items():
        assert abs(by_position.get(scenario_id, 0.0) - total) <= tolerance
        assert abs(by_asset.get(scenario_id, 0.0) - total) <= tolerance
        assert abs(by_currency.get(scenario_id, 0.0) - total) <= tolerance


@seed(20240511)
@given(fixture=_stress_fixture(min_scenarios=2))
@settings(max_examples=20, deadline=None)
def test_scenario_ordering_invariance(
    fixture: tuple[Portfolio, dict[MarketDataId, float], list[ParametricShock]],
) -> None:
    portfolio, market_state, scenarios = fixture
    scenario_set_a = ScenarioSet(
        as_of=_AS_OF_DATE,
        shock_convention="RETURN_MULTIPLICATIVE",
        missing_shock_policy="ZERO_WITH_WARNING",
        scenarios=scenarios,
    )
    scenario_set_b = ScenarioSet(
        as_of=_AS_OF_DATE,
        shock_convention="RETURN_MULTIPLICATIVE",
        missing_shock_policy="ZERO_WITH_WARNING",
        scenarios=list(reversed(scenarios)),
    )

    engine = StressEngine()
    report_a = engine.run(
        portfolio=portfolio,
        market_state=market_state,
        scenarios=scenario_set_a,
        generated_at_utc=_GENERATED_AT,
    )
    report_b = engine.run(
        portfolio=portfolio,
        market_state=market_state,
        scenarios=scenario_set_b,
        generated_at_utc=_GENERATED_AT,
    )

    assert report_a.to_canonical_dict() == report_b.to_canonical_dict()
