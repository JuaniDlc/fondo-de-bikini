import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { VARIABLES_SENALES, aplicarMOS, ninoVigente, probabilidadesMOS, variablesMOS } from '../assets/mos.js';
import { conservarResumen, huboLluvia, leerNino, leerReporte, resumirAeropuerto } from '../scripts/fuentes.mjs';

// Casos con datos crudos y el resultado de Python (los escribe analisis/entrenar.py).
const casos = JSON.parse(readFileSync(new URL('./fixtures/mos-casos.json', import.meta.url), 'utf8'));

test('el modelo corregido da en JavaScript lo mismo que en Python', () => {
  assert.ok(casos.length >= 5);
  for (const c of casos) {
    const i = c.hourly.time.indexOf(c.hora);
    // Los modelos de «la hora T» con k horas de anticipación usan el aeropuerto hasta T − k y los
    // rayos hasta T − k + c.minutos; los de 6 h, hasta T.
    const v = variablesMOS(c.hourly, i, { nino: c.nino, aeropuerto: c.aeropuerto, rayos: c.rayos, ir: c.ir });
    for (const [nombre, esperado] of Object.entries(c.esperado)) {
      const k = nombre === 'hora_con_metar' ? '1' : nombre.match(/^hora_(?:con_metar|con_rayos|con_ir|con_vapor|completo)_(\d)$/)?.[1];
      const vk = k ? variablesMOS(c.hourly, i, {
        nino: c.nino, aeropuerto: c.aeropuerto_previo[k], rayos: c.rayos_previo?.[k], ir: c.ir_previo?.[k],
        fraccion: c.minutos / 60,
      }) : v;
      const p = aplicarMOS(nombre, vk);
      assert.ok(Math.abs(p - esperado) < 1e-5, `${c.hora} ${nombre}: ${p} ≠ ${esperado}`);
    }
  }
});

test('las señales de los reportes del aeropuerto salen igual que en Python', () => {
  for (const c of casos) {
    const { hora, reportes } = c.reportes_previos;
    const r = reportes.map((x) => ({ fecha: new Date(x.fecha), metar: x.metar }));
    const { senales } = resumirAeropuerto(r, hora);
    for (const nombre of VARIABLES_SENALES) {
      assert.ok(Math.abs(senales[nombre] - c.aeropuerto_previo['1'].senales[nombre]) < 1e-5,
        `${c.hora} ${nombre}: ${senales[nombre]} ≠ ${c.aeropuerto_previo['1'].senales[nombre]}`);
    }
  }
});

test('lectura de un reporte del aeropuerto', () => {
  const r = leerReporte('SEGU 012000Z 25008G18KT 200V280 4000 VCSH BKN012CB OVC090 M01/M03 Q1009 TEMPO 3000 TSRA RMK A2982');
  assert.equal(r.vc, 1);
  assert.equal(r.cb, 1);
  assert.equal(r.ts, 0);
  assert.equal(r.tend_lluvia, 1);
  assert.equal(r.sp, 2);
  assert.equal(r.pres, 1009);
  assert.ok(Math.abs(r.techo - Math.log1p(1200)) < 1e-9);
  assert.ok(Math.abs(r.vis - Math.log1p(4000)) < 1e-9);
  const viento = leerReporte('SEGU 012000Z VRB02KT CAVOK 27/24 Q1009 NOSIG');
  assert.deepEqual([viento.u_m, viento.v_m, viento.tend_lluvia], [-0, -0, 0]);
  assert.ok(Math.abs(viento.base - Math.log1p(12000)) < 1e-9);
});

test('sin señales o sin nubes bajas se usa el modelo anterior', () => {
  const conTodo = casos[0];
  const i = conTodo.hourly.time.indexOf(conTodo.hora);
  const contexto = (k, cambios = {}) => ({
    nino: conTodo.nino, aeropuerto: conTodo.aeropuerto_previo[k], rayos: conTodo.rayos_previo[k],
    ir: conTodo.ir_previo[k], fraccion: conTodo.minutos / 60, adelanto: Number(k), ...cambios,
  });
  for (const k of ['1', '2', '3']) {
    const p = probabilidadesMOS(conTodo.hourly, i, contexto(k));
    assert.equal(p.horaUsaSenales, true, k);
    assert.ok(Math.abs(p.hora - conTodo.esperado[`hora_completo_${k}`]) < 1e-5);
    const sinSenales = probabilidadesMOS(conTodo.hourly, i, contexto(k, {
      aeropuerto: { ...conTodo.aeropuerto_previo[k], senales: null },
    }));
    assert.equal(sinSenales.horaUsaSenales, false);
    assert.equal(sinSenales.horaUsaVapor, true);
    assert.ok(Math.abs(sinSenales.hora - conTodo.esperado[`hora_con_vapor_${k}`]) < 1e-5);
  }
  // A 2 y 3 h hacen falta las nubes bajas; la hora en curso no las usa.
  const { luz_centro: _l, ...sinBajas } = conTodo.ir_previo['2'];
  assert.equal(probabilidadesMOS(conTodo.hourly, i, contexto('2', { ir: sinBajas })).horaUsaSenales, false);
  const { luz_centro: _m, ...sinBajas1 } = conTodo.ir_previo['1'];
  assert.equal(probabilidadesMOS(conTodo.hourly, i, contexto('1', { ir: sinBajas1 })).horaUsaSenales, true);
  // A 4 h no hay modelo con señales.
  assert.equal(probabilidadesMOS(conTodo.hourly, i, contexto('4')).horaUsaSenales, false);
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
  const { senales, ...resumen } = resumirAeropuerto(reportes, '2026-10-25T22:00');
  assert.deepEqual(resumen, { hora: '2026-10-25T22:00', lluvia_ahora: 0, lluvia_3h: 1, reportes: 3, lloviendo: null });
  assert.equal(senales.vc, 0);
  // Falta el reporte de una de las 3 horas: lluvia_3h no se puede calcular
  assert.equal(resumirAeropuerto(reportes.slice(1), '2026-10-25T22:00').lluvia_3h, null);
  // Un especial a las 21:20 cuenta para la hora de las 22:00
  const especial = [...reportes, r('2026-10-26T02:20:00Z', 'SPECI SEGU 260220Z 4000 RA BKN020')];
  assert.equal(resumirAeropuerto(especial, '2026-10-25T22:00').lluvia_ahora, 1);
  // Un especial con lluvia a las 22:37 (hora en curso): ya está lloviendo, pero no cambia la hora anterior
  const enCurso = [...reportes, r('2026-10-26T03:37:00Z', 'SPECI SEGU 260337Z 8000 -RA BKN023')];
  const { senales: deEnCurso, ...lloviendo } = resumirAeropuerto(enCurso, '2026-10-25T22:00').lloviendo;
  assert.deepEqual(lloviendo, { hora: '2026-10-25T23:00', desde: '22:37' });
  assert.ok(Math.abs(deEnCurso.techo - Math.log1p(2300)) < 1e-5);
  assert.equal(resumirAeropuerto(enCurso, '2026-10-25T22:00').lluvia_ahora, 0);
});

