import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CARD = path.join(
  __dirname,
  "..",
  "custom_components",
  "sph",
  "static",
  "sph-nachrichten-card.js"
);

function loadCard() {
  const registry = new Map();
  class HTMLElement {
    attachShadow() {
      this.shadowRoot = { innerHTML: "" };
      return this.shadowRoot;
    }
  }
  const sandbox = {
    HTMLElement,
    customElements: {
      get: (name) => registry.get(name),
      define: (name, cls) => registry.set(name, cls),
    },
    Intl, Date, Number, Array, Object, String, Math, console,
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(CARD, "utf8"), sandbox);
  return { Card: registry.get("sph-nachrichten-card"), sandbox };
}

const ENTITY = "sensor.nachrichten_ungelesen_maxim_mk";
const PORTAL = "https://start.schulportal.hessen.de/nachrichten.php";

const PAYLOAD = {
  ungelesen: 2,
  abgerufen: "2026-11-23T10:00:00+00:00",
  aktiv: true,
  letzter_abruf_ok: true,
  portal_url: PORTAL,
  nachrichten: [
    { id: "a", betreff: "Elternabend <b>heute</b>", absender: "Muster, Erika", datum: "2026-11-23T08:00:00+00:00", datum_text: "", ungelesen: true },
    { id: "b", betreff: "Gelesene Info", absender: "Beispiel, Max", datum: "2026-11-20T08:00:00+00:00", datum_text: "", ungelesen: false },
    { id: "c", betreff: "Fundsachen", absender: "Metze, Julia", datum: "2026-11-10T08:00:00+00:00", datum_text: "", ungelesen: true },
  ],
};

function states(extra = {}) {
  return {
    [ENTITY]: {
      entity_id: ENTITY,
      state: "2",
      last_updated: "2026-11-23T10:00:01+00:00",
      attributes: { kind: "Maxim", "kind_kürzel": "Mk", portal_url: PORTAL },
    },
    ...extra,
  };
}

async function render(config, { payload = PAYLOAD, fail = false, hassStates = states() } = {}) {
  const { Card } = loadCard();
  const card = new Card();
  card.setConfig(config);
  const calls = [];
  card.hass = {
    states: hassStates,
    callWS: async (msg) => {
      calls.push(msg);
      if (fail) throw new Error("boom");
      return payload;
    },
  };
  await new Promise((resolve) => setImmediate(resolve));
  return { card, html: card.shadowRoot.innerHTML, calls };
}

test("lists only unread messages by default, escaped, linking to the portal", async () => {
  const { html, calls } = await render({ entity: ENTITY });
  // Objects from the vm sandbox have a foreign prototype; compare as JSON.
  assert.equal(JSON.stringify(calls), JSON.stringify([{ type: "sph/nachrichten", entity_id: ENTITY }]));
  assert.match(html, /Nachrichten Maxim/);
  assert.match(html, /class="badge ">2</);
  assert.match(html, /Elternabend &lt;b&gt;heute&lt;\/b&gt;/);
  assert.match(html, /Fundsachen/);
  assert.doesNotMatch(html, /Gelesene Info/);
  assert.match(html, new RegExp(`href="${PORTAL.replace(/[.?]/g, "\\$&")}" target="_blank" rel="noopener noreferrer"`));
  assert.match(html, /Im Schulportal öffnen/);
});

test("show_read and max options", async () => {
  const all = (await render({ entity: ENTITY, show_read: true })).html;
  assert.match(all, /Gelesene Info/);
  const one = (await render({ entity: ENTITY, max: 1 })).html;
  assert.match(one, /Elternabend/);
  assert.doesNotMatch(one, /Fundsachen/);
});

test("empty, disabled and error states", async () => {
  const empty = await render({ entity: ENTITY }, { payload: { ...PAYLOAD, ungelesen: 0, nachrichten: [] } });
  assert.match(empty.html, /Keine ungelesenen Nachrichten\./);
  assert.match(empty.html, /class="badge zero">0</);

  const disabled = await render({ entity: ENTITY }, { payload: { ...PAYLOAD, aktiv: false } });
  assert.match(disabled.html, /deaktiviert/);

  const failed = await render({ entity: ENTITY }, { fail: true });
  assert.match(failed.html, /class="empty error">boom</);
});

test("finds the sensor via child or automatically, and reports a missing sensor", async () => {
  assert.equal((await render({ child: "mk" })).calls[0].entity_id, ENTITY);
  assert.equal((await render({})).calls[0].entity_id, ENTITY);
  const missing = await render({ child: "xy" });
  assert.equal(missing.calls.length, 0);
  assert.match(missing.html, /Kein SPH-Nachrichten-Sensor gefunden/);
});

test("reloads only when the sensor changed", async () => {
  const { card, calls } = await render({ entity: ENTITY });
  card.hass = { states: states(), callWS: async (msg) => { calls.push(msg); return PAYLOAD; } };
  assert.equal(calls.length, 1);
  const changed = states();
  changed[ENTITY] = { ...changed[ENTITY], last_updated: "2026-11-24T10:00:00+00:00" };
  card.hass = { states: changed, callWS: async (msg) => { calls.push(msg); return PAYLOAD; } };
  assert.equal(calls.length, 2);
});

test("explains the state before the first poll and shows the fetch time", async () => {
  const before = await render({ entity: ENTITY }, { payload: { ...PAYLOAD, abgerufen: null, nachrichten: [] } });
  assert.match(before.html, /Noch kein Abruf erfolgt\./);
  const after = await render({ entity: ENTITY });
  assert.match(after.html, /Stand \d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}/);
});

test("re-renders relative dates after midnight without reloading", async () => {
  const { card, calls } = await render({ entity: ENTITY });
  card._renderedDay = "yesterday";
  card.shadowRoot.innerHTML = "";
  card.hass = { states: states(), callWS: async (msg) => { calls.push(msg); return PAYLOAD; } };
  assert.equal(calls.length, 1);
  assert.match(card.shadowRoot.innerHTML, /Elternabend/);
});

test("ignores an older answer that arrives after a newer one", async () => {
  const { Card } = loadCard();
  const card = new Card();
  card.setConfig({ entity: ENTITY });
  const pending = [];
  const callWS = () => new Promise((resolve) => pending.push(resolve));
  card.hass = { states: states(), callWS };
  const changed = states();
  changed[ENTITY] = { ...changed[ENTITY], last_updated: "2026-11-24T10:00:00+00:00" };
  card.hass = { states: changed, callWS };
  pending[1]({ ...PAYLOAD, nachrichten: [{ ...PAYLOAD.nachrichten[0], betreff: "Neuer Stand" }] });
  await new Promise((resolve) => setImmediate(resolve));
  pending[0]({ ...PAYLOAD, nachrichten: [{ ...PAYLOAD.nachrichten[0], betreff: "Alter Stand" }] });
  await new Promise((resolve) => setImmediate(resolve));
  assert.match(card.shadowRoot.innerHTML, /Neuer Stand/);
  assert.doesNotMatch(card.shadowRoot.innerHTML, /Alter Stand/);
});

test("does not re-render on every update when no sensor exists", async () => {
  const { card, html } = await render({ child: "xy" });
  card.shadowRoot.innerHTML = "untouched";
  card.hass = { states: states(), callWS: async () => PAYLOAD };
  assert.equal(card.shadowRoot.innerHTML, "untouched");
  assert.match(html, /Kein SPH-Nachrichten-Sensor gefunden/);
});
