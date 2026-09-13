from __future__ import annotations

import json

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ...api.subjects import subject_name
from ...const import CONF_CHILD_NAME, CONF_CHILD_SHORTCUT
from ...school_profiles import get_school_profile
from ..stundenplan.sensor import child_label
from .helpers import entries_for, plan_days, today, tomorrow


def enrich_entries(entries):
    """Add a normalized long subject name to every substitution entry."""
    return [
        dict(entry, fach_lang=subject_name(entry.get("fach")))
        for entry in (entries or [])
    ]


def vertretung_payload(coordinator, timetable_coordinator, entry) -> dict:
    """Build the complete substitution-plan payload for normal and JSON sensors."""
    data = coordinator.data or coordinator.last_successful_data or {}
    days = plan_days(data)
    timetable_data = (
        timetable_coordinator.data
        or getattr(timetable_coordinator, "last_successful_data", None)
        or {}
    )
    heute = enrich_entries(entries_for(data, today()))
    morgen = enrich_entries(entries_for(data, tomorrow()))
    payload = {
        "kind": entry.data.get(CONF_CHILD_NAME, ""),
        "kind_kürzel": entry.data.get(CONF_CHILD_SHORTCUT, ""),
        "klasse": timetable_data.get("klasse", ""),
        "tage": [
            dict(day, eintraege=enrich_entries(day.get("eintraege")))
            for day in days
        ],
        "heute": heute,
        "morgen": morgen,
        "anzahl_heute": len(heute),
        "anzahl_morgen": len(morgen),
        "entfaelle_heute": sum(1 for item in heute if item.get("entfall")),
        "entfaelle_morgen": sum(1 for item in morgen if item.get("entfall")),
        "hinweise": [note for day in days for note in day.get("hinweise", [])],
        "aktualisiert": data.get("aktualisiert"),
        "wird_aktualisiert": bool(data.get("wird_aktualisiert")),
        "geplante_tage": [day.get("datum") for day in days],
        "attribution": "Schulportal Hessen",
    }
    return get_school_profile(entry).transform_substitution_payload(
        payload,
        coordinator.hass,
    )


def compact_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class SphVertretungSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing the published substitution plan."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:account-switch"
    _attr_native_unit_of_measurement = "Einträge"

    def __init__(self, coordinator, timetable_coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self.timetable_coordinator = timetable_coordinator
        self._attr_unique_id = f"{entry.entry_id}_vertretungsplan"
        self._attr_name = f"Vertretungsplan {child_label(entry)}"

    def _current_data(self):
        return self.coordinator.data or self.coordinator.last_successful_data or {}

    @property
    def available(self):
        return self.coordinator.enabled and bool(self._current_data())

    @property
    def native_value(self):
        return sum(day.get("anzahl", 0) for day in plan_days(self._current_data()))

    @property
    def extra_state_attributes(self):
        return vertretung_payload(self.coordinator, self.timetable_coordinator, self.entry)


class SphVertretungJsonSensor(CoordinatorEntity, SensorEntity):
    """Substitution plan as compact JSON for ESPHome and external clients."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:code-json"

    def __init__(self, coordinator, timetable_coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self.timetable_coordinator = timetable_coordinator
        self._attr_unique_id = f"{entry.entry_id}_vertretungsplan_json"
        self._attr_name = f"Vertretungsplan {child_label(entry)} JSON"

    @property
    def available(self):
        return self.coordinator.enabled and bool(
            self.coordinator.data or self.coordinator.last_successful_data
        )

    @property
    def native_value(self):
        return "verfügbar" if self.available else "unbekannt"

    @property
    def extra_state_attributes(self):
        value = compact_json(
            vertretung_payload(self.coordinator, self.timetable_coordinator, self.entry)
        )
        return {
            "json": value,
            "format": "application/json",
            "bytes": len(value.encode("utf-8")),
        }
