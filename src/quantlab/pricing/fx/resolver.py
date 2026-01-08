from __future__ import annotations

from datetime import date
from math import isfinite
from typing import NamedTuple

from quantlab.instruments.value_types import Currency
from quantlab.pricing.errors import (
    InvalidFxRateError,
    MissingFxRateError,
    UnsupportedCurrencyError,
)
from quantlab.pricing.market_data import MarketDataView

FX_EURUSD_ASSET_ID = "FX.EURUSD"
SUPPORTED_CURRENCIES = ("EUR", "USD")


class FxRateResolution(NamedTuple):
    rate: float
    fx_asset_id: str | None
    inverted: bool


class FxRateResolver:
    """Resolve the effective FX rate for EUR/USD Policy B."""

    def __init__(self, market_data: MarketDataView, field: str = "close") -> None:
        self._market_data = market_data
        self._field = field

    @property
    def field(self) -> str:
        return self._field

    def effective_rate(
        self,
        native_currency: Currency,
        base_currency: Currency,
        as_of: date,
        instrument_id: str | None = None,
    ) -> FxRateResolution:
        self._ensure_supported(native_currency, base_currency, as_of, instrument_id)

        if native_currency == base_currency:
            return FxRateResolution(rate=1.0, fx_asset_id=None, inverted=False)

        eurusd = self._get_eurusd_rate(as_of, instrument_id)
        if native_currency == "EUR" and base_currency == "USD":
            return FxRateResolution(
                rate=eurusd,
                fx_asset_id=FX_EURUSD_ASSET_ID,
                inverted=False,
            )
        if native_currency == "USD" and base_currency == "EUR":
            return FxRateResolution(
                rate=1.0 / eurusd,
                fx_asset_id=FX_EURUSD_ASSET_ID,
                inverted=True,
            )
        raise UnsupportedCurrencyError(
            currency=native_currency,
            base_currency=base_currency,
            as_of=as_of,
            instrument_id=instrument_id,
        )

    def _ensure_supported(
        self,
        native_currency: Currency,
        base_currency: Currency,
        as_of: date,
        instrument_id: str | None,
    ) -> None:
        if native_currency not in SUPPORTED_CURRENCIES:
            raise UnsupportedCurrencyError(
                currency=native_currency,
                base_currency=base_currency,
                as_of=as_of,
                instrument_id=instrument_id,
            )
        if base_currency not in SUPPORTED_CURRENCIES:
            raise UnsupportedCurrencyError(
                currency=base_currency,
                base_currency=base_currency,
                as_of=as_of,
                instrument_id=instrument_id,
            )

    def _get_eurusd_rate(self, as_of: date, instrument_id: str | None) -> float:
        asset_id = FX_EURUSD_ASSET_ID
        field = self._field
        if not self._market_data.has_value(asset_id, field, as_of):
            raise MissingFxRateError(
                asset_id=asset_id,
                field=field,
                as_of=as_of,
                instrument_id=instrument_id,
            )

        rate = self._market_data.get_value(asset_id, field, as_of)
        if not isfinite(rate) or rate <= 0:
            raise InvalidFxRateError(
                asset_id=asset_id,
                field=field,
                as_of=as_of,
                rate=rate,
                instrument_id=instrument_id,
            )
        return rate


__all__ = [
    "FX_EURUSD_ASSET_ID",
    "SUPPORTED_CURRENCIES",
    "FxRateResolution",
    "FxRateResolver",
]
