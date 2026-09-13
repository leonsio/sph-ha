"""Server-side school profile API.

Profiles are deliberately small transformation layers. They receive data that
has already been selected and normalized by the core integration and may adapt
values for one school without changing the public sensor/JSON schema.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class SchoolProfile:
    """Base class for server-side school-specific transformations."""

    id = "none"
    name = "Standard / kein Schulprofil"

    # Optional exact subject-name replacements. Keys are matched case-insensitively.
    subject_names: dict[str, str] = {}

    # Optional substitution labels keyed by the raw school-specific code.
    substitution_labels: dict[str, str] = {}

    # Description prefixes whose value represents a teacher name/abbreviation.
    description_teacher_labels: tuple[str, ...] = ()

    # Known fields that may safely be transformed without changing structure.
    teacher_fields = frozenset(
        {
            "teacher",
            "lehrer",
            "lehrkraft",
            "vertreter",
            "lehrer_nach",
            "verantwortlich",
        }
    )
    subject_fields = frozenset({"fach", "fach_lang", "displaySubject"})

    @property
    def state_entities(self) -> tuple[str, ...]:
        """Return profile-owned HA entities whose changes republish outputs."""
        return ()

    def resolve_teacher(self, value: Any, hass=None) -> Any:
        """Resolve one teacher value.

        The base implementation is intentionally a no-op. A school profile can
        override this hook and use its own source, static mapping or algorithm.
        The core integration contains no school-specific teacher entity.
        """
        return value

    def resolve_subject(self, value: Any) -> Any:
        """Apply an exact school-specific subject-name replacement."""
        if not isinstance(value, str) or not value.strip():
            return value
        raw = value.strip()
        wanted = raw.casefold()
        key = next(
            (candidate for candidate in self.subject_names if str(candidate).strip().casefold() == wanted),
            None,
        )
        return self.subject_names.get(key, raw) if key is not None else raw

    def resolve_substitution_label(self, value: Any) -> str:
        """Return the school-specific long label for a substitution code."""
        raw = str(value or "").strip()
        return self.substitution_labels.get(raw, raw)

    def transform_description(self, value: Any, hass=None) -> Any:
        """Resolve teacher values in labelled multi-line descriptions."""
        if not isinstance(value, str) or not self.description_teacher_labels:
            return value
        labels = {item.casefold() for item in self.description_teacher_labels}
        result: list[str] = []
        for line in value.splitlines():
            if ":" not in line:
                result.append(line)
                continue
            prefix, content = line.split(":", 1)
            if prefix.strip().casefold() in labels:
                content = str(self.resolve_teacher(content.strip(), hass) or "")
                result.append(f"{prefix}: {content}")
            else:
                result.append(line)
        return "\n".join(result)

    def transform_data(self, value: Any, hass=None) -> Any:
        """Recursively transform supported fields while preserving the schema."""
        if isinstance(value, list):
            return [self.transform_data(item, hass) for item in value]
        if isinstance(value, tuple):
            return tuple(self.transform_data(item, hass) for item in value)
        if not isinstance(value, dict):
            return value

        result: dict = {}
        for key, item in value.items():
            if key in self.teacher_fields:
                result[key] = self.resolve_teacher(item, hass)
            elif key in self.subject_fields:
                result[key] = self.resolve_subject(item)
            elif key == "description":
                result[key] = self.transform_description(item, hass)
            else:
                result[key] = self.transform_data(item, hass)
        return result

    def _with_profile_marker(self, payload: dict) -> dict:
        result = dict(payload)
        result["school_profile"] = self.id
        return result

    def transform_timetable_payload(
        self,
        payload: dict,
        hass=None,
        *,
        substitution_data: dict | None = None,
    ) -> dict:
        """Transform the published timetable payload.

        The core has already decided which timetable output is exposed. Profiles
        must never switch between personal and complete timetable data.
        ``eigener_grundplan`` is intentionally neither used as a profile source
        nor rewritten by the generic profile transformation.

        Date-specific substitutions are not written into the recurring weekly
        plan. They are applied by date-aware consumers such as timetable
        calendars and cards.
        """
        source = deepcopy(payload)
        for key in ("eigener_plan", "tage"):
            if key in source:
                source[key] = self.transform_data(source[key], hass)
        return self._with_profile_marker(source)

    def transform_calendar_payload(self, payload: dict, hass=None) -> dict:
        return self._with_profile_marker(self.transform_data(deepcopy(payload), hass))

    def transform_meinunterricht_payload(self, payload: dict, hass=None) -> dict:
        return self._with_profile_marker(self.transform_data(deepcopy(payload), hass))

    def transform_learning_groups_payload(self, payload: dict, hass=None) -> dict:
        return self._with_profile_marker(self.transform_data(deepcopy(payload), hass))

    def transform_substitution_payload(self, payload: dict, hass=None) -> dict:
        result = self.transform_data(deepcopy(payload), hass)

        def labels(value: Any) -> Any:
            if isinstance(value, list):
                return [labels(item) for item in value]
            if isinstance(value, dict):
                item = dict(value)
                raw = str(item.get("art") or "").strip()
                if raw:
                    item["art_lang"] = self.resolve_substitution_label(raw) or item.get("art_lang") or raw
                return {key: labels(child) for key, child in item.items()}
            return value

        return self._with_profile_marker(labels(result))

    def transform_calendar_item(self, item: dict, hass=None) -> dict:
        """Transform one native school-calendar source item."""
        return self.transform_data(deepcopy(item), hass)

    def transform_timetable_display(
        self,
        display: dict,
        hass=None,
        *,
        substitution: dict | None = None,
    ) -> dict:
        """Transform a date-aware timetable/calendar display record."""
        result = dict(display)
        result["subject"] = self.resolve_subject(result.get("subject"))
        result["teacher"] = self.resolve_teacher(result.get("teacher"), hass)
        if substitution:
            raw = str(substitution.get("art") or "").strip()
            if raw:
                result["label"] = self.resolve_substitution_label(raw) or result.get("label", "")
        return result
