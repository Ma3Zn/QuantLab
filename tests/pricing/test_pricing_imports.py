import importlib


def test_pricing_imports_cleanly() -> None:
    modules = [
        "quantlab.pricing",
        "quantlab.pricing.fx",
        "quantlab.pricing.pricers",
        "quantlab.pricing.schemas",
        "quantlab.pricing.adapters",
    ]
    for module in modules:
        assert importlib.import_module(module)
