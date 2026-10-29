// Modelo corregido con la lluvia real del aeropuerto de Guayaquil (MOS).
// Toma los pronósticos de GFS, ECMWF e ICON y el índice de El Niño, y aplica la
// regresión logística entrenada en analisis/entrenar.py (coeficientes en mos-coeficientes.js).
// Las variables se calculan igual que en Python; tests/modelo.test.mjs lo comprueba.

import COEF from './mos-coeficientes.js';

export const META = COEF.meta;
const UMBRAL_MM = COEF.meta.umbral_mm;
const VENTANA = COEF.meta.ventana_h;

/**
 * Modelo de Open-Meteo de cada fuente, tal como aparece en las columnas de la respuesta. Viene con
 * los coeficientes, así la página siempre pide los modelos con que se entrenó.
 */
export const MODELOS_MOS = COEF.meta.modelos ?? { gfs: 'gfs_seamless', ecmwf: 'ecmwf_ifs025', icon: 'icon_seamless' };
export const VARIABLES_MOS = ['precipitation', 'cape', 'relative_humidity_2m', 'cloud_cover'];

/** Variables de rayos que escribe scripts/rayos.py en data/rayos.json (modelo). */
export const VARIABLES_RAYOS = [
  'rayos_15_1h', 'rayos_30_1h', 'rayos_60_1h', 'rayos_100_1h', 'rayos_150_1h',
  'rayos_60_20m', 'cercania_20m', 'cercania_1h', 'acercamiento',
];

const esNumero = (v) => typeof v === 'number' && Number.isFinite(v);

/** Valores de una columna en los índices [desde, hasta]; null si falta alguno. */
function tramo(hourly, columna, desde, hasta) {
  const serie = hourly[columna];
  if (!serie || desde < 0 || hasta >= serie.length) return null;
  const out = serie.slice(desde, hasta + 1);
  return out.every(esNumero) ? out : null;
}

const suma = (xs) => xs.reduce((s, x) => s + x, 0);
const max = (xs) => Math.max(...xs);
const log1p = (x) => (x === null ? null : Math.log1p(x));
const quizas = (xs, f) => (xs === null ? null : f(xs));

function diaDelAno(local) {
  const [a, m, d] = local.slice(0, 10).split('-').map(Number);
  return (Date.UTC(a, m - 1, d) - Date.UTC(a, 0, 0)) / 864e5;
}

/** Índice de El Niño vigente a la hora dada: el de la semana más reciente con al menos 7 días. */
export function ninoVigente(nino, local) {
  if (!Array.isArray(nino)) return null;
  const limite = Date.parse(`${local.slice(0, 10)}T00:00Z`) - 7 * 864e5;
  const validos = nino.filter((n) => Date.parse(`${n.semana}T00:00Z`) <= limite);
  if (!validos.length) return null;
  return validos.reduce((a, b) => (a.semana > b.semana ? a : b));
}

/**
 * Variables de entrada para la hora con índice i de la respuesta horaria multimodelo.
 * Una variable vale null si faltan datos para calcularla.
 */
