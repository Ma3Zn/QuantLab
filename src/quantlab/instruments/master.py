from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum


class InstrumentType(str, Enum):
    EQUITY = "EQUITY"
    FX_SPOT = "FX_SPOT"


class InstrumentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


_INSTRUMENT_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "quantlab.instrument.v1")


def _require_non_empty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def normalize_ticker(value: str) -> str:
    _require_non_empty(value, "ticker")
    return value.strip().upper()


def normalize_ccy(value: str) -> str:
    _require_non_empty(value, "currency")
    return value.strip().upper()


def generate_instrument_id(key: str) -> str:
    _require_non_empty(key, "key")
    return f"inst_{uuid.uuid5(_INSTRUMENT_NAMESPACE, key)}"


@dataclass(frozen=True)
class InstrumentMasterRecord:
    instrument_id: str
    instrument_type: InstrumentType
    status: InstrumentStatus
    ticker_raw: str | None
    ticker_norm: str | None
    vendor_symbol: str | None
    mic: str | None
    currency: str | None
    exchange_timezone: str | None
    base_ccy: str | None
    quote_ccy: str | None
    pair_code: str | None
    vendor_pair_code: str | None

    def __post_init__(self) -> None:
        _require_non_empty(self.instrument_id, "instrument_id")
        if self.instrument_type == InstrumentType.EQUITY:
            _require_non_empty(self.mic or "", "mic")
            _require_non_empty(self.currency or "", "currency")
            _require_non_empty(self.vendor_symbol or "", "vendor_symbol")
            _require_non_empty(self.ticker_raw or "", "ticker_raw")
            _require_non_empty(self.ticker_norm or "", "ticker_norm")
            _require_non_empty(self.exchange_timezone or "", "exchange_timezone")
        elif self.instrument_type == InstrumentType.FX_SPOT:
            _require_non_empty(self.base_ccy or "", "base_ccy")
            _require_non_empty(self.quote_ccy or "", "quote_ccy")
            _require_non_empty(self.pair_code or "", "pair_code")
        else:
            raise ValueError("instrument_type is invalid")

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "instrument_id": self.instrument_id,
            "instrument_type": self.instrument_type.value,
            "status": self.status.value,
        }
        if self.ticker_raw is not None:
            payload["ticker_raw"] = self.ticker_raw
        if self.ticker_norm is not None:
            payload["ticker_norm"] = self.ticker_norm
        if self.vendor_symbol is not None:
            payload["vendor_symbol"] = self.vendor_symbol
        if self.mic is not None:
            payload["mic"] = self.mic
        if self.currency is not None:
            payload["currency"] = self.currency
        if self.exchange_timezone is not None:
            payload["exchange_timezone"] = self.exchange_timezone
        if self.base_ccy is not None:
            payload["base_ccy"] = self.base_ccy
        if self.quote_ccy is not None:
            payload["quote_ccy"] = self.quote_ccy
        if self.pair_code is not None:
            payload["pair_code"] = self.pair_code
        if self.vendor_pair_code is not None:
            payload["vendor_pair_code"] = self.vendor_pair_code
        return payload
