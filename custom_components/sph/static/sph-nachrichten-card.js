// SPH Nachrichten card: lists inbox messages of a child's Schulportal account.
// Subjects and senders come via the "sph/nachrichten" WebSocket command instead
// of sensor attributes, so the sensor does not write them to the recorder.

const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);

const formatTimestamp = (iso) => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("de-DE", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
};

const formatDate = (iso, fallback) => {
  if (!iso) return fallback || "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return fallback || "";
  const now = new Date();
  const sameDay = date.toDateString() === now.toDateString();
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const time = date.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
  if (sameDay) return `heute ${time}`;
  if (date.toDateString() === yesterday.toDateString()) return `gestern ${time}`;
  const sameYear = date.getFullYear() === now.getFullYear();
  return date.toLocaleDateString("de-DE", sameYear
    ? { day: "2-digit", month: "2-digit" }
    : { day: "2-digit", month: "2-digit", year: "numeric" });
};

class SphNachrichtenCard extends HTMLElement {
  setConfig(config) {
    this.config = { show_read: false, max: 10, ...(config || {}) };
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._payload = null;
    this._loadedFor = null;
    this._loadGeneration = 0;
    this._renderedDay = null;
    this._entity = null;
  }

  set hass(hass) {
    this._hass = hass;
    const entity = this._findEntity();
    if (!entity) {
      if (this._loadedFor !== "missing") {
        this._loadedFor = "missing";
        this._renderMessage("Kein SPH-Nachrichten-Sensor gefunden.");
      }
      return;
    }
    this._entity = entity;
    // Reload only when the sensor itself changed (i.e. after a poll).
    const key = `${entity.entity_id}|${entity.last_updated}`;
    if (key !== this._loadedFor) {
      this._loadedFor = key;
      this._load(entity);
      return;
    }
    // Relative labels ("heute", "gestern") go stale at midnight.
    if (this._payload && this._renderedDay !== new Date().toDateString()) {
      this._render(entity);
    }
  }

  _findEntity() {
    const states = this._hass?.states || {};
    const configured = this.config?.entity || this.config?.sensor;
    if (configured) return states[configured] || null;
    const candidates = Object.values(states).filter((state) =>
      state.entity_id.startsWith("sensor.nachrichten_ungelesen_"));
    const child = String(this.config?.child || "").trim().toLowerCase();
    if (child) {
      return candidates.find((state) =>
        [state.attributes?.kind_kürzel, state.attributes?.kind]
          .some((value) => String(value || "").trim().toLowerCase() === child)) || null;
    }
    return candidates[0] || null;
  }

  async _load(entity) {
    const generation = ++this._loadGeneration;
    let payload = null;
    let error = null;
    try {
      payload = await this._hass.callWS({
        type: "sph/nachrichten",
        entity_id: entity.entity_id,
      });
    } catch (err) {
      error = err?.message || "Nachrichten konnten nicht geladen werden.";
    }
    // Ignore answers overtaken by a newer request.
    if (generation !== this._loadGeneration) return;
    this._payload = payload;
    this._error = error;
    this._render(this._entity || entity);
  }

  _renderMessage(text) {
    this.shadowRoot.innerHTML = `${this._styles()}<ha-card><div class="empty">${escapeHtml(text)}</div></ha-card>`;
  }

