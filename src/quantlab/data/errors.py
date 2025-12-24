from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass
class DataError(Exception):
    """Base exception for data layer operations with optional context and cause."""

    message: str
    context: Mapping[str, Any] = field(default_factory=dict)
    cause: Exception | None = None

    def __str__(self) -> str:
        segments: list[str] = [self.message]
        if self.context:
            segments.append(f"context={dict(self.context)}")
        if self.cause:
            segments.append(f"cause={repr(self.cause)}")
        return " | ".join(segments)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error_type": self.__class__.__name__,
            "message": self.message,
        }
        if self.context:
            payload["context"] = dict(self.context)
        if self.cause:
            payload["cause"] = repr(self.cause)
        return payload


class ProviderError(DataError):
    """Raised when provider adapters fail to fetch or parse data."""


class NormalizationError(DataError):
    """Raised when raw payloads cannot be normalized to canonical schema."""


class ValidationError(DataError):
    """Raised when canonical records fail validation rules."""


class StorageError(DataError):
    """Raised when snapshot staging or publishing fails."""
