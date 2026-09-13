from __future__ import annotations

from datetime import date, datetime
import logging
import re

from bs4 import BeautifulSoup

from ...api.client import SphAuthClient
from ...const import SPH_BASE

_LOGGER = logging.getLogger(__name__)

DAY_ID_PATTERN = re.compile(r"^tag(\d{2})_(\d{2})_(\d{4})$")
COLUMN_FIELDS = {
    "Stunde": "stunde",
    "Klasse": "klasse",
    "Klasse_alt": "klasse_alt",
    "Vertreter": "vertreter",
    "Lehrer": "lehrer",
    "Art": "art",
    "Fach": "fach",
    "Fach_alt": "fach_alt",
    "Raum": "raum",
    "Raum_alt": "raum_alt",
    "Hinweis": "hinweis",
}
ART_NAMES = {
    "betr": "Betreuung",
    "vertr": "Vertretung",
    "entf": "Entfall",
    "taus": "Tausch",
    "freis": "Freistunde",
    "raum": "Raumänderung",
    "statt-vertretung": "Statt-Vertretung",
    "paus": "Pausenaufsicht",
    "ses": "Sonderunterricht",
    "vtr. ohne lehrer": "Vertretung ohne Lehrer",
    "freisetzung": "Freisetzung",
    "eva": "EVA",
    "selbstlernzeit": "Selbstlernzeit",
}
CANCELLED_ARTEN = {
    "entfall",
    "freistunde",
    "freisetzung",
    "eva",
    "selbstlernzeit",
}
LAST_UPDATED_PATTERN = re.compile(
    r"(\d{2}\.\d{2}\.\d{4}).{0,8}?(\d{2}:\d{2}(?::\d{2})?)"
)
WEEKDAYS = (
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
)


