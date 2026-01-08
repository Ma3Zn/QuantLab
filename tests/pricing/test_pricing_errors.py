from __future__ import annotations

import re
from datetime import date

from quantlab.pricing.errors import (
    InvalidFxRateError,
    MissingFxRateError,
    MissingPriceError,
    NonFiniteInputError,
    UnsupportedCurrencyError,
)
from quantlab.pricing.warnings import ALL_WARNING_CODES


def test_missing_price_error_has_required_context() -> None:
    as_of = date(2024, 1, 5)
    error = MissingPriceError(
        asset_id="EQ.AAPL",
        field="close",
        as_of=as_of,
        instrument_id="inst-1",
    )

    assert error.context["asset_id"] == "EQ.AAPL"
    assert error.context["field"] == "close"
    assert error.context["as_of"] == as_of.isoformat()
    assert error.context["instrument_id"] == "inst-1"


def test_missing_fx_rate_error_has_required_context() -> None:
    as_of = date(2024, 1, 5)
    error = MissingFxRateError(
        asset_id="FX.EURUSD",
        field="close",
        as_of=as_of,
        instrument_id="inst-2",
    )

    assert error.context["asset_id"] == "FX.EURUSD"
    assert error.context["field"] == "close"
    assert error.context["as_of"] == as_of.isoformat()
    assert error.context["instrument_id"] == "inst-2"


def test_unsupported_currency_error_has_required_context() -> None:
    as_of = date(2024, 1, 5)
    error = UnsupportedCurrencyError(
        currency="JPY",
        base_currency="EUR",
        asset_id="EQ.TOYOTA",
        field="close",
        as_of=as_of,
        instrument_id="inst-3",
    )

    assert error.context["asset_id"] == "EQ.TOYOTA"
    assert error.context["field"] == "close"
    assert error.context["as_of"] == as_of.isoformat()
    assert error.context["instrument_id"] == "inst-3"


def test_non_finite_input_error_has_required_context() -> None:
    as_of = date(2024, 1, 5)
    error = NonFiniteInputError(
        field="unit_price",
        value=float("nan"),
        asset_id="EQ.MSFT",
        as_of=as_of,
        instrument_id="inst-4",
    )

    assert error.context["asset_id"] == "EQ.MSFT"
    assert error.context["field"] == "unit_price"
    assert error.context["as_of"] == as_of.isoformat()
    assert error.context["instrument_id"] == "inst-4"


def test_invalid_fx_rate_error_has_required_context() -> None:
    as_of = date(2024, 1, 5)
    error = InvalidFxRateError(
        asset_id="FX.EURUSD",
        field="close",
        as_of=as_of,
        rate=0.0,
        instrument_id="inst-5",
    )

    assert error.context["asset_id"] == "FX.EURUSD"
    assert error.context["field"] == "close"
    assert error.context["as_of"] == as_of.isoformat()
    assert error.context["instrument_id"] == "inst-5"


def test_warning_codes_are_stable_strings() -> None:
    pattern = re.compile(r"^[A-Z0-9_]+$")
    for code in ALL_WARNING_CODES:
        assert code == code.strip()
        assert pattern.fullmatch(code)
