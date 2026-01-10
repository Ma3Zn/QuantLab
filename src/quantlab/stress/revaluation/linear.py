from __future__ import annotations

from math import isfinite
from typing import Mapping, cast

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.instrument import InstrumentType
from quantlab.instruments.position import Position
from quantlab.instruments.specs import FutureSpec
from quantlab.instruments.value_types import FiniteFloat
from quantlab.stress.errors import StressInputError


def _require_finite(value: float, label: str) -> float:
    if not isfinite(value):
        raise StressInputError(
            f"{label} must be finite",
            context={"value": value},
        )
    return value


def _lookup_price(
    prices: Mapping[MarketDataId, FiniteFloat],
    market_data_id: MarketDataId,
    label: str,
) -> float:
    if market_data_id not in prices:
        raise StressInputError(
            "price missing for revaluation",
            context={"market_data_id": str(market_data_id), "price_set": label},
        )
    return _require_finite(float(prices[market_data_id]), label)


def linear_position_pnl(
    position: Position,
    base_prices: Mapping[MarketDataId, FiniteFloat],
    shocked_prices: Mapping[MarketDataId, FiniteFloat],
) -> float:
    """Compute position-level P&L for linear instruments under shocked prices."""

    if position.instrument is None:
        raise StressInputError(
            "position requires embedded instrument for revaluation",
            context={"instrument_id": str(position.instrument_id)},
        )

    instrument = position.instrument
    if instrument.instrument_type == InstrumentType.CASH:
        return 0.0

    market_data_id = instrument.market_data_id
    if market_data_id is None:
        raise StressInputError(
            "market_data_id required for revaluation",
            context={"instrument_id": str(position.instrument_id)},
        )

    base_price = _lookup_price(base_prices, market_data_id, "base_prices")
    shocked_price = _lookup_price(shocked_prices, market_data_id, "shocked_prices")
    delta_price = shocked_price - base_price
    quantity = _require_finite(float(position.quantity), "quantity")

    if instrument.instrument_type in {InstrumentType.EQUITY, InstrumentType.INDEX}:
        return float(quantity * delta_price)
    if instrument.instrument_type == InstrumentType.FUTURE:
        spec = cast(FutureSpec, instrument.spec)
        multiplier = _require_finite(float(spec.multiplier), "multiplier")
        return float(quantity * multiplier * delta_price)

    raise StressInputError(
        "unsupported instrument type for linear revaluation",
        context={
            "instrument_id": str(position.instrument_id),
            "instrument_type": instrument.instrument_type.value,
        },
    )


__all__ = ["linear_position_pnl"]
