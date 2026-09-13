"""Shared subject and course-name handling for SPH modules."""

from __future__ import annotations

import re

SUBJECT_NAMES = {
    "M": "Mathematik",
    "D": "Deutsch",
    "E": "Englisch",
    "F": "Französisch",
    "L": "Latein",
    "G": "Geschichte",
    "GE": "Geschichte",
    "EK": "Erdkunde",
    "POW": "Politik und Wirtschaft",
    "PW": "Politik und Wirtschaft",
    "PH": "Physik",
    "CH": "Chemie",
    "BIO": "Biologie",
    "SP": "Sport",
    "MU": "Musik",
    "ETH": "Ethik",
    "RKA": "Religion katholisch",
    "REV": "Religion evangelisch",
    "RELI": "Religion",
    "INF": "Informatik",
    "KU": "Kunst",
    "LRS": "Lese-Rechtschreib-Schwäche",
}

# Class designations as they appear inside course names: 05cG, 7n, 9c, 5, 10b.
CLASS_TOKEN = re.compile(r"^\d{1,2}[A-Za-zÄÖÜäöü]{0,3}$")
# Technical course identifiers are commonly appended as a separate token, e.g.
# (E2vd). Requiring a digit avoids dropping ordinary descriptive parentheses.
COURSE_ID_TOKEN = re.compile(r"^\((?=[^()]*\d)[A-Za-zÄÖÜäöü0-9._/-]+\)$")


def subject_name(subject):
    """Return the written-out subject for an abbreviation."""
    if not subject:
        return subject
    value = str(subject).strip()
    match = re.match(r"^([A-Za-zÄÖÜäöü]+)(\d+)(.*)$", value)
    if match:
        code, number, suffix = match.groups()
        base = SUBJECT_NAMES.get(code.upper())
        if base:
            return f"{base} {number}{suffix}"
    return SUBJECT_NAMES.get(value.upper(), value)


def subject_from_course(course: str) -> str:
    """Reduce a course name to a normalized subject name.

    Course names mix subject, class and technical identifiers in different
    orders and spellings, e.g. ``Biologie 05cg``, ``D 05cG``, ``Ethik 5``,
    ``7c, 7n Ethik`` or ``Englisch (E2vd)``. Class tokens and technical course
    identifiers are removed and subject abbreviations are expanded so that
    courses such as ``D 05cG`` and ``Deutsch 7n`` are grouped under the same
    subject.
    """
    value = str(course or "").strip()
    if not value:
        return ""

    tokens = [token.strip(",") for token in value.split()]
    kept = [
        token
        for token in tokens
        if token
        and not CLASS_TOKEN.match(token)
        and not COURSE_ID_TOKEN.match(token)
    ]
    if not kept:
        return value

    return subject_name(" ".join(kept))
