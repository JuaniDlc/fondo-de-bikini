// Modelo heurístico de probabilidad de lluvia para Guayaquil.
// Lo usan el workflow (Node) y el navegador, para que ambos den el mismo resultado.

/** Probabilidad base de lluvia por mes, de enero a diciembre. */
export const BASE_MES = [0.45, 0.60, 0.60, 0.45, 0.15, 0.06, 0.04, 0.03, 0.04, 0.05, 0.06, 0.18];

/** Umbral de base mensual a partir del cual se considera temporada lluviosa. */
export const UMBRAL_TEMPORADA = 0.30;

const P_REFERENCIA = 0.25;

const limitar = (x, min, max) => Math.min(max, Math.max(min, x));
const logit = (p) => Math.log(p / (1 - p));
const sigmoide = (z) => 1 / (1 + Math.exp(-z));

/** Punto de rocío (°C) con la fórmula de Magnus (a = 17.62, b = 243.12 °C). */
export function puntoRocio(T, HR) {
  const a = 17.62;
  const b = 243.12;
  const g = Math.log(HR / 100) + (a * T) / (b + T);
  return (b * g) / (a - g);
}

/** Marea barométrica semidiurna (hPa) a la hora local h. */
export function marea(h) {
  return 1.2 * Math.cos((2 * Math.PI * (h - 10)) / 12);
}

/**
 * Calcula la probabilidad de lluvia.
 * @param {object} e
 * @param {number} e.P     presión actual (hPa)
 * @param {number|null} e.P3  presión de hace 3 h (hPa); null si falta
 * @param {number} e.T     temperatura (°C)
 * @param {number} e.HR    humedad relativa (%)
 * @param {number} e.mes   mes, 1 a 12
 * @param {number} e.hora  hora local, 0 a 23
 */
export function calcular({ P, P3, T, HR, mes, hora }) {
  const base = BASE_MES[mes - 1];
  const lluviosa = base >= UMBRAL_TEMPORADA;

  const td = puntoRocio(T, HR);
  const sp = T - td;
  const cambioEsperado = marea(hora) - marea(hora - 3);
  const tieneP3 = typeof P3 === 'number' && Number.isFinite(P3);
  const anomalia = tieneP3 ? (P - P3) - cambioEsperado : null;

  let conveccion = 0;
  if (lluviosa && hora >= 13 && hora <= 20) {
    conveccion += 0.6;
    if (T >= 31) conveccion += 0.4;
  }

  const factores = {
    temporada: logit(base) - logit(P_REFERENCIA),
    margen: limitar(-0.55 * (sp - 4), -2.2, 2.0),
    humedad: limitar(0.06 * (HR - 80), -1.8, 1.0),
    tendencia: tieneP3 ? limitar(-0.9 * anomalia, -1.5, 2.0) : 0,
    presion: limitar(-0.25 * (P - 1011), -0.8, 1.0),
    conveccion: limitar(conveccion, 0, 1.0),
  };

  const z = logit(P_REFERENCIA) + Object.values(factores).reduce((s, f) => s + f, 0);

  return {
    probabilidad: sigmoide(z),
    detalle: { base, lluviosa, td, sp, cambioEsperado, anomalia, z, factores },
  };
}

/**
 * Tendencia lineal por mínimos cuadrados.
 * @param {{t:number, y:number}[]} puntos  t en horas (0 = ahora), y en %
 * @param {number} minimo  puntos necesarios para calcularla
 * @returns {{m:number, b:number, n:number} | null}  y = m·t + b; null si faltan puntos
 */
export function tendenciaLineal(puntos, minimo = 4) {
  const n = puntos.length;
  if (n < minimo) return null;
  const mt = puntos.reduce((s, p) => s + p.t, 0) / n;
  const my = puntos.reduce((s, p) => s + p.y, 0) / n;
  let sxy = 0;
  let sxx = 0;
  for (const p of puntos) {
    sxy += (p.t - mt) * (p.y - my);
    sxx += (p.t - mt) ** 2;
  }
  if (sxx === 0) return null;
  const m = sxy / sxx;
  return { m, b: my - m * mt, n };
}
