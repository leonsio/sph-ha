import { schoolCard, schoolDays, schoolLesson, schoolHeading, schoolBadges, schoolClasses, schoolStyles } from "./school-hacks.js?v=0.4.22";
class SphStundenplanGridCard extends HTMLElement {
  setConfig(config) {
    this.config = config || {};
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    const hass = this._hass;
    if (!hass || !this.config || !this.shadowRoot) return;

    const entity = this._findEntity(hass);
    const attrs = entity?.attributes || {};
    const days = Array.isArray(attrs.eigener_plan) ? schoolDays(this, attrs.eigener_plan, attrs.wochenkennung).slice(0, 5) : [];
    const calendarEvents = this._calendarEvents(hass);
    const title = this.config.title || "";
    const header = title ? ` header="${this._esc(title)}"` : "";
    const names = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"];

    if (!entity) {
      this.shadowRoot.innerHTML = `<ha-card${header}><div class="error">Kein passender Stundenplan gefunden.</div></ha-card>`;
      return;
    }

    const maxPeriod = Math.max(8, ...days.flatMap(day =>
      (Array.isArray(day) ? day : []).map(lesson => this._periodEnd(lesson))
    ));
    const slots = this._buildSlots(days, maxPeriod);
    const table = this._renderTable(days, names, slots, calendarEvents);

    // Keep the scroll container itself. Replacing it on every Home Assistant
    // state update resets scrollLeft and makes horizontal scrolling jump back
    // to the left on narrow screens.
    const existingWrap = this.shadowRoot.querySelector(".table-wrap");
    if (existingWrap) {
      existingWrap.innerHTML = table;
      return;
    }

    this.shadowRoot.innerHTML = `
      <style>${schoolStyles}
        :host { display:block; width:100%; box-sizing:border-box; }
        ha-card { width:100%; overflow:hidden; }
        .table-wrap { width:100%; overflow-x:auto; }
        table { width:100%; min-width:900px; border-collapse:collapse; table-layout:fixed; }
        th,td { border:1px solid var(--divider-color); text-align:center; vertical-align:middle; box-sizing:border-box; }
        thead th { background:var(--secondary-background-color); font-size:1.05rem; font-weight:700; padding:9px 6px; }
        thead th:first-child,tbody th { width:15%; }
        tbody th { padding:7px 4px; background:var(--secondary-background-color); font-weight:700; }
        .period { display:block; font-size:1rem; }
        .slot-time { display:block; margin-top:4px; font-size:.82rem; font-weight:400; white-space:nowrap; }
        td { padding:8px 6px; }
        .lesson { display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:52px; line-height:1.25; }
        .lessons { display:flex; flex-direction:column; gap:7px; width:100%; }
        .subject { font-size:1.05rem; font-weight:700; }
        .teacher { margin-top:3px; font-size:.9rem; color:var(--secondary-text-color); }
        .badge { display:inline-block; margin-left:4px; padding:1px 6px; border-radius:999px; background:var(--primary-color); color:var(--text-primary-color); font-size:.75rem; font-weight:700; }
        .calendar-event { display:inline-block; margin-top:5px; padding:3px 7px; border-radius:6px; font-size:.74rem; font-weight:700; line-height:1.2; max-width:100%; box-sizing:border-box; }
        .calendar-arbeiten { background:var(--warning-color, #ff9800); color:#fff; }
        .calendar-klausuren { background:var(--error-color, #e53935); color:#fff; }
        .empty { color:var(--secondary-text-color); }
        .error { padding:16px; color:var(--error-color); }
        @media (max-width:700px) { table{min-width:760px}.subject{font-size:.95rem} }
      </style>
      <ha-card${header}><div class="table-wrap">${table}</div></ha-card>`;
  }

