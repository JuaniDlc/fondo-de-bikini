// Envío por WhatsApp con CallMeBot (https://www.callmebot.com/blog/free-api-whatsapp-messages/).
//
// Los destinatarios vienen del secreto CALLMEBOT_DESTINOS de GitHub, nunca del código:
//   +593991234567:1234567;+593987654321:7654321
// (número con código de país, dos puntos, la clave que CallMeBot le dio a ese número;
// varios separados por punto y coma).

export function leerDestinos(texto = '') {
  return texto
    .split(/[;\n]/)
    .map((s) => s.trim())
    .filter(Boolean)
    .map((s) => {
      const [telefono, clave] = s.split(':').map((x) => x.trim());
      if (!/^\+\d{8,15}$/.test(telefono ?? '') || !clave) {
        throw new Error('CALLMEBOT_DESTINOS mal escrito: usa +593XXXXXXXXX:clave;+593YYYYYYYYY:clave');
      }
      return { telefono, clave };
    });
}

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

/** Envía el texto a todos los destinatarios. Devuelve cuántos lo recibieron. Nunca imprime números ni claves. */
export async function enviarWhatsApp(texto, destinos = leerDestinos(process.env.CALLMEBOT_DESTINOS)) {
  if (!destinos.length) {
    console.log('WhatsApp: no hay destinatarios configurados (secreto CALLMEBOT_DESTINOS).');
    return 0;
  }
  let enviados = 0;
  for (const [i, d] of destinos.entries()) {
    if (i > 0) await esperar(3000); // CallMeBot pide no mandar ráfagas
    const url = 'https://api.callmebot.com/whatsapp.php?'
      + new URLSearchParams({ phone: d.telefono, text: texto, apikey: d.clave });
    try {
      const r = await fetch(url);
      const cuerpo = await r.text();
      if (r.ok && !/error|invalid/i.test(cuerpo)) enviados++;
      else console.warn(`WhatsApp: el destinatario ${i + 1} no se pudo enviar (HTTP ${r.status}).`);
    } catch (e) {
      console.warn(`WhatsApp: el destinatario ${i + 1} falló: ${e.message}`);
    }
  }
  console.log(`WhatsApp: enviado a ${enviados} de ${destinos.length}.`);
  return enviados;
}
