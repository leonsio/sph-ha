from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.selector import (
    BooleanSelector,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
)

from .const import (
    CONF_ACTIVE_MODULES,
    CONF_CALENDAR_EVENT_TYPES,
    CONF_CHILD_NAME,
    CONF_CHILD_SHORTCUT,
    CONF_COMBINE_CALENDARS,
    CONF_MODULE_KALENDER,
    CONF_MODULE_LERNGRUPPEN,
    CONF_MODULE_MEINUNTERRICHT,
    CONF_MODULE_STUNDENPLAN,
    CONF_SCHOOL_DISTRICT,
    CONF_SCHOOL_ID,
    CONF_TIMETABLE_OUTPUT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_CALENDAR_EVENT_TYPES,
    DEFAULT_COMBINE_CALENDARS,
    DEFAULT_MODULE_ENABLED,
    DEFAULT_TIMETABLE_OUTPUT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    SCHOOL_DISTRICT_NONE,
    TIMETABLE_OUTPUT_ALL,
    TIMETABLE_OUTPUT_OWN,
)
from .module.stundenplan.movable_holidays import SCHOOL_DISTRICTS

MODULE_STUNDENPLAN = "stundenplan"
MODULE_KALENDER = "kalender"
MODULE_MEINUNTERRICHT = "meinunterricht"
MODULE_LERNGRUPPEN = "lerngruppen"
ALL_MODULES = [
    MODULE_STUNDENPLAN,
    MODULE_KALENDER,
    MODULE_MEINUNTERRICHT,
    MODULE_LERNGRUPPEN,
]

MODULE_CONFIG_KEYS = {
    MODULE_STUNDENPLAN: CONF_MODULE_STUNDENPLAN,
    MODULE_KALENDER: CONF_MODULE_KALENDER,
    MODULE_MEINUNTERRICHT: CONF_MODULE_MEINUNTERRICHT,
    MODULE_LERNGRUPPEN: CONF_MODULE_LERNGRUPPEN,
}


def _calendar_types_to_text(value: Any) -> str:
    """Render stored calendar types as an editable comma-separated string."""
    if isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value if str(item).strip()]
    else:
        items = [
            item.strip()
            for item in re.split(r"[,;\n]+", str(value or ""))
            if item.strip()
        ]
    return ", ".join(items)


def _parse_calendar_types(value: Any) -> list[str]:
    """Parse a user-editable list and remove duplicates case-insensitively.

    An empty list intentionally means that no type filter is applied and all
    SPH calendar entries are kept.
    """
    if isinstance(value, (list, tuple, set)):
        raw_items = [str(item) for item in value]
    else:
        raw_items = re.split(r"[,;\n]+", str(value or ""))

    result: list[str] = []
    seen: set[str] = set()
    for raw in raw_items:
        item = raw.strip()
        key = item.casefold()
        if not item or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _active_modules(values: dict[str, Any]) -> list[str]:
    """Return selected modules from the existing per-module boolean settings."""
    return [
        module
        for module, config_key in MODULE_CONFIG_KEYS.items()
        if bool(values.get(config_key, DEFAULT_MODULE_ENABLED))
    ]


def _store_active_modules(data: dict[str, Any], selected: Any) -> None:
    """Store the module multi-select as the existing boolean config keys."""
    selected_modules = {
        str(value).strip()
        for value in (selected if isinstance(selected, (list, tuple, set)) else [])
    }
    for module, config_key in MODULE_CONFIG_KEYS.items():
        data[config_key] = module in selected_modules


def _module_selector(default_modules: list[str]):
    return SelectSelector(
        SelectSelectorConfig(
            options=ALL_MODULES,
            multiple=True,
            translation_key="active_modules",
        )
    )


def _timetable_output_selector():
    return SelectSelector(
        SelectSelectorConfig(
            options=[TIMETABLE_OUTPUT_OWN, TIMETABLE_OUTPUT_ALL],
            multiple=False,
            translation_key="timetable_output",
        )
    )


def _school_district_selector():
    """Return a selector whose stored values are the real district names.

    District names contain spaces and umlauts and therefore cannot be used as
    Home Assistant translation option keys. Supplying explicit value/label
    pairs keeps the persisted values stable without requiring invalid
    translation keys.
    """
    options = [{"value": SCHOOL_DISTRICT_NONE, "label": "—"}]
    options.extend({"value": district, "label": district} for district in SCHOOL_DISTRICTS)
    return SelectSelector(
        SelectSelectorConfig(
            options=options,
            multiple=False,
        )
    )


class SphConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            if not user_input[CONF_SCHOOL_ID].isdigit():
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._schema(user_input),
                    errors={"base": "invalid_school_id"},
                )
            user_input[CONF_CHILD_NAME] = user_input[CONF_CHILD_NAME].strip()
            user_input[CONF_CHILD_SHORTCUT] = user_input[CONF_CHILD_SHORTCUT].strip()
            if not user_input[CONF_CHILD_NAME] or not user_input[CONF_CHILD_SHORTCUT]:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._schema(user_input),
                    errors={"base": "invalid_child"},
                )

            selected_modules = user_input.pop(CONF_ACTIVE_MODULES, ALL_MODULES)
            _store_active_modules(user_input, selected_modules)
            return self.async_create_entry(
                title=f"Schulportal Hessen – {user_input[CONF_CHILD_NAME]} ({user_input[CONF_CHILD_SHORTCUT]})",
                data=user_input,
            )
        return self.async_show_form(step_id="user", data_schema=self._schema())

    def _schema(self, values: dict[str, Any] | None = None):
        values = values or {}
        active_modules = values.get(CONF_ACTIVE_MODULES)
        if not isinstance(active_modules, list):
            active_modules = _active_modules(values)
        return vol.Schema(
            {
                vol.Required(CONF_CHILD_NAME, default=values.get(CONF_CHILD_NAME, "")): str,
                vol.Required(CONF_CHILD_SHORTCUT, default=values.get(CONF_CHILD_SHORTCUT, "")): str,
                vol.Required(CONF_SCHOOL_ID, default=values.get(CONF_SCHOOL_ID, "")): str,
                vol.Required(CONF_USERNAME, default=values.get(CONF_USERNAME, "")): str,
                vol.Required(CONF_PASSWORD, default=values.get(CONF_PASSWORD, "")): str,
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=values.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=1440)),
                vol.Required(
                    CONF_TIMETABLE_OUTPUT,
                    default=values.get(CONF_TIMETABLE_OUTPUT, DEFAULT_TIMETABLE_OUTPUT),
                ): _timetable_output_selector(),
                vol.Required(
                    CONF_COMBINE_CALENDARS,
                    default=values.get(CONF_COMBINE_CALENDARS, DEFAULT_COMBINE_CALENDARS),
                ): BooleanSelector(),
                vol.Required(
                    CONF_SCHOOL_DISTRICT,
                    default=values.get(CONF_SCHOOL_DISTRICT, SCHOOL_DISTRICT_NONE),
                ): _school_district_selector(),
                vol.Required(CONF_ACTIVE_MODULES, default=active_modules): _module_selector(active_modules),
            }
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SphOptionsFlow()


class SphOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        current = self.config_entry.data

        if user_input is not None:
            child_name = user_input[CONF_CHILD_NAME].strip()
            child_shortcut = user_input[CONF_CHILD_SHORTCUT].strip()
            school_id = user_input[CONF_SCHOOL_ID].strip()

            if not child_name or not child_shortcut:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._schema(user_input),
                    errors={"base": "invalid_child"},
                )
            if not school_id.isdigit():
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._schema(user_input),
                    errors={"base": "invalid_school_id"},
                )

            data = dict(current)
            data.update(
                {
                    CONF_CHILD_NAME: child_name,
                    CONF_CHILD_SHORTCUT: child_shortcut,
                    CONF_SCHOOL_ID: school_id,
                    CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_UPDATE_INTERVAL: int(user_input[CONF_UPDATE_INTERVAL]),
                    CONF_TIMETABLE_OUTPUT: str(
                        user_input.get(CONF_TIMETABLE_OUTPUT, DEFAULT_TIMETABLE_OUTPUT)
                    ),
                    CONF_COMBINE_CALENDARS: bool(
                        user_input.get(CONF_COMBINE_CALENDARS, DEFAULT_COMBINE_CALENDARS)
                    ),
                    CONF_SCHOOL_DISTRICT: str(
                        user_input.get(CONF_SCHOOL_DISTRICT, SCHOOL_DISTRICT_NONE)
                    ),
                    CONF_CALENDAR_EVENT_TYPES: _parse_calendar_types(
                        user_input.get(CONF_CALENDAR_EVENT_TYPES)
                    ),
                }
            )
            _store_active_modules(data, user_input.get(CONF_ACTIVE_MODULES, []))

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=data,
                title=f"Schulportal Hessen – {child_name} ({child_shortcut})",
            )

            # Recreate the integration so credentials, module switches and
            # filters are applied immediately without a HA restart.
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="init", data_schema=self._schema(current))

    @staticmethod
    def _schema(values: dict[str, Any]):
        active_modules = values.get(CONF_ACTIVE_MODULES)
        if not isinstance(active_modules, list):
            active_modules = _active_modules(values)

        calendar_types = _calendar_types_to_text(
            values.get(CONF_CALENDAR_EVENT_TYPES, DEFAULT_CALENDAR_EVENT_TYPES)
        )

        return vol.Schema(
            {
                vol.Required(
                    CONF_CHILD_NAME,
                    default=values.get(CONF_CHILD_NAME, ""),
                ): str,
                vol.Required(
                    CONF_CHILD_SHORTCUT,
                    default=values.get(CONF_CHILD_SHORTCUT, ""),
                ): str,
                vol.Required(
                    CONF_SCHOOL_ID,
                    default=values.get(CONF_SCHOOL_ID, ""),
                ): str,
                vol.Required(
                    CONF_USERNAME,
                    default=values.get(CONF_USERNAME, ""),
                ): str,
                vol.Required(
                    CONF_PASSWORD,
                    default=values.get(CONF_PASSWORD, ""),
                ): str,
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=values.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=1440)),
                vol.Required(
                    CONF_TIMETABLE_OUTPUT,
                    default=values.get(CONF_TIMETABLE_OUTPUT, DEFAULT_TIMETABLE_OUTPUT),
                ): _timetable_output_selector(),
                vol.Required(
                    CONF_COMBINE_CALENDARS,
                    default=values.get(CONF_COMBINE_CALENDARS, DEFAULT_COMBINE_CALENDARS),
                ): BooleanSelector(),
                vol.Required(
                    CONF_SCHOOL_DISTRICT,
                    default=values.get(CONF_SCHOOL_DISTRICT, SCHOOL_DISTRICT_NONE),
                ): _school_district_selector(),
                vol.Optional(
                    CONF_CALENDAR_EVENT_TYPES,
                    description={"suggested_value": calendar_types},
                ): TextSelector(),
                vol.Required(
                    CONF_ACTIVE_MODULES,
                    default=active_modules,
                ): _module_selector(active_modules),
            }
        )