class SphVertretungClient:
    """Schulportal Hessen substitution plan access and HTML parsing."""

    def __init__(self, auth: SphAuthClient):
        self.auth = auth

    @property
    def session(self):
        return self.auth.session

    def get_substitutions(self):
        """Fetch the substitution plan and recover once from a broken session."""
        for attempt in range(2):
            try:
                self.auth.login(force=attempt == 1)
                response = self.session.get(
                    f"{SPH_BASE}/vertretungsplan.php",
                    allow_redirects=False,
                    timeout=20,
                )
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location")
                    if not location:
                        raise RuntimeError("Keine SPH-Weiterleitung für den Vertretungsplan.")
                    response = self.session.get(
                        location
                        if location.startswith("http")
                        else f"{SPH_BASE}/{location.lstrip('/')}",
                        allow_redirects=False,
                        timeout=20,
                    )
                response.raise_for_status()
                soup = BeautifulSoup(self.auth._decrypt_tags(response.text), "html.parser")
                return self._parse_page(soup)
            except Exception as err:
                if attempt == 0:
                    _LOGGER.warning(
                        "SPH: Vertretungsplan-Abruf fehlgeschlagen (%s); erneuere Anmeldung und versuche es erneut",
                        err,
                    )
                    continue
                raise

    def get_full_plan_for_day(self, day: date):
        """Return the complete plan of one day via the AJAX endpoint."""
        self.auth.login()
        response = self.session.post(
            f"{SPH_BASE}/vertretungsplan.php",
            params={"a": "my"},
            data={"tag": day.strftime("%d.%m.%Y"), "ganzerPlan": "true"},
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError("Unerwartete Antwort des Vertretungsplans.")
        return [self._normalise_ajax_row(row) for row in payload]

    @classmethod
    def _parse_page(cls, soup: BeautifulSoup) -> dict:
        days = []
        for panel in soup.select("div[id^=tag]"):
            match = DAY_ID_PATTERN.match(panel.get("id", ""))
            if not match:
                continue
            day, month, year = (int(part) for part in match.groups())
            try:
                plan_date = date(year, month, day)
            except ValueError:
                _LOGGER.debug("SPH: ungültiges Datum im Panel %s", panel.get("id"))
                continue
            days.append(cls._parse_day(panel, plan_date))

        days.sort(key=lambda item: item["datum"])
        return {
            "tage": days,
            "aktualisiert": cls._parse_last_updated(soup),
            "wird_aktualisiert": cls._is_updating(soup),
        }

    @classmethod
    def _parse_day(cls, panel, plan_date: date) -> dict:
        heading = panel.select_one(".panel-heading")
        relative = ""
        week = ""
        if heading:
            for badge in heading.select(".badge"):
                text = badge.get_text(" ", strip=True)
                if not text:
                    continue
                if "woche" in " ".join(badge.get("class", [])).lower():
                    week = text
                elif not relative:
                    relative = text

        entries = []
        table = panel.select_one("table.table[data-classview]") or panel.select_one("table.table")
        if table is not None and table.select_one(".alert.alert-warning") is None:
            entries = cls._parse_table(table)

        return {
            "datum": plan_date.isoformat(),
            "datum_de": plan_date.strftime("%d.%m.%Y"),
            "wochentag": WEEKDAYS[plan_date.weekday()],
            "relativ": relative,
            "woche": week,
            "eintraege": entries,
            "anzahl": len(entries),
            "entfaelle": sum(1 for entry in entries if entry.get("entfall")),
            "hinweise": cls._parse_news(panel),
        }

    @classmethod
    def _parse_table(cls, table) -> list[dict]:
        columns = []
        for index, header in enumerate(table.select("th")):
            key = COLUMN_FIELDS.get(header.get("data-field") or "")
            if key is None:
                key = COLUMN_FIELDS.get(header.get_text(" ", strip=True))
            if key is not None:
                columns.append((index, key))
        if not columns:
            return []

        entries = []
        body = table.find("tbody") or table
        for row in body.find_all("tr", recursive=False):
            cells = row.find_all(["td", "th"], recursive=False)
            if not cells or (row.find("th") is not None and row.find("td") is None):
                continue
            entry = {key: "" for key in COLUMN_FIELDS.values()}
            for index, key in columns:
                if index < len(cells):
                    entry[key] = cells[index].get_text(" ", strip=True)
            if any(entry.values()):
                entries.append(cls._enrich(entry))
        return entries

    @classmethod
    def _normalise_ajax_row(cls, row: dict) -> dict:
        entry = {key: "" for key in COLUMN_FIELDS.values()}
        for field, key in COLUMN_FIELDS.items():
            value = row.get(field)
            if value is not None:
                entry[key] = BeautifulSoup(str(value), "html.parser").get_text(" ", strip=True)
        return cls._enrich(entry)

    @classmethod
    def _enrich(cls, entry: dict) -> dict:
        lessons = cls._parse_lessons(entry.get("stunde", ""))
        art_long = cls._art_long(entry.get("art"))
        entry["stunden"] = lessons
        entry["von_stunde"] = lessons[0] if lessons else None
        entry["bis_stunde"] = lessons[-1] if lessons else None
        entry["art_lang"] = art_long
        entry["entfall"] = art_long.casefold() in CANCELLED_ARTEN
        return entry

    @staticmethod
    def _art_long(value) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        key = raw.casefold().rstrip(".")
        if key in ART_NAMES:
            return ART_NAMES[key]
        for name in ART_NAMES.values():
            if key == name.casefold():
                return name
        return raw

    @staticmethod
    def _parse_lessons(value: str) -> list[int]:
        numbers = [int(part) for part in re.findall(r"\d+", value or "")]
        if not numbers:
            return []
        if len(numbers) == 1:
            return numbers
        start, end = numbers[0], numbers[-1]
        if end < start:
            start, end = end, start
        if end - start > 20:
            return sorted(set(numbers))
        return list(range(start, end + 1))

    @staticmethod
    def _parse_news(panel) -> list[str]:
        notes = []
        for cell in panel.select(".infos > tbody > tr > td"):
            if "subheader" in " ".join(cell.parent.get("class", [])):
                continue
            for chunk in re.split(r"<hr[^>]*>", cell.decode_contents()):
                text = BeautifulSoup(chunk, "html.parser").get_text(" ", strip=True)
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    notes.append(text)
        return notes

    @staticmethod
    def _parse_last_updated(soup) -> str | None:
        for element in soup.select(
            ".panel .panel-body .pull-right i, .panel .panel-body .pull-right"
        ):
            match = LAST_UPDATED_PATTERN.search(element.get_text(" ", strip=True))
            if not match:
                continue
            day, time_value = match.groups()
            fmt = (
                "%d.%m.%Y %H:%M:%S"
                if time_value.count(":") == 2
                else "%d.%m.%Y %H:%M"
            )
            try:
                return datetime.strptime(f"{day} {time_value}", fmt).isoformat()
            except ValueError:
                continue
        return None

    @staticmethod
    def _is_updating(soup) -> bool:
        return soup.select_one("#content .alert.alert-danger a[href].btn.btn-primary") is not None
