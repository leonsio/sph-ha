class SphVertretungsplanCard extends HTMLElement {
  setConfig(config) {
    this.config = config || {};
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  static getStubConfig(hass) {
    const entity = Object.values(hass?.states || {}).find((state) =>
      state.entity_id.startsWith("sensor.vertretungsplan_")
    );
    return { entity: entity ? entity.entity_id : "sensor.vertretungsplan" };
  }

  getCardSize() {
    const days = this._days().length;
    return days ? 1 + days * 2 : 3;
  }

  _entity() {
    const hass = this._hass;
    if (!hass) return null;
    const configured = this.config.entity || this.config.sensor;
    if (configured) return hass.states[configured] || null;

    const candidates = Object.values(hass.states).filter(
      (state) =>
        state.entity_id.startsWith("sensor.vertretungsplan_") &&
        Array.isArray(state.attributes?.tage)
    );
    if (!this.config.child) return candidates[0] || null;
    const wanted = this._norm(this.config.child);
    return (
      candidates.find(
        (state) =>
          this._norm(state.attributes?.kind_kürzel) === wanted ||
          this._norm(state.attributes?.kind) === wanted
      ) || null
    );
  }

  _days() {
    const attrs = this._entity()?.attributes || {};
    let days = Array.isArray(attrs.tage) ? attrs.tage.slice() : [];
    if (this.config.only_cancellations) {
      days = days.map((day) => ({
        ...day,
        eintraege: (day.eintraege || []).filter((entry) => entry.entfall),
      }));
    }
    if (this.config.hide_empty) {
      days = days.filter((day) => (day.eintraege || []).length > 0);
    }
    const limit = Number(this.config.days);
    if (Number.isFinite(limit) && limit > 0) days = days.slice(0, limit);
    return days;
  }

  _render() {
    if (!this._hass || !this.config || !this.shadowRoot) return;

    const entity = this._entity();
    const attrs = entity?.attributes || {};
    const days = this._days();
    const title = this.config.title || "";
    const header = title ? ` header="${this._escapeAttr(title)}"` : "";

    let body;
    if (!entity) {
      body = `<div class="empty">Kein Vertretungsplan-Sensor gefunden.</div>`;
    } else if (!days.length) {
      body = `<div class="empty">${this._escape(
        this.config.only_cancellations
          ? "Zurzeit fällt nichts aus."
          : "Zurzeit ist kein Vertretungsplan veröffentlicht."
      )}</div>`;
    } else {
      body = days.map((day) => this._renderDay(day)).join("");
    }

    this.shadowRoot.innerHTML = `<style>${this._styles()}</style><ha-card${header}><div class="content">${body}${this._renderFooter(attrs)}</div></ha-card>`;
  }

  _renderDay(day) {
    const entries = day.eintraege || [];
    const badges = [];
    if (day.relativ) badges.push(`<span class="badge rel">${this._escape(day.relativ)}</span>`);
    if (day.woche) badges.push(`<span class="badge week">${this._escape(day.woche)}</span>`);

    const notes = (day.hinweise || [])
      .map((note) => `<div class="note">${this._escape(note)}</div>`)
      .join("");

    const rows = entries.length
      ? entries.map((entry) => this._renderEntry(entry)).join("")
      : `<div class="empty small">Keine Einträge</div>`;

    return `<div class="day">
      <div class="day-head">
        <span class="day-title">${this._escape(day.wochentag || "")}, ${this._escape(day.datum_de || day.datum || "")}</span>
        <span class="badges">${badges.join("")}</span>
      </div>
      ${notes}
      ${rows}
    </div>`;
  }

  _renderEntry(entry) {
    const cancelled = Boolean(entry.entfall);
    const subject = entry.fach_lang || entry.fach || "Unbekannt";
    const art = entry.art_lang || entry.art || (cancelled ? "Entfall" : "Änderung");

    const details = [];
    if (entry.raum) {
      details.push(
        entry.raum_alt && entry.raum_alt !== entry.raum
          ? `Raum ${this._escape(entry.raum)} <span class="was">statt ${this._escape(entry.raum_alt)}</span>`
          : `Raum ${this._escape(entry.raum)}`
      );
    }
    if (entry.vertreter) details.push(`Vertretung ${this._escape(entry.vertreter)}`);
    if (entry.lehrer) details.push(`für ${this._escape(entry.lehrer)}`);
    if (entry.klasse) details.push(this._escape(entry.klasse));

    return `<div class="entry${cancelled ? " cancelled" : ""}">
      <div class="lesson">${this._escape(this._lessonLabel(entry))}</div>
      <div class="body">
        <div class="line">
          <span class="subject">${this._escape(subject)}</span>
          <span class="badge art${cancelled ? " out" : ""}">${this._escape(art)}</span>
        </div>
        ${details.length ? `<div class="details">${details.join(" · ")}</div>` : ""}
        ${entry.hinweis ? `<div class="hint">${this._escape(entry.hinweis)}</div>` : ""}
      </div>
    </div>`;
  }

  _lessonLabel(entry) {
    const from = entry.von_stunde;
    const to = entry.bis_stunde;
    if (from === null || from === undefined) return entry.stunde ? `${entry.stunde}.` : "–";
    if (to === null || to === undefined || to === from) return `${from}.`;
    return `${from}.–${to}.`;
  }

  _renderFooter(attrs) {
    const parts = [];
    if (attrs.aktualisiert) {
      const stamp = new Date(attrs.aktualisiert);
      if (!Number.isNaN(stamp.getTime())) {
        parts.push(
          "Stand: " +
            new Intl.DateTimeFormat("de-DE", {
              day: "2-digit",
              month: "2-digit",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            }).format(stamp) +
            " Uhr"
        );
      }
    }
    if (attrs.wird_aktualisiert) parts.push("Plan wird gerade aktualisiert");
    return parts.length ? `<div class="footer">${this._escape(parts.join(" · "))}</div>` : "";
  }

  _styles() {
    return `
      :host{display:block}
      .content{padding:12px 16px}
      .day{padding-bottom:10px}
      .day+.day{border-top:1px solid var(--divider-color);padding-top:12px}
      .day-head{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;margin-bottom:8px}
      .day-title{font-size:1.05rem;font-weight:600}
      .badges{display:flex;gap:4px;flex-wrap:wrap}
      .badge{display:inline-flex;align-items:center;padding:1px 7px;border-radius:9px;font-size:.75rem;font-weight:600;white-space:nowrap}
      .badge.rel{background:var(--primary-color);color:var(--text-primary-color)}
      .badge.week{background:var(--secondary-background-color);color:var(--secondary-text-color)}
      .badge.art{background:var(--secondary-background-color);color:var(--secondary-text-color)}
      .badge.art.out{background:var(--error-color,#e53935);color:#fff}
      .entry{display:flex;gap:12px;padding:8px 0;border-bottom:1px solid var(--divider-color)}
      .entry:last-child{border-bottom:0}
      .entry.cancelled{border-left:3px solid var(--error-color,#e53935);padding-left:9px;margin-left:-12px}
      .lesson{min-width:44px;color:var(--secondary-text-color);font-variant-numeric:tabular-nums;white-space:nowrap;padding-top:1px}
      .body{flex:1;min-width:0}
      .line{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
      .subject{font-weight:600}
      .entry.cancelled .subject{text-decoration:line-through;text-decoration-thickness:1px}
      .details{color:var(--secondary-text-color);font-size:.88rem;margin-top:2px}
      .was{text-decoration:line-through;opacity:.7}
      .hint{color:var(--secondary-text-color);font-size:.85rem;font-style:italic;margin-top:3px}
      .note{border-left:3px solid var(--primary-color);padding:2px 0 2px 9px;margin-bottom:8px;color:var(--secondary-text-color);font-size:.88rem}
      .empty{color:var(--secondary-text-color)}
      .empty.small{font-size:.9rem;padding:4px 0}
      .footer{margin-top:10px;color:var(--secondary-text-color);font-size:.78rem}
    `;
  }

  _norm(value) {
    return String(value ?? "")
      .trim()
      .toLowerCase()
      .replace(/ä/g, "a")
      .replace(/ö/g, "o")
      .replace(/ü/g, "u")
      .replace(/ß/g, "ss")
      .replace(/[^a-z0-9]+/g, "");
  }

  _escape(value) {
    const div = document.createElement("div");
    div.textContent = String(value ?? "");
    return div.innerHTML;
  }

  _escapeAttr(value) {
    return this._escape(value).replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
}

if (!customElements.get("sph-vertretungsplan-card")) {
  customElements.define("sph-vertretungsplan-card", SphVertretungsplanCard);
}
window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "sph-vertretungsplan-card")) {
  window.customCards.push({
    type: "sph-vertretungsplan-card",
    name: "SPH Vertretungsplan",
    description: "Vertretungen, Raumwechsel und Ausfälle aus dem Schulportal Hessen",
  });
}
