// Revisa data/actual.json y data/rayos.json y, si toca, avisa por Telegram y WhatsApp
// (los canales que estén configurados en los secretos de GitHub).
// Guarda en data/alertas.json qué avisos están activos para no repetirlos.
//
//   node scripts/avisar.mjs           decide y envía
//   node scripts/avisar.mjs --prueba  envía un mensaje de prueba

import { readFile, writeFile } from 'node:fs/promises';
import { PAGINA, decidir, estadoInicial } from './alertas.mjs';
import { enviarTelegram } from './telegram.mjs';
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

/** Envía por todos los canales configurados; devuelve a cuántos destinos llegó. */
async function enviar(texto) {
  return (await enviarTelegram(texto)) + (await enviarWhatsApp(texto));
}

if (process.argv.includes('--prueba')) {
  const n = await enviar(`✅ Prueba de Lluvia en Fondo de Bikini: los avisos funcionan. ${PAGINA}`);
  process.exit(n > 0 ? 0 : 1);
}

const estado = await leerJSON('alertas.json', estadoInicial());
const actual = await leerJSON('actual.json', null);
const rayos = await leerJSON('rayos.json', null);
const { mensajes, estado: nuevo } = decidir(estado, actual, rayos);

let entregados = 0;
for (const m of mensajes) {
  console.log(`Aviso: ${m}`);
  entregados += await enviar(m);
}
if (!mensajes.length) console.log('Sin avisos nuevos.');
// Si había avisos y no llegó ninguno (sin canales configurados o fallaron), no se marcan como
// enviados: se reintenta en la próxima ejecución.
const guardar = mensajes.length && entregados === 0 ? estado : nuevo;
await writeFile(new URL('alertas.json', carpeta), `${JSON.stringify(guardar, null, 2)}\n`);
