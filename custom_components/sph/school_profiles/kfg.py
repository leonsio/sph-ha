"""Kaiserin-Friedrich-Gymnasium school profile."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from ..module.vertretung.apply import apply_substitution, find_substitution
from .base import SchoolProfile


class KFGProfile(SchoolProfile):
    """School-specific data and behaviour currently required by the KFG."""

    id = "kfg"
    name = "Kaiserin-Friedrich-Gymnasium Bad Homburg"

    # Existing KFG school-hacks settings, now shared with server-side output.
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

    @staticmethod
    def _reference_monday(payload: dict) -> date | None:
        value = str(payload.get("wochenbeginn") or "").strip()
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            return None
        return parsed - timedelta(days=parsed.weekday())

    def _apply_substitution_to_lesson(
        self,
        lesson: dict,
        target: date,
        child_class: str,
        substitution_data: dict,
        hass=None,
    ) -> dict:
        entry = find_substitution(substitution_data, target, lesson, child_class)
        if not entry:
            return lesson

        original_teacher = str(lesson.get("teacher") or "").strip()
        original_room = str(lesson.get("room") or "").strip()
        original_subject = str(lesson.get("fach") or lesson.get("subject") or "").strip()
        display = apply_substitution(lesson, entry)
        display = self.transform_timetable_display(
            display,
            hass,
            substitution=entry,
        )

        result = dict(lesson)
        if display.get("subject"):
            result["fach"] = display["subject"]
        if display.get("teacher") is not None:
            result["teacher"] = display["teacher"]
        if display.get("room") is not None:
            result["room"] = display["room"]

        label = str(display.get("label") or "").strip()
        if label:
            result["change_type"] = label
        if display.get("cancelled"):
            result["cancelled"] = True

        current_teacher = str(result.get("teacher") or "").strip()
        if original_teacher and current_teacher and original_teacher != current_teacher:
            result["teacher_original"] = self.resolve_teacher(original_teacher, hass)

        current_room = str(result.get("room") or "").strip()
        if original_room and current_room and original_room != current_room:
            result["room_original"] = original_room

        changed_subject = str(display.get("original_subject") or "").strip()
        if changed_subject:
            result["subject_original"] = self.resolve_subject(changed_subject)
        elif original_subject and str(result.get("fach") or "").strip() != original_subject:
            result["subject_original"] = self.resolve_subject(original_subject)

        return result

    def _apply_week_substitutions(
        self,
        days: Any,
        monday: date | None,
        child_class: str,
        substitution_data: dict | None,
        hass=None,
    ) -> Any:
        if not isinstance(days, list) or monday is None or not substitution_data:
            return days
        result: list = []
        for day_index, lessons in enumerate(days):
            if not isinstance(lessons, list):
                result.append(lessons)
                continue
            target = monday + timedelta(days=day_index)
            result.append(
                [
                    self._apply_substitution_to_lesson(
                        lesson,
                        target,
                        child_class,
                        substitution_data,
                        hass,
                    )
                    if isinstance(lesson, dict)
                    else lesson
                    for lesson in lessons
                ]
            )
        return result

    def transform_timetable_payload(
        self,
        payload: dict,
        hass=None,
        *,
        substitution_data: dict | None = None,
    ) -> dict:
        """Apply KFG names and current-week substitutions to exposed outputs."""
        result = super().transform_timetable_payload(
            payload,
            hass,
            substitution_data=substitution_data,
        )
        monday = self._reference_monday(result)
        child_class = str(result.get("klasse") or "").strip()

        # Only already-exposed timetable outputs are touched. In particular,
        # eigener_grundplan is not used as a profile source and is not rewritten.
        for key in ("eigener_plan", "tage"):
            result[key] = self._apply_week_substitutions(
                result.get(key),
                monday,
                child_class,
                substitution_data,
                hass,
            )
        return result
