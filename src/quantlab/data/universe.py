from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from quantlab.data.errors import StorageError
from quantlab.data.identity import request_fingerprint
from quantlab.instruments.master import (
    InstrumentMasterRecord,
    InstrumentStatus,
    InstrumentType,
    generate_instrument_id,
    normalize_ccy,
    normalize_ticker,
)


def _require_non_empty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _get_required_str(payload: Mapping[str, object], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _normalize_mic(value: str) -> str:
    _require_non_empty(value, "mic")
    return value.strip().upper()


def _normalize_timezone(value: str) -> str:
    _require_non_empty(value, "exchange_timezone")
    return value.strip()


def _parse_status(value: object) -> InstrumentStatus:
    if value is None:
        return InstrumentStatus.ACTIVE
    if not isinstance(value, str) or not value:
        raise ValueError("status must be a non-empty string")
    try:
        return InstrumentStatus(value)
    except ValueError as exc:
        raise ValueError("status is invalid") from exc


def _equity_key(mic: str, ticker_norm: str, currency: str) -> str:
    return f"EQUITY|{mic}|{ticker_norm}|{currency}"


def _fx_key(base_ccy: str, quote_ccy: str) -> str:
    return f"FX_SPOT|{base_ccy}|{quote_ccy}"


def _parse_equities(entries: Sequence[object]) -> list[InstrumentMasterRecord]:
    records: list[InstrumentMasterRecord] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("equities entries must be mappings")
        mic = _normalize_mic(_get_required_str(entry, "mic"))
        vendor_symbol = _get_required_str(entry, "vendor_symbol")
        ticker_raw = _get_required_str(entry, "ticker") if "ticker" in entry else vendor_symbol
        ticker_norm = normalize_ticker(ticker_raw)
        currency = normalize_ccy(_get_required_str(entry, "currency"))
        exchange_timezone = _normalize_timezone(_get_required_str(entry, "timezone"))
        status = _parse_status(entry.get("status"))
        instrument_id = generate_instrument_id(_equity_key(mic, ticker_norm, currency))

        records.append(
            InstrumentMasterRecord(
                instrument_id=instrument_id,
                instrument_type=InstrumentType.EQUITY,
                status=status,
                ticker_raw=ticker_raw,
                ticker_norm=ticker_norm,
                vendor_symbol=vendor_symbol,
                mic=mic,
                currency=currency,
                exchange_timezone=exchange_timezone,
                base_ccy=None,
                quote_ccy=None,
                pair_code=None,
                vendor_pair_code=None,
            )
        )
    return records


def _parse_fx(entries: Sequence[object]) -> list[InstrumentMasterRecord]:
    records: list[InstrumentMasterRecord] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("fx_spot entries must be mappings")
        base_ccy = normalize_ccy(_get_required_str(entry, "base_ccy"))
        quote_ccy = normalize_ccy(_get_required_str(entry, "quote_ccy"))
        pair_code = _get_required_str(entry, "pair_code") if "pair_code" in entry else None
        if pair_code is None:
            pair_code = f"{base_ccy}{quote_ccy}"
        status = _parse_status(entry.get("status"))
        vendor_pair_code = entry.get("vendor_pair_code")
        if vendor_pair_code is not None and (
            not isinstance(vendor_pair_code, str) or not vendor_pair_code
        ):
            raise ValueError("vendor_pair_code must be a non-empty string when provided")
        instrument_id = generate_instrument_id(_fx_key(base_ccy, quote_ccy))

        records.append(
            InstrumentMasterRecord(
                instrument_id=instrument_id,
                instrument_type=InstrumentType.FX_SPOT,
                status=status,
                ticker_raw=None,
                ticker_norm=None,
                vendor_symbol=None,
                mic=None,
                currency=None,
                exchange_timezone=None,
                base_ccy=base_ccy,
                quote_ccy=quote_ccy,
                pair_code=pair_code,
                vendor_pair_code=vendor_pair_code,
            )
        )
    return records


def compute_universe_hash(records: Iterable[InstrumentMasterRecord]) -> str:
    sorted_records = sorted(records, key=lambda record: record.instrument_id)
    payload = {"instruments": [record.to_payload() for record in sorted_records]}
    return request_fingerprint(payload)


@dataclass(frozen=True)
class UniverseSnapshot:
    version: str
    instruments: tuple[InstrumentMasterRecord, ...]
    universe_hash: str

    def __post_init__(self) -> None:
        _require_non_empty(self.version, "version")
        if not self.instruments:
            raise ValueError("instruments must not be empty")
        seen_ids: set[str] = set()
        for record in self.instruments:
            if record.instrument_id in seen_ids:
                raise ValueError("instrument_id values must be unique")
            seen_ids.add(record.instrument_id)


def load_seed_universe(path: Path) -> UniverseSnapshot:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StorageError(
            "failed to read universe seed",
            context={"path": str(path)},
            cause=exc,
        ) from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StorageError(
            "invalid universe seed",
            context={"path": str(path)},
            cause=exc,
        ) from exc
    if not isinstance(payload, Mapping):
        raise StorageError("universe seed must be a mapping", context={"path": str(path)})

    try:
        version = _get_required_str(payload, "version")
        equities_payload = payload.get("equities", [])
        fx_payload = payload.get("fx_spot", [])
        if not isinstance(equities_payload, Sequence):
            raise ValueError("equities must be a sequence")
        if not isinstance(fx_payload, Sequence):
            raise ValueError("fx_spot must be a sequence")
        equity_records = _parse_equities(equities_payload)
        fx_records = _parse_fx(fx_payload)
        records = tuple(equity_records + fx_records)
        universe_hash = compute_universe_hash(records)
        return UniverseSnapshot(
            version=version,
            instruments=records,
            universe_hash=universe_hash,
        )
    except ValueError as exc:
        raise StorageError(
            "invalid universe seed",
            context={"path": str(path)},
            cause=exc,
        ) from exc
