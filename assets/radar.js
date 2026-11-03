// Tarjetas de rayos: si hay tormenta eléctrica, a qué distancia y cerca de qué población. Los datos
// son de data/rayos.json (scripts/rayos.py), medidos desde el centro de Guayaquil. No van aquí los
// lugares del secreto LUGARES: solo poblaciones y sectores conocidos.

export const RAYOS_MINIMOS = 3; // menos que esto puede ser ruido del sensor
export const CERCA_KM = 25;
const VIGENCIA_MIN = 30;

/** 0: sin rayos; 1: a menos de 60 km; 2: a menos de CERCA_KM. Los avisos usan el mismo criterio. */
export function nivelRayos(r) {
  if (!r || r.rayos < RAYOS_MINIMOS) return 0;
  return r.mas_cercano_km !== null && r.mas_cercano_km <= CERCA_KM ? 2 : 1;
}

// [nombre, rumbo en grados, km desde el centro, lado de la etiqueta, cuánto subirla si choca]
export const REGION = [
  ['Durán', 67, 6, 'start'], ['Chongón', 256, 22, 'end'], ['Taura', 128, 22, 'start'],
  ['Yaguachi', 65, 24, 'start', -5], ['Samborondón', 36, 31, 'start'], ['Nobol', 335, 33, 'end'],
  ['Milagro', 79, 34, 'start', 5], ['Daule', 345, 38, 'start'], ['Lomas de Sargentillo', 328, 41, 'end'],
  ['Jujan', 54, 51, 'start'], ['Puerto Inca', 136, 54, 'start'], ['Pedro Carbo', 317, 56, 'end'],
  ['El Triunfo', 106, 57, 'end'], ['Babahoyo', 43, 59, 'start'],
];
export const CIUDAD = [
  ['Aeropuerto', 11, 3.7, 'start', -7], ['Ceibos', 296, 6, 'end'], ['Maps', 317, 5.5, 'end', -2], ['Durán', 67, 6, 'start'],
  ['La Puntilla', 24, 7, 'start'], ['Isla Santay', 128, 5, 'start'], ['Guasmo', 183, 6, 'start'],
  ['Nueva Prosperina', 314, 11, 'end'], ['Mucho Lote', 344, 12, 'start'], ['Pascuales', 341, 15, 'end'],
  ['Chongón', 256, 22, 'start'], ['Taura', 128, 22, 'start'], ['Yaguachi', 65, 24, 'end'],
];
const SECTORES = [...CIUDAD.filter(([n]) => n !== 'Aeropuerto'), ...REGION.filter(([n]) => !CIUDAD.some(([c]) => c === n))];

const RUMBOS = ['norte', 'noreste', 'este', 'sureste', 'sur', 'suroeste', 'oeste', 'noroeste'];
const rumboEnPalabras = (grados) => RUMBOS[Math.round(grados / 45) % 8];

/** Distancia en km entre dos puntos dados como [rumbo, km] desde el mismo centro. */
function entre([r1, d1], [r2, d2]) {
  const a = ((r1 - r2) * Math.PI) / 180;
  return Math.sqrt(d1 ** 2 + d2 ** 2 - 2 * d1 * d2 * Math.cos(a));
}

/** Nombre del lugar más cercano a un punto, si está a menos de 15 km de él. */
export function cercaDe(rumbo, km) {
  const [mejor, distancia] = SECTORES
    .map(([nombre, r, d]) => [nombre, entre([rumbo, km], [r, d])])
    .reduce((a, b) => (b[1] < a[1] ? b : a));
  return distancia <= 15 ? mejor : null;
}

