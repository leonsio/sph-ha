from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from homeassistant.helpers.storage import Store

STORE_VERSION = 1
STORE_KEY_PREFIX = "sph_meinunterricht_manual"
RETENTION_DAYS = 7


class SphMeinUnterrichtManualStore:
    """Persist manually added homework independently of SPH updates."""

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
        stored["id"] = str(stored.get("id") or f"manual-{uuid4().hex}")
        stored["uid"] = str(stored.get("uid") or f"sph-meinunterricht-{stored['id']}")
        stored["quelle"] = "manuell"
        stored["created_at"] = str(
            stored.get("created_at") or datetime.now(timezone.utc).isoformat()
        )

        try:
            homework_date = date.fromisoformat(str(stored.get("datum", "")))
            stored["expires_on"] = (homework_date + timedelta(days=RETENTION_DAYS)).isoformat()
        except ValueError:
            stored["expires_on"] = ""

        self._items.append(stored)
        await self._async_save()
        return deepcopy(stored)

    async def async_delete(self, item_id: str) -> bool:
        wanted = str(item_id or "").strip()
        before = len(self._items)
        self._items = [item for item in self._items if str(item.get("id", "")) != wanted]
        changed = len(self._items) != before
        if changed:
            await self._async_save()
        return changed

    async def async_purge_expired(self, today: date) -> int:
        """Remove manual homework seven days after its homework date."""
        kept: list[dict] = []
        removed = 0
        for item in self._items:
            expiry = self._expiry_date(item)
            if expiry is not None and today >= expiry:
                removed += 1
                continue
            kept.append(item)

        if removed:
            self._items = kept
            await self._async_save()
        return removed

    @staticmethod
    def _expiry_date(item: dict) -> date | None:
        value = str(item.get("expires_on", "")).strip()
        if value:
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass

        try:
            homework_date = date.fromisoformat(str(item.get("datum", "")))
            return homework_date + timedelta(days=RETENTION_DAYS)
        except ValueError:
            pass

        # Fallback for legacy/manual data without a valid homework date.
        try:
            created = datetime.fromisoformat(str(item.get("created_at", "")).replace("Z", "+00:00"))
            return created.date() + timedelta(days=RETENTION_DAYS)
        except ValueError:
            return None

    async def _async_save(self) -> None:
        await self._store.async_save({"items": self._items})
