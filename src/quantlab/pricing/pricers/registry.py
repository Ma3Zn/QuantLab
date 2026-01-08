from __future__ import annotations

from typing import Mapping

from quantlab.pricing.errors import MissingPricerError
from quantlab.pricing.pricers.base import Pricer


class PricerRegistry:
    """Map instrument kinds to pricer components."""

    def __init__(self, mapping: Mapping[str, Pricer] | None = None) -> None:
        self._pricers: dict[str, Pricer] = dict(mapping or {})

    def register(self, instrument_kind: str, pricer: Pricer) -> None:
        if not instrument_kind:
            raise ValueError("instrument_kind must be non-empty")
        self._pricers[instrument_kind] = pricer

    def resolve(self, instrument_kind: str) -> Pricer:
        if not instrument_kind:
            raise ValueError("instrument_kind must be non-empty")
        try:
            return self._pricers[instrument_kind]
        except KeyError as exc:
            raise MissingPricerError(instrument_kind=instrument_kind) from exc

    def registered_kinds(self) -> tuple[str, ...]:
        return tuple(sorted(self._pricers.keys()))


__all__ = ["PricerRegistry"]
