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
  r = decidir(r.estado, actual(40, min(240)), null, min(240)); // bajó: se rearma
  assert.equal(r.estado.lluvia.activa, false);
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
