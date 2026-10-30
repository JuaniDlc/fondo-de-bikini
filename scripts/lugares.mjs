// Lo corre el workflow «Rayos» cada 10 minutos: el pronóstico por hora en el aeropuerto y en los
// lugares del secreto LUGARES, con los rayos y el infrarrojo medidos desde cada uno (los calculan
// scripts/rayos.py y scripts/infrarrojo.py en LUGARES_SALIDA y LUGARES_IR, que no se guardan en el
// repositorio).
// Escribe data/lugares.json solo con nombres y porcentajes: nunca coordenadas ni distancias, para
// que no se pueda deducir dónde quedan. Solo lo reescribe si algo cambió al menos CAMBIO puntos.

import { readFile, writeFile } from 'node:fs/promises';
import { consultarOpenMeteo, procesarRespuesta } from '../assets/openmeteo.js';

const HORAS = 6;
const CAMBIO = 3;
const carpeta = new URL('../data/', import.meta.url);
const leerJSON = (url) => readFile(url, 'utf8').then(JSON.parse, () => null);

const rayos = await leerJSON(process.env.LUGARES_SALIDA);
const ir = (await leerJSON(process.env.LUGARES_IR)) ?? {};
if (!rayos) {
  console.log('Sin rayos por lugar: no se calcula.');
  process.exit(0);
}
const nino = await leerJSON(new URL('nino.json', carpeta));
const aeropuerto = (await leerJSON(new URL('aeropuerto.json', carpeta)))
  ?? (await leerJSON(new URL('actual.json', carpeta)))?.aeropuerto ?? null;
const respuesta = await consultarOpenMeteo();

const lugares = Object.entries(rayos).map(([nombre, r]) => {
  const { actual, proyeccion } = procesarRespuesta(respuesta, {
    nino, aeropuerto, rayos: r, ir: ir[nombre] ?? null, enAeropuerto: nombre === 'Aeropuerto',
  });
  const horas = [{ hora: actual.horaLluvia, probabilidad: actual.probabilidad }, ...proyeccion].slice(0, HORAS);
  return {
    nombre,
    usaRayos: actual.horaUsaRayos,
    horas: horas.map((f) => ({ hora: f.hora, probabilidad: Math.round(f.probabilidad) })),
  };
});

const archivo = new URL('lugares.json', carpeta);
const anterior = await leerJSON(archivo);
const clave = (l) => l.map((x) => `${x.nombre}|${x.horas.map((h) => h.hora).join(',')}`).join(';');
const cambio = !anterior || clave(anterior.lugares) !== clave(lugares) || lugares.some((l, i) =>
  l.horas.some((h, j) => Math.abs(h.probabilidad - anterior.lugares[i].horas[j].probabilidad) >= CAMBIO));
for (const l of lugares) console.log(`${l.nombre}: ${l.horas.map((h) => `${h.probabilidad} %`).join(' · ')}`);
if (cambio) {
  await writeFile(archivo, `${JSON.stringify({ generado: new Date().toISOString(), lugares }, null, 1)}\n`);
} else {
  console.log(`Sin cambios de ${CAMBIO} puntos o más: no se reescribe.`);
}
