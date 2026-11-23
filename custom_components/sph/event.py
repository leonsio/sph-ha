"""Event platform for SPH (new message notifications)."""

from .const import DOMAIN
from .module.nachrichten.event import SphNeueNachrichtEvent


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data.get("nachrichten")
    if coordinator is None or not coordinator.enabled:
        return
    async_add_entities([SphNeueNachrichtEvent(coordinator, entry)])


__all__ = ["async_setup_entry", "SphNeueNachrichtEvent"]
