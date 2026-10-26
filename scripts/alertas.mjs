// Decide cuándo mandar un aviso por WhatsApp, sin repetir el mismo aviso una y otra vez.
//
// Dos avisos independientes:
// - lluvia: el modelo corregido da ≥ 80 % de lluvia en las próximas 6 horas. Se vuelve a
//   avisar solo después de que baje de 60 % (así no llega un mensaje cada hora).
// - rayos: el satélite ve una tormenta eléctrica a menos de 60 km. Avisa al aparecer y si se
//   acerca a menos de 25 km; como mucho un aviso de rayos por hora.

export const PAGINA = 'https://juanidlc.github.io/fondo-de-bikini/';
export const LLUVIA_ACTIVA = 80;
export const LLUVIA_DESACTIVA = 60;
export const RAYOS_MINIMOS = 3; // menos que esto puede ser ruido del sensor
export const ESPERA_RAYOS_MIN = 60;
const VIGENCIA_ACTUAL_MIN = 120;
const VIGENCIA_RAYOS_MIN = 20;

const minutosDesde = (iso, ahora) => (ahora - Date.parse(iso)) / 60000;
const nivelRayos = (r) => {
  if (!r || r.rayos < RAYOS_MINIMOS) return 0;
  return r.mas_cercano_km !== null && r.mas_cercano_km <= 25 ? 2 : 1;
};

export function estadoInicial() {
  return { lluvia: { activa: false, enviado: null }, rayos: { nivel: 0, enviado: null } };
}

/**
 * @param {object} estado    lo guardado en data/alertas.json
 * @param {object|null} actual   data/actual.json
 * @param {object|null} rayos    data/rayos.json
 * @param {number} ahora     Date.now()
 * @returns {{ mensajes: string[], estado: object }}
 */
export function decidir(estado, actual, rayos, ahora = Date.now()) {
  const nuevo = structuredClone(estado ?? estadoInicial());
  const mensajes = [];

  // Lluvia (solo con una lectura reciente del modelo corregido)
  const p6 = actual?.proximas6hFuente === 'corregido' && actual.generado
    && minutosDesde(actual.generado, ahora) <= VIGENCIA_ACTUAL_MIN ? actual.proximas6h : null;
  if (p6 !== null && p6 !== undefined) {
    if (!nuevo.lluvia.activa && p6 >= LLUVIA_ACTIVA) {
      nuevo.lluvia = { activa: true, enviado: new Date(ahora).toISOString() };
      mensajes.push(mensajeLluvia(p6, actual));
    } else if (nuevo.lluvia.activa && p6 < LLUVIA_DESACTIVA) {
      nuevo.lluvia.activa = false;
    }
  }

  // Rayos (solo con una lectura reciente del satélite)
  if (rayos?.generado && minutosDesde(rayos.generado, ahora) <= VIGENCIA_RAYOS_MIN) {
    const nivel = nivelRayos(rayos);
    const esperaCumplida = !nuevo.rayos.enviado || minutosDesde(nuevo.rayos.enviado, ahora) >= ESPERA_RAYOS_MIN;
    if (nivel > nuevo.rayos.nivel && (esperaCumplida || nivel === 2)) {
      nuevo.rayos = { nivel, enviado: new Date(ahora).toISOString() };
      mensajes.push(mensajeRayos(rayos));
    } else if (nivel === 0) {
      nuevo.rayos.nivel = 0;
    }
  }

  return { mensajes, estado: nuevo };
}

export function mensajeLluvia(p6, actual) {
  const aero = actual?.aeropuerto?.lluvia_ahora === 1 ? ' Ya está lloviendo en el aeropuerto.' : '';
  return `🌧️ Lluvia en Fondo de Bikini: ${Math.round(p6)} % de probabilidad de lluvia en Guayaquil `
    + `en las próximas 6 horas.${aero} Lleva paraguas. ${PAGINA}`;
}

export function mensajeRayos(r) {
  const donde = r.mas_cercano_km <= 25
    ? `muy cerca de Guayaquil (a ${Math.round(r.mas_cercano_km)} km)`
    : `a ${Math.round(r.mas_cercano_km)} km${r.rumbo ? ` al ${r.rumbo}` : ''} de Guayaquil`;
  return `⚡ Tormenta eléctrica ${donde}: ${r.rayos} rayos en los últimos ${r.minutos} minutos. `
    + `Puede llover fuerte pronto. ${PAGINA}`;
}