export function variablesMOS(hourly, i, { nino, aeropuerto, rayos } = {}) {
  const local = hourly.time[i];
  const hora = Number(local.slice(11, 13));
  const dia = diaDelAno(local);
  const n = ninoVigente(nino, local);
  const v = {
    hora_sin: Math.sin((2 * Math.PI * hora) / 24),
    hora_cos: Math.cos((2 * Math.PI * hora) / 24),
    dia_sin: Math.sin((2 * Math.PI * dia) / 365.25),
    dia_cos: Math.cos((2 * Math.PI * dia) / 365.25),
    nino12: n ? n.nino12 : null,
    nino34: n ? n.nino34 : null,
    // El mismo resumen del aeropuerto sirve a dos modelos: para «6 h desde la hora i» es la lluvia
    // hasta i; para «la hora i» es la lluvia hasta i − 1. Quien llama pasa el índice que corresponde.
    lluvia_ahora: aeropuerto?.lluvia_ahora ?? null,
    lluvia_3h: aeropuerto?.lluvia_3h ?? null,
    lluvia_previa: aeropuerto?.lluvia_ahora ?? null,
    lluvia_previa_3h: aeropuerto?.lluvia_3h ?? null,
  };
  // Rayos de la última hora (scripts/rayos.py), con el mismo criterio que el aeropuerto.
  for (const nombre of VARIABLES_RAYOS) v[nombre] = rayos?.[nombre] ?? null;
  const llueve2h = [];
  for (const [corto, modelo] of Object.entries(MODELOS_MOS)) {
    const col = `precipitation_${modelo}`;
    const ahora = tramo(hourly, col, i, i);
    const vecinas = tramo(hourly, col, i - 1, i + 1);
    const prox = tramo(hourly, col, i + 1, i + VENTANA);
    v[`${corto}_mm`] = quizas(ahora, (xs) => Math.log1p(xs[0]));
    v[`${corto}_mm_vecinas`] = log1p(quizas(vecinas, max));
    // Ventanas más anchas: los modelos suelen errar la hora de una tormenta por 1 a 3 horas.
    const v2 = tramo(hourly, col, i - 2, i + 2);
    v[`${corto}_mm_2h`] = log1p(quizas(v2, max));
    v[`${corto}_mm_3h`] = log1p(quizas(tramo(hourly, col, i - 3, i + 3), max));
    v[`${corto}_suma_2h`] = log1p(quizas(v2, suma));
    llueve2h.push(quizas(v2, (xs) => (xs.some((x) => x >= UMBRAL_MM) ? 1 : 0)));
    v[`${corto}_mm_6h`] = log1p(quizas(prox, suma));
    v[`${corto}_max_6h`] = log1p(quizas(prox, max));
    v[`${corto}_llueve_6h`] = quizas(prox, (xs) => (xs.some((x) => x >= UMBRAL_MM) ? 1 : 0));
  }
  const cape = tramo(hourly, 'cape_gfs_seamless', i, i);
  const capeProx = tramo(hourly, 'cape_gfs_seamless', i + 1, i + VENTANA);
  const hum = tramo(hourly, 'relative_humidity_2m_gfs_seamless', i, i);
  const nubes = tramo(hourly, 'cloud_cover_gfs_seamless', i, i);
  const nubesProx = tramo(hourly, 'cloud_cover_gfs_seamless', i + 1, i + VENTANA);
  v.modelos_llueve_2h = llueve2h.includes(null) ? null : suma(llueve2h);
  v.cape = quizas(cape, (xs) => Math.log1p(xs[0]));
  v.cape_2h = log1p(quizas(tramo(hourly, 'cape_gfs_seamless', i - 2, i + 2), max));
  v.cape_icon_2h = log1p(quizas(tramo(hourly, 'cape_icon_seamless', i - 2, i + 2), max));
  v.cape_max_6h = log1p(quizas(capeProx, max));
  v.humedad = hum ? hum[0] : null;
  v.nubes = nubes ? nubes[0] : null;
  v.nubes_6h = quizas(nubesProx, (xs) => suma(xs) / xs.length);
  return v;
}

/** Aplica uno de los modelos exportados; null si falta alguna variable. */
export function aplicarMOS(nombre, variables) {
  const m = COEF[nombre];
  let z = m.intercepto;
  for (let k = 0; k < m.variables.length; k++) {
    const x = variables[m.variables[k]];
    if (!esNumero(x)) return null;
    z += m.coeficientes[k] * ((x - m.media[k]) / m.escala[k]);
  }
  return 1 / (1 + Math.exp(-z));
}

/** Nombre del modelo de «la hora i» con el aeropuerto resumido hasta i − adelanto. */
export const modeloPrevia = (adelanto) => (adelanto === 1 ? 'hora_con_metar' : `hora_con_metar_${adelanto}`);
/** Igual, con los rayos de la hora antes de i − adelanto. */
export const modeloRayos = (adelanto) => `hora_con_rayos_${adelanto}`;

/**
 * Probabilidades del modelo corregido para la hora con índice i (la hora i acumula la lluvia
 * de i − 1 a i, como en Open-Meteo). Con contexto.aeropuerto usa las variantes con el reporte:
 * - hora: que llueva en la hora i (aeropuerto resumido hasta i − contexto.adelanto, 1 a 6 h)
 * - proximas6h: que llueva en algún momento de i + 1 … i + 6 (aeropuerto resumido hasta i)
 */
export function probabilidadesMOS(hourly, i, contexto = {}) {
  const v = variablesMOS(hourly, i, contexto);
  const adelanto = contexto.adelanto ?? 1;
  const intentar = (nombre) => (COEF[nombre] ? aplicarMOS(nombre, v) : null);
  const horaRayos = intentar(modeloRayos(adelanto));
  const horaMetar = intentar(modeloPrevia(adelanto));
  const seisRayos = intentar('6h_con_rayos');
  const seisMetar = aplicarMOS('6h_con_metar', v);
  return {
    hora: horaRayos ?? horaMetar ?? aplicarMOS('hora', v),
    horaUsaAeropuerto: (horaRayos ?? horaMetar) !== null,
    horaUsaRayos: horaRayos !== null,
    proximas6h: seisRayos ?? seisMetar ?? aplicarMOS('6h', v),
    usaAeropuerto: (seisRayos ?? seisMetar) !== null,
    usaRayos: seisRayos !== null,
  };
}

