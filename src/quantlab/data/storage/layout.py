from __future__ import annotations

from pathlib import Path

from quantlab.data.schemas.requests import AssetId

_MARKET_DIR = "market"
_MANIFESTS_DIR = "manifests"
_DEFAULT_FREQUENCY = "1D"


def _sanitize_component(value: str, name: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    sanitized = value.strip()
    for token in ("/", "\\", ":"):
        sanitized = sanitized.replace(token, "_")
    if sanitized in {".", ".."}:
        raise ValueError(f"{name} must not be a path traversal value")
    return sanitized


def market_cache_root(root_path: Path) -> Path:
    return root_path / _MARKET_DIR


def asset_dir(
    root_path: Path,
    provider: str,
    asset_id: AssetId,
    frequency: str = _DEFAULT_FREQUENCY,
) -> Path:
    provider_dir = _sanitize_component(provider, "provider")
    asset_dirname = _sanitize_component(str(asset_id), "asset_id")
    freq = _sanitize_component(frequency, "frequency")
    return market_cache_root(root_path) / provider_dir / asset_dirname / freq


def asset_cache_path(
    root_path: Path,
    provider: str,
    asset_id: AssetId,
    year: int,
    frequency: str = _DEFAULT_FREQUENCY,
) -> Path:
    if year <= 0:
        raise ValueError("year must be positive")
    return asset_dir(root_path, provider, asset_id, frequency) / f"part-{year}.parquet"


def manifest_path(root_path: Path, request_hash: str) -> Path:
    request = _sanitize_component(request_hash, "request_hash")
    return root_path / _MANIFESTS_DIR / f"{request}.json"
