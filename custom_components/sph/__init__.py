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
from .const import (
    CONF_CHILD_NAME,
    CONF_CHILD_SHORTCUT,
    CONF_COMBINE_CALENDARS,
    CONF_MODULE_KALENDER,
    CONF_PASSWORD,
    CONF_SCHOOL_DISTRICT,
    CONF_SCHOOL_ID,
    CONF_USERNAME,
    DEFAULT_COMBINE_CALENDARS,
    DEFAULT_MODULE_ENABLED,
    DOMAIN,
    SCHOOL_DISTRICT_NONE,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
CARD_VERSION = "0.4.19"
CARD_URLS = (
    f"/api/{DOMAIN}/static/sph-stundenplan-card.js?v={CARD_VERSION}",
    f"/api/{DOMAIN}/static/sph-stundenplan-tag-card.js?v={CARD_VERSION}",
    f"/api/{DOMAIN}/static/sph-stundenplan-grid-card.js?v={CARD_VERSION}",
    f"/api/{DOMAIN}/static/sph-lerngruppen-card.js?v={CARD_VERSION}",
    f"/api/{DOMAIN}/static/sph-meinunterricht-card.js?v={CARD_VERSION}",
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
    from .module.lerngruppen.services import async_register_services as async_register_lerngruppen_services
    from .module.meinunterricht.services import async_register_services as async_register_meinunterricht_services

    static_dir = Path(__file__).parent / "static"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"/api/{DOMAIN}/static", str(static_dir), False)]
    )
    await async_register_lerngruppen_services(hass)
    await async_register_meinunterricht_services(hass)

    if hass.is_running:
        hass.async_create_task(_register_lovelace_resources(hass))
    else:
        async def _on_started(_event):
            await _register_lovelace_resources(hass)
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started)
    return True


async def _remove_disabled_calendar_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove school-calendar entities entirely when the module is disabled."""
    if bool(entry.data.get(CONF_MODULE_KALENDER, DEFAULT_MODULE_ENABLED)):
        return

    registry = er.async_get(hass)
    for platform, unique_id in (
        ("sensor", f"{entry.entry_id}_calendar"),
        ("sensor", f"{entry.entry_id}_calendar_json"),
        ("calendar", f"{entry.entry_id}_native_calendar"),
    ):
        entity_id = registry.async_get_entity_id(platform, DOMAIN, unique_id)
        if entity_id:
            registry.async_remove(entity_id)
            _LOGGER.debug("SPH: deaktivierte Schulkalender-Entity %s entfernt", entity_id)


async def _remove_inactive_calendar_layout_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Keep only the configured combined or separate user-facing calendars."""
    combine = bool(entry.data.get(CONF_COMBINE_CALENDARS, DEFAULT_COMBINE_CALENDARS))
    registry = er.async_get(hass)

    if combine:
        unique_ids = (
            f"{entry.entry_id}_native_calendar",
            f"{entry.entry_id}_timetable_calendar",
            f"{entry.entry_id}_lerngruppen_calendar",
        )
    else:
        unique_ids = (f"{entry.entry_id}_sph_calendar",)

    for unique_id in unique_ids:
        entity_id = registry.async_get_entity_id("calendar", DOMAIN, unique_id)
        if entity_id:
            registry.async_remove(entity_id)
            _LOGGER.debug("SPH: nicht verwendete Kalender-Entity %s entfernt", entity_id)


async def _remove_unconfigured_movable_holiday_calendar(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove an old movable-holiday calendar when no district is selected."""
    district = str(entry.data.get(CONF_SCHOOL_DISTRICT, SCHOOL_DISTRICT_NONE)).strip()
    if district and district != SCHOOL_DISTRICT_NONE:
        return
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "calendar", DOMAIN, f"{entry.entry_id}_movable_holidays_calendar"
    )
    if entity_id:
        registry.async_remove(entity_id)


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
        (f"{entry.entry_id}_lerngruppen", f"lerngruppen_{suffix}"),
        (f"{entry.entry_id}_lerngruppen_json", f"lerngruppen_{suffix}_json"),
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

    for unique_id, object_id in (
        (f"{entry.entry_id}_native_calendar", f"schulkalender_{suffix}"),
        (f"{entry.entry_id}_timetable_calendar", f"stundenplan_{suffix}"),
        (f"{entry.entry_id}_lerngruppen_calendar", f"lerngruppen_{suffix}"),
        (f"{entry.entry_id}_sph_calendar", f"sph_{suffix}"),
        (f"{entry.entry_id}_movable_holidays_calendar", f"bewegliche_ferientage_{suffix}"),
    ):
        entity_id = registry.async_get_entity_id("calendar", DOMAIN, unique_id)
        desired = f"calendar.{object_id}"
        if entity_id and entity_id != desired and not registry.async_get(desired):
            registry.async_update_entity(entity_id, new_entity_id=desired)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from .module.kalender.coordinator import SphCalendarCoordinator
    from .module.lerngruppen.coordinator import SphLearningGroupsCoordinator
    from .module.meinunterricht.coordinator import SphMeinUnterrichtCoordinator
    from .module.stundenplan.coordinator import SphTimetableCoordinator
    from .module.stundenplan.movable_holidays import SphMovableHolidaysCoordinator

    auth = SphAuthClient(
        entry.data[CONF_SCHOOL_ID],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )

    movable_holidays = SphMovableHolidaysCoordinator(hass, entry)
    await movable_holidays.async_load_cache()
    if movable_holidays.enabled:
        try:
            await movable_holidays.async_config_entry_first_refresh()
        except Exception as err:
            _LOGGER.warning("Bewegliche Ferientage für %s aktuell nicht verfügbar: %s", entry.title, err)

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
    await meinunterricht.async_load_manual_items()
    try:
        await meinunterricht.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning("Schulportal Hessen Mein Unterricht für %s aktuell nicht verfügbar: %s", entry.title, err)

    lerngruppen = SphLearningGroupsCoordinator(hass, entry, auth, timetable)
    await lerngruppen.async_load_manual_items()
    try:
        await lerngruppen.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning("Schulportal Hessen Lerngruppen für %s aktuell nicht verfügbar: %s", entry.title, err)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "auth": auth,
        "timetable": timetable,
        "calendar": calendar,
        "meinunterricht": meinunterricht,
        "lerngruppen": lerngruppen,
        "movable_holidays": movable_holidays,
    }

    await _remove_disabled_calendar_entities(hass, entry)
    await _remove_inactive_calendar_layout_entities(hass, entry)
    await _remove_unconfigured_movable_holiday_calendar(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "calendar"])
    await _migrate_sensor_entity_ids(hass, entry)

    # Free-day calendars may still be restoring/loading when SPH performs its
    # first refresh. Track them after all SPH entities have been set up and
    # refresh the overlay independently from the SPH polling cycle.
    timetable.async_start_free_day_tracking()
    meinunterricht.async_start_manual_cleanup()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    timetable = data.get("timetable")
    if timetable is not None:
        timetable.async_stop_free_day_tracking()

    meinunterricht = data.get("meinunterricht")
    if meinunterricht is not None:
        meinunterricht.async_stop_manual_cleanup()

    unloaded = await hass.config_entries.async_unload_platforms(entry, ["sensor", "calendar"])
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded
