# Fase B: ¿qué tan certeros son los pronósticos de lluvia para Guayaquil?

Verdad: lluvia o llovizna reportada en el aeropuerto (SEGU). Entrenamiento: 2023-01-01 a 2024-12-31. Prueba (datos que el modelo no vio): 2025-01-01 a 2026-10-27. Las regresiones logísticas dan más peso a lo reciente (media vida de 730 días). La página usa además la recalibración y los modelos según el minuto de la hora, que se validan mes a mes en [validacion.md](validacion.md).

## ¿Llueve en esta hora?

Horas de prueba: 15,327. Llovió en el 7 % de ellas (en entrenamiento: 6 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Heurística actual | 0.160 | -181 % | 0.81 |
| Climatología (mes y hora) | 0.057 | +0 % | 0.77 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.145 | -155 % | 0.90 |
| MOS: regresión logística | 0.045 | +21 % | 0.92 |
| MOS: gradient boosting | 0.048 | +16 % | 0.91 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.031 | +45 % | 0.95 |
| MOS logística + aeropuerto + rayos del satélite | 0.030 | +48 % | 0.96 |
| MOS logística + aeropuerto + rayos + infrarrojo | 0.030 | +48 % | 0.96 |
| MOS logística + aeropuerto + rayos + infrarrojo + vapor de agua | 0.029 | +49 % | 0.96 |

**Calibración de «MOS logística + aeropuerto + rayos + infrarrojo + vapor de agua»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 13,394 | 2 % | 1 % |
| 10–20 % | 632 | 14 % | 11 % |
| 20–30 % | 200 | 24 % | 26 % |
| 30–40 % | 109 | 35 % | 30 % |
| 40–50 % | 96 | 45 % | 43 % |
| 50–60 % | 79 | 55 % | 53 % |
| 60–70 % | 134 | 65 % | 53 % |
| 70–80 % | 143 | 76 % | 71 % |
| 80–90 % | 243 | 85 % | 81 % |
| 90–100 % | 297 | 95 % | 91 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 7 | 55 % | 43 % |
| 60 % | 5 | 63 % | 30 % |
| 70 % | 3 | 73 % | 18 % |
| 80 % | 2 | 85 % | 10 % |
| 90 % | 0 | 100 % | 0 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 12 | 74 % | 65 % |
| 60 % | 11 | 76 % | 63 % |
| 70 % | 9 | 79 % | 55 % |
| 80 % | 7 | 83 % | 43 % |
| 90 % | 3 | 89 % | 17 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos del satélite»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 11 | 75 % | 67 % |
| 60 % | 10 | 78 % | 62 % |
| 70 % | 9 | 82 % | 55 % |
| 80 % | 7 | 86 % | 44 % |
| 90 % | 5 | 90 % | 25 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos + infrarrojo»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 11 | 75 % | 67 % |
| 60 % | 10 | 78 % | 62 % |
| 70 % | 9 | 82 % | 56 % |
| 80 % | 7 | 86 % | 45 % |
| 90 % | 5 | 90 % | 28 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos + infrarrojo + vapor de agua»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 11 | 76 % | 66 % |
| 60 % | 10 | 78 % | 62 % |
| 70 % | 9 | 83 % | 55 % |
| 80 % | 8 | 87 % | 45 % |
| 90 % | 6 | 91 % | 26 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | Modelo de la página |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,491 | 15 % | -129 %; 0.81 | +48 %; 0.93 |
| Temporada seca (may–dic) | 9,836 | 2 % | -226 %; 0.91 | +49 %; 0.96 |
| Último mes (2026-10) | 636 | 13 % | -94 %; 0.87 | +62 %; 0.92 |

## ¿Llueve en las próximas 6 horas?

Horas de prueba: 14,854. Llovió en el 15 % de ellas (en entrenamiento: 15 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Climatología (mes y hora) | 0.112 | +0 % | 0.76 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.226 | -102 % | 0.87 |
| MOS: regresión logística | 0.084 | +25 % | 0.90 |
| MOS: gradient boosting | 0.090 | +19 % | 0.88 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.076 | +32 % | 0.91 |
| MOS logística + aeropuerto + rayos del satélite | 0.075 | +33 % | 0.92 |
| MOS logística + aeropuerto + rayos + infrarrojo + vapor de agua | 0.074 | +34 % | 0.92 |

**Calibración de «MOS logística + aeropuerto + rayos + infrarrojo + vapor de agua»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 8,928 | 3 % | 2 % |
| 10–20 % | 1,715 | 14 % | 11 % |
| 20–30 % | 1,005 | 25 % | 19 % |
| 30–40 % | 775 | 35 % | 27 % |
| 40–50 % | 520 | 45 % | 38 % |
| 50–60 % | 375 | 55 % | 48 % |
| 60–70 % | 321 | 65 % | 48 % |
| 70–80 % | 312 | 75 % | 68 % |
| 80–90 % | 315 | 85 % | 78 % |
| 90–100 % | 588 | 96 % | 94 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 11 | 62 % | 58 % |
| 60 % | 10 | 69 % | 47 % |
| 70 % | 7 | 76 % | 35 % |
| 80 % | 5 | 84 % | 21 % |
| 90 % | 2 | 96 % | 7 % |

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
| 50 % | 16 | 69 % | 58 % |
| 60 % | 14 | 76 % | 50 % |
| 70 % | 13 | 83 % | 44 % |
| 80 % | 11 | 88 % | 35 % |
| 90 % | 7 | 94 % | 24 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos + infrarrojo + vapor de agua»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 16 | 70 % | 59 % |
| 60 % | 14 | 76 % | 51 % |
| 70 % | 13 | 83 % | 44 % |
| 80 % | 10 | 89 % | 35 % |
| 90 % | 7 | 94 % | 24 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | Modelo de la página |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,318 | 32 % | -74 %; 0.77 | +33 %; 0.87 |
| Temporada seca (may–dic) | 9,536 | 6 % | -153 %; 0.88 | +35 %; 0.91 |
| Último mes (2026-10) | 624 | 28 % | -50 %; 0.76 | +45 %; 0.84 |
