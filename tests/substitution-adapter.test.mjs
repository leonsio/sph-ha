import test from "node:test";
import assert from "node:assert/strict";

import { SchoolContext, selectSchoolWeek } from "../custom_components/sph/static/school-hacks.js";
import kfg from "../custom_components/sph/static/school-hacks/kfg.js";
import {
  sphSubstitutionState,
  substitutionLesson,
  substitutionNews,
} from "../custom_components/sph/static/substitution-adapter.js";

const lesson = {
  subject: "M",
  fach: "Mathematik",
  teacher: "HER",
  room: "101",
  index: 1,
  duration: 1,
  start: "07:55",
  end: "08:40",
};

function makeHass() {
  const timetable = {
    entity_id: "sensor.stundenplan_maxim_mk",
    attributes: {
      kind: "Maxim",
      kind_kürzel: "Mk",
      klasse: "7n",
      wochenkennung: "A",
      wochenbeginn: "2026-09-07",
      eigener_plan: [[lesson]],
    },
  };
  const states = {
    [timetable.entity_id]: timetable,
    "sensor.vertretungsplan_maxim_mk": {
      entity_id: "sensor.vertretungsplan_maxim_mk",
      attributes: {
        kind: "Maxim",
        kind_kürzel: "Mk",
        tage: [{
          datum: "2026-09-07",
          hinweise: ["Interner Hinweis"],
          eintraege: [{
            klasse: "7n",
            stunde: "1",
            stunden: [1],
            fach: "M",
            fach_alt: "M",
            art: "Entf.",
            art_lang: "Entfall",
            entfall: true,
          }],
        }],
      },
    },
    "sensor.vertretungsplan_7n": {
      entity_id: "sensor.vertretungsplan_7n",
      attributes: {
        entries: [{
          klasse: "7n",
          datum: "2026-09-07",
          stunde: "1",
          fach_original: "M",
          fach: "E",
          vertreter: "DRG",
          art: "Vertr",
          raum: "202",
        }],
      },
    },
    "sensor.vertretungsplan": {
      entity_id: "sensor.vertretungsplan",
      attributes: { entries: [] },
    },
    "sensor.kfg_kollegium": {
      entity_id: "sensor.kfg_kollegium",
      attributes: { lehrer: { HER: "Herr Beispiel", DRG: "Frau Vertretung", Fra: "Fra" } },
    },
  };
  return { states, config: { time_zone: "Europe/Berlin" } };
}

function makeCard(hass, config = {}) {
  return {
    config: {
      entity: "sensor.stundenplan_maxim_mk",
      type: "custom:sph-stundenplan-card",
      ...config,
    },
    _hass: hass,
  };
}

const date = new Date(2026, 8, 7, 8, 0, 0);

test("normal SPH cards use the internal child substitution sensor", () => {
  const hass = makeHass();
  const card = makeCard(hass);
  assert.equal(sphSubstitutionState(card, hass)?.entity_id, "sensor.vertretungsplan_maxim_mk");
  const result = substitutionLesson(card, lesson, date);
  assert.equal(result.cancelled, true);
  assert.equal(result.changeLabel, "Entfall");
  assert.equal(result.substitutionSource, "sph");
  assert.match(substitutionNews(card, date), /Interner Hinweis/);
});

