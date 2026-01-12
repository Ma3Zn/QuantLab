from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from quantlab.data.schemas.bundle import TimeSeriesBundle
from quantlab.data.schemas.lineage import LineageMeta
from quantlab.data.schemas.quality import QualityReport
from quantlab.data.schemas.requests import AssetId
from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position
from quantlab.instruments.specs import EquitySpec
from quantlab.risk.engine import RiskEngine
from quantlab.risk.schemas.request import RiskRequest

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "integration"


def _load_price_bundle() -> tuple[list[date], list[str], TimeSeriesBundle]:
    payload = json.loads((FIXTURE_DIR / "risk_prices.json").read_text(encoding="utf-8"))
    dates = [date.fromisoformat(value) for value in payload["dates"]]
    prices = payload["prices"]
    assets = list(prices.keys())
    columns = pd.MultiIndex.from_product([assets, ["close"]], names=["asset_id", "field"])
    data = [[float(prices[asset][index]) for asset in assets] for index in range(len(dates))]
    frame = pd.DataFrame(data, index=dates, columns=columns)
    bundle = TimeSeriesBundle(
        data=frame,
        assets_meta={AssetId(asset): {} for asset in assets},
        quality=QualityReport(),
        lineage=LineageMeta(
            request_hash="risk_integration_demo",
            request_json={"assets": assets, "field": "close"},
            provider="TEST",
            ingestion_ts_utc="2024-01-10T00:00:00Z",
            as_of_utc="2024-01-09T00:00:00Z",
            dataset_version="fixture.v1",
            code_version=None,
            storage_paths=[],
        ),
    )
    return dates, assets, bundle


def _build_portfolio(as_of: date, assets: list[str]) -> Portfolio:
    as_of_dt = datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc)
    instruments = {
        asset: Instrument(
            instrument_id=asset,
            instrument_type=InstrumentType.EQUITY,
            market_data_id=AssetId(asset),
            currency="USD",
            spec=EquitySpec(),
        )
        for asset in assets
    }
    positions = [
        Position(instrument_id="EQ.AAPL", quantity=10.0, instrument=instruments["EQ.AAPL"]),
        Position(instrument_id="EQ.MSFT", quantity=5.0, instrument=instruments["EQ.MSFT"]),
    ]
    return Portfolio(as_of=as_of_dt, positions=positions, cash={})


def test_risk_pipeline_from_fixture_bundle() -> None:
    dates, assets, bundle = _load_price_bundle()
    as_of = dates[-1]
    portfolio = _build_portfolio(as_of, assets)
    request = RiskRequest(
        as_of=as_of,
        lookback_trading_days=5,
        confidence_levels=(0.8,),
        annualization_factor=252,
        input_mode="STATIC_WEIGHTS_X_ASSET_RETURNS",
        missing_data_policy="ERROR",
    )

    report = RiskEngine().run(
        portfolio=portfolio,
        market_data=bundle,
        request=request,
        generated_at_utc=datetime(2024, 1, 10, tzinfo=timezone.utc),
    )

    assert report.as_of == as_of
    assert report.window.start == dates[0]
    assert report.window.end == dates[-1]
    assert report.metrics.portfolio_vol_annualized is not None
    assert report.metrics.var is not None
    assert report.metrics.es is not None
    assert report.input_lineage is not None
    assert report.input_lineage.market_data_bundle_hash == "risk_integration_demo"
    assert len(report.exposures.by_asset) == 2
    assert sum(exposure.weight for exposure in report.exposures.by_asset) == pytest.approx(1.0)
    assert any(warning.code == "RAW_PRICES" for warning in report.warnings)
