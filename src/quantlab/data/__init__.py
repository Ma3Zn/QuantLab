"""Data layer package scaffolding for QuantLab."""

from quantlab.data.calendar import CalendarBaseline, CalendarBaselineSpec, calendar_version_id
from quantlab.data.canonical import CanonicalDataset
from quantlab.data.errors import (
    DataError,
    NormalizationError,
    ProviderError,
    ProviderRequestError,
    ProviderResponseError,
    StorageError,
    ValidationError,
)
from quantlab.data.identity import generate_ingest_run_id, request_fingerprint
from quantlab.data.ingestion import (
    IngestionConfig,
    IngestionResult,
    build_canonical_parts,
    run_ingestion,
)
from quantlab.data.logging import StructuredJSONFormatter, get_logger, log_data_error
from quantlab.data.normalizers import (
    EQUITY_EOD_DATASET_ID,
    FX_DAILY_DATASET_ID,
    SCHEMA_VERSION,
    NormalizationContext,
    normalize_equity_eod,
    normalize_fx_daily,
)
from quantlab.data.providers import (
    EodProvider,
    FetchRequest,
    LocalFileProviderAdapter,
    ProviderAdapter,
    RawResponse,
    SymbolMapper,
    TimeRange,
)
from quantlab.data.quality import QualityFlag, ValidationReport
from quantlab.data.registry import (
    DatasetRegistryEntry,
    append_registry_entry,
    lookup_registry_entry,
)
from quantlab.data.schemas import (
    Bar,
    BarRecord,
    CanonicalRecord,
    IngestRunMeta,
    PointRecord,
    Source,
    TimeSeriesBundle,
)
from quantlab.data.service import MarketDataService
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
from quantlab.data.transforms.returns import ReturnMethod, ReturnMissingPolicy, compute_returns
from quantlab.data.validators import ValidationContext, validate_records

__all__ = [
    "DataError",
    "ProviderError",
    "ProviderRequestError",
    "ProviderResponseError",
    "NormalizationError",
    "ValidationError",
    "StorageError",
    "CalendarBaseline",
    "CalendarBaselineSpec",
    "calendar_version_id",
    "StructuredJSONFormatter",
    "get_logger",
    "log_data_error",
    "EQUITY_EOD_DATASET_ID",
    "FX_DAILY_DATASET_ID",
    "SCHEMA_VERSION",
    "NormalizationContext",
    "normalize_equity_eod",
    "normalize_fx_daily",
    "request_fingerprint",
    "generate_ingest_run_id",
    "IngestionConfig",
    "IngestionResult",
    "build_canonical_parts",
    "run_ingestion",
    "QualityFlag",
    "ValidationReport",
    "DatasetRegistryEntry",
    "append_registry_entry",
    "lookup_registry_entry",
    "TimeRange",
    "FetchRequest",
    "RawResponse",
    "ProviderAdapter",
    "LocalFileProviderAdapter",
    "EodProvider",
    "SymbolMapper",
    "Source",
    "CanonicalRecord",
    "Bar",
    "BarRecord",
    "IngestRunMeta",
    "PointRecord",
    "TimeSeriesBundle",
    "ReturnMethod",
    "ReturnMissingPolicy",
    "compute_returns",
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
    "ValidationContext",
    "validate_records",
    "MarketDataService",
    "CanonicalDataset",
]
