"""Binary sensor platform for SPH substitution-plan helpers."""

from .module.vertretung.binary_sensor import SphFirstLessonCancelledSensor


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data["sph"][entry.entry_id]
    coordinator = data["vertretung"]
    if not coordinator.enabled:
        return
    async_add_entities(
        [
            SphFirstLessonCancelledSensor(coordinator, entry, 0),
            SphFirstLessonCancelledSensor(coordinator, entry, 1),
        ]
    )


__all__ = ["async_setup_entry", "SphFirstLessonCancelledSensor"]
