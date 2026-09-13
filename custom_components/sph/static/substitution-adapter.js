import { escapeHtml, schoolLesson, schoolNews, schoolTeacher } from "./school-hacks.js?v=0.4.24";

const norm = value => String(value ?? "")
  .trim()
  .toLowerCase()
  .replace(/ä/g, "a")
  .replace(/ö/g, "o")
  .replace(/ü/g, "u")
  .replace(/ß/g, "ss")
  .replace(/[^a-z0-9]+/g, "");

const dateKey = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
const explicitSchoolSource = card => card?.config?.vertretungsplan_sensor ?? card?.config?.vertretungsplan ?? card?.config?.substitution_sensor;

function timetableState(card, hass) {
  if (!hass) return null;
  if (card?._school?.timetable) return card._school.timetable(hass);
  const config = card?.config || {};
  const explicit = config.sensor || config.entity;
  if (explicit && Array.isArray(hass.states?.[explicit]?.attributes?.eigener_plan)) return hass.states[explicit];
  const wanted = norm(config.child);
  const candidates = Object.values(hass.states || {}).filter(state =>
    state.entity_id?.startsWith("sensor.stundenplan_") && Array.isArray(state.attributes?.eigener_plan)
  );
  if (wanted) {
    const match = candidates.find(state =>
      norm(state.attributes?.kind_kürzel) === wanted || norm(state.attributes?.kind) === wanted
    );
    if (match) return match;
  }
  return candidates[0] || null;
}

export function sphSubstitutionState(card, hass) {
  if (!hass) return null;
  const timetable = timetableState(card, hass);
  const attrs = timetable?.attributes || {};
  const wantedShortcut = norm(attrs.kind_kürzel || card?.config?.child);
  const wantedName = norm(attrs.kind);
  const candidates = Object.values(hass.states || {}).filter(state =>
    state.entity_id?.startsWith("sensor.vertretungsplan_") &&
    !state.entity_id.endsWith("_json") &&
    Array.isArray(state.attributes?.tage) &&
    (state.attributes?.kind_kürzel || state.attributes?.kind)
  );
  const exact = candidates.find(state =>
    (wantedShortcut && norm(state.attributes?.kind_kürzel) === wantedShortcut) ||
    (wantedName && norm(state.attributes?.kind) === wantedName)
  );
  return exact || (candidates.length === 1 ? candidates[0] : null);
}

function internalEntries(state, date) {
  const wanted = dateKey(date);
  const day = (state?.attributes?.tage || []).find(item => String(item?.datum || "") === wanted);
  if (!day) return [];
  return (Array.isArray(day.eintraege) ? day.eintraege : []).map(entry => ({ ...entry, datum: entry.datum || day.datum }));
}

function lessonPeriods(lesson) {
  const start = Number(lesson?.index);
  if (!Number.isFinite(start)) return [];
  const duration = Math.max(1, Number(lesson?.duration) || 1);
  return Array.from({ length: duration }, (_, index) => start + index);
}

function entryPeriods(entry) {
  if (Array.isArray(entry?.stunden)) return entry.stunden.map(Number).filter(Number.isFinite);
  const numbers = String(entry?.stunde || "").match(/\d+/g)?.map(Number).filter(number => number > 0 && number < 20) || [];
  if (numbers.length === 2 && /[-–—]/.test(String(entry?.stunde || ""))) {
    const [a, b] = numbers[0] <= numbers[1] ? numbers : [numbers[1], numbers[0]];
    return Array.from({ length: b - a + 1 }, (_, index) => a + index);
  }
  return numbers;
}

function classMatches(entry, childClass) {
  if (!entry?.klasse || !childClass) return true;
  const wanted = norm(childClass);
  return String(entry.klasse).split(/[,;/|]+/).some(value => norm(value) === wanted);
}

function subjectMatches(entry, lesson) {
  const original = entry?.fach_alt || entry?.fach_original || entry?.subject_original || entry?.fach || entry?.subject;
  if (!original) return true;
  const wanted = norm(original);
  return [lesson?.subject, lesson?.fach].filter(Boolean).some(value => norm(value) === wanted);
}

