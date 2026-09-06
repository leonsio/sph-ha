from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
import re

from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from ...api.client import SphAuthClient
from ...const import (
    CONF_MODULE_MEINUNTERRICHT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MODULE_ENABLED,
    DEFAULT_UPDATE_INTERVAL,
)
from .client import SphMeinUnterrichtClient, WEEKDAYS
from .storage import SphMeinUnterrichtManualStore

_LOGGER = logging.getLogger(__name__)

MANUAL_CLEANUP_INTERVAL = timedelta(hours=1)


class SphMeinUnterrichtCoordinator(DataUpdateCoordinator):
    """Coordinator for SPH Mein Unterricht and locally added homework."""

    def __init__(self, hass, entry, auth: SphAuthClient):
        self.entry = entry
        self.client = SphMeinUnterrichtClient(auth)
        self.enabled = bool(entry.data.get(CONF_MODULE_MEINUNTERRICHT, DEFAULT_MODULE_ENABLED))
        self.manual_store = SphMeinUnterrichtManualStore(hass, entry.entry_id)
        self._manual_items: list[dict] = []
        self._sph_items: list[dict] = []
        self._manual_cleanup_unsub = None
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Schulportal Hessen Mein Unterricht",
            update_interval=(
                timedelta(minutes=int(entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)))
                if self.enabled
                else None
            ),
        )

    def _today(self) -> date:
        tz = dt_util.get_time_zone(self.hass.config.time_zone)
        return dt_util.now().astimezone(tz).date()

    async def async_load_manual_items(self) -> None:
        """Load local homework and immediately purge expired entries."""
        self._manual_items = await self.manual_store.async_load()
        await self._async_purge_manual_items(publish=False)
        if self.enabled and self._manual_items:
            self.async_set_updated_data(self._merged_items())

    async def async_add_manual_item(self, item: dict) -> dict:
        """Persist one manual homework item and publish merged data immediately."""
        stored = await self.manual_store.async_add(self._normalize_item(item, "manuell"))
        self._manual_items = self.manual_store.items
        await self._async_purge_manual_items(publish=False)
        if self.enabled:
            self.async_set_updated_data(self._merged_items())
        return stored

    async def async_delete_manual_item(self, item_id: str) -> bool:
        """Delete one manual homework item and publish merged data immediately."""
        changed = await self.manual_store.async_delete(item_id)
        if changed:
            self._manual_items = self.manual_store.items
            if self.enabled:
                self.async_set_updated_data(self._merged_items())
        return changed

    async def _async_purge_manual_items(self, publish: bool = True) -> int:
        """Delete manual homework seven days after the homework date."""
        removed = await self.manual_store.async_purge_expired(self._today())
        if not removed:
            return 0

        self._manual_items = self.manual_store.items
        if publish and self.enabled:
            self.async_set_updated_data(self._merged_items())
        _LOGGER.debug("SPH: %d abgelaufene manuelle Hausaufgabe(n) gelöscht", removed)
        return removed

    def async_start_manual_cleanup(self) -> None:
        """Periodically clean expired local homework without SPH network traffic."""
        if self._manual_cleanup_unsub is not None:
            return

        async def _cleanup(_now):
            await self._async_purge_manual_items()

        self._manual_cleanup_unsub = async_track_time_interval(
            self.hass,
            _cleanup,
            MANUAL_CLEANUP_INTERVAL,
        )

    def async_stop_manual_cleanup(self) -> None:
        if self._manual_cleanup_unsub is not None:
            self._manual_cleanup_unsub()
            self._manual_cleanup_unsub = None

    async def _async_update_data(self):
        if not self.enabled:
            return []

        await self._async_purge_manual_items(publish=False)
        try:
            items = await self.hass.async_add_executor_job(self.client.get_homework)
            self._sph_items = [
                self._normalize_item(item, "sph")
                for item in (items or [])
                if isinstance(item, dict)
            ]
            return self._merged_items()
        except Exception as err:
            # DataUpdateCoordinator keeps the last successful data on UpdateFailed.
            raise UpdateFailed(str(err)) from err

    def _merged_items(self) -> list[dict]:
        """Combine SPH and manual homework, preferring SPH on duplicates."""
        sph_items = [dict(item) for item in self._sph_items]
        manual_items = [self._normalize_item(item, "manuell") for item in self._manual_items]
        sph_keys = {self._duplicate_key(item) for item in sph_items}
        combined = [
            *sph_items,
            *(item for item in manual_items if self._duplicate_key(item) not in sph_keys),
        ]
        return sorted(
            combined,
            key=lambda item: (
                str(item.get("datum", "")),
                str(item.get("fach", "")).casefold(),
                str(item.get("aufgabe", "")).casefold(),
            ),
        )

    @staticmethod
    def _duplicate_key(item: dict) -> tuple:
        """Build a conservative key for the same homework from both sources."""
        normalize = lambda value: re.sub(r"\s+", " ", str(value or "").strip()).casefold()
        return (
            str(item.get("datum", "")),
            normalize(item.get("fach", "")),
            normalize(item.get("aufgabe", "")),
        )

    @staticmethod
    def _normalize_item(item: dict, source: str) -> dict:
        result = dict(item)
        result["quelle"] = source
        value = str(result.get("datum", "")).strip()
        try:
            parsed = datetime.fromisoformat(value).date()
        except ValueError:
            try:
                parsed = date.fromisoformat(value)
            except ValueError:
                parsed = None
        if parsed is not None:
            result["datum"] = parsed.isoformat()
            result["wochentag"] = str(result.get("wochentag") or WEEKDAYS[parsed.weekday()])
        else:
            result["wochentag"] = str(result.get("wochentag") or "")
        result["erledigt"] = bool(result.get("erledigt", False))
        return result
