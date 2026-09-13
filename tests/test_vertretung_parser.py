"""Offline regression tests for the Vertretungsplan HTML parser."""

from __future__ import annotations

import pathlib
import unittest

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


class VertretungParserTest(unittest.TestCase):
    def setUp(self):
        soup = BeautifulSoup(FIXTURE.read_text(encoding="utf-8"), "html.parser")
        self.data = SphVertretungClient._parse_page(soup)

    def test_parser(self):
        data = self.data
        self.assertEqual(
            [day["datum"] for day in data["tage"]],
            ["2026-08-26", "2026-08-27", "2026-08-28"],
        )
        self.assertEqual(data["aktualisiert"], "2026-08-26T07:12:44")
        self.assertFalse(data["wird_aktualisiert"])

        today = data["tage"][0]
        self.assertEqual(today["relativ"], "heute")
        self.assertEqual(today["woche"], "A-Woche")
        self.assertEqual(today["anzahl"], 3)
        self.assertEqual(today["entfaelle"], 2)
        self.assertEqual(
            today["hinweise"],
            [
                "Der Schulhof ist wegen Bauarbeiten gesperrt.",
                "Die Mensa öffnet erst ab 12:00 Uhr.",
            ],
        )

        first, second, third = today["eintraege"]
        self.assertEqual(first["stunden"], [1, 2])
        self.assertTrue(first["entfall"])
        self.assertEqual(first["art_lang"], "Entfall")
        self.assertEqual(second["art"], "Vertr")
        self.assertEqual(second["art_lang"], "Vertretung")
        self.assertFalse(second["entfall"])
        self.assertEqual(third["art_lang"], "Entfall")
        self.assertTrue(third["entfall"])

        tomorrow = data["tage"][1]
        self.assertEqual(tomorrow["eintraege"][0]["fach_alt"], "D")
        self.assertEqual(tomorrow["eintraege"][0]["art_lang"], "Freisetzung")
        self.assertTrue(tomorrow["eintraege"][0]["entfall"])
        self.assertEqual(data["tage"][2]["anzahl"], 0)

    def test_art_and_lesson_normalization(self):
        resolve = SphVertretungClient._art_long
        self.assertEqual(resolve("Betr"), "Betreuung")
        self.assertEqual(resolve("taus"), "Tausch")
        self.assertEqual(resolve("Entf."), "Entfall")
        self.assertEqual(resolve("Wandertag"), "Wandertag")
        self.assertEqual(SphVertretungClient._parse_lessons("1 - 3"), [1, 2, 3])
        self.assertEqual(SphVertretungClient._parse_lessons("4"), [4])


if __name__ == "__main__":
    unittest.main()
