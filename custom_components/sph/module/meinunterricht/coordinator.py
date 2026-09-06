from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ...api.client import SphAuthClient
from ...const import (
    CONF_MODULE_MEINUNTERRICHT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MODULE_ENABLED,
    DEFAULT_UPDATE_INTERVAL,
)
from .client import SphMeinUnterrichtClient

_LOGGER = logging.getLogger(__name__)


class SphMeinUnterrichtCoordinator(DataUpdateCoordinator):
    """Coordinator for the SPH Mein-Unterricht module."""

    def __init__(self, hass, entry, auth: SphAuthClient):
        self.entry = entry
        self.client = SphMeinUnterrichtClient(auth)
        self.enabled = bool(entry.data.get(CONF_MODULE_MEINUNTERRICHT, DEFAULT_MODULE_ENABLED))
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

    async def _async_update_data(self):
        if not self.enabled:
            return []

        try:
            return await self.hass.async_add_executor_job(self.client.get_homework)
        except Exception as err:
            # DataUpdateCoordinator keeps the last successful data on UpdateFailed.
            raise UpdateFailed(str(err)) from err
