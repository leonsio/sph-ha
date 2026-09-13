// Shared, opt-in presentation adapter. Portal records and hass.states stay untouched.
const profiles = new Map();
export const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const badges = value => (Array.isArray(value) ? value : String(value ?? "").split(/[,;/|]+/)).map(x => String(x).trim().replace(/[()]/g, "").toUpperCase()).filter(Boolean);
export function filterDay(day, week, profile) {
  const lessons = Array.isArray(day) ? day : [];
  const wanted = String(week || "").trim().toUpperCase();
  if (!profile?.weekBadges?.includes(wanted)) return lessons;
  const weekBadges = lesson => badges(lesson.badge).filter(b => profile.weekBadges.includes(b));
  const slot = l => l.start || l.end ? `${l.start || ""}|${l.end || ""}` : `${l.index ?? ""}|${l.duration ?? 1}`;
  const matching = new Set(lessons.filter(l => weekBadges(l).includes(wanted)).map(slot));
  return lessons.filter(l => {
    const values = weekBadges(l);
    return values.length ? values.includes(wanted) : !(profile.unbadgedFallback && matching.has(slot(l)));
  });
}

// Calendar-day arithmetic avoids DST-dependent 167/169-hour week differences.
const mondayOf = date => {
  const result = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  result.setDate(result.getDate() - (result.getDay() + 6) % 7);
  return result;
};
const dateKey = date => `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,"0")}-${String(date.getDate()).padStart(2,"0")}`;
const civilDay = date => Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / 86400000;
const parseDate = value => {
  const match = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return null;
  const date = new Date(+match[1], +match[2]-1, +match[3]);
  return dateKey(date) === value ? date : null;
};
export const schoolNow = (card, instant = new Date()) => {
  const zone = card._hass?.config?.time_zone;
  if (!zone) return instant;
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-GB", {
    timeZone: zone, year:"numeric", month:"2-digit", day:"2-digit",
    hour:"2-digit", minute:"2-digit", second:"2-digit", hourCycle:"h23"
  }).formatToParts(instant).map(p => [p.type, p.value]));
  return new Date(+parts.year, +parts.month-1, +parts.day, +parts.hour, +parts.minute, +parts.second);
};
export function weekForDate(attrs, date, now = new Date()) {
  const badge = String(attrs.wochenkennung || "").trim().toUpperCase();
  if (!["A", "B"].includes(badge)) return badge;
  const anchor = mondayOf(parseDate(attrs.wochenbeginn) || now);
  const distance = Math.round((civilDay(mondayOf(date)) - civilDay(anchor)) / 7);
  return Math.abs(distance) % 2 ? (badge === "A" ? "B" : "A") : badge;
}
const planForDate = (attrs, date, profile, now) => {
  const source = Array.isArray(attrs.eigener_grundplan) ? attrs.eigener_grundplan : (Array.isArray(attrs.eigener_plan) ? attrs.eigener_plan : []);
  if ((attrs.freie_tage || []).includes(dateKey(date))) return [];
  return filterDay(source?.[(date.getDay()+6)%7], weekForDate(attrs,date,now), profile);
};
const endMinutes = value => {
  const match = String(value || "").trim().match(/^(\d{1,2}):(\d{2})$/);
  return match && +match[1] < 24 && +match[2] < 60 ? +match[1]*60 + +match[2] : null;
};
export function selectSchoolWeek(attrs, profile, now = new Date()) {
  const monday = mondayOf(now);
  if (profile?.advanceWeekAfterFriday) {
    const weekday = (now.getDay()+6)%7;
    const friday = new Date(monday); friday.setDate(friday.getDate()+4);
    const lessons = planForDate(attrs, friday, profile, now);
    const ends = lessons.map(l => endMinutes(l.end));
    // A free Friday switches at midnight. Unknown end times wait until Saturday.
    const finished = !lessons.length || (ends.every(end => end !== null) && now.getHours()*60+now.getMinutes() >= Math.max(...ends));
    if (weekday > 4 || (weekday === 4 && finished)) monday.setDate(monday.getDate()+7);
  }
  const week = weekForDate(attrs, monday, now);
  const days = profile?.advanceWeekAfterFriday ? Array.from({length:5}, (_, i) => {
    const date = new Date(monday); date.setDate(date.getDate()+i);
    return planForDate(attrs,date,profile,now);
  }) : (Array.isArray(attrs.eigener_plan) ? attrs.eigener_plan : []).map(day => filterDay(day,week,profile));
  return {monday, week, days};
}
export function selectSchoolDay(attrs, profile, now = new Date()) {
  for (let offset=0; offset<=7; offset++) {
    const date = new Date(now.getFullYear(),now.getMonth(),now.getDate()+offset);
    const index = (date.getDay()+6)%7;
    const lessons = planForDate(attrs,date,profile,now);
    if (index > 4 || !lessons.length) continue;
    const ends = lessons.map(l => endMinutes(l.end));
    if (offset === 0 && ends.every(end => end !== null) && now.getHours()*60+now.getMinutes() >= Math.max(...ends)) continue;
    return {date,index,lessons,week:weekForDate(attrs,date,now)};
  }
  return null;
}
export function visibleSchoolBadges(card, value) {
  const profile = card._school?.profile;
  if (!profile?.hideWeekBadges) return value;
  const values = Array.isArray(value) ? value : String(value ?? "").split(/[,;/|]+/);
  return values.filter(v => String(v ?? "").trim() && !badges(v).some(b => profile.weekBadges?.includes(b)));
}

