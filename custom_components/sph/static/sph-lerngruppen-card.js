class SphLerngruppenCard extends HTMLElement {
  setConfig(config) {
    this.config = config || {};
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
  }

  set hass(hass) {
    this._hass = hass;
    const entity = this._findEntity();

    // Home Assistant calls the hass setter for many unrelated state changes.
    // Do not rebuild the Shadow DOM unless this card's own entity changed.
    // Replacing the DOM on every hass update resets horizontal scrolling,
    // closes dialogs and interrupts text input/focus.
    if (this._renderedEntity === entity && this.shadowRoot?.childNodes?.length) {
      return;
    }

    this._render(entity);
  }

  _findEntity() {
    const hass = this._hass;
    if (!hass) return null;
    const configured = this.config?.entity || this.config?.sensor;
    if (configured && hass.states[configured]) return hass.states[configured];

    const child = String(this.config?.child || "").trim().toLowerCase();
    if (child) {
      const match = Object.values(hass.states).find(state =>
        state.entity_id.startsWith("sensor.lerngruppen_") &&
        !state.entity_id.endsWith("_json") &&
        String(state.attributes?.kind_kürzel || "").trim().toLowerCase() === child
      );
      if (match) return match;
    }

    return Object.values(hass.states).find(state =>
      state.entity_id.startsWith("sensor.lerngruppen_") &&
      !state.entity_id.endsWith("_json") &&
      Array.isArray(state.attributes?.leistungskontrollen)
    ) || null;
  }

  _captureUiState() {
    const wrap = this.shadowRoot?.querySelector(".table-wrap");
    const dialog = this.shadowRoot?.querySelector("dialog");
    const form = dialog?.querySelector("form");
    const active = this.shadowRoot?.activeElement;
    const values = {};

    if (form) {
      new FormData(form).forEach((value, key) => {
        values[key] = value;
      });
    }

    return {
      scrollLeft: wrap?.scrollLeft || 0,
      dialogOpen: Boolean(dialog?.open),
      values,
      activeName: active?.name || "",
      selectionStart: typeof active?.selectionStart === "number" ? active.selectionStart : null,
      selectionEnd: typeof active?.selectionEnd === "number" ? active.selectionEnd : null,
    };
  }

  _restoreUiState(state) {
    if (!state) return;

    const wrap = this.shadowRoot?.querySelector(".table-wrap");
    if (wrap) wrap.scrollLeft = state.scrollLeft || 0;

    if (!state.dialogOpen) return;

    const dialog = this.shadowRoot?.querySelector("dialog");
    const form = dialog?.querySelector("form");
    if (!dialog || !form) return;

    Object.entries(state.values || {}).forEach(([name, value]) => {
      const field = form.elements.namedItem(name);
      if (field && "value" in field) field.value = value;
    });

    if (!dialog.open) dialog.showModal();

    if (state.activeName) {
      queueMicrotask(() => {
        const field = form.elements.namedItem(state.activeName);
        if (!field || typeof field.focus !== "function") return;
        field.focus();
        if (
          typeof field.setSelectionRange === "function" &&
          state.selectionStart !== null &&
          state.selectionEnd !== null
        ) {
          try {
            field.setSelectionRange(state.selectionStart, state.selectionEnd);
          } catch (_err) {
            // Some input types such as date/number do not support selections.
          }
        }
      });
    }
  }

  _render(entity = this._findEntity()) {
    if (!this.shadowRoot || !this._hass) return;

    // Preserve interaction state even when the Lerngruppen sensor itself is
    // updated while the user is scrolling or editing the dialog.
    const uiState = this._captureUiState();
    const items = Array.isArray(entity?.attributes?.leistungskontrollen)
      ? [...entity.attributes.leistungskontrollen]
      : [];
    items.sort((a, b) => String(a.datum || "").localeCompare(String(b.datum || "")) || String(a.summary || "").localeCompare(String(b.summary || "")));

    const title = this.config?.title || "Lerngruppen – Leistungskontrollen";
    const header = ` header="${this._esc(title)}"`;

    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        .content { padding: 12px 16px 16px; }
        .toolbar { display:flex; justify-content:flex-end; margin-bottom:12px; }
        button { cursor:pointer; }
        .add { border:0; border-radius:8px; padding:8px 12px; background:var(--primary-color); color:var(--text-primary-color); font-weight:600; }
        .delete { border:0; background:transparent; color:var(--error-color,#d32f2f); font-size:1.1rem; padding:4px 8px; }
        .table-wrap { overflow-x:auto; }
        table { width:100%; border-collapse:collapse; min-width:760px; }
        th, td { text-align:left; padding:8px 7px; border-bottom:1px solid var(--divider-color); vertical-align:top; }
        th { font-weight:700; color:var(--secondary-text-color); }
        .source { white-space:nowrap; }
        .manual { font-weight:600; }
        .empty, .error { color:var(--secondary-text-color); padding:10px 0; }
        dialog { color:var(--primary-text-color); background:var(--card-background-color,var(--ha-card-background)); border:0; border-radius:12px; padding:0; box-shadow:var(--ha-card-box-shadow,0 4px 18px rgba(0,0,0,.3)); width:min(520px,calc(100vw - 32px)); }
        dialog::backdrop { background:rgba(0,0,0,.45); }
        form { padding:18px; }
        h3 { margin:0 0 14px; }
        .fields { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
        label { display:flex; flex-direction:column; gap:5px; font-size:.9rem; }
        label.full { grid-column:1/-1; }
        input { box-sizing:border-box; width:100%; padding:9px; border:1px solid var(--divider-color); border-radius:7px; background:var(--card-background-color,var(--ha-card-background)); color:var(--primary-text-color); }
        .actions { display:flex; justify-content:flex-end; gap:8px; margin-top:18px; }
        .secondary { border:1px solid var(--divider-color); border-radius:8px; padding:8px 12px; background:transparent; color:var(--primary-text-color); }
        @media(max-width:600px){ .fields { grid-template-columns:1fr; } label.full { grid-column:auto; } }
      </style>
      <ha-card${header}>
        <div class="content">
          ${entity ? `
            <div class="toolbar"><button class="add" type="button">+ Termin hinzufügen</button></div>
            ${items.length ? `<div class="table-wrap"><table>
              <thead><tr><th>Datum</th><th>Art</th><th>Fach/Kurs</th><th>Dauer</th><th>Stunden</th><th>Lehrkraft</th><th>Quelle</th><th></th></tr></thead>
              <tbody>${items.map(item => this._row(item)).join("")}</tbody>
            </table></div>` : `<div class="empty">Keine Leistungskontrollen vorhanden.</div>`}
            ${this._dialog()}
          ` : `<div class="error">Kein Lerngruppen-Sensor gefunden.</div>`}
        </div>
      </ha-card>`;

    this._renderedEntity = entity;

    if (!entity) return;
    this.shadowRoot.querySelector(".add")?.addEventListener("click", () => {
      const dialog = this.shadowRoot.querySelector("dialog");
      if (dialog) dialog.showModal();
    });
    this.shadowRoot.querySelector(".cancel")?.addEventListener("click", () => this.shadowRoot.querySelector("dialog")?.close());
    this.shadowRoot.querySelector("form")?.addEventListener("submit", event => this._submit(event, entity.entity_id));
    this.shadowRoot.querySelectorAll(".delete").forEach(button => {
      button.addEventListener("click", () => this._delete(entity.entity_id, button.dataset.id));
    });

    this._restoreUiState(uiState);
  }

  _row(item) {
    const manual = String(item.quelle || "").toLowerCase() === "manuell";
    const duration = item.dauer_minuten == null ? "" : `${item.dauer_minuten} Min`;
    const periods = Array.isArray(item.stunden) ? item.stunden.join(", ") : (item.stunden_text || "");
    return `<tr>
      <td>${this._esc(this._formatDate(item.datum))}</td>
      <td>${this._esc(item.art || "")}</td>
      <td>${this._esc(item.kurs || "")}</td>
      <td>${this._esc(duration)}</td>
      <td>${this._esc(periods)}</td>
      <td>${this._esc(item.lehrkraft || "")}</td>
      <td class="source ${manual ? "manual" : ""}">${manual ? "Manuell" : "SPH"}</td>
      <td>${manual ? `<button class="delete" type="button" title="Termin löschen" data-id="${this._esc(item.id || "")}">✕</button>` : ""}</td>
    </tr>`;
  }

  _dialog() {
    const today = new Date();
    const localDate = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;
    return `<dialog>
      <form method="dialog">
        <h3>Termin hinzufügen</h3>
        <div class="fields">
          <label>Datum<input name="datum" type="date" value="${localDate}" required></label>
          <label>Art<input name="art" type="text" placeholder="Arbeit" required></label>
          <label class="full">Fach/Kurs<input name="kurs" type="text" placeholder="Englisch" required></label>
          <label>Dauer (Min)<input name="dauer_minuten" type="number" min="1" max="1440" placeholder="60"></label>
          <label>Stunden<input name="stunden" type="text" placeholder="3,4"></label>
          <label class="full">Lehrkraft<input name="lehrkraft" type="text" placeholder="optional"></label>
        </div>
        <div class="actions">
          <button class="secondary cancel" type="button">Abbrechen</button>
          <button class="add" type="submit">Speichern</button>
        </div>
      </form>
    </dialog>`;
  }

  async _submit(event, entityId) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    const payload = {
      entity_id: entityId,
      datum: data.datum,
      art: data.art,
      kurs: data.kurs,
      stunden: data.stunden || "",
      lehrkraft: data.lehrkraft || "",
    };
    if (String(data.dauer_minuten || "").trim()) payload.dauer_minuten = Number(data.dauer_minuten);
    try {
      await this._hass.callService("sph", "lerngruppen_termin_hinzufuegen", payload);
      this.shadowRoot.querySelector("dialog")?.close();
      form.reset();
    } catch (err) {
      console.error("SPH: Lerngruppen-Termin konnte nicht hinzugefügt werden", err);
    }
  }

  async _delete(entityId, id) {
    if (!id || !window.confirm("Diesen manuell hinzugefügten Termin löschen?")) return;
    try {
      await this._hass.callService("sph", "lerngruppen_termin_loeschen", { entity_id: entityId, id });
    } catch (err) {
      console.error("SPH: Lerngruppen-Termin konnte nicht gelöscht werden", err);
    }
  }

  _formatDate(value) {
    const text = String(value || "");
    const match = text.match(/^(\d{4})-(\d{2})-(\d{2})/);
    return match ? `${match[3]}.${match[2]}.${match[1]}` : text;
  }

  _esc(value) {
    const div = document.createElement("div");
    div.textContent = String(value ?? "");
    return div.innerHTML;
  }

  getCardSize() { return 6; }
}

if (!customElements.get("sph-lerngruppen-card")) {
  customElements.define("sph-lerngruppen-card", SphLerngruppenCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some(card => card.type === "sph-lerngruppen-card")) {
  window.customCards.push({
    type: "sph-lerngruppen-card",
    name: "SPH Lerngruppen",
    description: "Leistungskontrollen anzeigen und lokale Termine verwalten",
  });
}
