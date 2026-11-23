from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..stundenplan.sensor import child_label

EVENT_TYPE_NEUE_NACHRICHT = "neue_nachricht"


class SphNeueNachrichtEvent(CoordinatorEntity, EventEntity):
    """Fires once per poll in which at least one message became unread.

    One event per poll (not per message): events triggered in the same
    instant share their timestamp state, so Home Assistant would merge them
    and state-triggered automations would only see one of them.
    """

    _attr_has_entity_name = False
    _attr_icon = "mdi:email-receive-outline"
    _attr_event_types = [EVENT_TYPE_NEUE_NACHRICHT]
    # Keep message subjects and senders out of the recorder database.
    _unrecorded_attributes = frozenset({"absender", "betreff", "nachrichten"})

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_nachrichten_event"
        self._attr_name = f"Neue Nachricht {child_label(entry)}"
        self._handled_poll = coordinator.poll_count

    @property
    def available(self):
        # An event entity keeps its last event even if a poll fails.
        return self.coordinator.enabled

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.coordinator.poll_count == self._handled_poll:
            return
        self._handled_poll = self.coordinator.poll_count
        if not self.coordinator.new_messages:
            return
        self._trigger_event(EVENT_TYPE_NEUE_NACHRICHT, self.coordinator.poll_event_data())
        self.async_write_ha_state()
