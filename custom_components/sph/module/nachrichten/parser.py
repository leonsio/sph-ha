"""Pure helpers for SPH messages (nachrichten.php). No Home Assistant imports."""
from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
import re

_TAG_RE = re.compile(r"<[^>]+>")


def clean_text(value) -> str:
    """Strip HTML tags/entities and collapse whitespace."""
    text = unescape(_TAG_RE.sub(" ", str(value or "")))
    return " ".join(text.split())


def _is_unread(value) -> bool:
    return str(value).strip() == "1"


def _timestamp(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_headers(rows) -> list[dict]:
    """Turn decrypted ``a=headers`` rows into compact message summaries.

    Only fields needed for display are kept. The recipient lists (``empf``,
    ``WeitereEmpfaenger``) are dropped on purpose: they are huge for
    school-wide mailings and contain other people's names.
    """
    items: list[dict] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        uid = str(row.get("Uniquid") or row.get("Id") or "").strip()
        if not uid:
            continue
        unix = _timestamp(row.get("DatumUnix"))
        datum = (
            datetime.fromtimestamp(unix, tz=timezone.utc).isoformat()
            if unix is not None
            else ""
        )
        items.append(
            {
                "id": uid,
                "betreff": clean_text(row.get("Betreff")) or "(ohne Betreff)",
                "absender": clean_text(row.get("SenderName")) or clean_text(row.get("kuerzel")),
                "datum": datum,
                "datum_text": clean_text(row.get("Datum")),
                "datum_unix": unix or 0,
                "ungelesen": _is_unread(row.get("unread")),
            }
        )
    items.sort(key=lambda item: item["datum_unix"], reverse=True)
    return items


def unread_state(items) -> dict[str, bool]:
    """Map message id -> unread flag, for change detection across polls."""
    return {item["id"]: bool(item["ungelesen"]) for item in items}


def summarize_new(items) -> dict:
    """Describe all new messages of one poll as a single event payload.

    Several messages found in one poll must not become several events in the
    same instant: Home Assistant would merge them into one state change.
    The newest message is exposed at top level for simple notifications.
    """
    newest = max(items, key=lambda item: item["datum_unix"])
    return {
        "anzahl": len(items),
        "absender": newest["absender"],
        "betreff": newest["betreff"],
        "datum": newest["datum"],
        "nachrichten": [
            {"absender": item["absender"], "betreff": item["betreff"], "datum": item["datum"]}
            for item in sorted(items, key=lambda item: item["datum_unix"], reverse=True)
        ],
    }


def detect_new(previous: dict[str, bool] | None, items) -> list[dict]:
    """Return messages that became unread since the previous poll.

    ``previous`` is ``None`` on the very first poll: then nothing counts as
    new, so existing unread messages do not fire events after installation.
    A message counts as new when it is unread and was either unknown before
    or known as read (e.g. a reply arrived in an existing conversation).
    """
    if previous is None:
        return []
    return [
        item
        for item in items
        if item["ungelesen"] and previous.get(item["id"]) is not True
    ]
