"""Aggregation helpers for Mein Unterricht."""

from __future__ import annotations

from ...api.subjects import subject_from_course


def subject_overview(tasks) -> list[dict]:
    """Group entries by normalized subject and summarize their status."""
    grouped: dict[str, dict] = {}

    for task in tasks or []:
        raw_subject = task.get("fach") or task.get("kurs") or "Ohne Fach"
        subject = subject_from_course(str(raw_subject)) or "Ohne Fach"
        item = grouped.get(subject)
        if item is None:
            item = {
                "fach": subject,
                "kurse": [],
                "lehrer": [],
                "anzahl": 0,
                "offen": 0,
                "erledigt": 0,
                "letzter_eintrag": "",
                "offene_themen": [],
            }
            grouped[subject] = item

        done = bool(task.get("erledigt"))
        item["anzahl"] += 1
        item["erledigt" if done else "offen"] += 1

        course = str(task.get("kurs") or "").strip()
        if course and course not in item["kurse"]:
            item["kurse"].append(course)

        teacher = str(task.get("lehrer") or "").strip()
        if teacher and teacher not in item["lehrer"]:
            item["lehrer"].append(teacher)

        date = str(task.get("datum") or "")
        if date > item["letzter_eintrag"]:
            item["letzter_eintrag"] = date

        if not done:
            topic = str(task.get("thema") or "").strip()
            if topic and topic not in item["offene_themen"]:
                item["offene_themen"].append(topic)

    for item in grouped.values():
        item["status"] = "offen" if item["offen"] else "erledigt"

    return sorted(
        grouped.values(),
        key=lambda item: (-item["offen"], item["fach"].casefold()),
    )
