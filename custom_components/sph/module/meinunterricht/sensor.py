from __future__ import annotations

import json

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ...const import CONF_CHILD_NAME, CONF_CHILD_SHORTCUT


def child_label(entry) -> str:
    name = str(entry.data.get(CONF_CHILD_NAME, "")).strip()
    shortcut = str(entry.data.get(CONF_CHILD_SHORTCUT, "")).strip()
    if name and shortcut:
        return f"{name} ({shortcut})"
    return name or shortcut or "Schulportal Hessen"


def meinunterricht_payload(coordinator, entry) -> dict:
    """Build the complete Mein Unterricht payload."""
    tasks = coordinator.data or []
    return {
        "kind": entry.data.get(CONF_CHILD_NAME, ""),
        "kind_kürzel": entry.data.get(CONF_CHILD_SHORTCUT, ""),
        "aufgaben": tasks,
        "anzahl": len(tasks),
        "unerledigt": sum(not task.get("erledigt", False) for task in tasks),
        "erledigt": sum(bool(task.get("erledigt", False)) for task in tasks),
    }


def compact_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class SphMeinUnterrichtSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing current homework entries from Mein Unterricht."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:home-edit"
    _attr_native_unit_of_measurement = "Aufgaben"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_meinunterricht"
        self._attr_name = f"Mein Unterricht {child_label(entry)}"

    @property
    def native_value(self):
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self):
        payload = meinunterricht_payload(self.coordinator, self.entry)
        return {
            "aufgaben": payload["aufgaben"],
            "anzahl": payload["anzahl"],
            "unerledigt": payload["unerledigt"],
            "erledigt": payload["erledigt"],
        }


class SphMeinUnterrichtJsonSensor(CoordinatorEntity, SensorEntity):
    """Mein Unterricht as one JSON string for simple external clients."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:code-json"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_meinunterricht_json"
        self._attr_name = f"Mein Unterricht {child_label(entry)} JSON"

    @property
    def native_value(self):
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self):
        value = compact_json(meinunterricht_payload(self.coordinator, self.entry))
        return {
            "json": value,
            "format": "application/json",
            "bytes": len(value.encode("utf-8")),
        }
