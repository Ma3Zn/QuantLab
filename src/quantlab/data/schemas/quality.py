from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, cast

from quantlab.data.schemas.requests import AssetId


class QualityFlag(str, Enum):
    """Quality flags emitted by data access validation and guardrails."""

    MISSING = "MISSING"
    DUPLICATE_RESOLVED = "DUPLICATE_RESOLVED"
    OUTLIER_RETURN = "OUTLIER_RETURN"
    SUSPECT_CORP_ACTION = "SUSPECT_CORP_ACTION"
    NONPOSITIVE_PRICE = "NONPOSITIVE_PRICE"
    NONMONOTONIC_INDEX = "NONMONOTONIC_INDEX"


@dataclass(frozen=True)
class QualityReport:
    """Aggregated quality metrics and example dates per asset."""

    coverage: Mapping[AssetId, float] = field(default_factory=dict)
    flag_counts: Mapping[AssetId, Mapping[QualityFlag, int]] = field(default_factory=dict)
    flag_examples: Mapping[AssetId, Mapping[QualityFlag, list[str]]] = field(default_factory=dict)
    actions: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized_coverage: dict[AssetId, float] = {}
        for asset, value in self.coverage.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError("coverage must be in [0, 1]")
            normalized_coverage[AssetId(str(asset))] = float(value)

        normalized_counts: dict[AssetId, dict[QualityFlag, int]] = {}
        for asset, counts in self.flag_counts.items():
            normalized_asset = AssetId(str(asset))
            normalized_counts[normalized_asset] = {}
            for flag, count in counts.items():
                normalized_flag = QualityFlag(flag)
                if count < 0:
                    raise ValueError("flag count must be non-negative")
                normalized_counts[normalized_asset][normalized_flag] = int(count)

        normalized_examples: dict[AssetId, dict[QualityFlag, list[str]]] = {}
        for asset, examples in self.flag_examples.items():
            normalized_asset = AssetId(str(asset))
            normalized_examples[normalized_asset] = {}
            for flag, dates in examples.items():
                normalized_flag = QualityFlag(flag)
                normalized_examples[normalized_asset][normalized_flag] = list(dates)

        object.__setattr__(self, "coverage", normalized_coverage)
        object.__setattr__(self, "flag_counts", normalized_counts)
        object.__setattr__(self, "flag_examples", normalized_examples)

    def to_dict(self) -> dict[str, object]:
        return {
            "coverage": {str(asset): value for asset, value in self.coverage.items()},
            "flag_counts": {
                str(asset): {flag.value: count for flag, count in counts.items()}
                for asset, counts in self.flag_counts.items()
            },
            "flag_examples": {
                str(asset): {flag.value: dates for flag, dates in examples.items()}
                for asset, examples in self.flag_examples.items()
            },
            "actions": dict(self.actions),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> QualityReport:
        coverage_raw = cast(Mapping[str, object], payload.get("coverage") or {})
        coverage = {
            AssetId(asset): float(cast(float | int | str, value))
            for asset, value in coverage_raw.items()
        }
        flag_counts: dict[AssetId, dict[QualityFlag, int]] = {}
        flag_counts_raw = cast(Mapping[str, Mapping[str, object]], payload.get("flag_counts") or {})
        for asset, counts in flag_counts_raw.items():
            flag_counts[AssetId(asset)] = {
                QualityFlag(flag): int(cast(int | float | str, count))
                for flag, count in counts.items()
            }
        flag_examples: dict[AssetId, dict[QualityFlag, list[str]]] = {}
        flag_examples_raw = cast(
            Mapping[str, Mapping[str, object]], payload.get("flag_examples") or {}
        )
        for asset, examples in flag_examples_raw.items():
            flag_examples[AssetId(asset)] = {
                QualityFlag(flag): list(cast(list[str], dates)) for flag, dates in examples.items()
            }
        actions = dict(cast(Mapping[str, str], payload.get("actions") or {}))
        return cls(
            coverage=coverage,
            flag_counts=flag_counts,
            flag_examples=flag_examples,
            actions=actions,
        )

    @classmethod
    def from_json(cls, payload: str) -> QualityReport:
        return cls.from_dict(json.loads(payload))
