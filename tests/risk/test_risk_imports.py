import importlib


def test_risk_imports_cleanly() -> None:
    modules = [
        "quantlab.risk",
        "quantlab.risk.engine",
        "quantlab.risk.errors",
    ]
    for module in modules:
        assert importlib.import_module(module)
