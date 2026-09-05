"""Sensor platform dispatcher for the SPH modules."""

from .module.kalender.sensor import SphCalendarJsonSensor, SphCalendarSensor
from .module.lerngruppen.sensor import (
    SphLearningGroupsJsonSensor,
    SphLearningGroupsSensor,
)
from .module.meinunterricht.sensor import (
    SphMeinUnterrichtJsonSensor,
    SphMeinUnterrichtSensor,
)
from .module.stundenplan.sensor import SphTimetableJsonSensor, SphTimetableSensor


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data["sph"][entry.entry_id]
    async_add_entities(
        [
            SphTimetableSensor(data["timetable"], entry),
            SphTimetableJsonSensor(data["timetable"], entry),
            SphCalendarSensor(data["calendar"], data["timetable"], entry),
            SphCalendarJsonSensor(data["calendar"], data["timetable"], entry),
            SphMeinUnterrichtSensor(data["meinunterricht"], entry),
            SphMeinUnterrichtJsonSensor(data["meinunterricht"], entry),
            SphLearningGroupsSensor(data["lerngruppen"], entry),
            SphLearningGroupsJsonSensor(data["lerngruppen"], entry),
        ]
    )


__all__ = [
    "async_setup_entry",
    "SphTimetableSensor",
    "SphTimetableJsonSensor",
    "SphCalendarSensor",
    "SphCalendarJsonSensor",
    "SphMeinUnterrichtSensor",
    "SphMeinUnterrichtJsonSensor",
    "SphLearningGroupsSensor",
    "SphLearningGroupsJsonSensor",
]
