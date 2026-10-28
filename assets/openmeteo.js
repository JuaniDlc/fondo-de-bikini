// Consulta a Open-Meteo y conversión de la respuesta en lecturas con probabilidad.
// Compartido por el workflow (Node) y el navegador.
//
// La probabilidad principal sale del modelo corregido (mos.js): GFS, ECMWF e ICON ajustados
// con la lluvia real del aeropuerto. Si no se puede calcular, se usan los ensambles de
// ECMWF (51 simulaciones) y GFS (31), y si tampoco hay, la heurística de modelo.js.
// Los tres valores se guardan para poder compararlos.

import { calcular } from './modelo.js';
import { MODELOS_MOS, VARIABLES_MOS, probabilidadesMOS } from './mos.js';

export const GUAYAQUIL = { lat: -2.19, lon: -79.89 };
export const ZONA = 'America/Guayaquil';

/** mm en una hora a partir de los cuales una simulación cuenta como «llueve». */
export const UMBRAL_LLUVIA_MM = 0.1;
/** Horas de la ventana «próximas horas», contando la hora en curso. */
export const VENTANA_H = 6;
// api: nombre para pedirlo; clave: cómo aparece en los nombres de las series de la respuesta.
export const MODELOS_ENSAMBLE = {
  ecmwf: { api: 'ecmwf_ifs025', clave: 'ecmwf_ifs025' },
  gfs: { api: 'gfs025', clave: 'ncep_gefs025' },
};

// Guayaquil está en UTC−5 todo el año (sin horario de verano).
const DESFASE_MS = -5 * 3600 * 1000;
const VARIABLES = 'temperature_2m,relative_humidity_2m,pressure_msl';

function consulta(extra) {
  return new URLSearchParams({
    latitude: GUAYAQUIL.lat,
    longitude: GUAYAQUIL.lon,
    // 24 horas para la gráfica y 3 más para las ventanas del modelo corregido.
    past_hours: 27,
    // La hora en curso cuenta como la primera de forecast_hours: 13 deja 12 horas por delante.
    forecast_hours: 13,
    timezone: ZONA,
    ...extra,
  });
}

export function urlOpenMeteo() {
  return `https://api.open-meteo.com/v1/forecast?${consulta({ current: VARIABLES, hourly: VARIABLES })}`;
}

export function urlEnsamble() {
  const modelos = Object.values(MODELOS_ENSAMBLE).map((m) => m.api).join(',');
  return `https://ensemble-api.open-meteo.com/v1/ensemble?${consulta({ hourly: 'precipitation', models: modelos })}`;
}

/** Pronóstico de cada modelo por separado, para el modelo corregido. */
export function urlModelos() {
  return `https://api.open-meteo.com/v1/forecast?${consulta({
    hourly: VARIABLES_MOS.join(','),
    models: Object.values(MODELOS_MOS).join(','),
    // La ventana de 6 h de la última hora proyectada necesita 6 horas más.
    forecast_hours: 13 + VENTANA_H,
  })}`;
}

async function pedirJSON(url) {
  const r = await fetch(url, { cache: 'no-store' });
  if (!r.ok) throw new Error(`Open-Meteo respondió ${r.status}`);
  return r.json();
}

/**
 * Trae el clima actual, los modelos por separado y los ensambles. Si fallan los modelos o
 * los ensambles, sigue sin ellos; si falla el clima actual, lanza error.
 */
export async function consultarOpenMeteo() {
  const [clima, modelos, ensamble] = await Promise.allSettled(
    [urlOpenMeteo(), urlModelos(), urlEnsamble()].map(pedirJSON),
  );
  if (clima.status === 'rejected') throw clima.reason;
  const valor = (r, nombre) => {
    if (r.status === 'fulfilled') return r.value;
    console.warn(`${nombre} no disponible:`, r.reason);
    return null;
  };
  return { clima: clima.value, modelos: valor(modelos, 'Modelos'), ensamble: valor(ensamble, 'Ensambles') };
}

/** "2026-10-25T14:00" (hora local de Guayaquil) → Date */
export function aFecha(local) {
  return new Date(Date.parse(`${local}:00Z`) - DESFASE_MS);
}

/** Date → "2026-10-25T14:00" en hora local de Guayaquil */
export function aLocal(fecha) {
  return new Date(fecha.getTime() + DESFASE_MS).toISOString().slice(0, 16);
}

/** Suma horas a una hora local y devuelve otra hora local. */
export function sumarHoras(local, horas) {
  return aLocal(new Date(aFecha(local).getTime() + horas * 3600 * 1000));
}

/** Diferencia en horas entre dos horas locales (b − a). */
export function horasEntre(a, b) {
  return (aFecha(b) - aFecha(a)) / 3600000;
}

const redondear = (x, d = 1) => Math.round(x * 10 ** d) / 10 ** d;

