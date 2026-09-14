"""Offline regression tests for the Mein Unterricht HTML parser."""

from __future__ import annotations

import pathlib
import unittest

from bs4 import BeautifulSoup

CLIENT_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components" / "sph" / "module" / "meinunterricht" / "client.py"
)
FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "meinunterricht_pupilbox.html"


def _load_client():
    source = CLIENT_PATH.read_text(encoding="utf-8")
    source = source.replace(
        "from ...api.client import SphAuthClient", "SphAuthClient = object"
    )
    source = source.replace(
        "from ...api.subjects import subject_from_course",
        "subject_from_course = lambda course: course",
    )
    source = source.replace(
        "from ...const import SPH_BASE",
        'SPH_BASE = "https://start.schulportal.hessen.de"',
    )
    namespace: dict = {"__name__": "sph_meinunterricht_client"}
    exec(compile(source, str(CLIENT_PATH), "exec"), namespace)
    return namespace["SphMeinUnterrichtClient"]


SphMeinUnterrichtClient = _load_client()


def _row(status: str = "", classes: str = "done") -> str:
    return f"""
        <tr data-entry="entry-1" data-book="book-1">
          <td class="name">Testfach</td>
          <td class="datum">14.09.2026</td>
          <td class="homework">
            <span class="realHomework">Neutrale Testaufgabe</span>
            <span class="{classes}">{status}</span>
          </td>
        </tr>
    """


class MeinUnterrichtParserTest(unittest.TestCase):
    def setUp(self):
        self.fixture_html = FIXTURE.read_text(encoding="utf-8")

    def test_pupilbox_fixture_statuses_and_entries_without_homework(self):
        tasks = SphMeinUnterrichtClient(_Auth(self.fixture_html)).get_homework()

        self.assertEqual(len(tasks), 3)
        tasks_by_id = {task["entry_id"]: task for task in tasks}
        self.assertNotIn("test-entry-without-homework", tasks_by_id)
        self.assertTrue(tasks_by_id["test-entry-completed"]["erledigt"])
        self.assertFalse(tasks_by_id["test-entry-open"]["erledigt"])
        self.assertFalse(tasks_by_id["test-entry-with-content"]["erledigt"])

    def test_pupilbox_fixture_multiline_homework(self):
        tasks = SphMeinUnterrichtClient(_Auth(self.fixture_html)).get_homework()
        tasks_by_id = {task["entry_id"]: task for task in tasks}

        self.assertEqual(
            tasks_by_id["test-entry-open"]["aufgabe"],
            "Erste neutrale Zeile\nZweite neutrale Zeile",
        )

    def test_legacy_visibility_fallback_is_preserved(self):
        for classes, expected in (("done", True), ("done hidden", False)):
            with self.subTest(classes=classes):
                tbody = BeautifulSoup(
                    f"<table><tbody>{_row('', classes)}</tbody></table>",
                    "html.parser",
                ).tbody
                task = SphMeinUnterrichtClient._parse(tbody)[0]
                self.assertIs(task["erledigt"], expected)

    def test_get_homework_accepts_pupilbox_layout(self):
        tasks = SphMeinUnterrichtClient(_Auth(self.fixture_html)).get_homework()

        self.assertEqual(len(tasks), 3)

    def test_get_homework_prefers_legacy_layout(self):
        html = f"""
            {self.fixture_html}
            <table id="aktuellTable"><tbody>
              {_row().replace('entry-1', 'legacy-entry')}
            </tbody></table>
        """

        tasks = SphMeinUnterrichtClient(_Auth(html)).get_homework()

        self.assertEqual(tasks[0]["entry_id"], "legacy-entry")


class _Response:
    status_code = 200
    headers = {}

    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


class _Session:
    def __init__(self, html):
        self.html = html

    def get(self, *args, **kwargs):
        return _Response(self.html)


class _Auth:
    def __init__(self, html):
        self.session = _Session(html)

    def login(self, force=False):
        pass

    @staticmethod
    def _decrypt_tags(html):
        return html


if __name__ == "__main__":
    unittest.main()
