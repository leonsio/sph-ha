"""Regression tests for the dynamic server-side School Profile API."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPH_DIR = ROOT / "custom_components" / "sph"
PROFILE_DIR = SPH_DIR / "school_profiles"

# The lightweight Python CI intentionally does not install Home Assistant.
# Create only the parent package shells so school_profiles can be imported
# without executing custom_components.sph.__init__.
for name, path in (
    ("custom_components", ROOT / "custom_components"),
    ("custom_components.sph", SPH_DIR),
):
    package = ModuleType(name)
    package.__path__ = [str(path)]
    sys.modules.setdefault(name, package)


def _load_package(name: str, path: Path, search_path: Path):
    spec = spec_from_file_location(
        name,
        path,
        submodule_search_locations=[str(search_path)],
    )
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


REGISTRY = _load_package(
    "custom_components.sph.school_profiles",
    PROFILE_DIR / "__init__.py",
    PROFILE_DIR,
)
SchoolProfile = REGISTRY.SchoolProfile
KFGProfile = type(REGISTRY.available_school_profiles()["kfg"])


class _State:
    def __init__(self, attributes):
        self.attributes = attributes


class _States(dict):
    def get(self, entity_id, default=None):
        return super().get(entity_id, default)


class _Hass:
    def __init__(self, states=None):
        self.states = _States(states or {})


class SchoolProfileDiscoveryTest(unittest.TestCase):
    def test_profile_package_is_discovered_without_central_school_import(self):
        profiles = REGISTRY.available_school_profiles()
        self.assertIn("none", profiles)
        self.assertIn("kfg", profiles)
        self.assertNotIn("KFGProfile", (PROFILE_DIR / "__init__.py").read_text())
        self.assertTrue((PROFILE_DIR / "kfg" / "profile.py").is_file())
        self.assertTrue((PROFILE_DIR / "kfg" / "frontend" / "lovelace.js").is_file())

    def test_profile_supplies_configuration_and_frontend_metadata(self):
        profile = REGISTRY.available_school_profiles()["kfg"]
        metadata = profile.metadata()
        self.assertEqual(metadata["id"], "kfg")
        self.assertEqual(metadata["name"], "Kaiserin-Friedrich-Gymnasium Bad Homburg")
        self.assertTrue(metadata["description"])
        self.assertEqual(metadata["frontend_module"], "lovelace.js")
        self.assertEqual(
            profile.config_option(),
            {"value": "kfg", "label": "Kaiserin-Friedrich-Gymnasium Bad Homburg"},
        )
        self.assertIn(profile.config_option(), REGISTRY.school_profile_options())

    def test_frontend_paths_are_derived_from_discovered_profile_packages(self):
        paths = dict(REGISTRY.school_profile_frontend_paths())
        self.assertEqual(paths["kfg"], PROFILE_DIR / "kfg" / "frontend")

    def test_get_school_profile_uses_discovered_registry(self):
        entry = SimpleNamespace(data={"school_profile": "kfg"})
        self.assertIsInstance(REGISTRY.get_school_profile(entry), KFGProfile)
        unknown = SimpleNamespace(data={"school_profile": "does-not-exist"})
        self.assertEqual(REGISTRY.get_school_profile(unknown).id, "none")


class SchoolProfileTransformTest(unittest.TestCase):
    def test_base_profile_has_no_school_specific_state_dependency(self):
        profile = SchoolProfile()
        self.assertEqual(profile.state_entities, ())
        self.assertEqual(profile.resolve_teacher("FRA", _Hass()), "FRA")

    def test_kfg_teacher_directory_is_profile_local(self):
        profile = KFGProfile()
        hass = _Hass(
            {
                "sensor.kfg_kollegium": _State(
                    {"lehrer": {"FRA": "Frau Beispiel", "bär": "Herr Beispiel"}}
                )
            }
        )

        self.assertEqual(profile.state_entities, ("sensor.kfg_kollegium",))
        self.assertEqual(profile.resolve_teacher("fra", hass), "Frau Beispiel")
        self.assertEqual(profile.resolve_teacher("BÄR", hass), "Herr Beispiel")
        self.assertEqual(profile.resolve_teacher("UNBEKANNT", hass), "UNBEKANNT")

    def test_kfg_epoch_subject_names_are_cleaned_and_expanded(self):
        profile = KFGProfile()

        self.assertEqual(profile.resolve_subject("Mu (epo1)"), "Musik")
        self.assertEqual(profile.resolve_subject("Ku (epo2)"), "Kunst")
        self.assertEqual(profile.resolve_subject("mu (EPO2)"), "Musik")
        self.assertEqual(
            profile.resolve_subject("Darstellendes Spiel (epo1)"),
            "Darstellendes Spiel",
        )
        self.assertEqual(profile.resolve_subject("Mu"), "Mu")

        display = {
            "subject": "Ku (epo2)",
            "teacher": "",
            "room": "123",
            "label": "",
            "cancelled": False,
            "original_subject": "",
        }
        result = profile.transform_timetable_display(display, _Hass())
        self.assertEqual(result["subject"], "Kunst")

    def test_timetable_profile_transforms_personal_and_complete_output_but_not_grundplan(self):
        profile = KFGProfile()
        hass = _Hass(
            {
                "sensor.kfg_kollegium": _State(
                    {
                        "lehrer": {
                            "FRA": "Frau Beispiel",
                            "BÄR": "Herr Beispiel",
                            "SPI": "Herr Spiegel",
                        }
                    }
                )
            }
        )
        grundplan = [[{"subject": "R", "fach": "Religion", "teacher": "BÄR"}]]
        payload = {
            "kind": "Maxim",
            "kind_kürzel": "Mk",
            "eigener_grundplan": grundplan,
            "eigener_plan": [
                [{"subject": "D", "fach": "Deutsch", "teacher": "FRA"}]
            ],
            "tage": [
                [{"subject": "M", "fach": "Mathematik", "teacher": "SPI"}]
            ],
        }

        result = profile.transform_timetable_payload(payload, hass)

        self.assertEqual(result["school_profile"], "kfg")
        self.assertEqual(result["eigener_plan"][0][0]["teacher"], "Frau Beispiel")
        self.assertEqual(result["eigener_plan"][0][0]["fach"], "Deutsch")
        self.assertEqual(result["tage"][0][0]["teacher"], "Herr Spiegel")
        self.assertEqual(result["tage"][0][0]["fach"], "Mathematik")
        self.assertEqual(result["eigener_grundplan"], grundplan)
        self.assertEqual(result["eigener_grundplan"][0][0]["teacher"], "BÄR")
        self.assertEqual(payload["eigener_plan"][0][0]["teacher"], "FRA")
        self.assertEqual(payload["tage"][0][0]["teacher"], "SPI")

    def test_kfg_substitution_labels_are_added_without_losing_raw_code(self):
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

        self.assertEqual(result["school_profile"], "kfg")
        self.assertEqual(entries[0]["art"], "Vertr")
        self.assertEqual(entries[0]["art_lang"], "Vertretung")
        self.assertEqual(entries[1]["art"], "Entf")
        self.assertEqual(entries[1]["art_lang"], "Entfall")

    def test_profile_can_customize_subject_names_without_changing_structure(self):
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

        self.assertEqual(result["school_profile"], "example")
        self.assertEqual(result["aufgaben"][0]["fach"], "Evangelische Religion")
        self.assertEqual(result["aufgaben"][0]["kurs"], "Religion ev. 7n")
        self.assertEqual(result["aufgaben"][0]["lehrer"], "ABC")

    def test_date_aware_timetable_display_uses_profile_mapping(self):
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

        self.assertEqual(result["teacher"], "Frau Beispiel")
        self.assertEqual(result["label"], "Vertretung")


if __name__ == "__main__":
    unittest.main()