// ---------- ensambles ----------

/**
 * Agrupa las series del ensamble por modelo.
 * Las claves vienen como "precipitation_ecmwf_ifs025_ensemble" (control)
 * y "precipitation_member07_ecmwf_ifs025_ensemble" (miembros); igual con "ncep_gefs025".
 * @returns {{ horas: string[], modelos: Record<string, (number|null)[][]> }}
 */
export function seriesEnsamble(json) {
  const { time, ...resto } = json.hourly;
  const modelos = {};
  for (const [clave, valores] of Object.entries(resto)) {
    if (!clave.startsWith('precipitation')) continue;
    const nombre = Object.entries(MODELOS_ENSAMBLE).find(([, m]) => clave.includes(m.clave))?.[0];
    if (!nombre) continue;
    (modelos[nombre] ??= []).push(valores);
  }
  return { horas: time, modelos };
}

const llueve = (mm) => typeof mm === 'number' && mm >= UMBRAL_LLUVIA_MM;

/** Fracción de simulaciones con lluvia en el conjunto de índices dado; null si no hay datos. */
function fraccion(miembros, indices) {
  const validos = miembros.filter((m) => indices.every((i) => m[i] !== null && m[i] !== undefined));
  if (!validos.length) return null;
  return validos.filter((m) => indices.some((i) => llueve(m[i]))).length / validos.length;
}

/** Promedia los modelos disponibles por igual (no por número de simulaciones). */
function promedioModelos(porModelo) {
  const v = Object.values(porModelo).filter((x) => x !== null);
  return v.length ? v.reduce((s, x) => s + x, 0) / v.length : null;
}

/**
 * Probabilidad del ensamble en una hora y en la ventana de VENTANA_H horas que empieza ahí.
 * @returns {{ probabilidad: number|null, modelos: Record<string, number|null>,
 *             ventana: number|null, ventanaModelos: Record<string, number|null> } | null}
 */
export function probabilidadEnsamble(series, hora) {
  if (!series) return null;
  const i = series.horas.indexOf(hora);
  if (i < 0) return null;
  const indicesVentana = [];
  for (let k = 0; k < VENTANA_H; k++) {
    const j = series.horas.indexOf(sumarHoras(hora, k));
    if (j >= 0) indicesVentana.push(j);
  }
  const modelos = {};
  const ventanaModelos = {};
  for (const [nombre, miembros] of Object.entries(series.modelos)) {
    modelos[nombre] = fraccion(miembros, [i]);
    ventanaModelos[nombre] = indicesVentana.length === VENTANA_H ? fraccion(miembros, indicesVentana) : null;
  }
  return {
    probabilidad: promedioModelos(modelos),
    modelos,
    ventana: promedioModelos(ventanaModelos),
    ventanaModelos,
  };
}

// ---------- filas por hora ----------

const pct = (p) => (p === null || p === undefined ? null : redondear(p * 100));
const primeraDisponible = (opciones) => opciones.find(([, v]) => v !== null && v !== undefined);

function fila(hora, T, HR, P, P3, series, modelos, contexto) {
  const heuristica = calcular({
    P, P3, T, HR,
    mes: Number(hora.slice(5, 7)),
    hora: Number(hora.slice(11, 13)),
  });
  const ens = probabilidadEnsamble(series, hora);
  const iMod = modelos ? modelos.hourly.time.indexOf(hora) : -1;
  const mos = iMod >= 0 ? probabilidadesMOS(modelos.hourly, iMod, contexto) : null;
  const [fuente, p] = primeraDisponible([
    ['corregido', mos?.hora],
    ['ensamble', ens?.probabilidad],
    ['heuristica', heuristica.probabilidad],
  ]);
  return {
    hora,
    probabilidad: pct(p),
    fuente,
    corregido: pct(mos?.hora),
    ensamble: pct(ens?.probabilidad),
    heuristica: pct(heuristica.probabilidad),
    temperatura: redondear(T),
    humedad: Math.round(HR),
    presion: redondear(P),
    mos,
    ens,
    detalle: heuristica.detalle,
  };
}

/**
 * Convierte las respuestas de Open-Meteo en:
 * - actual: la lectura de ahora; su probabilidad es la de la hora en curso (de T0 a T0 + 1,
 *   que en Open-Meteo se llama T0 + 1) y proximas6h la de las 6 horas desde T0
 * - pasado: las horas ya terminadas (hasta T0), calculadas con los datos horarios
 * - proyeccion: las horas siguientes a la hora en curso, calculadas con el pronóstico
 *
 * contexto.nino: índices semanales de El Niño; contexto.aeropuerto: lluvia reportada en
 * SEGU hasta T0 ({hora, lluvia_ahora, lluvia_3h}), que solo se usa si es de T0;
 * contexto.rayos: rayos de la última hora (data/rayos.json → modelo, con «hasta» en hora local),
 * que solo se usan si terminan entre T0 − 20 min y T0 + 1 h (se entrenó con la hora antes de T0).
 */
