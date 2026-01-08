from __future__ import annotations

from quantlab.instruments.instrument import Instrument
from quantlab.instruments.position import Position
from quantlab.pricing.market_data import MarketDataView
from quantlab.pricing.pricers.base import PricingContext
from quantlab.pricing.schemas.valuation import PositionValuation


class CashPricer:
    """Price cash positions as quantity * 1.0 in native currency."""

    def required_fields(self, *, context: PricingContext) -> tuple[str, ...]:
        return ()

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
            raise ValueError("Cash instruments must declare a currency")

        unit_price = 1.0
        notional_native = position.quantity * unit_price
        conversion = context.fx_converter.convert(
            notional_native=notional_native,
            native_currency=instrument_currency,
            base_currency=context.base_currency,
            as_of=context.as_of,
            instrument_id=str(instrument.instrument_id),
        )

        return PositionValuation(
            as_of=context.as_of,
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
            inputs=[],
            warnings=list(conversion.warnings),
        )


__all__ = ["CashPricer"]
