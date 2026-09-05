from __future__ import annotations

from datetime import datetime, time, timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ...api.client import SphAuthClient
from ...const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
from .client import SphLearningGroupsClient

_LOGGER = logging.getLogger(__name__)


class SphLearningGroupsCoordinator(DataUpdateCoordinator):
    """Coordinator for SPH Lerngruppen/Leistungskontrollen."""

    def __init__(self, hass, entry, auth: SphAuthClient, timetable_coordinator):
        self.entry = entry
        self.client = SphLearningGroupsClient(auth)
        self.timetable_coordinator = timetable_coordinator
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Schulportal Hessen Lerngruppen",
            update_interval=timedelta(
                minutes=int(entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL))
            ),
        )

    async def _async_update_data(self):
        try:
            items = await self.hass.async_add_executor_job(self.client.get_assessments)
            return [self._with_timetable_times(item) for item in (items or [])]
        except Exception as err:
            raise UpdateFailed(str(err)) from err

    def _timetable_data(self):
        return (
            self.timetable_coordinator.data
            or self.timetable_coordinator.last_successful_data
            or {}
        )

    def _with_timetable_times(self, item: dict) -> dict:
        result = dict(item)
        try:
            day = datetime.fromisoformat(str(item.get("datum", ""))).date()
        except ValueError:
            return result

        periods = [int(value) for value in item.get("stunden", []) if str(value).isdigit()]
        if not periods:
            result.update({"start": day.isoformat(), "end": day.isoformat(), "all_day": True})
            return result

        start_time, end_time = self._period_window(day.weekday(), periods)
        if start_time is None or end_time is None:
            result.update({"start": day.isoformat(), "end": day.isoformat(), "all_day": True})
            return result

        start_dt = datetime.combine(day, start_time)
        end_dt = datetime.combine(day, end_time)
        if end_dt <= start_dt:
            end_dt = start_dt + timedelta(minutes=1)
        result.update(
            {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "all_day": False,
            }
        )
        return result

    def _period_window(self, weekday: int, periods: list[int]) -> tuple[time | None, time | None]:
        data = self._timetable_data()
        days = data.get("own") or data.get("all") or []
        if weekday < 0 or weekday >= len(days):
            return None, None

        lessons = days[weekday] or []
        first = min(periods)
        last = max(periods)
        start_value = None
        end_value = None

        for lesson in lessons:
            try:
                index = int(lesson.get("index"))
                duration = max(1, int(lesson.get("duration", 1)))
            except (TypeError, ValueError):
                continue
            covered_last = index + duration - 1
            if index <= first <= covered_last and start_value is None:
                start_value = self._parse_time(lesson.get("start"))
            if index <= last <= covered_last:
                end_value = self._parse_time(lesson.get("end"))

        return start_value, end_value

    @staticmethod
    def _parse_time(value) -> time | None:
        text = str(value or "").strip()
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).time()
            except ValueError:
                continue
        return None
