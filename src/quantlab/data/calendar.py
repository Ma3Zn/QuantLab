from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


def _require_non_empty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True)
class CalendarBaselineSpec:
    name: str
    version: str
    overrides_hash: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "name")
        _require_non_empty(self.version, "version")
        if self.overrides_hash is not None:
            _require_non_empty(self.overrides_hash, "overrides_hash")

    @property
    def version_id(self) -> str:
        if self.overrides_hash:
            return f"{self.name}:{self.version}+{self.overrides_hash}"
        return f"{self.name}:{self.version}"


class CalendarBaseline(Protocol):
    name: str
    version: str
    overrides_hash: str | None = None

    def is_session_day(self, mic: str, session_date: date) -> bool:
        """Return True when the venue is scheduled to trade on the local date."""

    def session_open_local(self, mic: str, session_date: date) -> str | None:
        """Return the scheduled open time in HH:MM local time, if known."""

    def session_close_local(self, mic: str, session_date: date) -> str | None:
        """Return the scheduled close time in HH:MM local time, if known."""

    def timezone_local(self, mic: str) -> str | None:
        """Return the venue timezone (IANA), if available."""


def calendar_version_id(baseline: CalendarBaseline) -> str:
    _require_non_empty(baseline.name, "name")
    _require_non_empty(baseline.version, "version")
    if baseline.overrides_hash is not None:
        _require_non_empty(baseline.overrides_hash, "overrides_hash")
    if baseline.overrides_hash:
        return f"{baseline.name}:{baseline.version}+{baseline.overrides_hash}"
    return f"{baseline.name}:{baseline.version}"