export class SchoolContext {
  constructor(profile, card) { this.profile = profile; this.card = card; }
  timetable(hass) {
    const config = this.card.config || {};
    const explicit = config.sensor || config.entity;
    if (explicit && this.card.config.type?.includes("stundenplan")) return hass.states[explicit] || null;
    if (explicit && Array.isArray(hass.states[explicit]?.attributes?.eigener_plan)) return hass.states[explicit];
    return Object.values(hass.states).find(s => Array.isArray(s.attributes?.eigener_plan) && (!config.child || String(s.attributes.kind_kürzel || "").toLowerCase() === String(config.child).toLowerCase()));
  }
  substitution(hass) {
    const config = this.card.config || {};
    const explicit = config.vertretungsplan_sensor ?? config.vertretungsplan ?? config.substitution_sensor;
    if (explicit) return hass.states[explicit] || null;
    const settings = this.profile.substitution;
    if (!settings) return null;
    const cls = String(this.timetable(hass)?.attributes?.klasse || "").trim().toLowerCase().replace(/ä/g,"a").replace(/ö/g,"o").replace(/ü/g,"u").replace(/ß/g,"ss").replace(/[^a-z0-9_]+/g,"_").replace(/^_+|_+$/g, "");
    return (cls && hass.states[`${settings.classPrefix}${cls}`]) || hass.states[settings.fallback] || null;
  }
  teacher(value, hass) {
    const settings = this.profile.teachers;
    return this._teacher(value, hass?.states?.[settings?.entity]?.attributes?.[settings?.attribute] || {});
  }
  lesson(lesson, date, hass) {
    const base = { ...lesson, displaySubject: lesson.fach || lesson.subject || "Unterricht", displayTeacher: this.teacher(lesson.teacher, hass) };
    const attrs = this.timetable(hass)?.attributes || {};
    const entries = this._entries(this.substitution(hass)?.attributes || {});
    // Match the original subject code before resolving display names.
    const item = entries.find(i => this._class(i, attrs.klasse) && this._dateMatch(i, date, (date.getDay()+6)%7, parseDate(attrs.wochenbeginn) || schoolNow(this.card)) && this._period(i.stunde, lesson) && this._norm(i.fach_original || i.subject_original || i.fach || i.subject) === this._norm(lesson.subject));
    if (!item) return base;
    const art = String(item.art || "").trim();
    const label = this.profile.substitution?.labels?.[art] || art || "Vertretung";
    const cancelled = /entfall|ausfall|freistunde/i.test(label);
    const subject = item.fach || item.subject || lesson.subject;
    const original = item.fach_original || item.subject_original || lesson.subject;
    const changed = !cancelled && this._norm(subject) !== this._norm(original);
    const aliases = (attrs.eigener_plan || []).flat().filter(Boolean);
    const resolve = code => aliases.find(l => this._norm(l.subject) === this._norm(code))?.fach || code;
    const changeLabel = changed ? "Fachwechsel" : label;
    return { ...base, displaySubject: cancelled ? base.displaySubject : resolve(subject), originalSubject: changed ? resolve(original) : "", displayTeacher: this.teacher(item.vertreter || item.lehrer_nach || item.teacher || lesson.teacher, hass), room: item.raum || item.room || lesson.room, cancelled, changeLabel, changeClass: `change-${this._className(changeLabel)}` };
  }
  _entries(attributes) {
    const result = [], walk = value => { if (Array.isArray(value)) return value.forEach(walk); if (!value || typeof value !== "object") return; if (this._looksLikeEntry(value)) result.push(value); Object.values(value).forEach(walk); };
    walk(attributes); return result;
  }

