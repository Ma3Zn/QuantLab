from __future__ import annotations

from math import isfinite
from typing import Mapping

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.value_types import FiniteFloat
from quantlab.stress.errors import StressInputError
from quantlab.stress.scenarios import ShockConvention


def _normalize_convention(convention: ShockConvention | str) -> str:
    return str(convention).upper()


def _require_finite(value: float, label: str) -> float:
    if not isfinite(value):
        raise StressInputError(
            f"{label} must be finite",
            context={"value": value},
        )
    return value


def apply_shock_to_price(
    price: FiniteFloat,
    shock: FiniteFloat,
    convention: ShockConvention | str,
    *,
    allow_negative: bool = False,
) -> float:
    """Apply a single shock to a price using the configured convention."""

    _require_finite(float(price), "price")
    _require_finite(float(shock), "shock")
    if not allow_negative and price < 0:
        raise StressInputError(
            "price must be non-negative",
            context={"price": float(price)},
        )

    normalized = _normalize_convention(convention)
    if normalized == "RETURN_MULTIPLICATIVE":
        shocked_price = float(price) * (1.0 + float(shock))
    elif normalized == "PRICE_MULTIPLIER":
        shocked_price = float(price) * float(shock)
    else:
        raise StressInputError(
            "unknown shock convention",
            context={"shock_convention": normalized},
        )

    _require_finite(shocked_price, "shocked_price")
    if not allow_negative and shocked_price < 0:
        raise StressInputError(
            "shocked_price must be non-negative",
            context={"price": float(price), "shock": float(shock), "shocked_price": shocked_price},
        )
    return float(shocked_price)


def apply_shocks_to_prices(
    prices: Mapping[MarketDataId, FiniteFloat],
    shock_vector: Mapping[MarketDataId, FiniteFloat],
    convention: ShockConvention | str,
    *,
    allow_negative: bool = False,
) -> dict[MarketDataId, float]:
    """Apply a shock vector to a price map, returning shocked prices."""

    if not prices:
        raise StressInputError("prices must be non-empty")
    if not shock_vector:
        raise StressInputError("shock_vector must be non-empty")

    shocked_prices: dict[MarketDataId, float] = {}
    for asset_id, shock in shock_vector.items():
        if asset_id not in prices:
            raise StressInputError(
                "price missing for shock application",
                context={"asset_id": str(asset_id)},
            )
        shocked_prices[asset_id] = apply_shock_to_price(
            prices[asset_id],
            shock,
            convention,
            allow_negative=allow_negative,
        )
    return shocked_prices


__all__ = ["apply_shock_to_price", "apply_shocks_to_prices"]
