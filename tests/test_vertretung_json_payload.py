"""Standalone regression test for the Vertretungsplan JSON payload."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from types import SimpleNamespace

SENSOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "sph"
    / "module"
    / "vertretung"
    / "sensor.py"
)


def _load_sensor_module():
    source = SENSOR_PATH.read_text(encoding="utf-8")
    source = source.replace(
        "from homeassistant.components.sensor import SensorEntity",
        "class SensorEntity: pass",
    )
    source = source.replace(
        "from homeassistant.helpers.update_coordinator import CoordinatorEntity",
        "class CoordinatorEntity:\n    def __init__(self, coordinator):\n        self.coordinator = coordinator",
    )
    source = source.replace(
        "from ...api.subjects import subject_name",
        "def subject_name(value):\n    return {'M': 'Mathematik', 'D': 'Deutsch'}.get(value, value)",
    )
    source = source.replace(
        "from ...const import CONF_CHILD_NAME, CONF_CHILD_SHORTCUT",
        "CONF_CHILD_NAME = 'child_name'\nCONF_CHILD_SHORTCUT = 'child_shortcut'",
    )
    source = source.replace(
        "from ..stundenplan.sensor import child_label",
        "def child_label(entry):\n    return 'Maxim (Mk)'",
    )
    source = source.replace(
        "from .helpers import entries_for, plan_days, today, tomorrow",
        "",
    )

    def plan_days(data):
        return data.get("tage", []) if isinstance(data, dict) else []

    def entries_for(data, wanted):
        target = wanted.isoformat()
        for day in plan_days(data):
            if day.get("datum") == target:
                return day.get("eintraege", [])
        return []

    namespace = {
        "__name__": "sph_vertretung_sensor",
        "plan_days": plan_days,
        "entries_for": entries_for,
        "today": lambda: date(2026, 8, 26),
        "tomorrow": lambda: date(2026, 8, 27),
    }
    exec(compile(source, str(SENSOR_PATH), "exec"), namespace)
    return namespace


def test_json_payload_contains_full_plan():
    module = _load_sensor_module()
    coordinator = SimpleNamespace(
        data={
            "tage": [
                {
                    "datum": "2026-08-26",
                    "wochentag": "Mittwoch",
                    "eintraege": [
                        {
                            "fach": "M",
                            "art": "Entf.",
                            "art_lang": "Entfall",
                            "entfall": True,
                            "stunden": [1, 2],
                        }
                    ],
                    "hinweise": ["Hinweis"],
                    "anzahl": 1,
                },
                {
                    "datum": "2026-08-27",
                    "wochentag": "Donnerstag",
                    "eintraege": [
                        {
                            "fach": "D",
                            "art": "Vertr",
                            "art_lang": "Vertretung",
                            "entfall": False,
                            "stunden": [3],
                        }
                    ],
                    "hinweise": [],
                    "anzahl": 1,
                },
            ],
            "aktualisiert": "2026-08-26T07:12:44",
            "wird_aktualisiert": False,
        },
        last_successful_data=None,
    )
    timetable = SimpleNamespace(data={"klasse": "05cG"}, last_successful_data=None)
    entry = SimpleNamespace(data={"child_name": "Maxim", "child_shortcut": "Mk"})

    payload = module["vertretung_payload"](coordinator, timetable, entry)
    encoded = module["compact_json"](payload)
    decoded = json.loads(encoded)

    assert decoded["kind"] == "Maxim"
    assert decoded["kind_kürzel"] == "Mk"
    assert decoded["klasse"] == "05cG"
    assert decoded["anzahl_heute"] == 1
    assert decoded["anzahl_morgen"] == 1
    assert decoded["entfaelle_heute"] == 1
    assert decoded["entfaelle_morgen"] == 0
    assert decoded["heute"][0]["fach_lang"] == "Mathematik"
    assert decoded["morgen"][0]["fach_lang"] == "Deutsch"
    assert decoded["tage"][0]["eintraege"][0]["art_lang"] == "Entfall"
    assert decoded["aktualisiert"] == "2026-08-26T07:12:44"
