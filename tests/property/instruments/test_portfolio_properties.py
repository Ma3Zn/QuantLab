from __future__ import annotations

import string
from datetime import datetime, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position

_INSTRUMENT_ID_ALPHABET = string.ascii_uppercase + string.digits + "._-"
_INSTRUMENT_ID_CORE = st.text(
    alphabet=_INSTRUMENT_ID_ALPHABET,
    min_size=1,
    max_size=12,
)
INSTRUMENT_IDS = _INSTRUMENT_ID_CORE.map(lambda value: f"EQ.{value}")

QUANTITIES = st.floats(
    min_value=0.0,
    max_value=1_000_000.0,
    allow_nan=False,
    allow_infinity=False,
)
POSITIONS = st.lists(
    st.builds(Position, instrument_id=INSTRUMENT_IDS, quantity=QUANTITIES),
    min_size=0,
    max_size=6,
    unique_by=lambda position: position.instrument_id,
)

CURRENCIES = st.text(alphabet=string.ascii_uppercase, min_size=3, max_size=3)
CASH = st.dictionaries(keys=CURRENCIES, values=QUANTITIES, min_size=0, max_size=6)

AS_OF_TIMESTAMPS = st.datetimes(timezones=st.just(timezone.utc))

NONFINITE_FLOATS = st.sampled_from([float("nan"), float("inf"), -float("inf")])
NEGATIVE_FLOATS = st.floats(
    max_value=-1e-6,
    allow_nan=False,
    allow_infinity=False,
)


@given(as_of=AS_OF_TIMESTAMPS, positions=POSITIONS, cash=CASH)
@settings(max_examples=50, deadline=None)
def test_portfolio_round_trip_preserves_semantics(
    as_of: datetime, positions: list[Position], cash: dict[str, float]
) -> None:
    portfolio = Portfolio(as_of=as_of, positions=positions, cash=cash)
    canonical_json = portfolio.to_canonical_json()
    reloaded = Portfolio.model_validate_json(canonical_json)

    assert reloaded.to_canonical_dict() == portfolio.to_canonical_dict()


@given(as_of=AS_OF_TIMESTAMPS, positions=POSITIONS, cash=CASH)
@settings(max_examples=50, deadline=None)
def test_portfolio_canonical_json_is_deterministic(
    as_of: datetime, positions: list[Position], cash: dict[str, float]
) -> None:
    portfolio_a = Portfolio(as_of=as_of, positions=positions, cash=cash)
    reversed_positions = list(reversed(positions))
    reversed_cash_items = list(reversed(list(cash.items())))
    mixed_case_cash = {currency.lower(): amount for currency, amount in reversed_cash_items}
    portfolio_b = Portfolio(as_of=as_of, positions=reversed_positions, cash=mixed_case_cash)

    assert portfolio_a.to_canonical_json() == portfolio_b.to_canonical_json()


@given(quantity=NONFINITE_FLOATS)
@settings(max_examples=10, deadline=None)
def test_position_rejects_nonfinite_quantity_property(quantity: float) -> None:
    with pytest.raises(ValidationError):
        Position(instrument_id="EQ.TEST", quantity=quantity)


@given(quantity=NEGATIVE_FLOATS)
@settings(max_examples=25, deadline=None)
def test_position_rejects_negative_quantity_property(quantity: float) -> None:
    with pytest.raises(ValidationError):
        Position(instrument_id="EQ.TEST", quantity=quantity)
