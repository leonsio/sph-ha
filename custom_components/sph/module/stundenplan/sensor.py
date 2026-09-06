from __future__ import annotations

from datetime import timedelta
import json
import re

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from ...const import CONF_CHILD_NAME, CONF_CHILD_SHORTCUT

SUBJECT_NAMES = {
    "M": "Mathematik", "D": "Deutsch", "E": "Englisch", "F": "Französisch", "L": "Latein",
    "G": "Geschichte", "GE": "Geschichte", "EK": "Erdkunde", "POW": "Politik und Wirtschaft",
    "PW": "Politik und Wirtschaft", "PH": "Physik", "CH": "Chemie", "BIO": "Biologie",
    "SP": "Sport", "MU": "Musik", "ETH": "Ethik", "RKA": "Religion katholisch",
    "REV": "Religion evangelisch", "RELI": "Religion", "INF": "Informatik", "KU": "Kunst",
    "LRS": "Lese-Rechtschreib-Schwäche",
}


def subject_name(subject):
    if not subject:
        return subject
    value = str(subject).strip()
    match = re.match(r"^([A-Za-zÄÖÜäöü]+)(\d+)(.*)$", value)
    if match:
        code, number, suffix = match.groups()
        base = SUBJECT_NAMES.get(code.upper())
        if base:
            return f"{base} {number}{suffix}"
    return SUBJECT_NAMES.get(value.upper(), value)


def enrich_days(days):
    return [
        [dict(lesson, fach=subject_name(lesson.get("subject"))) for lesson in day]
        for day in (days or [])
    ]


def child_label(entry) -> str:
    name = str(entry.data.get(CONF_CHILD_NAME, "")).strip()
    shortcut = str(entry.data.get(CONF_CHILD_SHORTCUT, "")).strip()
    if name and shortcut:
        return f"{name} ({shortcut})"
    return name or shortcut or "Schulportal Hessen"


def _mask_current_week_free_days(coordinator, days, free_days):
    """Remove lessons for free dates in the currently represented school week."""
    values = [list(day or []) for day in (days or [])]
    if not values or not free_days:
        return values

    tz = dt_util.get_time_zone(coordinator.hass.config.time_zone)
    today = dt_util.now().astimezone(tz).date()
    monday = today - timedelta(days=today.weekday())
    blocked = {str(value) for value in free_days}

    return [
        [] if (monday + timedelta(days=index)).isoformat() in blocked else day
        for index, day in enumerate(values)
    ]


def timetable_payload(coordinator, entry) -> dict:
    """Build the complete timetable payload shared by normal and JSON sensors."""
    data = coordinator.data or coordinator.last_successful_data or {}
    free_days = list(data.get("free_days", []) or [])
    all_days = _mask_current_week_free_days(coordinator, data.get("all", []), free_days)
    own_days = _mask_current_week_free_days(coordinator, data.get("own", []), free_days)
    return {
        "kind": entry.data.get(CONF_CHILD_NAME, ""),
        "kind_kürzel": entry.data.get(CONF_CHILD_SHORTCUT, ""),
        "klasse": data.get("klasse", ""),
        "wochenkennung": data.get("week_badge"),
        "tage": enrich_days(all_days),
        "eigener_plan": enrich_days(own_days),
        "freie_tage": free_days,
        "freie_tage_kalender": data.get("free_day_calendar", ""),
    }


def compact_json(payload: dict) -> str:
    """Serialize data as compact UTF-8 JSON for external consumers."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class SphTimetableSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_timetable"
        self._attr_name = f"Stundenplan {child_label(entry)}"

    def _current_data(self):
        """Return current data or the last successfully parsed timetable."""
        return self.coordinator.data or self.coordinator.last_successful_data or {}

    @property
    def available(self):
        """Keep the entity available when a refresh temporarily fails."""
        return bool(self._current_data())

    @property
    def native_value(self):
        return "verfügbar" if self._current_data() else "unbekannt"

    @property
    def extra_state_attributes(self):
        return timetable_payload(self.coordinator, self.entry)


class SphTimetableJsonSensor(CoordinatorEntity, SensorEntity):
    """Timetable as one JSON string for ESPHome and other simple clients."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:code-json"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_timetable_json"
        self._attr_name = f"Stundenplan {child_label(entry)} JSON"

    @property
    def available(self):
        return bool(self.coordinator.data or self.coordinator.last_successful_data)

    @property
    def native_value(self):
        # Home Assistant limits entity states to 255 characters. The complete
        # JSON therefore lives in a single string attribute instead of state.
        return "verfügbar" if self.available else "unbekannt"

    @property
    def extra_state_attributes(self):
        value = compact_json(timetable_payload(self.coordinator, self.entry))
        return {
            "json": value,
            "format": "application/json",
            "bytes": len(value.encode("utf-8")),
        }