export function procesarRespuesta(
  { clima, modelos = null, ensamble = null },
  { nino = null, aeropuerto = null, rayos = null } = {},
) {
  const series = ensamble ? seriesEnsamble(ensamble) : null;
  const h = clima.hourly;
  const porHora = new Map(h.time.map((t, i) => [t, i]));
  const presionEn = (hora) => {
    const i = porHora.get(hora);
    const p = i === undefined ? null : h.pressure_msl[i];
    return typeof p === 'number' ? p : null;
  };

  const c = clima.current;
  const horaActual = `${c.time.slice(0, 13)}:00`; // T0: la última hora terminada
  const horaLluvia = sumarHoras(horaActual, 1); // la hora en curso
  const P3 = presionEn(sumarHoras(horaActual, -3));
  const aeropuertoVigente = aeropuerto && aeropuerto.hora === horaActual ? aeropuerto : null;
  const desfaseRayos = rayos?.hasta ? horasEntre(horaActual, rayos.hasta) : NaN;
  const rayosVigentes = desfaseRayos >= -1 / 3 && desfaseRayos <= 1 ? rayos : null;
  const contextoAhora = { nino, aeropuerto: aeropuertoVigente, rayos: rayosVigentes };
  // Condiciones de ahora y «próximas 6 h» (desde T0, con el aeropuerto hasta T0)
  const { ens, mos, ...filaActual } = fila(
    horaActual, c.temperature_2m, c.relative_humidity_2m, c.pressure_msl, P3, series, modelos, contextoAhora,
  );
  const [fuente6h, p6] = primeraDisponible([
    ['corregido', mos?.proximas6h],
    ['ensamble', ens?.ventana],
  ]) ?? ['ninguna', null];
  // «Esta hora»: la hora en curso, con el aeropuerto hasta T0 como «lluvia previa»
  const iSig = modelos ? modelos.hourly.time.indexOf(horaLluvia) : -1;
  const mosSig = iSig >= 0 ? probabilidadesMOS(modelos.hourly, iSig, contextoAhora) : null;
  const ensSig = probabilidadEnsamble(series, horaLluvia);
  const [fuente, pHora] = primeraDisponible([
    ['corregido', mosSig?.hora],
    ['ensamble', ensSig?.probabilidad],
    ['heuristica', filaActual.heuristica / 100],
  ]);
  const actual = {
    ...filaActual,
    horaLluvia,
    probabilidad: pct(pHora),
    fuente,
    corregido: pct(mosSig?.hora),
    ensamble: pct(ensSig?.probabilidad),
    horaUsaAeropuerto: Boolean(mosSig?.horaUsaAeropuerto),
    horaUsaRayos: Boolean(mosSig?.horaUsaRayos),
    momento: c.time,
    presion3h: P3,
    proximas6h: pct(p6),
    proximas6hFuente: fuente6h,
    usaAeropuerto: Boolean(mos?.usaAeropuerto),
    usaRayos: Boolean(mos?.usaRayos),
    aeropuerto: aeropuertoVigente,
    rayos: rayosVigentes,
    ensamble6h: pct(ens?.ventana),
    modelos: ens ? {
      ahora: Object.fromEntries(Object.entries(ens.modelos).map(([k, v]) => [k, pct(v)])),
      proximas6h: Object.fromEntries(Object.entries(ens.ventanaModelos).map(([k, v]) => [k, pct(v)])),
    } : null,
  };

  const pasado = [];
  const proyeccion = [];
  h.time.forEach((hora, i) => {
    const T = h.temperature_2m[i];
    const HR = h.relative_humidity_2m[i];
    const P = h.pressure_msl[i];
    if (![T, HR, P].every((v) => typeof v === 'number')) return;
    if (hora === horaLluvia) return; // la hora en curso ya está en «actual»
    // Las próximas horas también usan el aeropuerto, con un modelo según cuántas horas faltan.
    const adelanto = horasEntre(horaActual, hora);
    const contexto = adelanto >= 2 && adelanto <= 6 ? { ...contextoAhora, adelanto } : { nino };
    const { ens: _e, mos: _m, detalle: _d, ...f } = fila(
      hora, T, HR, P, presionEn(sumarHoras(hora, -3)), series, modelos, contexto,
    );
    // Para no mezclar fuentes en la gráfica: si la hora actual usa el modelo corregido,
    // las horas donde no se puede calcular (bordes de la ventana de datos) se omiten.
    if (actual.fuente === 'corregido' && f.fuente !== 'corregido') return;
    (hora < horaLluvia ? pasado : proyeccion).push(f);
  });

  return { actual, pasado, proyeccion };
}

