from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from quantlab.data.schemas.errors import ProviderFetchError
from quantlab.data.schemas.requests import AssetId


@dataclass(frozen=True)
class SymbolMapper:
    """Resolve internal AssetId values to provider-specific symbols."""

    mapping: Mapping[AssetId, str]

    def resolve(self, asset_id: AssetId) -> str:
        provider_symbol = self.mapping.get(asset_id)
        if provider_symbol:
            return provider_symbol
        provider_symbol = self.mapping.get(AssetId(str(asset_id)))
        if provider_symbol:
            return provider_symbol
        raise ProviderFetchError(
            "missing provider symbol mapping",
            context={"asset_id": str(asset_id)},
        )

    def resolve_many(self, assets: Sequence[AssetId]) -> dict[AssetId, str]:
        resolved: dict[AssetId, str] = {}
        for asset in assets:
            resolved[asset] = self.resolve(asset)
        return resolved


__all__ = ["SymbolMapper"]
