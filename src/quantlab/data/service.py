from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

import pandas as pd

from quantlab.data.logging import get_logger
from quantlab.data.providers import EodProvider, SymbolMapper
from quantlab.data.schemas.bundle import TimeSeriesBundle
from quantlab.data.schemas.errors import DataValidationError, ProviderFetchError
from quantlab.data.schemas.lineage import LineageMeta
from quantlab.data.schemas.quality import QualityReport
from quantlab.data.schemas.requests import AssetId, CalendarSpec, TimeSeriesRequest
from quantlab.data.storage.layout import manifest_path
from quantlab.data.storage.manifests import read_manifest, write_manifest
from quantlab.data.storage.parquet_store import ParquetMarketDataStore
from quantlab.data.transforms.alignment import align_frame
from quantlab.data.transforms.validation import validate_and_flag
from quantlab.data.transforms.hashing import request_hash
from quantlab.data.transforms.calendars import TradingCalendar

CalendarFactory = Callable[[CalendarSpec], TradingCalendar]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(dt: datetime, name: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise ValueError(f"{name} must be timezone-aware and in UTC")


def _normalize_provider_columns(frame: pd.DataFrame) -> pd.DataFrame:
    if isinstance(frame.columns, pd.MultiIndex):
        return frame
    return frame.copy()


def _validate_provider_frame(frame: pd.DataFrame) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise ProviderFetchError("provider returned non-DataFrame result")
    if frame.empty:
        raise ProviderFetchError("provider returned empty data")


def _extract_provider_frames(
    frame: pd.DataFrame,
    asset_symbols: Mapping[AssetId, str],
    fields: Sequence[str],
) -> dict[AssetId, pd.DataFrame]:
    _validate_provider_frame(frame)
    normalized = _normalize_provider_columns(frame)
    frames: dict[AssetId, pd.DataFrame] = {}

    if isinstance(normalized.columns, pd.MultiIndex):
        symbol_index = normalized.columns.get_level_values(0).astype(str)
        for asset_id, symbol in asset_symbols.items():
            mask = symbol_index == symbol
            if not mask.any():
                raise ProviderFetchError(
                    "provider data missing symbol",
                    context={"asset_id": str(asset_id), "provider_symbol": symbol},
                )
            asset_frame = normalized.loc[:, mask].copy()
            asset_frame.columns = asset_frame.columns.get_level_values(1)
            _require_fields(asset_frame, asset_id, fields)
            frames[asset_id] = asset_frame.loc[:, list(fields)]
    else:
        if len(asset_symbols) != 1:
            raise ProviderFetchError(
                "provider data must include multi-asset columns",
                context={"asset_count": len(asset_symbols)},
            )
        asset_id = next(iter(asset_symbols.keys()))
        asset_frame = normalized.copy()
        _require_fields(asset_frame, asset_id, fields)
        frames[asset_id] = asset_frame.loc[:, list(fields)]

    return frames


def _require_fields(frame: pd.DataFrame, asset_id: AssetId, fields: Sequence[str]) -> None:
    missing = [field for field in fields if field not in frame.columns]
    if missing:
        raise ProviderFetchError(
            "provider data missing requested fields",
            context={"asset_id": str(asset_id), "missing_fields": missing},
        )


def _combine_asset_frames(
    frames: Mapping[AssetId, pd.DataFrame], assets: Sequence[AssetId]
) -> pd.DataFrame:
    ordered = {asset: frames[asset] for asset in assets}
    combined = pd.concat(ordered, axis=1)
    if not isinstance(combined.columns, pd.MultiIndex):
        raise DataValidationError("combined frame must have MultiIndex columns")
    combined.columns.names = ["asset_id", "field"]
    combined.index.name = "date"
    return combined


def _build_assets_meta(
    frames: Mapping[AssetId, pd.DataFrame],
    asset_symbols: Mapping[AssetId, str],
    provider_name: str,
) -> dict[AssetId, dict[str, object]]:
    meta: dict[AssetId, dict[str, object]] = {}
    for asset_id, frame in frames.items():
        entry: dict[str, object] = {
            "provider": provider_name,
            "provider_symbol": asset_symbols[asset_id],
        }
        vendor_symbol = frame.attrs.get("vendor_symbol")
        if vendor_symbol:
            entry["vendor_symbol"] = vendor_symbol
        ingestion_ts = frame.attrs.get("ingestion_ts_utc")
        if ingestion_ts:
            entry["ingestion_ts_utc"] = ingestion_ts
        meta[asset_id] = entry
    return meta


@dataclass
class MarketDataService:
    provider: EodProvider
    store: ParquetMarketDataStore
    calendar_factory: CalendarFactory
    symbol_mapper: SymbolMapper
    dataset_version: str | None = None
    code_version: str | None = None
    clock: Callable[[], datetime] = _utc_now

    def get_timeseries(self, request: TimeSeriesRequest) -> TimeSeriesBundle:
        req_hash = request_hash(request)
        provider_name = getattr(self.provider, "name", None) or ""
        if not provider_name:
            raise ProviderFetchError("provider name must be set")

        assets = list(request.assets)
        fields = sorted(request.fields)
        asset_symbols = self.symbol_mapper.resolve_many(assets)

        target_index = self._build_target_index(request)
        logger = get_logger(__name__)

        manifest_file = manifest_path(self.store.root_path, req_hash)
        cached_frames: dict[AssetId, pd.DataFrame] | None = None
        lineage: LineageMeta | None = None
        quality: QualityReport | None = None
        aligned: pd.DataFrame | None = None

        if manifest_file.exists():
            logger.info(
                "market_data.cache_hit",
                extra={"request_hash": req_hash, "provider": provider_name},
            )
            manifest_payload = read_manifest(self.store.root_path, req_hash)
            lineage = LineageMeta.from_dict(manifest_payload)
        else:
            logger.info(
                "market_data.cache_miss",
                extra={"request_hash": req_hash, "provider": provider_name},
            )
            ingestion_ts = self.clock()
            _ensure_utc(ingestion_ts, "ingestion_ts")
            raw_frame = self._fetch_provider_frame(
                asset_symbols,
                request.start,
                request.end,
                fields,
                req_hash,
            )
            asset_frames = _extract_provider_frames(raw_frame, asset_symbols, fields)
            storage_paths = self._store_provider_frames(
                asset_frames,
                asset_symbols,
                ingestion_ts,
                provider_name,
            )
            cached_frames = self._read_cached_assets(assets, request, fields, provider_name)
            aligned, quality = self._align_and_validate(
                cached_frames,
                assets,
                target_index,
                request,
                req_hash,
                provider_name,
            )
            lineage = self._build_lineage(
                request,
                req_hash,
                provider_name,
                ingestion_ts,
                storage_paths,
            )
            write_manifest(self.store.root_path, req_hash, lineage, quality, storage_paths)

        if cached_frames is None:
            cached_frames = self._read_cached_assets(assets, request, fields, provider_name)
        if aligned is None or quality is None:
            aligned, quality = self._align_and_validate(
                cached_frames,
                assets,
                target_index,
                request,
                req_hash,
                provider_name,
            )

        if lineage is None:
            raise DataValidationError(
                "lineage missing after cache load",
                context={"request_hash": req_hash, "provider": provider_name},
            )

        assets_meta = _build_assets_meta(cached_frames, asset_symbols, provider_name)
        return TimeSeriesBundle(
            data=aligned,
            assets_meta=assets_meta,
            quality=quality,
            lineage=lineage,
        )

    def _build_target_index(self, request: TimeSeriesRequest) -> pd.Index:
        if request.calendar is None:
            raise DataValidationError(
                "calendar must be provided", context={"request": request.to_dict()}
            )
        calendar = self.calendar_factory(request.calendar)
        sessions = calendar.sessions(request.start, request.end)
        target_index = pd.Index(sessions, name="date")
        if not target_index.is_unique:
            raise DataValidationError("target calendar sessions must be unique")
        if not target_index.is_monotonic_increasing:
            raise DataValidationError("target calendar sessions must be monotonic increasing")
        return target_index

    def _fetch_provider_frame(
        self,
        asset_symbols: Mapping[AssetId, str],
        start: date,
        end: date,
        fields: Sequence[str],
        request_hash: str,
    ) -> pd.DataFrame:
        provider_symbols = list(asset_symbols.values())
        try:
            return self.provider.fetch_eod(provider_symbols, start, end, fields)
        except ProviderFetchError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise ProviderFetchError(
                "provider fetch failed",
                context={
                    "request_hash": request_hash,
                    "provider": getattr(self.provider, "name", ""),
                },
                cause=exc,
            ) from exc

    def _store_provider_frames(
        self,
        frames: Mapping[AssetId, pd.DataFrame],
        asset_symbols: Mapping[AssetId, str],
        ingestion_ts: datetime,
        provider_name: str,
    ) -> list[Path]:
        storage_paths: list[Path] = []
        for asset_id, frame in frames.items():
            paths = self.store.write_asset_frame(
                asset_id,
                frame,
                meta={
                    "vendor_symbol": asset_symbols[asset_id],
                    "ingestion_ts_utc": ingestion_ts.isoformat(),
                    "provider": provider_name,
                },
                provider=provider_name,
            )
            storage_paths.extend(paths)
        return storage_paths

    def _read_cached_assets(
        self,
        assets: Sequence[AssetId],
        request: TimeSeriesRequest,
        fields: Sequence[str],
        provider_name: str,
    ) -> dict[AssetId, pd.DataFrame]:
        return self.store.read_assets(
            assets,
            start=request.start,
            end=request.end,
            fields=fields,
            provider=provider_name,
        )

    def _align_and_validate(
        self,
        frames: Mapping[AssetId, pd.DataFrame],
        assets: Sequence[AssetId],
        target_index: Iterable[date],
        request: TimeSeriesRequest,
        request_hash: str,
        provider_name: str,
    ) -> tuple[pd.DataFrame, QualityReport]:
        combined = _combine_asset_frames(frames, assets)
        combined.attrs["request_hash"] = request_hash
        combined.attrs["provider"] = provider_name

        aligned = align_frame(combined, target_index, request.missing)
        aligned.attrs["request_hash"] = request_hash
        aligned.attrs["provider"] = provider_name
        validated, quality = validate_and_flag(aligned, request.validate)
        return validated, quality

    def _build_lineage(
        self,
        request: TimeSeriesRequest,
        request_hash: str,
        provider_name: str,
        ingestion_ts: datetime,
        storage_paths: Sequence[Path],
    ) -> LineageMeta:
        dataset_version = self.dataset_version
        if not dataset_version:
            if request.as_of is not None:
                dataset_version = request.as_of.date().isoformat()
            else:
                dataset_version = ingestion_ts.date().isoformat()

        normalized_paths = sorted(Path(path).as_posix() for path in storage_paths)
        return LineageMeta(
            request_hash=request_hash,
            request_json=request.to_dict(),
            provider=provider_name,
            ingestion_ts_utc=ingestion_ts.isoformat(),
            as_of_utc=request.as_of.isoformat() if request.as_of else None,
            dataset_version=dataset_version,
            code_version=self.code_version,
            storage_paths=normalized_paths,
        )


__all__ = ["MarketDataService"]
