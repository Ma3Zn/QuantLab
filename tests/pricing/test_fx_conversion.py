from __future__ import annotations

from datetime import date
from typing import Mapping

import pytest

from quantlab.pricing.errors import (
    InvalidFxRateError,
    MissingFxRateError,
    UnsupportedCurrencyError,
)
from quantlab.pricing.fx.converter import FxConverter
from quantlab.pricing.fx.resolver import FX_EURUSD_ASSET_ID, FxRateResolver
from quantlab.pricing.market_data import MarketPoint
from quantlab.pricing.warnings import FX_INVERTED_QUOTE


class InMemoryMarketData:
    def __init__(self, data: Mapping[tuple[str, str, date], float]) -> None:
        self._data = dict(data)

    def get_value(self, asset_id: str, field: str, as_of: date) -> float:
        return self._data[(asset_id, field, as_of)]

    def has_value(self, asset_id: str, field: str, as_of: date) -> bool:
        return (asset_id, field, as_of) in self._data

    def get_point(self, asset_id: str, field: str, as_of: date) -> MarketPoint | None:
        return None


def test_eur_to_usd_uses_direct_eurusd_rate() -> None:
    as_of = date(2024, 1, 2)
    data = {(FX_EURUSD_ASSET_ID, "close", as_of): 1.2}
    resolver = FxRateResolver(InMemoryMarketData(data))

    rate, asset_id, inverted, warnings = resolver.effective_rate("EUR", "USD", as_of)

    assert rate == 1.2
    assert asset_id == FX_EURUSD_ASSET_ID
    assert inverted is False
    assert warnings == ()


def test_usd_to_eur_inverts_and_emits_warning() -> None:
    as_of = date(2024, 1, 2)
    data = {(FX_EURUSD_ASSET_ID, "close", as_of): 1.25}
    resolver = FxRateResolver(InMemoryMarketData(data))
    converter = FxConverter(resolver)

    result = converter.convert(
        notional_native=100.0,
        native_currency="USD",
        base_currency="EUR",
        as_of=as_of,
    )

    assert result.fx_asset_id_used == FX_EURUSD_ASSET_ID
    assert result.fx_inverted is True
    assert result.fx_rate_effective == pytest.approx(0.8)
    assert result.warnings == (FX_INVERTED_QUOTE,)
    assert result.notional_base == pytest.approx(80.0)


def test_same_currency_returns_rate_one_with_no_fx_asset() -> None:
    as_of = date(2024, 1, 2)
    resolver = FxRateResolver(InMemoryMarketData({}))

    rate, asset_id, inverted, warnings = resolver.effective_rate("EUR", "EUR", as_of)

    assert rate == 1.0
    assert asset_id is None
    assert inverted is False
    assert warnings == ()


def test_missing_fx_rate_raises() -> None:
    as_of = date(2024, 1, 2)
    resolver = FxRateResolver(InMemoryMarketData({}))

    with pytest.raises(MissingFxRateError):
        resolver.effective_rate("EUR", "USD", as_of)


def test_non_positive_fx_raises() -> None:
    as_of = date(2024, 1, 2)
    data = {(FX_EURUSD_ASSET_ID, "close", as_of): 0.0}
    resolver = FxRateResolver(InMemoryMarketData(data))

    with pytest.raises(InvalidFxRateError):
        resolver.effective_rate("EUR", "USD", as_of)


def test_unsupported_currency_raises() -> None:
    as_of = date(2024, 1, 2)
    resolver = FxRateResolver(InMemoryMarketData({}))

    with pytest.raises(UnsupportedCurrencyError):
        resolver.effective_rate("JPY", "EUR", as_of)
