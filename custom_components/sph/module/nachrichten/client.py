from __future__ import annotations

import json
import logging

from ...api.client import SphAuthClient
from ...const import SPH_NACHRICHTEN_URL
from .parser import parse_headers

_LOGGER = logging.getLogger(__name__)

AJAX_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*",
}


class SphNachrichtenClient:
    """Read-only access to the SPH message inbox (nachrichten.php).

    Only ``a=headers`` is used. Opening a conversation (``a=read``) would
    presumably mark it as read in the portal and is therefore avoided.
    """

    def __init__(self, auth: SphAuthClient):
        self.auth = auth

    def get_inbox(self) -> list[dict]:
        """Fetch the visible inbox (not hidden conversations) as summaries."""
        for attempt in range(2):
            try:
                self.auth.login(force=attempt == 1)
                return parse_headers(self._fetch_rows("visibleOnly"))
            except Exception as err:
                if attempt == 0:
                    _LOGGER.warning(
                        "SPH: Nachrichten-Abruf fehlgeschlagen (%s); erneuere Anmeldung und versuche es erneut",
                        err,
                    )
                    continue
                raise
        return []

    def _fetch_rows(self, get_type: str):
        response = self.auth.session.post(
            SPH_NACHRICHTEN_URL,
            data={"a": "headers", "getType": get_type, "last": "0"},
            headers=AJAX_HEADERS,
            timeout=60,
        )
        _LOGGER.debug(
            "SPH: Nachrichten (%s) HTTP %s, Bytes=%s",
            get_type,
            response.status_code,
            len(response.content),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("rows"), str):
            raise RuntimeError("Unerwartete Antwort von nachrichten.php.")
        decrypted = self.auth.decrypt_base64(payload["rows"])
        if decrypted is None:
            raise RuntimeError("Nachrichten konnten nicht entschlüsselt werden.")
        rows = json.loads(decrypted.decode("utf-8"))
        if not isinstance(rows, list):
            raise RuntimeError("Nachrichtenliste hat ein unerwartetes Format.")
        return rows
