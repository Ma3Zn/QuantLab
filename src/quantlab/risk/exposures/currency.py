from __future__ import annotations

from collections import defaultdict
from typing import Mapping

from quantlab.instruments.value_types import Currency
from quantlab.pricing.schemas.valuation import PortfolioValuation
from quantlab.risk.errors import RiskInputError
from quantlab.risk.schemas.report import CurrencyExposure, RiskWarning


def build_currency_exposures(
    *,
    valuation: PortfolioValuation | None = None,
    notionals: Mapping[Currency, float] | None = None,
) -> tuple[list[CurrencyExposure], list[RiskWarning]]:
    """Build currency exposures from a valuation snapshot or explicit notionals."""
    if valuation is None and notionals is None:
        raise RiskInputError(
            "currency exposures require a valuation snapshot or notionals mapping",
            context={"component": "currency"},
        )

    warnings: list[RiskWarning] = []
    notional_by_currency: dict[Currency, float] = defaultdict(float)

    if valuation is not None:
        for currency, breakdown in valuation.breakdown_by_currency.items():
            notional_by_currency[str(currency)] += float(breakdown.notional_base)
    else:
        assert notionals is not None
        for currency, notional in notionals.items():
            notional_by_currency[str(currency)] += float(notional)

    exposures = _normalize_currency_exposures(notional_by_currency, warnings)
    return exposures, warnings


def _normalize_currency_exposures(
    notional_by_currency: Mapping[Currency, float],
    warnings: list[RiskWarning],
) -> list[CurrencyExposure]:
    if notional_by_currency:
        total = sum(notional_by_currency.values())
    else:
        total = 0.0

    if total > 0.0:
        weights = {
            currency: notional / total for currency, notional in notional_by_currency.items()
        }
    else:
        weights = dict(notional_by_currency)
        if notional_by_currency:
            warnings.append(
                RiskWarning(
                    code="EXPOSURE_NOT_NORMALIZED",
                    message=(
                        "Currency exposures could not be normalized; weights represent raw "
                        "notionals."
                    ),
                    context={"total_notional": total},
                )
            )

    exposures = [
        CurrencyExposure(currency=currency, weight=weight) for currency, weight in weights.items()
    ]
    return sorted(exposures, key=lambda item: item.currency)


__all__ = ["build_currency_exposures"]
