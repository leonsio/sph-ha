from __future__ import annotations

import base64
import hashlib
import logging
import random
import re
from datetime import datetime, timedelta

import requests

from ..const import SPH_BASE, SPH_CONNECT, SPH_LOGIN

_LOGGER = logging.getLogger(__name__)


class SphClient:
    """Shared HTTP, authentication and encryption functionality for SPH modules."""

    def __init__(self, school_id, username, password):
        self.school_id = str(school_id)
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "Home Assistant Schulportal Hessen/0.3.3"
        self.key = None

    @staticmethod
    def _crypto():
        from Crypto.Cipher import AES, PKCS1_v1_5
        from Crypto.PublicKey import RSA
        from Crypto.Random import get_random_bytes
        from Crypto.Util.Padding import unpad
        return AES, PKCS1_v1_5, RSA, get_random_bytes, unpad

    @staticmethod
    def _kdf(salt, key):
        out, previous = b"", b""
        while len(out) < 48:
            previous = hashlib.md5(previous + key + salt).digest()
            out += previous
        return out[:48]

    @classmethod
    def _decrypt(cls, payload, key):
        AES, _, _, _, unpad = cls._crypto()
        if len(payload) < 16 or payload[:8] != b"Salted__":
            return None
        k = cls._kdf(payload[8:16], key)
        return unpad(
            AES.new(k[:32], AES.MODE_CBC, k[32:48]).decrypt(payload[16:]),
            AES.block_size,
        )

    def decrypt_base64(self, text: str) -> bytes | None:
        """Decrypt a base64 CryptoJS payload (e.g. AJAX ``rows``) with the session key."""
        if not self.key:
            return None
        return self._decrypt(base64.b64decode(text), self.key)

    def _decrypt_tags(self, html):
        if not self.key:
            return html

        def replace(match):
            try:
                data = self._decrypt(base64.b64decode(match.group(1)), self.key)
                return data.decode("utf-8") if data else ""
            except Exception:
                _LOGGER.debug("SPH: verschlüsselten Seitenbereich konnte nicht entschlüsseln", exc_info=True)
                return ""

        return re.sub(r"<encoded>(.*?)</encoded>", replace, html, flags=re.S)

    def _get_login_url(self):
        _LOGGER.debug("SPH: starte Login-Handshake für Schulnummer %s", self.school_id)
        response = self.session.post(
            f"{SPH_LOGIN}?i={self.school_id}",
            data={
                "user": f"{self.school_id}.{self.username}",
                "user2": self.username,
                "password": self.password,
            },
            allow_redirects=False,
            timeout=15,
        )
        _LOGGER.debug("SPH: Login-Request HTTP %s", response.status_code)
        if response.status_code == 503:
            raise RuntimeError("Schulportal Hessen ist nicht verfügbar.")
        if response.status_code not in (200, 301, 302, 303, 307, 308):
            raise RuntimeError(
                f"SPH-Anmeldung fehlgeschlagen (HTTP {response.status_code}). Zugangsdaten prüfen."
            )
        connect = self.session.head(SPH_CONNECT, allow_redirects=False, timeout=15)
        _LOGGER.debug(
            "SPH: connect.php HTTP %s, Location vorhanden=%s",
            connect.status_code,
            bool(connect.headers.get("Location")),
        )
        if connect.status_code in (401, 403):
            raise RuntimeError("SPH-Anmeldung fehlgeschlagen. Zugangsdaten prüfen.")
        login_url = connect.headers.get("Location")
        if not login_url:
            raise RuntimeError("SPH-Anmeldung konnte nicht abgeschlossen werden.")
        return login_url

    def _perform_login(self):
        login_url = self._get_login_url()
        response = self.session.get(login_url, allow_redirects=False, timeout=15)
        _LOGGER.debug(
            "SPH: Ziel der Login-Weiterleitung HTTP %s, URL=%s",
            response.status_code,
            login_url,
        )
        if response.status_code not in (200, 301, 302, 303, 307, 308):
            raise RuntimeError("SPH-Anmeldung konnte nicht abgeschlossen werden.")
        _LOGGER.debug("SPH: Login erfolgreich für Benutzer %s", self.username)
        self._handshake()

    def _handshake(self):
        _, PKCS1_v1_5, RSA, get_random_bytes, _ = self._crypto()
        response = self.session.post(
            f"{SPH_BASE}/ajax.php", params={"f": "rsaPublicKey"}, timeout=15
        )
        response.raise_for_status()
        public_key = RSA.import_key(response.json()["publickey"])
        self.key = get_random_bytes(46)
        encrypted = PKCS1_v1_5.new(public_key).encrypt(self.key)
        response = self.session.post(
            f"{SPH_BASE}/ajax.php",
            params={"f": "rsaHandshake", "s": random.randrange(2000)},
            data={"key": base64.b64encode(encrypted).decode()},
            timeout=15,
        )
        response.raise_for_status()
        challenge = base64.b64decode(response.json()["challenge"])
        if self._decrypt(challenge, self.key) != self.key:
            self.key = None
            raise RuntimeError("SPH RSA/AES-Handshake fehlgeschlagen.")


class SphAuthClient(SphClient):
    """Shared authenticated SPH session used by all module clients."""

    SESSION_MAX_AGE = timedelta(minutes=45)

    def __init__(self, school_id, username, password):
        super().__init__(school_id, username, password)
        self._logged_in = False
        self._authenticated_at: datetime | None = None

    def login(self, force=False):
        now = datetime.now()
        if (
            self._logged_in
            and self._authenticated_at is not None
            and not force
            and now - self._authenticated_at < self.SESSION_MAX_AGE
        ):
            _LOGGER.debug("SPH: verwende bestehende Login-Session für Benutzer %s", self.username)
            return

        self._logged_in = False
        self._authenticated_at = None
        self._perform_login()
        self._logged_in = True
        self._authenticated_at = datetime.now()

    def force_relogin(self):
        self._logged_in = False
        self._authenticated_at = None
        self.key = None
        self.login(force=True)

    def get(self, *args, **kwargs):
        """Perform a request after ensuring the shared session is authenticated."""
        self.login()
        return self.session.get(*args, **kwargs)

    def authenticated_session(self):
        self.login()
        return self.session
