"""WebSocket API for the Nachrichten card.

The card fetches subjects/senders on demand, so message details are not
stored in sensor attributes (and therefore not in the recorder database).

Access is not restricted to admins on purpose: dashboards are typically
used by non-admin household members, and the same data is shown to them by
the card. It is the inbox summary of the last poll, never message content.
"""
from __future__ import annotations

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from ...const import DOMAIN, SPH_NACHRICHTEN_URL

WS_TYPE_LIST = f"{DOMAIN}/nachrichten"
SENSOR_UNIQUE_ID_SUFFIX = "_nachrichten_ungelesen"


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_LIST,
        vol.Required("entity_id"): cv.entity_id,
    }
)
@callback
def ws_list_nachrichten(hass: HomeAssistant, connection, msg) -> None:
    registry_entry = er.async_get(hass).async_get(msg["entity_id"])
    if (
        registry_entry is None
        or registry_entry.platform != DOMAIN
        or registry_entry.unique_id != f"{registry_entry.config_entry_id}{SENSOR_UNIQUE_ID_SUFFIX}"
    ):
        connection.send_error(msg["id"], "not_found", "Kein SPH-Nachrichtensensor")
        return
    data = hass.data.get(DOMAIN, {}).get(registry_entry.config_entry_id) or {}
    coordinator = data.get("nachrichten")
    if coordinator is None:
        connection.send_error(msg["id"], "not_found", "Kein Nachrichten-Modul für diese Entity")
        return
    current = coordinator.data or {}
    connection.send_result(
        msg["id"],
        {
            "nachrichten": current.get("nachrichten", []),
            "ungelesen": current.get("ungelesen", 0),
            "abgerufen": current.get("abgerufen"),
            "aktiv": coordinator.enabled,
            "letzter_abruf_ok": coordinator.last_update_success,
            "portal_url": SPH_NACHRICHTEN_URL,
        },
    )


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_list_nachrichten)
