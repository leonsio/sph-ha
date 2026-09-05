from __future__ import annotations

from datetime import date, datetime, timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ...api import current_school_year_start
from ...api.client import SphAuthClient
from ...const import (
    CONF_CALENDAR_EVENT_TYPES,
    CONF_UPDATE_INTERVAL,
    DEFAULT_CALENDAR_EVENT_TYPES,
    DEFAULT_UPDATE_INTERVAL,
)
from .client import SphCalendarClient

_LOGGER = logging.getLogger(__name__)


# Official Hessian summer holidays. Calendar-specific bounds remain in the
# calendar module; the school-year selection itself is shared via api/.
HESSEN_SOMMERFERIEN = {
    2025: (date(2025, 7, 7), date(2025, 8, 15)),
    2026: (date(2026, 6, 29), date(2026, 8, 7)),
    2027: (date(2027, 6, 28), date(2027, 8, 6)),
    2028: (date(2028, 7, 3), date(2028, 8, 11)),
    2029: (date(2029, 7, 16), date(2029, 8, 24)),
    2030: (date(2030, 7, 22), date(2030, 8, 30)),
}


def school_year_bounds(school_year_start: int) -> tuple[datetime, datetime]:
    """Return the effective beginning and end of a Hessian school year."""
    previous_summer = HESSEN_SOMMERFERIEN.get(school_year_start)
    next_summer = HESSEN_SOMMERFERIEN.get(school_year_start + 1)
    start_date = (
        previous_summer[1] + timedelta(days=1)
        if previous_summer
        else date(school_year_start, 8, 1)
    )
    end_date = (
        next_summer[0] - timedelta(days=1)
        if next_summer
        else date(school_year_start + 1, 7, 31)
    )
    return (
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time()),
    )


def normalize_calendar_event_types(event_types=None) -> list[str]:
    """Normalize configured calendar categories while preserving display names."""
    values = event_types if isinstance(event_types, (list, tuple, set)) else DEFAULT_CALENDAR_EVENT_TYPES
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = str(value).strip()
        key = item.casefold()
        if not item or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result or list(DEFAULT_CALENDAR_EVENT_TYPES)


def relevant_calendar_events(events, event_types=None):
    """Return only SPH calendar entries selected in the integration settings."""
    wanted = {
        item.casefold()
        for item in normalize_calendar_event_types(event_types)
    }
    return [
        event
        for event in (events or [])
        if str(event.get("art", "")).strip().casefold() in wanted
    ]


class SphCalendarCoordinator(DataUpdateCoordinator):
    """Coordinator for the SPH calendar module."""

    def __init__(self, hass, entry, auth: SphAuthClient):
        self.entry = entry
        self.client = SphCalendarClient(auth)
        self.event_types = normalize_calendar_event_types(
            entry.data.get(CONF_CALENDAR_EVENT_TYPES, DEFAULT_CALENDAR_EVENT_TYPES)
        )
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Schulportal Hessen Kalender",
            update_interval=timedelta(
                minutes=int(entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL))
            ),
        )

    async def _async_update_data(self):
        try:
            today = datetime.now().date()
            school_year_start = current_school_year_start(today)
            start, end = school_year_bounds(school_year_start)
            _LOGGER.debug(
                "SPH: Kalender aktuelles Schuljahr %s/%s: %s bis %s",
                school_year_start,
                school_year_start + 1,
                start.date(),
                end.date(),
            )
            events = await self.hass.async_add_executor_job(
                self.client.get_calendar, start, end, school_year_start
            )
            filtered = relevant_calendar_events(events, self.event_types)
            _LOGGER.debug(
                "SPH: Kalender liefert für Schuljahr %s/%s %d relevante Termine der Arten %s von %d insgesamt",
                school_year_start,
                school_year_start + 1,
                len(filtered),
                ", ".join(self.event_types),
                len(events or []),
            )
            return filtered
        except Exception as err:
            raise UpdateFailed(str(err)) from err
