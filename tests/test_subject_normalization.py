"""Regression tests for shared SPH subject/course normalization."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "sph"
    / "api"
    / "subjects.py"
)
SPEC = spec_from_file_location("sph_subjects", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
subject_from_course = MODULE.subject_from_course
subject_name = MODULE.subject_name


class SubjectNormalizationTest(unittest.TestCase):
    def test_subject_abbreviations(self):
        self.assertEqual(subject_name("D"), "Deutsch")
        self.assertEqual(subject_name("M"), "Mathematik")
        self.assertEqual(subject_name("BIO"), "Biologie")
        self.assertEqual(subject_name("L2"), "Latein 2")

    def test_course_names_drop_class_tokens(self):
        self.assertEqual(subject_from_course("D 05cG"), "Deutsch")
        self.assertEqual(subject_from_course("Deutsch 7n"), "Deutsch")
        self.assertEqual(subject_from_course("Biologie 05cg"), "Biologie")
        self.assertEqual(subject_from_course("M 05cG"), "Mathematik")
        self.assertEqual(subject_from_course("Ethik 5"), "Ethik")
        self.assertEqual(subject_from_course("7c, 7n Ethik"), "Ethik")

    def test_course_names_drop_technical_identifiers(self):
        self.assertEqual(subject_from_course("Englisch (E2vd)"), "Englisch")
        self.assertEqual(subject_from_course("Englisch 7n (E2vd)"), "Englisch")
        self.assertEqual(subject_from_course("E (E2vd)"), "Englisch")

    def test_descriptive_parentheses_are_preserved(self):
        self.assertEqual(
            subject_from_course("Religion (evangelisch) 7n"),
            "Religion (evangelisch)",
        )

    def test_unknown_subject_is_preserved(self):
        self.assertEqual(
            subject_from_course("Darstellendes Spiel 9c"),
            "Darstellendes Spiel",
        )


if __name__ == "__main__":
    unittest.main()
