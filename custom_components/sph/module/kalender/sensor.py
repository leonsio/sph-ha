from __future__ import annotations

from collections import Counter
import json

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ...const import CONF_CHILD_NAME, CONF_CHILD_SHORTCUT
from ..stundenplan.sensor import child_label
from .coordinator import relevant_calendar_events

CALENDAR_ATTRIBUTE_LIMIT = 50


def calendar_preview(events, event_types=None):
    """Return only configured calendar entries for card consumption."""
    relevant = relevant_calendar_events(events, event_types)
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


def calendar_json_payload(coordinator, timetable_coordinator, entry) -> dict:
    """Build complete configured calendar data for JSON consumers."""
    events = relevant_calendar_events(
        coordinator.data,
        coordinator.event_types,
    )
    timetable_data = timetable_coordinator.data or {}
    items = [
        {
            "start": event.get("start", ""),
            "end": event.get("end", ""),
            "all_day": bool(event.get("all_day", False)),
            "summary": event.get("summary", ""),
            "description": event.get("description", ""),
            "art": event.get("art", ""),
            "verantwortlich": event.get("verantwortlich", ""),
            "location": event.get("location", ""),
            "uid": event.get("uid", ""),
        }
        for event in sorted(events, key=lambda item: str(item.get("start", "")))
    ]
    return {
        "kind": entry.data.get(CONF_CHILD_NAME, ""),
        "kind_kürzel": entry.data.get(CONF_CHILD_SHORTCUT, ""),
        "klasse": timetable_data.get("klasse", ""),
        "kalenderarten": list(coordinator.event_types),
        "termine_gesamt": len(items),
        "termine": items,
    }


def compact_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


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
        return len(
            relevant_calendar_events(
                self.coordinator.data,
                self.coordinator.event_types,
            )
        )

    @property
    def extra_state_attributes(self):
        # Filter again at entity level deliberately. This guarantees that the
        # legacy sensor and all cards consuming its `termine` attribute expose
        # only calendar categories selected in the integration settings.
        events = relevant_calendar_events(
            self.coordinator.data,
            self.coordinator.event_types,
        )
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
            "kalenderarten": list(self.coordinator.event_types),
            "termine": calendar_preview(events, self.coordinator.event_types),
            "termine_gesamt": len(events),
            "termine_weitere": max(0, len(events) - CALENDAR_ATTRIBUTE_LIMIT),
            "arten": dict(art_counts),
            "verantwortliche": dict(responsible_counts),
            "attribution": "Schulportal Hessen",
        }


class SphCalendarJsonSensor(CoordinatorEntity, SensorEntity):
    """Configured SPH calendar as one JSON string for external clients."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:code-json"
    _attr_native_unit_of_measurement = "Termine"

    def __init__(self, coordinator, timetable_coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self.timetable_coordinator = timetable_coordinator
        self._attr_unique_id = f"{entry.entry_id}_calendar_json"
        self._attr_name = f"Schulkalender {child_label(entry)} JSON"

    @property
    def native_value(self):
        return len(
            relevant_calendar_events(
                self.coordinator.data,
                self.coordinator.event_types,
            )
        )

    @property
    def extra_state_attributes(self):
        value = compact_json(
            calendar_json_payload(
                self.coordinator,
                self.timetable_coordinator,
                self.entry,
            )
        )
        return {
            "json": value,
            "format": "application/json",
            "bytes": len(value.encode("utf-8")),
        }
