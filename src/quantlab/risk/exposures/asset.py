from __future__ import annotations

from collections import defaultdict
from typing import Mapping

from quantlab.instruments.ids import MarketDataId
from quantlab.pricing.schemas.valuation import PortfolioValuation
from quantlab.risk.errors import RiskInputError
from quantlab.risk.schemas.report import AssetExposure, RiskWarning


def build_asset_exposures(
    *,
    valuation: PortfolioValuation | None = None,
    notionals: Mapping[MarketDataId, float] | None = None,
) -> tuple[list[AssetExposure], list[RiskWarning]]:
    """Build asset exposures from a valuation snapshot or explicit notionals."""
    if valuation is None and notionals is None:
        raise RiskInputError(
            "asset exposures require a valuation snapshot or notionals mapping",
            context={"component": "asset"},
        )

    warnings: list[RiskWarning] = []
    notional_by_asset: dict[MarketDataId, float] = defaultdict(float)

    if valuation is not None:
        for position in valuation.positions:
            asset_id = position.market_data_id
            if asset_id is None:
                warnings.append(
                    RiskWarning(
                        code="EXPOSURE_MISSING_MARKET_DATA_ID",
                        message=(
                            "Position valuation missing market_data_id; excluded from asset "
                            "exposure."
                        ),
                        context={"instrument_id": position.instrument_id},
                    )
                )
                continue
            notional_by_asset[MarketDataId(str(asset_id))] += float(position.notional_base)
    else:
        assert notionals is not None
        for asset_id, notional in notionals.items():
            notional_by_asset[MarketDataId(str(asset_id))] += float(notional)

    exposures = _normalize_asset_exposures(notional_by_asset, warnings)
    return exposures, warnings


def _normalize_asset_exposures(
    notional_by_asset: Mapping[MarketDataId, float],
    warnings: list[RiskWarning],
) -> list[AssetExposure]:
    if notional_by_asset:
        total = sum(notional_by_asset.values())
    else:
        total = 0.0

    if total > 0.0:
        weights = {asset_id: notional / total for asset_id, notional in notional_by_asset.items()}
    else:
        weights = dict(notional_by_asset)
        if notional_by_asset:
            warnings.append(
                RiskWarning(
                    code="EXPOSURE_NOT_NORMALIZED",
                    message="Asset exposures could not be normalized; weights represent raw "
                    "notionals.",
                    context={"total_notional": total},
                )
            )

    exposures = [
        AssetExposure(asset_id=asset_id, weight=weight) for asset_id, weight in weights.items()
    ]
    return sorted(exposures, key=lambda item: item.asset_id)


__all__ = ["build_asset_exposures"]
