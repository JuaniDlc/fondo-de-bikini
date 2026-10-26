// Decide cuándo mandar un aviso (Telegram, WhatsApp), sin repetir el mismo aviso una y otra vez.
//
// Dos avisos independientes, cada uno con su mensaje de cierre:
// - lluvia: el modelo corregido da ≥ 80 % de lluvia en las próximas 6 horas. Cuando baja de
//   60 %, avisa que bajó el riesgo y se rearma (así no llega un mensaje cada hora).
// - rayos: el satélite ve una tormenta eléctrica a menos de 60 km. Avisa al aparecer y si se
//   acerca a menos de 25 km; como mucho un aviso de rayos por hora. Si avisó, avisa también
//   cuando lleva 30 minutos sin rayos cerca.

export const PAGINA = 'https://juanidlc.github.io/fondo-de-bikini/';
export const LLUVIA_ACTIVA = 80;
export const LLUVIA_DESACTIVA = 60;
export const RAYOS_MINIMOS = 3; // menos que esto puede ser ruido del sensor
export const ESPERA_RAYOS_MIN = 60;
export const SIN_RAYOS_MIN = 30; // sin rayos este tiempo = la tormenta se alejó
const VIGENCIA_ACTUAL_MIN = 120;
const VIGENCIA_RAYOS_MIN = 20;

const minutosDesde = (iso, ahora) => (ahora - Date.parse(iso)) / 60000;
const nivelRayos = (r) => {
  if (!r || r.rayos < RAYOS_MINIMOS) return 0;
  return r.mas_cercano_km !== null && r.mas_cercano_km <= 25 ? 2 : 1;
};

export function estadoInicial() {
  return {
    lluvia: { activa: false, enviado: null },
    rayos: { nivel: 0, enviado: null, avisada: false, ultimoRayo: null },
  };
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
      mensajes.push(mensajeLluviaFin(p6));
    }
  }

  // Rayos (solo con una lectura reciente del satélite)
  if (rayos?.generado && minutosDesde(rayos.generado, ahora) <= VIGENCIA_RAYOS_MIN) {
    const r = nuevo.rayos;
    r.avisada ??= r.nivel > 0; // estados guardados antes de que existiera el aviso de cierre
    const nivel = nivelRayos(rayos);
    if (nivel > 0) r.ultimoRayo = rayos.generado;
    const esperaCumplida = !r.enviado || minutosDesde(r.enviado, ahora) >= ESPERA_RAYOS_MIN;
    if (nivel > r.nivel && (esperaCumplida || nivel === 2)) {
      Object.assign(r, { nivel, enviado: new Date(ahora).toISOString(), avisada: true });
      mensajes.push(mensajeRayos(rayos));
    } else if (nivel === 0) {
      r.nivel = 0;
      const ultimo = r.ultimoRayo ?? r.enviado;
      if (r.avisada && ultimo && minutosDesde(ultimo, ahora) >= SIN_RAYOS_MIN) {
        r.avisada = false;
        mensajes.push(mensajeRayosFin());
      }
    }
  }

  return { mensajes, estado: nuevo };
}

export function mensajeLluvia(p6, actual) {
  const aero = actual?.aeropuerto?.lluvia_ahora === 1 ? ' Ya está lloviendo en el aeropuerto.' : '';
  return `🌧️ Lluvia en Fondo de Bikini: ${Math.round(p6)} % de probabilidad de lluvia en Guayaquil `
    + `en las próximas 6 horas.${aero} Lleva paraguas. ${PAGINA}`;
}

export function mensajeLluviaFin(p6) {
  return `✅ Bajó el riesgo de lluvia en Guayaquil: ahora ${Math.round(p6)} % de probabilidad `
    + `en las próximas 6 horas. ${PAGINA}`;
}

export function mensajeRayosFin() {
  return `✅ La tormenta eléctrica se alejó de Guayaquil: no hay rayos a menos de 60 km desde hace `
    + `${SIN_RAYOS_MIN} minutos. ${PAGINA}`;
}

export function mensajeRayos(r) {
  const donde = r.mas_cercano_km <= 25
    ? `muy cerca de Guayaquil (a ${Math.round(r.mas_cercano_km)} km)`
    : `a ${Math.round(r.mas_cercano_km)} km${r.rumbo ? ` al ${r.rumbo}` : ''} de Guayaquil`;
  return `⚡ Tormenta eléctrica ${donde}: ${r.rayos} rayos en los últimos ${r.minutos} minutos. `
    + `Puede llover fuerte pronto. ${PAGINA}`;
}
