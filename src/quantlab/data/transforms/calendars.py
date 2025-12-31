from __future__ import annotations

from datetime import date
from typing import Protocol

import pandas_market_calendars as mcal

from quantlab.data.schemas.errors import DataValidationError


class TradingCalendar(Protocol):
    """Calendar abstraction for retrieving trading session dates."""

    def sessions(self, start: date, end: date) -> list[date]:
        """Return trading session dates between start and end (inclusive)."""


class MarketCalendarAdapter:
    """Adapter around pandas_market_calendars for market session dates."""

    def __init__(self, market: str) -> None:
        if not isinstance(market, str) or not market:
            raise ValueError("market must be a non-empty string")
        self.market = market
        try:
            self._calendar = mcal.get_calendar(market)
        except Exception as exc:
            raise DataValidationError(
                "unknown market calendar",
                context={"market": market},
                cause=exc,
            ) from exc

    def sessions(self, start: date, end: date) -> list[date]:
        if start > end:
            raise ValueError("start must be on or before end")
        schedule = self._calendar.schedule(start_date=start, end_date=end)
        if schedule.empty:
            return []
        return [session_date.date() for session_date in schedule.index]