function findInternalEntry(card, rawLesson, date) {
  const hass = card?._hass;
  const state = sphSubstitutionState(card, hass);
  if (!state || !date) return null;
  const childClass = timetableState(card, hass)?.attributes?.klasse || "";
  const periods = new Set(lessonPeriods(rawLesson));
  return internalEntries(state, date).find(entry => {
    if (!classMatches(entry, childClass) || !subjectMatches(entry, rawLesson)) return false;
    const values = entryPeriods(entry);
    return !periods.size || !values.length || values.some(value => periods.has(value));
  }) || null;
}

function resolveSubject(card, code, fallback) {
  if (!code) return fallback;
  const aliases = timetableState(card, card?._hass)?.attributes?.eigener_plan?.flat?.().filter(Boolean) || [];
  const match = aliases.find(lesson => norm(lesson.subject) === norm(code) || norm(lesson.fach) === norm(code));
  return match?.fach || code;
}

function className(value) {
  return String(value || "").toLowerCase()
    .replace(/ä/g, "a").replace(/ö/g, "o").replace(/ü/g, "u").replace(/ß/g, "ss")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function applyInternal(card, adjustedLesson, rawLesson, date) {
  const entry = findInternalEntry(card, rawLesson, date);
  if (!entry) return adjustedLesson;

  const rawLabel = String(entry.art_lang || entry.art || "Vertretung").trim() || "Vertretung";
  const cancelled = Boolean(entry.entfall) || /entfall|ausfall|freistunde|freisetzung/i.test(rawLabel);
  const newCode = entry.fach || entry.subject || rawLesson.subject;
  const oldCode = entry.fach_alt || entry.fach_original || entry.subject_original || rawLesson.subject;
  const changed = !cancelled && newCode && oldCode && norm(newCode) !== norm(oldCode);
  const baseSubject = adjustedLesson.displaySubject || adjustedLesson.fach || adjustedLesson.subject || "Unterricht";
  const displaySubject = cancelled
    ? baseSubject
    : (entry.fach_lang || resolveSubject(card, newCode, baseSubject));
  const replacementTeacher = entry.vertreter || entry.lehrer_nach || entry.lehrer || entry.teacher;
  const displayTeacher = replacementTeacher
    ? (card?._school ? schoolTeacher(card, replacementTeacher) : replacementTeacher)
    : (adjustedLesson.displayTeacher || adjustedLesson.teacher || "");
  const changeLabel = changed ? "Fachwechsel" : rawLabel;

  return {
    ...adjustedLesson,
    displaySubject,
    originalSubject: changed ? baseSubject : (adjustedLesson.originalSubject || ""),
    displayTeacher,
    room: entry.raum || entry.room || adjustedLesson.room || rawLesson.room,
    cancelled,
    changeLabel,
    changeClass: `change-${className(changeLabel)}`,
    substitutionSource: "sph",
  };
}

function hasSchoolSubstitution(lesson) {
  return Boolean(lesson?.changeLabel || lesson?.cancelled || lesson?.originalSubject);
}

export function substitutionLesson(card, rawLesson, date) {
  const schoolAdjusted = card?._school
    ? schoolLesson(card, rawLesson, date)
    : { ...rawLesson, displaySubject: rawLesson?.fach || rawLesson?.subject || "Unterricht", displayTeacher: rawLesson?.teacher || "" };

  if (card?._school) {
    // Explicit per-card sources remain authoritative, including a deliberately
    // missing entity. Otherwise every school profile gets first chance and the
    // built-in SPH Vertretungsplan acts only as fallback.
    if (explicitSchoolSource(card) !== undefined || hasSchoolSubstitution(schoolAdjusted)) return schoolAdjusted;
  }
  return applyInternal(card, schoolAdjusted, rawLesson, date);
}

function internalNews(card, date) {
  const state = sphSubstitutionState(card, card?._hass);
  if (!state || !date) return [];
  const day = (state.attributes?.tage || []).find(item => String(item?.datum || "") === dateKey(date));
  return Array.isArray(day?.hinweise) ? day.hinweise.map(value => String(value).trim()).filter(Boolean) : [];
}

export function substitutionNews(card, date) {
  if (!date) return "";
  if (card?._school) {
    const preferred = schoolNews(card, date);
    if (preferred || explicitSchoolSource(card) !== undefined) return preferred;
  }
  const news = internalNews(card, date);
  return news.length
    ? `<div class="news"><div class="news-title">Nachricht des Tages</div>${news.map(value => `<div>${escapeHtml(value)}</div>`).join("")}</div>`
    : "";
}
