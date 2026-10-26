// Modelo corregido con la lluvia real del aeropuerto de Guayaquil (MOS).
// Toma los pronósticos de GFS, ECMWF e ICON y el índice de El Niño, y aplica la
// regresión logística entrenada en analisis/entrenar.py (coeficientes en mos-coeficientes.js).
// Las variables se calculan igual que en Python; tests/modelo.test.mjs lo comprueba.

import COEF from './mos-coeficientes.js';

export const META = COEF.meta;
const UMBRAL_MM = COEF.meta.umbral_mm;
const VENTANA = COEF.meta.ventana_h;

/** Modelo de Open-Meteo de cada fuente, tal como aparece en las columnas de la respuesta. */
export const MODELOS_MOS = { gfs: 'gfs_seamless', ecmwf: 'ecmwf_ifs025', icon: 'icon_seamless' };
export const VARIABLES_MOS = ['precipitation', 'cape', 'relative_humidity_2m', 'cloud_cover'];

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
export function variablesMOS(hourly, i, { nino, aeropuerto } = {}) {
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
    lluvia_ahora: aeropuerto?.lluvia_ahora ?? null,
    lluvia_3h: aeropuerto?.lluvia_3h ?? null,
  };
  for (const [corto, modelo] of Object.entries(MODELOS_MOS)) {
    const col = `precipitation_${modelo}`;
    const ahora = tramo(hourly, col, i, i);
    const vecinas = tramo(hourly, col, i - 1, i + 1);
    const prox = tramo(hourly, col, i + 1, i + VENTANA);
    v[`${corto}_mm`] = quizas(ahora, (xs) => Math.log1p(xs[0]));
    v[`${corto}_mm_vecinas`] = log1p(quizas(vecinas, max));
    v[`${corto}_mm_6h`] = log1p(quizas(prox, suma));
    v[`${corto}_max_6h`] = log1p(quizas(prox, max));
    v[`${corto}_llueve_6h`] = quizas(prox, (xs) => (xs.some((x) => x >= UMBRAL_MM) ? 1 : 0));
  }
  const cape = tramo(hourly, 'cape_gfs_seamless', i, i);
  const capeProx = tramo(hourly, 'cape_gfs_seamless', i + 1, i + VENTANA);
  const hum = tramo(hourly, 'relative_humidity_2m_gfs_seamless', i, i);
  const nubes = tramo(hourly, 'cloud_cover_gfs_seamless', i, i);
  const nubesProx = tramo(hourly, 'cloud_cover_gfs_seamless', i + 1, i + VENTANA);
  v.cape = quizas(cape, (xs) => Math.log1p(xs[0]));
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

/**
 * Probabilidades del modelo corregido para la hora con índice i:
 * - hora: que llueva en esa hora
 * - proximas6h: que llueva en algún momento de las 6 horas siguientes; usa el reporte
 *   del aeropuerto si se lo pasan, y si no, la variante sin él
 */
export function probabilidadesMOS(hourly, i, contexto = {}) {
  const v = variablesMOS(hourly, i, contexto);
  const conMetar = aplicarMOS('6h_con_metar', v);
  return {
    hora: aplicarMOS('hora', v),
    proximas6h: conMetar ?? aplicarMOS('6h', v),
    usaAeropuerto: conMetar !== null,
  };
}
