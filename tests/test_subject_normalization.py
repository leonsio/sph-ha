"""Regression tests for shared SPH subject/course normalization."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "sph"
    / "api"
    / "subjects.py"
)
SPEC = spec_from_file_location("sph_subjects", MODULE_PATH)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
subject_from_course = MODULE.subject_from_course
subject_name = MODULE.subject_name


def test_subject_abbreviations():
    assert subject_name("D") == "Deutsch"
    assert subject_name("M") == "Mathematik"
    assert subject_name("BIO") == "Biologie"
    assert subject_name("L2") == "Latein 2"


def test_course_names_drop_class_tokens():
    assert subject_from_course("D 05cG") == "Deutsch"
    assert subject_from_course("Deutsch 7n") == "Deutsch"
    assert subject_from_course("Biologie 05cg") == "Biologie"
    assert subject_from_course("M 05cG") == "Mathematik"
    assert subject_from_course("Ethik 5") == "Ethik"
    assert subject_from_course("7c, 7n Ethik") == "Ethik"


def test_unknown_subject_is_preserved():
    assert subject_from_course("Darstellendes Spiel 9c") == "Darstellendes Spiel"
