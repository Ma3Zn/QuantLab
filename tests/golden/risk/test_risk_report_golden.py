from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

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

FIXTURE_DIR = Path(__file__).resolve().parent
FIXTURE_NAME = "01_risk_report_static_weights.json"


def _load_fixture() -> dict:
    return json.loads((FIXTURE_DIR / FIXTURE_NAME).read_text(encoding="utf-8"))


def _build_portfolio(as_of: date) -> Portfolio:
    as_of_dt = datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc)
    instruments = {
        "EQ.AAPL": Instrument(
            instrument_id="EQ.AAPL",
            instrument_type=InstrumentType.EQUITY,
            market_data_id=AssetId("EQ.AAPL"),
            currency="USD",
            spec=EquitySpec(),
        ),
        "EQ.MSFT": Instrument(
            instrument_id="EQ.MSFT",
            instrument_type=InstrumentType.EQUITY,
            market_data_id=AssetId("EQ.MSFT"),
            currency="USD",
            spec=EquitySpec(),
        ),
    }
    positions = [
        Position(instrument_id="EQ.AAPL", quantity=10.0, instrument=instruments["EQ.AAPL"]),
        Position(instrument_id="EQ.MSFT", quantity=5.0, instrument=instruments["EQ.MSFT"]),
    ]
    return Portfolio(as_of=as_of_dt, positions=positions, cash={})


def _build_market_data(dates: list[date]) -> TimeSeriesBundle:
    columns = pd.MultiIndex.from_product(
        [["EQ.AAPL", "EQ.MSFT"], ["close"]], names=["asset_id", "field"]
    )
    data = pd.DataFrame(
        [
            [100.0, 200.0],
            [101.0, 198.0],
            [103.0, 199.0],
            [102.0, 201.0],
            [104.0, 203.0],
            [106.0, 202.0],
        ],
        index=dates,
        columns=columns,
    )
    return TimeSeriesBundle(
        data=data,
        assets_meta={AssetId("EQ.AAPL"): {}, AssetId("EQ.MSFT"): {}},
        quality=QualityReport(),
        lineage=LineageMeta(
            request_hash="md_req_hash_demo",
            request_json={"assets": ["EQ.AAPL", "EQ.MSFT"]},
            provider="DEMO",
            ingestion_ts_utc="2024-01-10T00:00:00Z",
            as_of_utc="2024-01-09T00:00:00Z",
            dataset_version="demo.v1",
            code_version=None,
            storage_paths=[],
        ),
    )


def test_risk_report_static_weights_golden() -> None:
    fixture = _load_fixture()
    dates = [
        date(2024, 1, 2),
        date(2024, 1, 3),
        date(2024, 1, 4),
        date(2024, 1, 5),
        date(2024, 1, 8),
        date(2024, 1, 9),
    ]
    as_of = dates[-1]

    portfolio = _build_portfolio(as_of)
    market_data = _build_market_data(dates)
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
        market_data=market_data,
        request=request,
        generated_at_utc=datetime(2024, 1, 10, tzinfo=timezone.utc),
    )

    assert report.to_canonical_dict() == fixture
