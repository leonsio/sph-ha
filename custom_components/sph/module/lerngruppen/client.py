from __future__ import annotations

from datetime import datetime
import logging
import re

from bs4 import BeautifulSoup

from ...api.client import SphAuthClient
from ...const import SPH_BASE

_LOGGER = logging.getLogger(__name__)


class SphLearningGroupsClient:
    """Fetch and parse SPH Lerngruppen and Leistungskontrollen."""

    def __init__(self, auth: SphAuthClient):
        self.auth = auth

    @property
    def session(self):
        return self.auth.session

    def get_assessments(self) -> list[dict]:
        """Return Leistungskontrollen enriched with teacher data."""
        for attempt in range(2):
            try:
                self.auth.login(force=attempt == 1)
                response = self.session.get(
                    f"{SPH_BASE}/lerngruppen.php",
                    allow_redirects=True,
                    timeout=20,
                )
                response.raise_for_status()
                html = self.auth._decrypt_tags(response.text)
                soup = BeautifulSoup(html, "html.parser")
                groups_table = soup.select_one("#LGs tbody")
                assessments_panel = soup.select_one("#klausuren")
                if groups_table is None or assessments_panel is None:
                    raise RuntimeError(
                        "Die SPH-Seite Lerngruppen enthält nicht die erwarteten Bereiche."
                    )
                groups = self._parse_groups(groups_table)
                assessments = assessments_panel.select("tr[data-type='klausur']")
                return self._parse_assessments(assessments, groups)
            except Exception:
                if attempt == 0:
                    _LOGGER.warning(
                        "SPH: Lerngruppen-Abruf fehlgeschlagen; erneuere Anmeldung und versuche es erneut",
                        exc_info=True,
                    )
                    continue
                raise

    @classmethod
    def _parse_groups(cls, tbody) -> dict[str, dict]:
        groups: dict[str, dict] = {}
        for row in tbody.find_all("tr", recursive=False):
            group_id = str(row.get("data-id", "")).strip()
            cells = row.find_all("td", recursive=False)
            if not group_id or len(cells) < 3:
                continue

            course_cell = BeautifulSoup(str(cells[1]), "html.parser")
            for small in course_cell.find_all("small"):
                small.decompose()
            course = " ".join(course_cell.stripped_strings).strip()

            teacher = ""
            teacher_code = ""
            button = cells[2].find("button", title=True)
            if button is not None:
                title = str(button.get("title", "")).strip()
                match = re.match(r"^(.*?)\s*\(([^()]+)\)\s*$", title)
                if match:
                    teacher = match.group(1).strip()
                    teacher_code = match.group(2).strip()
                else:
                    teacher = title

            groups[group_id] = {
                "kurs": course,
                "lehrkraft": teacher,
                "lehrkraft_kürzel": teacher_code,
            }
        return groups

    @classmethod
    def _parse_assessments(cls, rows, groups: dict[str, dict]) -> list[dict]:
        result = []
        for row in rows:
            cells = row.find_all("td", recursive=False)
            if len(cells) < 5:
                continue

            values = []
            for index, cell in enumerate(cells[:5]):
                parsed = BeautifulSoup(str(cell), "html.parser")
                for small in parsed.find_all("small"):
                    small.decompose()
                if index == 0:
                    for label in parsed.select(".label"):
                        label.decompose()
                values.append(" ".join(parsed.stripped_strings).strip())

            date_value = cls._parse_date(values[0])
            if date_value is None:
                continue

            group_id = str(row.get("data-lerngruppe", "")).strip()
            group = groups.get(group_id, {})
            course = group.get("kurs") or values[1]
            art = values[2].strip()
            periods = [int(value) for value in re.findall(r"\d+", values[3])]
            duration_match = re.search(r"(\d+)", values[4])
            duration_minutes = int(duration_match.group(1)) if duration_match else None
            assessment_id = str(row.get("data-id", "")).strip()

            result.append(
                {
                    "id": assessment_id,
                    "lerngruppe_id": group_id,
                    "datum": date_value.date().isoformat(),
                    "kurs": course,
                    "art": art,
                    "stunden": periods,
                    "stunden_text": values[3],
                    "dauer_minuten": duration_minutes,
                    "lehrkraft": group.get("lehrkraft", ""),
                    "lehrkraft_kürzel": group.get("lehrkraft_kürzel", ""),
                    "summary": f"{art}: {course}" if art else course,
                    "uid": f"sph-lerngruppen-{assessment_id or group_id + '-' + date_value.date().isoformat()}",
                }
            )

        return sorted(result, key=lambda item: (item.get("datum", ""), item.get("stunden", [])))

    @staticmethod
    def _parse_date(value: str) -> datetime | None:
        match = re.search(r"(\d{2}\.\d{2}\.\d{4})", value or "")
        if not match:
            return None
        try:
            return datetime.strptime(match.group(1), "%d.%m.%Y")
        except ValueError:
            return None
