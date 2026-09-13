from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ...api.client import SphAuthClient
from ...const import (
    CONF_MODULE_VERTRETUNG,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MODULE_ENABLED,
    DEFAULT_UPDATE_INTERVAL,
)
from .client import SphVertretungClient

_LOGGER = logging.getLogger(__name__)


class SphVertretungCoordinator(DataUpdateCoordinator):
    """Coordinator for the SPH substitution plan module."""

    def __init__(self, hass, entry, auth: SphAuthClient):
        self.entry = entry
        self.client = SphVertretungClient(auth)
        self.enabled = bool(entry.data.get(CONF_MODULE_VERTRETUNG, DEFAULT_MODULE_ENABLED))
        self._last_successful_data = None
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Schulportal Hessen Vertretungsplan",
            update_interval=(
                timedelta(minutes=int(entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)))
                if self.enabled
                else None
            ),
        )

    @property
    def last_successful_data(self):
        return self._last_successful_data

    async def _async_update_data(self):
        if not self.enabled:
            return {}
        try:
            data = await self.hass.async_add_executor_job(self.client.get_substitutions)
            if not isinstance(data, dict):
                raise ValueError("Vertretungsplan-Antwort enthält keine gültigen Daten.")
            self._last_successful_data = data
            return data
        except Exception as err:
            if self._last_successful_data is not None:
                _LOGGER.warning(
                    "SPH: Vertretungsplan konnte nicht aktualisiert werden (%s); letzte erfolgreich geladene Daten bleiben erhalten.",
                    err,
                )
            raise UpdateFailed(str(err)) from err
