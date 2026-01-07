import pytest
from pydantic import ValidationError

from quantlab.instruments.position import Position


def test_position_rejects_negative_quantity() -> None:
    with pytest.raises(ValidationError):
        Position(instrument_id="EQ.AAPL", quantity=-1.0)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_position_rejects_non_finite_quantity(value: float) -> None:
    with pytest.raises(ValidationError):
        Position(instrument_id="EQ.AAPL", quantity=value)
