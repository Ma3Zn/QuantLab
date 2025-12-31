from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from quantlab.data.schemas.errors import DataValidationError
from quantlab.data.schemas.quality import QualityFlag
from quantlab.data.schemas.requests import AssetId, ValidationPolicy
from quantlab.data.transforms.validation import validate_and_flag


def _frame_with_dupes() -> pd.DataFrame:
    frame = pd.DataFrame(
        {"close": [100.0, 101.0, 102.0]},
        index=[date(2024, 1, 2), date(2024, 1, 2), date(2024, 1, 3)],
    )
    frame.attrs["asset_id"] = "EQ:TEST"
    return frame


def test_validation_dedup_last_keeps_last_value() -> None:
    frame, report = validate_and_flag(
        _frame_with_dupes(),
        ValidationPolicy(deduplicate="LAST", no_nonpositive_prices=False),
    )

    assert frame.loc[date(2024, 1, 2), "close"] == 101.0
    asset = AssetId("EQ:TEST")
    assert report.flag_counts[asset][QualityFlag.DUPLICATE_RESOLVED] == 1
    assert report.actions["deduplicate"] == "LAST"


def test_validation_dedup_first_keeps_first_value() -> None:
    frame, report = validate_and_flag(
        _frame_with_dupes(),
        ValidationPolicy(deduplicate="FIRST", no_nonpositive_prices=False),
    )

    assert frame.loc[date(2024, 1, 2), "close"] == 100.0
    asset = AssetId("EQ:TEST")
    assert report.flag_counts[asset][QualityFlag.DUPLICATE_RESOLVED] == 1


def test_validation_dedup_error_raises() -> None:
    with pytest.raises(DataValidationError):
        validate_and_flag(
            _frame_with_dupes(),
            ValidationPolicy(deduplicate="ERROR", no_nonpositive_prices=False),
        )
