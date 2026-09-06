from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ...api.client import SphAuthClient
from ...const import (
    CONF_MODULE_STUNDENPLAN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MODULE_ENABLED,
    DEFAULT_UPDATE_INTERVAL,
)
from .client import SphTimetableClient

_LOGGER = logging.getLogger(__name__)


class SphTimetableCoordinator(DataUpdateCoordinator):
    """Coordinator for the SPH timetable module."""

    def __init__(self, hass, entry, auth: SphAuthClient):
        self.entry = entry
        self.client = SphTimetableClient(auth)
        self.enabled = bool(entry.data.get(CONF_MODULE_STUNDENPLAN, DEFAULT_MODULE_ENABLED))
        self._last_successful_data = None
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Schulportal Hessen Stundenplan",
            update_interval=(
                timedelta(minutes=int(entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)))
                if self.enabled
                else None
            ),
        )

    @property
    def last_successful_data(self):
        """Return the last successfully parsed timetable data."""
        return self._last_successful_data

    async def _async_update_data(self):
        if not self.enabled:
            self._last_successful_data = None
            return {}

        try:
            data = await self.hass.async_add_executor_job(self.client.get_timetable)
            if not isinstance(data, dict) or not data:
                raise ValueError("Stundenplan-Antwort enthält keine gültigen Daten.")

            self._last_successful_data = data
            return data
        except Exception as err:
            if self._last_successful_data is not None:
                _LOGGER.warning(
                    "SPH: Stundenplan konnte nicht aktualisiert werden (%s); "
                    "letzte erfolgreich geladene Daten bleiben erhalten.",
                    err,
                )
            raise UpdateFailed(str(err)) from err
