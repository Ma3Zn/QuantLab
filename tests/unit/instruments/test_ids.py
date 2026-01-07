from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from quantlab.data.schemas.requests import AssetId
from quantlab.instruments.ids import InstrumentId, MarketDataId


def test_instrument_id_accepts_valid_value() -> None:
    adapter = TypeAdapter(InstrumentId)
    assert adapter.validate_python("EQ.AAPL") == "EQ.AAPL"


@pytest.mark.parametrize("value", ["", " ", "EQ. AAPL", "EQ\tAAPL"])
def test_instrument_id_rejects_whitespace_or_empty(value: str) -> None:
    adapter = TypeAdapter(InstrumentId)
    with pytest.raises(ValidationError):
        adapter.validate_python(value)


def test_market_data_id_aliases_asset_id() -> None:
    assert MarketDataId is AssetId
