# Lluvia en Fondo de Bikini

**https://juanidlc.github.io/fondo-de-bikini/**

Página pública que estima la probabilidad de lluvia en Guayaquil cada hora, muestra hacia dónde va la tendencia y deja que cualquier visitante la actualice al momento, sin cuenta ni permisos.

- **GitHub Actions** consulta cada hora Open-Meteo, el reporte del aeropuerto (METAR de SEGU) y el índice de El Niño, calcula la probabilidad y guarda los JSON de `data/` en el repositorio.
- **GitHub Pages** publica `index.html`, que lee esos JSON y dibuja la pantalla.
- **«Actualizar ahora»** consulta Open-Meteo desde el navegador y recalcula con el mismo modelo, reutilizando el reporte del aeropuerto que guardó el workflow si es de la misma hora. No escribe en el repositorio ni usa tokens.

## Estructura

```
index.html
assets/mos.js               modelo corregido (compartido por Node y el navegador)
assets/mos-coeficientes.js  coeficientes del modelo corregido (generado por analisis/entrenar.py)
assets/openmeteo.js         consulta a Open-Meteo y cálculo por hora (compartido)
assets/modelo.js            heurística original, solo como referencia
assets/app.js               pantalla, gráfica y botón
assets/estilos.css
data/actual.json            última lectura, probabilidades y proyección de 12 h
data/historial.json         una fila por hora, últimos 7 días
data/nino.json              últimas 12 semanas del índice de El Niño
scripts/actualizar.mjs      lo que corre el workflow
scripts/fuentes.mjs         aeropuerto y El Niño (solo desde el workflow)
analisis/                   descarga de datos, evaluación y entrenamiento (Python)
tests/                      pruebas (node:test)
.github/workflows/actualizar.yml
```

## Publicar en GitHub

1. Crea un repositorio **público** en GitHub (por ejemplo `fondo-de-bikini`) y sube este código a la rama `main`.
2. En **Settings → Actions → General → Workflow permissions**, elige **Read and write permissions** y guarda.
3. En **Settings → Pages**, en *Build and deployment* elige **Deploy from a branch**, rama `main`, carpeta `/ (root)`.
4. En la pestaña **Actions**, abre «Actualizar lectura» y pulsa **Run workflow** una vez.
5. Abre `https://<tu-usuario>.github.io/fondo-de-bikini/`.

A partir de ahí el workflow corre solo cada hora (minuto 7, en UTC).

**Límites de GitHub:** las ejecuciones programadas pueden atrasarse varios minutos en horas de mucha carga, y GitHub pausa los workflows programados de un repo público tras unos 60 días sin actividad. Si pasa, entra a **Actions** y pulsa **Enable workflow**. La página avisa «la lectura automática está atrasada» cuando los datos tienen más de 2 horas.

## Avisos por WhatsApp

