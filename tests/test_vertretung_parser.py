"""Offline regression tests for the Vertretungsplan HTML parser."""

from __future__ import annotations

import pathlib

from bs4 import BeautifulSoup

CLIENT_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components" / "sph" / "module" / "vertretung" / "client.py"
)
FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "vertretungsplan.html"


def _load_client():
    source = CLIENT_PATH.read_text(encoding="utf-8")
    source = source.replace("from ...api.client import SphAuthClient", "SphAuthClient = object")
    source = source.replace(
        "from ...const import SPH_BASE",
        'SPH_BASE = "https://start.schulportal.hessen.de"',
    )
    namespace: dict = {"__name__": "sph_vertretung_client"}
    exec(compile(source, str(CLIENT_PATH), "exec"), namespace)
    return namespace["SphVertretungClient"]


SphVertretungClient = _load_client()


def test_parser():
    soup = BeautifulSoup(FIXTURE.read_text(encoding="utf-8"), "html.parser")
    data = SphVertretungClient._parse_page(soup)

    assert [day["datum"] for day in data["tage"]] == [
        "2026-08-26",
        "2026-08-27",
        "2026-08-28",
    ]
    assert data["aktualisiert"] == "2026-08-26T07:12:44"
    assert data["wird_aktualisiert"] is False

    today = data["tage"][0]
    assert today["relativ"] == "heute"
    assert today["woche"] == "A-Woche"
    assert today["anzahl"] == 3
    assert today["entfaelle"] == 2
    assert today["hinweise"] == [
        "Der Schulhof ist wegen Bauarbeiten gesperrt.",
        "Die Mensa öffnet erst ab 12:00 Uhr.",
    ]

    first, second, third = today["eintraege"]
    assert first["stunden"] == [1, 2]
    assert first["entfall"] is True
    assert first["art_lang"] == "Entfall"
    assert second["art"] == "Vertr"
    assert second["art_lang"] == "Vertretung"
    assert second["entfall"] is False
    assert third["art_lang"] == "Entfall"
    assert third["entfall"] is True

    tomorrow = data["tage"][1]
    assert tomorrow["eintraege"][0]["fach_alt"] == "D"
    assert tomorrow["eintraege"][0]["art_lang"] == "Freisetzung"
    assert tomorrow["eintraege"][0]["entfall"] is True

    assert data["tage"][2]["anzahl"] == 0


def test_art_and_lesson_normalization():
    resolve = SphVertretungClient._art_long
    assert resolve("Betr") == "Betreuung"
    assert resolve("taus") == "Tausch"
    assert resolve("Entf.") == "Entfall"
    assert resolve("Wandertag") == "Wandertag"
    assert SphVertretungClient._parse_lessons("1 - 3") == [1, 2, 3]
    assert SphVertretungClient._parse_lessons("4") == [4]
