"""Shared helpers for the SPH substitution plan module."""

from __future__ import annotations

from datetime import date, timedelta

from homeassistant.util import dt as dt_util


def plan_days(data) -> list[dict]:
    if not isinstance(data, dict):
        return []
    days = data.get("tage")
    return days if isinstance(days, list) else []


def day_for_date(data, wanted: date) -> dict | None:
    target = wanted.isoformat()
    for day in plan_days(data):
        if day.get("datum") == target:
            return day
    return None


def today() -> date:
    return dt_util.now().date()


def tomorrow() -> date:
    return today() + timedelta(days=1)


def entries_for(data, wanted: date) -> list[dict]:
    day = day_for_date(data, wanted)
    if not day:
        return []
    entries = day.get("eintraege")
    return entries if isinstance(entries, list) else []


def covers_lesson(entry: dict, lesson: int) -> bool:
    lessons = entry.get("stunden")
    return isinstance(lessons, list) and lesson in lessons


def first_lesson_cancelled(data, wanted: date, lesson: int = 1) -> bool | None:
    day = day_for_date(data, wanted)
    if day is None:
        return None
    return any(
        entry.get("entfall") and covers_lesson(entry, lesson)
        for entry in day.get("eintraege", [])
    )
