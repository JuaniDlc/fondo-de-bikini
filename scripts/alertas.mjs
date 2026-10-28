// Decide cuándo mandar un aviso (Telegram, WhatsApp), sin repetir el mismo aviso una y otra vez.
//
// Dos avisos independientes, cada uno con su mensaje de cierre:
// - lluvia: alguna de las próximas 6 horas de la tabla de la página (la en curso y las 5
//   siguientes) llega a 70 % en el modelo corregido. Cuando todas bajan de 50 %, avisa que bajó
//   el riesgo y se rearma (así no llega un mensaje cada hora).
// - rayos: el satélite ve una tormenta eléctrica a menos de 60 km. Avisa al aparecer y si se
//   acerca a menos de 25 km; como mucho un aviso de rayos por hora. Si avisó, avisa también
//   cuando lleva 30 minutos sin rayos cerca.

export const PAGINA = 'https://juanidlc.github.io/fondo-de-bikini/';
export const LLUVIA_ACTIVA = 70;
export const LLUVIA_DESACTIVA = 50;
const HORAS_LLUVIA = 6;
export const RAYOS_MINIMOS = 3; // menos que esto puede ser ruido del sensor
export const ESPERA_RAYOS_MIN = 60;
export const REPETIR_RAYOS_MIN = 120; // tormenta que sigue activa: se recuerda cada 2 horas
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
  const mayor = horaMasProbable(actual, ahora);
  if (mayor) {
    if (!nuevo.lluvia.activa && mayor.probabilidad >= LLUVIA_ACTIVA) {
      nuevo.lluvia = { activa: true, enviado: new Date(ahora).toISOString() };
      mensajes.push(mensajeLluvia(mayor, actual));
    } else if (nuevo.lluvia.activa && mayor.probabilidad < LLUVIA_DESACTIVA) {
      nuevo.lluvia.activa = false;
      mensajes.push(mensajeLluviaFin(mayor));
    }
  }

  // Rayos (solo con una lectura reciente del satélite)
  if (rayos?.generado && minutosDesde(rayos.generado, ahora) <= VIGENCIA_RAYOS_MIN) {
    const r = nuevo.rayos;
    r.avisada ??= r.nivel > 0; // estados guardados antes de que existiera el aviso de cierre
    const nivel = nivelRayos(rayos);
    if (nivel > 0) r.ultimoRayo = rayos.generado;
    const desdeAviso = r.enviado ? minutosDesde(r.enviado, ahora) : Infinity;
    const sube = nivel > r.nivel && (desdeAviso >= ESPERA_RAYOS_MIN || nivel === 2);
    // Si la tormenta no se ha ido (o las revisiones se atrasaron y no se vio irse),
    // se vuelve a avisar cuando pasaron 2 horas desde el último aviso.
    const sigue = nivel > 0 && desdeAviso >= REPETIR_RAYOS_MIN;
    if (sube || sigue) {
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

/**
 * La hora más probable de las próximas HORAS_LLUVIA (la en curso y las siguientes), como en la
 * tabla de la página; null si la lectura es vieja o no es del modelo corregido.
 * Las horas son de Open-Meteo: la de las 23:00 es la lluvia de 22:00 a 23:00.
 */
export function horaMasProbable(actual, ahora) {
  if (!actual?.generado || minutosDesde(actual.generado, ahora) > VIGENCIA_ACTUAL_MIN) return null;
  if (!['corregido', 'aeropuerto'].includes(actual.fuente) || !actual.horaLluvia) return null;
  const enHoras = (local) => Date.parse(`${local}:00Z`) / 3600000; // horas locales, para restar
  const horas = [{ hora: actual.horaLluvia, probabilidad: actual.probabilidad }, ...(actual.proyeccion ?? [])]
    .filter((f) => enHoras(f.hora) - enHoras(actual.horaLluvia) < HORAS_LLUVIA)
    .filter((f) => typeof f.probabilidad === 'number');
  return horas.reduce((a, b) => (b.probabilidad > a.probabilidad ? b : a));
}

const hora = (local) => Number(local.slice(11, 13));
const las = (h) => (h === 1 ? 'la 1' : `las ${h}`);
const rango = (local) => `entre ${las((hora(local) + 23) % 24)} y ${las(hora(local))} h`;

export function mensajeLluvia(mayor, actual) {
  if (actual?.lloviendo && mayor.hora === actual.horaLluvia) {
    return `🌧️ Lluvia en Fondo de Bikini: está lloviendo en el aeropuerto de Guayaquil desde las `
      + `${actual.lloviendo.desde}. Lleva paraguas. ${PAGINA}`;
  }
  const aero = actual?.aeropuerto?.lluvia_ahora === 1 ? ' Ya está lloviendo en el aeropuerto.' : '';
  return `🌧️ Lluvia en Fondo de Bikini: ${Math.round(mayor.probabilidad)} % de probabilidad de lluvia `
    + `en Guayaquil ${rango(mayor.hora)}.${aero} Lleva paraguas. ${PAGINA}`;
}

export function mensajeLluviaFin(mayor) {
  return `✅ Bajó el riesgo de lluvia en Guayaquil: ninguna de las próximas ${HORAS_LLUVIA} horas `
    + `pasa de ${Math.round(mayor.probabilidad)} %. ${PAGINA}`;
}

export function mensajeRayosFin() {
  return `✅ La tormenta eléctrica se alejó de Guayaquil: no hay rayos a menos de 60 km desde hace `
    + `${SIN_RAYOS_MIN} minutos. ${PAGINA}`;
}

export function mensajeRayos(r) {
  const donde = r.mas_cercano_km <= 5
    ? `sobre Guayaquil (a ${Math.round(r.mas_cercano_km)} km)`
    : r.mas_cercano_km <= 25
    ? `muy cerca de Guayaquil (a ${Math.round(r.mas_cercano_km)} km)`
    : `a ${Math.round(r.mas_cercano_km)} km${r.rumbo ? ` al ${r.rumbo}` : ''} de Guayaquil`;
  return `⚡ Tormenta eléctrica ${donde}: ${r.rayos} rayos en los últimos ${r.minutos} minutos. `
    + `Puede llover fuerte pronto. ${PAGINA}`;
}
