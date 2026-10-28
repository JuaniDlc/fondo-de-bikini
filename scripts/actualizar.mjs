// Lo corre el workflow cada hora: consulta Open-Meteo, el aeropuerto y El Niño, calcula
// la probabilidad y escribe data/actual.json, data/historial.json y data/nino.json.

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { consultarOpenMeteo, procesarRespuesta, sumarHoras } from '../assets/openmeteo.js';
import { consultarAeropuerto, consultarNino } from './fuentes.mjs';

const DIAS_HISTORIAL = 7;
const SEMANAS_NINO = 12;
const carpeta = new URL('../data/', import.meta.url);

async function leerJSON(nombre, porDefecto) {
  try {
    return JSON.parse(await readFile(new URL(nombre, carpeta), 'utf8'));
  } catch (e) {
    if (e.code === 'ENOENT') return porDefecto;
    throw e;
  }
}

const sinDetalle = ({ detalle, momento, presion3h, modelos, ...resto }) => resto;

async function intentar(nombre, f, porDefecto) {
  try {
    return await f();
  } catch (e) {
    console.warn(`${nombre}: ${e.message}`);
    return porDefecto;
  }
}

const [respuesta, ninoNuevo] = await Promise.all([
  consultarOpenMeteo(),
  intentar('El Niño', consultarNino, null),
]);
// Si CPC no responde, se sigue con el último índice guardado.
const nino = ninoNuevo ? ninoNuevo.slice(-SEMANAS_NINO) : await leerJSON('nino.json', null);
const horaActual = `${respuesta.clima.current.time.slice(0, 13)}:00`;
const aeropuerto = await intentar('Aeropuerto', () => consultarAeropuerto(horaActual), null);

// Rayos de la última hora: los escribe scripts/rayos.py, que corre justo antes en el workflow.
const rayos = (await leerJSON('rayos.json', null))?.modelo ?? null;
const { actual, pasado, proyeccion } = procesarRespuesta(respuesta, { nino, aeropuerto, rayos });

// Historial: una fila por hora. La lectura de esta hora reemplaza a la que hubiera;
// las horas pasadas que falten (primer uso, ejecuciones atrasadas) se rellenan con
// los datos horarios de Open-Meteo, sin tocar las que ya existen.
const historial = await leerJSON('historial.json', []);
const porHora = new Map(historial.map((f) => [f.hora, f]));
for (const f of pasado) {
  if (!porHora.has(f.hora)) porHora.set(f.hora, { ...f, origen: 'horario' });
}
// La lectura se guarda en la hora que pronostica (la hora en curso), como las demás filas.
porHora.set(actual.horaLluvia, { ...sinDetalle(actual), hora: actual.horaLluvia, horaLectura: actual.hora, origen: 'lectura' });

const desde = sumarHoras(actual.hora, -24 * DIAS_HISTORIAL);
const filas = [...porHora.values()]
  .filter((f) => f.hora > desde && f.hora <= actual.horaLluvia)
  .sort((a, b) => a.hora.localeCompare(b.hora));

const salidaActual = {
  generado: new Date().toISOString(),
  ...actual,
  proyeccion,
};

await mkdir(carpeta, { recursive: true });
await writeFile(new URL('actual.json', carpeta), `${JSON.stringify(salidaActual, null, 2)}\n`);
if (nino) await writeFile(new URL('nino.json', carpeta), `${JSON.stringify(nino, null, 1)}\n`);
if (aeropuerto) {
  await writeFile(new URL('aeropuerto.json', carpeta),
    `${JSON.stringify({ generado: new Date().toISOString(), ...aeropuerto }, null, 1)}\n`);
}
// Una fila por línea para que los diffs del repositorio sean legibles.
await writeFile(
  new URL('historial.json', carpeta),
  `[\n${filas.map((f) => `  ${JSON.stringify(f)}`).join(',\n')}\n]\n`,
);

console.log(
  `${actual.hora} · esta hora ${actual.probabilidad} % (${actual.fuente}) · ` +
    `próximas 6 h ${actual.proximas6h ?? '—'} % (${actual.proximas6hFuente}` +
    `${actual.usaAeropuerto ? ', con aeropuerto' : ''}${actual.usaRayos ? ' y rayos' : ''}) · ensamble ${actual.ensamble ?? '—'} % · ` +
    `heurística ${actual.heuristica} % · aeropuerto: ${aeropuerto ? (aeropuerto.lluvia_ahora ? 'lloviendo' : 'sin lluvia') : 'sin dato'} · ` +
    `El Niño 1+2: ${nino?.at(-1)?.nino12 ?? '—'} °C · ${actual.temperatura} °C · ` +
    `${actual.humedad} % · ${actual.presion} hPa · historial: ${filas.length} filas`,
);
