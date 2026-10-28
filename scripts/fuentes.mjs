// Fuentes que solo consulta el workflow (sus servidores no aceptan llamadas desde el navegador):
// - lluvia reportada en el aeropuerto de Guayaquil (METAR de SEGU), de aviationweather.gov
// - índice semanal de El Niño, de NOAA CPC
// Las reglas son las mismas que en analisis/entrenar.py.

import { aLocal, sumarHoras } from '../assets/openmeteo.js';

// RA (lluvia) o DZ (llovizna), con o sin SH (chubasco), TS (tormenta), intensidad (+/-)
// o RE (reciente). VC (en las cercanías) no cuenta.
const TOKEN_LLUVIA = /^[+-]?(RE)?(TS|SH)?(RA|DZ)+$/;

export function huboLluvia(metar) {
  // El pronóstico de tendencia (TEMPO, BECMG) y los comentarios (RMK) no son observación.
  const cuerpo = String(metar).split(/\s(?:NOSIG|TEMPO|BECMG|RMK)\b/)[0];
  return cuerpo.split(/\s+/).some((t) => TOKEN_LLUVIA.test(t));
}

/** Hora local a la que se asigna un reporte: la hora T cubre (T − 1 h, T]. */
function horaDelReporte(fecha) {
  const local = aLocal(fecha); // "YYYY-MM-DDTHH:MM"
  const base = `${local.slice(0, 13)}:00`;
  return local.endsWith(':00') ? base : sumarHoras(base, 1);
}

/**
 * Resume los reportes en las dos variables del modelo para la hora actual:
 * lluvia_ahora (en la última hora) y lluvia_3h (en las últimas 3). Si a alguna de esas horas
 * le falta reporte, la variable vale null, igual que en el entrenamiento.
 * lloviendo: si algún reporte de la hora en curso (un especial, por ejemplo) ya trae lluvia,
 * {hora: la hora en curso, desde: "HH:MM" del primero}; si no, null.
 * @param {{fecha: Date, metar: string}[]} reportes
 */
export function resumirAeropuerto(reportes, horaActual) {
  const porHora = new Map();
  for (const r of reportes) {
    const h = horaDelReporte(r.fecha);
    porHora.set(h, (porHora.get(h) ?? 0) || (huboLluvia(r.metar) ? 1 : 0));
  }
  const ultimas = [0, -1, -2].map((k) => porHora.get(sumarHoras(horaActual, k)));
  const enCurso = sumarHoras(horaActual, 1);
  const primera = reportes
    .filter((r) => horaDelReporte(r.fecha) === enCurso && huboLluvia(r.metar))
    .sort((a, b) => a.fecha - b.fecha)[0];
  return {
    hora: horaActual,
    lluvia_ahora: ultimas[0] ?? null,
    lluvia_3h: ultimas.every((v) => v !== undefined) ? Math.max(...ultimas) : null,
    reportes: reportes.length,
    lloviendo: primera ? { hora: enCurso, desde: aLocal(primera.fecha).slice(11, 16) } : null,
  };
}

export async function consultarAeropuerto(horaActual) {
  const r = await fetch('https://aviationweather.gov/api/data/metar?ids=SEGU&hours=5&format=json');
  if (!r.ok) throw new Error(`aviationweather.gov respondió ${r.status}`);
  const datos = await r.json();
  const reportes = datos.map((m) => ({
    fecha: typeof m.obsTime === 'number' ? new Date(m.obsTime * 1000) : new Date(m.reportTime),
    metar: m.rawOb,
  }));
  return resumirAeropuerto(reportes, horaActual);
}

/** Índices semanales (Niño 1+2 y 3.4) del archivo de texto de CPC. */
export function leerNino(texto) {
  const meses = { JAN: 1, FEB: 2, MAR: 3, APR: 4, MAY: 5, JUN: 6, JUL: 7, AUG: 8, SEP: 9, OCT: 10, NOV: 11, DEC: 12 };
  const filas = [];
  for (const linea of texto.split('\n')) {
    const m = linea.match(/^\s*(\d{2})([A-Z]{3})(\d{4})\s+(.*)$/);
    if (!m || !meses[m[2]]) continue;
    // Cada región trae temperatura y anomalía, a veces pegadas: "23.4-0.4"
    const n = (m[4].match(/-?\d+\.\d/g) ?? []).map(Number);
    if (n.length !== 8) continue;
    filas.push({
      semana: `${m[3]}-${String(meses[m[2]]).padStart(2, '0')}-${m[1]}`,
      nino12: n[1],
      nino34: n[5],
    });
  }
  return filas;
}

export async function consultarNino() {
  const r = await fetch('https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for');
  if (!r.ok) throw new Error(`CPC respondió ${r.status}`);
  return leerNino(await r.text());
}
