from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from quantlab.data.errors import StorageError
from quantlab.data.identity import request_fingerprint


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
    _require_non_empty(value, "timezone_local")
    return value.strip()


def _parse_time(value: str, field: str) -> str:
    _require_non_empty(value, field)
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ValueError(f"{field} must be in HH:MM format") from exc
    return parsed.strftime("%H:%M")


def _parse_optional_date(value: object, field: str) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string when provided")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be in YYYY-MM-DD format") from exc


def _parse_optional_str(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string when provided")
    return value


@dataclass(frozen=True)
class SessionRule:
    mic: str
    timezone_local: str
    regular_close_local: str
    regular_open_local: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    source_note: str | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "mic": self.mic,
            "timezone_local": self.timezone_local,
            "regular_close_local": self.regular_close_local,
        }
        if self.regular_open_local is not None:
            payload["regular_open_local"] = self.regular_open_local
        if self.effective_from is not None:
            payload["effective_from"] = self.effective_from.isoformat()
        if self.effective_to is not None:
            payload["effective_to"] = self.effective_to.isoformat()
        if self.source_note is not None:
            payload["source_note"] = self.source_note
        return payload


def _parse_rule(entry: Mapping[str, object]) -> SessionRule:
    if not isinstance(entry, Mapping):
        raise ValueError("rules entries must be mappings")
    mic = _normalize_mic(_get_required_str(entry, "mic"))
    timezone_local = _normalize_timezone(_get_required_str(entry, "timezone_local"))
    regular_close_local = _parse_time(
        _get_required_str(entry, "regular_close_local"),
        "regular_close_local",
    )
    regular_open_local = entry.get("regular_open_local")
    if regular_open_local is not None:
        if not isinstance(regular_open_local, str) or not regular_open_local:
            raise ValueError("regular_open_local must be a non-empty string when provided")
        regular_open_local = _parse_time(regular_open_local, "regular_open_local")
    effective_from = _parse_optional_date(entry.get("effective_from"), "effective_from")
    effective_to = _parse_optional_date(entry.get("effective_to"), "effective_to")
    if effective_from and effective_to and effective_to < effective_from:
        raise ValueError("effective_to must be on or after effective_from")
    source_note = _parse_optional_str(entry.get("source_note"), "source_note")
    return SessionRule(
        mic=mic,
        timezone_local=timezone_local,
        regular_close_local=regular_close_local,
        regular_open_local=regular_open_local,
        effective_from=effective_from,
        effective_to=effective_to,
        source_note=source_note,
    )


def compute_sessionrules_hash(rules: Iterable[SessionRule]) -> str:
    sorted_rules = sorted(rules, key=lambda rule: rule.mic)
    payload = {"rules": [rule.to_payload() for rule in sorted_rules]}
    return request_fingerprint(payload)


@dataclass(frozen=True)
class SessionRulesSnapshot:
    version: str
    rules: tuple[SessionRule, ...]
    sessionrules_hash: str

    def __post_init__(self) -> None:
        _require_non_empty(self.version, "version")
        if not self.rules:
            raise ValueError("rules must not be empty")
        seen: set[str] = set()
        for rule in self.rules:
            if rule.mic in seen:
                raise ValueError("mic values must be unique")
            seen.add(rule.mic)


def load_seed_sessionrules(path: Path) -> SessionRulesSnapshot:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StorageError(
            "failed to read sessionrules seed",
            context={"path": str(path)},
            cause=exc,
        ) from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StorageError(
            "invalid sessionrules seed",
            context={"path": str(path)},
            cause=exc,
        ) from exc
    if not isinstance(payload, Mapping):
        raise StorageError(
            "sessionrules seed must be a mapping",
            context={"path": str(path)},
        )
    try:
        version = _get_required_str(payload, "version")
        rules_payload = payload.get("rules", [])
        if not isinstance(rules_payload, Sequence) or isinstance(rules_payload, str):
            raise ValueError("rules must be a sequence")
        rules = tuple(_parse_rule(entry) for entry in rules_payload)
        sessionrules_hash = compute_sessionrules_hash(rules)
        return SessionRulesSnapshot(
            version=version,
            rules=rules,
            sessionrules_hash=sessionrules_hash,
        )
    except ValueError as exc:
        raise StorageError(
            "invalid sessionrules seed",
            context={"path": str(path)},
            cause=exc,
        ) from exc
