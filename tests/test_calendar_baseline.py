from __future__ import annotations

from datetime import date

import pytest

from quantlab.data.calendar import CalendarBaseline, CalendarBaselineSpec, calendar_version_id


class _DummyCalendar(CalendarBaseline):
    name = "TestCal"
    version = "2024.1"
    overrides_hash = None

    def is_session_day(self, mic: str, session_date: date) -> bool:
        return True

    def session_open_local(self, mic: str, session_date: date) -> str | None:
        return "09:30"

    def session_close_local(self, mic: str, session_date: date) -> str | None:
        return "16:00"

    def timezone_local(self, mic: str) -> str | None:
        return "America/New_York"


def test_calendar_baseline_spec_version_id() -> None:
    spec = CalendarBaselineSpec(name="OpenSource", version="1.2.3")
    assert spec.version_id == "OpenSource:1.2.3"

    spec_with_overrides = CalendarBaselineSpec(
        name="OpenSource",
        version="1.2.3",
        overrides_hash="ovr_001",
    )
    assert spec_with_overrides.version_id == "OpenSource:1.2.3+ovr_001"


def test_calendar_version_id_uses_baseline_fields() -> None:
    baseline: CalendarBaseline = _DummyCalendar()
    assert calendar_version_id(baseline) == "TestCal:2024.1"

    baseline.overrides_hash = "override_hash"
    assert calendar_version_id(baseline) == "TestCal:2024.1+override_hash"


def test_calendar_baseline_spec_rejects_empty_fields() -> None:
    with pytest.raises(ValueError):
        CalendarBaselineSpec(name="", version="1.0")

    with pytest.raises(ValueError):
        CalendarBaselineSpec(name="Cal", version="")

    with pytest.raises(ValueError):
        CalendarBaselineSpec(name="Cal", version="1.0", overrides_hash="")
