import importlib


def test_stress_imports_cleanly() -> None:
    modules = [
        "quantlab.stress",
        "quantlab.stress.engine",
        "quantlab.stress.errors",
        "quantlab.stress.schemas",
        "quantlab.stress.scenarios",
    ]
    for module in modules:
        assert importlib.import_module(module)
