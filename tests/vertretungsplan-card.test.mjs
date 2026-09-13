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
  "sph-vertretungsplan-card.js"
);

function makeSandbox() {
  const registry = new Map();
  const escapeElement = {
    set textContent(value) { this._text = value; },
    get innerHTML() {
      return String(this._text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    },
  };
  class HTMLElement {
    attachShadow() {
      this.shadowRoot = { innerHTML: "" };
      return this.shadowRoot;
    }
  }
  const sandbox = {
    HTMLElement,
    document: { createElement: () => Object.create(escapeElement) },
    customElements: {
      get: (name) => registry.get(name),
      define: (name, cls) => registry.set(name, cls),
    },
    window: {}, Intl, Date, Number, Array, Object, String, console,
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  return { sandbox, registry };
}

const PLAN = {
  kind: "Maxim",
  "kind_kürzel": "Mk",
  aktualisiert: "2026-08-26T07:11:02",
  wird_aktualisiert: false,
  tage: [
    {
      datum: "2026-08-26",
      datum_de: "26.08.2026",
      wochentag: "Mittwoch",
      relativ: "heute",
      woche: "A-Woche",
      hinweise: ["Der Schulhof ist gesperrt."],
      eintraege: [
        {
          stunde: "5", klasse: "05cG", vertreter: "NN", lehrer: "",
          art: "Vertr", art_lang: "Vertretung", fach: "ETH", fach_lang: "Ethik",
          raum: "Spie", raum_alt: "b302", hinweis: "Spieleraum Ethikgruppe",
          stunden: [5], von_stunde: 5, bis_stunde: 5, entfall: false,
        },
        {
          stunde: "1 - 2", klasse: "05cG", vertreter: "", lehrer: "MUE",
          art: "Entf.", art_lang: "Entfall", fach: "M", fach_lang: "Mathematik",
          raum: "", raum_alt: "", hinweis: "", stunden: [1, 2],
          von_stunde: 1, bis_stunde: 2, entfall: true,
        },
      ],
    },
    {
      datum: "2026-08-27", datum_de: "27.08.2026", wochentag: "Donnerstag",
      relativ: "morgen", woche: "A-Woche", hinweise: [], eintraege: [],
    },
  ],
};

function buildCard(config, states) {
  const { sandbox, registry } = makeSandbox();
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(CARD, "utf8"), sandbox);
  const Card = registry.get("sph-vertretungsplan-card");
  const card = new Card();
  card.setConfig(config);
  card.hass = { states };
  return { card, html: card.shadowRoot.innerHTML };
}

const states = {
  "sensor.vertretungsplan_maxim_mk": {
    entity_id: "sensor.vertretungsplan_maxim_mk",
    attributes: PLAN,
  },
};

test("Vertretungsplan card renders normalized entries and filters", () => {
  const { html, card } = buildCard(
    { entity: "sensor.vertretungsplan_maxim_mk", title: "Vertretungsplan Maxim" },
    states
  );
  assert.match(html, /header="Vertretungsplan Maxim"/);
  assert.match(html, /26\.08\.2026/);
  assert.match(html, /27\.08\.2026/);
  assert.match(html, />Ethik</);
  assert.match(html, />Mathematik</);
  assert.match(html, /1\.–2\./);
  assert.match(html, /class="entry cancelled"/);
  assert.match(html, />Vertretung</);
  assert.doesNotMatch(html, />Vertr</);
  assert.match(html, /class="was">statt b302/);
  assert.ok(card.getCardSize() > 1);

  const onlyCancelled = buildCard(
    { entity: "sensor.vertretungsplan_maxim_mk", only_cancellations: true },
    states
  ).html;
  assert.match(onlyCancelled, /Mathematik/);
  assert.doesNotMatch(onlyCancelled, /Ethik/);

  const hideEmpty = buildCard(
    { entity: "sensor.vertretungsplan_maxim_mk", hide_empty: true },
    states
  ).html;
  assert.doesNotMatch(hideEmpty, /27\.08\.2026/);
});

test("Vertretungsplan card can select sensor by child shortcut", () => {
  const { html } = buildCard({ child: "Mk" }, states);
  assert.match(html, /26\.08\.2026/);
});