/** Qué dicen las tarjetas; null si los datos están viejos. */
export function resumenRayos(r, ahora = Date.now()) {
  const minutos = r?.generado ? Math.round((ahora - Date.parse(r.generado)) / 60000) : Infinity;
  if (minutos > VIGENCIA_MIN) return null;
  const nivel = nivelRayos(r);
  const puntos = (r.puntos ?? []).filter((p) => p.every(Number.isFinite));
  const base = { nivel, minutos: Math.max(minutos, 0), puntos };
  if (!nivel) return { ...base, etiqueta: 'Sin tormenta eléctrica', titulo: '' };
  // Se ubica por la celda con rayos más cercana al centro; puede haber más rayos en otras zonas.
  const cercano = puntos[0];
  const lado = cercano ? rumboEnPalabras(cercano[1]) : r.rumbo;
  const pueblo = cercano ? cercaDe(cercano[1], cercano[0]) : null;
  return {
    ...base,
    etiqueta: 'Hay tormenta eléctrica',
    titulo: `A ${Math.round(r.mas_cercano_km)} km${lado ? ` al ${lado}` : ''}${pueblo ? `, cerca de ${pueblo}` : ''}`,
  };
}

const ANCHO = 440;
const MEDIO = ANCHO / 2;
const R_MAX = 195;
const NUM = (x) => x.toFixed(1);
const MAXIMO_PULSOS = 6;

/** Radar en SVG: el centro de Guayaquil, sus anillos, las poblaciones y los rayos. */
export function svgRadar({ radioKm, anillos, lugares, puntos, nivel }) {
  const k = R_MAX / radioKm;
  const pos = (rumbo, km) => {
    const a = ((rumbo - 90) * Math.PI) / 180;
    return [MEDIO + Math.cos(a) * km * k, MEDIO + Math.sin(a) * km * k];
  };
  // Del más grande al más chico, para que el relleno no tape a los de adentro. Solo se pinta si hay peligro.
  const partes = [...anillos].sort((a, b) => b - a).map((km) => {
    const clase = km === CERCA_KM && nivel === 2 ? 'anillo cerca' : 'anillo';
    return `<circle class="${clase}" cx="${MEDIO}" cy="${MEDIO}" r="${NUM(km * k)}"/>`
      + `<text class="escala" x="${MEDIO}" y="${NUM(MEDIO + km * k - 4)}" text-anchor="middle">${km} km</text>`;
  });
  partes.unshift(...[['N', MEDIO, 14], ['S', MEDIO, ANCHO - 6], ['E', ANCHO - 10, MEDIO + 4], ['O', 10, MEDIO + 4]]
    .map(([t, x, y]) => `<text class="escala" x="${x}" y="${y}" text-anchor="middle">${t}</text>`));
  for (const [nombre, rumbo, km, lado, subir = 0] of lugares) {
    const [x, y] = pos(rumbo, km);
    partes.push(`<circle class="pueblo" cx="${NUM(x)}" cy="${NUM(y)}" r="2.5"/>`
      + `<text class="pueblo" x="${NUM(x + (lado === 'start' ? 6 : -6))}" y="${NUM(y + 4 + subir)}" text-anchor="${lado}">${nombre}</text>`);
  }
  // Los rayos después de los nombres, para que no queden tapados; son translúcidos para poder leerlos.
  // Con tormenta, las zonas más cercanas lanzan una onda (los puntos vienen del más cercano al más lejano).
  puntos.filter((p) => p[0] <= radioKm).forEach(([km, rumbo, n], i) => {
    const [x, y] = pos(rumbo, km);
    const radio = NUM(Math.min(3 + Math.sqrt(n), 8));
    if (nivel && i < MAXIMO_PULSOS) {
      partes.push(`<circle class="pulso pulso-${i % 3} nivel-${nivel}" cx="${NUM(x)}" cy="${NUM(y)}" r="${radio}"/>`);
    }
    partes.push(`<circle class="rayo nivel-${nivel}" cx="${NUM(x)}" cy="${NUM(y)}" r="${radio}"/>`);
  });
  partes.push(`<circle class="centro" cx="${MEDIO}" cy="${MEDIO}" r="4"/>`
    + `<text class="centro" x="${MEDIO}" y="${MEDIO + 16}" text-anchor="middle">Guayaquil</text>`);
  const hay = puntos.filter((p) => p[0] <= radioKm).length;
  return `<svg viewBox="0 0 ${ANCHO} ${ANCHO}" role="img" aria-label="Radar de rayos a ${radioKm} km de Guayaquil: ${hay ? `${hay} zonas con rayos` : 'sin rayos'}">${partes.join('')}</svg>`;
}
