from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from quantlab.data.schemas.errors import DataValidationError
from quantlab.data.schemas.requests import ValidationPolicy
from quantlab.data.transforms.validation import validate_and_flag


def test_validation_nonpositive_raises_by_default() -> None:
    frame = pd.DataFrame(
        {"close": [100.0, 0.0]},
        index=[date(2024, 1, 2), date(2024, 1, 3)],
    )
    frame.attrs["asset_id"] = "EQ:TEST"

    with pytest.raises(DataValidationError):
        validate_and_flag(frame, ValidationPolicy())
