// Pantalla, gráfica y botón «Actualizar ahora».

import { tendenciaLineal } from './modelo.js';
import {
  ZONA, aFecha, consultarOpenMeteo, horasEntre, procesarRespuesta, sumarHoras,
} from './openmeteo.js';

const ESPERA_BOTON_S = 60;
const VIGENCIA_MIN = 10; // con la página abierta, datos más viejos que esto se recalculan solos
// Umbrales del aviso sobre la hora más probable de la tabla: avisa solo si alguna hora es
// más probable que no.
const UMBRAL_ATENCION = 50;
const UMBRAL_PRECAUCION = 70;
const CLAVE_ESPERA = 'lluvia-gye-espera-hasta';

const $ = (id) => document.getElementById(id);
const debug = new URLSearchParams(location.search).get('debug') === '1';

const estado = {
  actual: null,      // lectura de ahora, con probabilidad y detalle
  historial: [],     // filas guardadas por el workflow
  relleno: [],       // horas pasadas calculadas en el navegador (no se guardan)
  proyeccion: [],
  generado: null,    // cuándo escribió el workflow actual.json
  obtenido: null,    // cuándo se calcularon los datos en pantalla (ms)
  nino: null,        // índices de El Niño guardados por el workflow
  aeropuerto: null,  // último reporte del aeropuerto resumido por el workflow
  rayos: null,       // rayos de la última hora (data/rayos.json, cada 10 minutos)
};

// ---------- formato ----------

const num = (x, d = 0) =>
  x.toLocaleString('es-EC', { minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: false });
