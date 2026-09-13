from __future__ import annotations

from types import SimpleNamespace

from custom_components.sph.school_profiles.base import SchoolProfile
from custom_components.sph.school_profiles.kfg import KFGProfile


class _State:
    def __init__(self, attributes):
        self.attributes = attributes


class _States(dict):
    def get(self, entity_id, default=None):
        return super().get(entity_id, default)


class _Hass:
    def __init__(self, states=None):
        self.states = _States(states or {})


def test_base_profile_has_no_school_specific_state_dependency():
    profile = SchoolProfile()
    assert profile.state_entities == ()
    assert profile.resolve_teacher("FRA", _Hass()) == "FRA"


def test_kfg_teacher_directory_is_profile_local():
    profile = KFGProfile()
    hass = _Hass(
        {
            "sensor.kfg_kollegium": _State(
                {"lehrer": {"FRA": "Frau Beispiel", "bär": "Herr Beispiel"}}
            )
        }
    )

    assert profile.state_entities == ("sensor.kfg_kollegium",)
    assert profile.resolve_teacher("fra", hass) == "Frau Beispiel"
    assert profile.resolve_teacher("BÄR", hass) == "Herr Beispiel"
    assert profile.resolve_teacher("UNBEKANNT", hass) == "UNBEKANNT"


def test_timetable_profile_preserves_schema_and_does_not_touch_grundplan():
    profile = KFGProfile()
    hass = _Hass(
        {
            "sensor.kfg_kollegium": _State(
                {"lehrer": {"FRA": "Frau Beispiel", "BÄR": "Herr Beispiel"}}
            )
        }
    )
    grundplan = [[{"subject": "R", "fach": "Religion", "teacher": "BÄR"}]]
    payload = {
        "kind": "Maxim",
        "kind_kürzel": "Mk",
        "eigener_grundplan": grundplan,
        "eigener_plan": [[{"subject": "D", "fach": "Deutsch", "teacher": "FRA"}]],
        "tage": [[{"subject": "D", "fach": "Deutsch", "teacher": "FRA"}]],
    }

    result = profile.transform_timetable_payload(payload, hass)

    assert result["school_profile"] == "kfg"
    assert result["eigener_plan"][0][0]["teacher"] == "Frau Beispiel"
    assert result["tage"][0][0]["teacher"] == "Frau Beispiel"
    assert result["eigener_grundplan"] == grundplan
    assert result["eigener_grundplan"][0][0]["teacher"] == "BÄR"
    assert payload["eigener_plan"][0][0]["teacher"] == "FRA"


def test_kfg_substitution_labels_are_added_without_losing_raw_code():
    profile = KFGProfile()
    payload = {
        "tage": [
            {
                "datum": "2026-09-18",
                "eintraege": [
                    {"art": "Vertr", "fach": "D", "vertreter": "FRA"},
                    {"art": "Entf", "fach": "M", "lehrer": "BÄR"},
                ],
            }
        ]
    }

    result = profile.transform_substitution_payload(payload, _Hass())
    entries = result["tage"][0]["eintraege"]

    assert result["school_profile"] == "kfg"
    assert entries[0]["art"] == "Vertr"
    assert entries[0]["art_lang"] == "Vertretung"
    assert entries[1]["art"] == "Entf"
    assert entries[1]["art_lang"] == "Entfall"


def test_profile_can_customize_subject_names_without_changing_structure():
    class ExampleProfile(SchoolProfile):
        id = "example"
        subject_names = {"Religion ev.": "Evangelische Religion"}

    profile = ExampleProfile()
    payload = {
        "aufgaben": [
            {
                "fach": "Religion ev.",
                "kurs": "Religion ev. 7n",
                "lehrer": "ABC",
            }
        ]
    }

    result = profile.transform_meinunterricht_payload(payload, _Hass())

    assert result["school_profile"] == "example"
    assert result["aufgaben"][0]["fach"] == "Evangelische Religion"
    assert result["aufgaben"][0]["kurs"] == "Religion ev. 7n"
    assert result["aufgaben"][0]["lehrer"] == "ABC"


def test_date_aware_timetable_display_uses_profile_mapping():
    profile = KFGProfile()
    hass = _Hass(
        {
            "sensor.kfg_kollegium": _State(
                {"lehrer": {"FRA": "Frau Beispiel"}}
            )
        }
    )
    display = {
        "subject": "Deutsch",
        "teacher": "FRA",
        "room": "123",
        "label": "Vertr",
        "cancelled": False,
        "original_subject": "",
    }

    result = profile.transform_timetable_display(
        display,
        hass,
        substitution={"art": "Vertr"},
    )

    assert result["teacher"] == "Frau Beispiel"
    assert result["label"] == "Vertretung"
