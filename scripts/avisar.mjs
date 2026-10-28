// Revisa data/actual.json y data/rayos.json y, si toca, avisa por Telegram y WhatsApp
// (los canales que estén configurados en los secretos de GitHub).
// Guarda en data/alertas.json qué avisos están activos para no repetirlos.
//
//   node scripts/avisar.mjs           decide y envía
//   node scripts/avisar.mjs --prueba  envía un mensaje de prueba

import { readFile, writeFile } from 'node:fs/promises';
import { consultarOpenMeteo, procesarRespuesta } from '../assets/openmeteo.js';
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

/**
 * Lectura de este momento, como la calcula la página: la guardada en actual.json es de la última
 * hora, y los rayos cambian cada 10 minutos. Si no se puede, se usa la guardada.
 */
async function lecturaDeAhora(guardada, rayos) {
  try {
    const { actual, proyeccion } = procesarRespuesta(await consultarOpenMeteo(), {
      nino: await leerJSON('nino.json', null),
      aeropuerto: (await leerJSON('aeropuerto.json', null)) ?? guardada?.aeropuerto ?? null,
      rayos: rayos?.modelo ?? null,
    });
    return { ...actual, proyeccion, generado: new Date().toISOString() };
  } catch (e) {
    console.warn(`No se pudo recalcular (${e.message}); se usa la última lectura guardada.`);
    return guardada;
  }
}

const estado = await leerJSON('alertas.json', estadoInicial());
const rayos = await leerJSON('rayos.json', null);
const actual = await lecturaDeAhora(await leerJSON('actual.json', null), rayos);
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
