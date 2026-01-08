from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite

from quantlab.instruments.value_types import Currency
from quantlab.pricing.errors import InvalidFxRateError, NonFiniteInputError
from quantlab.pricing.fx.resolver import FX_EURUSD_ASSET_ID, FxRateResolver
from quantlab.pricing.warnings import FX_INVERTED_QUOTE


@dataclass(frozen=True)
class FxConversionResult:
    notional_native: float
    notional_base: float
    fx_rate_effective: float
    fx_asset_id_used: str | None
    fx_inverted: bool
    warnings: tuple[str, ...] = ()


class FxConverter:
    """Apply resolved FX rates with numeric hygiene."""

    def __init__(self, resolver: FxRateResolver) -> None:
        self._resolver = resolver

    def convert(
        self,
        *,
        notional_native: float,
        native_currency: Currency,
        base_currency: Currency,
        as_of: date,
        instrument_id: str | None = None,
    ) -> FxConversionResult:
        if not isfinite(notional_native):
            raise NonFiniteInputError(
                field="notional_native",
                value=notional_native,
                as_of=as_of,
                instrument_id=instrument_id,
            )

        rate, fx_asset_id, inverted = self._resolver.effective_rate(
            native_currency=native_currency,
            base_currency=base_currency,
            as_of=as_of,
            instrument_id=instrument_id,
        )
        if not isfinite(rate) or rate <= 0:
            raise InvalidFxRateError(
                asset_id=fx_asset_id or FX_EURUSD_ASSET_ID,
                field=self._resolver.field,
                as_of=as_of,
                rate=rate,
                instrument_id=instrument_id,
            )

        notional_base = notional_native * rate
        if not isfinite(notional_base):
            raise NonFiniteInputError(
                field="notional_base",
                value=notional_base,
                as_of=as_of,
                instrument_id=instrument_id,
            )

        warnings = (FX_INVERTED_QUOTE,) if inverted else ()
        return FxConversionResult(
            notional_native=notional_native,
            notional_base=notional_base,
            fx_rate_effective=rate,
            fx_asset_id_used=fx_asset_id,
            fx_inverted=inverted,
            warnings=warnings,
        )


__all__ = [
    "FxConversionResult",
    "FxConverter",
]
