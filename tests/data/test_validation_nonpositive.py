from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from quantlab.data.schemas.errors import DataValidationError
from quantlab.data.schemas.quality import QualityFlag
from quantlab.data.schemas.requests import AssetId, ValidationPolicy
from quantlab.data.transforms.validation import validate_and_flag


@pytest.mark.parametrize("value", [-1.0, 0.0])
def test_validation_nonpositive_raises_by_default(value: float) -> None:
    frame = pd.DataFrame(
        {"close": [100.0, value]},
        index=[date(2024, 1, 2), date(2024, 1, 3)],
    )
    frame.attrs["asset_id"] = "EQ:TEST"

    with pytest.raises(DataValidationError):
        validate_and_flag(frame, ValidationPolicy())


def test_validation_nonpositive_allows_small_positive() -> None:
    frame = pd.DataFrame(
        {"close": [100.0, 0.0001]},
        index=[date(2024, 1, 2), date(2024, 1, 3)],
    )
    frame.attrs["asset_id"] = "EQ:TEST"

    _, report = validate_and_flag(frame, ValidationPolicy())

    asset = AssetId("EQ:TEST")
    assert QualityFlag.NONPOSITIVE_PRICE not in report.flag_counts[asset]
