from __future__ import annotations

from datetime import date, datetime, time, timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from ...api.client import SphAuthClient
from ...const import (
    CONF_MODULE_STUNDENPLAN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MODULE_ENABLED,
    DEFAULT_UPDATE_INTERVAL,
)
from .client import SphTimetableClient

_LOGGER = logging.getLogger(__name__)

FREE_DAY_CALENDAR_ENTITY = "calendar.deutschland_he"
FREE_DAY_PAST_WEEKS = 2
FREE_DAY_FUTURE_WEEKS = 8


class SphTimetableCoordinator(DataUpdateCoordinator):
    """Coordinator for the SPH timetable module."""

    def __init__(self, hass, entry, auth: SphAuthClient):
        self.entry = entry
        self.client = SphTimetableClient(auth)
        self.enabled = bool(entry.data.get(CONF_MODULE_STUNDENPLAN, DEFAULT_MODULE_ENABLED))
        self._last_successful_data = None
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Schulportal Hessen Stundenplan",
            update_interval=(
                timedelta(minutes=int(entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)))
                if self.enabled
                else None
            ),
        )

    @property
    def last_successful_data(self):
        """Return the last successfully parsed timetable data."""
        return self._last_successful_data

    def _timezone(self):
        return dt_util.get_time_zone(self.hass.config.time_zone)

    def _free_day_window(self) -> tuple[datetime, datetime]:
        """Return the same rolling range used by the timetable calendar."""
        tz = self._timezone()
        today = dt_util.now().astimezone(tz).date()
        start_day = today - timedelta(weeks=FREE_DAY_PAST_WEEKS)
        end_day = today + timedelta(weeks=FREE_DAY_FUTURE_WEEKS) + timedelta(days=1)
        return (
            datetime.combine(start_day, time.min, tzinfo=tz),
            datetime.combine(end_day, time.min, tzinfo=tz),
        )

    @staticmethod
    def _parse_calendar_value(value) -> date | datetime | None:
        """Parse a Home Assistant calendar start/end value."""
        if isinstance(value, (date, datetime)):
            return value
        text = str(value or "").strip()
        if not text:
            return None
        try:
            if "T" in text or " " in text:
                return datetime.fromisoformat(text.replace("Z", "+00:00"))
            return date.fromisoformat(text[:10])
        except ValueError:
            return None

    @classmethod
    def _event_dates(cls, event: dict) -> set[str]:
        """Return every local date touched by one calendar event."""
        start_value = cls._parse_calendar_value(event.get("start"))
        end_value = cls._parse_calendar_value(event.get("end"))
        if start_value is None:
            return set()

        start_day = start_value.date() if isinstance(start_value, datetime) else start_value
        if end_value is None:
            end_day = start_day
        elif isinstance(start_value, date) and not isinstance(start_value, datetime) and isinstance(end_value, date) and not isinstance(end_value, datetime):
            # All-day calendar ends are exclusive.
            end_day = max(start_day, end_value - timedelta(days=1))
        else:
            end_dt = end_value if isinstance(end_value, datetime) else datetime.combine(end_value, time.min)
            # A timed event ending exactly at midnight does not occupy the new day.
            if end_dt.time() == time.min and end_dt.date() > start_day:
                end_day = end_dt.date() - timedelta(days=1)
            else:
                end_day = end_dt.date()

        result: set[str] = set()
        target = start_day
        while target <= end_day:
            result.add(target.isoformat())
            target += timedelta(days=1)
        return result

    async def _async_free_days(self) -> list[str]:
        """Read free days from calendar.deutschland_he when that entity exists."""
        if self.hass.states.get(FREE_DAY_CALENDAR_ENTITY) is None:
            _LOGGER.debug(
                "SPH: %s nicht vorhanden; Stundenplan wird nicht nach freien Tagen gefiltert",
                FREE_DAY_CALENDAR_ENTITY,
            )
            return []
        if not self.hass.services.has_service("calendar", "get_events"):
            _LOGGER.debug(
                "SPH: calendar.get_events noch nicht verfügbar; freie Tage werden vorerst nicht gefiltert"
            )
            return []

        start, end = self._free_day_window()
        try:
            response = await self.hass.services.async_call(
                "calendar",
                "get_events",
                {
                    "entity_id": FREE_DAY_CALENDAR_ENTITY,
                    "start_date_time": start.isoformat(),
                    "end_date_time": end.isoformat(),
                },
                blocking=True,
                return_response=True,
            )
        except Exception as err:
            _LOGGER.warning(
                "SPH: freie Tage konnten nicht aus %s gelesen werden: %s",
                FREE_DAY_CALENDAR_ENTITY,
                err,
            )
            return []

        entity_result = (response or {}).get(FREE_DAY_CALENDAR_ENTITY, {})
        events = entity_result.get("events", []) if isinstance(entity_result, dict) else []
        free_days: set[str] = set()
        for event in events or []:
            if isinstance(event, dict):
                free_days.update(self._event_dates(event))

        result = sorted(free_days)
        _LOGGER.debug(
            "SPH: %s liefert %d freie Tage im Stundenplan-Zeitraum",
            FREE_DAY_CALENDAR_ENTITY,
            len(result),
        )
        return result

    async def _async_update_data(self):
        if not self.enabled:
            self._last_successful_data = None
            return {}

        try:
            data = await self.hass.async_add_executor_job(self.client.get_timetable)
            if not isinstance(data, dict) or not data:
                raise ValueError("Stundenplan-Antwort enthält keine gültigen Daten.")

            data = dict(data)
            data["free_days"] = await self._async_free_days()
            data["free_day_calendar"] = (
                FREE_DAY_CALENDAR_ENTITY
                if self.hass.states.get(FREE_DAY_CALENDAR_ENTITY) is not None
                else ""
            )
            self._last_successful_data = data
            return data
        except Exception as err:
            if self._last_successful_data is not None:
                _LOGGER.warning(
                    "SPH: Stundenplan konnte nicht aktualisiert werden (%s); "
                    "letzte erfolgreich geladene Daten bleiben erhalten.",
                    err,
                )
            raise UpdateFailed(str(err)) from err
