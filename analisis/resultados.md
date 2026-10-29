# Fase B: ¿qué tan certeros son los pronósticos de lluvia para Guayaquil?

Verdad: lluvia o llovizna reportada en el aeropuerto (SEGU). Entrenamiento: 2023-01-01 a 2024-12-31. Prueba (datos que el modelo no vio): 2025-01-01 a 2026-10-27.

## ¿Llueve en esta hora?

Horas de prueba: 15,366. Llovió en el 7 % de ellas (en entrenamiento: 6 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Heurística actual | 0.160 | -181 % | 0.81 |
| Climatología (mes y hora) | 0.057 | +0 % | 0.77 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.145 | -154 % | 0.90 |
| MOS: regresión logística | 0.045 | +21 % | 0.92 |
| MOS: gradient boosting | 0.049 | +14 % | 0.90 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.031 | +45 % | 0.95 |
| MOS logística + aeropuerto + rayos del satélite | 0.030 | +48 % | 0.96 |

**Calibración de «MOS logística + aeropuerto + rayos del satélite»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 13,349 | 2 % | 1 % |
| 10–20 % | 691 | 14 % | 11 % |
| 20–30 % | 229 | 24 % | 23 % |
| 30–40 % | 89 | 35 % | 39 % |
| 40–50 % | 88 | 45 % | 39 % |
| 50–60 % | 98 | 55 % | 48 % |
| 60–70 % | 129 | 65 % | 54 % |
| 70–80 % | 170 | 75 % | 72 % |
| 80–90 % | 253 | 85 % | 81 % |
| 90–100 % | 270 | 95 % | 90 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 7 | 56 % | 43 % |
| 60 % | 5 | 65 % | 30 % |
| 70 % | 3 | 72 % | 19 % |
| 80 % | 2 | 83 % | 9 % |
| 90 % | 0 | 100 % | 1 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 12 | 74 % | 65 % |
| 60 % | 11 | 76 % | 62 % |
| 70 % | 9 | 80 % | 55 % |
| 80 % | 7 | 84 % | 43 % |
| 90 % | 3 | 89 % | 16 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos del satélite»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 11 | 75 % | 66 % |
| 60 % | 10 | 78 % | 62 % |
| 70 % | 9 | 83 % | 55 % |
| 80 % | 7 | 86 % | 43 % |
| 90 % | 5 | 90 % | 23 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | Modelo de la página |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,506 | 15 % | -128 %; 0.81 | +47 %; 0.93 |
| Temporada seca (may–dic) | 9,860 | 2 % | -227 %; 0.91 | +48 %; 0.96 |
| Último mes (2026-10) | 637 | 13 % | -95 %; 0.87 | +61 %; 0.93 |

## ¿Llueve en las próximas 6 horas?

Horas de prueba: 14,874. Llovió en el 15 % de ellas (en entrenamiento: 15 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Climatología (mes y hora) | 0.112 | +0 % | 0.76 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.226 | -102 % | 0.87 |
| MOS: regresión logística | 0.084 | +25 % | 0.90 |
| MOS: gradient boosting | 0.089 | +20 % | 0.88 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.076 | +32 % | 0.91 |
| MOS logística + aeropuerto + rayos del satélite | 0.074 | +33 % | 0.92 |

**Calibración de «MOS logística + aeropuerto + rayos del satélite»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 9,086 | 3 % | 2 % |
| 10–20 % | 1,624 | 14 % | 11 % |
| 20–30 % | 1,058 | 25 % | 20 % |
| 30–40 % | 713 | 35 % | 27 % |
| 40–50 % | 496 | 45 % | 40 % |
| 50–60 % | 404 | 55 % | 46 % |
| 60–70 % | 316 | 65 % | 51 % |
| 70–80 % | 291 | 75 % | 67 % |
| 80–90 % | 319 | 85 % | 79 % |
| 90–100 % | 567 | 96 % | 94 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 11 | 62 % | 57 % |
| 60 % | 9 | 70 % | 46 % |
| 70 % | 7 | 77 % | 34 % |
| 80 % | 4 | 85 % | 21 % |
| 90 % | 2 | 98 % | 7 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 14 | 70 % | 58 % |
| 60 % | 13 | 76 % | 49 % |
| 70 % | 12 | 82 % | 40 % |
| 80 % | 10 | 89 % | 31 % |
| 90 % | 6 | 94 % | 20 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos del satélite»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 15 | 70 % | 58 % |
| 60 % | 14 | 77 % | 50 % |
| 70 % | 13 | 83 % | 43 % |
| 80 % | 10 | 89 % | 34 % |
| 90 % | 7 | 94 % | 23 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | Modelo de la página |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,326 | 32 % | -74 %; 0.77 | +32 %; 0.86 |
| Temporada seca (may–dic) | 9,548 | 6 % | -153 %; 0.88 | +37 %; 0.91 |
| Último mes (2026-10) | 624 | 28 % | -50 %; 0.76 | +47 %; 0.85 |
