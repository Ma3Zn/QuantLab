"""Public entry points for the stress testing layer."""

from quantlab.stress.engine import FxAggregationPolicy, StressEngine
from quantlab.stress.errors import (
    StressComputationError,
    StressError,
    StressInputError,
    StressScenarioError,
)
from quantlab.stress.scenarios import (
    CustomShockVector,
    HistoricalShock,
    MissingShockPolicy,
    ParametricShock,
    Scenario,
    ScenarioSet,
    ScenarioType,
    ShockConvention,
    scenario_set_hash,
)
from quantlab.stress.schemas import StressReport
from quantlab.stress.shocks import apply_shock_to_price, apply_shocks_to_prices

__all__ = [
    "CustomShockVector",
    "HistoricalShock",
    "MissingShockPolicy",
    "ParametricShock",
    "Scenario",
    "ScenarioSet",
    "ScenarioType",
    "ShockConvention",
    "StressEngine",
    "FxAggregationPolicy",
    "StressError",
    "StressInputError",
    "StressScenarioError",
    "StressComputationError",
    "StressReport",
    "apply_shock_to_price",
    "apply_shocks_to_prices",
    "scenario_set_hash",
]
