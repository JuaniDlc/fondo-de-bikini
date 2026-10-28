# Fase B: ¿qué tan certeros son los pronósticos de lluvia para Guayaquil?

Verdad: lluvia o llovizna reportada en el aeropuerto (SEGU). Entrenamiento: 2023-01-01 a 2024-12-31. Prueba (datos que el modelo no vio): 2025-01-01 a 2026-10-26.

## ¿Llueve en esta hora?

Horas de prueba: 15,342. Llovió en el 7 % de ellas (en entrenamiento: 6 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Heurística actual | 0.160 | -181 % | 0.81 |
| Climatología (mes y hora) | 0.057 | +0 % | 0.78 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.144 | -152 % | 0.87 |
| MOS: regresión logística | 0.048 | +16 % | 0.92 |
| MOS: gradient boosting | 0.051 | +10 % | 0.89 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.032 | +44 % | 0.95 |
| MOS logística + aeropuerto + rayos del satélite | 0.030 | +47 % | 0.96 |

**Calibración de «MOS logística + aeropuerto + rayos del satélite»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 13,280 | 2 % | 1 % |
| 10–20 % | 716 | 14 % | 11 % |
| 20–30 % | 225 | 24 % | 20 % |
| 30–40 % | 107 | 35 % | 30 % |
| 40–50 % | 80 | 45 % | 44 % |
| 50–60 % | 91 | 55 % | 54 % |
| 60–70 % | 135 | 65 % | 52 % |
| 70–80 % | 185 | 75 % | 70 % |
| 80–90 % | 249 | 85 % | 81 % |
| 90–100 % | 274 | 95 % | 89 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 7 | 52 % | 43 % |
| 60 % | 5 | 57 % | 27 % |
| 70 % | 3 | 70 % | 15 % |
| 80 % | 1 | 81 % | 3 % |
| 90 % | 0 | nan % | 0 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 12 | 74 % | 66 % |
| 60 % | 11 | 75 % | 62 % |
| 70 % | 9 | 77 % | 56 % |
| 80 % | 7 | 82 % | 43 % |
| 90 % | 3 | 86 % | 13 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos del satélite»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 12 | 74 % | 67 % |
| 60 % | 11 | 77 % | 62 % |
| 70 % | 9 | 81 % | 55 % |
| 80 % | 7 | 85 % | 43 % |
| 90 % | 5 | 89 % | 24 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | Modelo de la página |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,506 | 15 % | -129 %; 0.78 | +46 %; 0.93 |
| Temporada seca (may–dic) | 9,836 | 2 % | -217 %; 0.88 | +48 %; 0.95 |
| Último mes (2026-10) | 613 | 13 % | -84 %; 0.85 | +62 %; 0.94 |

## ¿Llueve en las próximas 6 horas?

Horas de prueba: 14,850. Llovió en el 15 % de ellas (en entrenamiento: 15 %).

| Modelo | Brier (menor es mejor) | Mejora sobre climatología | AUC (0,5 = azar, 1 = perfecto) |
|---|---|---|---|
| Climatología (mes y hora) | 0.112 | +0 % | 0.76 |
| Modelos crudos (GFS, ECMWF, ICON) | 0.211 | -89 % | 0.85 |
| MOS: regresión logística | 0.086 | +23 % | 0.90 |
| MOS: gradient boosting | 0.097 | +13 % | 0.86 |
| MOS logística + lluvia en el aeropuerto (METAR) | 0.077 | +31 % | 0.91 |
| MOS logística + aeropuerto + rayos del satélite | 0.075 | +33 % | 0.92 |

**Calibración de «MOS logística + aeropuerto + rayos del satélite»** (cuando dice X %, ¿cuánto llovió?):

| Pronóstico | Horas | Promedio pronosticado | Llovió de verdad |
|---|---|---|---|
| 0–10 % | 8,968 | 4 % | 2 % |
| 10–20 % | 1,875 | 14 % | 12 % |
| 20–30 % | 954 | 25 % | 19 % |
| 30–40 % | 651 | 34 % | 27 % |
| 40–50 % | 496 | 45 % | 41 % |
| 50–60 % | 394 | 55 % | 50 % |
| 60–70 % | 350 | 65 % | 50 % |
| 70–80 % | 276 | 75 % | 67 % |
| 80–90 % | 336 | 85 % | 78 % |
| 90–100 % | 550 | 96 % | 93 % |

**Si se usara como alerta** («MOS: regresión logística»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 8 | 62 % | 57 % |
| 60 % | 7 | 66 % | 44 % |
| 70 % | 5 | 74 % | 34 % |
| 80 % | 4 | 82 % | 19 % |
| 90 % | 1 | 100 % | 2 % |

**Si se usara como alerta** («MOS logística + lluvia en el aeropuerto (METAR)»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 13 | 68 % | 58 % |
| 60 % | 12 | 74 % | 49 % |
| 70 % | 11 | 80 % | 40 % |
| 80 % | 10 | 87 % | 29 % |
| 90 % | 6 | 92 % | 19 % |

**Si se usara como alerta** («MOS logística + aeropuerto + rayos del satélite»):

| Alerta cuando dice ≥ | Avisos por mes | Cuando alerta, llueve | Lluvias que detecta |
|---|---|---|---|
| 50 % | 14 | 70 % | 58 % |
| 60 % | 14 | 75 % | 50 % |
| 70 % | 12 | 83 % | 42 % |
| 80 % | 11 | 87 % | 34 % |
| 90 % | 7 | 93 % | 22 % |

**Por periodo** (mejora sobre climatología; AUC):

| Periodo | Horas | Llovió | Modelos crudos | Modelo de la página |
|---|---|---|---|---|
| Temporada lluviosa (ene–abr) | 5,326 | 32 % | -65 %; 0.74 | +29 %; 0.85 |
| Temporada seca (may–dic) | 9,524 | 6 % | -134 %; 0.86 | +39 %; 0.91 |
| Último mes (2026-10) | 600 | 29 % | -31 %; 0.77 | +54 %; 0.87 |
