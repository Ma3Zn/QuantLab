from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping, Sequence


def _require_non_empty(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"{name} must be a non-empty string")


def _ensure_utc(dt: datetime, name: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise ValueError(f"{name} must be timezone-aware and in UTC")


class QualityFlag(str, Enum):
    """Standardized quality flag vocabulary for canonical records."""

    MISSING_VALUE = "MISSING_VALUE"
    STALE = "STALE"
    OUTLIER_SUSPECT = "OUTLIER_SUSPECT"
    ADJUSTED_PRICE_PRESENT = "ADJUSTED_PRICE_PRESENT"
    PROVIDER_TIMESTAMP_USED = "PROVIDER_TIMESTAMP_USED"
    IMPUTED = "IMPUTED"


@dataclass(frozen=True)
class ValidationReport:
    """Structured validation report emitted per dataset build."""

    dataset_id: str
    dataset_version: str
    ingest_run_id: str
    generated_ts: datetime
    total_records: int
    hard_errors: Sequence[str] = field(default_factory=tuple)
    flag_counts: Mapping[QualityFlag, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty(self.dataset_id, "dataset_id")
        _require_non_empty(self.dataset_version, "dataset_version")
        _require_non_empty(self.ingest_run_id, "ingest_run_id")
        _ensure_utc(self.generated_ts, "generated_ts")
        if self.total_records < 0:
            raise ValueError("total_records must be non-negative")

        normalized_errors = tuple(self.hard_errors)
        normalized_counts: dict[QualityFlag, int] = {}
        for flag, count in self.flag_counts.items():
            normalized_flag = QualityFlag(flag)
            if count < 0:
                raise ValueError("flag count must be non-negative")
            normalized_counts[normalized_flag] = int(count)

        object.__setattr__(self, "hard_errors", normalized_errors)
        object.__setattr__(self, "flag_counts", normalized_counts)

    def to_payload(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "ingest_run_id": self.ingest_run_id,
            "generated_ts": self.generated_ts.isoformat(),
            "total_records": self.total_records,
            "hard_errors": list(self.hard_errors),
            "flag_counts": {flag.value: count for flag, count in self.flag_counts.items()},
        }
