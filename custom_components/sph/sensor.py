"""Sensor platform dispatcher for the SPH modules."""

from .const import CONF_MODULE_KALENDER, DEFAULT_MODULE_ENABLED
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
    entities = [
        SphTimetableSensor(data["timetable"], entry),
        SphTimetableJsonSensor(data["timetable"], entry),
        SphMeinUnterrichtSensor(data["meinunterricht"], entry),
        SphMeinUnterrichtJsonSensor(data["meinunterricht"], entry),
        SphLearningGroupsSensor(data["lerngruppen"], entry),
        SphLearningGroupsJsonSensor(data["lerngruppen"], entry),
    ]

    if bool(entry.data.get(CONF_MODULE_KALENDER, DEFAULT_MODULE_ENABLED)):
        entities.extend(
            [
                SphCalendarSensor(data["calendar"], data["timetable"], entry),
                SphCalendarJsonSensor(data["calendar"], data["timetable"], entry),
            ]
        )

    async_add_entities(entities)


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
