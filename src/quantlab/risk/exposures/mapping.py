from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping, Protocol

from quantlab.instruments.ids import MarketDataId
from quantlab.risk.schemas.report import AssetExposure, RiskWarning

MappedExposureBuckets = dict[str, list[AssetExposure]]


class ExposureMappingProvider(Protocol):
    """Protocol for optional exposure mapping providers (e.g., sector/region taxonomy)."""

    def map_assets(
        self, asset_ids: Iterable[MarketDataId]
    ) -> Mapping[MarketDataId, Mapping[str, str]]:
        """Return mapping dimensions for assets (e.g., {"sector": "Tech"})."""


def build_mapped_exposures(
    *,
    asset_exposures: Iterable[AssetExposure],
    provider: ExposureMappingProvider | None,
) -> tuple[MappedExposureBuckets | None, list[RiskWarning]]:
    """Aggregate asset exposures into mapping buckets when a provider is available."""
    if provider is None:
        warning = RiskWarning(
            code="MAPPING_PROVIDER_MISSING",
            message="Mapped exposures are unavailable without a mapping provider.",
            context={"component": "mapped_exposures"},
        )
        return None, [warning]

    exposures_sorted = sorted(asset_exposures, key=lambda item: item.asset_id)
    asset_ids = [exposure.asset_id for exposure in exposures_sorted]
    mapping = provider.map_assets(asset_ids)

    warnings: list[RiskWarning] = []
    buckets: dict[str, dict[MarketDataId, float]] = defaultdict(dict)

    for exposure in exposures_sorted:
        asset_id = exposure.asset_id
        dimensions = mapping.get(asset_id)
        if not dimensions:
            warnings.append(
                RiskWarning(
                    code="MAPPING_ASSET_MISSING",
                    message="Mapping provider returned no mapping for asset.",
                    context={"asset_id": str(asset_id)},
                )
            )
            continue

        for dimension in sorted(dimensions):
            label = dimensions[dimension]
            if not dimension or not label:
                warnings.append(
                    RiskWarning(
                        code="MAPPING_BUCKET_INVALID",
                        message="Mapping provider returned an invalid bucket label.",
                        context={"asset_id": str(asset_id), "dimension": dimension},
                    )
                )
                continue
            bucket_key = f"{dimension}:{label}"
            buckets[bucket_key][asset_id] = float(exposure.weight)

    mapped: MappedExposureBuckets = {}
    for bucket_key, weights in buckets.items():
        bucket_exposures = [
            AssetExposure(asset_id=asset_id, weight=weight) for asset_id, weight in weights.items()
        ]
        mapped[bucket_key] = sorted(bucket_exposures, key=lambda item: item.asset_id)

    return dict(sorted(mapped.items(), key=lambda item: item[0])), warnings


__all__ = ["ExposureMappingProvider", "MappedExposureBuckets", "build_mapped_exposures"]
