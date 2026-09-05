from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .const import (
    CONF_CALENDAR_EVENT_TYPES,
    CONF_CHILD_NAME,
    CONF_CHILD_SHORTCUT,
    CONF_SCHOOL_ID,
    CONF_UPDATE_INTERVAL,
    DEFAULT_CALENDAR_EVENT_TYPES,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)


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
    return ", ".join(items or DEFAULT_CALENDAR_EVENT_TYPES)


def _parse_calendar_types(value: Any) -> list[str]:
    """Parse a user-editable list and remove duplicates case-insensitively."""
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
    return result or list(DEFAULT_CALENDAR_EVENT_TYPES)


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
            return self.async_create_entry(
                title=f"Schulportal Hessen – {user_input[CONF_CHILD_NAME]} ({user_input[CONF_CHILD_SHORTCUT]})",
                data=user_input,
            )
        return self.async_show_form(step_id="user", data_schema=self._schema())

    def _schema(self, values: dict[str, Any] | None = None):
        values = values or {}
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
                    CONF_CALENDAR_EVENT_TYPES: _parse_calendar_types(
                        user_input.get(CONF_CALENDAR_EVENT_TYPES)
                    ),
                }
            )

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=data,
                title=f"Schulportal Hessen – {child_name} ({child_shortcut})",
            )

            # Recreate the integration so credentials, school ID, update interval
            # and calendar filters are applied immediately without a HA restart.
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="init", data_schema=self._schema(current))

    @staticmethod
    def _schema(values: dict[str, Any]):
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
                    CONF_CALENDAR_EVENT_TYPES,
                    default=_calendar_types_to_text(
                        values.get(CONF_CALENDAR_EVENT_TYPES, DEFAULT_CALENDAR_EVENT_TYPES)
                    ),
                ): str,
            }
        )
