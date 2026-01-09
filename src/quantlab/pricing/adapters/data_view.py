from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from numbers import Real
from typing import Mapping, Sequence

import pandas as pd

from quantlab.data.canonical import CanonicalDataset
from quantlab.pricing.errors import MissingPriceError
from quantlab.pricing.market_data import MarketDataMeta, MarketDataView, MarketPoint

BAR_FIELD_MAP: dict[str, str] = {
    "open": "bar_open",
    "high": "bar_high",
    "low": "bar_low",
    "close": "bar_close",
    "volume": "bar_volume",
    "adj_close": "bar_adj_close",
}


def _parse_iso_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            if "T" in value:
                return datetime.fromisoformat(value).date()
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _row_as_of_date(row: Mapping[str, object]) -> date | None:
    return _parse_iso_date(row.get("trading_date_local")) or _parse_iso_date(row.get("ts"))


def _parse_quality_flags(value: object) -> tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, str):
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return (value,)
        if isinstance(payload, list):
            return tuple(str(flag) for flag in payload)
        return (str(payload),)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(str(flag) for flag in value)
    return (str(value),)


def _format_lineage_ids(lineage: Mapping[str, str]) -> tuple[str, ...]:
    ordered_keys = ("dataset_id", "dataset_version", "ingest_run_id", "schema_version", "asof_ts")
    entries: list[str] = []
    for key in ordered_keys:
        value = lineage.get(key)
        if value:
            entries.append(f"{key}={value}")
    return tuple(entries)


def _parse_fx_pair(asset_id: str) -> tuple[str, str] | None:
    if not asset_id.startswith("FX."):
        return None
    pair = asset_id[3:]
    if len(pair) != 6:
        return None
    return pair[:3], pair[3:]


def _is_missing_value(value: object) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _coerce_float(value: object) -> float | None:
    if isinstance(value, Real):
        return float(value)
    return None


@dataclass(frozen=True)
class _DatasetIndex:
    dataset: CanonicalDataset
    dataset_type: str
    records: Mapping[tuple[object, ...], Mapping[str, object]]
    instrument_ids: set[str]
    available_fields: set[str]
    fx_pair_map: Mapping[tuple[str, str], str]
    lineage_ids: tuple[str, ...]
    asset_id_map: Mapping[str, str]

    def resolve_instrument_id(self, asset_id: str) -> str | None:
        mapped = self.asset_id_map.get(asset_id)
        if mapped:
            return mapped
        if asset_id in self.instrument_ids:
            return asset_id
        if self.dataset_type == "point":
            pair = _parse_fx_pair(asset_id)
            if pair:
                return self.fx_pair_map.get(pair)
        return None

    def resolve_point_field(self, field: str) -> str:
        if field in self.available_fields:
            return field
        if field == "close" and "mid" in self.available_fields:
            return "mid"
        return field


def _build_index(
    dataset: CanonicalDataset,
    *,
    asset_id_map: Mapping[str, str],
) -> _DatasetIndex:
    frame = dataset.frame
    if "bar_close" in frame.columns:
        dataset_type = "bar"
    elif "field" in frame.columns and "value" in frame.columns:
        dataset_type = "point"
    else:
        raise ValueError("unsupported canonical dataset schema")

    records: dict[tuple[object, ...], Mapping[str, object]] = {}
    instrument_ids: set[str] = set()
    available_fields: set[str] = set()
    fx_pair_map: dict[tuple[str, str], str] = {}

    for row in frame.to_dict(orient="records"):
        instrument_id = row.get("instrument_id")
        if not instrument_id:
            continue
        instrument_id_str = str(instrument_id)
        as_of = _row_as_of_date(row)
        if as_of is None:
            continue
        instrument_ids.add(instrument_id_str)
        if dataset_type == "bar":
            records[(instrument_id_str, as_of)] = row
        else:
            field = row.get("field")
            if not field:
                continue
            field_str = str(field)
            available_fields.add(field_str)
            records[(instrument_id_str, field_str, as_of)] = row
            base_ccy = row.get("base_ccy")
            quote_ccy = row.get("quote_ccy")
            if base_ccy and quote_ccy:
                fx_pair_map[(str(base_ccy), str(quote_ccy))] = instrument_id_str

    return _DatasetIndex(
        dataset=dataset,
        dataset_type=dataset_type,
        records=records,
        instrument_ids=instrument_ids,
        available_fields=available_fields,
        fx_pair_map=fx_pair_map,
        lineage_ids=_format_lineage_ids(dataset.lineage()),
        asset_id_map=asset_id_map,
    )


class CanonicalDataView(MarketDataView):
    """MarketDataView over one or more canonical datasets."""

    def __init__(
        self,
        datasets: Sequence[CanonicalDataset],
        *,
        asset_id_map: Mapping[str, str] | None = None,
    ) -> None:
        if not datasets:
            raise ValueError("datasets must not be empty")
        asset_map = {str(key): str(value) for key, value in (asset_id_map or {}).items()}
        ordered = sorted(datasets, key=lambda dataset: dataset.dataset_id)
        self._indices = tuple(_build_index(dataset, asset_id_map=asset_map) for dataset in ordered)
        self._lineage = {dataset.dataset_id: dataset.dataset_version for dataset in ordered}

    @property
    def lineage(self) -> dict[str, str]:
        """Return dataset lineage identifiers for valuation outputs."""
        return dict(self._lineage)

    def has_value(self, asset_id: str, field: str, as_of: date) -> bool:
        """Return True if a numeric market value exists for the key."""
        return self.get_point(asset_id, field, as_of) is not None

    def get_value(self, asset_id: str, field: str, as_of: date) -> float:
        """Return the numeric market value or raise MissingPriceError."""
        point = self.get_point(asset_id, field, as_of)
        if point is None:
            raise MissingPriceError(asset_id=asset_id, field=field, as_of=as_of)
        return float(point.value)

    def get_point(self, asset_id: str, field: str, as_of: date) -> MarketPoint | None:
        """Return the market point and metadata if available."""
        for index in self._indices:
            instrument_id = index.resolve_instrument_id(asset_id)
            if not instrument_id:
                continue
            if index.dataset_type == "bar":
                column = BAR_FIELD_MAP.get(field)
                if not column:
                    continue
                row = index.records.get((instrument_id, as_of))
                if row is None:
                    continue
                value = row.get(column)
            else:
                field_key = index.resolve_point_field(field)
                row = index.records.get((instrument_id, field_key, as_of))
                if row is None:
                    continue
                value = row.get("value")
            if _is_missing_value(value):
                continue
            value_float = _coerce_float(value)
            if value_float is None:
                continue
            meta = MarketDataMeta(
                quality_flags=_parse_quality_flags(row.get("quality_flags")),
                source_date=_parse_iso_date(row.get("trading_date_local")),
                aligned_date=as_of,
                lineage_ids=index.lineage_ids,
            )
            return MarketPoint(value=value_float, meta=meta)
        return None


__all__ = ["CanonicalDataView"]
