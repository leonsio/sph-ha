"""Kaiserin-Friedrich-Gymnasium school profile."""

from __future__ import annotations

from typing import Any

from ..base import SchoolProfile


class KFGProfile(SchoolProfile):
    """School-specific data and behaviour required by the KFG."""

    id = "kfg"
    name = "Kaiserin-Friedrich-Gymnasium Bad Homburg"
    description = "Schulprofil für das Kaiserin-Friedrich-Gymnasium Bad Homburg."
    frontend_module = "lovelace.js"

    week_badges = ("A", "B")
    unbadged_fallback = True
    hide_week_badges = True
    grid_week_heading = True
    advance_week_after_friday = True

    teacher_entity = "sensor.kfg_kollegium"
    teacher_attribute = "lehrer"
    description_teacher_labels = ("lehrer", "lehrkraft", "verantwortlich")

    substitution_labels = {
        "Betr": "Betreuung",
        "Vertr": "Vertretung",
        "Entf": "Entfall",
        "Taus": "Tausch",
        "Freis": "Freistunde",
        "Raum": "Raumänderung",
        "Statt-Vertretung": "Statt-Vertretung",
        "Paus": "Pausenaufsicht",
        "SES": "Sonderunterricht",
        "Vtr. ohne Lehrer": "Vertretung ohne Lehrer",
    }

    substitution_news = True

    @property
    def state_entities(self) -> tuple[str, ...]:
        """Republish KFG profile data when its teacher directory changes."""
        return (self.teacher_entity,)

    def _teacher_map(self, hass) -> dict:
        if hass is None:
            return {}
        state = hass.states.get(self.teacher_entity)
        value = state.attributes.get(self.teacher_attribute, {}) if state else {}
        return value if isinstance(value, dict) else {}

    def resolve_teacher(self, value: Any, hass=None) -> Any:
        """Resolve KFG teacher abbreviations via sensor.kfg_kollegium."""
        if not isinstance(value, str) or not value.strip():
            return value
        raw = value.strip()
        wanted = raw.casefold()
        mapping = self._teacher_map(hass)
        key = next(
            (candidate for candidate in mapping if str(candidate).strip().casefold() == wanted),
            None,
        )
        resolved = mapping.get(key) if key is not None else raw
        return resolved if isinstance(resolved, str) and resolved.strip() else raw


PROFILE = KFGProfile()