const fmtHora = new Intl.DateTimeFormat('es-EC', { timeZone: ZONA, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
const fmtDia = new Intl.DateTimeFormat('es-EC', { timeZone: ZONA, weekday: 'short', day: 'numeric', month: 'short' });
const horaCorta = (local) => local.slice(11, 16);
const fmtDiaCorto = new Intl.DateTimeFormat('es-EC', { timeZone: ZONA, weekday: 'short', day: 'numeric' });

function frase(pct) {
  if (pct < 20) return 'Sin lluvia esperada';
  if (pct < 40) return 'Poco probable';
  if (pct < 65) return 'Posible lluvia';
  return 'Lluvia probable';
}

// ---------- series ----------

// Rango de la gráfica: las horas de hoy desde la medianoche (al menos las últimas 6) y las 6 próximas.
const PASADO_MIN_H = 6;
const FUTURO_H = 6;

/** {desde, hasta} en horas relativas a ahora (t = 0). */
function rangoGrafica() {
  const horaDelDia = Number(estado.actual.hora.slice(11, 13));
  return { desde: -Math.max(PASADO_MIN_H, horaDelDia), hasta: FUTURO_H };
}

/**
 * Cada fila de Open-Meteo acumula la lluvia de la hora anterior (la de las 14:00 es de 13:00 a 14:00),
 * así que se dibuja donde empieza: t = 0 es la hora en curso. hora = inicio, para mostrarla.
 */
const punto = (f) => ({
  hora: sumarHoras(f.hora, -1),
  t: horasEntre(estado.actual.hora, f.hora) - 1,
  y: f.probabilidad,
});

/** Puntos reales dentro del rango, terminando en la lectura de ahora. t en horas (0 = ahora). */
function serieReal() {
  const { actual } = estado;
  const porHora = new Map();
  for (const f of estado.relleno) porHora.set(f.hora, f);
  for (const f of estado.historial) porHora.set(f.hora, f); // el historial oficial manda
  const { desde } = rangoGrafica();
  const puntos = [...porHora.values()]
    .map(punto)
    .filter((p) => p.t < 0 && p.t >= desde)
    .sort((a, b) => a.t - b.t);
  puntos.push({ hora: actual.hora, t: 0, y: actual.probabilidad });
  return puntos;
}

function serieProyeccion() {
  return estado.proyeccion
    .map(punto)
    .filter((p) => p.t > 0 && p.t <= FUTURO_H);
}

/** Regresión sobre las últimas 6 horas reales (de t = −5 a t = 0). */
function calcularTendencia(real) {
  return tendenciaLineal(real.filter((p) => p.t >= -5));
}

// ---------- pantalla ----------

function dibujar() {
  const { actual } = estado;
  if (!actual) return;
  const pHora = Math.round(actual.probabilidad);
  const real = serieReal();
  const tend = calcularTendencia(real);

  // El número grande es la hora en curso.
  const inicio = actual.horaLluvia ? actual.hora : sumarHoras(actual.hora, -1);
  const fin = actual.horaLluvia ?? actual.hora;
  $('etiqueta').textContent = `Lluvia de ${horaCorta(inicio)} a ${horaCorta(fin)}`;
  $('prob').textContent = `${pHora} %`;
  $('frase').textContent = frase(pHora);
  $('proximas').hidden = true; // el dato de 6 h solo se usa para los avisos
  const aero = actual.aeropuerto;
  $('aeropuerto').hidden = !aero || aero.lluvia_ahora === null;
  if (aero && aero.lluvia_ahora !== null) {
    $('aeropuerto').textContent =
      `Aeropuerto a las ${horaCorta(aero.hora)}: ${aero.lluvia_ahora ? 'lloviendo' : 'sin lluvia'}`;
  }
  $('temp').innerHTML = `${num(actual.temperatura, 1)}<small> °C</small>`;
  $('hum').innerHTML = `${num(actual.humedad)}<small> %</small>`;
  $('pres').innerHTML = `${num(actual.presion, 1)}<small> hPa</small>`;

  dibujarHoras();

  // Aviso sobre la hora más probable de la tabla
  const mayor = proximasHoras().reduce((a, b) => (b.probabilidad > a.probabilidad ? b : a), { probabilidad: pHora });
  const pMayor = Math.round(mayor.probabilidad);
  const cuando = mayor.hora ? ` entre ${rangoHora(mayor.hora)} (${pMayor} %)` : ` (${pMayor} %)`;
  const aviso = $('aviso');
  aviso.hidden = pMayor < UMBRAL_ATENCION;
  if (pMayor >= UMBRAL_PRECAUCION) {
    aviso.innerHTML = `<strong>Precaución:</strong> lluvia probable${cuando}. Lleva paraguas y evita las calles que suelen inundarse.`;
  } else if (pMayor >= UMBRAL_ATENCION) {
    aviso.innerHTML = `<strong>Atención:</strong> posible lluvia${cuando}. Ten el paraguas a mano.`;
  }

  // Cuándo se calcularon los datos en pantalla y de qué hora es el dato del clima
  const calculado = estado.obtenido ? new Date(estado.obtenido) : aFecha(actual.momento ?? actual.hora);
  const clima = aFecha(actual.momento ?? actual.hora);
  const esHoy = fmtDia.format(calculado) === fmtDia.format(new Date());
  $('hora-lectura').textContent =
    `Actualizado a las ${fmtHora.format(calculado)} · ${esHoy ? 'hoy' : fmtDia.format(calculado)}`
    + ` (clima de las ${fmtHora.format(clima)})`;

  dibujarGrafica(real, serieProyeccion(), tend);
  if (debug) dibujarDebug();
}

/**
 * Tabla de las próximas 6 horas con la probabilidad de cada hora. Las horas vienen como en
 * Open-Meteo (la de las 22:00 es de 21:00 a 22:00).
 */
/** La hora en curso y las siguientes, hasta FUTURO_H filas ({hora, probabilidad}). */
function proximasHoras() {
  const { actual } = estado;
  return actual.horaLluvia
    ? [{ hora: actual.horaLluvia, probabilidad: actual.probabilidad }, ...estado.proyeccion].slice(0, FUTURO_H)
    : [];
}

/** «las 22 y las 23 h» para la fila de Open-Meteo de las 23:00 (lluvia de 22:00 a 23:00). */
function rangoHora(hora) {
  const las = (local) => { const h = Number(local.slice(11, 13)); return h === 1 ? 'la 1' : `las ${h}`; };
  return `${las(sumarHoras(hora, -1))} y ${las(hora)} h`;
}

function dibujarHoras() {
  const filas = proximasHoras();
  $('horas').hidden = !filas.length;
  if (!filas.length) return;
  $('horas-filas').innerHTML = filas.map(({ hora, probabilidad: p }) => {
    const barra = (v, clase) => (v === undefined ? '—'
      : `<span class="celda"><span class="barra ${clase}"><span style="width:${Math.round(v)}%"></span></span><b>${Math.round(v)} %</b></span>`);
    const h = (local) => Number(local.slice(11, 13));
    return `<tr><th scope="row">${h(sumarHoras(hora, -1))}–${h(hora)} h</th>`
      + `<td>${barra(p, 'hora')}</td></tr>`;
  }).join('');
}

// ---------- gráfica (SVG a mano) ----------

const ALTO = 222;
const M = { izq: 30, der: 8, arr: 18, aba: 36 };

function dibujarGrafica(real, proy, tend) {
  const cont = $('grafica');
  const ancho = Math.max(280, cont.clientWidth || 320);
  const { desde, hasta } = rangoGrafica();
  const x = (t) => M.izq + ((t - desde) / (hasta - desde)) * (ancho - M.izq - M.der);
  const horaEn = (t) => sumarHoras(estado.actual.hora, t);
  const y = (v) => M.arr + (1 - v / 100) * (ALTO - M.arr - M.aba);
  const ruta = (pts) => pts.map((p, i) => `${i ? 'L' : 'M'}${x(p.t).toFixed(1)},${y(p.y).toFixed(1)}`).join('');

  const partes = [];

  // Rejilla horizontal y referencia en 60 %
  for (const v of [0, 20, 40, 80, 100]) {
    partes.push(`<line class="${v === 0 ? 'base' : 'rejilla'}" x1="${M.izq}" x2="${ancho - M.der}" y1="${y(v)}" y2="${y(v)}"/>`);
    partes.push(`<text x="${M.izq - 6}" y="${y(v) + 4}" text-anchor="end">${v}</text>`);
  }
  partes.push(`<line class="ref" x1="${M.izq}" x2="${ancho - M.der}" y1="${y(60)}" y2="${y(60)}"/>`);
  partes.push(`<text class="ref-texto" x="${M.izq - 6}" y="${y(60) + 4}" text-anchor="end">60</text>`);
  partes.push(`<text x="${M.izq - 6}" y="${M.arr - 8}" text-anchor="end">%</text>`);

  // Eje X: la hora del reloj (cada hora si cabe, si no cada 2); «Ahora» va arriba para no tapar ninguna
  const paso = hasta - desde <= 14 ? 1 : 2;
  for (let t = desde; t <= hasta; t++) {
    const h = Number(horaEn(t).slice(11, 13));
    if (h % paso !== 0) continue;
    partes.push(`<line class="base" x1="${x(t)}" x2="${x(t)}" y1="${ALTO - M.aba}" y2="${ALTO - M.aba + 4}"/>`);
    partes.push(`<text x="${x(t)}" y="${ALTO - M.aba + 16}" text-anchor="middle">${h}</text>`);
  }
  partes.push(`<text x="${ancho - M.der}" y="${ALTO - 2}" text-anchor="end">hora del día</text>`);

  // Cambio de día: línea en la medianoche y el nombre de cada día a su lado
  for (let t = desde + 1; t < hasta; t++) {
    if (horaEn(t).slice(11, 13) !== '00') continue;
    const xm = x(t);
    const dia = (k) => fmtDiaCorto.format(aFecha(horaEn(k)));
    partes.push(`<line class="dia" x1="${xm}" x2="${xm}" y1="${M.arr}" y2="${ALTO - M.aba}"/>`);
    partes.push(`<text class="dia-texto" x="${xm - 5}" y="${M.arr + 12}" text-anchor="end">${dia(t - 1)}</text>`);
    partes.push(`<text class="dia-texto" x="${xm + 5}" y="${M.arr + 12}" text-anchor="start">${dia(t)}</text>`);
  }
  partes.push(`<line class="linea-ahora" x1="${x(0)}" x2="${x(0)}" y1="${M.arr}" y2="${ALTO - M.aba}"/>`);
  partes.push(`<text x="${x(0)}" y="${M.arr - 6}" text-anchor="middle" style="fill:var(--texto-2);font-weight:600">Ahora</text>`);

  partes.push(`<clipPath id="area"><rect x="${M.izq}" y="${M.arr}" width="${ancho - M.izq - M.der}" height="${ALTO - M.arr - M.aba}"/></clipPath>`);

  // Pasado: línea continua, cortada donde falten horas
  let tramo = [];
  const tramos = [];
  for (const p of real) {
    if (tramo.length && p.t - tramo[tramo.length - 1].t > 1.5) { tramos.push(tramo); tramo = []; }
    tramo.push(p);
  }
  tramos.push(tramo);
  for (const tr of tramos) if (tr.length > 1) partes.push(`<path class="pasado" d="${ruta(tr)}"/>`);

  // Proyección: punteada desde ahora
  const ahora = real[real.length - 1];
  if (proy.length) partes.push(`<path class="proyeccion" d="${ruta([ahora, ...proy])}"/>`);

  // Tendencia: últimas 6 h reales prolongadas 3 h
  if (tend) {
    const t0 = Math.min(...real.filter((p) => p.t >= -5).map((p) => p.t));
    const ext = [t0, 3].map((t) => ({ t, y: tend.m * t + tend.b }));
    partes.push(`<path class="tendencia" clip-path="url(#area)" d="${ruta(ext)}"/>`);
  }

  partes.push(`<circle class="ahora" cx="${x(0)}" cy="${y(ahora.y)}" r="5"/>`);
  partes.push(`<g id="hover" visibility="hidden"><line class="cruz" y1="${M.arr}" y2="${ALTO - M.aba}"/><circle class="marca" r="4"/></g>`);

  const resumen = `Probabilidad de lluvia por hora: ahora ${Math.round(ahora.y)} %` +
    (proy.length ? `, en ${FUTURO_H} horas ${Math.round(proy[proy.length - 1].y)} %` : '');
  cont.innerHTML =
    `<svg viewBox="0 0 ${ancho} ${ALTO}" width="${ancho}" height="${ALTO}" role="img" aria-label="${resumen}">${partes.join('')}</svg>` +
    '<div class="globo" hidden></div>';

  activarHover(cont, [...real, ...proy.map((p) => ({ ...p, proyectado: true }))], x, y, ancho);
}

function activarHover(cont, puntos, x, y, ancho) {
  const svg = cont.querySelector('svg');
  const grupo = svg.querySelector('#hover');
  const cruz = grupo.querySelector('line');
  const marca = grupo.querySelector('circle');
  const globo = cont.querySelector('.globo');

  const mostrar = (ev) => {
    const r = svg.getBoundingClientRect();
    const px = ((ev.clientX - r.left) / r.width) * ancho;
    let cercano = puntos[0];
    for (const p of puntos) if (Math.abs(x(p.t) - px) < Math.abs(x(cercano.t) - px)) cercano = p;
    const cx = x(cercano.t);
    cruz.setAttribute('x1', cx);
    cruz.setAttribute('x2', cx);
    marca.setAttribute('cx', cx);
    marca.setAttribute('cy', y(cercano.y));
    grupo.setAttribute('visibility', 'visible');
    const etiqueta = cercano.t === 0 ? 'ahora' : cercano.proyectado ? 'pronóstico' : '';
    globo.innerHTML = `${horaCorta(cercano.hora)}${etiqueta ? ` · ${etiqueta}` : ''}<br><b>${Math.round(cercano.y)} %</b>`;
    globo.hidden = false;
    const izq = (cx / ancho) * r.width;
    const anchoGlobo = globo.offsetWidth;
    globo.style.left = `${Math.min(Math.max(0, izq - anchoGlobo / 2), r.width - anchoGlobo)}px`;
    globo.style.top = `${Math.max(0, (y(cercano.y) / ALTO) * r.height - globo.offsetHeight - 12)}px`;
  };
  const ocultar = () => { grupo.setAttribute('visibility', 'hidden'); globo.hidden = true; };

  svg.addEventListener('pointermove', mostrar);
  svg.addEventListener('pointerdown', mostrar);
  svg.addEventListener('pointerleave', ocultar);
}

// ---------- modo depuración (?debug=1) ----------

function dibujarDebug() {
  const { actual } = estado;
  const d = actual.detalle;
  const caja = $('debug');
  caja.hidden = false;
  if (!d) { caja.textContent = 'Sin detalle del modelo para esta lectura.'; return; }
  const f = (v, dec = 3) => (v === null || v === undefined ? '—' : num(v, dec));
  const m = actual.modelos;
  const fuentes = { corregido: 'modelo corregido', ensamble: 'ensambles ECMWF + GFS', heuristica: 'heurística', ninguna: '—' };
  const filas = [
    ['Fuente: esta hora / 6 h', `${fuentes[actual.fuente]} / ${fuentes[actual.proximas6hFuente] ?? '—'}`],
    ['Usa el reporte del aeropuerto', actual.usaAeropuerto ? 'sí' : 'no'],
    ['Usa los rayos del satélite (esta hora / 6 h)', `${actual.horaUsaRayos ? 'sí' : 'no'} / ${actual.usaRayos ? 'sí' : 'no'}`],
    ['Rayos: más cercano en 20 min / acercándose', actual.rayos
      ? `${actual.rayos.cercania_20m > 0 ? `${f(-30 * Math.log(actual.rayos.cercania_20m), 0)} km` : 'ninguno'} / ${f(actual.rayos.acercamiento, 2)}`
      : '—'],
    ['Corregido: esta hora / 6 h (%)', `${f(actual.corregido, 1)} / ${actual.proximas6hFuente === 'corregido' ? f(actual.proximas6h, 1) : '—'}`],
    ['Ensambles sin corregir: esta hora / 6 h (%)', `${f(actual.ensamble, 1)} / ${f(actual.ensamble6h, 1)}`],
    ['ECMWF ahora / 6 h (%)', m ? `${f(m.ahora.ecmwf, 0)} / ${f(m.proximas6h.ecmwf, 0)}` : '—'],
    ['GFS ahora / 6 h (%)', m ? `${f(m.ahora.gfs, 0)} / ${f(m.proximas6h.gfs, 0)}` : '—'],
    ['El Niño 1+2 (anomalía °C)', f(estado.nino?.at(-1)?.nino12, 1)],
    ['Heurística (%)', f(actual.heuristica, 1)],
    ['Probabilidad base del mes', f(d.base, 2)],
    ['Temporada lluviosa', d.lluviosa ? 'sí' : 'no'],
    ['Presión hace 3 h (hPa)', f(estado.actual.presion3h, 1)],
    ['Punto de rocío Td (°C)', f(d.td, 2)],
    ['Margen T − Td (°C)', f(d.sp, 2)],
    ['Cambio esperado por marea (hPa)', f(d.cambioEsperado)],
    ['Anomalía de presión (hPa)', f(d.anomalia)],
    ...Object.entries(d.factores).map(([k, v]) => [`Factor ${k}`, f(v)]),
    ['z (logit)', f(d.z)],
  ];
  caja.innerHTML = '<h2>Desglose de los modelos</h2><table>' +
    filas.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join('') + '</table>';
}

// ---------- botón ----------

function leerEspera() {
  try { return Number(localStorage.getItem(CLAVE_ESPERA)) || 0; } catch { return 0; }
}

function iniciarEspera(hasta) {
  try { localStorage.setItem(CLAVE_ESPERA, String(hasta)); } catch { /* sin almacenamiento */ }
  const boton = $('actualizar');
  const tic = () => {
    const resta = Math.ceil((hasta - Date.now()) / 1000);
    if (resta <= 0) {
      boton.disabled = false;
      boton.textContent = 'Actualizar ahora';
      return;
    }
    boton.disabled = true;
    boton.textContent = `Actualizar ahora (${resta} s)`;
    setTimeout(tic, 1000);
  };
  tic();
}

let consultando = false;

async function actualizarAhora({ automatico = false } = {}) {
  if (consultando) return;
  consultando = true;
  const boton = $('actualizar');
  const msg = $('estado');
  boton.disabled = true;
  msg.classList.remove('error');
  msg.textContent = 'Actualizando con el clima de este momento…';
  try {
    // El reporte del aeropuerto y los rayos solo los puede leer el workflow; se reutilizan si son
    // de esta hora. Los rayos se actualizan cada 10 minutos, así que se vuelven a pedir.
    const [respuesta, rayos] = await Promise.all([
      consultarOpenMeteo(),
      leerJSON('data/rayos.json').then((r) => r.modelo ?? null, () => estado.rayos),
    ]);
    estado.rayos = rayos;
    const datos = procesarRespuesta(respuesta, {
      nino: estado.nino,
      aeropuerto: estado.aeropuerto,
      rayos: estado.rayos,
    });
    estado.actual = datos.actual;
    estado.proyeccion = datos.proyeccion;
    estado.relleno = datos.pasado;
    estado.generado = null;
    estado.obtenido = Date.now();
    dibujar();
    msg.textContent = ''; // la hora de actualización ya se ve arriba del botón
  } catch (e) {
    console.error(e);
    msg.classList.add('error');
    msg.textContent = estado.actual
      ? 'No se pudo conectar con el servicio del clima. Se muestran los últimos datos.'
      : 'No se pudo conectar con el servicio del clima. Revisa tu conexión e inténtalo de nuevo.';
  } finally {
    consultando = false;
    if (!automatico) iniciarEspera(Date.now() + ESPERA_BOTON_S * 1000);
    else if (leerEspera() <= Date.now()) boton.disabled = false;
  }
}

/**
 * Recalcula con el clima de ahora: siempre al abrir la página; después, al volver a la pestaña
 * o cada minuto que pase con ella a la vista, si los datos tienen más de VIGENCIA_MIN minutos.
 */
function refrescarSiHaceFalta({ alAbrir = false } = {}) {
  if (alAbrir) return actualizarAhora({ automatico: true });
  if (document.visibilityState !== 'visible') return;
  if (!estado.obtenido || Date.now() - estado.obtenido > VIGENCIA_MIN * 60000) {
    actualizarAhora({ automatico: true });
  }
}

// ---------- inicio ----------

async function leerJSON(ruta) {
  const r = await fetch(ruta, { cache: 'no-cache' });
  if (!r.ok) throw new Error(`${ruta}: ${r.status}`);
  return r.json();
}

async function iniciar() {
  $('actualizar').addEventListener('click', () => actualizarAhora());
  const espera = leerEspera();
  if (espera > Date.now()) iniciarEspera(espera);

  const [actual, historial, nino] = await Promise.allSettled([
    leerJSON('data/actual.json'),
    leerJSON('data/historial.json'),
    leerJSON('data/nino.json'),
  ]);
  if (historial.status === 'fulfilled' && Array.isArray(historial.value)) estado.historial = historial.value;
  if (nino.status === 'fulfilled' && Array.isArray(nino.value)) estado.nino = nino.value;

  if (actual.status === 'fulfilled') {
    const { proyeccion = [], generado = null, ...lectura } = actual.value;
    estado.actual = lectura;
    estado.proyeccion = proyeccion;
    estado.generado = generado;
    estado.aeropuerto = lectura.aeropuerto ?? null;
    estado.obtenido = generado ? Date.parse(generado) : null;
    dibujar(); // se muestra de inmediato lo guardado…
  }
  // …y enseguida se recalcula con el clima de este momento.
  refrescarSiHaceFalta({ alAbrir: true });
  // El celular puede «reabrir» la página desde su memoria sin cargarla de nuevo.
  window.addEventListener('pageshow', (e) => { if (e.persisted) refrescarSiHaceFalta({ alAbrir: true }); });
  document.addEventListener('visibilitychange', () => refrescarSiHaceFalta());
  setInterval(() => refrescarSiHaceFalta(), 60000);

  let ancho = $('grafica').clientWidth;
  new ResizeObserver(() => {
    const nuevo = $('grafica').clientWidth;
    if (nuevo !== ancho && estado.actual) { ancho = nuevo; dibujar(); }
  }).observe($('grafica'));
}

iniciar();
