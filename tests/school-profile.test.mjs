import test from 'node:test';
import assert from 'node:assert/strict';
import { schoolCard } from '../custom_components/sph/static/school-profile.js';

class Base {
  setConfig(config) {
    this.config = config;
    this.shadowRoot = { innerHTML: '' };
  }
  set hass(hass) {
    this._hass = hass;
    this.renders = (this.renders || 0) + 1;
  }
}

const timetable = {
  entity_id: 'sensor.stundenplan_kind_k',
  attributes: {
    kind: 'Kind',
    kind_kürzel: 'K',
    school_profile: 'kfg',
    eigener_plan: [[], [], [], [], []],
  },
};

const hass = {
  states: {
    [timetable.entity_id]: timetable,
    'sensor.kfg_kollegium': { attributes: { lehrer: {} } },
  },
};

test('card detects profile from configured SPH sensor', async () => {
  const Card = schoolCard(Base);
  const card = new Card();
  card.setConfig({ entity: timetable.entity_id });
  card.hass = hass;
  await card._schoolReady;

  assert.equal(card._schoolName, 'kfg');
  assert.equal(card._school.profile.gridWeekHeading, true);
  assert.equal(card.renders, 1);
});

test('explicit school-profile overrides sensor profile', async () => {
  const Card = schoolCard(Base);
  const card = new Card();
  card.setConfig({ entity: timetable.entity_id, 'school-profile': false });
  card.hass = hass;

  assert.equal(card._schoolName, null);
  assert.equal(card._school, null);
  assert.equal(card.renders, 1);
});

test('explicit school-profile selects a profile', async () => {
  const Card = schoolCard(Base);
  const card = new Card();
  card.setConfig({ entity: timetable.entity_id, 'school-profile': 'kfg' });
  card.hass = hass;
  await card._schoolReady;

  assert.equal(card._schoolName, 'kfg');
  assert.ok(card._school);
});
