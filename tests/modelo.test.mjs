import { test } from 'node:test';
import assert from 'node:assert/strict';
import { BASE_MES, calcular, marea, puntoRocio, tendenciaLineal } from '../assets/modelo.js';
import { aFecha, aLocal, procesarRespuesta, sumarHoras } from '../assets/openmeteo.js';

const cerca = (real, esperado, tol = 1e-6) =>
  assert.ok(Math.abs(real - esperado) <= tol, `${real} ≠ ${esperado} (±${tol})`);

// Casos fijos: si alguno cambia, el modelo cambió.
test('caso fijo: tarde de febrero, calurosa y con presión bajando', () => {
  const { probabilidad, detalle } = calcular({ P: 1009.5, P3: 1011.0, T: 32, HR: 85, mes: 2, hora: 15 });
  cerca(probabilidad, 0.930351);
  assert.equal(detalle.factores.conveccion, 1.0);
  assert.equal(detalle.factores.humedad, 0.3);
  assert.equal(detalle.factores.presion, 0.375);
});

test('caso fijo: mañana seca de agosto', () => {
  const { probabilidad, detalle } = calcular({ P: 1013.2, P3: 1012.8, T: 26, HR: 65, mes: 8, hora: 10 });
  cerca(probabilidad, 0.002715);
  // A las 10 h la marea sube 1.2 hPa en 3 h; subió solo 0.4 → anomalía −0.8.
  cerca(detalle.cambioEsperado, 1.2);
  cerca(detalle.anomalia, -0.8);
  cerca(detalle.factores.tendencia, 0.72);
  assert.equal(detalle.factores.conveccion, 0);
});

test('caso fijo: madrugada húmeda de diciembre sin presión de hace 3 h', () => {
  const { probabilidad, detalle } = calcular({ P: 1011.0, P3: null, T: 24, HR: 92, mes: 12, hora: 3 });
  cerca(probabilidad, 0.655597);
  assert.equal(detalle.factores.tendencia, 0);
  assert.equal(detalle.anomalia, null);
});

test('límites de cada factor', () => {
  const extremo = calcular({ P: 990, P3: 1010, T: 40, HR: 100, mes: 3, hora: 15 }).detalle.factores;
  assert.equal(extremo.humedad, 1.0);
  assert.equal(extremo.tendencia, 2.0);
  assert.equal(extremo.presion, 1.0);
  assert.equal(extremo.margen, 2.0);
  const seco = calcular({ P: 1030, P3: 1010, T: 35, HR: 20, mes: 8, hora: 3 }).detalle.factores;
  assert.equal(seco.humedad, -1.8);
  assert.equal(seco.tendencia, -1.5);
  assert.equal(seco.presion, -0.8);
  assert.equal(seco.margen, -2.2);
});

test('convección solo en temporada lluviosa entre 13 y 20 h', () => {
  const f = (mes, hora, T) => calcular({ P: 1011, P3: 1011, T, HR: 80, mes, hora }).detalle.factores.conveccion;
  assert.equal(f(3, 13, 30), 0.6);
  assert.equal(f(3, 20, 31), 1.0);
  assert.equal(f(3, 12, 33), 0);
  assert.equal(f(3, 21, 33), 0);
  assert.equal(f(12, 15, 33), 0); // diciembre: base 0.18, no es temporada lluviosa
});

test('temporada: con el resto neutro la probabilidad es la base del mes', () => {
  // HR = 80 y sp ≈ 4 no son alcanzables a la vez, así que se revisa solo el término.
  for (let mes = 1; mes <= 12; mes++) {
    const t = calcular({ P: 1011, P3: null, T: 28, HR: 80, mes, hora: 3 }).detalle.factores.temporada;
    const base = BASE_MES[mes - 1];
    cerca(1 / (1 + Math.exp(-(Math.log(0.25 / 0.75) + t))), base);
  }
});

test('punto de rocío y marea', () => {
  cerca(puntoRocio(30, 70), 23.927, 1e-3);
  cerca(puntoRocio(25, 100), 25, 1e-9);
  cerca(marea(10), 1.2);
  cerca(marea(4), -1.2);
});

test('tendencia lineal', () => {
  assert.equal(tendenciaLineal([{ t: -1, y: 10 }, { t: 0, y: 12 }]), null);
  const r = tendenciaLineal([-5, -4, -3, -2, -1, 0].map((t) => ({ t, y: 40 + 3 * t })));
  cerca(r.m, 3);
  cerca(r.b, 40);
  assert.equal(r.n, 6);
});

