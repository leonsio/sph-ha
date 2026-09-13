"""Standalone tests for applying SPH substitutions to timetable lessons."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import unittest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "sph"
    / "module"
    / "vertretung"
    / "apply.py"
)


def _load_module():
    source = MODULE_PATH.read_text(encoding="utf-8")
    source = source.replace(
        "from ...api.subjects import subject_name",
        "def subject_name(value):\n"
        "    return {'M': 'Mathematik', 'D': 'Deutsch', 'E': 'Englisch'}.get(str(value or ''), value)",
    )
    namespace = {"__name__": "sph_substitution_apply"}
    exec(compile(source, str(MODULE_PATH), "exec"), namespace)
    return namespace


MODULE = _load_module()
find_substitution = MODULE["find_substitution"]
apply_substitution = MODULE["apply_substitution"]


class SubstitutionApplyTest(unittest.TestCase):
    def setUp(self):
        self.lesson = {
            "subject": "M",
            "fach": "Mathematik",
            "teacher": "HER",
            "room": "101",
            "index": 1,
            "duration": 2,
            "start": "07:55",
            "end": "09:25",
        }

    def test_matches_date_class_period_and_original_subject(self):
        data = {
            "tage": [{
                "datum": "2026-09-14",
                "eintraege": [{
                    "klasse": "7n",
                    "stunden": [1, 2],
                    "fach": "E",
                    "fach_alt": "M",
                    "art": "Vertr",
                    "art_lang": "Vertretung",
                    "vertreter": "DRG",
                    "raum": "202",
                    "entfall": False,
                }],
            }]
        }
        entry = find_substitution(data, date(2026, 9, 14), self.lesson, "7n")
        self.assertIsNotNone(entry)
        result = apply_substitution(self.lesson, entry)
        self.assertEqual(result["subject"], "Englisch")
        self.assertEqual(result["teacher"], "DRG")
        self.assertEqual(result["room"], "202")
        self.assertEqual(result["label"], "Fachwechsel")
        self.assertEqual(result["original_subject"], "Mathematik")
        self.assertFalse(result["cancelled"])

    def test_cancellation_keeps_original_subject(self):
        entry = {
            "klasse": "7n",
            "stunden": [1],
            "fach": "M",
            "art": "Entf.",
            "art_lang": "Entfall",
            "entfall": True,
        }
        result = apply_substitution(self.lesson, entry)
        self.assertEqual(result["subject"], "Mathematik")
        self.assertEqual(result["label"], "Entfall")
        self.assertTrue(result["cancelled"])

    def test_wrong_class_subject_or_date_does_not_match(self):
        base_entry = {
            "klasse": "8a",
            "stunden": [1],
            "fach": "M",
            "art": "Entf.",
            "entfall": True,
        }
        data = {"tage": [{"datum": "2026-09-14", "eintraege": [base_entry]}]}
        self.assertIsNone(find_substitution(data, date(2026, 9, 14), self.lesson, "7n"))

        data["tage"][0]["eintraege"][0] = {**base_entry, "klasse": "7n", "fach": "D"}
        self.assertIsNone(find_substitution(data, date(2026, 9, 14), self.lesson, "7n"))
        self.assertIsNone(find_substitution(data, date(2026, 9, 15), self.lesson, "7n"))


if __name__ == "__main__":
    unittest.main()
