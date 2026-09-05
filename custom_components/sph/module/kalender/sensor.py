from __future__ import annotations

from collections import Counter

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ...const import CONF_CHILD_NAME, CONF_CHILD_SHORTCUT
from ..stundenplan.sensor import child_label
from .coordinator import relevant_calendar_events

CALENDAR_ATTRIBUTE_LIMIT = 50


def calendar_preview(events):
    """Return only relevant calendar entries for card consumption."""
    relevant = relevant_calendar_events(events)
    return [
        {
            "start": event.get("start", ""),
            "end": event.get("end", ""),
            "all_day": bool(event.get("all_day", False)),
            "summary": event.get("summary", ""),
            "art": event.get("art", ""),
            "verantwortlich": event.get("verantwortlich", ""),
            "location": event.get("location", ""),
            "uid": event.get("uid", ""),
        }
        for event in sorted(relevant, key=lambda item: str(item.get("start", "")))[:CALENDAR_ATTRIBUTE_LIMIT]
    ]


class SphCalendarSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-multiple"
    _attr_native_unit_of_measurement = "Termine"

    def __init__(self, coordinator, timetable_coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self.timetable_coordinator = timetable_coordinator
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_name = f"Schulkalender {child_label(entry)}"

    @property
    def native_value(self):
        return len(relevant_calendar_events(self.coordinator.data))

    @property
    def extra_state_attributes(self):
        # Filter again at entity level deliberately. The coordinator already
        # limits its data to Arbeiten/Klausuren, but this guarantees that the
        # legacy sensor and all cards consuming its `termine` attribute can
        # never expose or use other SPH calendar categories.
        events = relevant_calendar_events(self.coordinator.data)
        timetable_data = self.timetable_coordinator.data or {}
        art_counts = Counter(
            str(event.get("art", "")).strip()
            for event in events
            if str(event.get("art", "")).strip()
        )
        responsible_counts = Counter(
            str(event.get("verantwortlich", "")).strip()
            for event in events
            if str(event.get("verantwortlich", "")).strip()
        )
        return {
            "kind": self.entry.data.get(CONF_CHILD_NAME, ""),
            "kind_kürzel": self.entry.data.get(CONF_CHILD_SHORTCUT, ""),
            "klasse": timetable_data.get("klasse", ""),
            "termine": calendar_preview(events),
            "termine_gesamt": len(events),
            "termine_weitere": max(0, len(events) - CALENDAR_ATTRIBUTE_LIMIT),
            "arten": dict(art_counts),
            "verantwortliche": dict(responsible_counts),
            "attribution": "Schulportal Hessen",
        }
