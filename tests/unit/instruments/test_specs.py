from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from quantlab.instruments.specs import BondSpec, CashSpec, FutureSpec, IndexSpec


def test_future_spec_rejects_non_positive_multiplier() -> None:
    expiry = date(2030, 6, 30)
    with pytest.raises(ValidationError):
        FutureSpec(expiry=expiry, multiplier=0.0, market_data_binding="REQUIRED")
    with pytest.raises(ValidationError):
        FutureSpec(expiry=expiry, multiplier=-1.0, market_data_binding="REQUIRED")


def test_required_fields_are_enforced() -> None:
    with pytest.raises(ValidationError):
        IndexSpec()
    with pytest.raises(ValidationError):
        FutureSpec(multiplier=1.0)
    with pytest.raises(ValidationError):
        BondSpec()


def test_cash_spec_requires_market_data_binding() -> None:
    with pytest.raises(ValidationError):
        CashSpec()
