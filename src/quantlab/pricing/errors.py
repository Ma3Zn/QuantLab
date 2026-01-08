from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Mapping


def _format_as_of(as_of: date | str | None) -> str | None:
    if isinstance(as_of, date):
        return as_of.isoformat()
    return as_of


def _base_context(
    *,
    asset_id: str | None,
    field: str | None,
    as_of: date | str | None,
    instrument_id: str | None,
) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "field": field,
        "as_of": _format_as_of(as_of),
        "instrument_id": instrument_id,
    }


@dataclass
class PricingError(Exception):
    """Base exception for pricing failures with typed context."""

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


class MissingPriceError(PricingError):
    """Raised when a required market price is missing at the as-of date."""

    def __init__(
        self,
        *,
        asset_id: str,
        field: str,
        as_of: date | str,
        instrument_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        context = _base_context(
            asset_id=asset_id,
            field=field,
            as_of=as_of,
            instrument_id=instrument_id,
        )
        super().__init__(
            f"Missing price for asset_id={asset_id} field={field} as_of={context['as_of']}",
            context=context,
            cause=cause,
        )


class MissingFxRateError(PricingError):
    """Raised when the required FX rate is missing at the as-of date."""

    def __init__(
        self,
        *,
        asset_id: str,
        as_of: date | str,
        field: str = "close",
        instrument_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        context = _base_context(
            asset_id=asset_id,
            field=field,
            as_of=as_of,
            instrument_id=instrument_id,
        )
        super().__init__(
            f"Missing FX rate for asset_id={asset_id} field={field} as_of={context['as_of']}",
            context=context,
            cause=cause,
        )


class UnsupportedCurrencyError(PricingError):
    """Raised when pricing encounters a currency outside the MVP policy."""

    def __init__(
        self,
        *,
        currency: str,
        base_currency: str,
        as_of: date | str | None = None,
        instrument_id: str | None = None,
        asset_id: str | None = None,
        field: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        context = _base_context(
            asset_id=asset_id,
            field=field,
            as_of=as_of,
            instrument_id=instrument_id,
        )
        context.update({"currency": currency, "base_currency": base_currency})
        super().__init__(
            f"Unsupported currency {currency} for base {base_currency}",
            context=context,
            cause=cause,
        )


class NonFiniteInputError(PricingError):
    """Raised when an input value is NaN or infinite."""

    def __init__(
        self,
        *,
        field: str,
        value: float,
        as_of: date | str | None = None,
        instrument_id: str | None = None,
        asset_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        context = _base_context(
            asset_id=asset_id,
            field=field,
            as_of=as_of,
            instrument_id=instrument_id,
        )
        context["value"] = value
        super().__init__(
            f"Non-finite value for field={field}: {value}",
            context=context,
            cause=cause,
        )


class InvalidFxRateError(PricingError):
    """Raised when an FX rate is non-positive or otherwise invalid."""

    def __init__(
        self,
        *,
        asset_id: str,
        as_of: date | str,
        rate: float,
        field: str = "close",
        instrument_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        context = _base_context(
            asset_id=asset_id,
            field=field,
            as_of=as_of,
            instrument_id=instrument_id,
        )
        context["rate"] = rate
        super().__init__(
            f"Invalid FX rate for asset_id={asset_id} field={field} as_of={context['as_of']}",
            context=context,
            cause=cause,
        )


class MissingPricerError(PricingError):
    """Raised when no pricer is registered for an instrument kind."""

    def __init__(
        self,
        *,
        instrument_kind: str,
        instrument_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        context = _base_context(
            asset_id=None,
            field=None,
            as_of=None,
            instrument_id=instrument_id,
        )
        context["instrument_kind"] = instrument_kind
        super().__init__(
            f"Missing pricer for instrument_kind={instrument_kind}",
            context=context,
            cause=cause,
        )
