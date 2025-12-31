from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping

import pandas as pd

from quantlab.data.schemas.lineage import LineageMeta
from quantlab.data.schemas.quality import QualityReport
from quantlab.data.schemas.requests import AssetId


def _serialize_index(values: pd.Index) -> list[str]:
    serialized: list[str] = []
    for value in values:
        if isinstance(value, datetime):
            serialized.append(value.date().isoformat())
        elif isinstance(value, date):
            serialized.append(value.isoformat())
        else:
            serialized.append(str(value))
    return serialized


def _serialize_columns(columns: pd.Index) -> list[object]:
    if isinstance(columns, pd.MultiIndex):
        return [[str(level) for level in entry] for entry in columns.to_list()]
    return [str(column) for column in columns]


def _serialize_frame(frame: pd.DataFrame) -> dict[str, object]:
    return {
        "index": _serialize_index(frame.index),
        "columns": _serialize_columns(frame.columns),
        "data": frame.to_numpy().tolist(),
    }


@dataclass(frozen=True)
class TimeSeriesBundle:
    """Aligned, validated time series bundle with lineage and quality metadata."""

    data: pd.DataFrame
    assets_meta: Mapping[AssetId, Mapping[str, Any]]
    quality: QualityReport
    lineage: LineageMeta

    def to_dict(self) -> dict[str, object]:
        return {
            "data": _serialize_frame(self.data),
            "assets_meta": {
                str(asset): dict(meta) for asset, meta in self.assets_meta.items()
            },
            "quality": self.quality.to_dict(),
            "lineage": self.lineage.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


__all__ = ["TimeSeriesBundle"]
