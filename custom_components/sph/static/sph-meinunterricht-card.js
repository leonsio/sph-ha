class SphMeinUnterrichtCard extends HTMLElement {
  setConfig(config) {
    this.config = config || {};
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
  }

  set hass(hass) {
    this._hass = hass;
    const entity = this._findEntity();

    // Home Assistant invokes the hass setter for unrelated state changes too.
    // Do not rebuild the Shadow DOM unless this card's entity actually changed.
    // This is essential for stable horizontal scrolling, dialogs and text input.
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
        state.entity_id.startsWith("sensor.mein_unterricht_") &&
        !state.entity_id.endsWith("_json") &&
        String(state.attributes?.kind_kürzel || "").trim().toLowerCase() === child
      );
      if (match) return match;
    }

    return Object.values(hass.states).find(state =>
      state.entity_id.startsWith("sensor.mein_unterricht_") &&
      !state.entity_id.endsWith("_json") &&
      Array.isArray(state.attributes?.aufgaben)
    ) || null;
  }

  _captureUiState() {
    const wrap = this.shadowRoot?.querySelector(".table-wrap");
    const dialog = this.shadowRoot?.querySelector("dialog");
    const form = dialog?.querySelector("form");
    const active = this.shadowRoot?.activeElement;
    const values = {};

    if (form) {
      Array.from(form.elements).forEach(field => {
        if (!field?.name) return;
        values[field.name] = {
          value: field.value,
          checked: field.type === "checkbox" ? field.checked : undefined,
        };
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

    Object.entries(state.values || {}).forEach(([name, saved]) => {
      const field = form.elements.namedItem(name);
      if (!field) return;
      if (field.type === "checkbox") field.checked = Boolean(saved?.checked);
      else if ("value" in field) field.value = saved?.value ?? "";
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
            // Date and checkbox inputs do not support text selections.
          }
        }
      });
    }
  }

  _render(entity = this._findEntity()) {
    if (!this.shadowRoot || !this._hass) return;

    const uiState = this._captureUiState();
    const items = Array.isArray(entity?.attributes?.aufgaben)
      ? [...entity.attributes.aufgaben]
      : [];
    items.sort((a, b) =>
      String(a.datum || "").localeCompare(String(b.datum || "")) ||
      String(a.fach || a.kurs || "").localeCompare(String(b.fach || b.kurs || "")) ||
      String(a.aufgabe || "").localeCompare(String(b.aufgabe || ""))
    );

    const title = this.config?.title || "Mein Unterricht – Hausaufgaben";
    const header = ` header="${this._esc(title)}"`;

    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        .content { padding:12px 16px 16px; }
        .toolbar { display:flex; justify-content:flex-end; margin-bottom:12px; }
        button { cursor:pointer; }
        .add { border:0; border-radius:8px; padding:8px 12px; background:var(--primary-color); color:var(--text-primary-color); font-weight:600; }
        .delete { border:0; background:transparent; color:var(--error-color,#d32f2f); font-size:1.1rem; padding:4px 8px; }
        .table-wrap { overflow-x:auto; overscroll-behavior-x:contain; }
        table { width:100%; border-collapse:collapse; min-width:980px; }
        th, td { text-align:left; padding:8px 7px; border-bottom:1px solid var(--divider-color); vertical-align:top; }
        th { font-weight:700; color:var(--secondary-text-color); }
        .task { white-space:pre-wrap; min-width:260px; }
        .source, .status { white-space:nowrap; }
        .manual { font-weight:600; }
        .done { color:var(--success-color,#2e7d32); }
        .open { color:var(--warning-color,#ed6c02); }
        .empty, .error { color:var(--secondary-text-color); padding:10px 0; }
        dialog { color:var(--primary-text-color); background:var(--card-background-color,var(--ha-card-background)); border:0; border-radius:12px; padding:0; box-shadow:var(--ha-card-box-shadow,0 4px 18px rgba(0,0,0,.3)); width:min(620px,calc(100vw - 32px)); }
        dialog::backdrop { background:rgba(0,0,0,.45); }
        form { padding:18px; }
        h3 { margin:0 0 14px; }
        .fields { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
        label { display:flex; flex-direction:column; gap:5px; font-size:.9rem; }
        label.full { grid-column:1/-1; }
        label.check { flex-direction:row; align-items:center; gap:8px; }
        input, textarea { box-sizing:border-box; width:100%; padding:9px; border:1px solid var(--divider-color); border-radius:7px; background:var(--card-background-color,var(--ha-card-background)); color:var(--primary-text-color); font:inherit; }
        textarea { min-height:88px; resize:vertical; }
        input[type="checkbox"] { width:auto; }
        .hint { grid-column:1/-1; color:var(--secondary-text-color); font-size:.82rem; }
        .actions { display:flex; justify-content:flex-end; gap:8px; margin-top:18px; }
        .secondary { border:1px solid var(--divider-color); border-radius:8px; padding:8px 12px; background:transparent; color:var(--primary-text-color); }
        @media(max-width:600px){ .fields { grid-template-columns:1fr; } label.full, .hint { grid-column:auto; } }
      </style>
      <ha-card${header}>
        <div class="content">
          ${entity ? `
            <div class="toolbar"><button class="add" type="button">+ Hausaufgabe hinzufügen</button></div>
            ${items.length ? `<div class="table-wrap"><table>
              <thead><tr><th>Datum</th><th>Fach/Kurs</th><th>Thema</th><th>Hausaufgabe</th><th>Lehrer</th><th>Status</th><th>Quelle</th><th></th></tr></thead>
              <tbody>${items.map(item => this._row(item)).join("")}</tbody>
            </table></div>` : `<div class="empty">Keine Hausaufgaben vorhanden.</div>`}
            ${this._dialog()}
          ` : `<div class="error">Kein Mein-Unterricht-Sensor gefunden.</div>`}
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
    const done = Boolean(item.erledigt);
    const subject = item.kurs || item.fach || "";
    return `<tr>
      <td>${this._esc(this._formatDate(item.datum))}</td>
      <td>${this._esc(subject)}</td>
      <td>${this._esc(item.thema || "")}</td>
      <td class="task">${this._esc(item.aufgabe || "")}</td>
      <td>${this._esc(item.lehrer || "")}</td>
      <td class="status ${done ? "done" : "open"}">${done ? "Erledigt" : "Offen"}</td>
      <td class="source ${manual ? "manual" : ""}">${manual ? "Manuell" : "SPH"}</td>
      <td>${manual ? `<button class="delete" type="button" title="Hausaufgabe löschen" data-id="${this._esc(item.id || "")}">✕</button>` : ""}</td>
    </tr>`;
  }

  _dialog() {
    const today = new Date();
    const localDate = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;
    return `<dialog>
      <form method="dialog">
        <h3>Hausaufgabe hinzufügen</h3>
        <div class="fields">
          <label>Datum<input name="datum" type="date" value="${localDate}" required></label>
          <label>Fach<input name="fach" type="text" placeholder="Englisch" required></label>
          <label>Kurs<input name="kurs" type="text" placeholder="optional"></label>
          <label>Lehrer<input name="lehrer" type="text" placeholder="optional"></label>
          <label class="full">Thema<input name="thema" type="text" placeholder="optional"></label>
          <label class="full">Hausaufgabe<textarea name="aufgabe" placeholder="Aufgabe" required></textarea></label>
          <label class="check full"><input name="erledigt" type="checkbox"> Bereits erledigt</label>
          <div class="hint">Manuell angelegte Hausaufgaben werden sieben Tage nach dem eingetragenen Datum automatisch gelöscht.</div>
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
      fach: data.fach,
      kurs: data.kurs || "",
      thema: data.thema || "",
      aufgabe: data.aufgabe,
      lehrer: data.lehrer || "",
      erledigt: data.erledigt === "on",
    };
    try {
      await this._hass.callService("sph", "meinunterricht_hausaufgabe_hinzufuegen", payload);
      this.shadowRoot.querySelector("dialog")?.close();
      form.reset();
    } catch (err) {
      console.error("SPH: Hausaufgabe konnte nicht hinzugefügt werden", err);
    }
  }

  async _delete(entityId, id) {
    if (!id || !window.confirm("Diese manuell hinzugefügte Hausaufgabe löschen?")) return;
    try {
      await this._hass.callService("sph", "meinunterricht_hausaufgabe_loeschen", { entity_id: entityId, id });
    } catch (err) {
      console.error("SPH: Hausaufgabe konnte nicht gelöscht werden", err);
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

if (!customElements.get("sph-meinunterricht-card")) {
  customElements.define("sph-meinunterricht-card", SphMeinUnterrichtCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some(card => card.type === "sph-meinunterricht-card")) {
  window.customCards.push({
    type: "sph-meinunterricht-card",
    name: "SPH Mein Unterricht",
    description: "Hausaufgaben tabellarisch anzeigen und lokale Hausaufgaben verwalten",
  });
}
