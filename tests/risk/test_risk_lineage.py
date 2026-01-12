from __future__ import annotations

from datetime import date, datetime, timezone

from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position
from quantlab.instruments.specs import EquitySpec
from quantlab.risk.engine import _build_input_lineage, _portfolio_snapshot_hash
from quantlab.risk.schemas.request import RiskRequest


def _build_portfolio(as_of: date) -> Portfolio:
    as_of_dt = datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc)
    instrument = Instrument(
        instrument_id="EQ.AAPL",
        instrument_type=InstrumentType.EQUITY,
        market_data_id="EQ.AAPL",
        currency="USD",
        spec=EquitySpec(),
    )
    position = Position(instrument_id="EQ.AAPL", quantity=10.0, instrument=instrument)
    return Portfolio(as_of=as_of_dt, positions=[position], cash={})


def _build_request(as_of: date, *, lineage: dict[str, str] | None = None) -> RiskRequest:
    return RiskRequest(
        as_of=as_of,
        lookback_trading_days=2,
        annualization_factor=252,
        confidence_levels=(0.95,),
        input_mode="STATIC_WEIGHTS_X_ASSET_RETURNS",
        missing_data_policy="ERROR",
        lineage=lineage,
    )


def test_portfolio_snapshot_hash_is_deterministic() -> None:
    as_of = date(2025, 1, 3)
    portfolio_a = _build_portfolio(as_of)
    portfolio_b = _build_portfolio(as_of)

    assert _portfolio_snapshot_hash(portfolio_a) == _portfolio_snapshot_hash(portfolio_b)


def test_input_lineage_respects_portfolio_hash_override() -> None:
    as_of = date(2025, 1, 3)
    portfolio = _build_portfolio(as_of)
    request = _build_request(as_of, lineage={"portfolio_snapshot_hash": "override-hash"})

    lineage = _build_input_lineage(request, market_lineage=None, portfolio=portfolio)

    assert lineage is not None
    assert lineage.portfolio_snapshot_hash == "override-hash"


def test_input_lineage_includes_benchmark_lineage() -> None:
    as_of = date(2025, 1, 3)
    portfolio = _build_portfolio(as_of)
    request = _build_request(
        as_of,
        lineage={"benchmark_id": "BENCH:SPX", "benchmark_hash": "bench-hash"},
    )

    lineage = _build_input_lineage(request, market_lineage=None, portfolio=portfolio)

    assert lineage is not None
    assert lineage.benchmark_id == "BENCH:SPX"
    assert lineage.benchmark_hash == "bench-hash"
