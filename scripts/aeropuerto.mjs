// Lo corre el workflow «Rayos» cada 10 minutos: lee los reportes del aeropuerto (METAR y los
// especiales, SPECI) y escribe data/aeropuerto.json, para que la página y los avisos sepan
// enseguida si empezó a llover, sin esperar la lectura de cada hora.
// Solo reescribe el archivo si cambió algo, para no hacer un commit cada 10 minutos.

import { readFile, writeFile } from 'node:fs/promises';
import { aLocal } from '../assets/openmeteo.js';
import { consultarAeropuerto } from './fuentes.mjs';

const archivo = new URL('../data/aeropuerto.json', import.meta.url);
const horaActual = `${aLocal(new Date()).slice(0, 13)}:00`;
const resumen = await consultarAeropuerto(horaActual);

const anterior = await readFile(archivo, 'utf8').then(JSON.parse, () => null);
const { generado: _g, ...sinFecha } = anterior ?? {};
if (JSON.stringify(sinFecha) === JSON.stringify(resumen)) {
  console.log('Aeropuerto sin cambios.');
} else {
  await writeFile(archivo, `${JSON.stringify({ generado: new Date().toISOString(), ...resumen }, null, 1)}\n`);
  console.log(`Aeropuerto: ${JSON.stringify(resumen)}`);
}
