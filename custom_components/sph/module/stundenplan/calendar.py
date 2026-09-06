"""Native Home Assistant calendar for the personal SPH timetable."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
import re

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .sensor import child_label, subject_name

PAST_WEEKS = 2
FUTURE_WEEKS = 8


def _badge_values(value) -> list[str]:
    """Return normalized A/B badge values from one timetable lesson."""
    if value is None or value == "":
        return []
    raw = value if isinstance(value, (list, tuple, set)) else re.split(r"[,;/|]+", str(value))
    return [str(item).strip().replace("(", "").replace(")", "").upper() for item in raw if str(item).strip()]


def _week_code(value) -> str:
    """Extract the current A/B week code from the SPH week marker."""
    text = str(value or "").strip().upper().replace("(", " ").replace(")", " ")
    match = re.search(r"(?:^|\s)([AB])(?:$|\s)", text)
    if match:
        return match.group(1)
    return text if text in {"A", "B"} else ""


def _slot_key(lesson: dict) -> tuple:
    return (
        str(lesson.get("start", "")).strip(),
        str(lesson.get("end", "")).strip(),
        lesson.get("index"),
        lesson.get("duration", 1),
    )


def _filter_day_for_week(day, week: str) -> list[dict]:
    """Apply the same A/B counterpart semantics as the KFG cards."""
    lessons = list(day or [])
    wanted = _week_code(week)
    if not wanted:
        return lessons

    groups: dict[tuple, list[dict]] = {}
    order: list[tuple] = []
    for lesson in lessons:
        key = _slot_key(lesson)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(lesson)

    result: list[dict] = []
    for key in order:
        group = groups[key]
        matching = [lesson for lesson in group if wanted in _badge_values(lesson.get("badge"))]
        unbadged = [lesson for lesson in group if not _badge_values(lesson.get("badge"))]
        has_explicit = any(_badge_values(lesson.get("badge")) for lesson in group)

        if matching:
            result.extend(matching)
        elif has_explicit:
            result.extend(unbadged)
        else:
            result.extend(unbadged)
    return result


class SphTimetableCalendar(CoordinatorEntity, CalendarEntity):
    """Read-only rolling calendar generated from the personal timetable."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_timetable_calendar"
        self._attr_name = f"Stundenplan {child_label(entry)}"

    def _timezone(self):
        return dt_util.get_time_zone(self.hass.config.time_zone)

    def _today(self) -> date:
        return dt_util.now().astimezone(self._timezone()).date()

    def _window(self) -> tuple[datetime, datetime]:
        """Return rolling -2/+8 week bounds; end is exclusive."""
        today = self._today()
        start_day = today - timedelta(weeks=PAST_WEEKS)
        end_day = today + timedelta(weeks=FUTURE_WEEKS) + timedelta(days=1)
        tz = self._timezone()
        return (
            datetime.combine(start_day, time.min, tzinfo=tz),
            datetime.combine(end_day, time.min, tzinfo=tz),
        )

    def _data(self) -> dict:
        return self.coordinator.data or self.coordinator.last_successful_data or {}

    @staticmethod
    def _parse_time(value) -> time | None:
        text = str(value or "").strip()
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).time()
            except ValueError:
                continue
        return None

    def _week_for_date(self, target: date, current_week: str) -> str:
        """Calculate A/B week for a target date from the currently reported week."""
        current = _week_code(current_week)
        if current not in {"A", "B"}:
            return ""
        today = self._today()
        current_monday = today - timedelta(days=today.weekday())
        target_monday = target - timedelta(days=target.weekday())
        offset = (target_monday - current_monday).days // 7
        if offset % 2 == 0:
            return current
        return "B" if current == "A" else "A"

    def _week_day_event(self, target: date, week: str) -> CalendarEvent | None:
        """Create one all-day A/B marker for a single school day."""
        code = _week_code(week)
        if code not in {"A", "B"}:
            return None
        return CalendarEvent(
            start=target,
            end=target + timedelta(days=1),
            summary=f"Schulwoche {code}",
            uid=f"sph-schulwoche-{self.entry.entry_id}-{target.isoformat()}-{code}",
        )

    def _lesson_event(self, lesson: dict, target: date, week: str) -> CalendarEvent | None:
        start_time = self._parse_time(lesson.get("start"))
        end_time = self._parse_time(lesson.get("end"))
        if start_time is None or end_time is None:
            return None

        tz = self._timezone()
        start = datetime.combine(target, start_time, tzinfo=tz)
        end = datetime.combine(target, end_time, tzinfo=tz)
        if end <= start:
            end = start + timedelta(minutes=1)

        subject = subject_name(lesson.get("subject")) or str(lesson.get("subject") or "Unterricht")
        teacher = str(lesson.get("teacher") or "").strip()
        room = str(lesson.get("room") or "").strip()
        index = lesson.get("index")
        duration = lesson.get("duration", 1)
        badge = ", ".join(_badge_values(lesson.get("badge")))

        description_parts = []
        if teacher:
            description_parts.append(f"Lehrkraft: {teacher}")
        if room:
            description_parts.append(f"Raum: {room}")
        if index not in (None, ""):
            try:
                first = int(index)
                last = first + max(1, int(duration)) - 1
                description_parts.append(f"Stunden: {first}" if last == first else f"Stunden: {first}-{last}")
            except (TypeError, ValueError):
                pass

        uid_parts = [
            self.entry.entry_id,
            target.isoformat(),
            str(index or ""),
            str(lesson.get("start") or ""),
            str(lesson.get("subject") or ""),
            badge,
        ]
        uid = "sph-stundenplan-" + "-".join(re.sub(r"[^A-Za-z0-9_-]+", "_", part) for part in uid_parts)

        return CalendarEvent(
            start=start,
            end=end,
            summary=subject,
            description="\n".join(description_parts) or None,
            location=room or None,
            uid=uid,
        )

    def _event_start(self, event: CalendarEvent) -> datetime:
        """Normalize all-day and timed event starts to timezone-aware datetimes."""
        if isinstance(event.start, datetime):
            return event.start if event.start.tzinfo else event.start.replace(tzinfo=self._timezone())
        return datetime.combine(event.start, time.min, tzinfo=self._timezone())

    def _event_end(self, event: CalendarEvent) -> datetime:
        """Normalize all-day and timed event ends to timezone-aware datetimes."""
        if isinstance(event.end, datetime):
            return event.end if event.end.tzinfo else event.end.replace(tzinfo=self._timezone())
        return datetime.combine(event.end, time.min, tzinfo=self._timezone())

    def _events(self) -> list[CalendarEvent]:
        """Generate only the rolling -2/+8 week event set in memory."""
        data = self._data()
        days = data.get("own") or data.get("all") or []
        if not isinstance(days, list) or not days:
            return []

        window_start, window_end = self._window()
        start_day = window_start.date()
        end_day = window_end.date()
        current_week = str(data.get("week_badge") or "")
        free_days = {str(value) for value in (data.get("free_days", []) or [])}
        events: list[CalendarEvent] = []

        target = start_day
        while target < end_day:
            # Any entry in calendar.deutschland_he marks the complete date as
            # school-free. Suppress both lessons and the Schulwoche A/B marker.
            if target.isoformat() in free_days:
                target += timedelta(days=1)
                continue

            weekday = target.weekday()
            if 0 <= weekday < len(days):
                week = self._week_for_date(target, current_week)
                lessons = _filter_day_for_week(days[weekday], week)

                if lessons:
                    week_event = self._week_day_event(target, week)
                    if week_event is not None:
                        events.append(week_event)

                for lesson in lessons:
                    event = self._lesson_event(lesson, target, week)
                    if event is not None:
                        events.append(event)
            target += timedelta(days=1)

        return sorted(events, key=self._event_start)

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        for event in self._events():
            if self._event_end(event) > now:
                return event
        return None

    async def async_get_events(
        self,
        hass,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return timetable events, clamped to the rolling retention window."""
        window_start, window_end = self._window()
        requested_start = max(start_date, window_start)
        requested_end = min(end_date, window_end)
        if requested_start >= requested_end:
            return []

        return [
            event
            for event in self._events()
            if self._event_end(event) > requested_start and self._event_start(event) < requested_end
        ]
