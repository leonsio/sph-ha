"""Apply internal SPH substitution-plan entries to timetable lessons."""

from __future__ import annotations

from datetime import date
import re

from ...api.subjects import subject_name


def _norm(value) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().casefold()
        .replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss"))


def _subject_values(value) -> set[str]:
    raw = str(value or "").strip()
    if not raw:
        return set()
    return {_norm(raw), _norm(subject_name(raw))}


def _entry_periods(entry: dict) -> list[int]:
    values = entry.get("stunden")
    if isinstance(values, list):
        result = []
        for value in values:
            try:
                result.append(int(value))
            except (TypeError, ValueError):
                continue
        return result

    numbers = [int(value) for value in re.findall(r"\d+", str(entry.get("stunde") or ""))]
    if len(numbers) == 2 and re.search(r"[-–—]", str(entry.get("stunde") or "")):
        start, end = sorted(numbers)
        return list(range(start, end + 1))
    return numbers


def _lesson_periods(lesson: dict) -> list[int]:
    try:
        start = int(lesson.get("index"))
    except (TypeError, ValueError):
        return []
    try:
        duration = max(1, int(lesson.get("duration", 1)))
    except (TypeError, ValueError):
        duration = 1
    return list(range(start, start + duration))


def _class_matches(entry: dict, child_class: str) -> bool:
    entry_class = str(entry.get("klasse") or "").strip()
    if not entry_class or not child_class:
        return True
    wanted = _norm(child_class)
    return any(_norm(value) == wanted for value in re.split(r"[,;/|]+", entry_class))


def _subject_matches(entry: dict, lesson: dict) -> bool:
    original = (
        entry.get("fach_alt")
        or entry.get("fach_original")
        or entry.get("subject_original")
        or entry.get("fach")
        or entry.get("subject")
    )
    if not original:
        return True
    wanted = _subject_values(original)
    lesson_values = _subject_values(lesson.get("subject")) | _subject_values(lesson.get("fach"))
    return bool(wanted & lesson_values)


def find_substitution(data: dict, target: date, lesson: dict, child_class: str = "") -> dict | None:
    """Return the matching internal SPH substitution for one timetable lesson."""
    if not isinstance(data, dict):
        return None
    wanted_date = target.isoformat()
    days = data.get("tage")
    if not isinstance(days, list):
        return None
    day = next((item for item in days if str(item.get("datum") or "") == wanted_date), None)
    if not isinstance(day, dict):
        return None

    lesson_periods = set(_lesson_periods(lesson))
    candidates: list[dict] = []
    for entry in day.get("eintraege", []) or []:
        if not isinstance(entry, dict):
            continue
        if not _class_matches(entry, child_class):
            continue
        periods = set(_entry_periods(entry))
        if lesson_periods and periods and not (lesson_periods & periods):
            continue
        candidates.append(entry)

    if not candidates:
        return None

    # Prefer an exact subject match. Some SPH rows omit Fach_alt and expose only
    # a shortened/current subject. A unique class+period entry is still safe to
    # apply and prevents teacher/room changes from being silently discarded.
    exact = next((entry for entry in candidates if _subject_matches(entry, lesson)), None)
    if exact is not None:
        return exact
    return candidates[0] if len(candidates) == 1 else None


def apply_substitution(lesson: dict, entry: dict | None) -> dict:
    """Return display fields for a timetable lesson plus one substitution entry."""
    base_subject = subject_name(lesson.get("subject")) or str(
        lesson.get("fach") or lesson.get("subject") or "Unterricht"
    )
    base_teacher = str(lesson.get("teacher") or "").strip()
    base_room = str(lesson.get("room") or "").strip()
    if not entry:
        return {
            "subject": base_subject,
            "teacher": base_teacher,
            "room": base_room,
            "cancelled": False,
            "label": "",
            "original_subject": "",
            "entry": None,
        }

    label = str(entry.get("art_lang") or entry.get("art") or "Vertretung").strip() or "Vertretung"
    cancelled = bool(entry.get("entfall")) or bool(
        re.search(r"entfall|ausfall|freistunde|freisetzung", label, re.IGNORECASE)
    )
    new_code = entry.get("fach") or entry.get("subject") or lesson.get("subject")
    old_code = (
        entry.get("fach_alt")
        or entry.get("fach_original")
        or entry.get("subject_original")
        or lesson.get("subject")
    )
    changed = bool(new_code and old_code and not cancelled and _norm(new_code) != _norm(old_code))
    subject = base_subject if cancelled else (
        str(entry.get("fach_lang") or "").strip() or subject_name(new_code) or base_subject
    )
    teacher = str(
        entry.get("vertreter")
        or entry.get("lehrer_nach")
        or entry.get("lehrer")
        or entry.get("teacher")
        or base_teacher
    ).strip()
    room = str(entry.get("raum") or entry.get("room") or base_room).strip()

    return {
        "subject": subject,
        "teacher": teacher,
        "room": room,
        "cancelled": cancelled,
        "label": "Fachwechsel" if changed else label,
        "original_subject": base_subject if changed else "",
        "entry": entry,
    }
