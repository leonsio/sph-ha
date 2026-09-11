import { schoolCard, schoolDescription } from "./school-hacks.js?v=0.4.22";
class SphKalenderCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._calendars = [];
    this._eventsByEntity = new Map();
    this._unsubs = [];
    this._subscriptionKey = "";
    this._subscriptionGeneration = 0;
    this._disabledSources = new Set();
    this._view = "week";
    this._cursor = this._startOfDay(new Date());
    this._renderEvents = [];
  }

  static getStubConfig() {
    return { view: "week" };
  }

  setConfig(config) {
    const next = config || {};
    const view = String(next.view || "week").toLowerCase();
    if (!new Set(["day", "week", "month"]).has(view)) {
      throw new Error("view muss day, week oder month sein");
    }
    this.config = next;
    this._view = view;
    this._locale = String(next.locale || "de-DE");
    if (next.date) {
      const parsed = this._parseLocalDate(String(next.date));
      if (parsed) this._cursor = parsed;
    }
    this._subscriptionKey = "";
  }

  set hass(hass) {
    this._hass = hass;
    this._syncSubscriptions();
  }

  connectedCallback() {
    if (this._hass) this._syncSubscriptions();
  }

  disconnectedCallback() {
    this._stopSubscriptions();
    this._subscriptionKey = "";
  }

  _discoverCalendars() {
    if (!this._hass) return [];
    const configured = Array.isArray(this.config?.calendars) ? this.config.calendars : [];
    if (configured.length) {
      return configured
        .map((item) => {
          const spec = typeof item === "string" ? { entity: item } : (item || {});
          const entity = String(spec.entity || "").trim();
          const state = this._hass.states[entity];
          if (!entity || !state) return null;
          return {
            entity,
            name: String(spec.name || state.attributes?.friendly_name || entity),
            color: spec.color ? String(spec.color) : "",
            source: String(spec.source || this._sourceForEntity(entity)),
          };
        })
        .filter(Boolean);
    }

    const child = String(this.config?.child || "").trim().toLowerCase();
    const states = Object.values(this._hass.states).filter((state) => {
      if (!state?.entity_id?.startsWith("calendar.")) return false;
      if (state.state === "unavailable") return false;
      if (!child) return true;
      const text = `${state.entity_id} ${state.attributes?.friendly_name || ""}`.toLowerCase();
      return text.includes(child);
    });

    const combined = states.filter((state) => state.entity_id.startsWith("calendar.sph_"));
    const selected = combined.length
      ? combined
      : states.filter((state) =>
          state.entity_id.startsWith("calendar.schulkalender_") ||
          state.entity_id.startsWith("calendar.stundenplan_") ||
          state.entity_id.startsWith("calendar.lerngruppen_")
        );

    return selected.sort((a, b) => a.entity_id.localeCompare(b.entity_id)).map((state) => ({
      entity: state.entity_id,
      name: String(state.attributes?.friendly_name || state.entity_id),
      color: "",
      source: this._sourceForEntity(state.entity_id),
    }));
  }

  _sourceForEntity(entityId) {
    const id = String(entityId || "").toLowerCase();
    if (id.startsWith("calendar.stundenplan_")) return "stundenplan";
    if (id.startsWith("calendar.lerngruppen_")) return "lerngruppen";
    if (id.startsWith("calendar.schulkalender_")) return "schulkalender";
    if (id.startsWith("calendar.sph_")) return "sph";
    return id.replace(/^calendar\./, "") || "kalender";
  }

  _sourceForEvent(raw, entityId) {
    const entitySource = this._sourceForEntity(entityId);
    if (entitySource !== "sph") return entitySource;

    const uid = String(raw?.uid || "").toLowerCase();
    if (uid.startsWith("sph-kalender-manual-")) return "manuell";
    if (uid.startsWith("sph-stundenplan-") || uid.startsWith("sph-schulwoche-")) return "stundenplan";
    if (uid.startsWith("sph-lerngruppen-")) return "lerngruppen";

    const description = String(raw?.description || "").toLowerCase();
    if (description.includes("dauer:") || description.includes("stunden:")) {
      const summary = String(raw?.summary || "").toLowerCase();
      if (!uid.startsWith("sph-stundenplan-") && (summary.includes(":") || description.includes("dauer:"))) {
        return "lerngruppen";
      }
    }
    return "schulkalender";
  }

  _syncSubscriptions() {
    if (!this._hass || !this.isConnected) return;
    const calendars = this._discoverCalendars();
    const range = this._viewRange();
    const key = JSON.stringify({
      view: this._view,
      start: range.start.toISOString(),
      end: range.end.toISOString(),
      calendars: calendars.map((item) => item.entity),
    });

    this._calendars = calendars;
    if (key === this._subscriptionKey) {
      if (!this.shadowRoot?.querySelector("ha-card")) this._render();
      return;
    }

    this._subscriptionKey = key;
    this._stopSubscriptions();
    this._eventsByEntity = new Map(calendars.map((cal) => [cal.entity, []]));
    const generation = ++this._subscriptionGeneration;
    this._render();

    calendars.forEach((cal) => {
      const promise = this._hass.connection.subscribeMessage(
        (update) => {
          if (generation !== this._subscriptionGeneration) return;
          this._eventsByEntity.set(cal.entity, Array.isArray(update?.events) ? update.events : []);
          this._render();
        },
        {
          type: "calendar/event/subscribe",
          entity_id: cal.entity,
          start: range.start.toISOString(),
          end: range.end.toISOString(),
        }
      );
      Promise.resolve(promise)
        .then((unsub) => {
          if (typeof unsub !== "function") return;
          if (generation !== this._subscriptionGeneration) {
            unsub();
            return;
          }
          this._unsubs.push(unsub);
        })
        .catch((err) => console.error("SPH: Kalender-Subscription fehlgeschlagen", err));
    });
  }

  _stopSubscriptions() {
    this._subscriptionGeneration += 1;
    for (const unsub of this._unsubs.splice(0)) {
      try { unsub(); } catch (_err) { /* ignore stale subscriptions */ }
    }
  }

  _viewRange() {
    if (this._view === "day") {
      const start = this._startOfDay(this._cursor);
      return { start, end: this._addDays(start, 1) };
    }
    if (this._view === "week") {
      const start = this._startOfWeek(this._cursor);
      return { start, end: this._addDays(start, 7) };
    }
    const first = new Date(this._cursor.getFullYear(), this._cursor.getMonth(), 1);
    const last = new Date(this._cursor.getFullYear(), this._cursor.getMonth() + 1, 0);
    const start = this._startOfWeek(first);
    const end = this._addDays(this._startOfWeek(last), 7);
    return { start, end };
  }

  _visibleDays() {
    const range = this._viewRange();
    const days = [];
    for (let day = range.start; day < range.end; day = this._addDays(day, 1)) {
      days.push(day);
    }
    return days;
  }

  _normalizedEvents() {
    const result = [];
    for (const cal of this._calendars) {
      for (const raw of this._eventsByEntity.get(cal.entity) || []) {
        const normalized = this._normalizeEvent(raw, cal);
        if (normalized) result.push(normalized);
      }
    }
    return result
      .filter((event) => this._passesYamlFilters(event))
      .filter((event) => !this._disabledSources.has(event.source))
      .sort((a, b) => a.start - b.start || a.end - b.end || a.summary.localeCompare(b.summary));
  }

  _normalizeEvent(raw, cal) {
    const startValue = this._calendarDateValue(raw?.start);
    const endValue = this._calendarDateValue(raw?.end);
    if (!startValue || !endValue) return null;
    const allDay = /^\d{4}-\d{2}-\d{2}$/.test(startValue);
    const start = allDay ? this._parseLocalDate(startValue) : new Date(startValue);
    const end = allDay ? this._parseLocalDate(endValue) : new Date(endValue);
    if (!start || !end || Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;

    const source = this._sourceForEvent(raw, cal.entity);
    return {
      entity_id: cal.entity,
      calendar_name: cal.name,
      calendar_color: cal.color,
      source,
      color: this._colorFor(source, cal),
      uid: raw?.uid || "",
      recurrence_id: raw?.recurrence_id || "",
      rrule: raw?.rrule || "",
      summary: String(raw?.summary || "Termin"),
      description: String(raw?.description || ""),
      location: String(raw?.location || ""),
      start,
      end,
      allDay,
    };
  }

  _calendarDateValue(value) {
    if (typeof value === "string") return value;
    if (value && typeof value === "object") return value.dateTime || value.date || "";
    return "";
  }

  _passesYamlFilters(event) {
    const filters = this.config?.filters || {};
    const allowed = this._asArray(filters.calendars || filters.include_calendars);
    const blocked = this._asArray(filters.exclude_calendars);
    const identity = `${event.entity_id} ${event.calendar_name} ${event.source}`.toLowerCase();
    if (allowed.length && !allowed.some((term) => identity.includes(term.toLowerCase()))) return false;
    if (blocked.some((term) => identity.includes(term.toLowerCase()))) return false;

    const haystack = `${event.summary}\n${event.description}\n${event.location}\n${event.calendar_name}\n${event.source}`.toLowerCase();
    const include = this._asArray(filters.include);
    const exclude = this._asArray(filters.exclude);
    if (include.length && !include.some((term) => haystack.includes(term.toLowerCase()))) return false;
    if (exclude.some((term) => haystack.includes(term.toLowerCase()))) return false;
    return true;
  }

  _asArray(value) {
    if (Array.isArray(value)) return value.map((item) => String(item).trim()).filter(Boolean);
    if (value == null || value === "") return [];
    return [String(value).trim()].filter(Boolean);
  }

  _colorFor(source, cal) {
    const defaults = {
      schulkalender: "#ef6c00",
      stundenplan: "#1565c0",
      lerngruppen: "#7b1fa2",
      manuell: "#2e7d32",
      sph: "#00838f",
      kalender: "#546e7a",
    };
    const configured = this.config?.colors || {};
    return String(configured[source] || cal.color || defaults[source] || "#546e7a");
  }

  _sourceLabel(source) {
    const labels = {
      schulkalender: "Schulkalender",
      stundenplan: "Stundenplan",
      lerngruppen: "Lerngruppen",
      manuell: "Eigene Termine",
      sph: "SPH",
    };
    return labels[source] || source;
  }

  _render() {
    if (!this.shadowRoot || !this._hass) return;
    const events = this._normalizedEvents();
    this._renderEvents = events;
    this._eventIndexes = new Map(events.map((event, index) => [event, index]));
    const title = String(this.config?.title || "SPH Kalender");
    const sources = this._filterSources(events);
    const writable = this._writableCalendar();

    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <ha-card>
        <div class="card-header">
          <div class="title-row">
            <div class="title">${this._esc(title)}</div>
            <button class="primary add-event" type="button" ${writable ? "" : "disabled"}>+ Termin</button>
          </div>
          <div class="nav-row">
            <div class="nav-buttons">
              <button type="button" data-nav="prev" aria-label="Zurück">‹</button>
              <button type="button" data-nav="today">Heute</button>
              <button type="button" data-nav="next" aria-label="Weiter">›</button>
            </div>
            <div class="period">${this._esc(this._periodTitle())}</div>
            <div class="view-buttons">
              ${["day", "week", "month"].map((view) => `<button type="button" data-view="${view}" class="${this._view === view ? "active" : ""}">${view === "day" ? "Tag" : view === "week" ? "Woche" : "Monat"}</button>`).join("")}
            </div>
          </div>
          ${sources.length > 1 ? `<div class="filters">${sources.map((source) => {
            const disabled = this._disabledSources.has(source);
            const sample = events.find((event) => event.source === source);
            const color = sample?.color || this._colorFor(source, { color: "" });
            return `<button type="button" class="filter-chip ${disabled ? "off" : ""}" data-source="${this._esc(source)}" style="--chip-color:${this._esc(color)}"><span></span>${this._esc(this._sourceLabel(source))}</button>`;
          }).join("")}</div>` : ""}
        </div>
        <div class="calendar-body">
          ${this._calendars.length === 0
            ? `<div class="empty">Kein SPH-Kalender gefunden. Optional können Kalender über <code>calendars:</code> angegeben werden.</div>`
            : this._view === "month" ? this._renderMonth(events) : this._renderDayWeek(events)}
        </div>
        ${this._renderAddDialog()}
        ${this._renderDetailDialog()}
      </ha-card>`;

    this._bindInteractions();
  }

  _filterSources(events) {
    const set = new Set();
    for (const cal of this._calendars) {
      if (cal.source !== "sph") set.add(cal.source);
    }
    for (const event of events) set.add(event.source);
    for (const source of this._disabledSources) set.add(source);
    return [...set].sort((a, b) => this._sourceLabel(a).localeCompare(this._sourceLabel(b), this._locale));
  }

  _renderDayWeek(events) {
    const days = this._visibleDays();
    const minWidth = this._view === "week" ? "900px" : "560px";
    const bannerEvents = events.filter((event) => this._isBannerEvent(event));
    const timedEvents = events.filter((event) => !this._isBannerEvent(event));
    const banners = this._layoutBanners(bannerEvents, days);
    const lanes = Math.max(1, ...banners.map((item) => item.lane + 1));
    const bounds = this._timeBounds(timedEvents);
    const hourHeight = Math.max(36, Number(this.config?.hour_height || 52));
    const totalHeight = (bounds.end - bounds.start) * hourHeight;

    return `<div class="calendar-scroll"><div class="dayweek" style="min-width:${minWidth}">
      <div class="day-head-grid" style="grid-template-columns:64px repeat(${days.length},minmax(0,1fr))">
        <div></div>
        ${days.map((day) => `<div class="day-head ${this._isToday(day) ? "today" : ""}"><span>${this._esc(new Intl.DateTimeFormat(this._locale, { weekday: "short" }).format(day))}</span><b>${day.getDate()}</b></div>`).join("")}
      </div>
      <div class="all-day-grid" style="grid-template-columns:64px repeat(${days.length},minmax(0,1fr));grid-template-rows:repeat(${lanes},28px)">
        <div class="all-day-label" style="grid-row:1/${lanes + 1}">Ganztägig</div>
        ${days.map((_day, index) => `<div class="all-day-cell" style="grid-column:${index + 2};grid-row:1/${lanes + 1}"></div>`).join("")}
        ${banners.map((item) => this._bannerBlock(item)).join("")}
      </div>
      <div class="time-area" style="grid-template-columns:64px repeat(${days.length},minmax(0,1fr));height:${totalHeight}px">
        <div class="time-axis">
          ${Array.from({ length: bounds.end - bounds.start + 1 }, (_v, index) => `<div class="time-label" style="top:${index * hourHeight}px">${String(bounds.start + index).padStart(2, "0")}:00</div>`).join("")}
        </div>
        ${days.map((day, dayIndex) => this._renderTimedDay(day, dayIndex, timedEvents, bounds, hourHeight)).join("")}
      </div>
    </div></div>`;
  }

  _renderTimedDay(day, dayIndex, events, bounds, hourHeight) {
    const dayStart = this._startOfDay(day);
    const dayEnd = this._addDays(dayStart, 1);
    const visibleStart = new Date(dayStart);
    visibleStart.setHours(bounds.start, 0, 0, 0);
    const visibleEnd = new Date(dayStart);
    visibleEnd.setHours(bounds.end, 0, 0, 0);
    const dayEvents = events.filter((event) => event.end > visibleStart && event.start < visibleEnd && event.end > dayStart && event.start < dayEnd);
    const laidOut = this._layoutTimed(dayEvents, visibleStart, visibleEnd);

    return `<div class="time-day ${this._isToday(day) ? "today-col" : ""}" style="grid-column:${dayIndex + 2}">
      ${Array.from({ length: bounds.end - bounds.start }, (_v, index) => `<div class="hour-line" style="top:${index * hourHeight}px;height:${hourHeight}px"></div>`).join("")}
      ${laidOut.map((item) => {
        const top = ((item.start - visibleStart) / 60000 / 60) * hourHeight;
        const height = Math.max(22, ((item.end - item.start) / 60000 / 60) * hourHeight);
        const left = (item.lane / item.laneCount) * 100;
        const width = 100 / item.laneCount;
        return this._timedBlock(item.event, top, height, left, width);
      }).join("")}
    </div>`;
  }

  _layoutTimed(events, visibleStart, visibleEnd) {
    const intervals = events.map((event) => ({
      event,
      start: new Date(Math.max(event.start.getTime(), visibleStart.getTime())),
      end: new Date(Math.min(event.end.getTime(), visibleEnd.getTime())),
    })).sort((a, b) => a.start - b.start || a.end - b.end);

    const result = [];
    let cluster = [];
    let clusterEnd = null;
    const flush = () => {
      if (!cluster.length) return;
      const laneEnds = [];
      let maxLanes = 1;
      for (const item of cluster) {
        let lane = laneEnds.findIndex((end) => end <= item.start);
        if (lane < 0) lane = laneEnds.length;
        laneEnds[lane] = item.end;
        item.lane = lane;
        maxLanes = Math.max(maxLanes, laneEnds.length);
      }
      cluster.forEach((item) => { item.laneCount = maxLanes; result.push(item); });
      cluster = [];
      clusterEnd = null;
    };

    for (const item of intervals) {
      if (clusterEnd && item.start >= clusterEnd) flush();
      cluster.push(item);
      clusterEnd = !clusterEnd || item.end > clusterEnd ? item.end : clusterEnd;
    }
    flush();
    return result;
  }

  _layoutBanners(events, days) {
    if (!days.length) return [];
    const rangeStart = this._startOfDay(days[0]);
    const rangeEnd = this._addDays(this._startOfDay(days[days.length - 1]), 1);
    const items = [];
    for (const event of events) {
      let startDay = this._startOfDay(event.start);
      let endDay = this._startOfDay(event.end);
      if (!event.allDay && event.end > endDay) endDay = this._addDays(endDay, 1);
      if (endDay <= startDay) endDay = this._addDays(startDay, 1);
      const clippedStart = startDay < rangeStart ? rangeStart : startDay;
      const clippedEnd = endDay > rangeEnd ? rangeEnd : endDay;
      if (clippedEnd <= clippedStart) continue;
      items.push({
        event,
        start: this._daysBetween(rangeStart, clippedStart),
        end: this._daysBetween(rangeStart, clippedEnd),
      });
    }
    items.sort((a, b) => a.start - b.start || b.end - a.end);
    const laneEnds = [];
    for (const item of items) {
      let lane = laneEnds.findIndex((end) => end <= item.start);
      if (lane < 0) lane = laneEnds.length;
      item.lane = lane;
      laneEnds[lane] = item.end;
    }
    return items;
  }

  _bannerBlock(item) {
    const event = item.event;
    const index = this._eventIndexes.get(event);
    return `<button type="button" class="event-block banner" data-event-index="${index}" style="--event-color:${this._esc(event.color)};grid-column:${item.start + 2}/${item.end + 2};grid-row:${item.lane + 1}">
      <span class="event-title">${this._esc(event.summary)}</span>
    </button>`;
  }

  _timedBlock(event, top, height, left, width) {
    const index = this._eventIndexes.get(event);
    return `<button type="button" class="event-block timed" data-event-index="${index}" style="--event-color:${this._esc(event.color)};top:${top}px;height:${height}px;left:calc(${left}% + 2px);width:calc(${width}% - 4px)">
      <span class="event-title">${this._esc(event.summary)}</span>
      <span class="event-time">${this._esc(this._timeText(event))}${event.location ? ` · ${this._esc(event.location)}` : ""}</span>
    </button>`;
  }

  _renderMonth(events) {
    const days = this._visibleDays();
    const currentMonth = this._cursor.getMonth();
    const maxEvents = Math.max(1, Number(this.config?.month_max_events || 4));
    return `<div class="calendar-scroll"><div class="month-grid">
      ${["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"].map((day) => `<div class="month-weekday">${day}</div>`).join("")}
      ${days.map((day) => {
        const dayStart = this._startOfDay(day);
        const dayEnd = this._addDays(dayStart, 1);
        const dayEvents = events.filter((event) => event.end > dayStart && event.start < dayEnd);
        const shown = dayEvents.slice(0, maxEvents);
        return `<div class="month-day ${day.getMonth() !== currentMonth ? "outside" : ""} ${this._isToday(day) ? "today" : ""}">
          <button type="button" class="day-number" data-day="${this._ymd(day)}">${day.getDate()}</button>
          <div class="month-events">
            ${shown.map((event) => {
              const index = this._eventIndexes.get(event);
              const prefix = event.allDay || this._isBannerEvent(event) ? "" : `${this._formatTime(event.start)} `;
              return `<button type="button" class="month-event" data-event-index="${index}" style="--event-color:${this._esc(event.color)}"><b>${this._esc(prefix)}</b>${this._esc(event.summary)}</button>`;
            }).join("")}
            ${dayEvents.length > shown.length ? `<div class="more">+${dayEvents.length - shown.length} weitere</div>` : ""}
          </div>
        </div>`;
      }).join("")}
    </div></div>`;
  }

  _timeBounds(events) {
    let start = this.config?.start_hour != null ? Number(this.config.start_hour) : 7;
    let end = this.config?.end_hour != null ? Number(this.config.end_hour) : 18;
    if (this.config?.start_hour == null || this.config?.end_hour == null) {
      for (const event of events) {
        if (this.config?.start_hour == null) start = Math.min(start, event.start.getHours());
        if (this.config?.end_hour == null) {
          const roundedEnd = event.end.getHours() + (event.end.getMinutes() || event.end.getSeconds() ? 1 : 0);
          end = Math.max(end, roundedEnd);
        }
      }
    }
    start = Math.max(0, Math.min(23, Math.floor(start)));
    end = Math.max(start + 1, Math.min(24, Math.ceil(end)));
    return { start, end };
  }

  _isBannerEvent(event) {
    if (event.allDay) return true;
    const endProbe = new Date(Math.max(event.start.getTime(), event.end.getTime() - 1));
    return this._ymd(event.start) !== this._ymd(endProbe);
  }

  _periodTitle() {
    if (this._view === "day") {
      return new Intl.DateTimeFormat(this._locale, { weekday: "long", day: "2-digit", month: "long", year: "numeric" }).format(this._cursor);
    }
    if (this._view === "month") {
      return new Intl.DateTimeFormat(this._locale, { month: "long", year: "numeric" }).format(this._cursor);
    }
    const start = this._startOfWeek(this._cursor);
    const end = this._addDays(start, 6);
    const startText = new Intl.DateTimeFormat(this._locale, { day: "2-digit", month: "short" }).format(start);
    const endText = new Intl.DateTimeFormat(this._locale, { day: "2-digit", month: "short", year: "numeric" }).format(end);
    return `${startText} – ${endText}`;
  }

  _renderAddDialog() {
    return `<dialog class="add-dialog">
      <form class="add-form">
        <h3>Termin hinzufügen</h3>
        <div class="form-grid">
          <label class="full">Titel<input name="summary" type="text" required maxlength="255"></label>
          <label class="check full"><input name="all_day" type="checkbox"> Ganztägig</label>
          <label>Von<input name="start_date" type="date" required></label>
          <label>Bis<input name="end_date" type="date" required></label>
          <label class="time-field">Startzeit<input name="start_time" type="time" value="08:00" required></label>
          <label class="time-field">Endzeit<input name="end_time" type="time" value="09:00" required></label>
          <label class="full">Ort<input name="location" type="text" maxlength="255"></label>
          <label class="full">Beschreibung<textarea name="description" rows="3"></textarea></label>
        </div>
        <div class="form-error" aria-live="polite"></div>
        <div class="dialog-actions">
          <button class="secondary cancel-add" type="button">Abbrechen</button>
          <button class="primary" type="submit">Speichern</button>
        </div>
      </form>
    </dialog>`;
  }

  _renderDetailDialog() {
    return `<dialog class="detail-dialog">
      <div class="detail-content">
        <div class="detail-head"><h3 data-detail="summary"></h3><button type="button" class="icon close-detail" aria-label="Schließen">×</button></div>
        <div class="detail-time" data-detail="time"></div>
        <div class="detail-meta" data-detail="source"></div>
        <div class="detail-row" data-detail-row="location"><b>Ort</b><span data-detail="location"></span></div>
        <div class="detail-row description" data-detail-row="description"><b>Beschreibung</b><span data-detail="description"></span></div>
        <div class="dialog-actions">
          <button class="danger delete-detail" type="button">Termin löschen</button>
          <button class="secondary close-detail" type="button">Schließen</button>
        </div>
      </div>
    </dialog>`;
  }

  _bindInteractions() {
    this.shadowRoot.querySelectorAll("[data-nav]").forEach((button) => {
      button.addEventListener("click", () => this._navigate(button.dataset.nav));
    });
    this.shadowRoot.querySelectorAll("[data-view]").forEach((button) => {
      button.addEventListener("click", () => this._setView(button.dataset.view));
    });
    this.shadowRoot.querySelectorAll("[data-source]").forEach((button) => {
      button.addEventListener("click", () => {
        const source = button.dataset.source;
        if (this._disabledSources.has(source)) this._disabledSources.delete(source);
        else this._disabledSources.add(source);
        this._render();
      });
    });
    this.shadowRoot.querySelectorAll("[data-event-index]").forEach((button) => {
      button.addEventListener("click", () => this._openDetails(Number(button.dataset.eventIndex)));
    });
    this.shadowRoot.querySelectorAll("[data-day]").forEach((button) => {
      button.addEventListener("click", () => {
        const day = this._parseLocalDate(button.dataset.day);
        if (!day) return;
        this._cursor = day;
        this._view = "day";
        this._subscriptionKey = "";
        this._syncSubscriptions();
      });
    });

    this.shadowRoot.querySelector(".add-event")?.addEventListener("click", () => this._openAddDialog());
    this.shadowRoot.querySelector(".cancel-add")?.addEventListener("click", () => this.shadowRoot.querySelector(".add-dialog")?.close());
    this.shadowRoot.querySelector(".add-form")?.addEventListener("submit", (event) => this._submitAdd(event));
    this.shadowRoot.querySelector(".add-form input[name='all_day']")?.addEventListener("change", (event) => this._toggleAllDay(Boolean(event.target.checked)));
    this.shadowRoot.querySelectorAll(".close-detail").forEach((button) => button.addEventListener("click", () => this.shadowRoot.querySelector(".detail-dialog")?.close()));
    this.shadowRoot.querySelector(".delete-detail")?.addEventListener("click", () => this._deleteDetailEvent());
  }

  _navigate(direction) {
    if (direction === "today") {
      this._cursor = this._startOfDay(new Date());
    } else if (this._view === "day") {
      this._cursor = this._addDays(this._cursor, direction === "prev" ? -1 : 1);
    } else if (this._view === "week") {
      this._cursor = this._addDays(this._cursor, direction === "prev" ? -7 : 7);
    } else {
      this._cursor = new Date(this._cursor.getFullYear(), this._cursor.getMonth() + (direction === "prev" ? -1 : 1), 1);
    }
    this._subscriptionKey = "";
    this._syncSubscriptions();
  }

  _setView(view) {
    if (!new Set(["day", "week", "month"]).has(view) || view === this._view) return;
    this._view = view;
    this._subscriptionKey = "";
    this._syncSubscriptions();
  }

  _openAddDialog() {
    const target = this._writableCalendar();
    if (!target) return;
    const dialog = this.shadowRoot.querySelector(".add-dialog");
    const form = this.shadowRoot.querySelector(".add-form");
    if (!dialog || !form) return;
    form.reset();
    const range = this._viewRange();
    const today = this._startOfDay(new Date());
    const defaultDay = today >= range.start && today < range.end ? today : this._startOfDay(this._cursor);
    form.elements.start_date.value = this._ymd(defaultDay);
    form.elements.end_date.value = this._ymd(defaultDay);
    form.elements.start_time.value = "08:00";
    form.elements.end_time.value = "09:00";
    form.elements.all_day.checked = false;
    this._toggleAllDay(false);
    const error = dialog.querySelector(".form-error");
    if (error) error.textContent = "";
    dialog.showModal();
    queueMicrotask(() => form.elements.summary?.focus());
  }

  _toggleAllDay(allDay) {
    this.shadowRoot.querySelectorAll(".time-field").forEach((field) => {
      field.classList.toggle("hidden", allDay);
      const input = field.querySelector("input");
      if (input) input.disabled = allDay;
    });
  }

  async _submitAdd(event) {
    event.preventDefault();
    const target = this._writableCalendar();
    const form = event.currentTarget;
    const dialog = this.shadowRoot.querySelector(".add-dialog");
    const error = dialog?.querySelector(".form-error");
    if (!target) {
      if (error) error.textContent = "Kein schreibbarer SPH-Kalender gefunden.";
      return;
    }
    const data = Object.fromEntries(new FormData(form).entries());
    const allDay = form.elements.all_day.checked;
    let dtstart;
    let dtend;
    if (allDay) {
      const start = this._parseLocalDate(data.start_date);
      const endInclusive = this._parseLocalDate(data.end_date);
      if (!start || !endInclusive || endInclusive < start) {
        if (error) error.textContent = "Das Enddatum muss am oder nach dem Startdatum liegen.";
        return;
      }
      dtstart = this._ymd(start);
      dtend = this._ymd(this._addDays(endInclusive, 1));
    } else {
      const start = new Date(`${data.start_date}T${data.start_time}:00`);
      const end = new Date(`${data.end_date}T${data.end_time}:00`);
      if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end <= start) {
        if (error) error.textContent = "Das Ende muss nach dem Start liegen.";
        return;
      }
      dtstart = start.toISOString();
      dtend = end.toISOString();
    }

    const payload = {
      summary: String(data.summary || "").trim(),
      dtstart,
      dtend,
    };
    if (String(data.description || "").trim()) payload.description = String(data.description).trim();
    if (String(data.location || "").trim()) payload.location = String(data.location).trim();

    try {
      if (error) error.textContent = "";
      await this._hass.callWS({
        type: "calendar/event/create",
        entity_id: target.entity,
        event: payload,
      });
      dialog?.close();
    } catch (err) {
      console.error("SPH: Kalendertermin konnte nicht angelegt werden", err);
      if (error) error.textContent = err?.message || "Termin konnte nicht gespeichert werden.";
    }
  }

  _openDetails(index) {
    const event = this._renderEvents[index];
    if (!event) return;
    this._detailEvent = event;
    const dialog = this.shadowRoot.querySelector(".detail-dialog");
    if (!dialog) return;
    const setText = (name, value) => {
      const node = dialog.querySelector(`[data-detail='${name}']`);
      if (node) node.textContent = value || "";
    };
    setText("summary", event.summary);
    setText("time", this._detailTimeText(event));
    setText("source", `${this._sourceLabel(event.source)} · ${event.calendar_name}`);
    setText("location", event.location);
    setText("description", schoolDescription(this, event.description));
    dialog.querySelector("[data-detail-row='location']")?.classList.toggle("hidden", !event.location);
    dialog.querySelector("[data-detail-row='description']")?.classList.toggle("hidden", !event.description);
    const deleteButton = dialog.querySelector(".delete-detail");
    if (deleteButton) deleteButton.classList.toggle("hidden", !this._isDeletable(event));
    dialog.showModal();
  }

  async _deleteDetailEvent() {
    const event = this._detailEvent;
    if (!event || !this._isDeletable(event)) return;
    if (!window.confirm(`„${event.summary}“ löschen?`)) return;
    try {
      await this._hass.callWS({
        type: "calendar/event/delete",
        entity_id: event.entity_id,
        uid: event.uid,
        ...(event.recurrence_id ? { recurrence_id: event.recurrence_id } : {}),
      });
      this.shadowRoot.querySelector(".detail-dialog")?.close();
    } catch (err) {
      console.error("SPH: Kalendertermin konnte nicht gelöscht werden", err);
      window.alert(err?.message || "Termin konnte nicht gelöscht werden.");
    }
  }

  _writableCalendar() {
    for (const cal of this._calendars) {
      const state = this._hass?.states?.[cal.entity];
      const features = Number(state?.attributes?.supported_features || 0);
      if ((features & 1) && (cal.entity.startsWith("calendar.sph_") || cal.entity.startsWith("calendar.schulkalender_"))) {
        return cal;
      }
    }
    return null;
  }

  _isDeletable(event) {
    if (!String(event.uid || "").startsWith("sph-kalender-manual-")) return false;
    const state = this._hass?.states?.[event.entity_id];
    return Boolean(Number(state?.attributes?.supported_features || 0) & 2);
  }

  _detailTimeText(event) {
    if (event.allDay) {
      const endInclusive = this._addDays(event.end, -1);
      if (this._ymd(event.start) === this._ymd(endInclusive)) return `${this._formatDate(event.start)} · ganztägig`;
      return `${this._formatDate(event.start)} – ${this._formatDate(endInclusive)} · ganztägig`;
    }
    const sameDay = this._ymd(event.start) === this._ymd(event.end);
    if (sameDay) return `${this._formatDate(event.start)} · ${this._formatTime(event.start)}–${this._formatTime(event.end)}`;
    return `${this._formatDateTime(event.start)} – ${this._formatDateTime(event.end)}`;
  }

  _timeText(event) {
    return `${this._formatTime(event.start)}–${this._formatTime(event.end)}`;
  }

  _formatTime(date) {
    return new Intl.DateTimeFormat(this._locale, { hour: "2-digit", minute: "2-digit" }).format(date);
  }

  _formatDate(date) {
    return new Intl.DateTimeFormat(this._locale, { day: "2-digit", month: "2-digit", year: "numeric" }).format(date);
  }

  _formatDateTime(date) {
    return new Intl.DateTimeFormat(this._locale, { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(date);
  }

  _startOfDay(value) {
    return new Date(value.getFullYear(), value.getMonth(), value.getDate());
  }

  _startOfWeek(value) {
    const day = this._startOfDay(value);
    const offset = (day.getDay() + 6) % 7;
    return this._addDays(day, -offset);
  }

  _addDays(value, amount) {
    const result = new Date(value.getFullYear(), value.getMonth(), value.getDate());
    result.setDate(result.getDate() + amount);
    return result;
  }

  _daysBetween(start, end) {
    const a = Date.UTC(start.getFullYear(), start.getMonth(), start.getDate());
    const b = Date.UTC(end.getFullYear(), end.getMonth(), end.getDate());
    return Math.round((b - a) / 86400000);
  }

  _parseLocalDate(value) {
    const match = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!match) return null;
    const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
    return Number.isNaN(date.getTime()) ? null : date;
  }

  _ymd(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  }

  _isToday(date) {
    return this._ymd(date) === this._ymd(new Date());
  }

  _esc(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  _styles() {
    return `
      :host { display:block; }
      ha-card { overflow:hidden; }
      button, input, textarea { font:inherit; }
      button { cursor:pointer; color:var(--primary-text-color); }
      button:disabled { cursor:not-allowed; opacity:.45; }
      .card-header { padding:14px 16px 10px; border-bottom:1px solid var(--divider-color); }
      .title-row, .nav-row { display:flex; align-items:center; gap:10px; }
      .title-row { justify-content:space-between; margin-bottom:10px; }
      .title { font-size:1.25rem; font-weight:600; }
      .nav-row { display:grid; grid-template-columns:auto 1fr auto; }
      .period { text-align:center; font-weight:600; text-transform:capitalize; }
      .nav-buttons, .view-buttons { display:flex; gap:4px; }
      .nav-buttons button, .view-buttons button, .filter-chip { border:1px solid var(--divider-color); background:transparent; border-radius:8px; padding:6px 9px; }
      .view-buttons button.active { background:var(--primary-color); color:var(--text-primary-color); border-color:var(--primary-color); }
      .primary { border:0; border-radius:8px; background:var(--primary-color); color:var(--text-primary-color); padding:8px 12px; font-weight:600; }
      .secondary { border:1px solid var(--divider-color); background:transparent; border-radius:8px; padding:8px 12px; }
      .danger { border:1px solid var(--error-color,#d32f2f); color:var(--error-color,#d32f2f); background:transparent; border-radius:8px; padding:8px 12px; }
      .filters { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }
      .filter-chip { display:flex; align-items:center; gap:6px; font-size:.86rem; }
      .filter-chip span { width:9px; height:9px; border-radius:50%; background:var(--chip-color); }
      .filter-chip.off { opacity:.45; text-decoration:line-through; }
      .calendar-body { min-height:160px; }
      .calendar-scroll { overflow:auto; max-width:100%; }
      .dayweek { padding-bottom:10px; }
      .day-head-grid { display:grid; border-bottom:1px solid var(--divider-color); background:var(--card-background-color,var(--ha-card-background)); position:sticky; top:0; z-index:5; }
      .day-head { min-height:54px; display:flex; align-items:center; justify-content:center; gap:7px; border-left:1px solid var(--divider-color); }
      .day-head span { color:var(--secondary-text-color); text-transform:uppercase; font-size:.78rem; }
      .day-head b { display:grid; place-items:center; min-width:30px; height:30px; border-radius:50%; font-size:1rem; }
      .day-head.today b, .month-day.today .day-number { background:var(--primary-color); color:var(--text-primary-color); }
      .all-day-grid { display:grid; position:relative; border-bottom:1px solid var(--divider-color); min-height:32px; padding:3px 0; }
      .all-day-label { grid-column:1; display:flex; align-items:flex-start; justify-content:flex-end; padding:5px 8px 0 0; color:var(--secondary-text-color); font-size:.72rem; z-index:1; }
      .all-day-cell { border-left:1px solid var(--divider-color); min-height:28px; }
      .time-area { display:grid; position:relative; }
      .time-axis { grid-column:1; position:relative; }
      .time-label { position:absolute; right:8px; transform:translateY(-50%); color:var(--secondary-text-color); font-size:.72rem; white-space:nowrap; }
      .time-day { position:relative; border-left:1px solid var(--divider-color); overflow:hidden; }
      .time-day.today-col { background:color-mix(in srgb,var(--primary-color) 4%,transparent); }
      .hour-line { position:absolute; left:0; right:0; border-top:1px solid var(--divider-color); box-sizing:border-box; }
      .event-block, .month-event { --event-color:#546e7a; border:0; border-left:4px solid var(--event-color); background:color-mix(in srgb,var(--event-color) 18%,var(--card-background-color,var(--ha-card-background))); color:var(--primary-text-color); text-align:left; }
      .event-block:hover, .month-event:hover { background:color-mix(in srgb,var(--event-color) 28%,var(--card-background-color,var(--ha-card-background))); }
      .event-block.banner { z-index:2; margin:2px 3px; min-width:0; border-radius:5px; padding:3px 7px; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; }
      .event-block.timed { position:absolute; z-index:2; border-radius:5px; padding:4px 5px; overflow:hidden; min-height:20px; }
      .event-title { display:block; font-weight:650; font-size:.82rem; overflow:hidden; text-overflow:ellipsis; }
      .event-time { display:block; font-size:.7rem; color:var(--secondary-text-color); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .month-grid { display:grid; grid-template-columns:repeat(7,minmax(100px,1fr)); min-width:760px; }
      .month-weekday { padding:8px; text-align:center; font-size:.78rem; font-weight:700; color:var(--secondary-text-color); border-bottom:1px solid var(--divider-color); }
      .month-day { min-height:116px; padding:6px; border-right:1px solid var(--divider-color); border-bottom:1px solid var(--divider-color); box-sizing:border-box; }
      .month-day.outside { opacity:.48; }
      .day-number { width:28px; height:28px; border:0; background:transparent; border-radius:50%; padding:0; margin-bottom:4px; }
      .month-events { display:flex; flex-direction:column; gap:3px; }
      .month-event { width:100%; border-radius:4px; padding:3px 5px; font-size:.72rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .more { color:var(--secondary-text-color); font-size:.72rem; padding:2px 4px; }
      .empty { padding:24px 16px; color:var(--secondary-text-color); }
      code { font-family:monospace; }
      dialog { color:var(--primary-text-color); background:var(--card-background-color,var(--ha-card-background)); border:0; border-radius:12px; padding:0; box-shadow:var(--ha-card-box-shadow,0 8px 28px rgba(0,0,0,.32)); width:min(560px,calc(100vw - 28px)); }
      dialog::backdrop { background:rgba(0,0,0,.45); }
      form, .detail-content { padding:18px; }
      h3 { margin:0 0 14px; }
      .form-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
      label { display:flex; flex-direction:column; gap:5px; font-size:.85rem; color:var(--secondary-text-color); }
      label.full { grid-column:1/-1; }
      label.check { flex-direction:row; align-items:center; color:var(--primary-text-color); }
      input, textarea { box-sizing:border-box; width:100%; padding:9px; border:1px solid var(--divider-color); border-radius:7px; background:var(--card-background-color,var(--ha-card-background)); color:var(--primary-text-color); }
      textarea { resize:vertical; }
      .dialog-actions { display:flex; justify-content:flex-end; gap:8px; margin-top:18px; }
      .form-error { min-height:20px; margin-top:8px; color:var(--error-color,#d32f2f); font-size:.82rem; }
      .hidden { display:none !important; }
      .detail-head { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
      .detail-head h3 { margin-bottom:6px; }
      .icon { border:0; background:transparent; font-size:1.5rem; line-height:1; padding:0 4px; }
      .detail-time, .detail-meta { color:var(--secondary-text-color); font-size:.86rem; margin-bottom:8px; }
      .detail-row { display:grid; grid-template-columns:110px 1fr; gap:8px; margin-top:12px; }
      .detail-row span { white-space:pre-wrap; overflow-wrap:anywhere; }
      @media(max-width:650px) {
        .nav-row { grid-template-columns:1fr auto; }
        .period { grid-column:1/-1; grid-row:1; margin-bottom:6px; }
        .nav-buttons { grid-column:1; grid-row:2; }
        .view-buttons { grid-column:2; grid-row:2; }
        .form-grid { grid-template-columns:1fr; }
        label.full { grid-column:auto; }
        .detail-row { grid-template-columns:1fr; gap:3px; }
      }
    `;
  }

  getCardSize() {
    return this._view === "month" ? 8 : 10;
  }
}

if (!customElements.get("sph-kalender-card")) {
  customElements.define("sph-kalender-card", schoolCard(SphKalenderCard));
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "sph-kalender-card")) {
  window.customCards.push({
    type: "sph-kalender-card",
    name: "SPH Kalender",
    description: "SPH-Kalender mit Tag-, Wochen- und Monatsansicht sowie eigenen Terminen",
    preview: true,
  });
}
