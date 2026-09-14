from __future__ import annotations

from datetime import datetime
from html import unescape
import logging
import re

from bs4 import BeautifulSoup

from ...api.client import SphAuthClient
from ...api.subjects import subject_from_course
from ...const import SPH_BASE

_LOGGER = logging.getLogger(__name__)

WEEKDAYS = (
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
)


class SphMeinUnterrichtClient:
    """Access and parse the student "Mein Unterricht" page."""

    def __init__(self, auth: SphAuthClient):
        self.auth = auth

    @property
    def session(self):
        return self.auth.session

    def get_homework(self):
        """Fetch current course entries and return all available homework tasks."""
        for attempt in range(2):
            try:
                self.auth.login(force=attempt == 1)
                response = self.session.get(
                    f"{SPH_BASE}/meinunterricht.php",
                    allow_redirects=False,
                    timeout=20,
                )
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location")
                    if not location:
                        raise RuntimeError("Keine SPH-Weiterleitung für Mein Unterricht.")
                    response = self.session.get(
                        location
                        if location.startswith("http")
                        else f"{SPH_BASE}/{location.lstrip('/')}",
                        allow_redirects=False,
                        timeout=20,
                    )
                response.raise_for_status()
                html = self.auth._decrypt_tags(response.text)
                soup = BeautifulSoup(html, "html.parser")
                table = soup.select_one("#aktuellTable tbody")
                if table is None:
                    table = soup.select_one("#content .pupilbox table tbody")
                if table is None:
                    raise RuntimeError(
                        "Die SPH-Seite Mein Unterricht enthält keine Tabelle mit aktuellen Einträgen."
                    )
                return self._parse(table)
            except RuntimeError:
                if attempt == 0:
                    _LOGGER.warning(
                        "SPH: Mein-Unterricht-Abruf fehlgeschlagen; erneuere Anmeldung und versuche es erneut"
                    )
                    continue
                raise
            except Exception:
                if attempt == 0:
                    _LOGGER.warning(
                        "SPH: Fehler beim Mein-Unterricht-Abruf; erneuere Anmeldung und versuche es erneut",
                        exc_info=True,
                    )
                    continue
                raise

    @classmethod
    def _parse(cls, tbody):
        tasks = []
        for row in tbody.find_all("tr", recursive=False):
            homework = row.select_one(".homework .realHomework")
            if homework is None:
                continue

            text = cls._clean_homework(homework)
            if not text:
                continue

            name = row.select_one(".name")
            date_element = row.select_one(".datum")
            teacher = row.select_one(".teacher button")
            topic = row.select_one(".thema")
            done_element = row.select_one(".homework .done")
            undone_element = row.select_one(".homework .undone")

            course = unescape(name.get_text(" ", strip=True)) if name else ""
            date_text = date_element.get_text(" ", strip=True) if date_element else ""
            date_iso, weekday = cls._parse_date(date_text)
            teacher_code = cls._extract_teacher_code(teacher)
            done = cls._is_visible(done_element)
            undone = cls._is_visible(undone_element)
            status = (
                done_element.get_text(" ", strip=True).casefold() if done_element else ""
            )
            status_classes = (
                set(done_element.get("class", [])) if done_element else set()
            )
            if "offen" in status or "label-warning" in status_classes:
                completed = False
            elif "erledigt" in status or "label-default" in status_classes:
                completed = True
            else:
                completed = done and not undone or done

            tasks.append(
                {
                    "datum": date_iso or date_text,
                    "wochentag": weekday,
                    "fach": cls._extract_subject(course),
                    "kurs": course,
                    "lehrer": teacher_code,
                    "thema": unescape(topic.get_text(" ", strip=True)) if topic else "",
                    "aufgabe": text,
                    "erledigt": completed,
                    "entry_id": row.get("data-entry", ""),
                    "book_id": row.get("data-book", ""),
                }
            )
        return tasks

    @staticmethod
    def _clean_homework(element) -> str:
        for br in element.find_all("br"):
            br.replace_with("\n")
        text = unescape(element.get_text("", strip=False))
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)

    @staticmethod
    def _parse_date(value: str) -> tuple[str, str]:
        try:
            parsed = datetime.strptime(value.strip(), "%d.%m.%Y")
        except (TypeError, ValueError):
            return "", ""
        return parsed.date().isoformat(), WEEKDAYS[parsed.weekday()]

    @staticmethod
    def _extract_subject(course: str) -> str:
        """Normalize a course name to its plain subject name."""
        return subject_from_course(course)

    @staticmethod
    def _extract_teacher_code(element) -> str:
        if element is None:
            return ""
        text = element.get_text(" ", strip=True)
        title = element.get("title", "")
        match = re.search(r"\(([A-Za-zÄÖÜäöüß]+)\)", title)
        return match.group(1) if match else text

    @staticmethod
    def _is_visible(element) -> bool:
        if element is None:
            return False
        classes = set(element.get("class", []))
        return "hidden" not in classes
