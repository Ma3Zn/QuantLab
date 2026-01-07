from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Iterable, Mapping

from pydantic import field_validator

from quantlab.instruments.position import Position
from quantlab.instruments.types import INSTRUMENTS_SCHEMA_VERSION, InstrumentBaseModel
from quantlab.instruments.value_types import Currency, FiniteFloat


class Portfolio(InstrumentBaseModel):
    schema_version: int = INSTRUMENTS_SCHEMA_VERSION
    as_of: datetime
    positions: list[Position]
    cash: dict[Currency, FiniteFloat]
    meta: dict[str, Any] | None = None

    @field_validator("as_of")
    @classmethod
    def _require_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("as_of must be timezone-aware")
        return value

    @field_validator("positions")
    @classmethod
    def _canonicalize_positions(cls, value: list[Position]) -> list[Position]:
        seen: set[str] = set()
        for position in value:
            instrument_id = position.instrument_id
            if instrument_id in seen:
                raise ValueError("duplicate position instrument_id")
            seen.add(instrument_id)
        return sorted(value, key=lambda position: position.instrument_id)

    @field_validator("cash", mode="before")
    @classmethod
    def _normalize_cash_keys(
        cls, value: Mapping[str, float] | Iterable[tuple[str, float]]
    ) -> dict[str, float]:
        items: Iterable[tuple[str, float]]
        if isinstance(value, Mapping):
            items = value.items()
        else:
            items = value
        normalized: dict[str, float] = {}
        for key, amount in items:
            if not isinstance(key, str):
                raise TypeError("cash currency must be a string")
            currency = key.upper()
            if currency in normalized:
                raise ValueError("duplicate cash currency")
            normalized[currency] = amount
        return dict(sorted(normalized.items(), key=lambda item: item[0]))

    def to_canonical_dict(self) -> dict[str, Any]:
        payload = self.model_dump(mode="python", exclude_none=True)
        return {
            "schema_version": payload["schema_version"],
            "as_of": self.as_of.isoformat(),
            "positions": [
                position.model_dump(mode="json", exclude_none=True) for position in self.positions
            ],
            "cash": dict(self.cash),
            "meta": payload.get("meta"),
        }

    def to_canonical_json(self) -> str:
        return json.dumps(
            self.to_canonical_dict(),
            separators=(",", ":"),
            ensure_ascii=False,
        )


__all__ = ["Portfolio"]
