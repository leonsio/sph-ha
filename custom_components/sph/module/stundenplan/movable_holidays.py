"""Movable school holidays published by the Hessian school authorities."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from html.parser import HTMLParser
import logging
import re

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from ...const import CONF_CHILD_NAME, CONF_CHILD_SHORTCUT, CONF_SCHOOL_DISTRICT, SCHOOL_DISTRICT_NONE

_LOGGER = logging.getLogger(__name__)

SOURCE_URL = "https://schulaemter.hessen.de/schulbesuch/bewegliche-ferientage"
REFRESH_INTERVAL = timedelta(days=1)
STORE_VERSION = 1

SCHOOL_DISTRICTS = [
    "Bad Vilbel",
    "Bebra",
    "Darmstadt",
    "Frankfurt am Main",
    "Fritzlar",
    "Fulda",
    "Gießen",
    "Hanau",
    "Heppenheim",
    "Kassel",
    "Marburg",
    "Offenbach am Main",
    "Rüsselsheim am Main",
    "Weilburg",
    "Wiesbaden",
]

MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "maerz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


class _HolidayPageParser(HTMLParser):
    """Extract h2/h3/li text while ignoring the rest of the page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current_tag: str | None = None
        self.buffer: list[str] = []
        self.items: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"h2", "h3", "li"}:
            self.current_tag = tag
            self.buffer = []

    def handle_data(self, data):
        if self.current_tag:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == self.current_tag:
            text = re.sub(r"\s+", " ", "".join(self.buffer)).strip()
            if text:
                self.items.append((tag, text))
            self.current_tag = None
            self.buffer = []


def current_school_year(today: date) -> str:
    """Return the Hessian school-year label used on the source page."""
    first = today.year if today.month >= 8 else today.year - 1
    return f"{first}/{first + 1}"


def _parse_date(text: str) -> date | None:
    match = re.search(
        r"\b(\d{1,2})\.\s*(?:den\s+)?([A-Za-zÄÖÜäöüß]+)\s+(\d{4})\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    day = int(match.group(1))
    month_name = match.group(2).casefold().replace("ä", "ae")
    month = MONTHS.get(month_name)
    if month is None:
        return None
    try:
        return date(int(match.group(3)), month, day)
    except ValueError:
        return None


def _summary(text: str) -> str:
    match = re.search(r"\(([^()]*)\)\s*$", text)
    return match.group(1).strip() if match and match.group(1).strip() else "Beweglicher Ferientag"


def parse_district_holidays(html: str, district: str, school_year: str) -> list[dict]:
    """Parse only one district and one explicitly labelled school year."""
    parser = _HolidayPageParser()
    parser.feed(html)

    in_district = False
    in_year = False
    result: list[dict] = []
    wanted_year = f"schuljahr {school_year}".casefold()

    for tag, text in parser.items:
        if tag == "h2":
            in_district = text.casefold() == district.casefold()
            in_year = False
            continue
        if not in_district:
            continue
        if tag == "h3":
            in_year = text.casefold() == wanted_year
            continue
        if tag != "li" or not in_year:
            continue

        holiday_date = _parse_date(text)
        if holiday_date is not None:
            result.append(
                {
                    "date": holiday_date.isoformat(),
                    "summary": _summary(text),
                }
            )

    return sorted(result, key=lambda item: item["date"])


def movable_holiday_calendar_entity_id(entry) -> str:
    """Return the deterministic entity id used by the timetable free-day overlay."""
    name = str(entry.data.get(CONF_CHILD_NAME, "")).strip()
    shortcut = str(entry.data.get(CONF_CHILD_SHORTCUT, "")).strip()
    child = "_".join(part for part in (name, shortcut) if part)
    suffix = slugify(child) if child else "schulportal_hessen"
    return f"calendar.bewegliche_ferientage_{suffix}"


class SphMovableHolidaysCoordinator(DataUpdateCoordinator):
    """Daily cache for one selected Hessian school district."""

    def __init__(self, hass, entry):
        self.entry = entry
        self.district = str(entry.data.get(CONF_SCHOOL_DISTRICT, SCHOOL_DISTRICT_NONE)).strip()
        self.store = Store(hass, STORE_VERSION, f"sph_movable_holidays_{entry.entry_id}")
        self._cached: dict = {}
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Schulportal Hessen bewegliche Ferientage",
            update_interval=REFRESH_INTERVAL if self.enabled else None,
        )

    @property
    def enabled(self) -> bool:
        return bool(self.district and self.district != SCHOOL_DISTRICT_NONE)

    def _school_year(self) -> str:
        tz = dt_util.get_time_zone(self.hass.config.time_zone)
        return current_school_year(dt_util.now().astimezone(tz).date())

    async def async_load_cache(self) -> None:
        stored = await self.store.async_load() or {}
        if (
            isinstance(stored, dict)
            and stored.get("district") == self.district
            and stored.get("school_year") == self._school_year()
            and isinstance(stored.get("events"), list)
        ):
            self._cached = stored
            self.async_set_updated_data(list(stored.get("events", [])))
            return

        # Never reuse data from another district or school year.
        self._cached = {
            "district": self.district,
            "school_year": self._school_year(),
            "events": [],
        }
        await self.store.async_save(self._cached)

    async def _async_update_data(self):
        if not self.enabled:
            return []

        school_year = self._school_year()
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(SOURCE_URL, timeout=30) as response:
                response.raise_for_status()
                html = await response.text()
            events = parse_district_holidays(html, self.district, school_year)
            if not events:
                raise ValueError(
                    f"Keine beweglichen Ferientage für {self.district}, Schuljahr {school_year}, gefunden"
                )
        except Exception as err:
            cached_events = list(self._cached.get("events", []))
            _LOGGER.warning(
                "SPH: bewegliche Ferientage für %s konnten nicht aktualisiert werden (%s); "
                "gespeicherte Daten bleiben erhalten (%d Termine)",
                self.district,
                err,
                len(cached_events),
            )
            return cached_events

        self._cached = {
            "district": self.district,
            "school_year": school_year,
            "events": events,
        }
        await self.store.async_save(self._cached)
        _LOGGER.debug(
            "SPH: %d bewegliche Ferientage für %s im Schuljahr %s gespeichert",
            len(events),
            self.district,
            school_year,
        )
        return events


class SphMovableHolidaysCalendar(CoordinatorEntity, CalendarEntity):
    """Read-only calendar containing movable holidays for the selected district."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-star"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_movable_holidays_calendar"
        self._attr_name = f"Bewegliche Ferientage {coordinator.district}"

    def _events(self) -> list[CalendarEvent]:
        result: list[CalendarEvent] = []
        for item in self.coordinator.data or []:
            try:
                start = date.fromisoformat(str(item.get("date", "")))
            except (TypeError, ValueError):
                continue
            result.append(
                CalendarEvent(
                    start=start,
                    end=start + timedelta(days=1),
                    summary=str(item.get("summary") or "Beweglicher Ferientag"),
                    uid=(
                        f"sph-beweglicher-ferientag-{self.entry.entry_id}-"
                        f"{start.isoformat()}"
                    ),
                )
            )
        return result

    @property
    def event(self) -> CalendarEvent | None:
        today = dt_util.now().astimezone(
            dt_util.get_time_zone(self.hass.config.time_zone)
        ).date()
        for event in self._events():
            if event.end > today:
                return event
        return None

    async def async_get_events(self, hass, start_date: datetime, end_date: datetime):
        start_day = start_date.date()
        end_day = end_date.date()
        return [
            event
            for event in self._events()
            if event.end > start_day and event.start < end_day
        ]
