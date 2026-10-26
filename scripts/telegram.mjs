// Envío a un canal (o chat) de Telegram con un bot propio (https://core.telegram.org/bots/api).
//
// Configuración en los secretos de GitHub, nunca en el código:
//   TELEGRAM_TOKEN  el token que da @BotFather al crear el bot
//   TELEGRAM_CHAT   el canal, por ejemplo @fondodebikini (el bot debe ser administrador)

export function leerConfigTelegram(env = process.env) {
  const token = env.TELEGRAM_TOKEN?.trim();
  const chat = env.TELEGRAM_CHAT?.trim();
  if (!token || !chat) return null;
  return { token, chat };
}

/** Publica el texto. Devuelve 1 si llegó y 0 si no; nunca imprime el token. */
export async function enviarTelegram(texto, config = leerConfigTelegram()) {
  if (!config) {
    console.log('Telegram: no configurado (secretos TELEGRAM_TOKEN y TELEGRAM_CHAT).');
    return 0;
  }
  try {
    const r = await fetch(`https://api.telegram.org/bot${config.token}/sendMessage`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chat_id: config.chat, text: texto }),
    });
    const respuesta = await r.json().catch(() => ({}));
    if (r.ok && respuesta.ok) {
      console.log('Telegram: enviado.');
      return 1;
    }
    console.warn(`Telegram: no se pudo enviar (HTTP ${r.status}: ${respuesta.description ?? 'sin detalle'}).`);
  } catch (e) {
    console.warn(`Telegram: falló la conexión: ${e.message}`);
  }
  return 0;
}