test("generic week view applies Friday 18.09 teacher substitution from internal SPH plan", () => {
  const hass = makeHass();
  const timetable = hass.states["sensor.stundenplan_maxim_mk"].attributes;
  const fridayLesson = {
    subject: "M",
    fach: "Mathematik",
    teacher: "Bär",
    room: "153",
    index: 1,
    duration: 2,
    start: "07:55",
    end: "09:25",
  };
  timetable.eigener_grundplan = [[], [], [], [], [fridayLesson]];
  timetable.eigener_plan = [[], [], [], [], [fridayLesson]];
  hass.states["sensor.vertretungsplan_maxim_mk"].attributes.tage = [{
    datum: "2026-09-18",
    eintraege: [{
      stunde: "1 - 2",
      klasse: "7n",
      klasse_alt: "",
      vertreter: "Fra",
      lehrer: "",
      art: "",
      fach: "M",
      fach_alt: "",
      raum: "153",
      raum_alt: "",
      hinweis: "",
      stunden: [1, 2],
      von_stunde: 1,
      bis_stunde: 2,
      art_lang: "",
      entfall: false,
      fach_lang: "Mathematik",
    }],
    hinweise: [],
  }];

  const view = selectSchoolWeek(timetable, undefined, new Date(2026, 8, 13, 12, 0, 0));
  assert.equal(view.monday.getFullYear(), 2026);
  assert.equal(view.monday.getMonth(), 8);
  assert.equal(view.monday.getDate(), 14);

  const friday = new Date(view.monday);
  friday.setDate(friday.getDate() + 4);
  const result = substitutionLesson(makeCard(hass), view.days[4][0], friday);
  assert.equal(result.displayTeacher, "Fra");
  assert.equal(result.changeLabel, "Vertretung");
  assert.equal(result.room, "153");
  assert.equal(result.substitutionSource, "sph");
});

test("unique class and period entry is used when SPH subject labels differ", () => {
  const hass = makeHass();
  hass.states["sensor.vertretungsplan_maxim_mk"].attributes.tage = [{
    datum: "2026-09-07",
    eintraege: [{
      klasse: "7n",
      stunden: [1],
      fach: "X",
      vertreter: "Fra",
      art: "",
      art_lang: "",
      entfall: false,
    }],
  }];
  const result = substitutionLesson(makeCard(hass), lesson, date);
  assert.equal(result.displayTeacher, "Fra");
  assert.equal(result.changeLabel, "Fachwechsel");
  assert.equal(result.substitutionSource, "sph");
});

test("KFG school hack keeps its external source as first priority", () => {
  const hass = makeHass();
  const card = makeCard(hass, { "school-hacks": "kfg" });
  card._school = new SchoolContext(kfg, card);
  const result = substitutionLesson(card, lesson, date);
  assert.equal(result.cancelled, false);
  assert.equal(result.displaySubject, "E");
  assert.equal(result.displayTeacher, "Frau Vertretung");
  assert.equal(result.room, "202");
  assert.equal(result.changeLabel, "Fachwechsel");
  assert.notEqual(result.substitutionSource, "sph");
});

test("school hacks fall back to internal SPH substitutions when their source has no match", () => {
  const hass = makeHass();
  hass.states["sensor.vertretungsplan_7n"].attributes.entries = [];
  const card = makeCard(hass, { "school-hacks": "kfg" });
  card._school = new SchoolContext(kfg, card);
  const result = substitutionLesson(card, lesson, date);
  assert.equal(result.cancelled, true);
  assert.equal(result.substitutionSource, "sph");
});

test("explicit school substitution source remains authoritative even when missing", () => {
  const hass = makeHass();
  const card = makeCard(hass, {
    "school-hacks": "kfg",
    vertretungsplan_sensor: "sensor.does_not_exist",
  });
  card._school = new SchoolContext(kfg, card);
  const result = substitutionLesson(card, lesson, date);
  assert.equal(result.cancelled, undefined);
  assert.equal(result.changeLabel, undefined);
  assert.equal(result.substitutionSource, undefined);
});

test("future school profiles can define their own preferred class source", () => {
  const hass = makeHass();
  hass.states["sensor.other_7n"] = {
    entity_id: "sensor.other_7n",
    attributes: {
      entries: [{
        klasse: "7n",
        datum: "2026-09-07",
        stunde: "1",
        fach_original: "M",
        fach: "M",
        art: "Raum",
        raum: "303",
      }],
    },
  };
  const profile = {
    substitution: {
      classPrefix: "sensor.other_",
      fallback: "sensor.other",
      labels: { Raum: "Raumänderung" },
    },
  };
  const card = makeCard(hass, { "school-hacks": "other" });
  card._school = new SchoolContext(profile, card);
  const result = substitutionLesson(card, lesson, date);
  assert.equal(result.room, "303");
  assert.equal(result.changeLabel, "Raumänderung");
  assert.notEqual(result.substitutionSource, "sph");
});
