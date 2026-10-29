import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { aplicarMOS, ninoVigente, variablesMOS } from '../assets/mos.js';
import { huboLluvia, leerNino, resumirAeropuerto } from '../scripts/fuentes.mjs';

// Casos con datos crudos y el resultado de Python (los escribe analisis/entrenar.py).
const casos = JSON.parse(readFileSync(new URL('./fixtures/mos-casos.json', import.meta.url), 'utf8'));

test('el modelo corregido da en JavaScript lo mismo que en Python', () => {
  assert.ok(casos.length >= 5);
  for (const c of casos) {
    const i = c.hourly.time.indexOf(c.hora);
    // Los modelos de «la hora T» con k horas de anticipación usan el aeropuerto y los rayos
    // hasta T − k; los de 6 h, hasta T.
    const v = variablesMOS(c.hourly, i, { nino: c.nino, aeropuerto: c.aeropuerto, rayos: c.rayos });
    for (const [nombre, esperado] of Object.entries(c.esperado)) {
      const k = nombre === 'hora_con_metar' ? '1' : nombre.match(/^hora_con_(?:metar|rayos|ir)_(\d)$/)?.[1];
      const vk = k ? variablesMOS(c.hourly, i, {
        nino: c.nino, aeropuerto: c.aeropuerto_previo[k], rayos: c.rayos_previo?.[k], ir: c.ir_previo?.[k],
      }) : v;
      const p = aplicarMOS(nombre, vk);
      assert.ok(Math.abs(p - esperado) < 1e-5, `${c.hora} ${nombre}: ${p} ≠ ${esperado}`);
    }
  }
});

test('sin datos de un modelo, el corregido no se calcula', () => {
  const c = structuredClone(casos[0]);
  c.hourly.precipitation_icon_seamless = c.hourly.precipitation_icon_seamless.map(() => null);
  const v = variablesMOS(c.hourly, c.hourly.time.indexOf(c.hora), { nino: c.nino });
  assert.equal(aplicarMOS('hora', v), null);
  assert.equal(aplicarMOS('6h_con_metar', v), null); // tampoco hay aeropuerto
});

test('índice de El Niño vigente: el de hace al menos 7 días', () => {
  const nino = [{ semana: '2026-10-07', nino12: 5.2 }, { semana: '2026-10-14', nino12: 5.3 }];
  assert.equal(ninoVigente(nino, '2026-10-20T10:00').nino12, 5.2);
  assert.equal(ninoVigente(nino, '2026-10-21T00:00').nino12, 5.3);
  assert.equal(ninoVigente(nino, '2026-10-10T00:00'), null);
});

test('lluvia en los reportes del aeropuerto', () => {
  assert.equal(huboLluvia('SEGU 022200Z 23007KT 6000 RA FEW010 BKN020 27/25 Q1005 TEMPO 4000'), true);
  assert.equal(huboLluvia('SEGU 040300Z 11003KT 9999 -RA BKN020 27/23 Q1009'), true);
  assert.equal(huboLluvia('SEGU 040300Z 11003KT 9999 -TSRA BKN020CB 27/23 Q1009'), true);
  assert.equal(huboLluvia('SEGU 040300Z 11003KT 9999 RERA BKN020 27/23 Q1009 NOSIG'), true);
  assert.equal(huboLluvia('SEGU 010500Z 32006KT 9999 VCSH SCT023 26/23 Q1011 NOSIG'), false);
  // La lluvia en el pronóstico de tendencia no cuenta
  assert.equal(huboLluvia('SEGU 010500Z 32006KT 9999 SCT023 26/23 Q1011 TEMPO 3000 RA'), false);
});

test('resumen del aeropuerto para la hora actual', () => {
  // Reportes en UTC; 03:00Z = 22:00 en Guayaquil
  const r = (iso, metar) => ({ fecha: new Date(iso), metar });
  const reportes = [
    r('2026-10-26T01:00:00Z', 'SEGU 260100Z 9999 -RA SCT026'), // 20:00 → hora 20:00
    r('2026-10-26T02:00:00Z', 'SEGU 260200Z 9999 SCT026'), // 21:00
    r('2026-10-26T03:00:00Z', 'SEGU 260300Z 9999 SCT026'), // 22:00
  ];
  assert.deepEqual(resumirAeropuerto(reportes, '2026-10-25T22:00'),
    { hora: '2026-10-25T22:00', lluvia_ahora: 0, lluvia_3h: 1, reportes: 3, lloviendo: null });
  // Falta el reporte de una de las 3 horas: lluvia_3h no se puede calcular
  assert.equal(resumirAeropuerto(reportes.slice(1), '2026-10-25T22:00').lluvia_3h, null);
  // Un especial a las 21:20 cuenta para la hora de las 22:00
  const especial = [...reportes, r('2026-10-26T02:20:00Z', 'SPECI SEGU 260220Z 4000 RA BKN020')];
  assert.equal(resumirAeropuerto(especial, '2026-10-25T22:00').lluvia_ahora, 1);
  // Un especial con lluvia a las 22:37 (hora en curso): ya está lloviendo, pero no cambia la hora anterior
  const enCurso = [...reportes, r('2026-10-26T03:37:00Z', 'SPECI SEGU 260337Z 8000 -RA BKN023')];
  assert.deepEqual(resumirAeropuerto(enCurso, '2026-10-25T22:00').lloviendo,
    { hora: '2026-10-25T23:00', desde: '22:37' });
  assert.equal(resumirAeropuerto(enCurso, '2026-10-25T22:00').lluvia_ahora, 0);
});

test('lectura del índice de El Niño de CPC', () => {
  const texto = ' 07OCT2026     26.1 5.2     29.0 4.1     30.0 3.3     29.9 1.3\n'
    + ' 03JAN1990     23.4-0.4     25.1-0.3     26.6 0.0     28.6 0.3\n';
  assert.deepEqual(leerNino(texto), [
    { semana: '2026-10-07', nino12: 5.2, nino34: 3.3 },
    { semana: '1990-01-03', nino12: -0.4, nino34: 0 },
  ]);
});