  _looksLikeEntry(value) { return !!(value && (value.fach || value.fach_original || value.subject) && (value.stunde || value.datum || value.art || value.vertreter || value.lehrer_nach)); }

  _dateMatch(item, date, dayIndex, referenceDate = date) {
    if (!item?.datum) return false;
    const value = String(item.datum).trim().toLowerCase();
    const names = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"];
    const weekdayIndex = names.indexOf(value);
    if (weekdayIndex >= 0) return weekdayIndex === dayIndex && civilDay(mondayOf(date)) === civilDay(mondayOf(referenceDate));
    const iso = value.match(/^(\d{4})-(\d{2})-(\d{2})(?:$|T|\s)/i);
    if (iso) return +iso[1] === date.getFullYear() && +iso[2] === date.getMonth()+1 && +iso[3] === date.getDate();
    const match = value.match(/(\d{1,2})[.\/-](\d{1,2})(?:[.\/-](\d{2,4}))?/);
    if (!match) return false;
    if (Number(match[1]) !== date.getDate() || Number(match[2]) !== date.getMonth() + 1) return false;
    return !match[3] || Number(match[3]) === date.getFullYear() || Number(match[3]) === date.getFullYear() % 100;
  }

  _period(value, lesson) {
    if (!value || !lesson) return true;
    const numbers = String(value).match(/\d+/g)?.map(Number).filter(number => number > 0 && number < 20) || [], index = Number(lesson.index);
    if (!numbers.length || !Number.isFinite(index)) return true;
    if (numbers.length === 2 && /[-–—]/.test(String(value))) { const range = []; for (let number = numbers[0]; number <= numbers[1]; number++) range.push(number); return range.includes(index); }
    return numbers.includes(index);
  }

  _class(item, childClass) { if (!childClass || !item?.klasse) return false; const wanted = this._norm(childClass); return String(item.klasse).split(/[,;/|]+/).some(value => this._norm(value) === wanted); }

  _teacher(value, map) {
    if (!value) return "";
    const raw = String(value).trim(), wanted = raw.toLocaleLowerCase("de-DE");
    const key = Object.keys(map || {}).find(item => String(item).trim().toLocaleLowerCase("de-DE") === wanted);
    const name = key ? map[key] : raw;
    return typeof name === "string" ? name : raw;
  }

