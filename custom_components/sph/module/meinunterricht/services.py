from __future__ import annotations

from datetime import date

import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from ...const import DOMAIN

SERVICE_ADD = "meinunterricht_hausaufgabe_hinzufuegen"
SERVICE_DELETE = "meinunterricht_hausaufgabe_loeschen"

ADD_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("datum"): str,
        vol.Required("fach"): cv.string,
        vol.Required("aufgabe"): cv.string,
        vol.Optional("kurs", default=""): cv.string,
        vol.Optional("thema", default=""): cv.string,
        vol.Optional("lehrer", default=""): cv.string,
        vol.Optional("erledigt", default=False): cv.boolean,
    }
)

DELETE_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("id"): cv.string,
    }
)


def _coordinator_for_entity(hass, entity_id: str):
    registry = er.async_get(hass)
    registry_entry = registry.async_get(entity_id)
    if registry_entry is None or not registry_entry.config_entry_id:
        raise vol.Invalid(f"Keine SPH-Konfiguration für {entity_id} gefunden")

    data = hass.data.get(DOMAIN, {}).get(registry_entry.config_entry_id)
    if not data or "meinunterricht" not in data:
        raise vol.Invalid(f"Kein Mein-Unterricht-Modul für {entity_id} gefunden")
    return data["meinunterricht"]


def _parse_date(value: str) -> str:
    text = str(value or "").strip()
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as err:
        raise vol.Invalid("datum muss im Format YYYY-MM-DD angegeben werden") from err


async def async_register_services(hass) -> None:
    """Register manual Mein-Unterricht services once for the integration domain."""
    if not hass.services.has_service(DOMAIN, SERVICE_ADD):
        async def _handle_add(call):
            coordinator = _coordinator_for_entity(hass, call.data["entity_id"])
            item = {
                "datum": _parse_date(call.data["datum"]),
                "fach": str(call.data["fach"]).strip(),
                "kurs": str(call.data.get("kurs", "")).strip(),
                "lehrer": str(call.data.get("lehrer", "")).strip(),
                "thema": str(call.data.get("thema", "")).strip(),
                "aufgabe": str(call.data["aufgabe"]).strip(),
                "erledigt": bool(call.data.get("erledigt", False)),
                "entry_id": "",
                "book_id": "",
            }
            await coordinator.async_add_manual_item(item)

        hass.services.async_register(
            DOMAIN,
            SERVICE_ADD,
            _handle_add,
            schema=ADD_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_DELETE):
        async def _handle_delete(call):
            coordinator = _coordinator_for_entity(hass, call.data["entity_id"])
            await coordinator.async_delete_manual_item(call.data["id"])

        hass.services.async_register(
            DOMAIN,
            SERVICE_DELETE,
            _handle_delete,
            schema=DELETE_SCHEMA,
        )
