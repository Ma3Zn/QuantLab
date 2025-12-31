from __future__ import annotations

from quantlab.data.errors import DataError


class ProviderFetchError(DataError):
    """Raised when a provider cannot fetch the requested data."""


class StorageError(DataError):
    """Raised when reading or writing cached data fails."""


class DataValidationError(DataError):
    """Raised when validation or guardrail checks fail."""
