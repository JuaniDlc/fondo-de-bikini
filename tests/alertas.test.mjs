import { test } from 'node:test';
import assert from 'node:assert/strict';
import { decidir, estadoInicial } from '../scripts/alertas.mjs';
import { leerConfigTelegram } from '../scripts/telegram.mjs';
import { leerDestinos } from '../scripts/whatsapp.mjs';

const T0 = Date.parse('2026-10-26T04:00:00Z');
const min = (m) => T0 + m * 60000;
const iso = (t) => new Date(t).toISOString();
const actual = (p6, t = T0) => ({ generado: iso(t), proximas6h: p6, proximas6hFuente: 'corregido' });
const rayos = (n, km, t = T0) => ({ generado: iso(t), minutos: 10, rayos: n, mas_cercano_km: km, rumbo: 'noreste' });

test('lluvia: avisa al llegar a 80 %, no repite, y rearma bajo 60 %', () => {
  let r = decidir(estadoInicial(), actual(53), null, T0);
  assert.equal(r.mensajes.length, 0);
  r = decidir(r.estado, actual(85, min(60)), null, min(60));
  assert.equal(r.mensajes.length, 1);
  assert.match(r.mensajes[0], /85 %/);
  r = decidir(r.estado, actual(90, min(120)), null, min(120)); // sigue alto: no repite
  assert.equal(r.mensajes.length, 0);
  r = decidir(r.estado, actual(70, min(180)), null, min(180)); // entre 60 y 80: sigue activa
  assert.equal(r.estado.lluvia.activa, true);
  r = decidir(r.estado, actual(40, min(240)), null, min(240)); // bajó: avisa y se rearma
  assert.equal(r.estado.lluvia.activa, false);
  assert.equal(r.mensajes.length, 1);
  assert.match(r.mensajes[0], /Bajó el riesgo de lluvia.*40 %/);
  r = decidir(r.estado, actual(30, min(270)), null, min(270)); // sigue bajo: no repite el cierre
  assert.equal(r.mensajes.length, 0);
  r = decidir(r.estado, actual(82, min(300)), null, min(300));
  assert.equal(r.mensajes.length, 1);
});

test('lluvia: ignora lecturas viejas o que no son del modelo corregido', () => {
  assert.equal(decidir(estadoInicial(), actual(95, min(-180)), null, T0).mensajes.length, 0);
  const ens = { ...actual(95), proximas6hFuente: 'ensamble' };
  assert.equal(decidir(estadoInicial(), ens, null, T0).mensajes.length, 0);
});

test('rayos: avisa al aparecer y al acercarse, como mucho uno por hora', () => {
  let r = decidir(estadoInicial(), null, rayos(2, 40), T0); // muy pocos: puede ser ruido
  assert.equal(r.mensajes.length, 0);
  r = decidir(r.estado, null, rayos(225, 40, min(10)), min(10));
  assert.equal(r.mensajes.length, 1);
  assert.match(r.mensajes[0], /a 40 km al noreste/);
  r = decidir(r.estado, null, rayos(300, 35, min(20)), min(20)); // misma tormenta: no repite
  assert.equal(r.mensajes.length, 0);
  r = decidir(r.estado, null, rayos(300, 12, min(30)), min(30)); // se acerca: avisa aunque no pasó la hora
  assert.equal(r.mensajes.length, 1);
  assert.match(r.mensajes[0], /muy cerca de Guayaquil \(a 12 km\)/);
  r = decidir(r.estado, null, rayos(0, null, min(40)), min(40)); // se fue
  assert.equal(r.estado.rayos.nivel, 0);
  r = decidir(r.estado, null, rayos(50, 50, min(50)), min(50)); // vuelve antes de una hora: espera
  assert.equal(r.mensajes.length, 0);
  r = decidir(r.estado, null, rayos(50, 50, min(95)), min(95));
  assert.equal(r.mensajes.length, 1);
});

test('lluvia: sin aviso previo, bajar de 60 % no manda nada', () => {
  assert.equal(decidir(estadoInicial(), actual(20), null, T0).mensajes.length, 0);
});