test('si el reporte de la hora aún no llega, el resumen usa la hora anterior', () => {
  const r = (iso, metar) => ({ fecha: new Date(iso), metar });
  const reportes = [
    r('2026-11-03T07:00:00Z', 'SEGU 030700Z 36003KT 9999 BKN023 26/24 Q1009 NOSIG'), // 02:00
    r('2026-11-03T08:00:00Z', 'SEGU 030800Z 01006KT 9999 -RA BKN020 25/24 Q1009 NOSIG'), // 03:00
    r('2026-11-03T06:00:00Z', 'SEGU 030600Z 33004KT 9999 BKN023 27/23 Q1010 NOSIG'), // 01:00
  ];
  const s = resumirAeropuerto(reportes, '2026-11-03T04:00'); // falta el de las 04:00
  assert.equal(s.hora, '2026-11-03T03:00');
  assert.equal(s.lluvia_ahora, 1);
  assert.equal(s.lluvia_3h, 1);
  assert.ok(s.senales);
  // Sin reporte tampoco de la hora anterior, no se inventa: queda sin dato.
  const viejo = resumirAeropuerto(reportes, '2026-11-03T06:00');
  assert.equal(viejo.hora, '2026-11-03T06:00');
  assert.equal(viejo.lluvia_ahora, null);
  // Un especial con lluvia en la hora en curso se sigue viendo.
  const especial = [...reportes, r('2026-11-03T09:20:00Z', 'SPECI SEGU 030920Z 8000 RA BKN020')];
  assert.equal(resumirAeropuerto(especial, '2026-11-03T04:00').lloviendo.desde, '04:20');
  // Si la API pierde el reporte que ya teníamos, el resumen no retrocede.
  const guardado = { generado: 'x', hora: '2026-11-03T04:00', lluvia_ahora: 1, lluvia_3h: 1, reportes: 8, senales: { vc: 0 }, lloviendo: null };
  assert.deepEqual(conservarResumen(s, guardado),
    { hora: '2026-11-03T04:00', lluvia_ahora: 1, lluvia_3h: 1, reportes: s.reportes, senales: { vc: 0 }, lloviendo: null });
});

test('el resumen del aeropuerto no pierde datos si la API devuelve menos reportes', () => {
  const hora = '2026-11-02T10:00';
  const anterior = { generado: 'x', hora, lluvia_ahora: 1, lluvia_3h: 1, reportes: 7, lloviendo: null };
  const incompleto = { hora, lluvia_ahora: null, lluvia_3h: null, reportes: 6, senales: null, lloviendo: null };
  assert.deepEqual(conservarResumen(incompleto, anterior),
    { hora, lluvia_ahora: 1, lluvia_3h: 1, reportes: 6, senales: null, lloviendo: null });
  // Lo que sí trae el resumen nuevo gana, y una hora nueva no hereda nada
  const nuevo = { ...incompleto, lluvia_ahora: 0, lluvia_3h: 1 };
  assert.equal(conservarResumen(nuevo, anterior).lluvia_ahora, 0);
  assert.deepEqual(conservarResumen({ ...incompleto, hora: '2026-11-02T11:00' }, anterior),
    { ...incompleto, hora: '2026-11-02T11:00' });
  assert.deepEqual(conservarResumen(incompleto, null), incompleto);
});

test('lectura del índice de El Niño de CPC', () => {
  const texto = ' 07OCT2026     26.1 5.2     29.0 4.1     30.0 3.3     29.9 1.3\n'
    + ' 03JAN1990     23.4-0.4     25.1-0.3     26.6 0.0     28.6 0.3\n';
  assert.deepEqual(leerNino(texto), [
    { semana: '2026-10-07', nino12: 5.2, nino34: 3.3 },
    { semana: '1990-01-03', nino12: -0.4, nino34: 0 },
  ]);
});
