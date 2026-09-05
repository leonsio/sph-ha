from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from ..stundenplan.sensor import child_label


def _as_calendar_event(item: dict, hass) -> CalendarEvent | None:
    all_day = bool(item.get("all_day", False))
    try:
        if all_day:
            start = date.fromisoformat(str(item.get("datum", "")))
            end = start + timedelta(days=1)
        else:
            start = datetime.fromisoformat(str(item.get("start", "")))
            end = datetime.fromisoformat(str(item.get("end", "")))
            tz = dt_util.get_time_zone(hass.config.time_zone)
            if start.tzinfo is None:
                start = start.replace(tzinfo=tz)
            if end.tzinfo is None:
                end = end.replace(tzinfo=tz)
    except (TypeError, ValueError):
        return None

    description_lines = []
    if item.get("art"):
        description_lines.append(f"Art: {item['art']}")
    if item.get("stunden_text"):
        description_lines.append(f"Stunden: {item['stunden_text']}")
    if item.get("dauer_minuten") is not None:
        description_lines.append(f"Dauer: {item['dauer_minuten']} Min.")
    if item.get("lehrkraft"):
        teacher = item["lehrkraft"]
        if item.get("lehrkraft_kürzel"):
            teacher = f"{teacher} ({item['lehrkraft_kürzel']})"
        description_lines.append(f"Lehrkraft: {teacher}")

    return CalendarEvent(
        start=start,
        end=end,
        summary=str(item.get("summary", "")).strip() or "Leistungskontrolle",
        description="\n".join(description_lines) or None,
        uid=str(item.get("uid", "")).strip() or None,
    )


class SphLearningGroupsCalendar(CoordinatorEntity, CalendarEntity):
    """Read-only calendar containing Lerngruppen Leistungskontrollen."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-edit"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_lerngruppen_calendar"
        self._attr_name = f"Lerngruppen {child_label(entry)}"

    @staticmethod
    def _sort_key(value: date | datetime, hass) -> datetime:
        tz = dt_util.get_time_zone(hass.config.time_zone)
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=tz)
        return datetime.combine(value, datetime.min.time(), tzinfo=tz)

    def _events(self) -> list[CalendarEvent]:
        events = []
        for item in self.coordinator.data or []:
            event = _as_calendar_event(item, self.hass)
            if event is not None:
                events.append(event)
        return sorted(events, key=lambda event: self._sort_key(event.start, self.hass))

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        for event in self._events():
            if self._sort_key(event.end, self.hass) > now:
                return event
        return None

    async def async_get_events(self, hass, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        result = []
        for event in self._events():
            event_start = self._sort_key(event.start, hass)
            event_end = self._sort_key(event.end, hass)
            if event_end > start_date and event_start < end_date:
                result.append(event)
        return result
