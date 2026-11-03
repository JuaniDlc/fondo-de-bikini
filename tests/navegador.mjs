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
  // Por lugar con un número imposible: el aeropuerto debe mostrar el de «Próximas horas», no este.
  const guardada = JSON.parse(await readFile(join(RAIZ, 'data/actual.json'), 'utf8'));
  const horas = [guardada.horaLluvia, ...guardada.proyeccion.map((f) => f.hora)].slice(0, 6)
    .map((hora) => ({ hora, probabilidad: 77 }));
  await pagina.route(/data\/lugares\.json/, (ruta) => ruta.fulfill({
    json: { generado: new Date().toISOString(), lugares: [{ nombre: 'Aeropuerto', horas }, { nombre: 'Otro', horas }] },
  }));
  // Rayos de ejemplo, para que las tarjetas no dependan del clima de hoy.
  await pagina.route(/data\/rayos\.json/, (ruta) => ruta.fulfill({
    json: {
      generado: new Date().toISOString(), rayos: 12, mas_cercano_km: 12, rumbo: 'noreste',
      puntos: [[12, 60, 5], [40, 300, 7]], modelo: null,
    },
  }));
  await pagina.goto(url);
  await pagina.waitForFunction(() => /\d %/.test(document.getElementById('prob').textContent));
  await pagina.waitForFunction(() => document.getElementById('estado').textContent !== 'Actualizando con el clima de este momento…');

  const vista = await pagina.evaluate(() => ({
    barras: [...document.querySelectorAll('#horas-filas .barra span')].map((b) => b.style.width),
    grafica: document.querySelectorAll('#grafica svg path, #grafica svg polyline').length,
    ahora: [...document.querySelectorAll('#grafica text')].some((t) => t.textContent === 'Ahora'),
    rayos: [document.querySelectorAll('#radar-region circle.rayo').length, document.querySelectorAll('#radar-ciudad circle.rayo').length],
    tarjeta: document.getElementById('rayos-nivel').textContent,
    titulo: document.getElementById('rayos-titulo').textContent,
    consejos: /lugar cerrado|resguárd|lugar seguro/i.test(document.querySelector('main').textContent),
    arriba: document.querySelector('.principal').nextElementSibling.id,
    desbordada: document.documentElement.scrollWidth > window.innerWidth,
    error: document.getElementById('estado').classList.contains('error'),
    proximas: [...document.querySelectorAll('#horas-filas tr')].map((f) => f.querySelector('b').textContent),
    lugares: [...document.querySelectorAll('#lugares-filas tr')].map((f) => [...f.querySelectorAll('b')].map((b) => b.textContent)),
  }));
  assert.deepEqual(errores, [], 'errores o bloqueos de la CSP');
  assert.deepEqual(faltantes, [], 'archivos que la página no encontró');
  assert.ok(vista.barras.length >= 1 && vista.barras.every((b) => b.endsWith('%')), `barras: ${vista.barras}`);
  assert.ok(vista.grafica >= 1 && vista.ahora, 'la gráfica no se dibujó');
  assert.deepEqual(vista.rayos, [2, 1], 'rayos en cada radar');
  assert.equal(vista.tarjeta, 'Hay tormenta eléctrica');
  assert.match(vista.titulo, /^A 12 km al noreste/);
  assert.equal(vista.consejos, false, 'la sección de rayos no da consejos');
  assert.equal(vista.arriba, 'aviso', 'no debe haber aviso de rayos arriba');
  assert.equal(vista.desbordada, false, 'la página se desborda a lo ancho en un celular');
  assert.equal(vista.error, true, 'sin el servicio del clima, la página debe avisarlo');
  assert.deepEqual(vista.lugares.map((f) => f[0]), vista.proximas, 'dos números distintos para el aeropuerto');
  assert.ok(vista.lugares.length && vista.lugares.every((f) => f[1] === '77 %'), 'los demás lugares deben seguir igual');
  console.log(`La página funciona: ${vista.barras.length} barras, gráfica dibujada, sin errores.`);
} finally {
  await navegador.close();
  servidor.close();
}
