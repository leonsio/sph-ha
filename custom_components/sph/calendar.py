"""Native Home Assistant calendar platform for SPH tests and exams."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .module.lerngruppen.calendar import SphLearningGroupsCalendar
from .module.stundenplan.sensor import child_label


def _event_datetime(value: str, all_day: bool, hass) -> date | datetime | None:
    """Convert an SPH ISO value to the type expected by CalendarEvent."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    if all_day:
        return parsed.date()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.get_time_zone(hass.config.time_zone))
    return parsed


def _calendar_event(item: dict, hass) -> CalendarEvent | None:
    """Convert one cached SPH event to a Home Assistant CalendarEvent."""
    all_day = bool(item.get("all_day", False))
    start = _event_datetime(item.get("start", ""), all_day, hass)
    end = _event_datetime(item.get("end", ""), all_day, hass)
    if start is None:
        return None

    if all_day:
        if end is None or end <= start:
            end = start + timedelta(days=1)
    else:
        if end is None or end <= start:
            end = start + timedelta(minutes=1)

    art = str(item.get("art", "")).strip()
    description = str(item.get("description", "")).strip()
    if art:
        description = f"Art: {art}" + (f"\n{description}" if description else "")

    return CalendarEvent(
        start=start,
        end=end,
        summary=str(item.get("summary", "")).strip() or art or "Schultermin",
        description=description or None,
        location=str(item.get("location", "")).strip() or None,
        uid=str(item.get("uid", "")).strip() or None,
    )


class SphSchoolCalendar(CoordinatorEntity, CalendarEntity):
    """Read-only calendar containing selected SPH calendar categories."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-school"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_native_calendar"
        self._attr_name = f"Schulkalender {child_label(entry)}"

    def _events(self) -> list[CalendarEvent]:
        events = []
        for item in self.coordinator.data or []:
            event = _calendar_event(item, self.hass)
            if event is not None:
                events.append(event)
        return sorted(events, key=lambda event: self._sort_key(event.start))

    def _sort_key(self, value: date | datetime) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=dt_util.get_time_zone(self.hass.config.time_zone))
            return value
        return datetime.combine(
            value,
            datetime.min.time(),
            tzinfo=dt_util.get_time_zone(self.hass.config.time_zone),
        )

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        for event in self._events():
            if self._sort_key(event.end) > now:
                return event
        return None

    async def async_get_events(
        self,
        hass,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        result = []
        for event in self._events():
            event_start = self._sort_key(event.start)
            event_end = self._sort_key(event.end)
            if event_end > start_date and event_start < end_date:
                result.append(event)
        return result


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SphSchoolCalendar(data["calendar"], entry),
            SphLearningGroupsCalendar(data["lerngruppen"], entry),
        ]
    )
