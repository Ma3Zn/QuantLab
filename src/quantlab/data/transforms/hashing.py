from __future__ import annotations

import hashlib
import json

from quantlab.data.schemas.requests import TimeSeriesRequest


def canonical_request_dict(request: TimeSeriesRequest) -> dict[str, object]:
    """Return a canonical, order-invariant dict for request hashing."""

    return {
        "assets": sorted(str(asset) for asset in request.assets),
        "start": request.start.isoformat(),
        "end": request.end.isoformat(),
        "frequency": request.frequency,
        "fields": sorted(request.fields),
        "price_type": request.price_type,
        "calendar": request.calendar.to_dict() if request.calendar else None,
        "timezone": request.timezone,
        "alignment": request.alignment.to_dict(),
        "missing": request.missing.to_dict(),
        "validate": request.validate.to_dict(),
        "as_of": request.as_of.isoformat() if request.as_of else None,
    }


def request_hash(request: TimeSeriesRequest) -> str:
    """Compute sha256 hash of the canonical request representation."""

    payload = canonical_request_dict(request)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
