from __future__ import annotations

from datetime import date

import pandas as pd

from quantlab.data.schemas.quality import QualityFlag
from quantlab.data.schemas.requests import AssetId, ValidationPolicy
from quantlab.data.transforms.validation import validate_and_flag


def test_guardrails_flags_suspect_corp_action() -> None:
    frame = pd.DataFrame(
        {"close": [100.0, 50.0, 51.0]},
        index=[date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)],
    )
    frame.attrs["asset_id"] = "EQ:TEST"

    _, report = validate_and_flag(
        frame,
        ValidationPolicy(corp_action_jump_threshold=0.40, no_nonpositive_prices=False),
    )

    asset = AssetId("EQ:TEST")
    assert report.flag_counts[asset][QualityFlag.SUSPECT_CORP_ACTION] == 1
    assert report.flag_examples[asset][QualityFlag.SUSPECT_CORP_ACTION] == ["2024-01-03"]
