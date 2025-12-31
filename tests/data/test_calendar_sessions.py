from __future__ import annotations

from datetime import date

from quantlab.data.transforms.calendars import MarketCalendarAdapter


def test_xnys_excludes_new_years_day() -> None:
    calendar = MarketCalendarAdapter("XNYS")
    sessions = calendar.sessions(date(2023, 12, 29), date(2024, 1, 3))

    assert date(2024, 1, 1) not in sessions
    assert date(2024, 1, 2) in sessions
