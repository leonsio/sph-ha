import test from 'node:test';
import assert from 'node:assert/strict';

const registry = new Map();
globalThis.customElements = {
  get: name => registry.get(name),
  define: (name, klass) => registry.set(name, klass),
};
globalThis.document = {
  createElement: () => ({
    set textContent(value) { this.innerHTML = String(value ?? ''); },
  }),
};
globalThis.HTMLElement = class {};
globalThis.window = {
  customCards: [],
  clearInterval: () => {},
  setInterval: () => 1,
};

await import('../custom_components/sph/static/sph-meinunterricht-card.js?v=0.5.2');
const Card = registry.get('sph-meinunterricht-card');

const rowFor = item => new Card()._row({
  datum: '2026-09-04',
  thema: '',
  aufgabe: '',
  lehrer: '',
  erledigt: false,
  quelle: 'sph',
  ...item,
});

test('Mein Unterricht card prefers normalized fach over raw kurs', () => {
  const row = rowFor({ fach: 'Deutsch', kurs: 'Deutsch 7n' });
  assert.match(row, /<td>Deutsch<\/td>/);
  assert.doesNotMatch(row, /<td>Deutsch 7n<\/td>/);
});

test('Mein Unterricht card falls back to kurs when fach is missing', () => {
  const row = rowFor({ fach: '', kurs: 'Musik 7n' });
  assert.match(row, /<td>Musik 7n<\/td>/);
});
