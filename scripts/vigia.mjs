// Lo corre el workflow «Vigía de datos» cada hora: mira los datos en la página publicada, no en el
// repositorio, así también nota si falla la publicación. Si alguno está atrasado, termina con error y
// GitHub avisa por correo. No usa el canal de Telegram: ese es público y es para avisos de lluvia.

import { pathToFileURL } from 'node:url';

const PAGINA = 'https://juanidlc.github.io/fondo-de-bikini/data/';
// Minutos: infrarrojo cada 10 y la lectura cada hora, con margen por atrasos de GitHub.
export const LIMITES = { 'infrarrojo.json': 60, 'actual.json': 150 };
const INTENTOS = 3;

/** Lista de problemas a partir de {archivo: generado (texto ISO) o null}. */
export function atrasados(generados, ahora) {
  return Object.entries(LIMITES).flatMap(([archivo, limite]) => {
    const fecha = Date.parse(generados[archivo]);
    if (Number.isNaN(fecha)) return [`${archivo}: no se pudo leer`];
    const minutos = Math.round((ahora - fecha) / 60000);
    return minutos > limite ? [`${archivo}: tiene ${minutos} min (límite ${limite})`] : [];
  });
}

async function generado(archivo) {
  for (let i = 1; i <= INTENTOS; i++) {
    try {
      const r = await fetch(`${PAGINA}${archivo}?t=${Date.now()}`);
      if (r.ok) return (await r.json()).generado ?? null;
      console.warn(`${archivo}: HTTP ${r.status}`);
    } catch (e) {
      console.warn(`${archivo}: ${e.message}`);
    }
    if (i < INTENTOS) await new Promise((listo) => { setTimeout(listo, 20000); });
  }
  return null;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const archivos = Object.keys(LIMITES);
  const fechas = await Promise.all(archivos.map(generado));
  const problemas = atrasados(Object.fromEntries(archivos.map((a, i) => [a, fechas[i]])), Date.now());
  if (problemas.length) {
    console.error(`Datos atrasados:\n${problemas.join('\n')}`);
    process.exit(1);
  }
  console.log('Datos al día.');
}
