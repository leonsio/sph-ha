from __future__ import annotations

from datetime import date
import re

import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from ...const import DOMAIN

SERVICE_ADD = "lerngruppen_termin_hinzufuegen"
SERVICE_DELETE = "lerngruppen_termin_loeschen"

ADD_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("datum"): str,
        vol.Required("art"): cv.string,
        vol.Required("kurs"): cv.string,
        vol.Optional("dauer_minuten"): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
        vol.Optional("stunden", default=""): cv.string,
        vol.Optional("lehrkraft", default=""): cv.string,
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
    if not data or "lerngruppen" not in data:
        raise vol.Invalid(f"Kein Lerngruppen-Modul für {entity_id} gefunden")
    return data["lerngruppen"]


def _parse_date(value: str) -> str:
    text = str(value or "").strip()
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as err:
        raise vol.Invalid("datum muss im Format YYYY-MM-DD angegeben werden") from err


def _parse_periods(value: str) -> list[int]:
    text = str(value or "")
    periods: list[int] = []

    for start_raw, end_raw in re.findall(r"(\d+)\s*[-–—]\s*(\d+)", text):
        start, end = int(start_raw), int(end_raw)
        if start > end:
            start, end = end, start
        for number in range(max(1, start), min(20, end) + 1):
            if number not in periods:
                periods.append(number)

    text_without_ranges = re.sub(r"\d+\s*[-–—]\s*\d+", " ", text)
    for raw in re.findall(r"\d+", text_without_ranges):
        number = int(raw)
        if 1 <= number <= 20 and number not in periods:
            periods.append(number)

    return sorted(periods)


async def async_register_services(hass) -> None:
    """Register manual Lerngruppen services once for the integration domain."""
    if not hass.services.has_service(DOMAIN, SERVICE_ADD):
        async def _handle_add(call):
            coordinator = _coordinator_for_entity(hass, call.data["entity_id"])
            periods = _parse_periods(call.data.get("stunden", ""))
            duration = call.data.get("dauer_minuten")
            item = {
                "datum": _parse_date(call.data["datum"]),
                "art": str(call.data["art"]).strip(),
                "kurs": str(call.data["kurs"]).strip(),
                "dauer_minuten": int(duration) if duration is not None else None,
                "stunden": periods,
                "stunden_text": ", ".join(str(value) for value in periods),
                "lehrkraft": str(call.data.get("lehrkraft", "")).strip(),
                "lehrkraft_kürzel": "",
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
