from __future__ import annotations

from datetime import date
from typing import Mapping

import pytest

from quantlab.pricing.market_data import MarketDataMeta, MarketDataView, MarketPoint


class InMemoryMarketData:
    def __init__(self, data: Mapping[tuple[str, str, date], float]) -> None:
        self._data = dict(data)

    def get_value(self, asset_id: str, field: str, as_of: date) -> float:
        return self._data[(asset_id, field, as_of)]

    def has_value(self, asset_id: str, field: str, as_of: date) -> bool:
        return (asset_id, field, as_of) in self._data

    def get_point(self, asset_id: str, field: str, as_of: date) -> MarketPoint | None:
        if not self.has_value(asset_id, field, as_of):
            return None
        return MarketPoint(
            value=self._data[(asset_id, field, as_of)],
            meta=MarketDataMeta(
                quality_flags=("IMPUTED",),
                source_date=as_of,
                aligned_date=as_of,
                lineage_ids=("snapshot-1",),
            ),
        )


def _consume(view: MarketDataView) -> float:
    return view.get_value("EQ.AAPL", "close", date(2026, 1, 2))


def test_market_data_view_protocol_is_usable() -> None:
    view = InMemoryMarketData({("EQ.AAPL", "close", date(2026, 1, 2)): 200.0})

    assert isinstance(view, MarketDataView)
    assert view.has_value("EQ.AAPL", "close", date(2026, 1, 2))
    assert _consume(view) == 200.0

    point = view.get_point("EQ.AAPL", "close", date(2026, 1, 2))
    assert point is not None
    assert point.value == 200.0
    assert point.meta is not None
    assert point.meta.quality_flags == ("IMPUTED",)


def test_market_point_rejects_non_finite_values() -> None:
    with pytest.raises(ValueError):
        _ = MarketPoint(value=float("nan"))

    with pytest.raises(ValueError):
        _ = MarketPoint(value=float("inf"))
