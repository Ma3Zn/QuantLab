import pytest

from quantlab.instruments.ids import MarketDataId
from quantlab.stress.errors import StressInputError
from quantlab.stress.shocks import apply_shock_to_price, apply_shocks_to_prices


def test_apply_shock_to_price_return_multiplicative() -> None:
    assert apply_shock_to_price(100.0, -0.1, "RETURN_MULTIPLICATIVE") == 90.0


def test_apply_shock_to_price_price_multiplier() -> None:
    assert apply_shock_to_price(100.0, 0.9, "PRICE_MULTIPLIER") == 90.0


def test_apply_shock_to_price_rejects_negative_shocked_price() -> None:
    with pytest.raises(StressInputError):
        apply_shock_to_price(100.0, -2.0, "RETURN_MULTIPLICATIVE")


def test_apply_shocks_to_prices_requires_price_for_every_shock() -> None:
    prices = {MarketDataId("EQ.AAPL"): 100.0}
    shock_vector = {
        MarketDataId("EQ.AAPL"): -0.05,
        MarketDataId("EQ.MSFT"): -0.1,
    }
    with pytest.raises(StressInputError):
        apply_shocks_to_prices(prices, shock_vector, "RETURN_MULTIPLICATIVE")
