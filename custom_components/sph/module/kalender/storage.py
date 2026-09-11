from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from homeassistant.helpers.storage import Store

STORE_VERSION = 1
STORE_KEY_PREFIX = "sph_calendar_manual"


class SphCalendarManualStore:
    """Persist manually added calendar events independently of SPH updates."""

    def __init__(self, hass, entry_id: str):
        self._store = Store(hass, STORE_VERSION, f"{STORE_KEY_PREFIX}_{entry_id}")
        self._items: list[dict] = []

    @property
    def items(self) -> list[dict]:
        return deepcopy(self._items)

    async def async_load(self) -> list[dict]:
        data = await self._store.async_load()
        raw_items = data.get("items", []) if isinstance(data, dict) else []
        self._items = [dict(item) for item in raw_items if isinstance(item, dict)]
        return self.items

    async def async_add(self, item: dict) -> dict:
        stored = dict(item)
        stored["uid"] = str(
            stored.get("uid") or f"sph-kalender-manual-{uuid4().hex}"
        )
        stored["quelle"] = "manuell"
        stored["created_at"] = str(
            stored.get("created_at") or datetime.now(timezone.utc).isoformat()
        )
        self._items.append(stored)
        await self._async_save()
        return deepcopy(stored)

    async def async_delete(self, uid: str) -> bool:
        wanted = str(uid or "").strip()
        before = len(self._items)
        self._items = [
            item for item in self._items if str(item.get("uid", "")).strip() != wanted
        ]
        changed = len(self._items) != before
        if changed:
            await self._async_save()
        return changed

    async def _async_save(self) -> None:
        await self._store.async_save({"items": self._items})
