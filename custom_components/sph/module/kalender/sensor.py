from __future__ import annotations

from collections import Counter
import json

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ...const import CONF_CHILD_NAME, CONF_CHILD_SHORTCUT
from ...school_profiles import get_school_profile
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
    profile = get_school_profile(entry)
    events = relevant_calendar_events(
        coordinator.data,
        coordinator.event_types,
    )
    transformed = [profile.transform_calendar_item(event, coordinator.hass) for event in events]
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
        for event in sorted(transformed, key=lambda item: str(item.get("start", "")))
    ]
    payload = {
        "kind": entry.data.get(CONF_CHILD_NAME, ""),
        "kind_kürzel": entry.data.get(CONF_CHILD_SHORTCUT, ""),
        "klasse": timetable_data.get("klasse", ""),
        "kalenderarten": list(coordinator.event_types),
        "termine_gesamt": len(items),
        "termine": items,
    }
    return profile.transform_calendar_payload(payload, coordinator.hass)


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
        events = relevant_calendar_events(
            self.coordinator.data,
            self.coordinator.event_types,
        )
        profile = get_school_profile(self.entry)
        transformed = [
            profile.transform_calendar_item(event, self.coordinator.hass)
            for event in events
        ]
        timetable_data = self.timetable_coordinator.data or {}
        art_counts = Counter(
            str(event.get("art", "")).strip()
            for event in transformed
            if str(event.get("art", "")).strip()
        )
        responsible_counts = Counter(
            str(event.get("verantwortlich", "")).strip()
            for event in transformed
            if str(event.get("verantwortlich", "")).strip()
        )
        payload = {
            "kind": self.entry.data.get(CONF_CHILD_NAME, ""),
            "kind_kürzel": self.entry.data.get(CONF_CHILD_SHORTCUT, ""),
            "klasse": timetable_data.get("klasse", ""),
            "kalenderarten": list(self.coordinator.event_types),
            "termine": calendar_preview(transformed, self.coordinator.event_types),
            "termine_gesamt": len(transformed),
            "termine_weitere": max(0, len(transformed) - CALENDAR_ATTRIBUTE_LIMIT),
            "arten": dict(art_counts),
            "verantwortliche": dict(responsible_counts),
            "attribution": "Schulportal Hessen",
        }
        return profile.transform_calendar_payload(payload, self.coordinator.hass)


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
