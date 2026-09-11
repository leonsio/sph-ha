"""Native Home Assistant calendar platform for SPH data."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEntityFeature,
    CalendarEvent,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_COMBINE_CALENDARS,
    CONF_MODULE_KALENDER,
    CONF_MODULE_LERNGRUPPEN,
    CONF_MODULE_STUNDENPLAN,
    DEFAULT_COMBINE_CALENDARS,
    DEFAULT_MODULE_ENABLED,
    DOMAIN,
)
from .module.lerngruppen.calendar import SphLearningGroupsCalendar
from .module.stundenplan.calendar import SphTimetableCalendar
from .module.stundenplan.movable_holidays import SphMovableHolidaysCalendar
from .module.stundenplan.sensor import child_label


def _event_datetime(value: str, all_day: bool, hass) -> date | datetime | None:
    """Convert an SPH ISO value to the type expected by CalendarEvent."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        try:
            parsed_date = date.fromisoformat(str(value))
        except (TypeError, ValueError):
            return None
        if all_day:
            return parsed_date
        parsed = datetime.combine(parsed_date, datetime.min.time())
    if all_day:
        return parsed.date()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.get_time_zone(hass.config.time_zone))
    return parsed


def _calendar_event(item: dict, hass) -> CalendarEvent | None:
    """Convert one cached SPH event to a Home Assistant CalendarEvent."""
    all_day = bool(item.get("all_day", False))
    start = _event_datetime(item.get("start", ""), all_day, hass)
    end = _event_datetime(item.get("end", ""), all_day, hass)
    if start is None:
        return None

    if all_day:
        if end is None or end <= start:
            end = start + timedelta(days=1)
    else:
        if end is None or end <= start:
            end = start + timedelta(minutes=1)

    art = str(item.get("art", "")).strip()
    description = str(item.get("description", "")).strip()
    if art and str(item.get("quelle", "")).strip().lower() != "manuell":
        description = f"Art: {art}" + (f"\n{description}" if description else "")

    return CalendarEvent(
        start=start,
        end=end,
        summary=str(item.get("summary", "")).strip() or art or "Schultermin",
        description=description or None,
        location=str(item.get("location", "")).strip() or None,
        uid=str(item.get("uid", "")).strip() or None,
    )


