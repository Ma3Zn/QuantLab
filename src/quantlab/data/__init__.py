"""Data layer package scaffolding for QuantLab."""

from quantlab.data.errors import (
    DataError,
    NormalizationError,
    ProviderError,
    StorageError,
    ValidationError,
)
from quantlab.data.logging import StructuredJSONFormatter, get_logger, log_data_error
from quantlab.data.quality import QualityFlag, ValidationReport
from quantlab.data.schemas import Bar, BarRecord, CanonicalRecord, PointRecord, Source

__all__ = [
    "DataError",
    "ProviderError",
    "NormalizationError",
    "ValidationError",
    "StorageError",
    "StructuredJSONFormatter",
    "get_logger",
    "log_data_error",
    "QualityFlag",
    "ValidationReport",
    "Source",
    "CanonicalRecord",
    "Bar",
    "BarRecord",
    "PointRecord",
]
