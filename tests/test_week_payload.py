"""Check future-week data without a full HA installation."""
import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
import re


class WeekPayloadTest(unittest.TestCase):
    def test_holiday_mask_keeps_unmasked_personal_plan_and_badge_anchor(self):
        tree = ast.parse(Path('custom_components/sph/module/stundenplan/sensor.py').read_text())
        selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in
                    {'subject_name', 'enrich_days', '_mask_current_week_free_days', '_empty_days_like', 'timetable_payload'}]
        ns = dict(timedelta=timedelta, re=re, SUBJECT_NAMES={'M':'Mathematik'},
                  CONF_CHILD_NAME='child_name', CONF_CHILD_SHORTCUT='child_shortcut',
                  CONF_TIMETABLE_OUTPUT='timetable_output', DEFAULT_TIMETABLE_OUTPUT='own', TIMETABLE_OUTPUT_ALL='all',
                  dt_util=SimpleNamespace(now=lambda:datetime(2026,9,11,12,tzinfo=timezone.utc), get_time_zone=lambda _:timezone.utc))
        exec(compile(ast.Module(body=selected, type_ignores=[]), '<sensor>', 'exec'), ns)
        lesson = {'subject':'M', 'badge':'A', 'end':'13:10'}
        data = {'own':[[lesson] for _ in range(5)], 'all':[[] for _ in range(5)],
                'week_badge':'A', 'week_reference_date':'2026-09-07', 'free_days':['2026-09-07']}
        coordinator = SimpleNamespace(data=data, last_successful_data=data, hass=SimpleNamespace(config=SimpleNamespace(time_zone='UTC')))
        payload = ns['timetable_payload'](coordinator, SimpleNamespace(data={}))
        self.assertEqual(payload['eigener_plan'][0], [])
        self.assertEqual(payload['eigener_grundplan'][0][0]['fach'], 'Mathematik')
        self.assertEqual(payload['eigener_grundplan'][0][0]['badge'], 'A')
        self.assertEqual(payload['wochenbeginn'], '2026-09-07')
        self.assertEqual(payload['wochenkennung'], 'A')
        self.assertEqual(data['own'][0], [lesson])
        self.assertEqual(payload['tage'], [[],[],[],[],[]])
