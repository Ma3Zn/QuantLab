from __future__ import annotations

from math import isfinite

from quantlab.instruments.instrument import Instrument
from quantlab.instruments.position import Position
from quantlab.pricing.errors import MissingPriceError, NonFiniteInputError
from quantlab.pricing.market_data import MarketDataView, market_data_warnings
from quantlab.pricing.pricers.base import PricingContext
from quantlab.pricing.schemas.valuation import PositionValuation, ValuationInput


class EquityPricer:
    """Price equities (and tradable indices) using close prices."""

    def required_fields(self, *, context: PricingContext) -> tuple[str, ...]:
        return (context.price_field,)

    def price(
        self,
        *,
        position: Position,
        instrument: Instrument,
        market_data: MarketDataView,
        context: PricingContext,
    ) -> PositionValuation:
        instrument_currency = instrument.currency
        if instrument_currency is None:
            raise ValueError("Equity instruments must declare a currency")

        market_data_id = instrument.market_data_id
        if market_data_id is None:
            raise ValueError("Equity instruments must declare a market_data_id")

        asset_id = str(market_data_id)
        field = context.price_field
        as_of = context.as_of
        instrument_id = str(instrument.instrument_id)

        if not market_data.has_value(asset_id, field, as_of):
            raise MissingPriceError(
                asset_id=asset_id,
                field=field,
                as_of=as_of,
                instrument_id=instrument_id,
            )

        unit_price = market_data.get_value(asset_id, field, as_of)
        if not isfinite(unit_price):
            raise NonFiniteInputError(
                field=field,
                value=unit_price,
                as_of=as_of,
                instrument_id=instrument_id,
                asset_id=asset_id,
            )

        notional_native = position.quantity * unit_price
        conversion = context.fx_converter.convert(
            notional_native=notional_native,
            native_currency=instrument_currency,
            base_currency=context.base_currency,
            as_of=as_of,
            instrument_id=instrument_id,
        )

        inputs = [
            ValuationInput(
                asset_id=asset_id,
                field=field,
                date=as_of,
                value=unit_price,
            )
        ]

        warnings = market_data_warnings(market_data, asset_id, field, as_of)
        warnings.extend(conversion.warnings)

        return PositionValuation(
            as_of=as_of,
            instrument_id=instrument.instrument_id,
            market_data_id=instrument.market_data_id,
            instrument_kind=instrument.spec.kind,
            quantity=position.quantity,
            instrument_currency=instrument_currency,
            unit_price=unit_price,
            notional_native=conversion.notional_native,
            base_currency=context.base_currency,
            fx_asset_id_used=conversion.fx_asset_id_used,
            fx_inverted=conversion.fx_inverted,
            fx_rate_effective=conversion.fx_rate_effective,
            notional_base=conversion.notional_base,
            inputs=inputs,
            warnings=warnings,
        )


__all__ = ["EquityPricer"]