Dos avisos, publicados en un canal de Telegram y, si está configurado, enviados por WhatsApp con [CallMeBot](https://www.callmebot.com/blog/free-api-whatsapp-messages/):

- **Lluvia** (workflow «Actualizar lectura», cada hora): cuando alguna de las próximas 6 horas de la tabla de la página llega a 70 %, y dice cuál. Cuando todas bajan de 50 %, avisa que bajó el riesgo; solo entonces puede volver a avisar.
- **Rayos** (workflow «Rayos», cada 10 minutos): cuando el satélite GOES-19 ve al menos 3 rayos a menos de 60 km de Guayaquil en los últimos 10 minutos (`scripts/rayos.py`). Avisa otra vez si la tormenta se acerca a menos de 25 km; si no, como mucho uno por hora. Si avisó, avisa también cuando lleva 30 minutos sin rayos cerca.

La lógica está en `scripts/alertas.mjs` y el estado (qué avisos están activos) en `data/alertas.json`.

Los secretos se guardan en **Settings → Secrets and variables → Actions → New repository secret**. Nunca pongas tokens, números ni claves en el código. Para probar: **Actions → Probar avisos → Run workflow**.

**Telegram** (`scripts/telegram.mjs`):

1. En Telegram, crea un canal público (por ejemplo `@fondodebikini`).
2. Habla con @BotFather, envía `/newbot` y guarda el token que te da.
3. Agrega el bot al canal como administrador con permiso para publicar.
4. Secretos: `TELEGRAM_TOKEN` (el token) y `TELEGRAM_CHAT` (el canal, con @).

**WhatsApp** (`scripts/whatsapp.mjs`, opcional):

1. Cada persona activa CallMeBot desde su WhatsApp siguiendo las instrucciones de su página y recibe una clave (apikey).
2. Secreto `CALLMEBOT_DESTINOS` con el formato `+593XXXXXXXXX:clave` (varios separados por `;`).

## Pronóstico por lugar

Además del aeropuerto, la página puede mostrar la tabla «Por lugar» para otros puntos de la ciudad, con los rayos contados desde cada uno (`scripts/rayos.py` y `scripts/lugares.mjs`, en el workflow «Rayos»). Las coordenadas van solo en el secreto `LUGARES`, con el formato `Lugar A:<latitud>,<longitud>;Lugar B:<latitud>,<longitud>`. El repositorio y la página son públicos, así que nunca se escriben coordenadas ni distancias de los lugares: `data/lugares.json` solo lleva nombres y porcentajes, y los registros del workflow solo los nombres.

## En local

Necesitas Node 20 o superior.

```bash
node --test
```

```bash
node scripts/actualizar.mjs
```

Para ver la página, sírvela con cualquier servidor estático desde la raíz del proyecto (abrir `index.html` con doble clic no funciona porque los módulos ES necesitan HTTP), por ejemplo:

```bash
npx serve .
```

Agrega `?debug=1` a la URL para comparar el modelo corregido, los ensambles sin corregir y la heurística.

## Modelo

**Probabilidad principal: modelo corregido (MOS)** en `assets/mos.js`. Es una regresión logística entrenada con la lluvia que de verdad reportó el aeropuerto de Guayaquil (2023 a 2026). Usa como entrada los pronósticos de lluvia de seis modelos del clima (GFS, ECMWF de 25 y de 9 km, ICON, UKMO de 10 km y JMA), la energía para tormentas, la humedad y la nubosidad de GFS, la hora, la época del año, el índice de El Niño y, si es de la hora actual, si está lloviendo en el aeropuerto. Responde dos preguntas: «¿llueve en esta hora?» (la hora en curso) y «¿llueve en algún momento de las próximas 6 horas?». Ambas usan si llovió en el aeropuerto en la última hora y en las últimas 3, y los rayos que vio el satélite GOES en la última hora (cuántos por anillo de distancia, el más cercano y si se acercan); para las horas siguientes hay un modelo por anticipación (1 a 6 h), porque ese efecto se va perdiendo. Los rayos los calcula `scripts/rayos.py` cada 10 minutos en `data/rayos.json` (`modelo`), con todos los archivos del satélite (uno cada 20 s), igual que para entrenar; el historial lo arma el workflow manual «Historial de rayos» (`analisis/rayos_historial.py`). El reporte del aeropuerto se revisa cada 10 minutos (`scripts/aeropuerto.mjs` → `data/aeropuerto.json`, en el workflow «Rayos»): si de una hora a otra todavía no llegó el reporte nuevo, se usa el anterior con el modelo de una hora más de anticipación; si un reporte de la hora en curso (un especial) ya trae lluvia, esa hora se muestra como lluvia observada (100 %) y las siguientes se calculan desde ella. Si los rayos o el aeropuerto son más viejos, se usa el modelo sin ellos. `analisis/verificar.py` compara lo que dijo la página con lo que de verdad llovió, y `analisis/experimentos.py` prueba variantes del modelo. La página muestra en grande la hora en curso y, en la tabla «Próximas horas», la probabilidad de cada una de las 6 horas siguientes. El modelo de 6 h solo se usa para los avisos. La evaluación completa está en [analisis/resultados.md](analisis/resultados.md).

**Respaldo:** si no se puede calcular el modelo corregido, se usan los ensambles de ECMWF (51 simulaciones) y GFS (31) sin corregir, que exageran mucho la lluvia en Guayaquil. Si tampoco hay ensambles, se usa la heurística original (`assets/modelo.js`), que asume meses secos y subestima la lluvia en años de El Niño. Los tres valores se guardan en cada fila (`corregido`, `ensamble`, `heuristica`) para compararlos después.

### Reentrenar el modelo corregido

Conviene hacerlo cada pocos meses, para que aprenda de la lluvia más reciente:

```bash
python -m venv .venv
```

```bash
.venv/Scripts/python -m pip install -r analisis/requirements.txt
```

```bash
.venv/Scripts/python analisis/descargar.py --forzar
```

Para los rayos, corre en GitHub **Actions → Historial de rayos → Run workflow** y baja los resultados a `analisis/datos/rayos/`:

```bash
gh run download <id de la corrida> -D analisis/datos/rayos
```

```bash
.venv/Scripts/python analisis/entrenar.py
```

```bash
node --test
```

`entrenar.py` reescribe `analisis/resultados.md`, `assets/mos-coeficientes.js` y los casos de `tests/fixtures/mos-casos.json`. Las pruebas comprueban que JavaScript calcula exactamente lo mismo que Python.

No es un pronóstico oficial. Datos del clima: [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0).
