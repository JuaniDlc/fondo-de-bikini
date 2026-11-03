import { test } from 'node:test';
import assert from 'node:assert/strict';
import { CIUDAD, REGION, cercaDe, nivelRayos, resumenRayos, svgRadar } from '../assets/radar.js';

const ahora = Date.parse('2026-11-02T20:00:00Z');
const base = { generado: '2026-11-02T19:52:00Z', rayos: 40, mas_cercano_km: 12, rumbo: 'noreste' };

test('niveles de rayos, iguales a los de los avisos', () => {
  assert.equal(nivelRayos(null), 0);
  assert.equal(nivelRayos({ rayos: 2, mas_cercano_km: 5 }), 0); // puede ser ruido del sensor
  assert.equal(nivelRayos({ rayos: 3, mas_cercano_km: 25 }), 2);
  assert.equal(nivelRayos({ rayos: 3, mas_cercano_km: 40 }), 1);
});

test('la tarjeta dice si hay tormenta y dónde, sin consejos', () => {
  const r = resumenRayos({ ...base, puntos: [[12, 60, 5], [20, 70, 2]] }, ahora);
  assert.equal(r.nivel, 2);
  assert.equal(r.minutos, 8);
  assert.equal(r.etiqueta, 'Hay tormenta eléctrica');
  assert.equal(r.titulo, 'A 12 km al noreste, cerca de Durán');
  assert.equal('accion' in r, false);
  const lejos = resumenRayos({ ...base, mas_cercano_km: 48, puntos: [[48, 270, 9]] }, ahora);
  assert.equal(lejos.etiqueta, 'Hay tormenta eléctrica');
  assert.match(lejos.titulo, /^A 48 km al oeste/);
});

test('sin rayos solo lo dice, y los datos viejos no se muestran', () => {
  const r = resumenRayos({ ...base, rayos: 0, mas_cercano_km: null, puntos: [] }, ahora);
  assert.equal(r.etiqueta, 'Sin tormenta eléctrica');
  assert.equal(r.titulo, '');
  assert.equal(resumenRayos({ ...base, generado: '2026-11-02T19:00:00Z' }, ahora), null);
  assert.equal(resumenRayos(null, ahora), null);
});

test('si el archivo aún no trae puntos, la frase igual funciona', () => {
  assert.equal(resumenRayos(base, ahora).titulo, 'A 12 km al noreste');
});

test('un punto lejos de todo no se atribuye a ningún lugar', () => {
  assert.equal(cercaDe(200, 58), null);
  assert.equal(cercaDe(67, 6), 'Durán');
});

test('el radar dibuja lugares, anillos y solo los rayos de su radio', () => {
  const svg = svgRadar({ radioKm: 25, anillos: [10, 25], lugares: CIUDAD, puntos: [[12, 60, 5], [50, 60, 5]], nivel: 2 });
  assert.equal((svg.match(/class="rayo/g) ?? []).length, 1);
  assert.match(svg, /Aeropuerto/);
  assert.match(svg, /25 km/);
  assert.equal(/\sstyle=/.test(svg), false);
  assert.equal(/Lugar [AB]/.test(svg + JSON.stringify(REGION)), false);
});
