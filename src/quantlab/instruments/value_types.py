from __future__ import annotations

from math import isfinite
from typing import Annotated

from pydantic import AfterValidator, StringConstraints

Currency = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z]{3}$", strict=True),
]


def _require_finite_float(value: float) -> float:
    if not isfinite(value):
        raise ValueError("value must be finite")
    return value


FiniteFloat = Annotated[float, AfterValidator(_require_finite_float)]