  _renderTable(days, names, slots, calendarEvents) {
    const covered = Array.from({ length:5 }, () => new Set());
    const monday = this._monday(new Date());
    let html = "<table><thead><tr><th>Stunde</th>";
    names.forEach((name, i) => { const date = new Date(monday); date.setDate(date.getDate() + i); html += `<th>${this._esc(name)}${schoolHeading(this, date)}</th>`; });
    html += "</tr></thead><tbody>";

    for (const slot of slots) {
      html += "<tr>";
      html += `<th><span class="period">${slot.index}.</span><span class="slot-time">${this._esc(slot.start || "")}${slot.end ? ` – ${this._esc(slot.end)}` : ""}</span></th>`;
      for (let dayIndex=0; dayIndex<5; dayIndex++) {
        if (covered[dayIndex].has(slot.index)) continue;
        const lessons = this._lessonsAt(days[dayIndex], slot.index);
        const span = this._spanFor(lessons, slot.index);
        for (let p=slot.index+1; p<slot.index+span; p++) covered[dayIndex].add(p);
        const date = new Date(monday);
        date.setDate(date.getDate() + dayIndex);
        html += `<td${span>1 ? ` rowspan="${span}"` : ""}>${lessons.length ? this._renderLessons(lessons, date, calendarEvents) : '<span class="empty">–</span>'}</td>`;
      }
      html += "</tr>";
    }
    return html + "</tbody></table>";
  }

  _renderLessons(lessons, date, calendarEvents) {
    return `<div class="lessons">${lessons.map(rawLesson => {
      const lesson = schoolLesson(this, rawLesson, date);
      const events = this._calendarEventsForLesson(calendarEvents, date, lesson);
      return `<div class="lesson${schoolClasses(lesson)}"><div class="subject">${this._esc(lesson.displaySubject || lesson.fach || lesson.subject || "Unterricht")}${this._renderBadge(lesson.badge)}</div>${schoolBadges(lesson)}${events.map(event => `<span class="calendar-event ${event.cssClass}">${this._esc(event.summary)}</span>`).join("")}<div class="teacher">${this._esc(lesson.displayTeacher || lesson.teacher || "")}${lesson.room ? ` <span>· Raum: ${this._esc(lesson.room)}</span>` : ""}</div></div>`;
    }).join("")}</div>`;
  }

  _calendarEvents(hass) {
    const entity = hass.states["sensor.schulkalender_maxim_mk"] || Object.values(hass.states).find(state => state.entity_id.startsWith("sensor.schulkalender_") && Array.isArray(state.attributes?.termine));
    const events = entity?.attributes?.termine;
    if (!Array.isArray(events)) return [];
    return events.filter(event => ["arbeiten", "klausuren"].includes(this._norm(event.art)));
  }

  _calendarEventsForLesson(events, date, lesson) {
    return events.filter(event => {
      if (!this._eventOnDate(event, date)) return false;
      const summary = this._norm(event.summary);
      const subjects = [lesson.subject, lesson.fach].filter(Boolean).map(value => this._norm(value));
      const subjectMatch = subjects.some(subject => subject && (summary.includes(subject) || this._subjectWordsMatch(summary, subject)));
      if (subjectMatch) return true;
      if (event.all_day || !lesson.start || !lesson.end) return false;
      return this._eventOverlapsLesson(event, lesson);
    });
  }

  _subjectWordsMatch(summary, subject) {
    const words = String(subject).split(/\s+/).map(word => this._norm(word)).filter(word => word.length >= 2);
    return words.length > 0 && words.every(word => summary.includes(word));
  }

  _eventOnDate(event, date) {
    const start = this._dateValue(event.start), end = this._dateValue(event.end || event.start);
    if (!start) return false;
    const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const dayEnd = new Date(dayStart); dayEnd.setDate(dayEnd.getDate() + 1);
    return start < dayEnd && (end ? end > dayStart : start >= dayStart && start < dayEnd);
  }

  _eventOverlapsLesson(event, lesson) {
    const start = this._dateValue(event.start), end = this._dateValue(event.end || event.start);
    if (!start || !lesson.start || !lesson.end) return false;
    const lessonStart = this._timeToMinutes(lesson.start), lessonEnd = this._timeToMinutes(lesson.end);
    if (lessonStart === null || lessonEnd === null) return false;
    const eventStart = start.getHours() * 60 + start.getMinutes();
    const eventEnd = end ? end.getHours() * 60 + end.getMinutes() : eventStart;
    return eventStart < lessonEnd && eventEnd > lessonStart;
  }

  _dateValue(value) {
    if (!value) return null;
    const date = new Date(String(value));
    return Number.isNaN(date.getTime()) ? null : date;
  }

