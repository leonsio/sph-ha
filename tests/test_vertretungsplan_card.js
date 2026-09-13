/** Offline regression test for the Vertretungsplan Lovelace card. */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const CARD = path.join(__dirname, "..", "custom_components", "sph", "static", "sph-vertretungsplan-card.js");

function makeSandbox() {
  const registry = new Map();
  const escapeElement = {
    set textContent(value) { this._text = value; },
    get innerHTML() {
      return String(this._text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    },
  };
  class HTMLElement {
    attachShadow() { this.shadowRoot = { innerHTML: "" }; return this.shadowRoot; }
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
      datum: "2026-08-26", datum_de: "26.08.2026", wochentag: "Mittwoch",
      relativ: "heute", woche: "A-Woche", hinweise: ["Der Schulhof ist gesperrt."],
      eintraege: [
        {
          stunde: "5", klasse: "05cG", vertreter: "NN", lehrer: "", art: "Vertr",
          art_lang: "Vertretung", fach: "ETH", fach_lang: "Ethik", raum: "Spie",
          raum_alt: "b302", hinweis: "Spieleraum Ethikgruppe", stunden: [5],
          von_stunde: 5, bis_stunde: 5, entfall: false,
        },
        {
          stunde: "1 - 2", klasse: "05cG", vertreter: "", lehrer: "MUE", art: "Entf.",
          art_lang: "Entfall", fach: "M", fach_lang: "Mathematik", raum: "", raum_alt: "",
          hinweis: "", stunden: [1, 2], von_stunde: 1, bis_stunde: 2, entfall: true,
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

const failures = [];
function check(label, condition) { if (!condition) failures.push(`  ${label}`); }

const states = {
  "sensor.vertretungsplan_maxim_mk": {
    entity_id: "sensor.vertretungsplan_maxim_mk",
    attributes: PLAN,
  },
};

{
  const { html, card } = buildCard(
    { entity: "sensor.vertretungsplan_maxim_mk", title: "Vertretungsplan Maxim" }, states
  );
  check("Titel", html.includes('header="Vertretungsplan Maxim"'));
  check("Tage", html.includes("26.08.2026") && html.includes("27.08.2026"));
  check("Fächer", html.includes(">Ethik<") && html.includes(">Mathematik<"));
  check("Stundenbereich", html.includes("1.–2."));
  check("Entfall", html.includes('class="entry cancelled"') && html.includes('badge art out'));
  check("Art normalisiert", html.includes(">Vertretung<") && !html.includes(">Vertr<"));
  check("Alter Raum", html.includes('class="was">statt b302'));
  check("Hinweis", html.includes("Der Schulhof ist gesperrt."));
  check("Leerer Tag", html.includes("Keine Einträge"));
  check("Kartengröße", card.getCardSize() > 1);
}

{
  const { html } = buildCard(
    { entity: "sensor.vertretungsplan_maxim_mk", only_cancellations: true }, states
  );
  check("Nur Entfälle", html.includes("Mathematik") && !html.includes("Ethik"));
}

{
  const { html } = buildCard(
    { entity: "sensor.vertretungsplan_maxim_mk", hide_empty: true }, states
  );
  check("Leere Tage ausblenden", !html.includes("27.08.2026"));
}

{
  const { html } = buildCard({ child: "Mk" }, states);
  check("Sensor über Kind", html.includes("26.08.2026"));
}

if (failures.length) {
  console.log("FEHLGESCHLAGEN:\n" + failures.join("\n"));
  process.exit(1);
}
console.log("OK — Vertretungsplan-Karte rendert und filtert korrekt.");
