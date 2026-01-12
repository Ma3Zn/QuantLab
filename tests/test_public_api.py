from quantlab import risk as risk_module
from quantlab import stress as stress_module


def test_risk_public_api_exports() -> None:
    expected = [
        "RiskEngine",
        "RiskError",
        "RiskInputError",
        "RiskComputationError",
        "RiskSchemaError",
        "RiskRequest",
        "RiskReport",
    ]
    assert risk_module.__all__ == expected
    for name in expected:
        assert hasattr(risk_module, name)


def test_stress_public_api_exports() -> None:
    expected = [
        "CustomShockVector",
        "HistoricalShock",
        "MissingShockPolicy",
        "ParametricShock",
        "Scenario",
        "ScenarioSet",
        "ScenarioType",
        "ShockConvention",
        "StressEngine",
        "StressError",
        "StressInputError",
        "StressScenarioError",
        "StressComputationError",
        "StressReport",
        "apply_shock_to_price",
        "apply_shocks_to_prices",
        "scenario_set_hash",
    ]
    assert stress_module.__all__ == expected
    for name in expected:
        assert hasattr(stress_module, name)
