import { test } from 'node:test';
import assert from 'node:assert/strict';
import { atrasados } from '../scripts/vigia.mjs';

const ahora = Date.parse('2026-11-02T20:00:00Z');

test('el vigía solo protesta por datos atrasados o ilegibles', () => {
  assert.deepEqual(atrasados({
    'infrarrojo.json': '2026-11-02T19:10:00Z', 'actual.json': '2026-11-02T18:00:00Z',
  }, ahora), []);
  assert.deepEqual(atrasados({
    'infrarrojo.json': '2026-11-02T18:50:00Z', 'actual.json': '2026-11-02T17:00:00Z',
  }, ahora), ['infrarrojo.json: tiene 70 min (límite 60)', 'actual.json: tiene 180 min (límite 150)']);
  assert.deepEqual(atrasados({ 'infrarrojo.json': null, 'actual.json': '2026-11-02T19:00:00Z' }, ahora),
    ['infrarrojo.json: no se pudo leer']);
});
