from __future__ import annotations

from datetime import date
from typing import Iterable, Mapping

import pytest

from quantlab.data.schemas.requests import AssetId
from quantlab.pricing.schemas.valuation import (
    CurrencyBreakdown,
    PortfolioValuation,
    PositionValuation,
)
from quantlab.risk.exposures.asset import build_asset_exposures
from quantlab.risk.exposures.currency import build_currency_exposures
from quantlab.risk.exposures.mapping import build_mapped_exposures
from quantlab.risk.schemas.report import AssetExposure


def _position(asset_id: str, notional_base: float, currency: str = "USD") -> PositionValuation:
    return PositionValuation(
        as_of=date(2026, 1, 2),
        instrument_id=asset_id,
        market_data_id=AssetId(asset_id),
        instrument_kind="EQUITY",
        quantity=1.0,
        instrument_currency=currency,
        unit_price=100.0,
        notional_native=100.0,
        base_currency="USD",
        fx_asset_id_used=None,
        fx_inverted=False,
        fx_rate_effective=1.0,
        notional_base=notional_base,
        inputs=[],
        warnings=[],
    )


def _portfolio(positions: list[PositionValuation]) -> PortfolioValuation:
    breakdown: dict[str, CurrencyBreakdown] = {
        "JPY": CurrencyBreakdown(notional_native=200.0, notional_base=2.0),
        "USD": CurrencyBreakdown(notional_native=300.0, notional_base=3.0),
    }
    return PortfolioValuation(
        as_of=date(2026, 1, 2),
        base_currency="USD",
        nav_base=5.0,
        positions=positions,
        breakdown_by_currency=breakdown,
        warnings=[],
        lineage=None,
    )


def test_asset_exposures_from_valuation_normalize_and_sort() -> None:
    positions = [
        _position("EQ.MSFT", 3.0),
        _position("EQ.AAPL", 1.0),
    ]
    portfolio = _portfolio(positions)

    exposures, warnings = build_asset_exposures(valuation=portfolio)

    assert warnings == []
    assert [exposure.asset_id for exposure in exposures] == ["EQ.AAPL", "EQ.MSFT"]
    assert sum(exposure.weight for exposure in exposures) == pytest.approx(1.0)
    assert exposures[0].weight == pytest.approx(0.25)
    assert exposures[1].weight == pytest.approx(0.75)


def test_asset_exposures_from_notionals_normalize_and_sort() -> None:
    exposures, warnings = build_asset_exposures(
        notionals={AssetId("EQ.MSFT"): 3.0, AssetId("EQ.AAPL"): 1.0}
    )

    assert warnings == []
    assert [exposure.asset_id for exposure in exposures] == ["EQ.AAPL", "EQ.MSFT"]
    assert sum(exposure.weight for exposure in exposures) == pytest.approx(1.0)


def test_currency_exposures_from_valuation_normalize_and_sort() -> None:
    positions = [_position("EQ.AAPL", 1.0)]
    portfolio = _portfolio(positions)

    exposures, warnings = build_currency_exposures(valuation=portfolio)

    assert warnings == []
    assert [exposure.currency for exposure in exposures] == ["JPY", "USD"]
    assert sum(exposure.weight for exposure in exposures) == pytest.approx(1.0)


def test_currency_exposures_from_notionals_warns_fx_aggregation() -> None:
    exposures, warnings = build_currency_exposures(notionals={"USD": 3.0, "JPY": 2.0})

    assert [warning.code for warning in warnings] == ["FX_AGGREGATION_UNSUPPORTED"]
    assert [exposure.currency for exposure in exposures] == ["JPY", "USD"]


class _FakeMappingProvider:
    def __init__(self, mapping: dict[AssetId, dict[str, str]]) -> None:
        self._mapping = mapping

    def map_assets(self, asset_ids: Iterable[AssetId]) -> Mapping[AssetId, Mapping[str, str]]:
        return {asset_id: self._mapping.get(asset_id, {}) for asset_id in asset_ids}


def test_mapped_exposures_warns_without_provider() -> None:
    exposures = [AssetExposure(asset_id=AssetId("EQ.AAPL"), weight=1.0)]

    mapped, warnings = build_mapped_exposures(asset_exposures=exposures, provider=None)

    assert mapped is None
    assert [warning.code for warning in warnings] == ["MAPPING_PROVIDER_MISSING"]


def test_mapped_exposures_groups_and_sorts_buckets() -> None:
    exposures = [
        AssetExposure(asset_id=AssetId("EQ.MSFT"), weight=0.6),
        AssetExposure(asset_id=AssetId("EQ.AAPL"), weight=0.4),
    ]
    provider = _FakeMappingProvider(
        {
            AssetId("EQ.AAPL"): {"sector": "Tech", "region": "NA"},
            AssetId("EQ.MSFT"): {"sector": "Tech", "region": "NA"},
        }
    )

    mapped, warnings = build_mapped_exposures(asset_exposures=exposures, provider=provider)

    assert warnings == []
    assert mapped is not None
    assert list(mapped.keys()) == ["region:NA", "sector:Tech"]
    assert [exposure.asset_id for exposure in mapped["region:NA"]] == ["EQ.AAPL", "EQ.MSFT"]
    assert sum(exposure.weight for exposure in mapped["sector:Tech"]) == pytest.approx(1.0)
