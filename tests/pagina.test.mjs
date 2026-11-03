import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { urlEnsamble, urlModelos, urlOpenMeteo } from '../assets/openmeteo.js';

const leer = (ruta) => readFileSync(new URL(`../${ruta}`, import.meta.url), 'utf8');
const csp = leer('index.html').match(/http-equiv="Content-Security-Policy" content="([^"]+)"/)?.[1];

test('la CSP permite los servicios que usa la página', () => {
  assert.ok(csp);
  for (const url of [urlOpenMeteo(), urlModelos(), urlEnsamble()]) {
    assert.ok(csp.includes(new URL(url).origin), url);
  }
});

test('la CSP no abre la puerta a código ni estilos en línea', () => {
  assert.equal(csp.includes('unsafe'), false);
  assert.match(csp, /default-src 'none'/);
  const html = leer('index.html');
  assert.equal(/<script(?![^>]*\bsrc=)/.test(html), false);
  assert.equal(/\sstyle="/.test(html + leer('assets/app.js')), false);
});
