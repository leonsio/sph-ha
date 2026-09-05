from __future__ import annotations

import json

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ...const import CONF_CHILD_NAME, CONF_CHILD_SHORTCUT
from ..stundenplan.sensor import child_label


def learning_groups_payload(coordinator, entry) -> dict:
    items = list(coordinator.data or [])
    return {
        "kind": entry.data.get(CONF_CHILD_NAME, ""),
        "kind_kürzel": entry.data.get(CONF_CHILD_SHORTCUT, ""),
        "anzahl": len(items),
        "leistungskontrollen": items,
    }


def compact_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class SphLearningGroupsSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing SPH Leistungskontrollen from Lerngruppen."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:school"
    _attr_native_unit_of_measurement = "Termine"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_lerngruppen"
        self._attr_name = f"Lerngruppen {child_label(entry)}"

    @property
    def native_value(self):
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self):
        return learning_groups_payload(self.coordinator, self.entry)


class SphLearningGroupsJsonSensor(CoordinatorEntity, SensorEntity):
    """Lerngruppen data as one JSON string for simple external clients."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:code-json"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_lerngruppen_json"
        self._attr_name = f"Lerngruppen {child_label(entry)} JSON"

    @property
    def native_value(self):
        return "verfügbar" if self.coordinator.data is not None else "unbekannt"

    @property
    def extra_state_attributes(self):
        value = compact_json(learning_groups_payload(self.coordinator, self.entry))
        return {
            "json": value,
            "format": "application/json",
            "bytes": len(value.encode("utf-8")),
        }
