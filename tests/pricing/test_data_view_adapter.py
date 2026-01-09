from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from quantlab.data.canonical import CanonicalDataset
from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position
from quantlab.instruments.specs import EquitySpec
from quantlab.pricing.adapters.data_view import CanonicalDataView
from quantlab.pricing.engine import ValuationEngine
from quantlab.pricing.errors import MissingPriceError
from quantlab.pricing.fx.resolver import FX_EURUSD_ASSET_ID
from quantlab.pricing.pricers.equity import EquityPricer
from quantlab.pricing.pricers.registry import PricerRegistry

FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "golden"


def _parse_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        if "T" in value:
            return datetime.fromisoformat(value).date()
        return date.fromisoformat(value)
    raise ValueError("unsupported date value")


def _load_dataset(name: str) -> CanonicalDataset:
    return CanonicalDataset.from_snapshot_dir(FIXTURE_ROOT / name)


def test_adapter_prices_from_canonical_fixtures() -> None:
    equity_dataset = _load_dataset("md.equity.eod.bars")
    fx_dataset = _load_dataset("md.fx.spot.daily")
    view = CanonicalDataView([equity_dataset, fx_dataset])

    equity_row = equity_dataset.frame.iloc[0]
    equity_id = str(equity_row["instrument_id"])
    as_of = _parse_date(equity_row["trading_date_local"] or equity_row["ts"])
    equity_price = float(equity_row["bar_close"])
    fx_row = fx_dataset.frame.iloc[0]
    fx_price = float(fx_row["value"])

    instrument = Instrument(
        instrument_id=equity_id,
        instrument_type=InstrumentType.EQUITY,
        market_data_id=equity_id,
        currency=str(equity_row["currency"]),
        spec=EquitySpec(),
    )
    portfolio = Portfolio(
        as_of=datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc),
        positions=[Position(instrument_id=equity_id, quantity=2.0)],
        cash={},
    )

    registry = PricerRegistry({"equity": EquityPricer()})
    engine = ValuationEngine(registry)

    valuation = engine.value_portfolio(
        portfolio=portfolio,
        instruments={equity_id: instrument},
        market_data=view,
        base_currency="EUR",
        lineage=view.lineage,
    )

    assert view.get_value(FX_EURUSD_ASSET_ID, "close", as_of) == pytest.approx(fx_price)
    assert valuation.nav_base == pytest.approx(2.0 * equity_price / fx_price)
    assert valuation.lineage == view.lineage
    assert valuation.positions[0].fx_asset_id_used == FX_EURUSD_ASSET_ID
    assert "FX_INVERTED_QUOTE" in valuation.positions[0].warnings


def test_adapter_missing_value_raises_typed_error() -> None:
    dataset = _load_dataset("md.equity.eod.bars")
    view = CanonicalDataView([dataset])

    with pytest.raises(MissingPriceError):
        view.get_value("MISSING.ASSET", "close", date(2024, 1, 2))