test('horas locales de Guayaquil (UTC−5)', () => {
  assert.equal(aFecha('2026-10-25T14:00').toISOString(), '2026-10-25T19:00:00.000Z');
  assert.equal(aLocal(new Date('2026-10-26T02:00:00Z')), '2026-10-25T21:00');
  assert.equal(sumarHoras('2026-10-26T01:00', -3), '2026-10-25T22:00');
});

// Horas de 11:00 a 21:00; «ahora» son las 15:30.
const HORAS = Array.from({ length: 11 }, (_, i) => sumarHoras('2026-02-10T15:00', i - 4));
const CLIMA = {
  current: { time: '2026-02-10T15:30', temperature_2m: 32, relative_humidity_2m: 85, pressure_msl: 1009.5 },
  hourly: {
    time: HORAS,
    temperature_2m: HORAS.map(() => 30),
    relative_humidity_2m: HORAS.map(() => 80),
    pressure_msl: [1012, 1011, 1010, 1010, 1009.5, 1009, 1009, 1009, 1009, 1009, 1009],
  },
};
const serie = (lluvias) => HORAS.map((h) => lluvias[h.slice(11, 13)] ?? 0);
const ENSAMBLE = {
  hourly: {
    time: HORAS,
    // ECMWF: una simulación llueve a las 15 y 16, la otra a las 18
    precipitation_ecmwf_ifs025_ensemble: serie({ 15: 0.5, 16: 0.3 }),
    precipitation_member01_ecmwf_ifs025_ensemble: serie({ 18: 0.2 }),
    // GFS: una simulación seca, la otra llueve a las 15; 0.05 mm no cuenta como lluvia
    precipitation_ncep_gefs025: serie({ 16: 0.05 }),
    precipitation_member01_ncep_gefs025: serie({ 15: 1.0 }),
  },
};

test('procesarRespuesta separa pasado, actual y proyección', () => {
  const { actual, pasado, proyeccion } = procesarRespuesta({ clima: CLIMA, ensamble: ENSAMBLE });
  assert.equal(actual.hora, '2026-02-10T15:00');
  assert.equal(actual.presion3h, 1011);
  assert.deepEqual(pasado.map((f) => f.hora.slice(11)), ['11:00', '12:00', '13:00', '14:00', '15:00']);
  assert.deepEqual(proyeccion.map((f) => f.hora.slice(11)), ['17:00', '18:00', '19:00', '20:00', '21:00']);
});

test('probabilidad del ensamble: promedio de modelos, en la hora y en 6 h', () => {
  const { actual, proyeccion } = procesarRespuesta({ clima: CLIMA, ensamble: ENSAMBLE });
  assert.equal(actual.fuente, 'ensamble');
  // «Esta hora» es la hora en curso (15:30 → la de 16:00, de 15 a 16): ECMWF 1/2, GFS 0/2
  assert.equal(actual.horaLluvia, '2026-02-10T16:00');
  assert.equal(actual.probabilidad, 25);
  assert.equal(actual.heuristica, 93);
  assert.equal(actual.proximas6h, 75); // ECMWF 2/2, GFS 1/2 entre 15:00 y 20:00
  assert.deepEqual(actual.modelos.proximas6h, { ecmwf: 100, gfs: 50 });
  assert.equal(proyeccion.find((f) => f.hora.endsWith('18:00')).probabilidad, 25); // ECMWF 1/2, GFS 0/2
  assert.equal(proyeccion.find((f) => f.hora.endsWith('17:00')).probabilidad, 0);
});

test('la lluvia del aeropuerto en la hora en curso solo es observada en el aeropuerto', () => {
  const aeropuerto = {
    hora: '2026-02-10T15:00', lluvia_ahora: 0, lluvia_3h: 0, lloviendo: { hora: '2026-02-10T16:00', desde: '15:20' },
  };
  const enAeropuerto = procesarRespuesta({ clima: CLIMA, ensamble: ENSAMBLE }, { aeropuerto }).actual;
  assert.equal(enAeropuerto.fuente, 'aeropuerto');
  assert.equal(enAeropuerto.probabilidad, 100);
  const enLugar = procesarRespuesta({ clima: CLIMA, ensamble: ENSAMBLE }, { aeropuerto, enAeropuerto: false }).actual;
  assert.equal(enLugar.fuente, 'ensamble');
  assert.equal(enLugar.probabilidad, 25);
  assert.equal(enLugar.lloviendo, null);
});

test('sin ensambles la probabilidad cae a la heurística', () => {
  const { actual } = procesarRespuesta({ clima: CLIMA, ensamble: null });
  assert.equal(actual.fuente, 'heuristica');
  assert.equal(actual.probabilidad, 93);
  assert.equal(actual.proximas6h, null);
});
