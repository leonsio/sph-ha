"""Offline tests for the SPH Nachrichten parser and new-message detection."""

from __future__ import annotations

import importlib.util
import pathlib
import unittest

PARSER_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components" / "sph" / "module" / "nachrichten" / "parser.py"
)
_spec = importlib.util.spec_from_file_location("sph_nachrichten_parser", PARSER_PATH)
parser = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parser)


def _row(uid, unread=None, unix=1795423788, **extra):
    row = {
        "Id": "12345",
        "Uniquid": uid,
        "Sender": "67890",
        "Betreff": "Elternabend &amp; Termine",
        "Papierkorb": "nein",
        "private": 2,
        "WeitereEmpfaenger": "",
        "empf": ["<span>Viele</span>", "<span>Empfänger</span>"],
        "SenderName": "<i class='fa fa-user'></i> Muster, Erika <small>(Lehrkraft)</small>",
        "kuerzel": "MUS",
        "Datum": "heute 08:43",
        "DatumUnix": unix,
    }
    if unread is not None:
        row["unread"] = unread
    row.update(extra)
    return row


class ParseHeadersTest(unittest.TestCase):
    def test_extracts_clean_fields_and_drops_recipients(self):
        [item] = parser.parse_headers([_row("u1", unread=1)])
        self.assertEqual(item["id"], "u1")
        self.assertEqual(item["betreff"], "Elternabend & Termine")
        self.assertEqual(item["absender"], "Muster, Erika (Lehrkraft)")
        self.assertTrue(item["ungelesen"])
        self.assertEqual(item["datum"], "2026-11-23T08:49:48+00:00")
        self.assertNotIn("empf", item)

    def test_unread_flag_values(self):
        items = parser.parse_headers(
            [_row("a", unread=1), _row("b", unread=0), _row("c"), _row("d", unread="1")]
        )
        flags = {item["id"]: item["ungelesen"] for item in items}
        self.assertEqual(flags, {"a": True, "b": False, "c": False, "d": True})

    def test_sorted_newest_first(self):
        items = parser.parse_headers([_row("old", unix=100), _row("new", unix=200)])
        self.assertEqual([item["id"] for item in items], ["new", "old"])

    def test_skips_rows_without_id_and_falls_back(self):
        items = parser.parse_headers(
            [{"Betreff": "x"}, _row("u", Betreff="", SenderName="", DatumUnix="kaputt")]
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["betreff"], "(ohne Betreff)")
        self.assertEqual(items[0]["absender"], "MUS")
        self.assertEqual(items[0]["datum"], "")


class SummarizeNewTest(unittest.TestCase):
    def test_one_payload_for_all_new_messages_newest_first(self):
        items = parser.parse_headers(
            [_row("old", unread=1, unix=100, Betreff="Alt"), _row("new", unread=1, unix=200, Betreff="Neu")]
        )
        summary = parser.summarize_new(items)
        self.assertEqual(summary["anzahl"], 2)
        self.assertEqual(summary["betreff"], "Neu")
        self.assertEqual([entry["betreff"] for entry in summary["nachrichten"]], ["Neu", "Alt"])
        self.assertEqual(set(summary["nachrichten"][0]), {"absender", "betreff", "datum"})


class DetectNewTest(unittest.TestCase):
    def setUp(self):
        self.items = parser.parse_headers(
            [_row("known_unread", unread=1), _row("was_read", unread=1), _row("brand_new", unread=1), _row("read", unread=0)]
        )

    def test_first_poll_reports_nothing(self):
        self.assertEqual(parser.detect_new(None, self.items), [])

    def test_reports_unknown_and_read_to_unread(self):
        previous = {"known_unread": True, "was_read": False, "read": False}
        new_ids = {item["id"] for item in parser.detect_new(previous, self.items)}
        self.assertEqual(new_ids, {"was_read", "brand_new"})

    def test_unread_state_roundtrip(self):
        state = parser.unread_state(self.items)
        self.assertEqual(parser.detect_new(state, self.items), [])


if __name__ == "__main__":
    unittest.main()
