# Bitácora de mejoras probadas

Cada prueba de una mejora del modelo se anota aquí, haya funcionado o no, para no repetirla y poder comprobar el resultado. La entrada más reciente va primero.

- **Estados:** *En producción* (subida y en uso), *No subida* (probada, no cumplió o no convino), *Retirada* (estuvo en uso y se quitó), *Pendiente* (idea sin probar).
- **Brier:** error de la probabilidad, menor es mejor. Verdad: lluvia reportada en el aeropuerto.
- **Cuidado al comparar:** cada prueba usó su periodo y su modelo base de ese momento. Los Brier solo se comparan dentro de una misma fila.

## Cómo anotar una prueba nueva

1. Antes de ver resultados, escribir la regla para adoptarla.
2. Comparar contra el modelo de la página sobre las mismas horas, reentrenando solo con datos anteriores.
3. Revisar que el modelo base dé los valores ya conocidos (AUC cerca de 0,96 en la hora en curso). Si no, la prueba está mal, no el modelo.
4. Agregar la fila con fecha, resultado, estado, commit y dónde está el detalle.

## Resumen

| Fecha | Mejora | Resultado | Estado | Commit | Detalle |
|---|---|---|---|---|---|
| 2026-11-02 | Solo viento + temperatura del mar, de 1 a 6 h | De +0,7 a +2,0 % por hora, sin cumplir la regla; próximas 6 h empeora (−1,7 %) | No subida | solo la prueba | [abajo](#2026-11-02-solo-viento-y-temperatura-del-mar) |
| 2026-11-02 | Combinado: presión de vapor + viento + temperatura del mar | De +0,4 a +1,7 % según la anticipación; no cumple la regla en ninguna | No subida | solo la prueba | [abajo](#2026-11-02-modelo-combinado) |
| 2026-11-02 | Variables extra de GFS, repetición de la prueba de octubre: T − Td, nubes bajas, LI, CIN, viento a 10 m, chubascos, CAPE de ICON | Sin mejora. Con aeropuerto, hora en curso 0,031 → 0,031; 6 h 0,075 → 0,076 | No subida | solo la prueba | `experimentos.py` (no se guardó el resultado de octubre; base sin rayos) |
| 2026-10-30 | Vapor de agua de GOES (canales 8 y 10) | De +0,6 a +1,3 % por trimestres; próximas 6 h mejora en 7 de 8 | En producción | `b16b8a0` | [satelite.md](satelite.md) |
| 2026-10-30 | Movimiento de las nubes (GOES) | Empeora: hora en curso 0,0294 → 0,0297; junto al vapor, −0,5 % | No subida | `20062fe` (solo historial) | [satelite.md](satelite.md) |
| 2026-10-30 | Inestabilidad de GOES (CAPE, LI, K, agua precipitable) | Casi nada: 0,0294 → 0,0293; junto al vapor, −0,5 % | No subida | `20062fe` (solo historial) | [satelite.md](satelite.md) |
| 2026-10-30 | Lluvia estimada por GOES (RRQPE) | No mejora: 0,0294 → 0,0295. Solo ve el 30 % de las horas con lluvia | No subida | `e306ad0` (solo historial) | [satelite.md](satelite.md) |
| 2026-10-30 | IMERG (NASA) como verdad por lugar | Coincide unas 6 de cada 10 veces con el aeropuerto; en vivo sale 4 h tarde | No subida | `27f44b7` (solo comparación) | [satelite.md](satelite.md) |
| 2026-10-29 | Modelo según el minuto de la hora | Minuto 50: 0,0294 → 0,0287 (tormenta 0,1002 → 0,0946). Minuto 0: 0,0296 → 0,0298 | En producción | `02821fb` | [validacion.md](validacion.md) |
| 2026-10-29 | Más peso a lo reciente (media vida de 2 años) | 6 h: 0,0730 → 0,0727. Hora en curso: 0,0288 → 0,0289, sin mejora; se usa en ambos | En producción | `02821fb` | [validacion.md](validacion.md) |
| 2026-10-29 | Recalibración Platt en 6 h | 0,0548 → 0,0540 | En producción | `02821fb` | [validacion.md](validacion.md) |
| 2026-10-29 | Recalibración de la hora en curso (Platt o isotónica) | No mejora: 0,0196 → 0,0197 con ambas | No subida | `02821fb` | [validacion.md](validacion.md) |
| 2026-10-29 | Isotónica en 6 h | Sin cambio frente a no recalibrar: 0,0548 | No subida | `02821fb` | [validacion.md](validacion.md) |
| 2026-10-29 | Interacciones con la época del año | Empeora: 6 h 0,0727 → 0,0732; hora en curso 0,0289 → 0,0290 | No subida | `02821fb` | [validacion.md](validacion.md) |
| 2026-10-29 | Gradient boosting monótono | Empeora: 6 h 0,0727 → 0,0759; hora en curso 0,0289 → 0,0294 | No subida | `02821fb` | [validacion.md](validacion.md) |
| 2026-10-29 | Lugares: la lluvia del aeropuerto entra como dato, no como 100 % | Cambio de lógica; no se midió con números | En producción | `02821fb` | [observaciones.md](observaciones.md) |
| 2026-10-28 | Infrarrojo de GOES, 1 a 4 h | Mejora de 0,5 a 1,1 puntos; a 5 y 6 h no ayuda | En producción | `ae2af2f` | [resultados.md](resultados.md) |
| 2026-10-28 | Seis modelos del clima (se suman UKMO, JMA y ECMWF de 9 km) | Mejora, sobre todo a 4-6 h: a 6 h, de 19,5 a 21,1 % sobre el promedio histórico | En producción | `2ef4685` | commit |
| 2026-10-27 | Rayos de GOES (GLM), con todos los archivos | Hora en curso 0,031 → 0,030; 6 h 0,076 → 0,075. Todos los archivos frente a muestra: 0,0306 → 0,0303 | En producción | `c904980`, `60db039` | [resultados.md](resultados.md) |
| 2026-10-27 | Ventanas de ±2 y ±3 h en los pronósticos | Corrige que se quedaba bajo en sep-oct 2026; sin número aislado | En producción | `c904980` | commit |
| 2026-10-27 | Probabilidad acumulada hora por hora | De 30 a 43 % sobre el promedio histórico; se quitó de la página | Retirada | `eb9cecd`, quitada en `c904980` | commit |
| 2026-10-26 | Lluvia del aeropuerto y un modelo por anticipación | Brier 0,048 → 0,032; AUC 0,89 → 0,94 | En producción | `181157b` | [resultados.md](resultados.md) |
| 2026-10-25 | Modelo corregido (regresión logística) frente a la heurística | Hora: 0,160 → 0,045 | En producción | `032ab19` | [resultados.md](resultados.md) |
| 2026-10-25 | Gradient boosting | Peor que la logística: hora 0,048 frente a 0,045; 6 h 0,090 frente a 0,084 | No subida | `032ab19` | [resultados.md](resultados.md) |

## Pendientes

Ideas sin probar, de [observaciones.md](observaciones.md):

- Forzar que los rayos cercanos solo puedan subir la probabilidad. El 1 de noviembre a las 18:10, más rayos la bajaron de 62 a 50 %.
- Suavizar las variables de rayos de 20 minutos. El mismo día, a las 16:10, un rayo que salió de la ventana bajó la hora de 49 a 21 %.
- Un objetivo aparte para lluvia fuerte: el modelo dice si llueve, no cuánto.

## 2026-11-02: solo viento y temperatura del mar

**Pregunta:** sin la presión de vapor, ¿el viento y el mar mejoran el modelo, sobre todo a 5 y 6 horas?

**Regla, fijada antes de ver resultados:** mejora de al menos 0,5 %, intervalo de 99 % sin el cero y mejora en al menos 6 de 8 trimestres. Es más estricta que la del combinado porque la idea salió de esas mismas horas.

**Método:** las mismas variables de viento y mar del combinado. A diferencia de esa prueba, usa los seis minutos de cada hora, agrega las horas 5 y 6 con su modelo y recalibra las próximas 6 h con Platt, como la página.

| Pronóstico | Brier página | Con viento y mar | Mejora | Intervalo de 99 % | Trimestres | ¿Cumple? |
|---|---|---|---|---|---|---|
| Hora en curso | 0,0268 | 0,0266 | +0,72 % | [−0,56; +1,86] | 4/8 | no |
| 2 h | 0,0333 | 0,0329 | +1,18 % | [−0,44; +2,73] | 5/8 | no |
| 3 h | 0,0366 | 0,0361 | +1,38 % | [−0,53; +3,25] | 5/8 | no |
| 4 h | 0,0388 | 0,0381 | +1,75 % | [−0,21; +3,79] | 5/8 | no |
| 5 h | 0,0408 | 0,0400 | +1,83 % | [−0,27; +3,87] | 5/8 | no |
| 6 h | 0,0414 | 0,0406 | +1,98 % | [−0,09; +4,03] | 4/8 | no |
| Próximas 6 h | 0,0694 | 0,0705 | −1,70 % | [−3,52; +0,15] | 2/8 | no |

**Lectura:**

1. **No se adopta.** Ninguna anticipación cumple la regla: los intervalos incluyen el cero y mejora en 5 de 8 trimestres como mucho.
2. **Mejora por hora, pero no de forma estable.** Crece con la anticipación y viene de la temporada lluviosa (+2,68 % a 6 h, intervalo [+0,29; +5,27]); en la seca es casi nula. El AUC no cambia en ninguna hora.
3. **Las próximas 6 h empeoran,** sobre todo en la temporada lluviosa (−2,87 %, intervalo [−5,24; −0,60]). Ese modelo decide los avisos, así que no conviene agregarlas ahí.

**Cuándo volver a mirarlo:** al terminar la temporada lluviosa de 2027 (enero a abril), con horas que no se usaron para idear la prueba. Se puede repetir con `viento_mar.py`, sobre todo para la temporada lluviosa de 4 a 6 h.

**Archivos:** [viento_mar.md](viento_mar.md) y `viento_mar.py`.

## 2026-11-02: modelo combinado

**Pregunta:** ¿la presión de vapor, el viento y la temperatura del mar, puestos juntos, mejoran el modelo aunque por separado no lo hagan?

**Regla, fijada antes de ver resultados:** mejora de al menos 0,5 %, intervalo de 95 % sin el cero y mejora en al menos 6 de 8 trimestres.

**Variables agregadas al modelo de la página:**

- **Presión de vapor:** a 2 m y a 850 hPa, de GFS. No es lo mismo que el vapor de GOES (canales 8 y 10), que ya está en producción y sigue en el modelo base.
- **Viento:** a 10 m, 850, 500 y 200 hPa, de GFS, más la cizalla entre 850 y 200 hPa.
- **Temperatura del mar:** en un punto frente a la costa, la diferencia con mar afuera, el cambio en 7 días y la diferencia con el aire a 850 hPa, de la API marina de Open-Meteo. Se usa la de 24 a 48 h antes, para no adelantar información.

**Método:** reentrenado cada trimestre desde 2025 solo con lo anterior, sobre las mismas horas.

| Pronóstico | Solo presión de vapor | Solo viento | Solo mar | **Combinado** | Intervalo | Trimestres | ¿Cumple? |
|---|---|---|---|---|---|---|---|
| Hora en curso | −0,30 % | +0,35 % | +0,45 % | **+0,56 %** | [−0,37; +1,46] | 4/8 | no |
| 2 h | −0,27 % | +0,62 % | +0,74 % | **+1,08 %** | [−0,22; +2,34] | 5/8 | no |
| 3 h | −0,24 % | +0,94 % | +0,77 % | **+1,33 %** | [−0,20; +2,78] | 5/8 | no |
| 4 h | −0,15 % | +1,29 % | +0,76 % | **+1,73 %** | [+0,16; +3,24] | 5/8 | no |
| Próximas 6 h | +0,10 % | +0,63 % | −0,23 % | **+0,42 %** | [−1,58; +2,45] | 4/8 | no |

**Lectura:**

1. **No se adopta.** Ninguna anticipación cumple la regla. La más cercana, a 4 h, falla porque mejora solo en 5 de 8 trimestres.
2. **Juntas no suman más que por separado.** A 4 h, el combinado da +1,73 %, menos que viento y mar sumados (+2,05 %). Las interacciones tampoco ayudan (+1,38 %), y gradient boosting queda por debajo del modelo de la página (−0,47 %).
3. **La presión de vapor no aporta en los modelos por hora.** Sola es levemente negativa de 1 a 4 h, quizá porque el modelo ya tiene humedad, nubes y el vapor de GOES.
4. **Lo prometedor:** la mejora crece con la anticipación y viene de la temporada lluviosa (+2,06 % a 4 h). El AUC casi no cambia, así que afina poco la capacidad de separar horas con y sin lluvia.

**Límites:**

- Solo se usaron los minutos 0 y 30 de cada hora; la página usa los seis.
- El viento y la presión de vapor son solo de GFS.
- La temperatura del mar es de un modelo, con 0,9 % de horas sin dato.
- Las 6 h no llevan la recalibración Platt.
- No se probaron 5 y 6 h, donde el infrarrojo y el vapor de GOES no se usan.

**Error corregido durante la prueba:** la primera corrida dio AUC 0,57 en el modelo base, porque al apilar minutos las predicciones quedaron en otro orden que las observaciones. Sus resultados, incluido un «+3 %» de gradient boosting, no valen. `combinado.py` ahora ordena las filas y se detiene si el modelo base sale con AUC menor a 0,85.

**Archivos:** [combinado.md](combinado.md) (tablas completas), `combinado.py` y `combinado_descargar.py`.
