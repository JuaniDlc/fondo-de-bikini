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

Dos avisos, enviados con [CallMeBot](https://www.callmebot.com/blog/free-api-whatsapp-messages/):

- **Lluvia** (workflow «Actualizar lectura», cada hora): cuando el modelo corregido da ≥ 80 % de lluvia en las próximas 6 horas. No se repite hasta que la probabilidad baje de 60 %.
- **Rayos** (workflow «Rayos», cada 10 minutos): cuando el satélite GOES-19 ve al menos 3 rayos a menos de 60 km de Guayaquil en los últimos 10 minutos (`scripts/rayos.py`). Avisa otra vez si la tormenta se acerca a menos de 25 km; si no, como mucho uno por hora.

La lógica está en `scripts/alertas.mjs` y el estado (qué avisos están activos) en `data/alertas.json`.

**Configurar destinatarios:**

1. Cada persona que quiera recibir los avisos activa CallMeBot desde su WhatsApp siguiendo las instrucciones de su página, y recibe una clave (apikey).
2. En el repositorio, **Settings → Secrets and variables → Actions → New repository secret**, nombre `CALLMEBOT_DESTINOS`, valor con el formato `+593XXXXXXXXX:clave` (varios separados por `;`). Nunca pongas números ni claves en el código.
3. En **Actions → Probar WhatsApp → Run workflow** se envía un mensaje de prueba.

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

**Probabilidad principal: modelo corregido (MOS)** en `assets/mos.js`. Es una regresión logística entrenada con la lluvia que de verdad reportó el aeropuerto de Guayaquil (2023 a 2026). Usa como entrada los pronósticos de GFS, ECMWF e ICON, la hora, la época del año, el índice de El Niño y, si es de la hora actual, si está lloviendo en el aeropuerto. Responde dos preguntas: «¿llueve en esta hora?» y «¿llueve en algún momento de las próximas 6 horas?». La segunda es el número grande de la página porque es la que mejor acierta. La evaluación completa está en [analisis/resultados.md](analisis/resultados.md).

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

```bash
.venv/Scripts/python analisis/entrenar.py
```

```bash
node --test
```

`entrenar.py` reescribe `analisis/resultados.md`, `assets/mos-coeficientes.js` y los casos de `tests/fixtures/mos-casos.json`. Las pruebas comprueban que JavaScript calcula exactamente lo mismo que Python.

No es un pronóstico oficial. Datos del clima: [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0).