  _renderBadge(value) {
    if (value === null || value === undefined || value === "") return "";
    const values = Array.isArray(value) ? value : String(value).split(/[,;/|]+/).map(x => x.trim()).filter(Boolean);
    return values.map(value => `<span class="badge">${this._esc(value)}</span>`).join("");
  }

  _lessonsAt(day, period) {
    return (Array.isArray(day) ? day : []).filter(lesson => {
      const index = Number(lesson?.index), duration = Math.max(1, Number(lesson?.duration) || 1);
      return Number.isFinite(index) && index <= period && period < index + duration;
    });
  }

  _spanFor(lessons, period) {
    const starting = lessons.filter(lesson => Number(lesson?.index) === period);
    return starting.length ? Math.max(1, ...starting.map(lesson => Number(lesson.duration) || 1)) : 1;
  }

  _periodEnd(lesson) {
    const index = Number(lesson?.index), duration = Math.max(1, Number(lesson?.duration) || 1);
    return Number.isFinite(index) ? index + duration - 1 : 1;
  }

  _buildSlots(days, maxPeriod) {
    const byPeriod = new Map();
    for (const day of days) for (const lesson of Array.isArray(day) ? day : []) {
      const index = Number(lesson?.index), duration = Math.max(1, Number(lesson?.duration) || 1);
      if (!Number.isFinite(index)) continue;
      const start = this._timeToMinutes(lesson.start), end = this._timeToMinutes(lesson.end);
      if (start !== null && end !== null && duration > 1) {
        const length = (end - start) / duration;
        for (let offset=0; offset<duration; offset++) {
          const period=index+offset;
          if (!byPeriod.has(period)) byPeriod.set(period,{start:this._minutesToTime(start+length*offset),end:this._minutesToTime(start+length*(offset+1))});
        }
      } else if (!byPeriod.has(index)) byPeriod.set(index,{start:lesson.start||"",end:lesson.end||""});
    }
    const slots=[];
    for (let index=1; index<=maxPeriod; index++) {
      const current=byPeriod.get(index)||{start:"",end:""};
      slots.push({index,start:current.start,end:current.end});
    }
    return slots;
  }

  _timeToMinutes(value) {
    if (typeof value !== "string") return null;
    const match=value.trim().match(/^(\d{1,2}):(\d{2})/);
    if (!match) return null;
    return Number(match[1])*60+Number(match[2]);
  }

  _minutesToTime(value) {
    const minutes=Math.round(value);
    return `${String(Math.floor(minutes/60)).padStart(2,"0")}:${String(minutes%60).padStart(2,"0")}`;
  }

  _monday(date) { const result = new Date(date.getFullYear(), date.getMonth(), date.getDate()); const day = result.getDay(); result.setDate(result.getDate() + (day === 0 ? -6 : 1 - day)); return result; }
  _norm(value) { return String(value ?? "").trim().toLowerCase().replace(/ä/g,"a").replace(/ö/g,"o").replace(/ü/g,"u").replace(/ß/g,"ss").replace(/[^a-z0-9]+/g,""); }

  _findEntity(hass) {
    const configured=this.config.sensor||this.config.entity;
    if (configured&&hass.states[configured]) return hass.states[configured];
    if (!this.config.child) return hass.states["sensor.stundenplan"];
    const wanted=String(this.config.child).toLowerCase();
    return Object.values(hass.states).find(state=>state.entity_id.startsWith("sensor.")&&state.attributes?.kind_kürzel?.toString().toLowerCase()===wanted);
  }

  _esc(value) { const div=document.createElement("div"); div.textContent=String(value??""); return div.innerHTML; }
  getCardSize() { return 10; }
  getGridOptions() { return { columns:"full", min_columns:12, rows:8, min_rows:5 }; }
}

if (!customElements.get("sph-stundenplan-grid-card")) customElements.define("sph-stundenplan-grid-card",schoolCard(SphStundenplanGridCard));
window.customCards=window.customCards||[];
if (!window.customCards.some(card=>card.type==="sph-stundenplan-grid-card")) window.customCards.push({type:"sph-stundenplan-grid-card",name:"SPH Stundenplan Raster",description:"Breiter Wochenstundenplan im Rasterformat"});
