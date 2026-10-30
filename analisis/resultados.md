# Fase B: ¿qué tan certeros son los pronósticos de lluvia para Guayaquil?

Verdad: lluvia o llovizna reportada en el aeropuerto (SEGU). Entrenamiento: 2023-01-01 a 2024-12-31. Prueba (datos que el modelo no vio): 2025-01-01 a 2026-10-27. Las regresiones logísticas dan más peso a lo reciente (media vida de 730 días). La página usa además la recalibración y los modelos según el minuto de la hora, que se validan mes a mes en [validacion.md](validacion.md).

## ¿Llueve en esta hora?

Horas de prueba: 15,346. Llovió en el 7 % de ellas (en entrenamiento: 6 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Heurística actual | 0.160 | -181 % | 0.81 |
| Climatología (mes y hora) | 0.057 | +0 % | 0.77 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.145 | -154 % | 0.90 |
| MOS: regresión logística | 0.045 | +21 % | 0.92 |
| MOS: gradient boosting | 0.049 | +14 % | 0.90 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.031 | +45 % | 0.95 |
| MOS logística + aeropuerto + rayos del satélite | 0.030 | +48 % | 0.96 |
| MOS logística + aeropuerto + rayos + infrarrojo | 0.030 | +48 % | 0.96 |

**Calibración de «MOS logística + aeropuerto + rayos + infrarrojo»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 13,390 | 2 % | 1 % |
| 10–20 % | 617 | 14 % | 13 % |
| 20–30 % | 233 | 24 % | 20 % |
| 30–40 % | 103 | 34 % | 32 % |
| 40–50 % | 81 | 44 % | 41 % |
| 50–60 % | 98 | 55 % | 50 % |
| 60–70 % | 115 | 65 % | 55 % |
| 70–80 % | 157 | 75 % | 69 % |
| 80–90 % | 224 | 85 % | 80 % |
| 90–100 % | 328 | 95 % | 90 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 7 | 55 % | 43 % |
| 60 % | 5 | 63 % | 30 % |
| 70 % | 3 | 73 % | 19 % |
| 80 % | 2 | 85 % | 10 % |
| 90 % | 0 | 100 % | 0 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 12 | 74 % | 65 % |
| 60 % | 11 | 76 % | 63 % |
| 70 % | 9 | 79 % | 55 % |
| 80 % | 7 | 84 % | 44 % |
| 90 % | 3 | 88 % | 17 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos del satélite»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 11 | 75 % | 67 % |
| 60 % | 10 | 78 % | 62 % |
| 70 % | 9 | 82 % | 55 % |
| 80 % | 7 | 85 % | 44 % |
| 90 % | 5 | 90 % | 25 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos + infrarrojo»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 11 | 75 % | 67 % |
| 60 % | 10 | 78 % | 62 % |
| 70 % | 9 | 82 % | 56 % |
| 80 % | 7 | 86 % | 45 % |
| 90 % | 5 | 90 % | 28 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | Modelo de la página |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,499 | 15 % | -129 %; 0.81 | +48 %; 0.93 |
| Temporada seca (may–dic) | 9,847 | 2 % | -226 %; 0.91 | +49 %; 0.96 |
| Último mes (2026-10) | 636 | 13 % | -94 %; 0.87 | +62 %; 0.92 |

## ¿Llueve en las próximas 6 horas?

Horas de prueba: 14,874. Llovió en el 15 % de ellas (en entrenamiento: 15 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Climatología (mes y hora) | 0.112 | +0 % | 0.76 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.226 | -102 % | 0.87 |
| MOS: regresión logística | 0.084 | +25 % | 0.90 |
| MOS: gradient boosting | 0.089 | +20 % | 0.88 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.076 | +32 % | 0.91 |
| MOS logística + aeropuerto + rayos del satélite | 0.075 | +33 % | 0.92 |

**Calibración de «MOS logística + aeropuerto + rayos del satélite»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 9,095 | 3 % | 2 % |
| 10–20 % | 1,586 | 14 % | 11 % |
| 20–30 % | 1,029 | 25 % | 20 % |
| 30–40 % | 743 | 35 % | 29 % |
| 40–50 % | 488 | 45 % | 38 % |
| 50–60 % | 410 | 55 % | 47 % |
| 60–70 % | 316 | 65 % | 47 % |
| 70–80 % | 299 | 75 % | 66 % |
| 80–90 % | 336 | 85 % | 78 % |
| 90–100 % | 572 | 96 % | 94 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 11 | 62 % | 58 % |
| 60 % | 10 | 69 % | 47 % |
| 70 % | 7 | 76 % | 35 % |
| 80 % | 5 | 84 % | 21 % |
| 90 % | 2 | 97 % | 7 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 14 | 69 % | 58 % |
| 60 % | 13 | 75 % | 49 % |
| 70 % | 12 | 82 % | 41 % |
| 80 % | 10 | 89 % | 32 % |
| 90 % | 7 | 94 % | 21 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos del satélite»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 16 | 69 % | 59 % |
| 60 % | 14 | 75 % | 50 % |
| 70 % | 13 | 83 % | 44 % |
| 80 % | 11 | 88 % | 35 % |
| 90 % | 7 | 94 % | 24 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | Modelo de la página |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,326 | 32 % | -74 %; 0.77 | +32 %; 0.86 |
| Temporada seca (may–dic) | 9,548 | 6 % | -153 %; 0.88 | +36 %; 0.91 |
| Último mes (2026-10) | 624 | 28 % | -50 %; 0.76 | +46 %; 0.85 |