test('rayos: avisa que la tormenta se alejó tras 30 minutos sin rayos', () => {
  let r = decidir(estadoInicial(), null, rayos(100, 40), T0);
  assert.equal(r.mensajes.length, 1);
  r = decidir(r.estado, null, rayos(80, 45, min(10)), min(10));
  r = decidir(r.estado, null, rayos(0, null, min(20)), min(20)); // 10 min sin rayos: espera
  assert.equal(r.mensajes.length, 0);
  r = decidir(r.estado, null, rayos(0, null, min(30)), min(30));
  assert.equal(r.mensajes.length, 0);
  r = decidir(r.estado, null, rayos(0, null, min(40)), min(40)); // 30 min desde el último rayo
  assert.equal(r.mensajes.length, 1);
  assert.match(r.mensajes[0], /se alejó/);
  r = decidir(r.estado, null, rayos(0, null, min(50)), min(50)); // no repite el cierre
  assert.equal(r.mensajes.length, 0);
});

test('rayos: si vuelve antes de 30 minutos, no avisa que se alejó', () => {
  let r = decidir(estadoInicial(), null, rayos(100, 40), T0);
  r = decidir(r.estado, null, rayos(0, null, min(10)), min(10));
  r = decidir(r.estado, null, rayos(0, null, min(20)), min(20));
  r = decidir(r.estado, null, rayos(30, 50, min(30)), min(30)); // volvió (sin repetir aviso: < 1 h)
  assert.equal(r.mensajes.length, 0);
  r = decidir(r.estado, null, rayos(0, null, min(50)), min(50)); // 20 min desde el último rayo
  assert.equal(r.mensajes.length, 0);
  r = decidir(r.estado, null, rayos(0, null, min(60)), min(60));
  assert.match(r.mensajes[0], /se alejó/);
});

test('rayos: sin aviso previo no manda «se alejó»', () => {
  let r = decidir(estadoInicial(), null, rayos(2, 40), T0); // muy pocos: no avisó
  r = decidir(r.estado, null, rayos(0, null, min(60)), min(60));
  assert.equal(r.mensajes.length, 0);
});

test('rayos: estado guardado antes de existir el cierre (sin «avisada»)', () => {
  const viejo = { lluvia: { activa: false, enviado: null }, rayos: { nivel: 2, enviado: iso(T0) } };
  const r = decidir(viejo, null, rayos(0, null, min(40)), min(40));
  assert.match(r.mensajes[0], /se alejó/);
});

test('rayos: si la tormenta sigue, recuerda cada 2 horas', () => {
  let r = decidir(estadoInicial(), null, rayos(100, 15), T0);
  assert.equal(r.mensajes.length, 1);
  r = decidir(r.estado, null, rayos(100, 10, min(90)), min(90)); // sigue, pero < 2 h
  assert.equal(r.mensajes.length, 0);
  r = decidir(r.estado, null, rayos(79, 2.6, min(210)), min(210)); // sigue después de 3,5 h
  assert.equal(r.mensajes.length, 1);
  assert.match(r.mensajes[0], /sobre Guayaquil \(a 3 km\)/);
});

test('rayos: ignora datos del satélite de hace más de 20 minutos', () => {
  assert.equal(decidir(estadoInicial(), null, rayos(225, 10, min(-30)), T0).mensajes.length, 0);
});

test('configuración de Telegram', () => {
  assert.deepEqual(leerConfigTelegram({ TELEGRAM_TOKEN: ' 123:abc ', TELEGRAM_CHAT: '@fondodebikini' }),
    { token: '123:abc', chat: '@fondodebikini' });
  assert.equal(leerConfigTelegram({ TELEGRAM_TOKEN: '123:abc' }), null);
  assert.equal(leerConfigTelegram({}), null);
});

test('destinatarios de WhatsApp', () => {
  assert.deepEqual(leerDestinos('+593991234567:123456; +593987654321:654321'), [
    { telefono: '+593991234567', clave: '123456' },
    { telefono: '+593987654321', clave: '654321' },
  ]);
  assert.deepEqual(leerDestinos(''), []);
  assert.deepEqual(leerDestinos(undefined), []);
  assert.throws(() => leerDestinos('0991234567:123'), /mal escrito/);
});
