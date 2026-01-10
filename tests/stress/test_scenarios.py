import json
from pathlib import Path

import pytest

from quantlab.stress.errors import StressScenarioError
from quantlab.stress.scenarios import ScenarioSet, scenario_set_hash


def test_scenario_set_example_validates() -> None:
    payload = json.loads(
        Path("docs/stress/examples/stress_scenarios_example.json").read_text(encoding="utf-8")
    )
    scenario_set = ScenarioSet.model_validate(payload)
    assert scenario_set.missing_shock_policy == "ZERO_WITH_WARNING"
    assert len(scenario_set.scenarios) == 3


def test_scenario_set_orders_by_id_and_hashes_deterministically() -> None:
    payload = {
        "as_of": "2025-12-31",
        "missing_shock_policy": "ZERO_WITH_WARNING",
        "scenarios": [
            {
                "scenario_id": "S2",
                "name": "Second scenario",
                "type": "ParametricShock",
                "shock_convention": "RETURN_MULTIPLICATIVE",
                "shock_vector": {"EQ.MSFT": -0.1},
            },
            {
                "scenario_id": "S1",
                "name": "First scenario",
                "type": "ParametricShock",
                "shock_convention": "RETURN_MULTIPLICATIVE",
                "shock_vector": {"EQ.AAPL": -0.05},
            },
        ],
    }
    reversed_payload = {
        "as_of": "2025-12-31",
        "missing_shock_policy": "ZERO_WITH_WARNING",
        "scenarios": list(reversed(payload["scenarios"])),
    }
    scenario_set = ScenarioSet.model_validate(payload)
    reversed_set = ScenarioSet.model_validate(reversed_payload)

    assert [scenario.scenario_id for scenario in scenario_set.scenarios] == ["S1", "S2"]
    assert scenario_set_hash(scenario_set) == scenario_set_hash(reversed_set)


def test_scenario_set_rejects_duplicate_ids() -> None:
    payload = {
        "as_of": "2025-12-31",
        "missing_shock_policy": "ZERO_WITH_WARNING",
        "scenarios": [
            {
                "scenario_id": "DUP",
                "name": "Duplicate scenario",
                "type": "ParametricShock",
                "shock_convention": "RETURN_MULTIPLICATIVE",
                "shock_vector": {"EQ.AAPL": -0.1},
            },
            {
                "scenario_id": "DUP",
                "name": "Duplicate scenario",
                "type": "ParametricShock",
                "shock_convention": "RETURN_MULTIPLICATIVE",
                "shock_vector": {"EQ.MSFT": -0.1},
            },
        ],
    }
    with pytest.raises(StressScenarioError):
        ScenarioSet.from_payload(payload)


def test_scenario_set_rejects_empty_ids() -> None:
    payload = {
        "as_of": "2025-12-31",
        "missing_shock_policy": "ZERO_WITH_WARNING",
        "scenarios": [
            {
                "scenario_id": " ",
                "name": "Bad scenario id",
                "type": "ParametricShock",
                "shock_convention": "RETURN_MULTIPLICATIVE",
                "shock_vector": {"EQ.AAPL": -0.1},
            }
        ],
    }
    with pytest.raises(StressScenarioError):
        ScenarioSet.from_payload(payload)