class SphSchoolCalendar(CoordinatorEntity, CalendarEntity):
    """Calendar containing selected SPH categories plus local user events."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-school"
    _attr_supported_features = (
        CalendarEntityFeature.CREATE_EVENT | CalendarEntityFeature.DELETE_EVENT
    )

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_native_calendar"
        self._attr_name = f"Schulkalender {child_label(entry)}"

    def _events(self) -> list[CalendarEvent]:
        events = []
        for item in self.coordinator.data or []:
            event = _calendar_event(item, self.hass)
            if event is not None:
                events.append(event)
        return sorted(events, key=lambda event: self._sort_key(event.start))

    def _sort_key(self, value: date | datetime) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=dt_util.get_time_zone(self.hass.config.time_zone))
            return value
        return datetime.combine(
            value,
            datetime.min.time(),
            tzinfo=dt_util.get_time_zone(self.hass.config.time_zone),
        )

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        for event in self._events():
            if self._sort_key(event.end) > now:
                return event
        return None

    async def async_get_events(
        self,
        hass,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        result = []
        for event in self._events():
            event_start = self._sort_key(event.start)
            event_end = self._sort_key(event.end)
            if event_end > start_date and event_start < end_date:
                result.append(event)
        return result

    async def async_create_event(self, **kwargs) -> None:
        """Create one locally stored SPH calendar event."""
        await self.coordinator.async_add_manual_event(**kwargs)
        self.async_update_event_listeners()

    async def async_delete_event(
        self,
        uid: str,
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        """Delete a locally stored SPH calendar event."""
        if recurrence_id or recurrence_range:
            raise HomeAssistantError(
                "Wiederholende eigene SPH-Kalendertermine werden derzeit nicht unterstützt"
            )
        if not await self.coordinator.async_delete_manual_event(uid):
            raise HomeAssistantError("Der Termin ist kein löschbarer eigener SPH-Termin")
        self.async_update_event_listeners()


class SphCombinedCalendar(CalendarEntity):
    """Calendar combining enabled SPH calendar sources for one child."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-multiple"

    def __init__(self, data: dict, entry):
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_sph_calendar"
        self._attr_name = f"SPH {child_label(entry)}"
        self._sources: list[CalendarEntity] = []
        self._coordinators = []
        self._school_calendar: SphSchoolCalendar | None = None

        if bool(entry.data.get(CONF_MODULE_STUNDENPLAN, DEFAULT_MODULE_ENABLED)):
            self._sources.append(SphTimetableCalendar(data["timetable"], entry))
            self._coordinators.append(data["timetable"])

        if bool(entry.data.get(CONF_MODULE_LERNGRUPPEN, DEFAULT_MODULE_ENABLED)):
            self._sources.append(SphLearningGroupsCalendar(data["lerngruppen"], entry))
            self._coordinators.append(data["lerngruppen"])

        if bool(entry.data.get(CONF_MODULE_KALENDER, DEFAULT_MODULE_ENABLED)):
            self._school_calendar = SphSchoolCalendar(data["calendar"], entry)
            self._sources.append(self._school_calendar)
            self._coordinators.append(data["calendar"])
            self._attr_supported_features = (
                CalendarEntityFeature.CREATE_EVENT | CalendarEntityFeature.DELETE_EVENT
            )

    async def async_added_to_hass(self) -> None:
        """Attach source helpers and react to every underlying coordinator update."""
        await super().async_added_to_hass()
        for source in self._sources:
            # The source calendars are helpers only and are not added to the
            # entity platform in combined mode. They still need HA context for
            # timezone handling and event conversion.
            source.hass = self.hass

        seen: set[int] = set()
        for coordinator in self._coordinators:
            key = id(coordinator)
            if key in seen:
                continue
            seen.add(key)
            self.async_on_remove(coordinator.async_add_listener(self.async_write_ha_state))

    def _sort_key(self, value: date | datetime) -> datetime:
        tz = dt_util.get_time_zone(self.hass.config.time_zone)
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=tz)
        return datetime.combine(value, datetime.min.time(), tzinfo=tz)

    def _events(self) -> list[CalendarEvent]:
        events: list[CalendarEvent] = []
        for source in self._sources:
            source_events = getattr(source, "_events", None)
            if callable(source_events):
                events.extend(source_events())
        return sorted(events, key=lambda event: self._sort_key(event.start))

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        for event in self._events():
            if self._sort_key(event.end) > now:
                return event
        return None

    async def async_get_events(
        self,
        hass,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Merge events from all enabled SPH modules for the requested range."""
        result: list[CalendarEvent] = []
        for source in self._sources:
            result.extend(await source.async_get_events(hass, start_date, end_date))
        return sorted(result, key=lambda event: self._sort_key(event.start))

    async def async_create_event(self, **kwargs) -> None:
        """Create a local event in the writable SPH school-calendar source."""
        if self._school_calendar is None:
            raise HomeAssistantError("Das SPH-Kalendermodul ist deaktiviert")
        await self._school_calendar.coordinator.async_add_manual_event(**kwargs)
        self.async_update_event_listeners()

    async def async_delete_event(
        self,
        uid: str,
        recurrence_id: str | None = None,
        recurrence_range: str | None = None,
    ) -> None:
        """Delete a local event from the writable SPH school-calendar source."""
        if self._school_calendar is None:
            raise HomeAssistantError("Das SPH-Kalendermodul ist deaktiviert")
        if recurrence_id or recurrence_range:
            raise HomeAssistantError(
                "Wiederholende eigene SPH-Kalendertermine werden derzeit nicht unterstützt"
            )
        if not await self._school_calendar.coordinator.async_delete_manual_event(uid):
            raise HomeAssistantError("Der Termin ist kein löschbarer eigener SPH-Termin")
        self.async_update_event_listeners()


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    combine = bool(entry.data.get(CONF_COMBINE_CALENDARS, DEFAULT_COMBINE_CALENDARS))

    if combine:
        entities: list[CalendarEntity] = [SphCombinedCalendar(data, entry)]
    else:
        entities = [
            SphTimetableCalendar(data["timetable"], entry),
            SphLearningGroupsCalendar(data["lerngruppen"], entry),
        ]
        if bool(entry.data.get(CONF_MODULE_KALENDER, DEFAULT_MODULE_ENABLED)):
            entities.insert(0, SphSchoolCalendar(data["calendar"], entry))

    # The movable-holiday calendar remains a dedicated technical free-day
    # source. It is intentionally not merged into the user-facing SPH calendar.
    if data["movable_holidays"].enabled:
        entities.append(SphMovableHolidaysCalendar(data["movable_holidays"], entry))

    async_add_entities(entities)
