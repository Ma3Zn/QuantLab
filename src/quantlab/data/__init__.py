"""Data layer package scaffolding for QuantLab."""

from quantlab.data.calendar import CalendarBaseline, CalendarBaselineSpec, calendar_version_id
from quantlab.data.errors import (
    DataError,
    NormalizationError,
    ProviderError,
    StorageError,
    ValidationError,
)
from quantlab.data.identity import generate_ingest_run_id, request_fingerprint
from quantlab.data.logging import StructuredJSONFormatter, get_logger, log_data_error
from quantlab.data.quality import QualityFlag, ValidationReport
from quantlab.data.registry import (
    DatasetRegistryEntry,
    append_registry_entry,
    lookup_registry_entry,
)
from quantlab.data.schemas import Bar, BarRecord, CanonicalRecord, PointRecord, Source
from quantlab.data.sessionrules import (
    SessionRule,
    SessionRulesSnapshot,
    compute_sessionrules_hash,
    load_seed_sessionrules,
)
from quantlab.data.storage import (
    CanonicalPaths,
    PublishedSnapshot,
    RawPaths,
    StagedSnapshot,
    build_canonical_paths,
    build_raw_paths,
    compute_content_hash,
    publish_canonical_snapshot,
    stage_canonical_snapshot,
    store_raw_payload,
)

__all__ = [
    "DataError",
    "ProviderError",
    "NormalizationError",
    "ValidationError",
    "StorageError",
    "CalendarBaseline",
    "CalendarBaselineSpec",
    "calendar_version_id",
    "StructuredJSONFormatter",
    "get_logger",
    "log_data_error",
    "request_fingerprint",
    "generate_ingest_run_id",
    "QualityFlag",
    "ValidationReport",
    "DatasetRegistryEntry",
    "append_registry_entry",
    "lookup_registry_entry",
    "Source",
    "CanonicalRecord",
    "Bar",
    "BarRecord",
    "PointRecord",
    "SessionRule",
    "SessionRulesSnapshot",
    "compute_sessionrules_hash",
    "load_seed_sessionrules",
    "RawPaths",
    "CanonicalPaths",
    "StagedSnapshot",
    "PublishedSnapshot",
    "build_raw_paths",
    "store_raw_payload",
    "build_canonical_paths",
    "compute_content_hash",
    "stage_canonical_snapshot",
    "publish_canonical_snapshot",
]
