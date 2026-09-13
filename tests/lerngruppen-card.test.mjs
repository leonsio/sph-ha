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

await import('../custom_components/sph/static/sph-lerngruppen-card.js?subject-normalization-test');
const Card = registry.get('sph-lerngruppen-card');

const rowFor = item => new Card()._row({
  datum: '2026-09-18',
  art: 'Arbeit',
  dauer_minuten: 45,
  stunden: [1],
  lehrkraft: '',
  quelle: 'sph',
  ...item,
});

test('Lerngruppen card prefers normalized fach over course name', () => {
  const row = rowFor({ fach: 'Deutsch', kurs: 'Deutsch 7n' });
  assert.match(row, /<td>Deutsch<\/td>/);
  assert.doesNotMatch(row, /<td>Deutsch 7n<\/td>/);
});

test('Lerngruppen card falls back to kurs for older payloads', () => {
  const row = rowFor({ fach: '', kurs: 'Musik 7n' });
  assert.match(row, /<td>Musik 7n<\/td>/);
});
