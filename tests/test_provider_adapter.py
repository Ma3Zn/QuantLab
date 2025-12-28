from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from quantlab.data.errors import ProviderResponseError
from quantlab.data.providers import FetchRequest, LocalFileProviderAdapter, TimeRange
from quantlab.data.storage import store_raw_payload


def _sample_request() -> FetchRequest:
    return FetchRequest(
        dataset_id="md.equity.eod.bars",
        instrument_ids=("EQ-0001",),
        time_range=TimeRange(
            start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end=datetime(2024, 1, 31, tzinfo=timezone.utc),
        ),
        fields=("close",),
    )


def test_local_file_provider_adapter_fetches_payload_and_retains_raw(tmp_path: Path) -> None:
    payload = b'{"ok": true}'
    payload_path = tmp_path / "payload.json"
    payload_path.write_bytes(payload)

    request = _sample_request()
    adapter = LocalFileProviderAdapter(
        provider="TEST",
        endpoint="eod_bars",
        payload_path=payload_path,
        payload_format="json",
    )

    response = adapter.fetch(request)

    assert response.payload == payload
    assert response.request_fingerprint == request.fingerprint()
    assert response.source.provider == "TEST"
    assert response.source.endpoint == "eod_bars"

    raw_root = tmp_path / "raw"
    metadata = {
        "source": {"provider": response.source.provider, "endpoint": response.source.endpoint},
        "fetched_at_ts": response.fetched_at_ts.isoformat(),
    }
    paths = store_raw_payload(
        raw_root,
        "run-1",
        response.request_fingerprint,
        response.payload,
        metadata,
        ext=response.payload_format,
    )

    assert paths.payload_path.read_bytes() == payload


def test_local_file_provider_adapter_missing_payload_raises_provider_error(
    tmp_path: Path,
) -> None:
    adapter = LocalFileProviderAdapter(
        provider="TEST",
        endpoint="eod_bars",
        payload_path=tmp_path / "missing.json",
        payload_format="json",
    )

    with pytest.raises(ProviderResponseError):
        adapter.fetch(_sample_request())
