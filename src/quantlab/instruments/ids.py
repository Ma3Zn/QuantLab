from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, NewType

from pydantic import StringConstraints

if TYPE_CHECKING:
    from quantlab.data.schemas.requests import AssetId as MarketDataId
else:
    try:
        from quantlab.data.schemas.requests import AssetId as MarketDataId
    except ModuleNotFoundError:
        try:
            from quantlab.data.ids import AssetId as MarketDataId
        except ModuleNotFoundError:
            MarketDataId = NewType("AssetId", str)


InstrumentId = Annotated[
    str,
    StringConstraints(min_length=1, max_length=64, pattern=r"^\S+$", strict=True),
]
