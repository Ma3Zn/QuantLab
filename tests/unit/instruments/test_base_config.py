from __future__ import annotations

import pytest
from pydantic import ValidationError

from quantlab.instruments.types import InstrumentBaseModel


class _ExampleModel(InstrumentBaseModel):
    name: str
    count: int


def test_extra_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        _ExampleModel.model_validate({"name": "test", "count": 1, "extra_field": "nope"})


def test_models_are_immutable() -> None:
    model = _ExampleModel(name="test", count=1)
    with pytest.raises(ValidationError):
        model.name = "changed"