  _className(value) { return String(value || "").toLowerCase().replace(/ä/g, "a").replace(/ö/g, "o").replace(/ü/g, "u").replace(/ß/g, "ss").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }
  _norm(value) { return String(value ?? "").trim().toLowerCase().replace(/ä/g, "a").replace(/ö/g, "o").replace(/ü/g, "u").replace(/ß/g, "ss").replace(/[^a-z0-9]+/g, ""); }
  _monday(date) { const result = new Date(date.getFullYear(), date.getMonth(), date.getDate()), day = result.getDay(); result.setDate(result.getDate() + (day === 0 ? -6 : 1 - day)); return result; }
  _date(date) { return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" }).format(date); }

 _news(h,d){const a=this.substitution(h)?.attributes;if(!a)return[];const t={day:d.getDate(),month:d.getMonth()+1,weekday:d.getDay()},r=[],walk=v=>{if(Array.isArray(v))return v.forEach(walk);if(!v||typeof v!=='object')return;if(v.weekday&&v.date&&Array.isArray(v.news)&&this._newsDate(v.weekday,v.date,t))v.news.forEach(n=>{const x=Array.isArray(n)?n.flat(Infinity).join(' '):n;if(String(x).trim())r.push(String(x).trim())});Object.values(v).forEach(walk)};walk(a);return[...new Set(r)]}
 _newsDate(w,d,t){const n=['sonntag','montag','dienstag','mittwoch','donnerstag','freitag','samstag'],wd=n.indexOf(String(w).trim().toLowerCase()),m=String(d).match(/(\d{1,2})\s*[.\-/]\s*(\d{1,2})/);return(wd<0||wd===t.weekday)&&!!m&&+m[1]===t.day&&+m[2]===t.month}
 _newsHtml(a){return`<div class="news"><div class="news-title">Nachricht des Tages</div>${a.map(x=>`<div>${escapeHtml(x)}</div>`).join('')}</div>`}

}

export const schoolDays = (card, days, week) => card._school ? (days || []).map(day => filterDay(day, week, card._school.profile)) : days;
export const schoolLesson = (card, lesson, date) => card._school ? card._school.lesson(lesson, date, card._hass) : lesson;
export const schoolTeacher = (card, value) => card._school ? card._school.teacher(value, card._hass) : value;
// Calendar descriptions remain original data; resolve only labeled teacher lines
// when displaying the details, never in edit/service payloads.
export const schoolDescription = (card, value) => {
  if (!card._school) return value;
  const labels = card._school.profile.teachers?.descriptionLabels || [];
  return String(value || "").split("\n").map(line => {
    const match = line.match(/^(\s*([^:]+):\s*)(.*)$/);
    return match && labels.includes(match[2].trim().toLowerCase()) ? match[1] + schoolTeacher(card, match[3]) : line;
  }).join("\n");
};
export const schoolNews = (card, date) => {
  if (!card._school?.profile.substitution?.news || !date) return "";
  const news = card._school._news(card._hass, date);
  return news.length ? card._school._newsHtml(news) : "";
};
export const schoolHeading = (card, date, selectedWeek) => {
  if (!card._school) return "";
  const week = selectedWeek ?? weekForDate(card._school.timetable(card._hass)?.attributes || {}, date, schoolNow(card));
  return ` ${escapeHtml(new Intl.DateTimeFormat("de-DE").format(date))}${week ? ` · Woche ${escapeHtml(week)}` : ""}`;
};
export const schoolBadges = lesson => `${lesson.originalSubject ? `<small>statt ${escapeHtml(lesson.originalSubject)}</small>` : ""}${lesson.changeLabel ? `<span class="badge ${escapeHtml(lesson.changeClass)}">${escapeHtml(lesson.changeLabel)}</span>` : ""}`;
export const schoolClasses = lesson => lesson.cancelled ? " cancelled" : lesson.changeLabel ? ` changed ${escapeHtml(lesson.changeClass)}` : "";
export const schoolStyles = `.cancelled{text-decoration:line-through;opacity:.65}.changed{border-left:3px solid var(--warning-color,#ff9800);padding-left:7px}.badge.change-vertretung{background:var(--info-color,#2196f3);color:white}.badge.change-entfall{background:var(--error-color,#f44336);color:white}.badge.change-fachwechsel,.badge.change-tausch{background:var(--warning-color,#ff9800);color:white}.badge.change-betreuung{background:#4caf50;color:white}.badge.change-freistunde{background:#757575;color:white}.badge.change-raumanderung{background:#9c27b0;color:white}.news{padding:10px;margin-bottom:12px;border-left:4px solid var(--primary-color)}.news-title{font-weight:700}`;

// Register a single renderer per card type. Profile loading is shared and is
// independent of Lovelace resource order; stale async loads cannot win.
export function schoolCard(Base) {
  return class extends Base {
    connectedCallback() {
      super.connectedCallback?.();
      this._startSchoolClock();
    }
    disconnectedCallback() {
      super.disconnectedCallback?.();
      this._stopSchoolClock();
    }
    _stopSchoolClock() {
      if (this._schoolClock != null) window.clearInterval(this._schoolClock);
      this._schoolClock = null;
    }
    _startSchoolClock() {
      this._stopSchoolClock();
      if (Base.schoolWeekView && this.isConnected && this._school?.profile.advanceWeekAfterFriday) {
        this._schoolClockKey = null;
        this._schoolClock = window.setInterval(() => {
          if (!this._hass) return;
          const attrs = this._school.timetable(this._hass)?.attributes || {};
          const view = selectSchoolWeek(attrs,this._school.profile,schoolNow(this));
          const key = `${dateKey(view.monday)}|${view.week}`;
          if (key !== this._schoolClockKey) { this._schoolClockKey = key; this._render(); }
        }, 1000);
      }
    }
    setConfig(config) {
      const name = config?.["school-hacks"];
      if (name != null && name !== false && (typeof name !== "string" || !/^[a-z0-9][a-z0-9_-]*$/.test(name))) throw new Error("school-hacks muss ein Schulprofilname sein, z.B. kfg");
      super.setConfig(config);
      const generation = this._schoolGeneration = (this._schoolGeneration || 0) + 1;
      this._stopSchoolClock();
      this._school = null;
      this._schoolError = null;
      this._renderedEntity = null;
      this._schoolLoading = Boolean(name);
      if (!name) { if (this._schoolHass) this.hass = this._schoolHass; return; }
      if (!profiles.has(name)) profiles.set(name, import(`./school-hacks/${name}.js?v=0.4.23`).then(m => m.default).catch(error => { profiles.delete(name); throw error; }));
      this._schoolReady = profiles.get(name).then(profile => {
        if (generation !== this._schoolGeneration) return;
        this._school = new SchoolContext(profile, this);
        this._schoolLoading = false;
        this._startSchoolClock();
        if (this._schoolHass) this.hass = this._schoolHass;
      }, () => {
        if (generation !== this._schoolGeneration) return;
        this._schoolLoading = false;
        this._schoolError = `Schulprofil „${name}“ konnte nicht geladen werden.`;
        this._showSchoolError();
      });
    }
    _render(...args) {
      if (this._schoolLoading) return;
      if (this._schoolError) { this._showSchoolError(); return; }
      return super._render(...args);
    }
    _showSchoolError() {
      if (!this.shadowRoot) this.attachShadow({mode:"open"});
      this.shadowRoot.innerHTML = `<ha-card><p>${escapeHtml(this._schoolError)}</p></ha-card>`;
    }
    set hass(hass) {
      this._schoolHass = hass;
      if (this._schoolLoading) return;
      if (this._schoolError) { this._showSchoolError(); return; }
      const teachers = hass.states[this._school?.profile.teachers?.entity];
      if (teachers !== this._schoolTeachers) { this._renderedEntity = null; this._schoolTeachers = teachers; }
      super.hass = hass;
    }
  };
}
