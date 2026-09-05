from __future__ import annotations

from pathlib import Path
import logging

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

from .api.client import SphAuthClient
from .const import CONF_CHILD_NAME, CONF_CHILD_SHORTCUT, CONF_PASSWORD, CONF_SCHOOL_ID, CONF_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
CARD_VERSION = "0.3.16"
CARD_URLS = (
    f"/api/{DOMAIN}/static/sph-stundenplan-card.js?v={CARD_VERSION}",
    f"/api/{DOMAIN}/static/sph-stundenplan-tag-card.js?v={CARD_VERSION}",
    f"/api/{DOMAIN}/static/sph-stundenplan-grid-card.js?v={CARD_VERSION}",
    f"/api/{DOMAIN}/static/kfg-stundenplan-compat.js?v={CARD_VERSION}",
    f"/api/{DOMAIN}/static/kfg-stundenplan-card.js?v={CARD_VERSION}",
    f"/api/{DOMAIN}/static/kfg-stundenplan-tag-card.js?v={CARD_VERSION}",
    f"/api/{DOMAIN}/static/kfg-stundenplan-grid-card.js?v={CARD_VERSION}",
)


async def _register_lovelace_resources(hass: HomeAssistant) -> None:
    data = hass.data.get(LOVELACE_DATA)
    if data is None:
        return
    resources = data.resources
    if not hasattr(resources, "async_create_item"):
        return
    if not getattr(resources, "loaded", True):
        await resources.async_load()
        resources.loaded = True

    items = resources.async_items() or []
    for url in CARD_URLS:
        base_url = url.split("?", 1)[0]
        existing = next(
            (r for r in items if r.get("url", "").split("?", 1)[0] == base_url),
            None,
        )
        if existing is None:
            await resources.async_create_item({"url": url, "res_type": "module"})
            continue
        if existing.get("url") != url or existing.get("type") != "module":
            if hasattr(resources, "async_update_item"):
                await resources.async_update_item(
                    existing["id"],
                    {"url": url, "res_type": "module"},
                )


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    static_dir = Path(__file__).parent / "static"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"/api/{DOMAIN}/static", str(static_dir), False)]
    )

    # Lovelace resources are registered exactly once here. Do not also use
    # add_extra_js_url(): doing both causes the same ES module to be evaluated
    # twice, which can trigger CustomElementRegistry duplicate-definition
    # errors in Safari/iOS.
    if hass.is_running:
        hass.async_create_task(_register_lovelace_resources(hass))
    else:
        async def _on_started(_event):
            await _register_lovelace_resources(hass)
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started)
    return True


async def _migrate_sensor_entity_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    registry = er.async_get(hass)
    name = str(entry.data.get(CONF_CHILD_NAME, "")).strip()
    shortcut = str(entry.data.get(CONF_CHILD_SHORTCUT, "")).strip()
    child = "_".join(part for part in (name, shortcut) if part)
    suffix = slugify(child) if child else "schulportal_hessen"
    for unique_id, object_id in (
        (f"{entry.entry_id}_timetable", f"stundenplan_{suffix}"),
        (f"{entry.entry_id}_timetable_json", f"stundenplan_{suffix}_json"),
        (f"{entry.entry_id}_calendar", f"schulkalender_{suffix}"),
        (f"{entry.entry_id}_calendar_json", f"schulkalender_{suffix}_json"),
        (f"{entry.entry_id}_meinunterricht", f"mein_unterricht_{suffix}"),
        (f"{entry.entry_id}_meinunterricht_json", f"mein_unterricht_{suffix}_json"),
    ):
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        if not entity_id:
            continue
        desired = f"sensor.{object_id}"
        if entity_id == desired:
            continue
        if registry.async_get(desired):
            _LOGGER.warning("Kann %s nicht in %s umbenennen, da die Ziel-Entity bereits existiert", entity_id, desired)
            continue
        registry.async_update_entity(entity_id, new_entity_id=desired)

    calendar_unique_id = f"{entry.entry_id}_native_calendar"
    calendar_entity_id = registry.async_get_entity_id("calendar", DOMAIN, calendar_unique_id)
    desired_calendar = f"calendar.schulkalender_{suffix}"
    if calendar_entity_id and calendar_entity_id != desired_calendar and not registry.async_get(desired_calendar):
        registry.async_update_entity(calendar_entity_id, new_entity_id=desired_calendar)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from .module.kalender.coordinator import SphCalendarCoordinator
    from .module.meinunterricht.coordinator import SphMeinUnterrichtCoordinator
    from .module.stundenplan.coordinator import SphTimetableCoordinator

    auth = SphAuthClient(
        entry.data[CONF_SCHOOL_ID],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    timetable = SphTimetableCoordinator(hass, entry, auth)
    try:
        await timetable.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning("Schulportal Hessen Stundenplan für %s aktuell nicht verfügbar: %s", entry.title, err)

    calendar = SphCalendarCoordinator(hass, entry, auth)
    try:
        await calendar.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning("Schulportal Hessen Kalender für %s aktuell nicht verfügbar: %s", entry.title, err)

    meinunterricht = SphMeinUnterrichtCoordinator(hass, entry, auth)
    try:
        await meinunterricht.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning("Schulportal Hessen Mein Unterricht für %s aktuell nicht verfügbar: %s", entry.title, err)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "auth": auth,
        "timetable": timetable,
        "calendar": calendar,
        "meinunterricht": meinunterricht,
    }
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "calendar"])
    await _migrate_sensor_entity_ids(hass, entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, ["sensor", "calendar"])
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded
