from __future__ import annotations

import math

import pytest
from pydantic import TypeAdapter, ValidationError

from quantlab.instruments.types import InstrumentBaseModel
from quantlab.instruments.value_types import Currency, FiniteFloat


class _ExampleValues(InstrumentBaseModel):
    quantity: FiniteFloat
    cash: FiniteFloat


@pytest.mark.parametrize("value", ["EUR", "USD"])
def test_currency_accepts_valid_codes(value: str) -> None:
    adapter = TypeAdapter(Currency)
    assert adapter.validate_python(value) == value


@pytest.mark.parametrize("value", ["eur", "EU", "EURO", " USD", "USD "])
def test_currency_rejects_invalid_codes(value: str) -> None:
    adapter = TypeAdapter(Currency)
    with pytest.raises(ValidationError):
        adapter.validate_python(value)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_finite_float_rejects_nan_and_inf(value: float) -> None:
    with pytest.raises(ValidationError):
        _ExampleValues(quantity=value, cash=1.0)
    with pytest.raises(ValidationError):
        _ExampleValues(quantity=1.0, cash=value)
