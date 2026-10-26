// Revisa data/actual.json y data/rayos.json y, si toca, avisa por WhatsApp.
// Guarda en data/alertas.json qué avisos están activos para no repetirlos.
//
//   node scripts/avisar.mjs           decide y envía
//   node scripts/avisar.mjs --prueba  envía un mensaje de prueba

import { readFile, writeFile } from 'node:fs/promises';
import { PAGINA, decidir, estadoInicial } from './alertas.mjs';
import { enviarWhatsApp } from './whatsapp.mjs';

const carpeta = new URL('../data/', import.meta.url);

async function leerJSON(nombre, porDefecto) {
  try {
    return JSON.parse(await readFile(new URL(nombre, carpeta), 'utf8'));
  } catch (e) {
    if (e.code === 'ENOENT') return porDefecto;
    throw e;
  }
}

if (process.argv.includes('--prueba')) {
  const n = await enviarWhatsApp(`✅ Prueba de Lluvia en Fondo de Bikini: los avisos por WhatsApp funcionan. ${PAGINA}`);
  process.exit(n > 0 ? 0 : 1);
}

const estado = await leerJSON('alertas.json', estadoInicial());
const actual = await leerJSON('actual.json', null);
const rayos = await leerJSON('rayos.json', null);
const { mensajes, estado: nuevo } = decidir(estado, actual, rayos);

for (const m of mensajes) {
  console.log(`Aviso: ${m}`);
  await enviarWhatsApp(m);
}
if (!mensajes.length) console.log('Sin avisos nuevos.');
await writeFile(new URL('alertas.json', carpeta), `${JSON.stringify(nuevo, null, 2)}\n`);
