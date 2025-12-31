from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from quantlab.data.schemas.quality import QualityFlag
from quantlab.data.schemas.requests import AssetId, ValidationPolicy
from quantlab.data.transforms.validation import validate_and_flag


def test_quality_report_aggregates_counts_and_examples() -> None:
    frame = pd.DataFrame(
        {"close": [100.0, 150.0, 151.0], "open": [100.0, 150.0, None]},
        index=[date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)],
    )
    frame.attrs["asset_id"] = "EQ:TEST"

    _, report = validate_and_flag(
        frame,
        ValidationPolicy(
            corp_action_jump_threshold=0.40,
            max_abs_return=0.20,
            no_nonpositive_prices=False,
        ),
    )

    asset = AssetId("EQ:TEST")
    assert report.coverage[asset] == pytest.approx(2 / 3)
    assert report.flag_counts[asset][QualityFlag.MISSING] == 1
    assert report.flag_counts[asset][QualityFlag.SUSPECT_CORP_ACTION] == 1
    assert report.flag_counts[asset][QualityFlag.OUTLIER_RETURN] == 1
    assert report.flag_examples[asset][QualityFlag.MISSING] == ["2024-01-04"]
    assert report.flag_examples[asset][QualityFlag.SUSPECT_CORP_ACTION] == ["2024-01-03"]
