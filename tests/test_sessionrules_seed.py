from __future__ import annotations

from pathlib import Path

from quantlab.data.sessionrules import (
    compute_sessionrules_hash,
    load_seed_sessionrules,
)


def _seed_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "seeds" / "sessionrules_v1.yaml"


def test_seed_sessionrules_loader_is_deterministic() -> None:
    snapshot = load_seed_sessionrules(_seed_path())

    assert snapshot.version == "v1"
    assert len(snapshot.rules) == 6

    reversed_hash = compute_sessionrules_hash(reversed(snapshot.rules))
    assert reversed_hash == snapshot.sessionrules_hash

    xlon = next(rule for rule in snapshot.rules if rule.mic == "XLON")
    assert xlon.timezone_local == "Europe/London"
    assert xlon.regular_close_local == "16:30"
