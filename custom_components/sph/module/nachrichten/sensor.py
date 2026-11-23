from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ...const import CONF_CHILD_NAME, CONF_CHILD_SHORTCUT, SPH_NACHRICHTEN_URL
from ..stundenplan.sensor import child_label


class SphNachrichtenUngelesenSensor(CoordinatorEntity, SensorEntity):
    """Number of unread conversations in the visible SPH inbox.

    Deliberately carries no message content: attributes end up in the
    recorder database. The card loads subjects/senders via WebSocket.
    """

    _attr_has_entity_name = False
    _attr_native_unit_of_measurement = "Nachrichten"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_nachrichten_ungelesen"
        self._attr_name = f"Nachrichten ungelesen {child_label(entry)}"

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        return data.get("ungelesen")

    @property
    def icon(self):
        return "mdi:email-alert-outline" if self.native_value else "mdi:email-check-outline"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "kind": self.entry.data.get(CONF_CHILD_NAME, ""),
            "kind_kürzel": self.entry.data.get(CONF_CHILD_SHORTCUT, ""),
            "nachrichten_gesamt": data.get("gesamt", 0),
            "abgerufen": data.get("abgerufen"),
            "portal_url": SPH_NACHRICHTEN_URL,
            "attribution": "Schulportal Hessen",
        }
