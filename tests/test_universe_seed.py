from __future__ import annotations

from pathlib import Path

from quantlab.data.universe import compute_universe_hash, load_seed_universe
from quantlab.instruments.master import InstrumentType, generate_instrument_id


def _seed_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "seeds" / "universe_v1.yaml"


def test_seed_universe_loader_is_deterministic() -> None:
    snapshot = load_seed_universe(_seed_path())

    assert snapshot.version == "v1"
    assert len(snapshot.instruments) == 12

    reversed_hash = compute_universe_hash(reversed(snapshot.instruments))
    assert reversed_hash == snapshot.universe_hash

    aapl = next(
        record
        for record in snapshot.instruments
        if record.instrument_type == InstrumentType.EQUITY
        and record.mic == "XNYS"
        and record.ticker_norm == "AAPL"
    )
    expected_equity_id = generate_instrument_id("EQUITY|XNYS|AAPL|USD")
    assert aapl.instrument_id == expected_equity_id

    usdjpy = next(
        record
        for record in snapshot.instruments
        if record.instrument_type == InstrumentType.FX_SPOT
        and record.base_ccy == "USD"
        and record.quote_ccy == "JPY"
    )
    expected_fx_id = generate_instrument_id("FX_SPOT|USD|JPY")
    assert usdjpy.instrument_id == expected_fx_id