  _render(entity) {
    const payload = this._payload || {};
    const all = Array.isArray(payload.nachrichten) ? payload.nachrichten : [];
    const shown = (this.config.show_read ? all : all.filter((item) => item.ungelesen))
      .slice(0, Math.max(1, Number(this.config.max) || 10));
    const unread = Number(payload.ungelesen ?? entity.state) || 0;
    const portal = payload.portal_url || entity.attributes?.portal_url || "https://start.schulportal.hessen.de/nachrichten.php";
    const kind = entity.attributes?.kind || "";
    const title = this.config.title || (kind ? `Nachrichten ${kind}` : "SPH Nachrichten");

    const rows = shown.map((item) => `
      <a class="row ${item.ungelesen ? "unread" : ""}" href="${escapeHtml(portal)}" target="_blank" rel="noopener noreferrer">
        <span class="dot" aria-hidden="true"></span>
        <span class="text">
          <span class="subject">${escapeHtml(item.betreff)}</span>
          <span class="meta">${escapeHtml(item.absender)}</span>
        </span>
        <span class="date">${escapeHtml(formatDate(item.datum, item.datum_text))}</span>
      </a>`).join("");

    let body;
    if (this._error) body = `<div class="empty error">${escapeHtml(this._error)}</div>`;
    else if (payload.aktiv === false) body = `<div class="empty">Das Nachrichten-Modul ist deaktiviert.</div>`;
    else if (!payload.abgerufen) body = `<div class="empty">Noch kein Abruf erfolgt.</div>`;
    else if (!shown.length) body = `<div class="empty">${this.config.show_read ? "Keine Nachrichten." : "Keine ungelesenen Nachrichten."}</div>`;
    else body = `<div class="list">${rows}</div>`;

    const stand = payload.abgerufen
      ? `Stand ${formatTimestamp(payload.abgerufen)}${payload.letzter_abruf_ok === false ? " · letzter Abruf fehlgeschlagen" : ""}`
      : "";

    this._renderedDay = new Date().toDateString();
    this.shadowRoot.innerHTML = `${this._styles()}
      <ha-card>
        <div class="header">
          <span class="title">${escapeHtml(title)}</span>
          <span class="badge ${unread ? "" : "zero"}">${unread}</span>
        </div>
        ${body}
        <div class="footer">
          <span class="stand">${escapeHtml(stand)}</span>
          <a class="portal" href="${escapeHtml(portal)}" target="_blank" rel="noopener noreferrer">Im Schulportal öffnen</a>
        </div>
      </ha-card>`;
  }

  _styles() {
    return `<style>
      ha-card { padding: 12px 16px; }
      .header { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
      .title { font-size: 1.1em; font-weight: 500; }
      .badge { min-width: 24px; padding: 2px 8px; border-radius: 12px; text-align: center; font-weight: 600;
        background: var(--primary-color); color: var(--text-primary-color, #fff); }
      .badge.zero { background: var(--disabled-color, #bdbdbd); }
      .list { display: flex; flex-direction: column; }
      .row { display: grid; grid-template-columns: 10px 1fr auto; gap: 10px; align-items: center;
        padding: 8px 0; border-top: 1px solid var(--divider-color); color: inherit; text-decoration: none; }
      .row:first-child { border-top: none; }
      .row:hover .subject { text-decoration: underline; }
      .dot { width: 8px; height: 8px; border-radius: 50%; background: transparent; }
      .row.unread .dot { background: var(--primary-color); }
      .text { display: flex; flex-direction: column; min-width: 0; }
      .subject, .meta { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .row.unread .subject { font-weight: 600; }
      .meta, .date, .stand { color: var(--secondary-text-color); font-size: 0.85em; }
      .date { white-space: nowrap; }
      .empty { padding: 12px 0; color: var(--secondary-text-color); }
      .empty.error { color: var(--error-color); }
      .footer { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap;
        margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--divider-color); }
      .portal { color: var(--primary-color); text-decoration: none; font-weight: 500; }
    </style>`;
  }

  getCardSize() { return 4; }

  static getStubConfig(hass) {
    const sensor = Object.keys(hass?.states || {}).find((id) => id.startsWith("sensor.nachrichten_ungelesen_"));
    return sensor ? { entity: sensor } : {};
  }
}

if (!customElements.get("sph-nachrichten-card")) {
  customElements.define("sph-nachrichten-card", SphNachrichtenCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "sph-nachrichten-card")) {
  window.customCards.push({
    type: "sph-nachrichten-card",
    name: "SPH Nachrichten",
    description: "Ungelesene Nachrichten aus dem Schulportal Hessen mit Link ins Portal.",
  });
}
