from __future__ import annotations

from datetime import date

import pytest

from quantlab.pricing.schemas.valuation import (
    CurrencyBreakdown,
    PortfolioValuation,
    PositionValuation,
    ValuationInput,
)


def _position() -> PositionValuation:
    return PositionValuation(
        as_of=date(2026, 1, 2),
        instrument_id="EQ.AAPL",
        market_data_id="EQ.AAPL",
        instrument_kind="EQUITY",
        quantity=5.0,
        instrument_currency="USD",
        unit_price=200.0,
        notional_native=1000.0,
        base_currency="EUR",
        fx_asset_id_used="FX.EURUSD",
        fx_inverted=True,
        fx_rate_effective=0.9,
        notional_base=900.0,
        inputs=[
            ValuationInput(
                asset_id="EQ.AAPL",
                field="close",
                date=date(2026, 1, 2),
                value=200.0,
            )
        ],
        warnings=["FX_INVERTED_QUOTE"],
    )


def test_position_valuation_json_serializes_dates() -> None:
    position = _position()
    payload = position.model_dump(mode="json")

    assert payload["as_of"] == "2026-01-02"
    assert payload["inputs"][0]["date"] == "2026-01-02"
    assert payload["instrument_id"] == "EQ.AAPL"
    assert payload["schema_version"]


def test_portfolio_valuation_json_serializes_dates() -> None:
    position = _position()
    portfolio = PortfolioValuation(
        as_of=date(2026, 1, 2),
        base_currency="EUR",
        nav_base=900.0,
        positions=[position],
        breakdown_by_currency={
            "USD": CurrencyBreakdown(
                notional_native=1000.0,
                notional_base=900.0,
            )
        },
        warnings=[],
        lineage={"market_data_snapshot_id": "snapshot-1"},
    )

    payload = portfolio.model_dump(mode="json")

    assert payload["as_of"] == "2026-01-02"
    assert payload["positions"][0]["instrument_id"] == "EQ.AAPL"
    assert payload["schema_version"]


def test_non_finite_values_are_rejected() -> None:
    with pytest.raises(ValueError):
        _ = PositionValuation(
            as_of=date(2026, 1, 2),
            instrument_id="EQ.AAPL",
            market_data_id="EQ.AAPL",
            instrument_kind="EQUITY",
            quantity=5.0,
            instrument_currency="USD",
            unit_price=float("nan"),
            notional_native=1000.0,
            base_currency="EUR",
            fx_asset_id_used="FX.EURUSD",
            fx_inverted=True,
            fx_rate_effective=0.9,
            notional_base=900.0,
            inputs=[],
            warnings=[],
        )

    with pytest.raises(ValueError):
        _ = ValuationInput(
            asset_id="FX.EURUSD",
            field="close",
            date=date(2026, 1, 2),
            value=float("inf"),
        )

    with pytest.raises(ValueError):
        _ = PortfolioValuation(
            as_of=date(2026, 1, 2),
            base_currency="EUR",
            nav_base=float("inf"),
            positions=[_position()],
            breakdown_by_currency={},
            warnings=[],
            lineage=None,
        )
