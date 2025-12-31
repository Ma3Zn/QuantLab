from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import pandas as pd

from quantlab.data.schemas.errors import StorageError
from quantlab.data.schemas.requests import AssetId
from quantlab.data.storage.layout import asset_cache_path, asset_dir

_META_COLUMNS = {"vendor_symbol", "ingestion_ts_utc", "source_ts"}
_DEFAULT_FREQUENCY = "1D"


def _normalize_meta_value(value: object, name: str) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise StorageError(f"{name} must be timezone-aware")
        return value.isoformat()
    if isinstance(value, str) and value:
        return value
    raise StorageError(f"{name} must be a non-empty string or datetime")


def _normalize_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise StorageError(
                "date must be ISO YYYY-MM-DD",
                context={"value": value},
                cause=exc,
            ) from exc
    raise StorageError("date must be a date or ISO string", context={"value": value})


def _normalize_date_column(series: pd.Series) -> pd.Series:
    return series.map(_normalize_date)


def _validate_frame(frame: pd.DataFrame) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    if isinstance(frame.columns, pd.MultiIndex):
        raise StorageError("frame columns must not be a MultiIndex")
    if frame.empty:
        raise StorageError("cannot store empty asset frame")
    for column in frame.columns:
        if str(column) == "source_ts":
            continue
        if not pd.api.types.is_numeric_dtype(frame[column]):
            raise StorageError(
                "data columns must be numeric",
                context={"column": str(column)},
            )


def _extract_required_meta(meta: Mapping[str, object]) -> tuple[str, str]:
    if "vendor_symbol" not in meta:
        raise StorageError("meta must include vendor_symbol")
    if "ingestion_ts_utc" not in meta:
        raise StorageError("meta must include ingestion_ts_utc")
    vendor_symbol = _normalize_meta_value(meta["vendor_symbol"], "vendor_symbol")
    ingestion_ts = _normalize_meta_value(meta["ingestion_ts_utc"], "ingestion_ts_utc")
    return vendor_symbol, ingestion_ts


def _resolve_provider(provider: str | None, meta: Mapping[str, object]) -> str:
    candidate = provider or str(meta.get("provider") or "")
    if not candidate:
        raise StorageError(
            "provider must be supplied",
            context={"provider": provider, "meta_provider": meta.get("provider")},
        )
    return candidate


def _with_meta_columns(
    frame: pd.DataFrame,
    vendor_symbol: str,
    ingestion_ts_utc: str,
    source_ts: object | None,
) -> pd.DataFrame:
    if "vendor_symbol" in frame.columns or "ingestion_ts_utc" in frame.columns:
        raise StorageError("frame columns conflict with metadata columns")

    normalized = frame.copy()
    normalized.index = pd.Index(
        [_normalize_date(value) for value in frame.index],
        name="date",
    )
    if not normalized.index.is_unique:
        raise StorageError("frame index contains duplicate dates")
    normalized = normalized.sort_index()
    normalized = normalized.reset_index()

    normalized["vendor_symbol"] = vendor_symbol
    normalized["ingestion_ts_utc"] = ingestion_ts_utc

    if source_ts is not None:
        if "source_ts" in normalized.columns:
            raise StorageError("source_ts already exists in frame")
        if isinstance(source_ts, pd.Series):
            if len(source_ts) != len(normalized):
                raise StorageError(
                    "source_ts length does not match frame",
                    context={"expected": len(normalized), "actual": len(source_ts)},
                )
            normalized["source_ts"] = source_ts.values
        elif isinstance(source_ts, Iterable) and not isinstance(source_ts, (str, bytes)):
            source_list = list(source_ts)
            if len(source_list) != len(normalized):
                raise StorageError(
                    "source_ts length does not match frame",
                    context={"expected": len(normalized), "actual": len(source_list)},
                )
            normalized["source_ts"] = source_list
        else:
            normalized["source_ts"] = source_ts

    return normalized


def _partition_by_year(frame: pd.DataFrame) -> Iterable[tuple[int, pd.DataFrame]]:
    years = frame["date"].map(lambda value: value.year)
    frame_with_year = frame.assign(_year=years)
    for year, group in frame_with_year.groupby("_year", sort=True):
        yield int(year), group.drop(columns=["_year"])


def _safe_read_parquet(path: Path) -> pd.DataFrame:
    try:
        return pd.read_parquet(path)
    except (ImportError, ValueError, OSError) as exc:
        raise StorageError(
            "failed to read parquet",
            context={"path": str(path)},
            cause=exc,
        ) from exc


