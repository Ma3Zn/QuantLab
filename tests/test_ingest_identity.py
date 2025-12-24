from __future__ import annotations

from datetime import datetime, timezone

from quantlab.data.identity import generate_ingest_run_id, request_fingerprint


def test_request_fingerprint_is_key_order_invariant() -> None:
    payload_a = {
        "dataset_id": "md.equity.eod.bars",
        "fields": ["open", "high", "low", "close"],
        "time_range": {"start": "2024-01-01", "end": "2024-01-31"},
        "vendor_overrides": {"limit": 100, "include_adjusted": False},
    }
    payload_b = {
        "vendor_overrides": {"include_adjusted": False, "limit": 100},
        "time_range": {"end": "2024-01-31", "start": "2024-01-01"},
        "fields": ["open", "high", "low", "close"],
        "dataset_id": "md.equity.eod.bars",
    }

    assert request_fingerprint(payload_a) == request_fingerprint(payload_b)


def test_generate_ingest_run_id_format_is_deterministic() -> None:
    started_at = datetime(2025, 12, 24, 7, 10, 3, tzinfo=timezone.utc)

    assert generate_ingest_run_id(started_at, sequence=1) == "ing_20251224_071003Z_0001"
