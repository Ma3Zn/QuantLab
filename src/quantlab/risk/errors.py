from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass
class RiskError(Exception):
    """Base exception for risk layer operations with optional context and cause."""

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


class RiskInputError(RiskError):
    """Raised when a risk request or inputs fail validation."""


class RiskComputationError(RiskError):
    """Raised when a risk metric computation fails."""


class RiskSchemaError(RiskError):
    """Raised when risk schemas fail validation or serialization."""
