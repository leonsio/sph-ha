"""Offline tests for the Nachrichten client (request shape, decryption, re-login).

Runs without requests/pycryptodome/Home Assistant: the client module is
loaded with its package imports replaced, like the other parser tests.
"""

from __future__ import annotations

import base64
import importlib.util
import json
import pathlib
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "sph" / "module" / "nachrichten"

_spec = importlib.util.spec_from_file_location("sph_nachrichten_parser", BASE / "parser.py")
parser = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parser)


def _load_client():
    source = (BASE / "client.py").read_text(encoding="utf-8")
    source = source.replace("from ...api.client import SphAuthClient", "SphAuthClient = object")
    source = source.replace(
        "from ...const import SPH_NACHRICHTEN_URL",
        'SPH_NACHRICHTEN_URL = "https://start.schulportal.hessen.de/nachrichten.php"',
    )
    source = source.replace("from .parser import parse_headers", "parse_headers = _parse_headers")
    namespace = {"__name__": "sph_nachrichten_client", "_parse_headers": parser.parse_headers}
    exec(compile(source, str(BASE / "client.py"), "exec"), namespace)
    return namespace["SphNachrichtenClient"]


SphNachrichtenClient = _load_client()

ROWS = [
    {"Uniquid": "u1", "Betreff": "Hallo", "SenderName": "Muster, Erika", "DatumUnix": 200, "unread": 1},
    {"Uniquid": "u2", "Betreff": "Alt", "SenderName": "Beispiel, Max", "DatumUnix": 100, "unread": 0},
]


class FakeHTTPError(Exception):
    """Like requests.HTTPError: not a RuntimeError."""


class FakeResponse:
    def __init__(self, payload=None, text=None, status=200):
        self._payload = payload
        self.status_code = status
        self.content = (text if text is not None else json.dumps(payload)).encode()

    def raise_for_status(self):
        if self.status_code >= 400:
            raise FakeHTTPError(f"HTTP {self.status_code}")

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.posts = []

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return self.responses.pop(0)


class FakeAuth:
    """Stands in for SphAuthClient; 'encryption' is a reversible prefix."""

    def __init__(self, responses):
        self.session = FakeSession(responses)
        self.key = b"k"
        self.logins = []

    def login(self, force=False):
        self.logins.append(force)

    def decrypt_base64(self, text):
        payload = base64.b64decode(text)
        return payload[len(b"enc:"):] if payload.startswith(b"enc:") else None


def encrypted(rows):
    return {"total": len(rows), "rows": base64.b64encode(b"enc:" + json.dumps(rows).encode()).decode()}


class ClientTest(unittest.TestCase):
    def test_fetches_visible_inbox_and_parses(self):
        auth = FakeAuth([FakeResponse(encrypted(ROWS))])
        items = SphNachrichtenClient(auth).get_inbox()

        [(url, kwargs)] = auth.session.posts
        self.assertTrue(url.endswith("/nachrichten.php"))
        self.assertEqual(kwargs["data"], {"a": "headers", "getType": "visibleOnly", "last": "0"})
        self.assertEqual(kwargs["headers"]["X-Requested-With"], "XMLHttpRequest")
        self.assertEqual([item["id"] for item in items], ["u1", "u2"])
        self.assertEqual([item["ungelesen"] for item in items], [True, False])
        self.assertEqual(auth.logins, [False])

    def test_relogin_once_when_session_returns_html(self):
        auth = FakeAuth([FakeResponse(text="<html>login</html>"), FakeResponse(encrypted(ROWS))])
        items = SphNachrichtenClient(auth).get_inbox()
        self.assertEqual(len(items), 2)
        self.assertEqual(auth.logins, [False, True])

    def test_relogin_once_after_http_error(self):
        auth = FakeAuth([FakeResponse(status=403, text="forbidden"), FakeResponse(encrypted(ROWS))])
        self.assertEqual(len(SphNachrichtenClient(auth).get_inbox()), 2)
        self.assertEqual(auth.logins, [False, True])

    def test_raises_after_second_failure(self):
        auth = FakeAuth([FakeResponse({"total": 0}), FakeResponse({"total": 0})])
        with self.assertRaises(RuntimeError):
            SphNachrichtenClient(auth).get_inbox()
        self.assertEqual(auth.logins, [False, True])

    def test_undecryptable_rows_raise(self):
        bad = {"total": 1, "rows": base64.b64encode(b"garbage").decode()}
        auth = FakeAuth([FakeResponse(bad), FakeResponse(bad)])
        with self.assertRaisesRegex(RuntimeError, "entschlüsselt"):
            SphNachrichtenClient(auth).get_inbox()


if __name__ == "__main__":
    unittest.main()
