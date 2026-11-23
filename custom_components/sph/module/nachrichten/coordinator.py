from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from ...api.client import SphAuthClient
from ...const import (
    CONF_CHILD_NAME,
    CONF_CHILD_SHORTCUT,
    CONF_MODULE_NACHRICHTEN,
    CONF_NACHRICHTEN_INTERVAL,
    DEFAULT_MODULE_NACHRICHTEN_ENABLED,
    DEFAULT_NACHRICHTEN_INTERVAL,
    DOMAIN,
    EVENT_NEUE_NACHRICHT,
    SPH_NACHRICHTEN_URL,
)
from .client import SphNachrichtenClient
from .parser import detect_new, summarize_new, unread_state

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1


def nachrichten_store(hass, entry_id: str) -> Store:
    """Persisted unread flags per message id, used to detect new messages."""
    return Store(hass, STORAGE_VERSION, f"{DOMAIN}_nachrichten_{entry_id}")


class SphNachrichtenCoordinator(DataUpdateCoordinator):
    """Poll the SPH inbox and detect newly unread messages.

    The first poll must not run during integration setup: automations attach
    their triggers only once Home Assistant has started, so events fired
    earlier would be lost while the stored state already moved on. Setup
    therefore only loads the stored state; __init__ schedules the first poll
    via ``async_at_started``.
    """

    def __init__(self, hass, entry, auth: SphAuthClient):
        self.entry = entry
        self.client = SphNachrichtenClient(auth)
        self.enabled = bool(
            entry.data.get(CONF_MODULE_NACHRICHTEN, DEFAULT_MODULE_NACHRICHTEN_ENABLED)
        )
        self.store = nachrichten_store(hass, entry.entry_id)
        self._previous: dict[str, bool] | None = None
        # Messages that became unread during the most recent successful poll,
        # and a counter so listeners can tell polls apart.
        self.new_messages: list[dict] = []
        self.poll_count = 0
        interval = int(entry.data.get(CONF_NACHRICHTEN_INTERVAL, DEFAULT_NACHRICHTEN_INTERVAL))
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Schulportal Hessen Nachrichten",
            update_interval=timedelta(minutes=interval) if self.enabled else None,
        )

    async def async_load_store(self) -> None:
        """Restore the unread state of the previous poll (no portal access)."""
        stored = await self.store.async_load()
        if isinstance(stored, dict) and isinstance(stored.get("unread"), dict):
            self._previous = {str(key): bool(value) for key, value in stored["unread"].items()}

    async def _async_update_data(self):
        self.new_messages = []
        if not self.enabled:
            return {"nachrichten": [], "ungelesen": 0, "gesamt": 0, "abgerufen": None}

        try:
            items = await self.hass.async_add_executor_job(self.client.get_inbox)
        except Exception as err:
            raise UpdateFailed(str(err)) from err

        self.new_messages = detect_new(self._previous, items)
        current = unread_state(items)
        if current != self._previous:
            self._previous = current
            await self.store.async_save({"unread": current})
        self.poll_count += 1

        for item in self.new_messages:
            self.hass.bus.async_fire(EVENT_NEUE_NACHRICHT, self.message_event_data(item))
        if self.new_messages:
            _LOGGER.debug("SPH: %d neue Nachricht(en) erkannt", len(self.new_messages))

        return {
            "nachrichten": items,
            "ungelesen": sum(1 for item in items if item["ungelesen"]),
            "gesamt": len(items),
            "abgerufen": dt_util.utcnow().isoformat(),
        }

    def _context(self) -> dict:
        return {
            "entry_id": self.entry.entry_id,
            "kind": self.entry.data.get(CONF_CHILD_NAME, ""),
            "kind_kürzel": self.entry.data.get(CONF_CHILD_SHORTCUT, ""),
            "portal_url": SPH_NACHRICHTEN_URL,
        }

    def message_event_data(self, item: dict) -> dict:
        """Payload of the bus event, fired once per new message."""
        return {
            **self._context(),
            "absender": item["absender"],
            "betreff": item["betreff"],
            "datum": item["datum"],
        }

    def poll_event_data(self) -> dict:
        """Payload of the event entity, fired once per poll with new messages."""
        return {**self._context(), **summarize_new(self.new_messages)}
