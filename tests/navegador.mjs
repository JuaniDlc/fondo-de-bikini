// Abre la página de verdad en Chrome, con los datos de data/ y sin el servicio del clima, y comprueba
// que se dibuja, sin errores ni bloqueos de la CSP. Uso: npm ci --ignore-scripts && node tests/navegador.mjs
// El navegador se puede cambiar con NAVEGADOR=msedge.

import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const RAIZ = fileURLToPath(new URL('..', import.meta.url));
const TIPOS = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json' };

const servidor = createServer(async (pedido, respuesta) => {
  const ruta = new URL(pedido.url, 'http://x').pathname;
  try {
    const archivo = join(RAIZ, normalize(ruta === '/' ? '/index.html' : ruta));
    const contenido = await readFile(archivo);
    respuesta.writeHead(200, { 'Content-Type': TIPOS[extname(archivo)] ?? 'application/octet-stream' }).end(contenido);
  } catch {
    respuesta.writeHead(404).end();
  }
});
await new Promise((listo) => { servidor.listen(0, '127.0.0.1', listo); });
const url = `http://127.0.0.1:${servidor.address().port}/`;

const navegador = await chromium.launch({ channel: process.env.NAVEGADOR ?? 'chrome' });
try {
  const contexto = await navegador.newContext({ viewport: { width: 375, height: 812 } });
  const pagina = await contexto.newPage();
  const errores = [];
  const faltantes = [];
  pagina.on('pageerror', (e) => errores.push(e.message));
  // La CSP avisa por la consola; se bloquea el clima a propósito, y esa falla se ignora.
  pagina.on('console', (m) => { if (/Content.Security.Policy/i.test(m.text())) errores.push(m.text()); });
  pagina.on('response', (r) => {
    if (r.status() >= 400 && r.url().startsWith(url)) faltantes.push(r.url().replace(url, ''));
  });
  await pagina.route(/open-meteo\.com/, (ruta) => ruta.abort());
  await pagina.goto(url);
  await pagina.waitForFunction(() => /\d %/.test(document.getElementById('prob').textContent));
  await pagina.waitForFunction(() => document.getElementById('estado').textContent !== 'Actualizando con el clima de este momento…');

  const vista = await pagina.evaluate(() => ({
    barras: [...document.querySelectorAll('#horas-filas .barra span')].map((b) => b.style.width),
    grafica: document.querySelectorAll('#grafica svg path, #grafica svg polyline').length,
    ahora: [...document.querySelectorAll('#grafica text')].some((t) => t.textContent === 'Ahora'),
    desbordada: document.documentElement.scrollWidth > window.innerWidth,
    error: document.getElementById('estado').classList.contains('error'),
    puntosPasados: document.getElementById('grafica').innerHTML.length,
  }));
  assert.deepEqual(errores, [], 'errores o bloqueos de la CSP');
  assert.deepEqual(faltantes, [], 'archivos que la página no encontró');
  assert.ok(vista.barras.length >= 1 && vista.barras.every((b) => b.endsWith('%')), `barras: ${vista.barras}`);
  assert.ok(vista.grafica >= 1 && vista.ahora, 'la gráfica no se dibujó');
  assert.equal(vista.desbordada, false, 'la página se desborda a lo ancho en un celular');
  assert.equal(vista.error, true, 'sin el servicio del clima, la página debe avisarlo');
  console.log(`La página funciona: ${vista.barras.length} barras, gráfica dibujada, sin errores.`);
} finally {
  await navegador.close();
  servidor.close();
}