def _safe_write_parquet(frame: pd.DataFrame, path: Path) -> None:
    try:
        frame.to_parquet(path, index=False)
    except (ImportError, ValueError, OSError) as exc:
        raise StorageError(
            "failed to write parquet",
            context={"path": str(path)},
            cause=exc,
        ) from exc


def _extract_constant(series: pd.Series, name: str) -> str | None:
    if series.empty:
        return None
    unique_values = series.dropna().unique().tolist()
    if not unique_values:
        return None
    if len(unique_values) > 1:
        raise StorageError(
            f"{name} values are inconsistent",
            context={"values": [str(value) for value in unique_values]},
        )
    return str(unique_values[0])


@dataclass(frozen=True)
class ParquetMarketDataStore:
    root_path: Path
    provider: str | None = None

    def write_asset_frame(
        self,
        asset_id: AssetId,
        frame: pd.DataFrame,
        meta: Mapping[str, object],
        *,
        frequency: str = _DEFAULT_FREQUENCY,
        provider: str | None = None,
    ) -> list[Path]:
        """Write a single-asset frame into partitioned parquet files."""

        _validate_frame(frame)
        vendor_symbol, ingestion_ts = _extract_required_meta(meta)
        provider_name = _resolve_provider(provider or self.provider, meta)
        source_ts = meta.get("source_ts")

        prepared = _with_meta_columns(frame, vendor_symbol, ingestion_ts, source_ts)
        prepared = prepared.sort_values("date")

        written_paths: list[Path] = []
        for year, group in _partition_by_year(prepared):
            target = asset_cache_path(
                self.root_path,
                provider_name,
                asset_id,
                year,
                frequency,
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            _safe_write_parquet(group, target)
            written_paths.append(target)
        return written_paths

    def read_assets(
        self,
        asset_ids: Sequence[AssetId],
        start: date,
        end: date,
        fields: Sequence[str],
        *,
        frequency: str = _DEFAULT_FREQUENCY,
        provider: str | None = None,
    ) -> dict[AssetId, pd.DataFrame]:
        """Read cached parquet files for the requested assets and date range."""

        if start > end:
            raise ValueError("start must be on or before end")
        provider_name = _resolve_provider(provider or self.provider, {})

        results: dict[AssetId, pd.DataFrame] = {}
        years = range(start.year, end.year + 1)

        for asset_id in asset_ids:
            asset_folder = asset_dir(self.root_path, provider_name, asset_id, frequency)
            if not asset_folder.exists():
                raise StorageError(
                    "asset cache missing",
                    context={"asset_id": str(asset_id), "provider": provider_name},
                )

            frames: list[pd.DataFrame] = []
            for year in years:
                part_path = asset_cache_path(
                    self.root_path, provider_name, asset_id, year, frequency
                )
                if part_path.exists():
                    frames.append(_safe_read_parquet(part_path))
            if not frames:
                raise StorageError(
                    "no cached parquet partitions found",
                    context={"asset_id": str(asset_id), "provider": provider_name},
                )

            combined = pd.concat(frames, ignore_index=True)
            if "date" not in combined.columns:
                raise StorageError(
                    "cached parquet missing date column",
                    context={"asset_id": str(asset_id), "provider": provider_name},
                )

            combined["date"] = _normalize_date_column(combined["date"])
            combined = combined.sort_values("date")
            if combined["date"].duplicated().any():
                raise StorageError(
                    "cached parquet contains duplicate dates",
                    context={"asset_id": str(asset_id), "provider": provider_name},
                )

            mask = (combined["date"] >= start) & (combined["date"] <= end)
            sliced = combined.loc[mask].copy()

            vendor_symbol = (
                _extract_constant(sliced["vendor_symbol"], "vendor_symbol")
                if "vendor_symbol" in sliced.columns
                else None
            )
            ingestion_ts = (
                _extract_constant(sliced["ingestion_ts_utc"], "ingestion_ts_utc")
                if "ingestion_ts_utc" in sliced.columns
                else None
            )

            missing_fields = set(fields) - set(sliced.columns)
            if missing_fields:
                raise StorageError(
                    "cached parquet missing requested fields",
                    context={
                        "asset_id": str(asset_id),
                        "provider": provider_name,
                        "missing_fields": sorted(missing_fields),
                    },
                )

            data = sliced.drop(columns=[col for col in _META_COLUMNS if col in sliced.columns])
            data = data[["date", *fields]]
            data = data.set_index("date")
            data.index.name = "date"
            data.attrs["asset_id"] = str(asset_id)
            data.attrs["provider"] = provider_name
            if vendor_symbol is not None:
                data.attrs["vendor_symbol"] = vendor_symbol
            if ingestion_ts is not None:
                data.attrs["ingestion_ts_utc"] = ingestion_ts

            results[asset_id] = data

        return results
